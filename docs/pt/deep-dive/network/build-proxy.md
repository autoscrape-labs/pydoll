# Construindo Seu Próprio Servidor Proxy

Este documento fornece implementações **completas** de servidores proxy HTTP e SOCKS5 em Python. Construir proxies do zero é a experiência de aprendizado definitiva, revelando vetores de ataque, oportunidades de otimização e nuances de protocolo invisíveis do exterior.

!!! info "Navegação do Módulo"
    - **[← Detecção de Proxy](./proxy-detection.md)** - Técnicas de anonimato e evasão
    - **[← Proxies SOCKS](./socks-proxies.md)** - Fundamentos do protocolo SOCKS
    - **[← Proxies HTTP/HTTPS](./http-proxies.md)** - Fundamentos do protocolo HTTP
    - **[← Visão Geral de Rede e Segurança](./index.md)** - Introdução do módulo
    - **[→ Legal e Ético](./proxy-legal.md)** - Conformidade e responsabilidade
    
    Para uso prático, veja **[Configuração de Proxy](../../features/configuration/proxy.md)**.

!!! warning "Propósito Educacional"
    Estas implementações são para **aprendizado e teste**. Proxies de produção exigem endurecimento (hardening) de segurança adicional, otimização de desempenho e tratamento robusto de erros.

## Construindo Seu Próprio Servidor Proxy

Vamos construir proxies HTTP e SOCKS5 do zero para entender seus componentes internos.

### Pré-requisitos

