# Arquitetura do Protocolo SOCKS

SOCKS (SOCKet Secure) é um protocolo de proxy que opera entre as camadas de transporte e aplicação da pilha de rede (comumente descrito como Camada 5 no modelo OSI). Diferente dos proxies HTTP, que analisam e compreendem o tráfego HTTP, os proxies SOCKS encaminham conexões TCP e UDP brutas sem inspecionar seu conteúdo. Esse design agnóstico a protocolo torna o SOCKS a escolha preferida para automação focada em privacidade: o proxy nunca precisa analisar suas requisições, injetar cabeçalhos ou terminar conexões TLS.

Este documento cobre como o SOCKS funciona no nível do protocolo, as diferenças entre SOCKS4 e SOCKS5, o tratamento de autenticação no Chrome, o comportamento de resolução de DNS e a configuração prática no Pydoll.

!!! info "Navegação do Módulo"
    - [Proxies HTTP/HTTPS](./http-proxies.md): Proxy na camada de aplicação
    - [Fundamentos de Rede](./network-fundamentals.md): TCP/IP, UDP, modelo OSI
    - [Visão Geral de Rede e Segurança](./index.md): Introdução do módulo
    - [Detecção de Proxy](./proxy-detection.md): Níveis de anonimato e evasão de detecção
    - [Construindo Proxies](./build-proxy.md): Implementação do SOCKS5 do zero

    Para configuração prática, veja [Configuração de Proxy](../../features/configuration/proxy.md).

## Como o SOCKS Difere dos Proxies HTTP

A diferença fundamental está no que cada proxy pode ver e fazer. Um proxy HTTP opera na camada de aplicação e compreende HTTP: ele pode ler URLs, cabeçalhos, cookies e corpos de requisição (para tráfego não criptografado), modificá-los em trânsito, armazenar respostas em cache e injetar seus próprios cabeçalhos como `Via` e `X-Forwarded-For`. Isso é poderoso para filtragem de conteúdo, mas significa que você precisa confiar no operador do proxy com os dados da sua aplicação.

Um proxy SOCKS opera abaixo da camada de aplicação. Ele vê apenas o endereço de destino, a porta e o volume de dados sendo transferido. Ele não analisa, modifica ou sequer compreende qual protocolo está fluindo através dele. HTTP, HTTPS, FTP, SSH, WebSocket ou qualquer protocolo customizado parecem todos iguais para um proxy SOCKS: apenas bytes sendo retransmitidos entre dois endpoints.

Isso tem uma implicação prática direta. Quando você envia uma requisição HTTPS através de um proxy SOCKS5, o proxy vê `example.com:443` e o fluxo TLS criptografado. Ele não consegue ler a URL, os cabeçalhos, os cookies ou o conteúdo da resposta. Ele não adiciona cabeçalhos identificadores. Ele não precisa terminar o TLS. O túnel criptografado funciona de ponta a ponta entre seu navegador e o servidor de destino.

No entanto, é importante entender o que o SOCKS não fornece. SOCKS é um protocolo de proxy, não um protocolo de criptografia. O nome "SOCKet Secure" refere-se à travessia segura de firewalls, não à segurança criptográfica. Se você enviar tráfego HTTP não criptografado através de um proxy SOCKS5, o operador do proxy pode ler os bytes passando através dele, mesmo que o proxy não tenha sido projetado para inspecioná-los. Para criptografia real, você precisa de TLS/HTTPS sobre SOCKS, ou de um túnel criptografado (SSH, VPN) envolvendo a conexão SOCKS.

!!! note "Modelo de Confiança"
    Com proxies HTTP, você confia no operador do proxy para não registrar seu histórico de navegação, roubar tokens, modificar respostas ou realizar ataques MITM. Com SOCKS5, você confia no proxy apenas para encaminhar pacotes corretamente e não registrar metadados de conexão. A superfície de ataque é menor, mas não é zero.

## SOCKS4 vs SOCKS5

O SOCKS possui duas versões de uso comum. O SOCKS4 foi desenvolvido pela NEC no início dos anos 1990 como um padrão informal sem RFC. O SOCKS5 foi padronizado como RFC 1928 em 1996 para resolver as limitações do SOCKS4.

