# Fundamentos de Rede

Este documento cobre os protocolos de rede fundamentais que alimentam a internet e como eles podem expor ou proteger sua identidade em cenários de automação. Uma compreensão funcional de TCP, UDP, do modelo OSI e do WebRTC tornará a configuração de proxy muito menos misteriosa e muito mais eficaz.

!!! info "Navegação do Módulo"
    - [Visão Geral de Rede e Segurança](./index.md): Introdução ao módulo e trilha de aprendizado
    - [Proxies HTTP/HTTPS](./http-proxies.md): Proxy de camada de aplicação
    - [Proxies SOCKS](./socks-proxies.md): Proxy de camada de sessão

    Para uso prático do Pydoll, veja [Configuração de Proxy](../../features/configuration/proxy.md) e [Opções do Navegador](../../features/configuration/browser-options.md).

## A Pilha de Rede

Cada requisição HTTP que seu navegador faz viaja através de uma pilha de rede em camadas. Cada camada tem responsabilidades, protocolos e implicações de segurança específicas. Proxies operam em camadas diferentes, e a camada determina o que o proxy pode ver, modificar e ocultar. Características de rede em camadas inferiores podem aplicar fingerprinting no seu sistema real mesmo através de proxies, então entender a pilha ajuda você a ver onde ocorrem vazamentos de identidade e como preveni-los.

### O Modelo OSI

O modelo OSI (Open Systems Interconnection), desenvolvido pela ISO em 1984, fornece um framework conceitual para entender como os protocolos de rede interagem. As redes do mundo real usam o modelo TCP/IP (que antecede o OSI e tem apenas 4 camadas), mas a terminologia OSI permanece como a forma padrão de descrever onde os proxies operam e o que eles podem acessar.

```mermaid
graph TD
    L7[Layer 7: Application - HTTP, FTP, SMTP, DNS]
    L6[Layer 6: Presentation - Encryption, Compression]
    L5[Layer 5: Session - SOCKS]
    L4[Layer 4: Transport - TCP, UDP]
    L3[Layer 3: Network - IP, ICMP]
    L2[Layer 2: Data Link - Ethernet, WiFi]
    L1[Layer 1: Physical - Cables, Radio Waves]

    L7 --> L6 --> L5 --> L4 --> L3 --> L2 --> L1
```

A Camada 7 (Aplicação) é onde vivem os protocolos voltados ao usuário: HTTP, HTTPS, FTP, SMTP e DNS operam aqui. Esta camada contém os dados reais com os quais sua aplicação se importa, como documentos HTML, respostas JSON e transferências de arquivos. Proxies HTTP operam nesta camada, o que lhes dá visibilidade total sobre o conteúdo de requisição e resposta.

A Camada 6 (Apresentação) lida com tradução de formato de dados, criptografia e compressão. SSL/TLS é comumente associado a esta camada pelo seu papel de criptografia, embora na prática o TLS abranja as Camadas 4 a 6 e não se mapeie de forma limpa a nenhuma camada OSI específica. O que importa para automação é que a criptografia HTTPS acontece aqui, criptografando os dados da Camada 7 antes de descerem pela pilha.

A Camada 5 (Sessão) gerencia conexões entre aplicações. Proxies SOCKS operam aqui, abaixo da camada de aplicação mas acima da de transporte. Esta posição torna o SOCKS agnóstico a protocolo: ele pode proxyar qualquer protocolo da Camada 7 (HTTP, FTP, SMTP, SSH) sem precisar entender suas especificidades.

A Camada 4 (Transporte) fornece entrega de dados de ponta a ponta. TCP (orientado à conexão, confiável) e UDP (sem conexão, rápido) são os protocolos dominantes aqui. Esta camada lida com números de porta, controle de fluxo e correção de erros. Todos os proxies dependem, em última análise, da Camada 4 para a transmissão real de dados.

A Camada 3 (Rede) lida com roteamento e endereçamento entre redes. O IP (Internet Protocol) opera aqui, gerenciando endereços IP e decisões de roteamento. É aqui que seu endereço IP real reside, e onde os proxies tentam substituí-lo.