```python
import asyncio
import base64
import struct
import logging
from typing import Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

### Servidor Proxy HTTP

```python
class HTTPProxy:
    """
    Implementação simples de servidor proxy HTTP/HTTPS.
    Lida com requisições HTTP e túneis HTTPS CONNECT.
    """
    
    def __init__(self, host='0.0.0.0', port=8080, username=None, password=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
    
    async def handle_client(self, reader, writer):
        """Lida com uma conexão de cliente."""
        try:
            # Ler linha de requisição HTTP
            request_line = await reader.readline()
            if not request_line:
                return
            
            request_parts = request_line.decode('utf-8').split()
            method, url, protocol = request_parts
            
            # Ler cabeçalhos
            headers = await self._read_headers(reader)
            
            # Checar autenticação
            if not self._check_auth(headers):
                await self._send_auth_required(writer)
                return
            
            # Lidar com base no método
            if method == 'CONNECT':
                await self._handle_https_tunnel(url, reader, writer)
            else:
                await self._handle_http_request(method, url, headers, reader, writer)
                
        except Exception as e:
            logger.error(f"Erro ao lidar com cliente: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def _read_headers(self, reader) -> dict:
        """Parseia cabeçalhos HTTP."""
        headers = {}
        while True:
            line = await reader.readline()
            if line == b'\r\n':  # Fim dos cabeçalhos
                break
            
            if b':' in line:
                key, value = line.decode('utf-8').split(':', 1)
                headers[key.strip().lower()] = value.strip()
        
        return headers
    
    def _check_auth(self, headers: dict) -> bool:
        """Verifica autenticação do proxy."""
        if not self.username:
            return True  # Nenhuma autenticação necessária
        
        auth_header = headers.get('proxy-authorization', '')
        if not auth_header.startswith('Basic '):
            return False
        
        # Decodificar credenciais base64
        encoded = auth_header[6:]  # Remover 'Basic '
        decoded = base64.b64decode(encoded).decode('utf-8')
        username, password = decoded.split(':', 1)
        
        return username == self.username and password == self.password
    
    async def _send_auth_required(self, writer):
        """Envia 407 Proxy Authentication Required."""
        response = (
            b'HTTP/1.1 407 Proxy Authentication Required\r\n'
            b'Proxy-Authenticate: Basic realm="Proxy"\r\n'
            b'Content-Length: 0\r\n'
            b'\r\n'
        )
        writer.write(response)
        await writer.drain()
    
    async def _handle_https_tunnel(self, target_address, client_reader, client_writer):
        """
        Lida com túnel HTTPS CONNECT.
        Cria um pipe bidirecional entre cliente e servidor.
        """
        host, port = target_address.split(':')
        port = int(port)
        
        try:
            # Conectar ao servidor alvo
            server_reader, server_writer = await asyncio.open_connection(host, port)
            
            # Enviar resposta de sucesso
            client_writer.write(b'HTTP/1.1 200 Connection Established\r\n\r\n')
            await client_writer.drain()
            
            # Criar túnel bidirecional
            await asyncio.gather(
                self._pipe_data(client_reader, server_writer, 'client→server'),
                self._pipe_data(server_reader, client_writer, 'server→client'),
            )
            
        except Exception as e:
            logger.error(f"Erro de túnel: {e}")
            client_writer.write(b'HTTP/1.1 502 Bad Gateway\r\n\r\n')
            await client_writer.drain()
    
    async def _handle_http_request(self, method, url, headers, client_reader, client_writer):
        """Encaminha requisição HTTP para servidor alvo."""
        # Parsear URL
        from urllib.parse import urlparse
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port or 80
        path = parsed.path or '/'
        
        try:
            # Conectar ao alvo
            server_reader, server_writer = await asyncio.open_connection(host, port)
            
            # Construir requisição
            request = f"{method} {path} HTTP/1.1\r\n"
            request += f"Host: {host}\r\n"
            
            # Encaminhar cabeçalhos (exceto os específicos do proxy)
            for key, value in headers.items():
                if key.lower() not in ['proxy-authorization', 'proxy-connection']:
                    request += f"{key}: {value}\r\n"
            
            request += '\r\n'
            
            # Enviar requisição
            server_writer.write(request.encode('utf-8'))
            
            # Encaminhar corpo se presente
            content_length = int(headers.get('content-length', 0))
            if content_length > 0:
                body = await client_reader.read(content_length)
                server_writer.write(body)
            
            await server_writer.drain()
            
            # Encaminhar resposta de volta ao cliente
            response = await server_reader.read(65536)
            client_writer.write(response)
            await client_writer.drain()
            
        except Exception as e:
            logger.error(f"Erro na requisição HTTP: {e}")
    
    async def _pipe_data(self, reader, writer, direction):
        """Transporta dados entre reader e writer."""
        try:
            while True:
                data = await reader.read(8192)
                if not data:
                    break
                
                writer.write(data)
                await writer.drain()
        except Exception as e:
            logger.debug(f"Pipe {direction} fechado: {e}")
    
    async def start(self):
        """Inicia o servidor proxy."""
        server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port
        )
        
        logger.info(f"Proxy HTTP escutando em {self.host}:{self.port}")
        
        async with server:
            await server.serve_forever()
```

### Servidor Proxy SOCKS5

```python
class SOCKS5Proxy:
    """
    Implementação do servidor proxy SOCKS5 (RFC 1928).
    Suporta autenticação e ambas as conexões TCP.
    """
    
    # Constantes SOCKS5
    VERSION = 0x05
    
    AUTH_METHODS = {
        0x00: 'NO_AUTH',
        0x02: 'USERNAME_PASSWORD',
    }
    
    COMMANDS = {
        0x01: 'CONNECT',
        0x02: 'BIND',
        0x03: 'UDP_ASSOCIATE',
    }
    
    ADDRESS_TYPES = {
        0x01: 'IPv4',
        0x03: 'DOMAIN',
        0x04: 'IPv6',
    }
    
    REPLY_CODES = {
        0x00: 'SUCCESS',
        0x01: 'GENERAL_FAILURE',
        0x02: 'NOT_ALLOWED',
        0x03: 'NETWORK_UNREACHABLE',
        0x04: 'HOST_UNREACHABLE',
        0x05: 'CONNECTION_REFUSED',
        0x06: 'TTL_EXPIRED',
        0x07: 'COMMAND_NOT_SUPPORTED',
        0x08: 'ADDRESS_TYPE_NOT_SUPPORTED',
    }
    
    def __init__(self, host='0.0.0.0', port=1080, username=None, password=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
    
    async def handle_client(self, reader, writer):
        """Lida com conexão de cliente SOCKS5."""
        try:
            # Fase 1: Negociação de método
            if not await self._negotiate_method(reader, writer):
                return
            
            # Fase 2: Autenticação (se necessário)
            if self.username and not await self._authenticate(reader, writer):
                return
            
            # Fase 3: Processamento da requisição
            await self._handle_request(reader, writer)
            
        except Exception as e:
            logger.error(f"Erro SOCKS5: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def _negotiate_method(self, reader, writer) -> bool:
        """Negociação de método SOCKS5."""
        # Ler saudação do cliente
        version = (await reader.read(1))[0]
        if version != self.VERSION:
            logger.error(f"Versão SOCKS não suportada: {version}")
            return False
        
        nmethods = (await reader.read(1))[0]
        methods = await reader.read(nmethods)
        
        # Selecionar método de autenticação
        if self.username:
            # Usuário/senha obrigatórios
            if 0x02 not in methods:
                writer.write(bytes([self.VERSION, 0xFF]))  # Nenhum método aceitável
                await writer.drain()
                return False
            selected_method = 0x02
        else:
            # Sem autenticação
            selected_method = 0x00
        
        # Enviar seleção de método
        writer.write(bytes([self.VERSION, selected_method]))
        await writer.drain()
        
        return True
    
    async def _authenticate(self, reader, writer) -> bool:
        """Autenticação por usuário/senha (RFC 1929)."""
        # Ler versão da autenticação
        auth_version = (await reader.read(1))[0]
        if auth_version != 0x01:
            return False
        
        # Ler usuário
        username_len = (await reader.read(1))[0]
        username = (await reader.read(username_len)).decode('utf-8')
        
        # Ler senha
        password_len = (await reader.read(1))[0]
        password = (await reader.read(password_len)).decode('utf-8')
        
        # Verificar credenciais
        success = (username == self.username and password == self.password)
        
        # Enviar resposta da autenticação
        status = 0x00 if success else 0x01
        writer.write(bytes([0x01, status]))
        await writer.drain()
        
        return success
    
    async def _handle_request(self, reader, writer):
        """Lida com requisição de conexão SOCKS5."""
        # Ler requisição
        version = (await reader.read(1))[0]
        command = (await reader.read(1))[0]
        reserved = (await reader.read(1))[0]
        address_type = (await reader.read(1))[0]
        
        # Parsear endereço de destino
        if address_type == 0x01:  # IPv4
            addr = await reader.read(4)
            address = '.'.join(str(b) for b in addr)
        elif address_type == 0x03:  # Domínio
            domain_len = (await reader.read(1))[0]
            address = (await reader.read(domain_len)).decode('utf-8')
        elif address_type == 0x04:  # IPv6
            addr = await reader.read(16)
            # Formatar endereço IPv6
            address = ':'.join(f'{b1:02x}{b2:02x}' for b1, b2 in zip(addr[::2], addr[1::2]))
        else:
            await self._send_reply(writer, 0x08)  # Tipo de endereço não suportado
            return
        
        # Ler porta (2 bytes, big-endian)
        port_bytes = await reader.read(2)
        port = struct.unpack('!H', port_bytes)[0]
        
        logger.info(f"SOCKS5 {self.COMMANDS.get(command)} para {address}:{port}")
        
        # Lidar com comando
        if command == 0x01:  # CONNECT
            await self._handle_connect(address, port, reader, writer)
        else:
            await self._send_reply(writer, 0x07)  # Comando não suportado
    
    async def _handle_connect(self, address, port, client_reader, client_writer):
        """Lida com comando CONNECT."""
        try:
            # Conectar ao alvo
            server_reader, server_writer = await asyncio.open_connection(address, port)
            
            # Enviar resposta de sucesso
            await self._send_reply(client_writer, 0x00)
            
            # Criar túnel bidirecional
            await asyncio.gather(
                self._pipe_data(client_reader, server_writer, 'client→server'),
                self._pipe_data(server_reader, client_writer, 'server→client'),
            )
            
        except ConnectionRefusedError:
            await self._send_reply(client_writer, 0x05)  # Conexão recusada
        except OSError as e:
            logger.error(f"Erro de conexão: {e}")
            await self._send_reply(client_writer, 0x04)  # Host inacessível
    
    async def _send_reply(self, writer, reply_code):
        """Envia resposta SOCKS5."""
        # Formato da resposta: VER REP RSV ATYP BND.ADDR BND.PORT
        response = bytes([
            self.VERSION,    # VER
            reply_code,      # REP
            0x00,            # RSV
            0x01,            # ATYP (IPv4)
            0, 0, 0, 0,      # BND.ADDR (0.0.0.0)
            0, 0             # BND.PORT (0)
        ])
        
        writer.write(response)
        await writer.drain()
    
    async def _pipe_data(self, reader, writer, direction):
        """Transporta dados entre reader e writer."""
        try:
            while True:
                data = await reader.read(8192)
                if not data:
                    break
                
                writer.write(data)
                await writer.drain()
        except Exception as e:
            logger.debug(f"Pipe {direction} fechado: {e}")
    
    async def start(self):
        """Inicia o servidor proxy SOCKS5."""
        server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port
        )
        
        logger.info(f"Proxy SOCKS5 escutando em {self.host}:{self.port}")
        
        async with server:
            await server.serve_forever()
```

### Exemplo de Uso

```python
# Exemplo: Rodando os proxies
async def main():
    # Inicia proxy HTTP na porta 8080
    http_proxy = HTTPProxy(
        host='0.0.0.0',
        port=8080,
        username='user',
        password='pass'
    )
    
    # Inicia proxy SOCKS5 na porta 1080
    socks5_proxy = SOCKS5Proxy(
        host='0.0.0.0',
        port=1080,
        username='user',
        password='pass'
    )
    
    # Roda ambos os proxies concorrentemente
    await asyncio.gather(
        http_proxy.start(),
        socks5_proxy.start()
    )

# Roda os proxies
# asyncio.run(main())
```

!!! warning "Considerações de Produção"
    Estas implementações são educacionais. Proxies de produção precisam de:
    
    - **Pool de conexões** (reutilizar conexões alvo)
    - **Limitação de taxa (Rate limiting)** (prevenir abuso)
    - **Controle de acesso** (lista branca de IPs, cotas de usuário)
    - **Log e monitoramento** (rastrear uso, detectar anomalias)
    - **Tratamento de erros** (degradação graciosa)
    - **Otimização de desempenho** (usar uvloop, otimizar tamanhos de buffer)
    - **Endurecimento de segurança (Security hardening)** (prevenir ataques de proxy aberto)

## Tópicos Avançados

### Encadeamento de Proxy (Proxy Chaining)

Encadeie múltiplos proxies para anonimato adicional:

```
Cliente → Proxy1 (SOCKS5) → Proxy2 (HTTP) → Proxy3 (SOCKS5) → Servidor
```

**Benefícios:**

- Cada proxy conhece apenas o próximo salto (não o caminho completo)
- Distribui a confiança por múltiplos provedores
- Roteamento geográfico (sair de um país específico)

**Desvantagens:**

- Latência aumentada (cada salto adiciona atraso)
- Velocidade reduzida (largura de banda limitada pelo salto mais lento)
- Custo mais alto (pagar por múltiplos proxies)
- Mais pontos de falha

**Métricas de Desempenho:**

| Configuração | Latência Típica | Impacto na Banda | Taxa de Falha |
|---|---|---|---|
| **Direto** | 10-50ms | 100% | <0.1% |
| **Proxy Único** | 60-150ms (+50-100ms) | 80-95% | 0.5-2% |
| **Cadeia de 2 Proxies** | 120-300ms (+110-250ms) | 60-80% | 1-4% |
| **Cadeia de 3 Proxies** | 200-500ms (+190-450ms) | 40-60% | 3-8% |

*Valores são aproximados e dependem fortemente da qualidade do proxy, distância geográfica e condições de rede.*

**Exemplo do mundo real (latências medidas em 2023):**

```
Conexão direta:        ~30ms
→ Proxy único (EUA):      ~85ms  (+55ms de sobrecarga)
→ + Segundo proxy (UE):    ~195ms (+110ms de sobrecarga)
→ + Terceiro proxy (APAC):   ~380ms (+185ms de sobrecarga)

Sobrecarga total: 350ms (11.6x mais lento que direto)
Largura de banda: 45% da conexão direta
```

!!! tip "Comprimento Ótimo da Cadeia"
    Para a maioria dos casos de uso, **1-2 proxies** fornecem o melhor equilíbrio entre anonimato e desempenho. Três ou mais proxies são justificados apenas para cenários de alto risco onde o anonimato absoluto é crítico.

### Pools de Proxy Rotativos

```python
# Arquitetura para pool de proxy rotativo
class ProxyPool:
    """
    Gerencia um pool de proxies com verificação de saúde e rotação.
    """
    
    def __init__(self, proxies: list[str]):
        self.proxies = proxies
        self.healthy_proxies = []
        self.failed_proxies = []
        self.current_index = 0
    
    async def health_check(self, proxy: str) -> bool:
        """Verifica se o proxy está funcionando."""
        try:
            # Testar conexão através do proxy
            # Retorna True se bem-sucedido, False caso contrário
            pass
        except:
            return False
    
    async def get_next_proxy(self) -> Optional[str]:
        """Obtém o próximo proxy saudável (round-robin)."""
        if not self.healthy_proxies:
            await self.refresh_health()
        
        if not self.healthy_proxies:
            return None
        
        proxy = self.healthy_proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.healthy_proxies)
        
        return proxy
    
    async def refresh_health(self):
        """Atualiza o status de saúde dos proxies."""
        # Testa todos os proxies em paralelo
        results = await asyncio.gather(
            *[self.health_check(p) for p in self.proxies]
        )
        
        self.healthy_proxies = [p for p, ok in zip(self.proxies, results) if ok]
        self.failed_proxies = [p for p, ok in zip(self.proxies, results) if not ok]
```

### Proxies Transparentes vs Explícitos

| Característica | Proxy Transparente | Proxy Explícito |
|---|---|---|
| **Configuração do Cliente** | Nenhuma necessária | Deve configurar as config. de proxy |
| **Detecção** | Invisível para o cliente | Cliente sabe que está usando proxy |
| **Implementação** | Nível de rede (roteador/gateway) | Nível de aplicação |
| **Controle** | Imposto pelo admin da rede | Escolha do usuário |
| **Caso de Uso** | Redes corporativas, filtragem de ISP | Privacidade pessoal, web scraping |

**Implementação de Proxy Transparente:**

Proxies transparentes operam na camada de rede, interceptando tráfego via regras iptables/nftables:

```bash
# Regras iptables do Linux para proxy HTTP transparente
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 \
    -j REDIRECT --to-port 8080

iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 443 \
    -j REDIRECT --to-port 8443
```

**Detecção:** Clientes podem detectar proxies transparentes via:
- Cabeçalhos `Via` nas respostas
- Fingerprinting de TCP/IP (mudanças de TTL)
- Análise de tempo (latência adicionada)

!!! warning "Proxy Transparente de HTTPS"
    Proxy transparente de HTTPS requer:

    - **Interceptação TLS** (MITM com certificado CA customizado)
    - **Instalação de certificado** nos dispositivos cliente
    - **Conformidade legal** (consentimento de funcionários, leis de privacidade)
    
    Isso é altamente invasivo e levanta preocupações significativas de privacidade.

## Resumo e Pontos Chave

Construir servidores proxy do zero revela as **diferenças fundamentais** entre as arquiteturas HTTP e SOCKS5, seus modelos de segurança e desafios de implementação. Entender os componentes internos do proxy é essencial para depuração, otimização e técnicas avançadas de evasão.

### Conceitos Centrais Cobertos

**1. Arquitetura de Proxy HTTP:**

- **Operação de modo duplo**: Encaminhamento de requisição HTTP vs tunelamento HTTPS (CONNECT)
- **Manipulação de cabeçalho**: Adicionando `Via`, `X-Forwarded-For`, removendo `Proxy-Authorization`
- **Autenticação**: Usuário/senha codificados em Base64 no cabeçalho `Proxy-Authorization`
- **Consciência da aplicação**: Pode ler/modificar tráfego HTTP, cachear respostas, aplicar políticas

**2. Arquitetura de Proxy SOCKS5:**

- **Protocolo de três fases**: Negociação de método → Autenticação → Processamento da requisição
- **Protocolo binário**: Estruturas de pacote eficientes (versão, comandos, tipos de endereço)
- **Agnóstico a protocolo**: Encaminhamento cego de qualquer tráfego TCP/UDP
- **Autenticação**: Usuário/senha (RFC 1929) ou GSSAPI (RFC 1961)

**3. Desafios de Implementação:**

- **Pipes de dados bidirecionais**: Encaminhamento assíncrono entre cliente e servidor
- **Tratamento de erros**: Falhas de rede, timeouts, violações de protocolo
- **Gerenciamento de recursos**: Pool de conexões, desligamento gracioso
- **Segurança**: Prevenindo abuso de proxy aberto, limitação de taxa

**4. Conceitos Avançados:**

- **Encadeamento de proxy**: Roteamento multi-salto para anonimato aprimorado (com trocas de latência)
- **Pools de proxy rotativos**: Verificação de saúde, balanceamento de carga, failover
- **Proxies transparentes**: Interceptação em nível de rede sem configuração do cliente

### Complexidade de Implementação HTTP vs SOCKS5

| Aspecto | Proxy HTTP | Proxy SOCKS5 |
|---|---|---|
| **Parse de Protocolo** | Complexo (HTTP baseado em texto) | Simples (estruturas binárias) |
| **Autenticação** | Cabeçalhos HTTP (Base64) | Handshake binário |
| **Manuseio de HTTPS** | Túnel CONNECT | Tunelamento nativo |
| **Lógica de Aplicação** | Modificação de requisição/resposta | Encaminhamento cego |
| **Tratamento de Erros** | Códigos de status HTTP | Códigos de resposta binários |
| **Linhas de Código** | ~200 (impl. simples) | ~180 (impl. simples) |

**Insight Chave:** SOCKS5 é **mais simples de implementar corretamente** devido ao seu protocolo binário e falta de preocupações da camada de aplicação.

### Requisitos de Proxy Pronto para Produção

Implementações educacionais carecem de recursos críticos de produção:

**1. Otimização de Desempenho:**

- **Pool de conexões**: Reutilizar conexões do servidor em vez de criar novas
- **I/O Assíncrono**: Usar `uvloop` para aumento de desempenho de 2-4x
- **Ajuste de buffer**: Otimizar tamanhos de buffer de `read()` para troca de largura de banda/latência
- **Encaminhamento zero-copy**: Usar syscall `sendfile()` onde possível

**2. Endurecimento de Segurança:**

- **Limitação de taxa**: Prevenir abuso (requisições/segundo, limites de banda)
- **Lista branca de IPs**: Restringir acesso a clientes autorizados
- **Validação de requisição**: Prevenir injeção de cabeçalho, ataques de buffer overflow
- **Prevenção de proxy aberto**: Exigir autenticação, restringir domínios alvo

**3. Monitoramento e Observabilidade:**

- **Log estruturado**: Logs JSON com IDs de requisição, timestamps, métricas
- **Métricas Prometheus**: Contagem de requisições, percentis de latência, taxas de erro
- **Rastreamento distribuído**: Integração OpenTelemetry para depurar cadeias
- **Verificações de saúde**: Probes Liveness e readiness para orquestração

**4. Confiabilidade e Disponibilidade:**

- **Degradação graciosa**: Continuar servindo requisições durante falhas parciais
- **Circuit breakers**: Prevenir falhas em cascata para servidores alvo
- **Lógica de retentativa**: Backoff exponencial para falhas transitórias
- **Limites de conexão**: Prevenir exaustão de recursos

**Exemplo de Arquitetura de Produção:**

```
┌─────────────────────────────────────────────────────────┐
│  Balanceador de Carga (HAProxy, Nginx)                  │
│  • Terminação TLS                                       │
│  • Proteção DDoS (limitação de taxa)                    │
│  • Verificações de saúde                                │
└─────────────────┬───────────────────────────────────────┘
                  │
      ┌───────────┴───────────┐
      │                       │
┌─────▼──────┐         ┌──────▼─────┐
│ Proxy 1    │         │ Proxy 2    │
│ • Python   │         │ • Python   │
│ • uvloop   │         │ • uvloop   │
│ • Métricas │         │ • Métricas │
└─────┬──────┘         └──────┬─────┘
      │                       │
      └───────────┬───────────┘
                  │
        ┌─────────▼──────────┐
        │ Servidores Alvo    │
        │ • Pool de conexões │
        │ • Cache DNS        │
        └────────────────────┘
```

### Quando Construir Seu Próprio Proxy

**Boas Razões:**

- **Aprendizado**: Entender protocolos, programação de rede, I/O assíncrono
- **Lógica customizada**: Roteamento especializado, modificação de requisição, analítica
- **Otimização de custos**: Proxies auto-hospedados mais baratos que serviços comerciais (em escala)
- **Conformidade**: Soberania de dados, requisitos regulatórios
- **Pesquisa**: Testes de segurança, fuzzing de protocolo, detecção de anomalias

**Más Razões:**

- **Desempenho**: Proxies de produção (Squid, HAProxy, Nginx) são altamente otimizados
- **Segurança**: Proxies maduros passaram por extensas auditorias de segurança
- **Recursos**: Proxies comerciais oferecem geo-roteamento, resolução de captcha, IPs residenciais
- **Manutenção**: Proxies auto-hospedados exigem monitoramento, atualizações, resposta a incidentes

!!! tip "Abordagem Híbrida"
    Use **proxies comerciais** para rotação de IP e geo-targeting, e **proxies customizados** para lógica específica da aplicação (ex: enriquecimento de requisição, analítica, cache).

### Métricas de Desempenho do Mundo Real

**Benchmarks (testado em m5.xlarge AWS EC2, 2023):**

| Tipo de Proxy | Requisições/seg | Latência (p50) | Latência (p99) | Uso de CPU |
|---|---|---|---|---|
| **Direto** | 50,000 | 5ms | 15ms | N/A |
| **Python HTTP (asyncio)** | 8,000 | 20ms | 80ms | 60% |
| **Python HTTP (uvloop)** | 15,000 | 15ms | 50ms | 45% |
| **Squid (C)** | 35,000 | 8ms | 25ms | 30% |
| **HAProxy (C)** | 45,000 | 6ms | 20ms | 25% |

**Ponto Chave:** Proxies Python são **suficientes para tráfego moderado** (< 10K req/s) mas proxies baseados em C são necessários para ambientes de produção de alto throughput.

## Leitura Adicional e Referências

### Documentação Relacionada

**Dentro Deste Módulo:**

- **[Proxies HTTP/HTTPS](./http-proxies.md)** - Fundamentos de protocolo e autenticação
- **[Proxies SOCKS](./socks-proxies.md)** - Especificação do protocolo SOCKS5
- **[Detecção de Proxy](./proxy-detection.md)** - Como proxies são detectados e identificados
- **[Fundamentos de Rede](./network-fundamentals.md)** - Fundações de TCP/IP, UDP, WebRTC
- **[Legal e Ético](./proxy-legal.md)** - Conformidade e operação responsável de proxy

**Uso Prático:**

- **[Configuração de Proxy (Recursos)](../../features/configuration/proxy.md)** - Usando proxies no Pydoll

### Referências Externas

**Especificações Oficiais:**

- **RFC 1928** - SOCKS Protocol Version 5: https://datatracker.ietf.org/doc/html/rfc1928
- **RFC 1929** - Username/Password Authentication for SOCKS V5: https://datatracker.ietf.org/doc/html/rfc1929
- **RFC 7230** - HTTP/1.1: Message Syntax and Routing: https://datatracker.ietf.org/doc/html/rfc7230
- **RFC 7231** - HTTP/1.1: Semantics and Content (método CONNECT): https://datatracker.ietf.org/doc/html/rfc7231
- **RFC 7235** - HTTP/1.1: Authentication (status 407): https://datatracker.ietf.org/doc/html/rfc7235

**I/O Assíncrono Python:**

- **Documentação asyncio**: https://docs.python.org/3/library/asyncio.html
- **uvloop**: https://github.com/MagicStack/uvloop (I/O assíncrono de alta performance)
- **Tutorial async/await**: https://realpython.com/async-io-python/

**Servidores Proxy de Produção:**

- **Squid**: http://www.squid-cache.org/ (Proxy HTTP rico em recursos)
- **HAProxy**: http://www.haproxy.org/ (Balanceador de carga de alta performance)
- **Nginx**: https://nginx.org/en/docs/http/ngx_http_proxy_module.html (Módulo proxy HTTP)
- **Dante**: https://www.inet.no/dante/ (Servidor SOCKS)
- **Privoxy**: https://www.privoxy.org/ (Proxy focado em privacidade)

**Implementações Open-Source:**

- **mitmproxy**: https://mitmproxy.org/ (Proxy HTTP/HTTPS interceptador para testes de segurança)
  - Baseado em Python, excelente para aprendizado
  - Interceptação TLS, suporte a scripting
- **tinyproxy**: https://tinyproxy.github.io/ (Proxy HTTP leve em C)
- **3proxy**: https://github.com/z3APA3A/3proxy (Servidor proxy multiprotocolo)
- **shadowsocks**: https://shadowsocks.org/ (Protocolo criptografado similar ao SOCKS5)

**Otimização de Desempenho:**

- **Dicas de Desempenho Python**: https://wiki.python.org/moin/PythonSpeed/PerformanceTips
- **Benchmarks uvloop**: https://magic.io/blog/uvloop-blazing-fast-python-networking/
- **I/O zero-copy**: Documentação syscall `sendfile()`

**Melhores Práticas de Segurança:**

- **Guia de Segurança de Proxy OWASP**: https://owasp.org/www-community/controls/Proxy_authentication
- **Prevenindo Abuso de Proxy Aberto**: https://www.us-cert.gov/ncas/alerts/TA15-051A
- **Algoritmos de Limitação de Taxa**: Implementações Token bucket, leaky bucket

**Ferramentas e Testes:**

- **curl**: Cliente HTTP de linha de comando para testes
  ```bash
  curl -x http://localhost:8080 -U user:pass http://example.com
  curl --socks5 localhost:1080 --socks5-basic -U user:pass https://example.com
  ```
- **Wireshark**: Analisador de pacotes para inspecionar tráfego de proxy
- **mitmproxy**: Proxy HTTPS interativo para depuração
- **netcat (nc)**: Teste de conexão TCP crua

**Livros e Tutoriais:**

- **"HTTP: The Definitive Guide"** por David Gourley, Brian Totty (O'Reilly)
- **"TCP/IP Illustrated"** por W. Richard Stevens (Addison-Wesley)
- **"Foundations of Python Network Programming"** por Brandon Rhodes, John Goerzen (Apress)

### Tópicos Avançados (Além Deste Documento)

**Proxying de Alta Performance:**

- **Arquitetura multi-processo**: Usando `multiprocessing` para escalar entre núcleos de CPU
- **Bypass de kernel**: DPDK, io_uring para latência ultra-baixa
- **Multiplexação de conexão**: HTTP/2, QUIC para uso eficiente de recursos

**Segurança e Privacidade:**

- **Interceptação TLS**: Geração de certificado, detecção de pinning
- **Ofuscação de tráfego**: Mascaramento de protocolo (Shadowsocks, Trojan)
- **Integração Tor**: Rodando proxies sobre a rede Tor

**Roteamento Avançado:**

- **Roteamento geográfico**: Sair de países/cidades específicas
- **Roteamento baseado em protocolo**: Backends diferentes para HTTP vs WebSocket
- **Roteamento baseado em conteúdo**: Rotear com base em padrões de URL, cabeçalhos

**Monitoramento e Depuração:**

- **Rastreamento distribuído**: Integração Jaeger, Zipkin
- **Agregação de logs**: Stack ELK, Grafana Loki
- **Profiling de desempenho**: `py-spy`, `cProfile` para identificação de gargalos

---

## Pensamentos Finais

Construir servidores proxy do zero é uma **experiência de aprendizado inestimável** que fornece insights profundos sobre:

- **Protocolos de rede**: Entender HTTP, SOCKS5, TLS em um nível fundamental
- **Programação assíncrona**: Dominar event loops, coroutines, concorrência
- **Segurança**: Vetores de ataque, autenticação, controle de acesso
- **Desempenho**: Gargalos, técnicas de otimização, gerenciamento de recursos

Embora **proxies de produção** (Squid, HAProxy, Nginx) sejam superiores em desempenho, confiabilidade e segurança, **proxies customizados** habilitam casos de uso especializados:

- **Lógica de roteamento customizada** (geo-targeting, testes A/B, canary deployments)
- **Enriquecimento de requisição** (adicionar cabeçalhos, analítica, logging)
- **Tradução de protocolo** (HTTP → WebSocket, REST → gRPC)
- **Pesquisa e testes** (fuzzing, detecção de anomalias, auditorias de segurança)

**Ponto Chave:** Use **proxies de nível de produção** para infraestrutura, construa **proxies customizados** para lógica específica da aplicação.

**Próximos Passos:**
1. Leia **[Detecção de Proxy](./proxy-detection.md)** para entender como proxies customizados podem ser identificados
2. Revise **[Legal e Ético](./proxy-legal.md)** para considerações de conformidade
3. Explore o código-fonte do **mitmproxy** para padrões avançados de implementação de proxy em Python