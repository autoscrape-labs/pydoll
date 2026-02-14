# Arquitetura do Protocolo SOCKS

Este documento fornece uma exploração abrangente do SOCKS (SOCKet Secure), amplamente considerado o **padrão ouro** para automação de rede consciente da privacidade e proxy seguro. Embora os proxies HTTP dominem os ambientes corporativos, os proxies SOCKS são favorecidos por profissionais de segurança, defensores da privacidade e engenheiros de automação avançados por sua **natureza agnóstica a protocolo**, **requisitos de confiança reduzidos** e **modelo de segurança superior**.

Operando na **Camada 5 (Camada de Sessão)** do modelo OSI (abaixo do HTTP, mas acima do transporte), os proxies SOCKS oferecem capacidades que os proxies HTTP fundamentalmente não podem: tunelamento UDP, flexibilidade de protocolo, preservação da criptografia de ponta a ponta e verdadeira privacidade de DNS. Entender a arquitetura SOCKS é essencial para construir sistemas de automação de navegador **indetectáveis e de alto desempenho**.

!!! info "Navegação do Módulo"
    - **[← Proxies HTTP/HTTPS](./http-proxies.md)** - Limitações do proxy de camada de aplicação
    - **[← Fundamentos de Rede](./network-fundamentals.md)** - Fundamentos de TCP/IP, UDP, modelo OSI
    - **[← Visão Geral de Rede e Segurança](./index.md)** - Introdução do módulo e trilha de aprendizado
    - **[→ Detecção de Proxy](./proxy-detection.md)** - Níveis de anonimato e evasão de detecção
    - **[→ Construindo Proxies](./build-proxy.md)** - Implementação completa do SOCKS5 do zero
    
    Para configuração prática do Pydoll, veja **[Configuração de Proxy](../../features/configuration/proxy.md)**.

!!! tip "Por que o SOCKS5 é Superior para Automação"
    O SOCKS5 opera **abaixo da camada de aplicação** (Camada 5 vs Camada 7 do HTTP). Esse posicionamento significa:
    
    - **Não pode ler tráfego HTTP**: Vê apenas IPs e portas de destino, não URLs/cabeçalhos
    - **Agnóstico a protocolo**: Proxy para HTTP, FTP, SSH, WebSocket, protocolos personalizados
    - **Preserva TLS ponta-a-ponta**: Sem possibilidade de MITM (diferente dos proxies HTTP)
    - **Resolução de DNS remota**: Previne vazamentos de DNS para seu ISP
    - **Suporte a UDP**: Crítico para WebRTC, DNS, VoIP, protocolos de jogos

    Isso reduz drasticamente a **superfície de confiança** em comparação com proxies HTTP. Você só confia no proxy para encaminhar pacotes corretamente, não para lidar com dados sensíveis da aplicação.

## Introdução: O Proxy de Camada de Sessão

SOCKS (SOCKet Secure) representa uma abordagem fundamentalmente diferente de proxying em comparação com proxies HTTP. Enquanto proxies HTTP são **cientes da aplicação** (entendendo semântica HTTP, cabeçalhos, métodos), proxies SOCKS são **cientes do transporte** (entendendo apenas conexões TCP/UDP, IPs e portas).

**Contexto Histórico:**

O SOCKS foi desenvolvido no início dos anos 1990 por **David Koblas e Michelle Koblas na MIPS Computer Systems** para permitir que hosts dentro de um firewall obtivessem **acesso total** à Internet sem exigir conectividade IP direta. A motivação original era simples: firewalls corporativos bloqueavam conexões de saída, mas os funcionários precisavam de acesso a recursos externos. O SOCKS forneceu uma solução estabelecendo um **gateway único controlado** através do firewall.

**Linha do Tempo da Evolução:**

- **1992**: SOCKS4 introduzido (especificação informal, sem RFC)
- **1996**: SOCKS5 padronizado como **RFC 1928** pelo IETF
- **1996**: Autenticação por Usuário/Senha padronizada como **RFC 1929**
- **2003**: Extensão de autenticação GSS-API (**RFC 1961**)
- **2020s**: Extensões modernas (extensões Tor SOCKS, propostas SOCKS6)

**Por que "SOCKet Secure"?**

Apesar do nome, o SOCKS em si **não fornece criptografia**. "Seguro" refere-se à sua capacidade de atravessar firewalls com segurança (de uma perspectiva de controle de acesso), não à segurança criptográfica. Para criptografia, você deve sobrepor TLS/SSL ao SOCKS, ou usá-lo dentro de um túnel criptografado (SSH, VPN).

!!! warning "SOCKS NÃO Criptografa"
    Um equívoco comum: **SOCKS ≠ Criptografia**. SOCKS é um **protocolo de proxy**, não um protocolo de criptografia. Ele encaminha pacotes transparentemente sem modificação, incluindo tráfego HTTP não criptografado.
    
    Para comunicação segura, combine SOCKS com:

    - **TLS/HTTPS** para tráfego web
    - **SSH** para criptografia de túnel
    - **VPN** para criptografia total do tráfego
    
    A vantagem de segurança do SOCKS é **arquitetônica** (menos confiança necessária), não criptográfica.