A Camada 2 (Enlace de Dados) gerencia a comunicação no mesmo segmento de rede físico. Ethernet, Wi-Fi e PPP operam aqui, lidando com endereços MAC e transmissão de frames. Endereços MAC são visíveis apenas no segmento de rede local e não são diretamente acessíveis por servidores remotos, embora possam ser expostos através de protocolos como IPv6 SLAAC (que incorpora o MAC no endereço).

A Camada 1 (Física) é o hardware real: cabos, ondas de rádio e níveis de voltagem. Raramente relevante para automação de software.

!!! tip "OSI vs TCP/IP"
    O modelo TCP/IP (4 camadas: Enlace, Internet, Transporte, Aplicação) é o que as redes realmente usam. O OSI (7 camadas) é uma ferramenta de ensino e modelo de referência. Quando as pessoas dizem "proxy de Camada 7", elas estão usando a terminologia OSI, mas a implementação real roda sobre TCP/IP.

### Como o Posicionamento da Camada Afeta os Proxies

A camada onde um proxy opera determina o que ele pode e o que não pode fazer.

Proxies HTTP/HTTPS operam na Camada 7 (Aplicação). Como eles entendem HTTP, podem ler e modificar URLs, cabeçalhos, cookies e corpos de requisição. Podem fazer cache de respostas de forma inteligente com base na semântica HTTP, filtrar conteúdo por URL ou palavra-chave e injetar cabeçalhos de autenticação. A contrapartida é que eles só entendem HTTP. Não podem proxyar FTP, SMTP, SSH ou outros protocolos, e inspecionar conteúdo HTTPS requer terminação TLS, o que significa descriptografar e recriptografar o tráfego.

Proxies SOCKS operam na Camada 5 (Sessão). Como ficam abaixo da camada de aplicação, são agnósticos a protocolo e podem proxyar qualquer protocolo da Camada 7 sem modificação. O tráfego HTTPS passa criptografado de ponta a ponta, já que o proxy SOCKS nunca precisa descriptografá-lo. O SOCKS5 também suporta UDP, permitindo proxyar consultas DNS, VoIP e outros protocolos baseados em UDP. A contrapartida é que proxies SOCKS não têm visibilidade dos dados da camada de aplicação: não podem fazer cache, filtrar por URL ou inspecionar conteúdo. Podem apenas filtrar por IP e porta.

!!! note "A Contrapartida Fundamental"
    Camadas mais altas (Camada 7) oferecem mais controle mas menos flexibilidade. Camadas mais baixas (Camada 5) oferecem menos controle mas mais flexibilidade. Escolha proxies HTTP quando precisar de controle de conteúdo, e proxies SOCKS quando precisar de flexibilidade de protocolo ou criptografia de ponta a ponta.

### O Problema de Vazamento de Camada

Mesmo com um proxy de Camada 7 perfeito, características de camadas inferiores podem expor sua identidade real. A pilha TCP do seu sistema operacional na Camada 4 tem um fingerprint único definido pelo tamanho da janela, ordem das opções e valores de TTL. Campos do cabeçalho IP na Camada 3, como TTL e comportamento de fragmentação, revelam seu SO e topologia de rede.

Por exemplo, se você configurar um proxy para apresentar um User-Agent de "Windows 10", mas o fingerprint TCP real do seu sistema Linux contradizer isso na Camada 4, sistemas de detecção sofisticados podem marcar essa inconsistência como um forte indicador de bot. É por isso que o fingerprinting em nível de rede (abordado em [Network Fingerprinting](../fingerprinting/network-fingerprinting.md)) é tão perigoso: ele opera abaixo da camada do proxy, expondo seu sistema real mesmo quando o proxy da camada de aplicação é impecável.

## TCP vs UDP

Na Camada 4 (Transporte), dois protocolos fundamentalmente diferentes dominam a comunicação na internet. Eles representam filosofias de design opostas: confiabilidade versus velocidade.

O TCP é orientado à conexão. Pense nele como uma ligação telefônica: você estabelece uma conexão, verifica se a outra parte está ouvindo, troca dados de forma confiável e, em seguida, desliga. Cada byte é confirmado, ordenado e tem entrega garantida. O UDP é sem conexão. Você envia seus dados e espera que cheguem. Sem handshake, sem confirmações, sem garantias. Apenas velocidade bruta com sobrecarga mínima.

