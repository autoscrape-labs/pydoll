# Construindo Servidores Proxy

Este documento implementa servidores proxy HTTP e SOCKS5 do zero em Python usando asyncio. O objetivo não é prontidão para produção, mas compreensão de protocolo: ver como cada byte é analisado, onde estão os limites de segurança e por que certas decisões de design existem em software proxy real.

!!! info "Navegação do Módulo"
    - [Fundamentos de Rede](./network-fundamentals.md): TCP/IP, UDP, WebRTC
    - [Proxies HTTP/HTTPS](./http-proxies.md): Proxy na camada de aplicação
    - [Proxies SOCKS](./socks-proxies.md): Proxy na camada de sessão
    - [Detecção de Proxy](./proxy-detection.md): Técnicas de detecção e evasão

    Para uso prático de proxy no Pydoll, veja [Configuração de Proxy](../../features/configuration/proxy.md).

!!! warning "Código Educacional"
    Estas implementações priorizam clareza sobre robustez. Elas não possuem limites de conexão, listas de controle de acesso e muitos caminhos de recuperação de erro que um proxy de produção requer. Não as exponha a redes não confiáveis.

## Proxy HTTP

Um proxy HTTP opera em dois modos. Para HTTP em texto plano, ele recebe a requisição completa (com uma URL em formato absoluto como `GET http://example.com/path HTTP/1.1`), reescreve o request-target para formato de origem (`GET /path HTTP/1.1`), conecta ao servidor destino, encaminha a requisição e retorna a resposta. Para HTTPS, o cliente envia uma requisição `CONNECT host:port`, o proxy abre uma conexão TCP para o destino, responde com `200 Connection Established`, e então retransmite bytes cegamente em ambas as direções sem inspecionar o conteúdo criptografado.

A implementação abaixo lida com ambos os modos. Algumas coisas para notar enquanto lê. O método `_pipe_data` chama `write_eof()` quando um lado fecha, que envia um TCP FIN para o outro lado. Sem isso, o túnel fica pendurado indefinidamente porque o outro `read()` nunca retorna bytes vazios. O caminho de encaminhamento HTTP usa a mesma abordagem de piping em vez de uma única chamada `read()`, porque respostas HTTP podem ser arbitrariamente grandes e um read de tamanho fixo as truncaria silenciosamente. A reescrita do request-target preserva query strings, que `urlparse().path` sozinho descartaria.