| Característica | SOCKS4 | SOCKS5 |
|---------|--------|--------|
| Padrão | Sem RFC oficial (de facto, 1992) | RFC 1928 (1996) |
| Autenticação | Apenas identificação (campo USERID, sem senha) | Múltiplos métodos (nenhum, usuário/senha, GSSAPI) |
| Versão IP | Apenas IPv4 | IPv4 e IPv6 |
| Suporte UDP | Não | Sim (comando UDP ASSOCIATE) |
| Resolução DNS | Lado do cliente (extensão SOCKS4A adiciona lado do servidor) | Lado do servidor ao usar nomes de domínio (ATYP=0x03) |
| Suporte a protocolo | Apenas TCP | TCP e UDP |

O SOCKS5 é superior em todos os aspectos práticos. Use SOCKS4 apenas se o proxy não suportar SOCKS5.

## O Handshake SOCKS5

O processo de conexão SOCKS5 segue a RFC 1928 e consiste em três fases: negociação de método, autenticação opcional e a requisição de conexão.

```mermaid
sequenceDiagram
    participant Client
    participant SOCKS5 as SOCKS5 Proxy
    participant Server as Target Server

    Note over Client,SOCKS5: Phase 1: Method Negotiation
    Client->>SOCKS5: Hello [VER=5, NMETHODS, METHODS]
    SOCKS5->>Client: Method Selected [VER=5, METHOD]

    Note over Client,SOCKS5: Phase 2: Authentication (if required)
    Client->>SOCKS5: Auth Request [VER=1, ULEN, UNAME, PLEN, PASSWD]
    SOCKS5->>Client: Auth Response [VER=1, STATUS]

    Note over Client,SOCKS5: Phase 3: Connection Request
    Client->>SOCKS5: Connect [VER=5, CMD=CONNECT, DST.ADDR, DST.PORT]
    SOCKS5->>Server: Establish TCP connection
    Server-->>SOCKS5: Connection established
    SOCKS5->>Client: Reply [VER=5, REP=SUCCESS, BND.ADDR, BND.PORT]

    Note over Client,Server: Data relay (proxied)
    Client->>SOCKS5: Application data
    SOCKS5->>Server: Forward data
    Server->>SOCKS5: Response data
    SOCKS5->>Client: Forward response
```

### Fase 1: Negociação de Método

O cliente abre uma conexão TCP com o proxy e envia uma saudação contendo a versão do protocolo (sempre `0x05` para SOCKS5) e uma lista de métodos de autenticação que ele suporta.

```python
# Client Hello
[
    0x05,        # VER: Protocol version (5)
    0x02,        # NMETHODS: Number of methods offered
    0x00, 0x02   # METHODS: No auth (0x00) and Username/Password (0x02)
]
```

O proxy responde com o método que ele seleciona. Se o proxy exigir autenticação e o cliente tiver oferecido `0x02` (usuário/senha), o proxy o seleciona. Se nenhum método aceitável foi oferecido, o proxy responde com `0xFF` e fecha a conexão.

```python
# Server response
[
    0x05,   # VER: Protocol version (5)
    0x02    # METHOD: Username/Password selected
]
```

Códigos de método definidos pela RFC 1928: `0x00` = sem autenticação, `0x01` = GSSAPI, `0x02` = usuário/senha (RFC 1929), `0x03-0x7F` = atribuídos pela IANA, `0x80-0xFE` = reservados para métodos privados, `0xFF` = nenhum método aceitável.

### Fase 2: Autenticação

Se o proxy selecionou o método `0x02`, o cliente envia as credenciais seguindo a RFC 1929. A subnegociação usa seu próprio número de versão (`0x01`, não `0x05`).

```python
# Client authentication
[
    0x01,              # VER: Subnegotiation version (1)
    len(username),     # ULEN: Username length (max 255)
    *username_bytes,   # UNAME: Username
    len(password),     # PLEN: Password length (max 255)
    *password_bytes    # PASSWD: Password
]

# Server response
[
    0x01,   # VER: Subnegotiation version (1)
    0x00    # STATUS: 0 = success, non-zero = failure
]
```

As credenciais são transmitidas em texto claro durante este handshake. Isso é inerente ao protocolo SOCKS5 (RFC 1929). Para ambientes sensíveis, envolva a conexão SOCKS em um túnel SSH ou VPN.

### Fase 3: Requisição de Conexão

Após a autenticação ser bem-sucedida (ou se nenhuma autenticação foi necessária), o cliente envia uma requisição de conexão especificando o comando, o endereço de destino e a porta.