| Característica | TCP | UDP |
|---------|-----|-----|
| Conexão | Orientado à conexão (handshake necessário) | Sem conexão (sem handshake) |
| Confiabilidade | Entrega garantida, pacotes ordenados | Entrega de melhor esforço, pacotes podem ser perdidos |
| Velocidade | Mais lento (sobrecarga dos mecanismos de confiabilidade) | Mais rápido (sobrecarga mínima) |
| Casos de Uso | Navegação web, transferência de arquivos, email | Streaming de vídeo, consultas DNS, jogos |
| Tamanho do Cabeçalho | 20 bytes mínimo (até 60 com opções) | 8 bytes fixo |
| Controle de Fluxo | Sim (janela deslizante, orientado pelo receptor) | Não (transmissor envia à vontade) |
| Controle de Congestionamento | Sim (desacelera quando a rede está congestionada) | Não (responsabilidade da aplicação) |
| Verificação de Erros | Extensiva (checksum + acknowledgments) | Básica (apenas checksum; opcional no IPv4, obrigatório no IPv6) |
| Ordenação | Pacotes reordenados se recebidos fora de sequência | Sem ordenação, pacotes entregues como recebidos |
| Retransmissão | Automática (pacotes perdidos são retransmitidos) | Nenhuma (aplicação deve tratar) |

### TCP e Proxies

Todos os protocolos de proxy (HTTP, HTTPS, SOCKS4, SOCKS5) usam TCP para seu canal de controle. Isso ocorre porque a autenticação de proxy e a troca de comandos exigem entrega garantida, protocolos de proxy têm sequências de comando estritas (handshake, depois auth, depois dados), e proxies precisam de conexões persistentes para rastrear o estado do cliente.

No entanto, o SOCKS5 também pode proxyar tráfego UDP, diferente do SOCKS4 ou de proxies HTTP. Isso torna o SOCKS5 essencial para proxyar consultas DNS, áudio/vídeo WebRTC, VoIP e protocolos de jogos.

!!! danger "UDP e Vazamento de IP"
    A maioria das conexões de navegador usa TCP (HTTP, WebSocket, etc.), mas o WebRTC usa UDP diretamente, contornando a configuração de proxy do navegador. Esta é a causa mais comum de vazamento de IP em automação de navegador com proxy: seu tráfego TCP passa pelo proxy enquanto seu tráfego UDP vaza seu IP real.

### O Handshake de Três Vias do TCP

Antes que quaisquer dados possam ser transmitidos, o TCP requer um handshake de três vias para estabelecer uma conexão. Esta negociação sincroniza números de sequência, acorda tamanhos de janela e estabelece o estado da conexão em ambas as pontas.

```mermaid
sequenceDiagram
    participant Client
    participant Server

    Client->>Server: SYN (Synchronize, seq=x)
    Note over Client,Server: Client requests connection

    Server->>Client: SYN-ACK (seq=y, ack=x+1)
    Note over Client,Server: Server acknowledges and sends its own SYN

    Client->>Server: ACK (ack=y+1)
    Note over Client,Server: Connection established, data transfer begins
```

O processo começa quando o cliente envia um pacote SYN (Synchronize) contendo um Número de Sequência Inicial (ISN) aleatório, por exemplo `seq=1000`. Junto com o ISN, opções TCP são negociadas: tamanho da janela, Tamanho Máximo de Segmento (MSS), timestamps e suporte a SACK.

O servidor responde com um SYN-ACK: ele escolhe seu próprio ISN aleatório (ex: `seq=5000`) e confirma o ISN do cliente definindo `ack=1001` (ISN do cliente + 1). Este único pacote tanto estabelece a direção servidor-para-cliente (SYN) quanto confirma a direção cliente-para-servidor (ACK). O servidor também retorna suas próprias opções TCP.

O cliente então envia um ACK final, confirmando o ISN do servidor (`ack=5001`). Neste ponto, a conexão está totalmente estabelecida em ambas as direções e a transmissão de dados pode começar.

O ISN é aleatorizado em vez de começar do zero para prevenir ataques de sequestro de TCP. Se ISNs fossem previsíveis, um atacante poderia injetar pacotes em uma conexão existente adivinhando os números de sequência. Sistemas modernos usam aleatoriedade criptográfica para seleção de ISN (RFC 6528).

### Fingerprinting TCP