```python
import asyncio
import base64
import contextlib
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class HTTPProxy:
    """Proxy HTTP/HTTPS assíncrono com autenticação Basic opcional."""

    def __init__(self, host='0.0.0.0', port=8080, username=None, password=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    async def start(self):
        server = await asyncio.start_server(
            self._handle_client, self.host, self.port
        )
        logger.info(f'HTTP proxy listening on {self.host}:{self.port}')
        async with server:
            await server.serve_forever()

    async def _handle_client(self, reader, writer):
        try:
            request_line = await asyncio.wait_for(
                reader.readline(), timeout=30
            )
            if not request_line:
                return

            parts = request_line.decode('latin-1').split()
            if len(parts) != 3:
                writer.write(b'HTTP/1.1 400 Bad Request\r\n\r\n')
                await writer.drain()
                return

            method, url, _ = parts
            headers = await self._read_headers(reader)

            if not self._check_auth(headers):
                writer.write(
                    b'HTTP/1.1 407 Proxy Authentication Required\r\n'
                    b'Proxy-Authenticate: Basic realm="Proxy"\r\n'
                    b'Content-Length: 0\r\n\r\n'
                )
                await writer.drain()
                return

            if method == 'CONNECT':
                await self._handle_connect(url, reader, writer)
            else:
                await self._handle_http(method, url, headers, reader, writer)
        except Exception as e:
            logger.error(f'Client handler error: {e}')
        finally:
            writer.close()
            await writer.wait_closed()

    async def _read_headers(self, reader):
        headers = {}
        while True:
            line = await reader.readline()
            if line in (b'\r\n', b'\n', b''):
                break
            if b':' in line:
                key, value = line.decode('latin-1').split(':', 1)
                headers[key.strip().lower()] = value.strip()
        return headers

    def _check_auth(self, headers):
        if not self.username:
            return True
        auth = headers.get('proxy-authorization', '')
        if not auth.startswith('Basic '):
            return False
        try:
            decoded = base64.b64decode(auth[6:]).decode('utf-8')
            if ':' not in decoded:
                return False
            user, pwd = decoded.split(':', 1)
            return user == self.username and pwd == self.password
        except Exception:
            return False

    async def _handle_connect(self, target, client_reader, client_writer):
        """Estabelece um túnel TCP cego para HTTPS."""
        # Analisa host:port, lidando com literais IPv6 como [::1]:443
        if target.startswith('['):
            bracket_end = target.index(']')
            host = target[1:bracket_end]
            port = int(target[bracket_end + 2:])
        elif ':' in target:
            host, port_str = target.rsplit(':', 1)
            port = int(port_str)
        else:
            client_writer.write(b'HTTP/1.1 400 Bad Request\r\n\r\n')
            await client_writer.drain()
            return

        try:
            server_reader, server_writer = await asyncio.open_connection(
                host, port
            )
        except OSError as e:
            logger.error(f'CONNECT failed to {host}:{port}: {e}')
            client_writer.write(b'HTTP/1.1 502 Bad Gateway\r\n\r\n')
            await client_writer.drain()
            return

        client_writer.write(b'HTTP/1.1 200 Connection Established\r\n\r\n')
        await client_writer.drain()

        await asyncio.gather(
            self._pipe(client_reader, server_writer),
            self._pipe(server_reader, client_writer),
        )

    async def _handle_http(self, method, url, headers, client_reader, client_writer):
        """Encaminha uma requisição HTTP em texto plano."""
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port or 80

        # Preserva query string no request-target
        path = parsed.path or '/'
        if parsed.query:
            path += f'?{parsed.query}'

        try:
            server_reader, server_writer = await asyncio.open_connection(
                host, port
            )
        except OSError as e:
            logger.error(f'HTTP forward failed to {host}:{port}: {e}')
            client_writer.write(b'HTTP/1.1 502 Bad Gateway\r\n\r\n')
            await client_writer.drain()
            return

        # Reescreve request-target de formato absoluto para formato de origem
        request = f'{method} {path} HTTP/1.1\r\n'

        # Cabeçalho Host deve incluir a porta se for não-padrão
        if port != 80:
            request += f'Host: {host}:{port}\r\n'
        else:
            request += f'Host: {host}\r\n'

        # Remove cabeçalhos hop-by-hop que não devem ser encaminhados
        hop_by_hop = {
            'proxy-authorization', 'proxy-connection',
            'connection', 'keep-alive', 'te', 'trailer', 'upgrade',
        }
        for key, value in headers.items():
            if key not in hop_by_hop:
                request += f'{key}: {value}\r\n'

        # Força Connection: close para que o servidor não mantenha keep-alive,
        # o que impediria o stream de resposta de terminar
        request += 'Connection: close\r\n\r\n'

        server_writer.write(request.encode('latin-1'))

        # Encaminha corpo da requisição se presente
        content_length = int(headers.get('content-length', 0))
        if content_length > 0:
            body = await client_reader.readexactly(content_length)
            server_writer.write(body)

        await server_writer.drain()

        # Retransmite a resposta inteira de volta (não um único read de tamanho fixo)
        while True:
            chunk = await server_reader.read(65536)
            if not chunk:
                break
            client_writer.write(chunk)
            await client_writer.drain()

        server_writer.close()
        await server_writer.wait_closed()

    async def _pipe(self, reader, writer):
        """Retransmissão bidirecional de dados com half-close adequado."""
        try:
            while True:
                data = await reader.read(8192)
                if not data:
                    break
                writer.write(data)
                await writer.drain()
        except (ConnectionResetError, BrokenPipeError, OSError):
            pass
        finally:
            with contextlib.suppress(Exception):
                if writer.can_write_eof():
                    writer.write_eof()
```