```python
[
    0x05,          # VER: Protocol version (5)
    0x01,          # CMD: 1=CONNECT, 2=BIND, 3=UDP ASSOCIATE
    0x00,          # RSV: Reserved
    0x03,          # ATYP: 1=IPv4 (4 bytes), 3=Domain (length+name), 4=IPv6 (16 bytes)
    len(domain),   # Domain length (only for ATYP=0x03)
    *domain_bytes, # Domain name
    *port_bytes    # Port (2 bytes, big-endian)
]
```

O tipo de endereço (ATYP) determina o formato: `0x01` significa que 4 bytes de endereço IPv4 seguem, `0x04` significa 16 bytes de IPv6, e `0x03` significa um byte de comprimento seguido pelo nome do domínio. Quando o cliente envia um nome de domínio (ATYP=0x03), o proxy resolve o DNS do seu lado, o que previne vazamentos de DNS para a rede local do cliente.

O proxy conecta ao destino e responde com uma resposta:

```python
[
    0x05,       # VER: Protocol version (5)
    0x00,       # REP: 0x00=success, 0x01-0x08=various errors
    0x00,       # RSV: Reserved
    0x01,       # ATYP: Address type of bound address
    *bind_addr, # BND.ADDR: Address the proxy bound to
    *bind_port  # BND.PORT: Port the proxy bound to
]
```

Códigos de resposta: `0x00` sucesso, `0x01` falha geral, `0x02` conexão não permitida, `0x03` rede inacessível, `0x04` host inacessível, `0x05` conexão recusada, `0x06` TTL expirado, `0x07` comando não suportado, `0x08` tipo de endereço não suportado.

Após uma resposta bem-sucedida, o proxy começa a retransmitir dados bidirecionalmente. Todo o handshake SOCKS5 é um protocolo binário, tornando-o mais eficiente que o HTTP baseado em texto, mas mais difícil de depurar sem dumps hexadecimais.

## Suporte UDP

O SOCKS5 suporta proxy UDP através do comando `UDP ASSOCIATE` (CMD=0x03). Isso funciona de forma diferente do proxy TCP: o cliente envia uma requisição UDP ASSOCIATE pela conexão de controle TCP, e o proxy responde com um endereço e porta de retransmissão. O cliente então envia datagramas UDP para essa retransmissão, e o proxy os encaminha para seus destinos.

```mermaid
sequenceDiagram
    participant Client
    participant SOCKS5
    participant UDP_Server as UDP Server

    Note over Client,SOCKS5: TCP control connection (handshake + auth)
    Client->>SOCKS5: UDP ASSOCIATE request (CMD=0x03)
    SOCKS5->>Client: Relay address and port

    Note over Client,SOCKS5: UDP data transfer
    Client->>SOCKS5: UDP datagram to relay
    SOCKS5->>UDP_Server: Forward datagram
    UDP_Server->>SOCKS5: Response datagram
    SOCKS5->>Client: Forward response

    Note over Client,SOCKS5: TCP control connection stays open
```

Cada datagrama UDP enviado através da retransmissão inclui um pequeno cabeçalho com o endereço e a porta de destino:

```python
[
    0x00, 0x00,    # RSV: Reserved
    0x00,          # FRAG: Fragment number (0 = no fragmentation)
    0x01,          # ATYP: Address type
    *dst_addr,     # DST.ADDR: Destination address
    *dst_port,     # DST.PORT: Destination port
    *data          # DATA: Application data
]
```

A conexão de controle TCP deve permanecer aberta durante toda a duração da associação UDP. Se ela for fechada, o proxy descarta a retransmissão UDP.