O handshake TCP revela características que aplicam fingerprinting no seu sistema operacional. Diferentes SOs usam valores padrão diferentes para o tamanho inicial da janela, ordem das opções TCP, TTL (Time To Live), fator de escala da janela e comportamento de timestamp. Esses valores são definidos pelo kernel, não pelo navegador, então um proxy não pode alterá-los.

Aqui estão exemplos ilustrativos para sistemas operacionais modernos. Note que os valores reais variam entre versões de SO, configurações de kernel e ajustes de rede:

```
Windows 10/11 (modern builds):
    Window Size: 65535
    MSS: 1460
    Options: MSS, NOP, WS, NOP, NOP, SACK_PERM
    TTL: 128

Linux (kernel 5.x+, Ubuntu 20.04+):
    Window Size: 29200
    MSS: 1460
    Options: MSS, SACK_PERM, TS, NOP, WS
    TTL: 64

macOS (Monterey+):
    Window Size: 65535
    TTL: 64
```

Essas diferenças estão gravadas no kernel. Um proxy não pode alterá-las porque são definidas pelo seu sistema operacional, não pelo seu navegador. É assim que sistemas de detecção sofisticados podem identificá-lo mesmo através de proxies.

!!! warning "Limitação do Proxy"
    Proxies HTTP e SOCKS operam acima da camada TCP. Eles não podem modificar características do handshake TCP. O fingerprint TCP do seu SO está sempre exposto ao servidor proxy e a quaisquer observadores de rede entre você e o proxy. Apenas soluções em nível de VPN ou configuração da pilha TCP em nível de SO podem resolver isso.

!!! note "Além do Fingerprinting TCP"
    O handshake TCP é apenas a primeira oportunidade de fingerprinting. Imediatamente após, o handshake TLS revela outro fingerprint único conhecido como JA3/JA4. Veja [Network Fingerprinting](../fingerprinting/network-fingerprinting.md) para detalhes sobre fingerprinting de TLS e HTTP/2.

### UDP

Diferente da abordagem confiável e orientada à conexão do TCP, o UDP é um protocolo de "dispare-e-esqueça". Ele troca confiabilidade por latência e sobrecarga mínimas, tornando-o ideal para aplicações em tempo real onde a velocidade importa mais que a entrega perfeita.

Um datagrama UDP tem apenas um cabeçalho de 8 bytes (comparado com 20-60 bytes do TCP), contendo porta de origem, porta de destino, comprimento e um checksum. Não há estabelecimento de conexão, nenhuma garantia de confiabilidade, nenhum controle de fluxo e nenhum controle de congestionamento. Se um pacote for perdido, a aplicação deve decidir se e como tratar isso.

O UDP é a escolha certa para comunicação em tempo real (chamadas de voz/vídeo via WebRTC e VoIP), jogos (atualizações de estado de baixa latência), streaming (onde perda ocasional de frames é aceitável) e consultas DNS (pares pequenos de requisição/resposta onde a aplicação cuida das retentativas). É uma escolha ruim para transferências de arquivos, navegação web, email ou bancos de dados, todos os quais precisam de entrega confiável e ordenada.

O DNS é um exemplo particularmente importante no contexto de automação. O DNS usa UDP porque as consultas são tipicamente pequenas e se beneficiam da ausência de sobrecarga de handshake do UDP. Embora o EDNS0 (RFC 6891) tenha aumentado o payload máximo de DNS sobre UDP além do limite original de 512 bytes, a maioria das consultas permanece compacta. O cliente DNS cuida das retentativas em nível de aplicação se uma resposta não chegar dentro do timeout.

Para automação de navegador, a preocupação principal com o UDP é que o WebRTC o utiliza para áudio e vídeo em tempo real, consultas DNS o utilizam para resolução de domínio, e a maioria dos proxies (HTTP, HTTPS, SOCKS4) só lida com TCP. A menos que você configure explicitamente o proxy de UDP, esse tráfego contorna seu proxy e vaza seu IP real.

| Tipo de Proxy | Suporte UDP | Notas |
|------------|-------------|-------|
| Proxy HTTP | Não | Proxyia apenas HTTP/HTTPS baseado em TCP |
| Proxy HTTPS (CONNECT) | Não | O método CONNECT só estabelece túneis TCP |
| SOCKS4 | Não | Protocolo apenas TCP |
| SOCKS5 | Sim | Suporta relay UDP via comando `UDP ASSOCIATE` |
| VPN | Sim | Tunela todo o tráfego IP (TCP e UDP) |