## Por que a Camada 5 Importa: Sessão vs Aplicação

A chave para entender o SOCKS é entender **onde ele opera** na pilha de rede:

```
┌─────────────────────────────────────────────┐
│  Camada 7: Aplicação (HTTP, FTP, SMTP)      │ ← Proxies HTTP operam aqui
│  • Visibilidade total do protocolo          │   (pode ler URLs, cabeçalhos)
│  • Pode modificar requisições/respostas     │
│  • Específico do protocolo (apenas HTTP)    │
├─────────────────────────────────────────────┤
│  Camada 6: Apresentação (TLS, criptografia) │
├─────────────────────────────────────────────┤
│  Camada 5: Sessão (SOCKS)                   │ ← Proxies SOCKS operam aqui
│  • Vê apenas IP:porta de destino           │   (agnóstico a protocolo)
│  • Não pode inspecionar dados da aplicação  │
│  • Funciona com qualquer protocolo Camada 7 │
├─────────────────────────────────────────────┤
│  Camada 4: Transporte (TCP, UDP)            │
│  • Gerenciamento de conexão                 │
│  • Números de porta, controle de fluxo      │
├─────────────────────────────────────────────┤
│  Camada 3: Rede (IP)                        │
│  • Roteamento, endereços IP                 │
├─────────────────────────────────────────────┤
│  Camada 2: Enlace de Dados (Ethernet, WiFi) │
├─────────────────────────────────────────────┤
│  Camada 1: Física (cabos, sinais)           │
└─────────────────────────────────────────────┘
```

**Implicação Prática:**

Quando você usa um proxy HTTP:
```http
GET http://example.com/secret-api?token=abc123 HTTP/1.1
Cookie: session=sensitive_data
Authorization: Bearer secret_token
```

**Proxy HTTP vê tudo** - URL, parâmetros de consulta, cookies, cabeçalhos de autorização.

Quando você usa um proxy SOCKS5:
```python
# Handshake SOCKS5 (simplificado)
CONNECT example.com:443  # Vê apenas: host de destino e porta
[Dados TLS Criptografados]     # Não pode ver URL, cabeçalhos ou conteúdo
```

**SOCKS5 vê apenas**: `example.com`, porta `443`, e volume de dados. A requisição HTTP dentro do túnel TLS é **completamente opaca** para o proxy.

!!! success "A Diferença de Segurança"
    Com proxies HTTP, você deve **confiar no operador do proxy** para não:

    - Registrar seu histórico de navegação (URLs completas)
    - Roubar tokens de autenticação/cookies
    - Modificar respostas (injetar malware, anúncios)
    - Realizar ataques MITM em HTTPS (via certificado CA)
    
    Com SOCKS5, você confia no proxy apenas para:

    - Encaminhar pacotes corretamente
    - Não registrar metadados de conexão (IP, porta, tempo)
    
    A **superfície de ataque** é drasticamente menor.

### SOCKS4 vs SOCKS5

| Característica | SOCKS4 | SOCKS5 |
|---|---|---|
| **RFC** | Sem RFC oficial (padrão de facto dos anos 1990) | RFC 1928 (padrão oficial, 1996) |
| **Autenticação** | Nenhuma (apenas ID de usuário) | Múltiplos métodos (sem auth, usuário/senha, GSSAPI) |
| **Versão IP** | Apenas IPv4 | IPv4 e IPv6 |
| **Suporte UDP** | Não | Sim |
| **Resolução DNS** | Lado do cliente | Lado do servidor (mais anônimo) |
| **Suporte a Protocolo** | Apenas TCP | TCP e UDP |

!!! info "História do SOCKS4"
    O SOCKS4 foi desenvolvido pela NEC no início dos anos 1990 como um padrão de facto sem documentação RFC formal. O SOCKS5 (RFC 1928) foi posteriormente padronizado pelo IETF em 1996 para suprir as limitações do SOCKS4.

!!! tip "Sempre Use SOCKS5"
    O SOCKS5 é superior em todos os sentidos. O SOCKS4 é legado e só deve ser usado se o proxy não suportar SOCKS5.

### Protocolo de Handshake SOCKS5

O processo de conexão SOCKS5 segue a RFC 1928:

```mermaid
sequenceDiagram
    participant Client
    participant SOCKS5 as Proxy SOCKS5
    participant Server as Servidor de Destino
    
    Note over Client,SOCKS5: Fase 1: Negociação de Método
    Client->>SOCKS5: 1. Olá<br/>[VER=5, NMETHODS, METHODS]
    SOCKS5->>Client: 2. Método Selecionado<br/>[VER=5, METHOD]
    
    Note over Client,SOCKS5: Fase 2: Autenticação (se necessário)
    Client->>SOCKS5: 3. Req. de Autenticação<br/>[VER=1, ULEN, UNAME, PLEN, PASSWD]
    SOCKS5->>Client: 4. Resp. de Autenticação<br/>[VER=1, STATUS]
    
    Note over Client,SOCKS5: Fase 3: Requisição de Conexão
    Client->>SOCKS5: 5. Req. de Conexão<br/>[VER=5, CMD, DST.ADDR, DST.PORT]
    SOCKS5->>Server: 6. Estabelecer Conexão TCP
    Server-->>SOCKS5: Conexão Estabelecida
    SOCKS5->>Client: 7. Resposta de Conexão<br/>[VER=5, REP, BND.ADDR, BND.PORT]
    
    Note over Client,Server: Transferência de dados (via proxy)
    Client->>SOCKS5: Dados da Aplicação
    SOCKS5->>Server: Encaminhar Dados
    Server->>SOCKS5: Dados de Resposta
    SOCKS5->>Client: Encaminhar Resposta
```