Alguns detalhes de protocolo que vale entender. Cabeçalhos HTTP são codificados como ISO-8859-1 (Latin-1), não UTF-8. Latin-1 mapeia cada valor de byte 0-255 para um caractere, então `decode('latin-1')` nunca levanta um `UnicodeDecodeError`, enquanto `decode('utf-8')` quebraria em certos valores de cabeçalho. O cabeçalho `Proxy-Authorization` usa codificação Base64, mas Base64 não é criptografia: as credenciais trafegam em texto claro (ou melhor, codificação trivialmente reversível) a menos que a conexão entre cliente e proxy esteja protegida por TLS. Os cabeçalhos hop-by-hop (`Connection`, `Keep-Alive`, `TE`, `Trailer`, `Upgrade`, `Proxy-Connection`) são destinados à conexão imediata entre dois nós, não para encaminhamento de ponta a ponta. A RFC 9110 Seção 7.6.1 requer que proxies os removam antes de encaminhar.

!!! warning "Risco de SSRF"
    Esta implementação não valida endereços de destino. Um cliente poderia solicitar `CONNECT 127.0.0.1:6379` para alcançar uma instância Redis local, ou `CONNECT 169.254.169.254:80` para acessar metadados de instância cloud (AWS, GCP, Azure). Qualquer proxy exposto a clientes não confiáveis deve validar destinos contra uma lista de negação de faixas privadas e link-local (`127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`, `::1`, `fc00::/7`).

## Proxy SOCKS5

Um proxy SOCKS5 opera em um nível mais baixo que o HTTP. Ele usa um protocolo binário definido na RFC 1928, consistindo de três fases: negociação de método, autenticação opcional e a requisição de conexão. O proxy não analisa HTTP de forma alguma. Uma vez que o túnel é estabelecido, ele retransmite bytes brutos sem entender qual protocolo flui por ele.

A natureza binária do SOCKS5 significa que cada leitura deve receber exatamente o número esperado de bytes. TCP é um protocolo de stream e não garante que `read(4)` retorne 4 bytes: pode retornar 1, 2 ou 3 bytes dependendo das condições de rede. A implementação abaixo usa `readexactly()` do asyncio, que bufferiza internamente até que o número solicitado de bytes chegue ou a conexão feche (levantando `IncompleteReadError`).