Para anonimato verdadeiro em automação de navegador, você precisa de: um proxy SOCKS5 com suporte UDP e WebRTC configurado para usá-lo, WebRTC desabilitado inteiramente (o que quebra videoconferência), uma VPN que tunele todo o tráfego, ou a flag do navegador `--force-webrtc-ip-handling-policy=disable_non_proxied_udp`.

### QUIC e HTTP/3

Navegadores modernos utilizam cada vez mais o QUIC (RFC 9000), um protocolo de transporte baseado em UDP que alimenta o HTTP/3. Como o QUIC roda sobre UDP, ele compartilha os mesmos problemas de bypass de proxy que o WebRTC e o DNS: a maioria dos proxies HTTP não consegue lidar com tráfego QUIC, e ele pode vazar para fora da sua configuração de proxy.

Em cenários de automação, considere desabilitar o QUIC com a flag `--disable-quic` do Chrome para forçar HTTP/2 sobre TCP, garantindo que todo o tráfego web passe pelo seu proxy. O QUIC também tem suas próprias características de fingerprinting, similares ao JA3 para TLS, o que adiciona mais um vetor de detecção.

## WebRTC e Vazamento de IP

WebRTC (Web Real-Time Communication) é uma API de navegador padronizada pelo W3C que permite comunicação ponto-a-ponto de áudio, vídeo e dados diretamente entre navegadores, sem plugins ou servidores intermediários. Embora poderosa para aplicações em tempo real, o WebRTC é a maior fonte isolada de vazamento de IP em automação de navegador com proxy.

### Como o WebRTC Vaza Seu IP

O WebRTC foi projetado para conexões ponto-a-ponto diretas, otimizando para baixa latência em detrimento da privacidade. Para estabelecer conexões P2P, o WebRTC deve descobrir seu endereço IP público real e compartilhá-lo com o par remoto, mesmo se seu navegador estiver configurado para usar um proxy.

O problema se desenrola assim: seu navegador usa um proxy para tráfego HTTP/HTTPS (que é TCP), mas o WebRTC usa servidores STUN para descobrir seu IP público real sobre UDP. Consultas STUN contornam o proxy porque a maioria dos proxies só lida com TCP. Seu IP real é descoberto e compartilhado com pares remotos como parte da negociação de conexão. JavaScript na página pode ler esses "candidatos ICE" e enviar seu IP real para o servidor do site.

!!! danger "Gravidade dos Vazamentos WebRTC"
    Mesmo com um proxy HTTP configurado corretamente, proxy HTTPS funcionando, consultas DNS proxyadas, User-Agent falsificado e fingerprinting de canvas mitigado, o WebRTC ainda pode vazar seu IP real em milissegundos. Isso porque o WebRTC opera abaixo da camada de proxy do navegador, interagindo diretamente com a pilha de rede do SO.

### O Processo ICE

O WebRTC usa ICE (Interactive Connectivity Establishment, RFC 8445) para descobrir caminhos de conexão possíveis e selecionar o melhor. Este processo inerentemente revela sua topologia de rede ao coletar três tipos de candidatos.

```mermaid
sequenceDiagram
    participant Browser
    participant STUN as STUN Server
    participant TURN as TURN Relay
    participant Peer as Remote Peer

    Note over Browser: WebRTC connection initiated

    Browser->>Browser: Gather local IP addresses<br/>(LAN interfaces)
    Note over Browser: Local candidate:<br/>192.168.1.100:54321

    Browser->>STUN: STUN Binding Request (over UDP)
    Note over STUN: STUN server discovers public IP<br/>(bypasses proxy!)
    STUN->>Browser: STUN Response with real public IP
    Note over Browser: Server reflexive candidate:<br/>203.0.113.45:54321

    Browser->>TURN: Allocate relay (if needed)
    TURN->>Browser: Relay address assigned
    Note over Browser: Relay candidate:<br/>198.51.100.10:61234

    Browser->>Peer: Send all ICE candidates<br/>(local + public + relay)
    Note over Peer: Now knows your:<br/>- LAN IP<br/>- Real public IP<br/>- Relay address

    Peer->>Browser: Send ICE candidates

    Note over Browser,Peer: ICE negotiation: try direct P2P first

    alt Direct P2P succeeds
        Browser<<->>Peer: Direct connection (bypasses proxy entirely!)
    else Direct P2P fails (firewall/NAT)
        Browser->>TURN: Use TURN relay
        TURN<<->>Peer: Relayed connection
        Note over Browser,Peer: Higher latency, but works
    end
```