### Estruturas de Pacote SOCKS5

#### 1. Olá do Cliente (Client Hello)

```python
# Layout de bytes
[
    0x05,        # VER: Versão do protocolo (5)
    0x02,        # NMETHODS: Número de métodos de autenticação
    0x00, 0x02   # METHODS: Sem auth (0x00) e Usuário/Senha (0x02)
]
```

#### 2. Seleção de Método do Servidor

```python
[
    0x05,        # VER: Versão do protocolo (5)
    0x02         # METHOD: Método selecionado (0x02 = Usuário/Senha)
]
```

**Códigos de método:**
- `0x00`: Nenhuma autenticação necessária
- `0x01`: GSSAPI
- `0x02`: Usuário/Senha
- `0xFF`: Nenhum método aceitável

#### 3. Autenticação (Usuário/Senha)

```python
# Requisição de autenticação do cliente
[
    0x01,              # VER: Versão da subnegociação (1)
    len(username),     # ULEN: Comprimento do nome de usuário
    *username_bytes,   # UNAME: Nome de usuário
    len(password),     # PLEN: Comprimento da senha
    *password_bytes    # PASSWD: Senha
]

# Resposta de autenticação do servidor
[
    0x01,              # VER: Versão da subnegociação (1)
    0x00               # STATUS: 0 = sucesso, não-zero = falha
]
```

#### 4. Requisição de Conexão

```python
[
    0x05,              # VER: Versão do protocolo (5)
    0x01,              # CMD: Comando (1=CONNECT, 2=BIND, 3=UDP ASSOCIATE)
    0x00,              # RSV: Reservado
    0x03,              # ATYP: Tipo de endereço (1=IPv4, 3=Domínio, 4=IPv6)
    len(domain),       # Comprimento do domínio
    *domain_bytes,     # Nome do domínio
    *port_bytes        # Porta (2 bytes, big-endian)
]
```

#### 5. Resposta de Conexão

```python
[
    0x05,              # VER: Versão do protocolo (5)
    0x00,              # REP: Resposta (0=sucesso, veja códigos de erro abaixo)
    0x00,              # RSV: Reservado
    0x01,              # ATYP: Tipo de endereço
    *bind_addr,        # BND.ADDR: Endereço vinculado
    *bind_port         # BND.PORT: Porta vinculada (2 bytes)
]
```

**Códigos de resposta:**

- `0x00`: Sucesso
- `0x01`: Falha geral do servidor SOCKS
- `0x02`: Conexão não permitida pelo conjunto de regras
- `0x03`: Rede inacessível
- `0x04`: Host inacessível
- `0x05`: Conexão recusada
- `0x06`: TTL expirou
- `0x07`: Comando não suportado
- `0x08`: Tipo de endereço não suportado

!!! info "Eficiência do SOCKS5"
    SOCKS5 é um protocolo binário (não baseado em texto como HTTP). Isso o torna:
    
    - Mais eficiente (pacotes menores)
    - Mais rápido de analisar
    - Menos legível por humanos (requer dump hexadecimal para depurar)

### Suporte UDP SOCKS5

Uma das características únicas do SOCKS5 é o suporte a UDP através do comando `UDP ASSOCIATE`:

```mermaid
sequenceDiagram
    participant Client
    participant SOCKS5
    participant UDP_Server as Servidor UDP
    
    Note over Client,SOCKS5: Estabelecer conexão de controle TCP
    Client->>SOCKS5: TCP: CONNECT (autenticação)
    Client->>SOCKS5: TCP: Requisição UDP ASSOCIATE
    SOCKS5->>Client: TCP: Endereço de retransmissão e porta
    
    Note over Client,SOCKS5: Transferência de dados UDP
    Client->>SOCKS5: UDP: Datagrama para retransmissão
    SOCKS5->>UDP_Server: UDP: Encaminhar datagrama
    UDP_Server->>SOCKS5: UDP: Datagrama de resposta
    SOCKS5->>Client: UDP: Encaminhar resposta
    
    Note over Client,SOCKS5: Conexão de controle TCP permanece aberta
```

**Formato do pacote UDP:**

```python
[
    0x00, 0x00,        # RSV: Reservado
    0x00,              # FRAG: Número do fragmento
    0x01,              # ATYP: Tipo de endereço
    *dst_addr,         # DST.ADDR: Endereço de destino
    *dst_port,         # DST.PORT: Porta de destino
    *data              # DATA: Dados do usuário
]
```

!!! warning "Limitações do UDP"
    UDP ASSOCIATE requer:
    
    - Uma conexão de controle TCP persistente
    - Cliente e servidor para manter estado
    - Infraestrutura de retransmissão adicional
    
    Muitos proxies não suportam UDP, e aqueles que suportam frequentemente têm restrições ou custos adicionais.

