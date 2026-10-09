# Construindo um servidor proxy

Para entender o que um proxy faz, construa um. Esta página implementa um proxy HTTP e um proxy SOCKS5 do zero em Python com asyncio, para você ver como cada byte é interpretado, onde ficam os limites de segurança, e por que os softwares de proxy reais fazem as escolhas que fazem. Para usar um proxy com o Pydoll em vez de construir um, veja [Proxies](../../guides/proxies.md); o Pydoll também traz um `SOCKS5Forwarder` em `pydoll.utils`, então você não precisa construir o caso de SOCKS5 autenticado você mesmo.

!!! warning "Código educacional"
    Estas implementações favorecem clareza em vez de robustez. Elas não têm limites de conexão, controle de acesso, e muitos caminhos de recuperação de erro que um proxy de produção precisa. Não os exponha a redes não confiáveis.

## Proxy HTTP

Um proxy HTTP opera em dois modos. Para HTTP em texto claro, ele recebe a requisição completa (com uma URL em forma absoluta como `GET http://example.com/path HTTP/1.1`), reescreve o request-target para a forma de origem (`GET /path HTTP/1.1`), conecta ao servidor de destino, encaminha a requisição, e canaliza a resposta de volta. Para HTTPS, o cliente envia uma requisição `CONNECT host:port`, o proxy abre uma conexão TCP ao destino, responde com `200 Connection Established`, e então repassa bytes às cegas nos dois sentidos sem inspecionar o conteúdo criptografado.

A implementação abaixo lida com os dois modos. Algumas coisas para notar enquanto você lê. O método `_pipe_data` chama `write_eof()` quando um lado fecha, o que envia um TCP FIN para o outro lado. Sem isso, o túnel trava indefinidamente porque o outro `read()` nunca retorna bytes vazios. O caminho de encaminhamento HTTP usa a mesma abordagem de canalização em vez de uma única chamada `read()`, porque respostas HTTP podem ser arbitrariamente grandes e um read de tamanho fixo as truncaria silenciosamente. A reescrita do request-target preserva query strings, que `urlparse().path` sozinho descartaria.

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
        # Faz parse de host:port, lidando com literais IPv6 como [::1]:443
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
        """Encaminha uma requisição HTTP em texto claro."""
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port or 80

        # Preserva a query string no request-target
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

        # Reescreve o request-target da forma absoluta para a forma de origem
        request = f'{method} {path} HTTP/1.1\r\n'

        # O header Host precisa incluir a porta se ela for não padrão
        if port != 80:
            request += f'Host: {host}:{port}\r\n'
        else:
            request += f'Host: {host}\r\n'

        # Remove os headers hop-by-hop que não devem ser encaminhados
        hop_by_hop = {
            'proxy-authorization', 'proxy-connection',
            'connection', 'keep-alive', 'te', 'trailer', 'upgrade',
        }
        for key, value in headers.items():
            if key not in hop_by_hop:
                request += f'{key}: {value}\r\n'

        # Força Connection: close para o servidor não manter keep-alive,
        # o que impediria o stream de resposta de terminar
        request += 'Connection: close\r\n\r\n'

        server_writer.write(request.encode('latin-1'))

        # Encaminha o corpo da requisição se presente
        content_length = int(headers.get('content-length', 0))
        if content_length > 0:
            body = await client_reader.readexactly(content_length)
            server_writer.write(body)

        await server_writer.drain()

        # Canaliza a resposta inteira de volta (não um único read de tamanho fixo)
        while True:
            chunk = await server_reader.read(65536)
            if not chunk:
                break
            client_writer.write(chunk)
            await client_writer.drain()

        server_writer.close()
        await server_writer.wait_closed()

    async def _pipe(self, reader, writer):
        """Relay de dados bidirecional com half-close adequado."""
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

Alguns detalhes de protocolo que vale entender. Headers HTTP são codificados como ISO-8859-1 (Latin-1), não UTF-8. O Latin-1 mapeia todo valor de byte 0-255 para um caractere, então `decode('latin-1')` nunca levanta um `UnicodeDecodeError`, enquanto `decode('utf-8')` quebraria em certos valores de header. O header `Proxy-Authorization` usa codificação Base64, mas Base64 não é criptografia: as credenciais viajam em texto claro (ou melhor, em codificação trivialmente reversível) a menos que a conexão entre cliente e proxy seja ela mesma protegida por TLS. Os headers hop-by-hop (`Connection`, `Keep-Alive`, `TE`, `Trailer`, `Upgrade`, `Proxy-Connection`) são destinados à conexão imediata entre dois nós, não ao encaminhamento ponta a ponta. A RFC 9110 Seção 7.6.1 exige que os proxies os removam antes de encaminhar.