```python
import asyncio
import contextlib
import struct
import logging

logger = logging.getLogger(__name__)


class SOCKS5Proxy:
    """Proxy SOCKS5 assíncrono com suporte a CONNECT e autenticação opcional (RFC 1928)."""

    VERSION = 0x05

    def __init__(self, host='0.0.0.0', port=1080, username=None, password=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    async def start(self):
        server = await asyncio.start_server(
            self._handle_client, self.host, self.port
        )
        logger.info(f'SOCKS5 proxy listening on {self.host}:{self.port}')
        async with server:
            await server.serve_forever()

    async def _handle_client(self, reader, writer):
        try:
            if not await self._negotiate_method(reader, writer):
                return
            if self.username and not await self._authenticate(reader, writer):
                return
            await self._handle_request(reader, writer)
        except (asyncio.IncompleteReadError, ConnectionResetError):
            pass
        except Exception as e:
            logger.error(f'SOCKS5 error: {e}')
        finally:
            writer.close()
            await writer.wait_closed()

    async def _negotiate_method(self, reader, writer):
        """Fase 1: cliente oferece métodos de autenticação, servidor escolhe um."""
        version = (await reader.readexactly(1))[0]
        if version != self.VERSION:
            return False

        nmethods = (await reader.readexactly(1))[0]
        methods = await reader.readexactly(nmethods)

        if self.username:
            if 0x02 not in methods:
                writer.write(bytes([self.VERSION, 0xFF]))
                await writer.drain()
                return False
            selected = 0x02
        else:
            selected = 0x00

        writer.write(bytes([self.VERSION, selected]))
        await writer.drain()
        return True

    async def _authenticate(self, reader, writer):
        """Fase 2: sub-negociação de usuário/senha (RFC 1929)."""
        auth_ver = (await reader.readexactly(1))[0]
        if auth_ver != 0x01:
            return False

        ulen = (await reader.readexactly(1))[0]
        username = (await reader.readexactly(ulen)).decode('utf-8')
        plen = (await reader.readexactly(1))[0]
        password = (await reader.readexactly(plen)).decode('utf-8')

        ok = username == self.username and password == self.password
        writer.write(bytes([0x01, 0x00 if ok else 0x01]))
        await writer.drain()
        return ok

    async def _handle_request(self, reader, writer):
        """Fase 3: analisa a requisição CONNECT e estabelece o túnel."""
        header = await reader.readexactly(4)
        version, command, _, atyp = header

        # Analisa endereço de destino baseado no tipo de endereço
        if atyp == 0x01:  # IPv4
            raw = await reader.readexactly(4)
            address = '.'.join(str(b) for b in raw)
        elif atyp == 0x03:  # Nome de domínio
            length = (await reader.readexactly(1))[0]
            address = (await reader.readexactly(length)).decode('ascii')
        elif atyp == 0x04:  # IPv6
            raw = await reader.readexactly(16)
            groups = [f'{raw[i]:02x}{raw[i+1]:02x}' for i in range(0, 16, 2)]
            address = ':'.join(groups)
        else:
            await self._reply(writer, 0x08)
            return

        port = struct.unpack('!H', await reader.readexactly(2))[0]
        logger.info(f'SOCKS5 CONNECT {address}:{port}')

        if command != 0x01:  # Apenas CONNECT é implementado
            await self._reply(writer, 0x07)
            return

        try:
            server_reader, server_writer = await asyncio.open_connection(
                address, port
            )
        except ConnectionRefusedError:
            await self._reply(writer, 0x05)
            return
        except OSError:
            await self._reply(writer, 0x04)
            return

        # BND.ADDR e BND.PORT devem refletir o endereço do socket local.
        # A maioria dos clientes ignora estes para CONNECT, mas preenchê-los
        # corretamente satisfaz a RFC 1928.
        local = server_writer.get_extra_info('sockname')
        await self._reply(writer, 0x00, local[0], local[1])

        await asyncio.gather(
            self._pipe(reader, server_writer),
            self._pipe(server_reader, writer),
        )

    async def _reply(self, writer, status, bind_addr='0.0.0.0', bind_port=0):
        """Envia uma resposta SOCKS5 com o status e endereço vinculado dados."""
        import socket
        try:
            packed_ip = socket.inet_aton(bind_addr)
            atyp = 0x01
        except OSError:
            packed_ip = socket.inet_aton('0.0.0.0')
            atyp = 0x01

        writer.write(bytes([
            self.VERSION, status, 0x00, atyp,
            *packed_ip,
            (bind_port >> 8) & 0xFF, bind_port & 0xFF,
        ]))
        await writer.drain()

    async def _pipe(self, reader, writer):
        try:
            while True:
                data = await reader.read(8192)
                if not data:
                    break
                writer.write(data)
                await writer.drain()
        except (ConnectionResetError, BrokenPipeError, OSError):
            pass
        finally:
            with contextlib.suppress(Exception):
                if writer.can_write_eof():
                    writer.write_eof()
```

Quando o tipo de endereço é `0x03` (nome de domínio), o proxy resolve DNS ele mesmo via `asyncio.open_connection()`. Esta é a propriedade de privacidade definidora do proxy SOCKS5: o cliente envia o nome de domínio em vez de resolvê-lo localmente, o que previne que consultas DNS vazem para a rede local do cliente. Este é o mesmo comportamento em que o Chrome se baseia quando configurado com `--proxy-server=socks5://...`, como discutido em [Proxies SOCKS](./socks-proxies.md).

O método `_reply` preenche `BND.ADDR` e `BND.PORT` com o endereço real do socket local após uma conexão bem-sucedida, como a RFC 1928 requer. Muitas implementações SOCKS5 retornam `0.0.0.0:0` aqui porque a maioria dos clientes ignora esses campos para comandos CONNECT, mas preenchê-los corretamente não custa nada e evita uma violação de protocolo.

## Executando Ambos os Proxies

```python
async def main():
    http_proxy = HTTPProxy(
        port=8080, username='user', password='pass'
    )
    socks5_proxy = SOCKS5Proxy(
        port=1080, username='user', password='pass'
    )
    await asyncio.gather(http_proxy.start(), socks5_proxy.start())

# asyncio.run(main())
```

Você pode testá-los com curl:

```bash
# Proxy HTTP
curl -x http://user:pass@localhost:8080 http://httpbin.org/ip

# HTTPS através de proxy HTTP (túnel CONNECT)
curl -x http://user:pass@localhost:8080 https://httpbin.org/ip

# Proxy SOCKS5
curl --socks5 localhost:1080 --proxy-user user:pass https://httpbin.org/ip
```

## O que o Código Não Lida

Estas implementações omitem várias coisas que proxies de produção lidam. Entender o que está faltando é tão instrutivo quanto entender o que está presente.

Não há limites de conexão. `asyncio.start_server` aceita conexões sem limite, então um único cliente abrindo milhares de conexões esgotaria descritores de arquivo. Proxies de produção usam semáforos ou pools de conexão para limitar concorrência.

Não há validação de destino. Ambos os proxies conectam a qualquer endereço que o cliente solicite, incluindo `127.0.0.1`, `169.254.169.254` (metadados cloud) e faixas de rede interna. Este é um vetor de Server-Side Request Forgery (SSRF). Proxies de produção mantêm listas de negação de faixas de endereços privados e link-local.

Não há logging de tráfego ou métricas. Proxies de produção rastreiam contagem de requisições, bytes transferidos, taxas de erro e percentis de latência, tipicamente exportando para Prometheus ou sistemas similares.

O proxy HTTP não adiciona um cabeçalho `Via`. A RFC 9110 Seção 7.6.3 requer que intermediários adicionem um campo `Via` às mensagens encaminhadas. Isso foi omitido por simplicidade, mas um proxy em conformidade com os padrões deve incluí-lo.

Nenhum dos proxies implementa shutdown gracioso. Quando o servidor para, túneis ativos são terminados abruptamente em vez de serem drenados. Proxies de produção rastreiam conexões ativas e aguardam que completem (com um prazo) antes de encerrar.

## Encadeamento de Proxy

Encadear proxies significa rotear tráfego através de múltiplos proxies em sequência: cliente para proxy A, proxy A para proxy B, proxy B para o servidor destino. Cada proxy na cadeia só conhece seus vizinhos imediatos, não o caminho completo.

O principal caso de uso é distribuir confiança. Se você não confia totalmente em nenhum provedor de proxy individual, encadear dois provedores significa que nenhum deles vê tanto seu IP real quanto seu destino. O tradeoff é latência: cada salto adiciona seu próprio tempo de setup de conexão e atraso de encaminhamento. Um único proxy tipicamente adiciona 50 a 100ms de overhead. Dois proxies aproximadamente dobram isso, e três proxies podem empurrar o overhead total além de 300ms.

Além de dois saltos, o ganho marginal de privacidade diminui enquanto latência e probabilidade de falha aumentam. A maioria das configurações práticas usa um ou dois proxies. O Tor usa três relays (guard, middle, exit) porque seu modelo de ameaça assume que alguns relays estão comprometidos, mas o Tor aceita a penalidade de latência como um tradeoff de design explícito.

```
Client --> Proxy A (SOCKS5) --> Proxy B (SOCKS5) --> Target
           vê: IP do cliente       vê: IP do Proxy A
           vê: endereço do Proxy B  vê: endereço do destino
```

Encadear um proxy SOCKS5 através de outro proxy SOCKS5 funciona fazendo o proxy A tratar o proxy B como o destino. O cliente conecta ao proxy A e envia uma requisição CONNECT para o endereço do proxy B. Uma vez que esse túnel é estabelecido, o cliente envia um segundo handshake SOCKS5 através do túnel, desta vez solicitando o destino real. O proxy A vê tráfego fluindo para o proxy B mas não pode lê-lo se a conexão interna estiver criptografada.

## Referências

- RFC 1928: SOCKS Protocol Version 5 - https://datatracker.ietf.org/doc/html/rfc1928
- RFC 1929: Username/Password Authentication for SOCKS V5 - https://datatracker.ietf.org/doc/html/rfc1929
- RFC 9110: HTTP Semantics - https://www.rfc-editor.org/rfc/rfc9110.html
- RFC 9112: HTTP/1.1 - https://www.rfc-editor.org/rfc/rfc9112.html
- OWASP SSRF Prevention Cheat Sheet - https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html
- mitmproxy (Python HTTPS intercepting proxy) - https://mitmproxy.org/