!!! tip "Alternativas Modernas de Proxy UDP"
    Para suporte UDP completo em configurações modernas, considere estas alternativas:
    
    - **Shadowsocks**: Protocolo moderno semelhante ao SOCKS5, projetado para proxy UDP/TCP com criptografia
    - **WireGuard**: Protocolo VPN com suporte UDP nativo e excelente desempenho
    - **V2Ray/VMess**: Framework de proxy flexível com manuseio UDP abrangente
    - **Trojan**: Protocolo leve que imita o tráfego HTTPS enquanto suporta UDP
    
    Estes protocolos são particularmente úteis para jogos, VoIP ou streaming de vídeo onde o desempenho UDP é crítico.

## Por que SOCKS5 é Mais Seguro

Agora que construímos a fundação, vamos analisar por que o SOCKS5 é geralmente considerado mais seguro que os proxies HTTP/HTTPS.

### Comparação em Nível de Protocolo

**Proxy HTTP (Camada 7):**

```mermaid
graph LR
    A1[Aplicação Cliente] --> A2[Biblioteca HTTP]
    A2 --> A3[Proxy intercepta requisições HTTP]
    A3 --> A4[Proxy pode ler Cabeçalhos, Cookies, Métodos, URLs]
```

**Proxy SOCKS5 (Camada 5):**

```mermaid
graph LR
    B1[Aplicação Cliente] --> B2[Qualquer Protocolo]
    B2 --> B3[Transporte TCP/UDP]
    B3 --> B4[SOCKS5 vê apenas: IP de Destino, Porta, Tamanho do pacote]
```

### Vantagens de Segurança do SOCKS5

| Aspecto | Proxy HTTP/HTTPS | Proxy SOCKS5 |
|---|---|---|
| **Visibilidade dos Dados** | Pode ler cabeçalhos HTTP, URLs, cookies (HTTP) | Vê apenas IP/porta de destino e tamanhos de pacote |
| **Suporte a Protocolo** | Apenas HTTP/HTTPS | Qualquer protocolo TCP/UDP |
| **Inspeção TLS** | Possível com certificados MITM | Impossível (opera abaixo do TLS) |
| **Vazamentos de DNS** | Cliente resolve DNS (vaza) | Proxy resolve DNS (sem vazamento) |
| **Consciência da Aplicação** | Entende HTTP | Agnóstico a protocolo |
| **Fingerprinting** | Pode injetar cabeçalhos, modificar requisições | Encaminhamento transparente de pacotes |
| **Suporte UDP** | Nenhum | Sim (para WebRTC, DNS, etc.) |

### Resolução de DNS: Uma Diferença Crítica

**Comportamento do DNS no Proxy HTTP:**

```mermaid
sequenceDiagram
    participant Client
    participant DNS
    participant Proxy
    participant Server
    
    Note over Client: Cliente resolve DNS<br/>(usa DNS do sistema)
    Client->>DNS: Consulta DNS: example.com?
    DNS->>Client: Resposta DNS: 93.184.216.34
    Note over Client: Vazamento de DNS: ISP vê a consulta
    
    Client->>Proxy: Conectar a 93.184.216.34
    Proxy->>Server: Encaminhar para 93.184.216.34
```

**Comportamento do DNS no SOCKS5:**

```mermaid
sequenceDiagram
    participant Client
    participant SOCKS5
    participant DNS
    participant Server
    
    Note over Client: Cliente envia nome de domínio<br/>(não IP) para SOCKS5
    Client->>SOCKS5: CONNECT example.com:443<br/>(ATYP=0x03, nome de domínio)
    
    Note over SOCKS5: Proxy resolve DNS<br/>(usando seu próprio DNS)
    SOCKS5->>DNS: Consulta DNS: example.com?
    DNS->>SOCKS5: Resposta DNS: 93.184.216.34
    Note over SOCKS5: Sem vazamento de DNS para o ISP do cliente
    
    SOCKS5->>Server: Conectar a 93.184.216.34
```

!!! tip "Resolução de DNS Remota"
    A capacidade do SOCKS5 de realizar resolução de DNS no servidor proxy é crucial para a privacidade. Seu ISP nunca vê quais sites você está consultando, apenas que você está conectado ao proxy.

### Resistência a Man-in-the-Middle (MITM)

**Proxies HTTP são vulneráveis a MITM:**

```mermaid
sequenceDiagram
    participant Client
    participant Malicious_Proxy as Proxy HTTP Malicioso
    participant Server
    
    Client->>Malicious_Proxy: Requisição HTTPS (criptografada)
    Note over Malicious_Proxy: Proxy termina o TLS<br/>(usando certificado falso)
    
    Malicious_Proxy->>Malicious_Proxy: Lê/modifica conteúdo
    
    Malicious_Proxy->>Server: Recriptografa com certificado real
    Server->>Malicious_Proxy: Resposta
    Malicious_Proxy->>Client: Resposta modificada
    
    Note over Client: Pode mostrar aviso de certificado
```

**SOCKS5 não pode realizar MITM:**