!!! warning "UDP no Chrome"
    O Chrome não utiliza UDP ASSOCIATE do SOCKS5 para nenhum tráfego. Mesmo quando configurado com um proxy SOCKS5, o Chrome apenas faz proxy de conexões TCP. WebRTC, DNS-sobre-UDP e outros tráfegos UDP não são roteados pelo proxy SOCKS5. Isso significa que vazamentos de IP via WebRTC ainda são possíveis com SOCKS5 no Chrome. Use `--force-webrtc-ip-handling-policy=disable_non_proxied_udp` ou `webrtc_leak_protection = True` do Pydoll para mitigar isso. Para mais detalhes, veja [Fundamentos de Rede: WebRTC e Vazamento de IP](./network-fundamentals.md#webrtc-and-ip-leakage).

!!! tip "Alternativas Modernas de Proxy UDP"
    Para cenários que exigem suporte UDP completo além do que a implementação SOCKS5 do Chrome oferece, considere Shadowsocks (protocolo criptografado semelhante ao SOCKS com UDP nativo), WireGuard (VPN com excelente desempenho) ou V2Ray/VMess (framework de proxy flexível com tratamento UDP abrangente).

## Resolução de DNS

Um equívoco comum é que proxies HTTP vazam consultas DNS enquanto proxies SOCKS5 não. A realidade no Chrome é mais nuançada.

Quando o Chrome é configurado com qualquer proxy (HTTP, HTTPS ou SOCKS5), ele envia nomes de host para o proxy em vez de resolver DNS localmente. Para proxies HTTP, o nome do host aparece na requisição `CONNECT host:443`. Para SOCKS5, ele aparece na requisição de conexão com ATYP=0x03 (nome de domínio). Em ambos os casos, o proxy resolve o DNS do seu lado, e o Chrome não faz consultas DNS locais para tráfego direcionado ao proxy.

A verdadeira diferença de privacidade de DNS entre os dois tipos de proxy não é quem resolve o DNS, mas o que o proxy vê na camada de aplicação. Um proxy HTTP vê a URL completa para requisições não criptografadas e o nome do host para requisições CONNECT. Um proxy SOCKS5 vê apenas o nome do host de destino e a porta como parâmetros opacos de conexão.

No entanto, existe uma ressalva importante: o prefetcher de DNS do Chrome pode fazer consultas DNS locais para nomes de host encontrados no conteúdo da página, mesmo quando um proxy está configurado. Isso pode vazar os domínios que você está navegando para o seu resolvedor DNS local. Para prevenir isso, desabilite o prefetching de DNS ou use a flag `--host-resolver-rules="MAP * ~NOTFOUND , EXCLUDE 127.0.0.1"`.

!!! note "`socks5://` vs `socks5h://`"
    Muitas ferramentas fora do Chrome distinguem entre `socks5://` (cliente resolve DNS) e `socks5h://` (proxy resolve DNS, o "h" significa hostname). O Chrome sempre resolve DNS do lado do proxy para SOCKS5, comportando-se como `socks5h://` independentemente de qual esquema você use. Mas se você usar ferramentas como `curl`, Firefox ou bibliotecas Python junto com o Pydoll, a distinção importa: sempre use `socks5h://` para prevenir vazamentos de DNS.

## SOCKS5 e Resistência a MITM

O SOCKS5 é frequentemente descrito como "resistente a MITM". Isso é verdade em um sentido específico: como o SOCKS5 não compreende nem interage com TLS, ele não tem mecanismo para terminar uma conexão TLS e recriptografá-la. Um proxy SOCKS5 simplesmente retransmite bytes criptografados sem modificação.

Um proxy HTTP, por outro lado, pode realizar terminação TLS (MITM) apresentando seu próprio certificado ao cliente, descriptografando o tráfego, inspecionando ou modificando-o, e recriptografando-o em direção ao servidor. Isso exige que o cliente confie no certificado CA do proxy, e é detectável através de certificate pinning e logs de Certificate Transparency. O comportamento normal de um proxy HTTP com HTTPS (usando CONNECT) é criar um túnel transparente sem terminação, mas a possibilidade arquitetônica de MITM existe.

Com SOCKS5, a terminação TLS não é possível no nível do protocolo. O proxy não consegue se inserir no handshake TLS porque ele não analisa os dados da aplicação fluindo através dele. A criptografia de ponta a ponta entre cliente e servidor é preservada por design.

Vale notar que é o TLS que fornece a proteção criptográfica real, não o SOCKS5 em si. Se você enviar HTTP não criptografado através de um proxy SOCKS5, o operador do proxy pode ler tudo. A vantagem de segurança do SOCKS5 é arquitetônica (ele não exige nem permite terminação TLS), não criptográfica.

## TLS e Browser Fingerprinting Através do SOCKS5

Uma limitação importante para entender: o SOCKS5 não altera o fingerprint do seu navegador. O handshake TLS (ClientHello) passa pelo proxy SOCKS5 byte por byte, o que significa que o servidor de destino vê o fingerprint JA3/JA4 exato do seu navegador. O mesmo se aplica aos frames HTTP/2 SETTINGS, à ordenação de cabeçalhos específica do navegador e a todos os outros sinais de fingerprinting na camada de aplicação.

O SOCKS5 oculta seu endereço IP e impede que o proxy injete cabeçalhos identificadores. Ele não ajuda com nenhuma forma de browser fingerprinting ou fingerprinting comportamental. Para uma estratégia completa de evasão, você precisa abordar o fingerprinting em múltiplas camadas. Veja [Técnicas de Evasão](../fingerprinting/evasion-techniques.md) para detalhes.

## Autenticação SOCKS5 no Chrome

O Chrome não suporta autenticação por usuário/senha do SOCKS5. Esta é uma limitação de longa data rastreada como [Chromium Issue #40323993](https://issues.chromium.org/issues/40323993). Quando o Chrome realiza a negociação de método SOCKS5, ele oferece apenas o método `0x00` (sem autenticação). Se o proxy exigir autenticação, a conexão falha silenciosamente.

Isso é fundamentalmente diferente da autenticação de proxy HTTP. Proxies HTTP autenticam via códigos de status HTTP (`407 Proxy Authentication Required`), que o Chrome trata através do domínio Fetch no CDP. O Pydoll intercepta esses eventos `Fetch.authRequired` e responde com as credenciais armazenadas automaticamente. A autenticação SOCKS5, por outro lado, acontece durante um handshake de protocolo binário na camada de sessão, antes que qualquer tráfego HTTP exista. Não há HTTP 407, nenhum evento `Fetch.authRequired` e nenhuma forma de ferramentas baseadas em CDP injetarem credenciais nesse processo.

Configurar `--proxy-server=socks5://user:pass@proxy:1080` não funciona. O Chrome ignora silenciosamente as credenciais embutidas.

### SOCKS5Forwarder do Pydoll

A solução padrão é um proxy forwarder local: um servidor SOCKS5 leve rodando no localhost que aceita conexões não autenticadas do Chrome e as encaminha para o proxy remoto com autenticação completa.

```mermaid
sequenceDiagram
    participant Chrome
    participant Forwarder as Local Forwarder<br/>(127.0.0.1:1081)
    participant Remote as Remote SOCKS5 Proxy<br/>(proxy:1080)
    participant Server as Destination Server

    Note over Chrome,Forwarder: No authentication
    Chrome->>Forwarder: SOCKS5 Hello [methods: 0x00]
    Forwarder->>Chrome: Method selected [0x00]
    Chrome->>Forwarder: CONNECT example.com:443

    Note over Forwarder,Remote: With authentication
    Forwarder->>Remote: SOCKS5 Hello [methods: 0x02]
    Remote->>Forwarder: Method selected [0x02]
    Forwarder->>Remote: Auth [username, password]
    Remote->>Forwarder: Auth OK
    Forwarder->>Remote: CONNECT example.com:443
    Remote->>Server: TCP connection
    Remote->>Forwarder: Connect OK

    Forwarder->>Chrome: Connect OK

    Note over Chrome,Server: Bidirectional data relay
    Chrome->>Forwarder: TLS + application data
    Forwarder->>Remote: Forward
    Remote->>Server: Forward
    Server->>Remote: Response
    Remote->>Forwarder: Forward
    Forwarder->>Chrome: Forward
```

O Pydoll fornece um `SOCKS5Forwarder` integrado no módulo `pydoll.utils`. É uma implementação async pura em Python, sem dependências externas, que lida com o handshake SOCKS5 completo com o proxy remoto, incluindo autenticação por usuário/senha (RFC 1929), tipos de endereço IPv4, IPv6 e domínio.

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
        local_port=1081,  # Use 0 for auto-assigned port
    )
    async with forwarder:
        options = ChromiumOptions()
        options.add_argument(f'--proxy-server=socks5://127.0.0.1:{forwarder.local_port}')

        async with Chrome(options=options) as browser:
            tab = await browser.start()
            await tab.go_to('https://httpbin.org/ip')

asyncio.run(main())
```

O forwarder também pode ser executado como ferramenta CLI standalone para testes ou uso com outras aplicações:

```bash
python -m pydoll.utils.socks5_proxy_forwarder \
    --remote-host proxy.example.com \
    --remote-port 1080 \
    --username myuser \
    --password mypass \
    --local-port 1081
```

O forwarder se vincula a `127.0.0.1` por padrão, tornando-o acessível apenas da sua máquina. Nunca vincule a `0.0.0.0` em produção, pois isso exporia um proxy SOCKS5 sem autenticação para a rede. As credenciais nunca são registradas em texto claro nos logs. O forwarder adiciona latência sub-milissegundo, já que toda a comunicação acontece pela interface de loopback local.

!!! tip "Ambientes Restritos"
    Alguns ambientes (contêineres Docker, plataformas serverless, VMs endurecidas) podem restringir a vinculação a portas locais. Use `local_port=0` para deixar o SO atribuir uma porta disponível. Se a vinculação local estiver completamente bloqueada, considere usar um proxy HTTP CONNECT, que o Chrome suporta nativamente com autenticação via ProxyManager do Pydoll.

## Configuração Prática

**SOCKS5 básico (sem autenticação):**

```python
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
options.add_argument('--proxy-server=socks5://proxy.example.com:1080')

async with Chrome(options=options) as browser:
    tab = await browser.start()
    await tab.go_to('https://example.com')
```

**SOCKS5 com autenticação (via SOCKS5Forwarder):**

Veja a [seção do SOCKS5Forwarder](#socks5forwarder-do-pydoll) acima.

**Prevenindo vazamentos:**

Para uma configuração SOCKS5 completa, você também deve prevenir vazamentos de WebRTC e DNS prefetch:

```python
options = ChromiumOptions()
options.add_argument('--proxy-server=socks5://proxy.example.com:1080')
options.webrtc_leak_protection = True  # Prevents WebRTC IP leaks
options.add_argument('--disable-quic')  # Forces HTTP/2 over TCP through proxy
```

**Testando sua configuração:**

Sempre verifique sua configuração de proxy com testes de vazamento. Visite [browserleaks.com/ip](https://browserleaks.com/ip) para confirmar seu IP, [browserleaks.com/webrtc](https://browserleaks.com/webrtc) para verificar vazamentos de WebRTC, e [dnsleaktest.com](https://dnsleaktest.com/) para confirmar que o DNS não está vazando.

## Resumo

O SOCKS5 fornece proxy agnóstico a protocolo com uma superfície de confiança menor que a dos proxies HTTP. Ele não analisa, modifica ou injeta nada no seu tráfego. A resolução de DNS acontece do lado do proxy no Chrome. A criptografia TLS é preservada de ponta a ponta. A principal limitação no Chrome é a falta de autenticação SOCKS5 nativa (resolvida pelo `SOCKS5Forwarder` do Pydoll) e a ausência de proxy UDP (mitigada desabilitando o WebRTC ou usando as flags apropriadas do navegador).

O SOCKS5 não altera o fingerprint TLS do seu navegador, as configurações HTTP/2 ou quaisquer características da camada de aplicação. Para evasão completa, combine SOCKS5 com gerenciamento de browser fingerprint e simulação comportamental.

**Próximos passos:**

- [Detecção de Proxy](./proxy-detection.md): Como até mesmo proxies SOCKS5 podem ser detectados
- [Construindo Proxies](./build-proxy.md): Implemente seu próprio servidor SOCKS5
- [Configuração de Proxy](../../features/configuration/proxy.md): Configuração prática de proxy no Pydoll
- [Técnicas de Evasão](../fingerprinting/evasion-techniques.md): Estratégia de evasão multicamada

## Referências

- RFC 1928: SOCKS Protocol Version 5 (1996) - https://datatracker.ietf.org/doc/html/rfc1928
- RFC 1929: Username/Password Authentication for SOCKS V5 (1996) - https://datatracker.ietf.org/doc/html/rfc1929
- RFC 1961: GSS-API Authentication Method for SOCKS V5 (1996) - https://datatracker.ietf.org/doc/html/rfc1961
- RFC 3089: SOCKS-based IPv6/IPv4 Gateway Mechanism (2001) - https://datatracker.ietf.org/doc/html/rfc3089
- Chromium Proxy Documentation - https://chromium.googlesource.com/chromium/src/+/689912289c/net/docs/proxy.md
- Chromium Issue #40323993: SOCKS5 Authentication - https://issues.chromium.org/issues/40323993
- BrowserLeaks: WebRTC Leak Test - https://browserleaks.com/webrtc
- DNS Leak Test - https://dnsleaktest.com/
- IPLeak: Comprehensive Leak Testing - https://ipleak.net