### Tipos de Candidatos ICE

O ICE descobre três tipos de candidatos (possíveis endpoints de conexão), cada um revelando diferentes informações sobre sua rede.

**Candidatos host** são seus endereços IP locais da LAN. O navegador enumera todas as interfaces de rede locais e cria candidatos para cada uma. Isso revela seus endereços IP locais em redes privadas, sua topologia de rede (presença de interfaces VPN, pontes de VM) e o número de interfaces de rede.

```javascript
// Example host candidates
candidate:1 1 UDP 2130706431 192.168.1.100 54321 typ host
candidate:2 1 UDP 2130706431 10.0.0.5 54322 typ host
```

Navegadores modernos (Chrome 75+, Firefox 78+, Safari) mitigam vazamentos de candidatos host substituindo endereços IP locais por nomes mDNS efêmeros (ex: `a1b2c3d4.local`) quando permissões de mídia (câmera/microfone) não foram concedidas. No entanto, candidatos reflexivos de servidor (seu IP público) permanecem expostos independentemente do mDNS.

**Candidatos reflexivos de servidor** são seu IP público como visto por um servidor STUN. O navegador envia uma requisição STUN para um servidor público, que responde com seu endereço IP público. Este é o vazamento do qual todos falam: seu proxy mostra um IP, mas o WebRTC revela o seu real, junto com seu tipo de NAT, mapeamento de porta externa e informações do ISP.

```javascript
// Server reflexive candidate (your real public IP)
candidate:4 1 UDP 1694498815 203.0.113.45 54321 typ srflx raddr 192.168.1.100 rport 54321
```

**Candidatos de retransmissão** são endereços de servidores TURN usados como fallback quando o P2P direto falha. O candidato de retransmissão ainda pode conter seu IP real no campo `raddr` (endereço remoto), dependendo da implementação do servidor TURN.

```javascript
// Relay candidate (TURN server address)
candidate:5 1 UDP 16777215 198.51.100.10 61234 typ relay raddr 203.0.113.45 rport 54321
```

### O Protocolo STUN

STUN (Session Traversal Utilities for NAT, RFC 8489) é um protocolo simples de requisição-resposta sobre UDP. Sua função é direta: o cliente pergunta "qual IP você vê de mim?" e o servidor responde com o IP público e a porta do cliente.

O cliente envia uma Binding Request contendo um magic cookie (`0x2112A442`, um valor fixo definido pela RFC) e um transaction ID aleatório de 12 bytes. O servidor responde com uma Binding Success Response que inclui um atributo `XOR-MAPPED-ADDRESS` contendo o IP público e a porta do cliente como vistos da perspectiva do servidor.

O endereço IP na resposta é XOR'ado com o magic cookie e o transaction ID. Isso não é por segurança, mas por compatibilidade com NAT: alguns dispositivos NAT modificam incorretamente endereços IP em payloads de pacotes, e o XOR ofusca o endereço para prevenir essa interferência.

Servidores STUN públicos comumente usados por navegadores incluem `stun.l.google.com:19302` (Google), `stun1.l.google.com:19302` (Google), `stun.services.mozilla.com` (Mozilla) e `stun.stunprotocol.org:3478`.

### Por que Proxies Não Conseguem Parar Vazamentos WebRTC

Vazamentos WebRTC acontecem por vários motivos que se reforçam. Primeiro, o WebRTC usa UDP, e a maioria dos proxies (HTTP, HTTPS CONNECT, SOCKS4) só lida com TCP. Apenas o SOCKS5 suporta UDP, e mesmo assim o navegador precisa ser explicitamente configurado para rotear o WebRTC através dele.

