# Arquitetura de Proxy HTTP/HTTPS

Proxies HTTP são o protocolo de proxy mais comum na internet. Quase toda rede corporativa os utiliza, e a maioria dos serviços de proxy comerciais os oferece como opção padrão. Eles operam na Camada 7 (Aplicação) do modelo OSI, o que significa que entendem HTTP e podem analisar, modificar, cachear e filtrar tráfego. Essa mesma integração profunda com o protocolo também é sua maior limitação: só podem lidar com tráfego HTTP, revelam uso de proxy através de cabeçalhos identificáveis, e não podem fazer proxy de UDP, o que deixa WebRTC e DNS vulneráveis a vazamentos.

Este documento cobre como proxies HTTP funcionam no nível do protocolo, o método CONNECT para tunelamento HTTPS, mecanismos de autenticação e as implicações de protocolos modernos como HTTP/2 e HTTP/3.

!!! info "Navegação do Módulo"
    - [Fundamentos de Rede](./network-fundamentals.md): TCP/IP, UDP, modelo OSI
    - [Proxies SOCKS](./socks-proxies.md): Alternativa agnóstica a protocolo
    - [Detecção de Proxy](./proxy-detection.md): Como evitar detecção

    Para configuração prática, veja [Configuração de Proxy](../../features/configuration/proxy.md).

## Como Proxies HTTP Funcionam

Um proxy HTTP fica entre o cliente e o servidor destino, mantendo duas conexões TCP separadas: uma do cliente para o proxy, e outra do proxy para o servidor destino. Como o proxy entende HTTP, ele pode tomar decisões inteligentes sobre o tráfego que passa por ele.

### Fluxo de Requisição

Quando um cliente é configurado para usar um proxy HTTP, ele envia a requisição HTTP completa para o proxy em vez de diretamente para o servidor destino. A diferença chave de uma requisição direta é que a linha de requisição inclui a URI absoluta, não apenas o caminho. Por exemplo, em vez de `GET /page HTTP/1.1`, o cliente envia `GET http://example.com/page HTTP/1.1`. Isso diz ao proxy para onde encaminhar a requisição.

```mermaid
sequenceDiagram
    participant Client as Navegador Cliente
    participant Proxy as Proxy HTTP
    participant Server as Servidor Destino

    Client->>Proxy: GET http://example.com/page HTTP/1.1<br/>Host: example.com<br/>User-Agent: Mozilla/5.0
    Note over Client,Proxy: Conexão TCP #1

    Note over Proxy: Analisa requisição, verifica auth,<br/>verifica cache, aplica regras

    Proxy->>Server: GET /page HTTP/1.1<br/>Host: example.com<br/>Via: 1.1 proxy.example.com<br/>X-Forwarded-For: 192.168.1.100
    Note over Proxy,Server: Conexão TCP #2

    Server->>Proxy: HTTP/1.1 200 OK<br/>[corpo da resposta]

    Note over Proxy: Cacheia resposta se permitido,<br/>filtra conteúdo, registra transação

    Proxy->>Client: HTTP/1.1 200 OK<br/>Via: 1.1 proxy.example.com<br/>[corpo possivelmente modificado]
```

O proxy recebe a requisição HTTP completa, analisa o método, URL e cabeçalhos, e decide o que fazer. Ele pode verificar credenciais de autenticação, verificar a URL contra uma lista de controle de acesso, procurar uma cópia em cache do recurso e modificar cabeçalhos antes de encaminhar. Então abre uma conexão TCP separada para o servidor destino e envia a requisição, potencialmente com cabeçalhos alterados.

Quando a resposta chega, o proxy pode cacheá-la de acordo com a semântica HTTP (`Cache-Control`, `ETag`), filtrar o conteúdo para malware ou palavras-chave bloqueadas, comprimi-la se o cliente suportar, e registrar a transação antes de encaminhar a resposta de volta ao cliente.