!!! warning "Risco de SSRF"
    Esta implementação não valida endereços de destino. Um cliente poderia requisitar `CONNECT 127.0.0.1:6379` para alcançar uma instância local do Redis, ou `CONNECT 169.254.169.254:80` para acessar o metadata da instância na nuvem (AWS, GCP, Azure). Qualquer proxy exposto a clientes não confiáveis precisa validar destinos contra uma deny list de faixas privadas e link-local (`127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`, `::1`, `fc00::/7`).

## Proxy SOCKS5

Um proxy SOCKS5 opera em um nível mais baixo que o HTTP. Ele usa um protocolo binário definido na RFC 1928, que consiste em três fases: negociação de método, autenticação opcional, e a requisição de conexão. O proxy não faz parse de HTTP de forma alguma. Uma vez que o túnel está estabelecido, ele repassa bytes crus sem entender qual protocolo flui por ele.

A natureza binária do SOCKS5 significa que cada read precisa receber exatamente o número esperado de bytes. O TCP é um protocolo de stream e não garante que `read(4)` retorne 4 bytes: pode retornar 1, 2 ou 3 bytes dependendo das condições da rede. A implementação abaixo usa `readexactly()` do asyncio, que faz buffer internamente até o número requisitado de bytes chegar ou a conexão fechar (levantando `IncompleteReadError`).

```python
import asyncio
import contextlib
import struct
import logging

logger = logging.getLogger(__name__)


class SOCKS5Proxy:
    """Proxy SOCKS5 assíncrono suportando CONNECT com auth opcional (RFC 1928)."""

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
        """Fase 1: o cliente oferece métodos de autenticação, o servidor escolhe um."""
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
        """Fase 2: subnegociação de usuário/senha (RFC 1929)."""
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
        """Fase 3: faz parse da requisição CONNECT e estabelece o túnel."""
        header = await reader.readexactly(4)
        version, command, _, atyp = header

        # Faz parse do endereço de destino com base no tipo de endereço
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

        if command != 0x01:  # Apenas CONNECT está implementado
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
        # A maioria dos clientes ignora esses campos para CONNECT, mas preenchê-los
        # corretamente satisfaz a RFC 1928.
        local = server_writer.get_extra_info('sockname')
        await self._reply(writer, 0x00, local[0], local[1])

        await asyncio.gather(
            self._pipe(reader, server_writer),
            self._pipe(server_reader, writer),
        )

    async def _reply(self, writer, status, bind_addr='0.0.0.0', bind_port=0):
        """Envia uma resposta SOCKS5 com o status e o endereço vinculado dados."""
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

Quando o tipo de endereço é `0x03` (nome de domínio), o proxy resolve o DNS ele mesmo via `asyncio.open_connection()`. Esta é a propriedade de privacidade que define o proxying SOCKS5: o cliente envia o nome de domínio em vez de resolvê-lo localmente, o que impede que consultas DNS vazem para a rede local do cliente. Este é o mesmo comportamento em que o Chrome se apoia quando configurado com `--proxy-server=socks5://...`, como discutido em [Proxies SOCKS](./socks-proxies.md).

O método `_reply` preenche `BND.ADDR` e `BND.PORT` com o endereço real do socket local após uma conexão bem-sucedida, como a RFC 1928 exige. Muitas implementações de SOCKS5 retornam `0.0.0.0:0` aqui porque a maioria dos clientes ignora esses campos para comandos CONNECT, mas preenchê-los corretamente não custa nada e evita uma violação de protocolo.

## Rodando os dois proxies

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

# HTTPS através do proxy HTTP (túnel CONNECT)
curl -x http://user:pass@localhost:8080 https://httpbin.org/ip