Segundo, o WebRTC é uma API de navegador que opera abaixo da camada HTTP. Ele acessa diretamente a pilha de rede do SO, contornando configurações de proxy definidas para HTTP/HTTPS. Consultas STUN vão diretamente para a interface de rede, e a tabela de roteamento do SO determina seu caminho, não a configuração de proxy do navegador. Apenas roteamento em nível de VPN pode interceptá-las.

Terceiro, o WebRTC enumera todas as interfaces de rede (ethernet física, Wi-Fi, adaptadores VPN, pontes de VM), incluindo interfaces não usadas para navegação regular. Isso vaza sua topologia de rede interna.

Finalmente, páginas web podem ler candidatos ICE via JavaScript usando o evento `RTCPeerConnection.onicecandidate`, extrair endereços IP das strings de candidatos com um regex simples e enviar seu IP real para o servidor de rastreamento deles.

### Prevenindo Vazamentos WebRTC no Pydoll

O Pydoll fornece múltiplas estratégias para prevenir vazamentos de IP via WebRTC.

**Método 1: Forçar o WebRTC a usar apenas rotas proxyadas (recomendado)**

```python
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
options.webrtc_leak_protection = True  # Adds --force-webrtc-ip-handling-policy=disable_non_proxied_udp
```

O Pydoll fornece uma propriedade conveniente `webrtc_leak_protection` que gerencia a flag do Chrome subjacente para você. Isso desabilita UDP se nenhum proxy o suportar, força o WebRTC a usar apenas retransmissores TURN (sem P2P direto) e previne consultas STUN para servidores públicos. A contrapartida é maior latência para chamadas de vídeo, já que conexões P2P diretas são desabilitadas.

**Método 2: Desabilitar o WebRTC inteiramente**

```python
options.add_argument('--disable-features=WebRTC')
```

Isso desabilita completamente a API WebRTC, eliminando qualquer possibilidade de vazamento de IP por este vetor. A contrapartida é que todos os sites dependentes de WebRTC (videoconferência, chamadas de voz) deixarão de funcionar. Note que esta flag deve ser testada com sua versão específica do Chrome, pois nomes de feature flags podem variar entre versões.

**Método 3: Restringir o WebRTC via preferências do navegador**

```python
options.browser_preferences = {
    'webrtc': {
        'ip_handling_policy': 'disable_non_proxied_udp',
        'multiple_routes_enabled': False,
        'nonproxied_udp_enabled': False,
        'allow_legacy_tls_protocols': False
    }
}
```

Isso alcança o mesmo efeito do Método 1, mas através de preferências em vez de flags de linha de comando. `multiple_routes_enabled` previne o uso de múltiplos caminhos de rede, e `nonproxied_udp_enabled` bloqueia UDP que não passa pelo proxy.

**Método 4: Usar um proxy SOCKS5 com suporte UDP**

```python
options.add_argument('--proxy-server=socks5://proxy.example.com:1080')
options.add_argument('--force-webrtc-ip-handling-policy=default_public_interface_only')
```

O SOCKS5 pode proxyar UDP via seu comando `UDP ASSOCIATE`, permitindo que as consultas STUN do WebRTC passem pelo proxy. Isso requer um proxy SOCKS5 que realmente suporte relay UDP, o que nem todos suportam.

!!! warning "Autenticação SOCKS5"
    O Chrome não suporta autenticação SOCKS5 inline (ex: `socks5://user:pass@host:port`) via a flag `--proxy-server`. O Pydoll fornece um `SOCKS5Forwarder` integrado que contorna essa limitação executando um proxy SOCKS5 local sem autenticação que encaminha o tráfego para o proxy remoto autenticado, cuidando do handshake de usuário/senha em nome do Chrome. Veja [Configuração de Proxy](../../features/configuration/proxy.md) para detalhes de uso.

### Testando Vazamentos WebRTC