### Cabeçalhos de Proxy e Privacidade

Proxies HTTP comumente adicionam cabeçalhos que revelam sua presença e o endereço IP real do cliente. O cabeçalho `Via` (RFC 9110) identifica o proxy na cadeia de requisição. O cabeçalho `X-Forwarded-For` contém o IP original do cliente, frequentemente formando uma cadeia se múltiplos proxies estão envolvidos. O cabeçalho `X-Forwarded-Proto` indica se a requisição original era HTTP ou HTTPS. Alguns proxies também adicionam `X-Real-IP` como alternativa mais simples ao `X-Forwarded-For`.

Também existe um cabeçalho padronizado `Forwarded` (RFC 7239) que combina toda essa informação em um único campo, por exemplo `Forwarded: for=192.168.1.100;proto=http;by=proxy.example.com`. Na prática, a maioria dos proxies ainda usa as variantes `X-Forwarded-*` já que têm suporte mais amplo.

Clientes legados e alguns navegadores mais antigos também podem enviar um cabeçalho `Proxy-Connection: keep-alive` em vez de `Connection: keep-alive` ao rotear através de um proxy. Este cabeçalho é um indicador bem conhecido de uso de proxy e um sinal clássico de detecção.

!!! danger "Detecção por Cabeçalho"
    Sistemas de detecção procuram a presença de cabeçalhos `Via`, `X-Forwarded-For` ou `Forwarded` para confirmar uso de proxy. Se `X-Real-IP` não corresponde ao IP de conexão, o proxy é confirmado. Proxies sofisticados podem remover esses cabeçalhos, mas muitos serviços de proxy comerciais os deixam por padrão. Sempre verifique o comportamento do seu proxy usando uma ferramenta como [browserleaks.com/ip](https://browserleaks.com/ip).

### Capacidades e Limitações

Como proxies HTTP analisam e entendem o protocolo HTTP, eles podem ler e modificar cada parte de uma requisição e resposta HTTP não criptografada: URLs, cabeçalhos, cookies e corpos. Isso permite que cacheiem respostas inteligentemente, filtrem conteúdo por URL ou palavra-chave, injetem ou removam cabeçalhos, autentiquem usuários e registrem todo o tráfego em detalhes.

O tradeoff é que esse acoplamento profundo com HTTP significa que o proxy é limitado a tráfego HTTP. Ele não pode nativamente fazer proxy de FTP, SSH, SMTP ou protocolos personalizados (embora o método CONNECT, descrito abaixo, forneça uma solução de tunelamento para qualquer protocolo baseado em TCP). Não tem suporte para UDP, o que significa que tráfego WebRTC, consultas DNS e QUIC/HTTP/3 o ignoram completamente. E inspecionar conteúdo HTTPS requer terminação TLS, que quebra a criptografia de ponta a ponta.

## O Método CONNECT: Tunelamento HTTPS

O método CONNECT (RFC 9110, Seção 9.3.6) resolve um problema fundamental: como um proxy HTTP pode encaminhar tráfego criptografado que não pode ler? A resposta é tornar-se um túnel TCP cego.

Quando um cliente quer acessar um site HTTPS através de um proxy, ele envia uma requisição `CONNECT` pedindo ao proxy para estabelecer uma conexão TCP bruta para o destino. Uma vez que o proxy confirma que o túnel está estabelecido, ele para de ser um proxy HTTP completamente e se torna um relay TCP transparente na Camada 4, encaminhando bytes em ambas as direções sem interpretá-los.

```mermaid
sequenceDiagram
    participant Client
    participant Proxy
    participant Server

    Client->>Proxy: CONNECT example.com:443 HTTP/1.1<br/>Host: example.com:443<br/>Proxy-Authorization: Basic dXNlcjpwYXNz
    Note over Client,Proxy: Requisição HTTP não criptografada

    Proxy->>Server: TCP three-way handshake
    Note over Proxy,Server: Conexão TCP estabelecida

    Proxy->>Client: HTTP/1.1 200 Connection Established

    Note right of Proxy: Proxy agora é um relay<br/>TCP transparente (Camada 4)

    Client->>Server: TLS ClientHello
    Note over Client,Server: Handshake TLS (proxy vê<br/>isso em texto plano)
    Server->>Client: TLS ServerHello, Certificate

    Client->>Server: Requisição HTTP/2 criptografada
    Server->>Client: Resposta HTTP/2 criptografada

    Note over Proxy: Proxy encaminha cegamente<br/>todos os dados criptografados
```

### A Requisição CONNECT

A requisição CONNECT é mínima. O método é `CONNECT`, a URI de requisição é o `host:port` de destino (não um caminho), e inclui autenticação se o proxy a requer. Não há corpo de requisição. O proxy valida as credenciais, verifica suas regras de controle de acesso e abre uma conexão TCP para o host e porta especificados. Se tudo for bem-sucedido, ele envia de volta `HTTP/1.1 200 Connection Established` seguido por uma linha em branco. Após essa linha em branco, a conversação HTTP termina e o proxy se torna um relay transparente.

### Visibilidade Após CONNECT

Uma vez que o túnel é estabelecido, a visibilidade do proxy é limitada. Ele sabe o hostname e porta de destino da requisição CONNECT. Ele pode observar o timing da conexão (quando foi estabelecida e por quanto tempo), o volume de dados transferidos em cada direção, e quando qualquer lado termina a conexão. Ele também pode observar o handshake TLS que se segue, o que é particularmente relevante.

A mensagem TLS ClientHello, enviada imediatamente após o túnel ser estabelecido, é transmitida em texto plano. O proxy (e qualquer observador de rede) pode ler diretamente a versão TLS, a lista completa de cipher suites suportadas, as extensões e seus parâmetros, as curvas elípticas oferecidas, e a extensão SNI (Server Name Indication) que contém o hostname destino. Esta é exatamente a informação usada para TLS fingerprinting (JA3/JA4). Veja [Network Fingerprinting](../fingerprinting/network-fingerprinting.md) para detalhes.

O que o proxy não pode ver é os dados de aplicação criptografados: métodos HTTP, URLs, cabeçalhos de requisição e resposta, cookies, tokens de sessão e conteúdo de resposta são todos criptografados dentro do túnel TLS.

!!! note "SNI e Encrypted Client Hello (ECH)"
    A extensão SNI no ClientHello revela o hostname destino em texto plano, que é redundante com a requisição CONNECT no cenário de proxy mas relevante para outros observadores de rede. Encrypted Client Hello (ECH), atualmente sendo implantado, visa criptografar o SNI para resolver esse vazamento. No entanto, a adoção do ECH ainda é limitada e requer suporte tanto do cliente quanto do servidor.

### CONNECT para Protocolos Não-HTTPS

Embora CONNECT seja usado principalmente para HTTPS, ele pode tunelar qualquer protocolo baseado em TCP. Uma conexão IMAPS na porta 993, uma conexão SSH na porta 22 ou FTP-over-TLS na porta 990 todos funcionam através de um túnel CONNECT. O proxy não precisa entender esses protocolos porque após o túnel ser estabelecido, ele está simplesmente retransmitindo bytes.

Na prática, muitos proxies corporativos restringem CONNECT à porta 443 (HTTPS) para prevenir abuso. Tentar `CONNECT example.com:22` para SSH frequentemente retornará `403 Forbidden`.

### O Dilema do HTTPS

Proxies HTTP enfrentam uma escolha fundamental com tráfego criptografado. Com a abordagem de túnel CONNECT, a criptografia de ponta a ponta é preservada, o cliente verifica o certificado do servidor diretamente, e certificate pinning funciona normalmente. Mas o proxy não pode inspecionar, cachear ou filtrar o conteúdo criptografado.

A alternativa é terminação TLS (MITM), onde o proxy descriptografa o tráfego HTTPS, inspeciona o conteúdo e re-criptografa antes de encaminhar. Isso requer instalar o certificado CA do proxy no cliente, quebra a criptografia de ponta a ponta e é detectável através de certificate pinning e logs de Certificate Transparency. A maioria dos proxies corporativos usa essa abordagem para filtragem de conteúdo e scanning de segurança, enquanto proxies focados em privacidade usam túneis CONNECT cegos.

Para web scraping e automação, essa distinção importa para TLS fingerprinting. Se o proxy realiza terminação TLS, o fingerprint TLS que o servidor destino vê pertence ao proxy, não ao seu navegador. Se você está usando um túnel CONNECT, o fingerprint é preservado de ponta a ponta. Dependendo da sua estratégia de evasão, uma abordagem pode ser preferível à outra.

| Aspecto | HTTP (sem CONNECT) | HTTPS (túnel CONNECT) |
|---------|--------------------|-----------------------|
| Visibilidade do proxy | Requisição/resposta HTTP completa | Apenas host:porta destino + TLS ClientHello |
| Criptografia | Nenhuma (a menos que terminação TLS) | TLS de ponta a ponta |
| Caching | Sim, baseado em semântica HTTP | Não (conteúdo criptografado) |
| Filtragem de conteúdo | Sim | Não (apenas bloqueio baseado em hostname) |
| Modificação de cabeçalhos | Sim | Não (cabeçalhos criptografados) |
| Visibilidade de URL | URL completa | Apenas hostname (via CONNECT e SNI) |
| Suporte a protocolo | Apenas HTTP | Qualquer protocolo sobre TCP |

## Proxies HTTPS (TLS para o Proxy)

Uma distinção que vale esclarecer é a diferença entre fazer proxy de tráfego HTTPS e conectar ao próprio proxy via HTTPS. Quando você configura `--proxy-server=https://proxy:port` em vez de `http://proxy:port`, a conexão entre seu navegador e o proxy é criptografada com TLS. Isso protege suas credenciais de autenticação do proxy de serem interceptadas na rede local e esconde até o hostname CONNECT de observadores locais, já que está encapsulado dentro da conexão TLS para o proxy.

O Chrome suporta isso via o esquema `https://` em `--proxy-server`. É particularmente importante ao usar um proxy em redes não confiáveis (Wi-Fi público, hospedagem compartilhada), onde a conexão entre você e o proxy é o elo mais fraco.

## Autenticação

A autenticação de proxy HTTP usa códigos de status e cabeçalhos HTTP padrão, seguindo a RFC 9110. Quando um proxy requer autenticação, ele responde com `407 Proxy Authentication Required` e um cabeçalho `Proxy-Authenticate` indicando quais esquemas de autenticação suporta. O cliente então retransmite a requisição com um cabeçalho `Proxy-Authorization` contendo as credenciais.

### Esquemas de Autenticação

Existem vários esquemas de autenticação, cada um com características de segurança diferentes.

**Basic** (RFC 7617) é o mais simples. O cliente envia `Proxy-Authorization: Basic <base64(username:password)>`. Base64 é uma codificação, não criptografia, então as credenciais são trivialmente reversíveis. Qualquer um que intercepte o cabeçalho pode decodificá-lo instantaneamente e reusá-lo indefinidamente já que não há proteção contra replay. Auth Basic deve ser usado apenas sobre conexões criptografadas com TLS.

**Digest** (RFC 7616) usa um mecanismo de challenge-response. O proxy envia um nonce aleatório, e o cliente computa um hash do username, password, nonce e URI da requisição. A senha nunca é transmitida, e o nonce fornece proteção contra replay. A versão original usa MD5, que é rápido o suficiente para brute-force eficiente, embora a RFC 7616 tenha adicionado suporte a SHA-256. Auth Digest é raramente implementado por serviços de proxy modernos.

**NTLM** é o protocolo proprietário de challenge-response da Microsoft, comum em ambientes corporativos Windows. Usa uma negociação de três etapas (Tipo 1 negociação, Tipo 2 challenge, Tipo 3 autenticação) e integra com Active Directory para single sign-on. NTLMv1 usa DES (quebrado), e NTLMv2 usa HMAC-MD5 (considerado fraco pelos padrões modernos). A Microsoft recomenda Kerberos sobre NTLM para novas implantações. NTLM é vinculado à conexão, o que significa que quebra com multiplexação HTTP/2.

**Negotiate** (RFC 4559) usa SPNEGO para selecionar entre Kerberos e NTLM, preferindo Kerberos. Kerberos oferece a segurança mais forte (criptografia AES, autenticação mútua, tickets com tempo limitado) mas requer infraestrutura Active Directory, máquinas no domínio e sincronização precisa de relógio. Em automação de navegador, Kerberos é difícil de configurar programaticamente.

| Esquema | Segurança | Mecanismo | Notas Práticas |
|---------|-----------|-----------|----------------|
| Basic | Baixa | Credenciais codificadas em Base64 | Suporte universal. Usar apenas sobre TLS. |
| Digest | Média | Challenge-response com MD5/SHA-256 | Proteção contra replay via nonce. Raramente implementado. |
| NTLM | Média | Challenge-response (NT hash) | SSO Windows. Proprietário, vulnerabilidades conhecidas. |
| Negotiate | Alta | Kerberos/SPNEGO | Mais forte. Requer Active Directory. |

### Autenticação no Pydoll

O Chrome não suporta credenciais de proxy inline na flag `--proxy-server`. Escrever `--proxy-server=http://user:pass@proxy:port` não funciona: o Chrome silenciosamente ignora a porção `user:pass` e conecta sem autenticação.

O Pydoll resolve isso transparentemente através do seu `ProxyManager`. Quando você fornece uma URL de proxy com credenciais embutidas, o Pydoll extrai o username e password, remove-os da URL antes de passá-la ao Chrome, e usa o domínio CDP Fetch para interceptar respostas `407 Proxy Authentication Required` e automaticamente fornecer as credenciais via `Fetch.continueWithAuth`. Essa abordagem funciona para todos os esquemas de autenticação que o Chrome suporta (Basic, Digest, NTLM, Negotiate) sem o Pydoll precisar implementar a lógica específica do protocolo.

```python
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
# Pydoll extrai credenciais, limpa a URL e lida com 407 via CDP
options.add_argument('--proxy-server=http://user:pass@proxy.example.com:8080')

async with Chrome(options=options) as browser:
    tab = await browser.start()
    await tab.go_to('https://example.com')
```

!!! tip "Melhores Práticas de Autenticação"
    Sempre use conexões de proxy criptografadas com TLS (proxy HTTPS ou túnel SSH) para proteger credenciais em trânsito. Prefira Bearer tokens para proxies de API já que são revogáveis e com tempo limitado. Nunca use auth Basic sobre uma conexão HTTP não criptografada para o proxy. Não codifique credenciais no código-fonte; use variáveis de ambiente.

## Protocolos Modernos e Proxy

### HTTP/2

HTTP/2 introduziu multiplexação, enquadramento binário e compressão de cabeçalhos HPACK, que mudam fundamentalmente como proxies lidam com conexões. No HTTP/1.1, cada requisição ocupa uma conexão sequencialmente (pipelining existe mas é desabilitado na prática, então navegadores contornam isso abrindo seis conexões paralelas por host). No HTTP/2, uma única conexão TCP carrega múltiplos streams concorrentes, cada um com sua própria requisição e resposta.

Para proxies, isso significa gerenciar IDs de stream, prioridades e janelas de controle de fluxo em ambos os lados da conexão. O proxy deve traduzir entre IDs de stream no lado do cliente e do servidor, manter árvores de prioridade e lidar com controle de fluxo por stream. Isso é significativamente mais complexo que o simples encaminhamento de requisição-resposta do HTTP/1.1.

Da perspectiva de fingerprinting, metadados de stream HTTP/2 (tamanhos de janela, configurações de prioridade, ordenação de cabeçalhos dentro do HPACK) podem fazer fingerprint de clientes individuais mesmo quando múltiplos usuários compartilham o mesmo proxy.

| Recurso | HTTP/1.1 | HTTP/2 |
|---------|----------|--------|
| Conexões | Sequencial por conexão (navegadores abrem 6 em paralelo) | Múltiplos streams concorrentes sobre uma conexão |
| Multiplexação | Não (head-of-line blocking) | Sim (apenas em nível de stream) |
| Compressão de Cabeçalhos | Nenhuma | HPACK |
| Complexidade do Proxy | Encaminhamento simples de requisição/resposta | Mapeamento de ID de stream, gerenciamento de prioridade |

No HTTP/2, o método CONNECT foi estendido pela RFC 8441 para suportar um pseudo-cabeçalho `:protocol`, habilitando tunelamento WebSocket e outras atualizações de protocolo diretamente dentro de streams HTTP/2 sem requerer conexões separadas.

### HTTP/3 e QUIC

HTTP/3 roda sobre QUIC (RFC 9000), que é um protocolo de transporte baseado em UDP. Isso introduz desafios fundamentais para proxies HTTP. Proxies HTTP tradicionais operam sobre TCP e não podem lidar com o tráfego UDP do QUIC. Conexões QUIC podem sobreviver a mudanças de IP (migração de conexão), complicando o gerenciamento de sessão do proxy. E QUIC criptografa quase tudo, incluindo metadados de nível de transporte que eram anteriormente visíveis.

Fazer proxy de QUIC requer CONNECT-UDP (RFC 9298), um novo método para estabelecer túneis UDP através de proxies HTTP. A maioria dos proxies tradicionais, incluindo muitos serviços comerciais, ainda não suporta isso. Navegadores fazem fallback para HTTP/2 sobre TCP quando o proxy não suporta QUIC, o que significa que mais metadados podem vazar do que esperado se você estava contando com o transporte criptografado do HTTP/3.

Em cenários de automação, considere desabilitar QUIC com a flag do Chrome `--disable-quic` para forçar HTTP/2 sobre TCP. Isso garante que todo tráfego passe pelo seu proxy e elimina o risco de vazamentos baseados em UDP do QUIC.

| Aspecto | TCP + TLS (HTTP/1.1, HTTP/2) | QUIC/UDP (HTTP/3) |
|---------|------------------------------|-------------------|
| Transporte | TCP (orientado a conexão) | UDP (sem conexão) |
| Handshake | TCP + TLS separados (2 RTT) | Combinado (0-1 RTT) |
| Head-of-line blocking | Sim (nível TCP) | Não (apenas nível de stream) |
| Migração de conexão | Não suportado | Suportado (sobrevive a mudanças de IP) |
| Compatibilidade com proxy | Excelente | Limitada (requer suporte a relay UDP) |

!!! warning "Downgrade de Protocolo"
    Quando um proxy não suporta HTTP/3, o navegador silenciosamente faz fallback para HTTP/2 ou HTTP/1.1. Este downgrade pode expor metadados (cabeçalhos, padrões de timing) que HTTP/3 teria criptografado. Monitore seu tráfego para entender sua versão de protocolo real, e esteja ciente de que a adoção do HTTP/3 varia por região e CDN.

## Resumo

Proxies HTTP fornecem funcionalidade rica ao custo de escopo limitado e preocupações de privacidade. Eles podem inspecionar, cachear e filtrar tráfego HTTP, mas não podem lidar com protocolos não-HTTP, tráfego UDP ou conteúdo HTTPS sem quebrar a criptografia. Sua presença é revelada através de cabeçalhos identificáveis a menos que explicitamente removidos.

Para automação, o túnel CONNECT é o recurso mais relevante: ele preserva a criptografia TLS de ponta a ponta enquanto dá ao proxy apenas visibilidade em nível de hostname. O Pydoll lida com autenticação de proxy transparentemente através do domínio CDP Fetch, suportando todos os esquemas que o Chrome implementa.

### Proxy HTTP vs SOCKS5

| Necessidade | Proxy HTTP | SOCKS5 |
|-------------|------------|--------|
| Filtragem de conteúdo | Sim | Não |
| Bloqueio baseado em URL | Sim | Não (apenas IP:porta) |
| Caching | Sim | Não |
| Suporte UDP | Não | Sim |
| Flexibilidade de protocolo | Apenas HTTP (CONNECT para tunelamento TCP) | Qualquer TCP/UDP |
| Privacidade | Baixa (analisa HTTP, adiciona cabeçalhos reveladores) | Média (não analisa ou modifica tráfego, mas conteúdo não criptografado ainda é visível ao operador) |
| Resolução DNS | Proxy resolve (remoto) | Depende (SOCKS5: tipicamente cliente resolve, SOCKS5h: proxy resolve. Chrome sempre resolve remotamente para SOCKS5.) |

Para ambientes corporativos que precisam de controle de conteúdo e caching, proxies HTTP são a escolha certa. Para automação focada em privacidade, SOCKS5 oferece melhor stealth e flexibilidade de protocolo. Para segurança máxima, use SOCKS5 sobre um túnel SSH ou VPN.

**Próximos passos:**

- [Proxies SOCKS](./socks-proxies.md): Proxy agnóstico a protocolo na camada de sessão
- [Fundamentos de Rede](./network-fundamentals.md): TCP/IP, UDP, WebRTC
- [Detecção de Proxy](./proxy-detection.md): Como proxies são detectados e como evitar
- [Configuração de Proxy](../../features/configuration/proxy.md): Configuração prática de proxy no Pydoll
- [Network Fingerprinting](../fingerprinting/network-fingerprinting.md): Fingerprinting TCP/IP e TLS

## Referências

- RFC 9110: HTTP Semantics (2022, substitui RFC 7230-7237) - https://www.rfc-editor.org/rfc/rfc9110.html
- RFC 9112: HTTP/1.1 (2022) - https://www.rfc-editor.org/rfc/rfc9112.html
- RFC 9113: HTTP/2 (2022, substitui RFC 7540) - https://www.rfc-editor.org/rfc/rfc9113.html
- RFC 9114: HTTP/3 (2022) - https://www.rfc-editor.org/rfc/rfc9114.html
- RFC 9000: QUIC Transport Protocol (2021) - https://www.rfc-editor.org/rfc/rfc9000.html
- RFC 9298: Proxying UDP in HTTP (CONNECT-UDP, 2022) - https://www.rfc-editor.org/rfc/rfc9298.html
- RFC 8441: Bootstrapping WebSockets with HTTP/2 (2018) - https://www.rfc-editor.org/rfc/rfc8441.html
- RFC 7617: Basic Authentication (2015) - https://www.rfc-editor.org/rfc/rfc7617.html
- RFC 7616: Digest Authentication (2015) - https://www.rfc-editor.org/rfc/rfc7616.html
- RFC 7239: Forwarded HTTP Extension (2014) - https://www.rfc-editor.org/rfc/rfc7239.html
- RFC 4559: Negotiate Authentication (2006) - https://www.rfc-editor.org/rfc/rfc4559.html
- MDN Web Docs: Proxy servers and tunneling - https://developer.mozilla.org/en-US/docs/Web/HTTP/Proxy_servers_and_tunneling
- Chrome DevTools Protocol: Fetch domain - https://chromedevtools.github.io/devtools-protocol/tot/Fetch/