```mermaid
sequenceDiagram
    participant Client
    participant SOCKS5
    participant Server
    
    Client->>SOCKS5: CONNECT server.com:443
    SOCKS5->>Server: Conexão TCP estabelecida
    SOCKS5->>Client: Conexão pronta
    
    Note over Client,Server: Túnel TLS ponta-a-ponta
    Client->>Server: Handshake TLS + Dados Criptografados
    Note over SOCKS5: Não pode descriptografar<br/>Não pode modificar<br/>Apenas encaminha pacotes
    Server->>Client: Resposta Criptografada
```

!!! info "Modelo de Confiança"
    - **Proxy HTTP**: Você confia nele com dados HTTP em texto claro e para tunelar HTTPS adequadamente
    - **Proxy SOCKS5**: Você confia nele apenas para encaminhar pacotes corretamente
    
    SOCKS5 tem uma superfície de confiança menor.

## Autenticação SOCKS5 e Chrome

Uma das armadilhas mais comuns ao usar proxies SOCKS5 com automação de navegador é a **autenticação**. O Chrome/Chromium **não** suporta autenticação SOCKS5 por usuário/senha nativamente. Esta é uma limitação conhecida e de longa data, rastreada como [Chromium Issue #40323993](https://issues.chromium.org/issues/40323993).

### Por que o Chrome Ignora Credenciais SOCKS5

Quando você configura o Chrome com `--proxy-server=socks5://user:pass@proxy:1080`, o Chrome **ignora silenciosamente** as credenciais incorporadas. Durante a negociação de método SOCKS5, o Chrome oferece apenas o método `0x00` (sem autenticação necessária) — ele nunca oferece o método `0x02` (usuário/senha).

Isso acontece porque a autenticação SOCKS5 opera em **uma camada de protocolo completamente diferente** da autenticação de proxy HTTP:

**Fluxo de autenticação de proxy HTTP (funciona no Chrome):**

```
Chrome → HTTP CONNECT → Proxy responde 407 → Chrome fornece credenciais → Proxy conecta
```

O Chrome lida com isso através do **domínio Fetch** do CDP — o Pydoll intercepta eventos `Fetch.authRequired` e responde automaticamente com as credenciais armazenadas.

**Fluxo de autenticação SOCKS5 (NÃO suportado pelo Chrome):**

```
Chrome → SOCKS5 Hello [métodos: 0x00] → Proxy seleciona 0x00 ou rejeita → Sem auth possível
```

O handshake SOCKS5 é uma negociação de **protocolo binário** na camada de sessão. A pilha de rede do Chrome simplesmente não implementa a subnegociação de usuário/senha (RFC 1929). Não há desafio HTTP 407, nenhum evento `Fetch.authRequired`, e nenhuma forma do Pydoll (ou qualquer ferramenta baseada em CDP) injetar credenciais.

### A Solução do Forwarder Local

A solução padrão da indústria é um **proxy forwarder local** — um servidor SOCKS5 local leve que:

1. **Aceita conexões do Chrome** sem autenticação (método `0x00`)
2. **Conecta ao proxy SOCKS5 remoto** com autenticação completa (método `0x02`, RFC 1929)
3. **Retransmite dados bidirecionalmente** entre o Chrome e o proxy remoto

```
┌────────────┐     sem auth     ┌──────────────┐   user/pass    ┌──────────────┐
│   Chrome   │ ──────────────►  │  SOCKS5 Local │ ────────────► │ SOCKS5 Remoto│
│            │  socks5://       │  Forwarder    │  socks5://    │    Proxy     │
│            │  127.0.0.1:1081  │  (localhost)  │  proxy:1080   │  (internet)  │
└────────────┘                  └──────────────┘                └──────┬───────┘
                                                                       │
                                                                       ▼
                                                                ┌──────────────┐
                                                                │   Servidor   │
                                                                │   Destino    │
                                                                └──────────────┘
```

**Sequência detalhada do handshake:**

```mermaid
sequenceDiagram
    participant Chrome
    participant Forwarder as Forwarder Local
    participant Remote as Proxy SOCKS5 Remoto
    participant Server as Destino

    Note over Chrome,Forwarder: Fase 1: Chrome → Forwarder (sem auth)
    Chrome->>Forwarder: SOCKS5 Hello [VER=5, METHODS=[0x00]]
    Forwarder->>Chrome: Método Selecionado [VER=5, METHOD=0x00]
    Chrome->>Forwarder: CONNECT example.com:443

    Note over Forwarder,Remote: Fase 2: Forwarder → Remoto (com auth)
    Forwarder->>Remote: SOCKS5 Hello [VER=5, METHODS=[0x02]]
    Remote->>Forwarder: Método Selecionado [VER=5, METHOD=0x02]
    Forwarder->>Remote: Auth [VER=1, USER=..., PASS=...]
    Remote->>Forwarder: Auth OK [VER=1, STATUS=0x00]
    Forwarder->>Remote: CONNECT example.com:443
    Remote->>Server: Conexão TCP
    Remote->>Forwarder: Resposta de Conexão [SUCESSO]

    Note over Chrome,Forwarder: Fase 3: Confirmação de relay
    Forwarder->>Chrome: Resposta de Conexão [SUCESSO]

    Note over Chrome,Server: Fase 4: Relay bidirecional de dados
    Chrome->>Forwarder: Dados da Aplicação (TLS)
    Forwarder->>Remote: Encaminhar Dados
    Remote->>Server: Encaminhar Dados
    Server->>Remote: Resposta
    Remote->>Forwarder: Encaminhar Resposta
    Forwarder->>Chrome: Encaminhar Resposta
```

### Usando o Forwarder com Pydoll

O Pydoll fornece um forwarder pronto para uso no módulo `pydoll.utils`:

```python
import asyncio
from pydoll.utils import SOCKS5Forwarder
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def main():
    forwarder = SOCKS5Forwarder(
        remote_host='proxy.example.com',
        remote_port=1080,
        username='myuser',
        password='mypass',
        local_port=1081,  # Use 0 para porta auto-atribuída
    )
    async with forwarder:
        options = ChromiumOptions()
        options.add_argument(f'--proxy-server=socks5://127.0.0.1:{forwarder.local_port}')

        async with Chrome(options=options) as browser:
            tab = await browser.start()
            await tab.go_to('https://httpbin.org/ip')

asyncio.run(main())
```

O forwarder também pode ser usado como ferramenta CLI standalone:

```bash
python -m pydoll.utils.socks5_proxy_forwarder \
    --remote-host proxy.example.com \
    --remote-port 1080 \
    --username myuser \
    --password mypass \
    --local-port 1081
```

### Considerações de Segurança

!!! warning "Notas de Segurança"
    - O forwarder local se vincula a `127.0.0.1` por padrão — acessível apenas da sua máquina
    - **Nunca** vincule a `0.0.0.0` em produção, pois isso exporia um proxy SOCKS5 sem autenticação para a rede
    - As credenciais são transmitidas em texto claro durante o handshake SOCKS5 com o proxy remoto (isso é inerente ao SOCKS5 RFC 1929) — use túneis SSH ou VPN para criptografia adicional se necessário
    - O forwarder adiciona latência mínima (loopback local é sub-milissegundo)

### Limitações de Ambiente

!!! info "Ambientes Restritos"
    Alguns ambientes (contêineres Docker, plataformas serverless, VMs endurecidas) podem restringir a vinculação a portas locais. Nesses casos:

    - Certifique-se de que seu ambiente permite vincular a `127.0.0.1` em portas arbitrárias
    - Use `local_port=0` para deixar o SO atribuir uma porta disponível
    - Se a vinculação local estiver completamente bloqueada, considere usar um proxy HTTP CONNECT, que o Chrome suporta nativamente com autenticação

## Resumo e Pontos Chave

SOCKS5 representa o **padrão ouro** para proxying consciente da privacidade, oferecendo flexibilidade de protocolo, requisitos de confiança reduzidos e segurança superior em comparação com alternativas da camada de aplicação. Entender a arquitetura SOCKS é essencial para construir sistemas de automação robustos e indetectáveis.

### Conceitos Centrais Cobertos

**1. Operação na Camada de Sessão:**

- SOCKS opera na **Camada 5 (Camada de Sessão)**, abaixo do HTTP mas acima do TCP/UDP
- **Agnóstico a protocolo**: Funciona com qualquer protocolo de aplicação (HTTP, FTP, SSH, WebSocket, customizado)
- **Encaminhamento cego**: Vê apenas IP e porta de destino, não dados da aplicação

**2. Recursos do Protocolo SOCKS5:**

- **Autenticação**: Múltiplos métodos (sem auth, usuário/senha, GSSAPI)
- **Suporte a Versão IP**: Tanto IPv4 quanto IPv6
- **TCP e UDP**: Suporte total para protocolos sem conexão
- **Resolução de DNS Remota**: Previne vazamentos de DNS para o ISP do cliente
- **Protocolo Binário**: Estruturas de pacote eficientes e de baixa sobrecarga

**3. Modelo de Segurança:**

- **Não pode inspecionar dados da aplicação**: Opera abaixo da criptografia TLS
- **Resistente a MITM**: Não pode terminar conexões TLS (diferente de proxies HTTP)
- **Superfície de confiança reduzida**: Confia no proxy apenas para encaminhar pacotes, não para lidar com dados sensíveis
- **Privacidade de DNS**: Proxy resolve domínios, escondendo consultas do ISP

**4. Suporte UDP:**

- Recurso único do SOCKS5 permitindo WebRTC, DNS-sobre-UDP, VoIP, jogos
- Requer conexão de controle TCP persistente + retransmissão UDP
- Muitos proxies não suportam UDP (requer infraestrutura adicional)

**5. SOCKS4 vs SOCKS5:**

- SOCKS4: Legado, apenas TCP, sem autenticação, apenas IPv4
- SOCKS5: Padrão moderno (RFC 1928), suporte UDP, autenticação flexível, IPv4/IPv6

### Matriz de Decisão: SOCKS5 vs Proxy HTTP

| Requisito | SOCKS5 | Proxy HTTP |
|---|---|---|
| **Privacidade** | **Excelente** (encaminhamento cego) | **Ruim** (vê todo o tráfego HTTP) |
| **Flexibilidade de Protocolo** | **Qualquer TCP/UDP** | **Apenas HTTP/HTTPS** |
| **Privacidade de DNS** | **Resolução remota** | **Vazamento no cliente** |
| **Suporte UDP** | **Sim** | **Não** |
| **Inspeção TLS** | **Impossível (seguro)** | **Possível (risco de MITM)** |
| **Furtividade (Stealth)** | **Alta (transparente)** | **Baixa (injeção de cabeçalho)** |
| **Complexidade de Config.** | **Moderada** | **Simples** |
| **Filtragem de Conteúdo** | **Não** (cego) | **Sim** (consciente da aplicação) |
| **Cache** | **Não** | **Sim** |
| **Ambientes Corporativos** | **Raro** | **Comum** |

**Recomendação Geral:**
- **Privacidade/Automação**: SOCKS5 (furtividade, flexibilidade de protocolo, segurança)
- **Corporativo/Filtragem**: Proxy HTTP (controle de conteúdo, cache, aplicação de políticas)
- **Segurança Máxima**: SOCKS5 sobre túnel SSH ou VPN

### Quando Usar SOCKS5

**Casos de Uso Ideais:**
- **Automação de navegador** exigindo furtividade e flexibilidade de protocolo
- **Aplicações críticas de privacidade** (ferramentas de jornalismo, VPNs, Tor)
- **Aplicações multiprotocolo** (FTP, SSH, WebSocket, protocolos customizados)
- **Aplicações WebRTC** (videoconferência, jogos, comunicação em tempo real)
- **Privacidade de DNS** (esconder padrões de navegação do ISP)
- **Contornar inspeção profunda de pacotes (DPI)** em redes restritivas

**Casos de Uso Ruins:**
- **Filtragem de conteúdo corporativo** (use proxy HTTP com políticas baseadas em URL)
- **Cache HTTP para otimização de banda** (use proxy HTTP ou CDN)
- **Scraping simples apenas HTTP onde furtividade não é crítica**

### Configuração Prática no Pydoll

**Proxy SOCKS5 Básico:**
```python
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
options.add_argument('--proxy-server=socks5://proxy.example.com:1080')
# Para proxies autenticados, inclua as credenciais na URL:
# options.add_argument('--proxy-server=socks5://usuario:senha@proxy.example.com:1080')

async with Chrome(options=options) as browser:
    tab = await browser.start()
    await tab.go_to('https://example.com')
```

**SOCKS5 com Autenticação (via Pydoll):**
O Pydoll lida automaticamente com a autenticação usuário/senha SOCKS5 através do domínio Fetch do Chrome. Nenhuma implementação manual necessária.

**Testando Proxy SOCKS5:**
```python
import socket
import socks

# Teste manual SOCKS5 (sem Pydoll)
socks.set_default_proxy(socks.SOCKS5, "proxy.example.com", 1080, 
                        username="user", password="pass")
socket.socket = socks.socksocket

# Agora todas as conexões de socket usam SOCKS5
```

!!! tip "Melhores Práticas SOCKS5"
    - **Use SOCKS5, não SOCKS4** (melhor segurança, suporte UDP)
    - **Habilite resolução de DNS remota** (previne vazamentos de DNS)
    - **Use autenticação** (usuário/senha ou GSSAPI)
    - **Teste vazamentos WebRTC** (mesmo com SOCKS5, WebRTC pode vazar IP real)
    - **Combine com TLS** (SOCKS fornece proxying, não criptografia)
    
    - **Não assuma SOCKS5 = criptografia** (coloque TLS por cima)
    - **Não use SOCKS4** (legado, limitações de segurança)
    - **Não confie no suporte UDP** (muitos proxies não suportam)

## Leitura Adicional e Referências

### Documentação Relacionada

**Dentro Deste Módulo:**

- **[Proxies HTTP/HTTPS](./http-proxies.md)** - Comparação de proxying de camada de aplicação
- **[Fundamentos de Rede](./network-fundamentals.md)** - Fundamentos de TCP/IP, UDP, modelo OSI
- **[Detecção de Proxy](./proxy-detection.md)** - Como proxies SOCKS5 ainda podem ser detectados
- **[Construindo Proxies](./build-proxy.md)** - Implementação completa de servidor SOCKS5 do zero

**Uso Prático:**

- **[Configuração de Proxy (Recursos)](../../features/configuration/proxy.md)** - Configurando SOCKS5 no Pydoll
- **[Opções do Navegador](../../features/configuration/browser-options.md)** - Flags do Chrome para otimização de proxy

**Análises Profundas:**

- **[Network Fingerprinting](../fingerprinting/network-fingerprinting.md)** - Características TCP/IP que vazam através de SOCKS5
- **[Browser Fingerprinting](../fingerprinting/browser-fingerprinting.md)** - Detecção em nível de aplicação apesar do SOCKS5
- **[Técnicas de Evasão](../fingerprinting/evasion-techniques.md)** - Como maximizar a furtividade do SOCKS5

### Referências Externas

**RFCs (Especificações Oficiais):**

- **RFC 1928** - SOCKS Protocol Version 5 (Março 1996)
  - https://datatracker.ietf.org/doc/html/rfc1928
  - A especificação oficial do SOCKS5
- **RFC 1929** - Username/Password Authentication for SOCKS V5 (Março 1996)
  - https://datatracker.ietf.org/doc/html/rfc1929
  - Mecanismo de autenticação padrão
- **RFC 1961** - GSS-API Authentication Method for SOCKS Version 5 (Junho 1996)
  - https://datatracker.ietf.org/doc/html/rfc1961
  - Autenticação corporativa (Kerberos)
- **RFC 3089** - A SOCKS-based IPv6/IPv4 Gateway Mechanism (Abril 2001)
  - https://datatracker.ietf.org/doc/html/rfc3089
  - Interoperabilidade IPv4/IPv6

**SOCKS4 (Especificação Informal):**

- **Protocolo SOCKS4**: http://ftp.icm.edu.pl/packages/socks/socks4/SOCKS4.protocol
- **Extensão SOCKS4A**: http://ftp.icm.edu.pl/packages/socks/socks4/SOCKS4A.protocol
  - Extensão de resolução de nome de domínio

**Artigos Técnicos e Guias:**

- **Understanding SOCKS5**: https://securitytrails.com/blog/socks5-proxy
- **SOCKS5 vs HTTP Proxies**: https://www.varonis.com/blog/socks-proxy-primer
- **Building a SOCKS5 Server**: Várias implementações no GitHub (veja build-proxy.md)

**Implementações SOCKS:**

- **Dante**: https://www.inet.no/dante/ (Servidor SOCKS de produção)
- **ss5**: http://ss5.sourceforge.net/ (Servidor SOCKS4/SOCKS5)
- **PySocks**: https://github.com/Anorov/PySocks (Cliente SOCKS Python)
- **go-socks5**: https://github.com/armon/go-socks5 (Biblioteca Go SOCKS5)

**Protocolos Modernos Semelhantes ao SOCKS:**

- **Shadowsocks**: https://shadowsocks.org/ (Protocolo criptografado semelhante ao SOCKS5)
- **WireGuard**: https://www.wireguard.com/ (VPN com simplicidade semelhante ao SOCKS)
- **V2Ray/VMess**: https://www.v2ray.com/ (Framework de proxy flexível)
- **Trojan**: https://trojan-gfw.github.io/trojan/ (Proxy que imita HTTPS)

**Ferramentas de Teste:**

- **curl com SOCKS5**:
  ```bash
  curl --socks5 proxy:1080 --socks5-basic --user user:pass https://example.com
  ```
- **proxychains**: Força qualquer aplicação a passar pelo SOCKS5
  ```bash
  proxychains4 firefox
  ```
- **Wireshark**: Análise de pacotes para verificar handshake SOCKS5

**Segurança e Privacidade:**

- **Teste de Vazamento de DNS**: https://dnsleaktest.com/
- **Teste de Vazamento de WebRTC**: https://browserleaks.com/webrtc
- **Detecção de IP**: https://ipleak.net/

### Tópicos Avançados (Além Deste Documento)

**Extensões SOCKS:**

- **Extensões Tor SOCKS**: Extensões SOCKS5 específicas do Tor para isolamento de circuito
- **Propostas SOCKS6**: Protocolo SOCKS de próxima geração (estágio de rascunho)
- **SOCKS sobre TLS**: Canais SOCKS criptografados

**Otimização de Desempenho:**

- **Pooling de Conexão**: Reutilizando conexões SOCKS5
- **Multiplexação**: Múltiplos streams sobre uma única conexão SOCKS
- **Desempenho UDP**: Otimizando retransmissão UDP SOCKS5

**Implantações Corporativas:**

- **Integração LDAP**: Autenticação de usuário corporativo
- **Balanceamento de Carga**: Distribuindo tráfego entre proxies SOCKS5
- **Alta Disponibilidade**: Estratégias de failover e redundância

**Comparação de Protocolos:**

- **SOCKS vs VPN**: Quando usar cada um
- **SOCKS vs Tunelamento SSH**: Tunelamento vs proxying
- **SOCKS vs Tor**: Anonimato vs trocas de desempenho

---

## Pensamentos Finais

SOCKS5 é o **protocolo de proxy preferido** para automação de navegador consciente da privacidade, oferecendo vantagens arquitetônicas fundamentais sobre proxies HTTP:

- **Flexibilidade de protocolo** permite proxyar qualquer aplicação TCP/UDP
- **Operação na camada de sessão** impede inspeção de dados da aplicação
- **Resolução de DNS remota** protege padrões de navegação
- **Resistência a MITM** preserva criptografia TLS ponta-a-ponta

Embora proxies HTTP dominem ambientes corporativos devido a capacidades de filtragem de conteúdo, **SOCKS5 é a escolha superior** para automação que requer furtividade, segurança e flexibilidade de protocolo.

**Ponto Chave**: Use SOCKS5 para privacidade e automação, proxies HTTP para filtragem corporativa.

**Próximos Passos:**
1. Leia **[Detecção de Proxy](./proxy-detection.md)** para entender como até mesmo o SOCKS5 pode ser detectado
2. Aprenda **[Construindo Proxies](./build-proxy.md)** para implementar seu próprio servidor SOCKS5
3. Configure SOCKS5 no Pydoll usando **[Configuração de Proxy](../../features/configuration/proxy.md)**

---