# Proxy SOCKS5
curl --socks5 localhost:1080 --proxy-user user:pass https://httpbin.org/ip
```

## O que o código não trata

Estas implementações omitem várias coisas que proxies de produção tratam. Entender o que está faltando é tão instrutivo quanto entender o que está presente.

Não há limites de conexão. `asyncio.start_server` aceita conexões sem limite, então um único cliente abrindo milhares de conexões esgotaria os file descriptors. Proxies de produção usam semáforos ou pools de conexão para limitar a concorrência.

Não há validação de destino. Ambos os proxies conectam a qualquer endereço que o cliente requisitar, incluindo `127.0.0.1`, `169.254.169.254` (metadata da nuvem), e faixas de rede internas. Este é um vetor de Server-Side Request Forgery (SSRF). Proxies de produção mantêm deny lists de faixas de endereços privados e link-local.

Não há logging de tráfego nem métricas. Proxies de produção rastreiam contagens de requisições, bytes transferidos, taxas de erro, e percentis de latência, tipicamente exportando para Prometheus ou sistemas similares.

O proxy HTTP não adiciona um header `Via`. A RFC 9110 Seção 7.6.3 exige que intermediários acrescentem um campo `Via` às mensagens encaminhadas. Isso foi omitido por simplicidade, mas um proxy em conformidade com o padrão precisa incluí-lo.

Nenhum dos proxies implementa desligamento gracioso. Quando o servidor para, os túneis ativos são terminados abruptamente em vez de serem drenados. Proxies de produção rastreiam conexões ativas e esperam que elas terminem (com um prazo) antes de desligar.

## Encadeamento de proxies

Encadear proxies significa rotear o tráfego através de múltiplos proxies em sequência: cliente para o proxy A, proxy A para o proxy B, proxy B para o servidor de destino. Cada proxy na cadeia conhece apenas seus vizinhos imediatos, não o caminho completo.

O principal caso de uso é distribuir a confiança. Se você não confia plenamente em nenhum provedor de proxy isolado, encadear dois provedores significa que nenhum deles vê ao mesmo tempo seu IP real e seu destino. O trade-off é a latência: cada salto adiciona seu próprio tempo de setup de conexão e atraso de encaminhamento. Um único proxy tipicamente adiciona de 50 a 100ms de overhead. Dois proxies grosso modo dobram isso, e três proxies podem empurrar o overhead total para além de 300ms.

Além de dois saltos, o ganho marginal de privacidade diminui enquanto a latência e a probabilidade de falha aumentam. A maioria das configurações práticas usa um ou dois proxies. O Tor usa três relays (guard, middle, exit) porque seu modelo de ameaça assume que alguns relays estão comprometidos, mas o Tor aceita a penalidade de latência como um trade-off de design explícito.

```
Client --> Proxy A (SOCKS5) --> Proxy B (SOCKS5) --> Target
           sees: client IP          sees: Proxy A IP
           sees: Proxy B addr       sees: target addr
```

Encadear um proxy SOCKS5 através de outro proxy SOCKS5 funciona fazendo o proxy A tratar o proxy B como o destino. O cliente conecta ao proxy A e envia uma requisição CONNECT para o endereço do proxy B. Uma vez que esse túnel está estabelecido, o cliente envia um segundo handshake SOCKS5 através do túnel, desta vez requisitando o destino real. O proxy A vê o tráfego fluindo para o proxy B, mas não consegue lê-lo se a conexão interna estiver criptografada.

## Relacionado

- [Fundamentos de rede](network-fundamentals.md): as camadas pelas quais este código move bytes.
- [Proxies HTTP/HTTPS](http-proxies.md) e [Proxies SOCKS](socks-proxies.md): os protocolos implementados aqui.
- [Proxies](../../guides/proxies.md): configurando um proxy no Pydoll em vez de construir um.

## Referências

- RFC 1928: SOCKS Protocol Version 5 - https://datatracker.ietf.org/doc/html/rfc1928
- RFC 1929: Username/Password Authentication for SOCKS V5 - https://datatracker.ietf.org/doc/html/rfc1929
- RFC 9110: HTTP Semantics - https://www.rfc-editor.org/rfc/rfc9110.html
- RFC 9112: HTTP/1.1 - https://www.rfc-editor.org/rfc/rfc9112.html
- OWASP SSRF Prevention Cheat Sheet - https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html
- mitmproxy (Python HTTPS intercepting proxy) - https://mitmproxy.org/