Você pode testar manualmente visitando [browserleaks.com/webrtc](https://browserleaks.com/webrtc) e verificando se seu IP real aparece na seção "Public IP Address". Se você vir seu IP real em vez do IP do proxy, está havendo vazamento.

Para testes automatizados com o Pydoll:

```python
import asyncio
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions

async def test_webrtc_leak():
    options = ChromiumOptions()
    options.add_argument('--proxy-server=http://proxy.example.com:8080')
    options.add_argument('--force-webrtc-ip-handling-policy=disable_non_proxied_udp')

    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://browserleaks.com/webrtc')

        await asyncio.sleep(3)

        ips = await tab.execute_script('''
            return Array.from(document.querySelectorAll('.ip-address'))
                .map(el => el.textContent.trim());
        ''')

        print("Detected IPs:", ips)
        # Should only show proxy IP, not your real IP

asyncio.run(test_webrtc_leak())
```

!!! danger "Sempre Teste Vazamentos WebRTC"
    Nunca assuma que sua configuração de proxy previne vazamentos WebRTC. Sempre verifique com [browserleaks.com/webrtc](https://browserleaks.com/webrtc) ou [ipleak.net](https://ipleak.net). Mesmo um único vazamento WebRTC compromete instantaneamente toda a sua configuração de proxy, já que o site agora conhece sua localização real, ISP e topologia de rede.

### Como Sites Exploram Vazamentos WebRTC

Sites podem intencionalmente acionar o WebRTC para extrair seu IP real usando poucas linhas de JavaScript:

```javascript
const pc = new RTCPeerConnection({
    iceServers: [{urls: 'stun:stun.l.google.com:19302'}]
});

pc.createDataChannel('');
pc.createOffer().then(offer => pc.setLocalDescription(offer));

pc.onicecandidate = (event) => {
    if (event.candidate) {
        const ipRegex = /([0-9]{1,3}(\.[0-9]{1,3}){3})/;
        const ipMatch = event.candidate.candidate.match(ipRegex);

        if (ipMatch) {
            const realIP = ipMatch[1];
            fetch(`/track?real_ip=${realIP}&proxy_ip=${window.clientIP}`);
        }
    }
};
```

Este código cria um RTCPeerConnection, aciona a coleta de candidatos ICE (que contata servidores STUN), extrai endereços IP dos candidatos com um regex e envia seu IP real para um servidor de rastreamento. Desabilitar o WebRTC ou forçar rotas apenas proxyadas como descrito acima previne isso.

## Resumo

Proxies operam em camadas específicas da pilha de rede: HTTP na Camada 7, SOCKS na Camada 5. A camada determina o que o proxy pode ver, modificar e ocultar. Fingerprints TCP (tamanho da janela, opções, TTL) vazam de camadas inferiores e revelam seu SO real mesmo através de um proxy. Tráfego UDP, incluindo WebRTC e DNS, frequentemente contorna proxies a menos que explicitamente configurado. O WebRTC é a fonte mais comum de vazamento de IP, e apenas SOCKS5 ou VPN podem proxyar tráfego UDP de forma eficaz. Navegadores modernos também usam QUIC (HTTP/3 sobre UDP), o que adiciona mais um vetor potencial de bypass.

**Próximos passos:**

- [Proxies HTTP/HTTPS](./http-proxies.md): Proxy de camada de aplicação
- [Proxies SOCKS](./socks-proxies.md): Proxy de camada de sessão, agnóstico a protocolo
- [Network Fingerprinting](../fingerprinting/network-fingerprinting.md): Técnicas de fingerprinting TCP/IP e TLS
- [Configuração de Proxy](../../features/configuration/proxy.md): Configuração prática de proxy no Pydoll

## Referências

- RFC 793: Transmission Control Protocol (TCP) - https://tools.ietf.org/html/rfc793
- RFC 768: User Datagram Protocol (UDP) - https://tools.ietf.org/html/rfc768
- RFC 8489: Session Traversal Utilities for NAT (STUN) - https://tools.ietf.org/html/rfc8489
- RFC 8445: Interactive Connectivity Establishment (ICE) - https://tools.ietf.org/html/rfc8445
- RFC 8656: Traversal Using Relays around NAT (TURN) - https://tools.ietf.org/html/rfc8656
- RFC 6528: Defending Against Sequence Number Attacks - https://tools.ietf.org/html/rfc6528
- RFC 9000: QUIC: A UDP-Based Multiplexed and Secure Transport - https://tools.ietf.org/html/rfc9000
- W3C WebRTC 1.0: Real-Time Communication Between Browsers - https://www.w3.org/TR/webrtc/
- BrowserLeaks: WebRTC Leak Test - https://browserleaks.com/webrtc
- IPLeak: Comprehensive Leak Testing - https://ipleak.net
