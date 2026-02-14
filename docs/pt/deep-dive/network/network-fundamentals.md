# Fundamentos de Rede

Este documento cobre os protocolos de rede fundamentais que alimentam a internet e como eles expõem ou protegem sua identidade em cenários de automação. Entender TCP, UDP, o modelo OSI e WebRTC é **essencial** antes de mergulhar nos protocolos de proxy.

!!! info "Navegação do Módulo"
    - **[← Visão Geral de Rede e Segurança](./index.md)** - Introdução ao módulo e trilha de aprendizado
    - **[→ Proxies HTTP/HTTPS](./http-proxies.md)** - Proxy de camada de aplicação
    - **[→ Proxies SOCKS](./socks-proxies.md)** - Proxy de camada de sessão
    
    Para uso prático do Pydoll, veja **[Configuração de Proxy](../../features/configuration/proxy.md)** e **[Opções do Navegador](../../features/configuration/browser-options.md)**.

!!! warning "Primeiro os Fundamentos"
    Este é um **conhecimento pré-requisito** para entender os protocolos de proxy. Sem compreender esses fundamentos, a configuração de proxy se torna uma tentativa e erro.

## Introdução: A Pilha de Rede

Cada requisição HTTP que seu navegador faz (cada conexão de proxy, cada mensagem WebSocket) viaja através de uma **pilha de rede em camadas**. Cada camada tem responsabilidades, protocolos e implicações de segurança específicos.

**Por que isso importa para automação:**

- Proxies operam em **camadas diferentes**, cada um com capacidades diferentes
- Características de rede em camadas inferiores podem **aplicar fingerprinting** (identificação) no seu sistema real (mesmo através de proxies)
- Entender a pilha revela **onde ocorrem vazamentos de identidade** e como preveni-los

Antes de mergulhar em proxies, precisamos entender a pilha de rede em que eles operam. Isso não é teoria abstrata. Cada conceito aqui tem **implicações diretas** para furtividade, desempenho e confiabilidade na automação de navegadores.

### O Contexto do Modelo OSI

O modelo OSI (Open Systems Interconnection), desenvolvido pela Organização Internacional para Padronização (ISO) em 1984, fornece um **framework conceitual** para entender como os protocolos de rede interagem. Embora as redes do mundo real usem primariamente o modelo TCP/IP (que antecede o OSI), entender as camadas OSI ajuda a conceituar **onde os proxies operam** e **o que eles podem inspecionar ou modificar**.

```mermaid
graph TD
    L7[Camada 7: Aplicacao - HTTP, FTP, SMTP]
    L6[Camada 6: Apresentacao - SSL/TLS, Criptografia]
    L5[Camada 5: Sessao - SOCKS]
    L4[Camada 4: Transporte - TCP, UDP]
    L3[Camada 3: Rede - IP, ICMP]
    L2[Camada 2: Enlace de Dados - Ethernet, WiFi]
    L1[Camada 1: Fisica - Cabos, Ondas de Radio]
    
    L7 --> L6 --> L5 --> L4 --> L3 --> L2 --> L1
```

#### Detalhamento Camada por Camada

**Camada 7 (Aplicação)**: Onde vivem os protocolos voltados ao usuário. HTTP, HTTPS, FTP, SMTP, DNS, todos operam aqui. Esta camada contém os **dados reais** com os quais sua aplicação se importa: documentos HTML, respostas JSON, transferências de arquivos. Proxies HTTP operam nesta camada, dando-lhes **visibilidade total** sobre o conteúdo da requisição/resposta.

**Camada 6 (Apresentação)**: Lida com tradução de formato de dados, criptografia e compressão. A criptografia SSL/TLS ocorre aqui (embora o TLS seja frequentemente considerado como abrangendo as Camadas 5-6). É aqui que a **criptografia HTTPS** acontece, criptografando dados da Camada 7 antes de passá-los para a Camada 5.

**Camada 5 (Sessão)**: Gerencia conexões entre aplicações. Proxies SOCKS operam aqui, abaixo da camada de aplicação, mas acima da de transporte. Esta posição torna o SOCKS **agnóstico a protocolo**, ele pode proxyar qualquer protocolo da Camada 7 (HTTP, FTP, SMTP, SSH) sem entender suas especificidades.

**Camada 4 (Transporte)**: Fornece entrega de dados de ponta a ponta. TCP (orientado à conexão, confiável) e UDP (sem conexão, rápido) são os protocolos dominantes. Esta camada lida com **números de porta**, **controle de fluxo** e **correção de erros**. Todos os proxies, em última análise, dependem da Camada 4 para a transmissão real de dados.

**Camada 3 (Rede)**: Lida com roteamento e endereçamento entre redes. O IP (Internet Protocol) opera aqui, gerenciando **endereços IP** e **decisões de roteamento**. É aqui que seu **endereço IP real** reside, e onde os proxies tentam substituí-lo.

**Camada 2 (Enlace de Dados)**: Gerencia a comunicação no mesmo segmento de rede físico. Ethernet, Wi-Fi e PPP operam aqui, lidando com **endereços MAC** e **transmissão de frames**. O fingerprinting de rede nesta camada pode revelar **características da rede física**.

**Camada 1 (Física)**: O hardware real (cabos, ondas de rádio, níveis de voltagem). Embora raramente relevante para software, características da camada física podem ser medidas (timing de sinal, propriedades elétricas) para **fingerprinting avançado**.

!!! tip "Modelos OSI vs TCP/IP"
    O **modelo TCP/IP** (4 camadas: Enlace, Internet, Transporte, Aplicação) é o que as redes realmente usam. O OSI (7 camadas) é uma **ferramenta de ensino** e modelo de referência. Quando as pessoas dizem "Proxy de Camada 7", elas estão usando a terminologia OSI, mas a implementação real usa TCP/IP.

#### Por que o Posicionamento da Camada Importa para Proxies

A camada onde um proxy opera determina suas **capacidades** e **limitações**:

**Proxies HTTP/HTTPS (Camada 7 - Aplicação):**

- **Visibilidade HTTP total**: Pode ler/modificar URLs, cabeçalhos, cookies, corpos de requisição
- **Cache inteligente**: Pode cachear respostas com base na semântica HTTP
- **Filtragem de conteúdo**: Pode bloquear URLs ou palavras-chave específicas
- **Integração de autenticação**: Pode adicionar cabeçalhos de autenticação
- **Limitação apenas HTTP**: Não pode proxyar FTP, SMTP, SSH ou outros protocolos
- **Terminação TLS necessária**: Deve descriptografar HTTPS para inspecionar conteúdo

**Proxies SOCKS (Camada 5 - Sessão):**

- **Agnóstico a protocolo**: Pode proxyar qualquer protocolo da Camada 7 (HTTP, FTP, SSH, etc.)
- **Sem terminação TLS**: HTTPS passa criptografado (segurança ponta-a-ponta)
- **Suporte UDP** (SOCKS5): Pode proxyar DNS, VoIP, protocolos de jogos
- **Sem visibilidade do conteúdo**: Não pode inspecionar ou modificar dados da camada de aplicação
- **Sem cache inteligente**: Não entende a semântica HTTP
- **Sem filtragem baseada em URL**: Não pode bloquear URLs específicas, apenas combinações IP:porta

!!! warning "O Trade-off Fundamental"
    **Camadas mais altas** (Camada 7) = Mais controle, menos flexibilidade
    **Camadas mais baixas** (Camada 5) = Menos controle, mais flexibilidade
    
    Escolha com base em suas necessidades: proxy HTTP para **controle de conteúdo**, proxy SOCKS para **flexibilidade de protocolo** e **criptografia ponta-a-ponta**.

#### Implicação Prática: O Problema de "Vazamento de Camada"

Entender as camadas revela um problema crítico de segurança: **características vazam entre as camadas**.

Mesmo com um proxy de Camada 7 perfeito (HTTP), características de camadas inferiores podem expor sua identidade real:

- **Camada 4 (TCP)**: A pilha TCP do seu SO tem um "fingerprint" único (tamanho da janela, opções, TTL)
- **Camada 3 (Rede)**: Campos do cabeçalho IP (TTL, fragmentação) revelam o SO e a topologia da rede
- **Camada 2 (Enlace de Dados)**: O fornecedor do endereço MAC revela o fabricante do hardware

**Exemplo**: Você configura um proxy para mostrar um User-Agent de "Windows 10", mas o **fingerprint TCP do seu sistema Linux real** (Camada 4) contradiz isso. Detecção instantânea de bot.

É por isso que o **fingerprinting em nível de rede** (abordado em [Network Fingerprinting](../fingerprinting/network-fingerprinting.md)) é tão perigoso: ele opera **abaixo da camada do proxy**, expondo seu sistema real mesmo quando o proxy em nível de aplicação é perfeito.

### TCP vs UDP: Protocolos da Camada de Transporte

Na Camada 4 (Transporte), dois protocolos fundamentalmente diferentes dominam a comunicação na internet: **TCP (Transmission Control Protocol)** e **UDP (User Datagram Protocol)**. Eles representam filosofias de design opostas: confiabilidade vs velocidade, sobrecarga vs eficiência.

#### A Diferença Fundamental

**TCP** é como uma ligação telefônica: você estabelece uma conexão, verifica se a outra parte está ouvindo, troca dados de forma confiável e, em seguida, desliga. Cada byte é acusado, ordenado e garantido que chegue.

**UDP** é como gritar em uma sala lotada: você envia sua mensagem e espera que ela chegue. Sem garantias, sem acusações de recebimento, sem configuração de conexão. Apenas velocidade bruta.

| Característica | TCP | UDP |
|---|---|---|
| **Conexão** | Orientado à conexão (requer handshake) | Sem conexão (sem handshake) |
| **Confiabilidade** | Entrega garantida, pacotes ordenados | Entrega de melhor esforço, pacotes podem ser perdidos |
| **Velocidade** | Mais lento (sobrecarga de mecanismos de confiabilidade) | Mais rápido (sobrecarga mínima) |
| **Casos de Uso** | Navegação web, transferência de arquivos, email | Streaming de vídeo, consultas DNS, jogos |
| **Tamanho do Cabeçalho** | 20 bytes mínimo (até 60 com opções) | 8 bytes fixo |
| **Controle de Fluxo** | Sim (janela deslizante, orientado pelo receptor) | Não (transmissor envia à vontade) |
| **Controle de Congestionamento** | Sim (desacelera quando a rede está congestionada) | Não (responsabilidade da aplicação) |
| **Verificação de Erros** | Extensiva (checksum + acknowledgments) | Básica (apenas checksum, descarte opcional) |
| **Ordenação** | Pacotes reordenados se recebidos fora de sequência | Sem ordenação, pacotes entregues como recebidos |
| **Retransmissão** | Automática (pacotes perdidos são retransmitidos) | Nenhuma (aplicação deve lidar) |

#### Por que Isso Importa para Proxies e Automação

**Todos os protocolos de proxy usam TCP**. Proxies HTTP, proxies HTTPS, SOCKS4 e SOCKS5, todos dependem do TCP para seu canal de controle porque:

1.  **Confiabilidade**: Autenticação de proxy e troca de comandos exigem entrega garantida
2.  **Ordenação**: Protocolos de proxy têm sequências de comando estritas (handshake → auth → dados)
3.  **Estado da conexão**: Proxies precisam de conexões persistentes para rastrear clientes

No entanto, **SOCKS5 pode proxyar tráfego UDP** (diferente de SOCKS4 ou proxies HTTP), tornando-o essencial para:

- **Consultas DNS**: Resolução rápida de domínio sem sobrecarga de TCP
- **WebRTC**: Áudio/vídeo em tempo real (que usa UDP para baixa latência)
- **VoIP**: Comunicação de voz requer velocidade acima de confiabilidade
- **Protocolos de jogos**: Atualizações de estado de jogo de baixa latência

!!! danger "UDP = Risco de Vazamento de IP"
    A maioria das conexões de navegador usa TCP (HTTP, WebSocket, etc.). Mas o WebRTC usa **UDP diretamente**, contornando a pilha de rede do navegador e a configuração de proxy. Esta é a **causa nº 1 de vazamento de IP** em automação de navegador com proxy. Seu IP real vaza através de UDP enquanto o tráfego TCP passa pelo proxy.

#### Handshake de Três Vias do TCP: Estabelecendo Conexões

Antes que quaisquer dados possam ser transmitidos, o TCP requer um **handshake de três vias** (three-way handshake) para estabelecer uma conexão. Esta negociação sincroniza números de sequência, acorda tamanhos de janela e estabelece o estado da conexão em ambas as pontas.

```mermaid
sequenceDiagram
    participant Client
    participant Server
    
    Client->>Server: SYN (Sincronizar, seq=x)
    Note over Client,Server: Cliente solicita conexao
    
    Server->>Client: SYN-ACK (seq=y, ack=x+1)
    Note over Client,Server: Servidor acusa recebimento e envia seu proprio SYN
    
    Client->>Server: ACK (ack=y+1)
    Note over Client,Server: Conexao estabelecida
    
    Note over Client,Server: Transferencia de dados comeca
```

**Detalhamento passo-a-passo:**

**1. SYN (Sincronizar)**: Cliente inicia a conexão

- Cliente seleciona um **Número de Sequência Inicial (ISN) aleatório** (ex: `seq=1000`)
- Envia pacote SYN com este ISN para o servidor
- Opções TCP negociadas: tamanho da janela, Tamanho Máximo de Segmento (MSS), timestamps, suporte a SACK

**2. SYN-ACK (Sincronizar-Acusar)**: Servidor responde

- Servidor seleciona seu próprio **ISN aleatório** (ex: `seq=5000`)
- Acusa o ISN do cliente: `ack=1001` (ISN do cliente + 1)
- Envia ambos SYN (para estabelecer direção servidor→cliente) e ACK (para confirmar direção cliente→servidor)
- Retorna suas próprias opções TCP

**3. ACK (Acusar)**: Cliente confirma

- Cliente acusa o ISN do servidor: `ack=5001` (ISN do servidor + 1)
- Conexão agora **estabelecida** em ambas as direções
- Transmissão de dados pode começar

!!! tip "Por que ISN Aleatório?"
    O ISN é aleatorizado (não começando do 0) para prevenir **ataques de sequestro de TCP**. Se ISNs fossem previsíveis, um atacante poderia injetar pacotes em uma conexão existente adivinhando os números de sequência. Sistemas modernos usam aleatoriedade criptográfica para seleção de ISN (RFC 6528).

**Implicação de Segurança: Fingerprinting TCP**

O handshake TCP revela numerosas características que aplicam **fingerprinting no seu sistema operacional**:

- **Tamanho Inicial da Janela**: SOs diferentes usam valores padrão diferentes (Windows: 8192, Linux: 5840, macOS: 65535)
- **Opções TCP**: Ordem e presença de opções variam por SO (MSS, SACK, Timestamps, Window Scale)
- **TTL (Time To Live)**: Valores padrão diferem (Windows: 128, Linux: 64, macOS: 64)
- **Fator de Escala da Janela**: Revela preferências de tamanho de buffer
- **Valor do Timestamp**: Padrões de tempo revelam tempo de atividade do sistema e resolução do relógio

**Exemplo de fingerprint de handshake TCP (capturado com Wireshark)**:

```
Windows 10:
    Tamanho da Janela: 8192
    MSS: 1460
    Opções: MSS, NOP, WS, NOP, NOP, SACK_PERM
    TTL: 128

Linux (Ubuntu):
    Tamanho da Janela: 29200
    MSS: 1460
    Opções: MSS, SACK_PERM, TS, NOP, WS
    TTL: 64
```

Essas diferenças estão **gravadas no kernel**. Um proxy não pode alterá-las porque elas são definidas pelo seu **sistema operacional**, não pelo seu navegador. É assim que sistemas de detecção sofisticados identificam você **mesmo através de proxies**.

!!! warning "Limitação do Proxy"
    Proxies HTTP e SOCKS operam **acima da camada TCP**. Eles não podem modificar características do handshake TCP. O fingerprint TCP do seu SO está **sempre exposto** ao servidor proxy (e a quaisquer observadores da rede). Apenas **soluções em nível de VPN** ou **spoofing da pilha TCP em nível de SO** podem resolver isso.

**Por que o TCP importa para proxies:**

- **Autenticação de proxy confiável**: Credenciais enviadas sobre TCP não serão perdidas
- **Conexões persistentes**: Conexão TCP única pode lidar com múltiplas requisições HTTP (HTTP/1.1 keep-alive, HTTP/2)
- **Entrega ordenada**: Comandos de proxy executam em sequência (crucial para fluxos de autenticação)
- **Exposição de fingerprinting**: Características do handshake TCP revelam seu SO real

#### Características do UDP: Velocidade Sem Garantias

Diferente da abordagem confiável e orientada à conexão do TCP, o UDP é um protocolo **"dispare-e-esqueça"**. Ele troca confiabilidade por **latência e sobrecarga mínimas**, tornando-o ideal para aplicações em tempo real onde a velocidade importa mais que a entrega perfeita.

**Estrutura do Pacote UDP (RFC 768)**:

```python
# Estrutura do datagrama UDP (formato real do cabeçalho)
{
    'source_port': 12345,        # 16 bits - opcional (0 = nenhuma resposta esperada)
    'destination_port': 53,       # 16 bits - obrigatório (identificador da aplicação)
    'length': 42,                 # 16 bits - tamanho do datagrama (cabeçalho + dados)
    'checksum': 0x1234,          # 16 bits - opcional no IPv4, obrigatório no IPv6
    'data': b'...'               # Variável - dados da aplicação
}
# Cabeçalho total: 8 bytes (vs 20-60 bytes do TCP)
```

**Características Chave do UDP:**

1.  **Sem Estabelecimento de Conexão**: Sem handshake, sem estado. Apenas envie o pacote e espere que chegue.
2.  **Sem Confiabilidade**: Pacotes podem ser perdidos, duplicados ou chegar fora de ordem. A aplicação deve lidar com esses cenários.
3.  **Sem Controle de Fluxo**: Transmissor envia tão rápido quanto quer. Nenhum mecanismo para desacelerar para a capacidade do receptor.
4.  **Sem Controle de Congestionamento**: UDP não detecta ou responde a congestionamento de rede. Pode sobrecarregar redes.
5.  **Cabeçalho Mínimo**: Apenas 8 bytes vs 20-60 bytes do TCP. Menor sobrecarga significa mais largura de banda para dados.
6.  **Multiplexação Baseada em Porta**: Como o TCP, usa números de porta para identificar aplicações (DNS=53, WebRTC=dinâmico)

**Quando Usar UDP:**

**Bons casos de uso:**
- **Comunicação em tempo real**: Chamadas de voz/vídeo (WebRTC, VoIP) onde dados antigos são inúteis
- **Jogos**: Atualizações de estado de jogo de baixa latência onde velocidade > precisão
- **Streaming**: Vídeo/áudio onde perda ocasional de frames é aceitável
- **Consultas DNS**: Pequena requisição/resposta onde a retransmissão é tratada pela aplicação
- **Descoberta de rede**: Protocolos de broadcast/multicast (DHCP, mDNS)

**Casos de uso ruins:**
- **Transferência de arquivos**: Exigiria confiabilidade em nível de aplicação (então apenas use TCP)
- **Navegação web**: Precisa de entrega ordenada e confiável (HTTP/3 sobre QUIC é exceção)
- **Email, bancos de dados**: Absolutamente exigem confiabilidade

**UDP e DNS: Um Exemplo Crítico**

O DNS (Domain Name System) usa UDP porque:

- **Mensagens pequenas**: Consultas e respostas DNS tipicamente cabem em um único pacote (<512 bytes)
- **Resolução rápida**: Sem sobrecarga de handshake significa buscas mais rápidas
- **Retentativa em nível de aplicação**: Cliente DNS tenta novamente se não houver resposta dentro do timeout
- **Uso disseminado**: Bilhões de consultas DNS por segundo no mundo todo

```python
# Consulta DNS típica sobre UDP
Porta de Origem: 54321 (porta efêmera aleatória)
Porta de Destino: 53 (porta padrão DNS)
Comprimento: 29 bytes (cabeçalho de 8 bytes + consulta de 21 bytes)
Checksum: 0x1a2b
Dados: "google.com A?" (Consulta por registro A)
```

**Por que o UDP importa para automação de navegador:**

- **WebRTC usa UDP** para áudio/vídeo em tempo real (não pode ser proxyado por proxies HTTP)
- **Consultas DNS usam UDP** (podem vazar requisições DNS se não proxyadas)
- **SOCKS5 suporta UDP** (diferente de SOCKS4 ou proxies HTTP)
- **UDP contorna proxies** a menos que explicitamente configurado
- **Sem números de sequência** significa sem fingerprinting via ISN (diferente do TCP)

!!! danger "O Vazamento UDP do WebRTC"
    Aqui está o problema crítico: Seu navegador faz **consultas DNS sobre UDP** e **conexões WebRTC sobre UDP**. A maioria das configurações de proxy cobre apenas **tráfego TCP** (HTTP, HTTPS, WebSocket).
    
    Resultado: Seu tráfego TCP (páginas web, chamadas de API) passa pelo proxy com o IP do proxy, mas seu **tráfego UDP vaza seu IP real diretamente**.
    
    É por isso que mesmo com um proxy, sites podem descobrir seu IP real via WebRTC. Ele está usando **UDP diretamente**, contornando seu proxy inteiramente.

**Suporte a Proxy UDP por Protocolo:**

| Tipo de Proxy | Suporte UDP | Notas |
|---|---|---|
| Proxy HTTP | Não | Proxyia apenas HTTP/HTTPS baseado em TCP |
| Proxy HTTPS (CONNECT) | Não | Método CONNECT estabelece apenas túnel TCP |
| SOCKS4 | Não | Protocolo apenas TCP |
| SOCKS5 | Sim | Suporta relay UDP via comando `UDP ASSOCIATE` |
| VPN | Sim | Tunela todo o tráfego IP (TCP e UDP) |

**Implicação Prática:**

Para **anonimato verdadeiro** em automação de navegador, você precisa de **uma destas opções**:
1.  **Proxy SOCKS5** (para proxyar UDP) + WebRTC configurado para usar SOCKS5
2.  **Desabilitar o WebRTC inteiramente** (previne vazamentos UDP, mas quebra videoconferência)
3.  **VPN** (tunela todo o tráfego, TCP e UDP)
4.  **Flags do navegador**: `--force-webrtc-ip-handling-policy=disable_non_proxied_udp`

!!! tip "Fingerprinting UDP"
    Diferente do TCP, o UDP não tem handshake e campos de cabeçalho mínimos, tornando-o **mais difícil de aplicar fingerprinting**. No entanto, **características de tempo** (intervalos de pacotes, jitter) e **padrões de payload** ainda podem revelar comportamento da aplicação.

## WebRTC e Vazamento de IP

WebRTC (Web Real-Time Communication) é uma API de navegador padronizada pelo W3C que habilita comunicação **ponto-a-ponto** (peer-to-peer) de áudio, vídeo e dados diretamente entre navegadores, sem requerer plugins ou servidores intermediários. Embora poderosa para aplicações em tempo real, o WebRTC é a **maior fonte isolada de vazamento de IP** em automação de navegador com proxy.

### Por que o WebRTC Vaza Seu IP

O WebRTC foi projetado para **conexões ponto-a-ponto diretas**, otimizando para baixa latência em detrimento da privacidade. Para estabelecer conexões P2P, o WebRTC deve descobrir seu **endereço IP público real** e compartilhá-lo com o par remoto, mesmo se seu navegador estiver configurado para usar um proxy.

**O problema fundamental:**
1.  Seu navegador usa um proxy para HTTP/HTTPS (tráfego TCP)
2.  WebRTC usa **servidores STUN** para descobrir seu IP público real (tráfego UDP)
3.  Consultas STUN **contornam o proxy** (porque são UDP e a maioria dos proxies lida apenas com TCP)
4.  Seu IP real é descoberto e **compartilhado com pares remotos**
5.  JavaScript pode ler esses "candidatos ICE" e **vazar seu IP real para sites**

!!! danger "Gravidade dos Vazamentos WebRTC"
    Mesmo com:

    - Proxy HTTP configurado corretamente
    - Proxy HTTPS funcionando
    - Consultas DNS proxyadas
    - User-Agent falsificado
    - Fingerprinting de Canvas mitigado
    
    **O WebRTC ainda pode vazar seu IP real em milissegundos**. Isso porque o WebRTC opera **abaixo da camada de proxy do navegador**, interagindo diretamente com a pilha de rede do SO.

### Como o WebRTC Estabelece Conexões: O Processo ICE

O WebRTC usa **ICE (Interactive Connectivity Establishment)**, definido na RFC 8445, para descobrir caminhos de conexão possíveis e selecionar o melhor. Este processo inerentemente revela sua topologia de rede.

```mermaid
sequenceDiagram
    participant Browser
    participant STUN as Servidor STUN
    participant TURN as Retransmissor TURN
    participant Peer as Par Remoto
    
    Note over Browser: Conexao WebRTC iniciada
    
    Browser->>Browser: Coletar enderecos IP locais<br/>(interfaces LAN)
    Note over Browser: Candidato local:<br/>192.168.1.100:54321
    
    Browser->>STUN: Requisicao STUN Binding (sobre UDP)
    Note over STUN: Servidor STUN descobre IP publico<br/>(contorna o proxy!)
    STUN->>Browser: Resposta STUN com IP publico real
    Note over Browser: Candidato reflexivo de servidor:<br/>203.0.113.45:54321
    
    Browser->>TURN: Alocar retransmissor (se necessario)
    TURN->>Browser: Endereco de retransmissao atribuido
    Note over Browser: Candidato de retransmissao:<br/>198.51.100.10:61234
    
    Browser->>Peer: Enviar todos os candidatos ICE<br/>(local + publico + retransmissao)
    Note over Peer: Agora sabe seu:<br/>- IP da LAN<br/>- IP publico real<br/>- Endereco de retransmissao
    
    Peer->>Browser: Enviar candidatos ICE
    
    Note over Browser,Peer: Negociacao ICE: tenta P2P direto primeiro
    
    alt P2P Direto bem-sucedido
        Browser<<->>Peer: Conexao direta (contorna o proxy inteiramente!)
    else P2P Direto falha (firewall/NAT)
        Browser->>TURN: Usar retransmissor TURN
        TURN<<->>Peer: Conexao retransmitida
        Note over Browser,Peer: Latencia mais alta, mas funciona
    end
```

### Tipos de Candidatos ICE: O que Vaza

O ICE descobre três tipos de "candidatos" (endpoints de conexão possíveis):

**1. Candidatos Host (Endereços IP da LAN Local)**

Seu navegador enumera todas as interfaces de rede locais e cria candidatos para cada:

```javascript
// Exemplo de candidatos host revelados pelo WebRTC
candidate:1 1 UDP 2130706431 192.168.1.100 54321 typ host
candidate:2 1 UDP 2130706431 10.0.0.5 54322 typ host
candidate:3 1 UDP 2130706431 172.16.0.10 54323 typ host
```

**O que isso revela:**

- Seu(s) **endereço(s) IP local(is)** em redes privadas
- Sua **topologia de rede** (presença de interfaces VPN, pontes de VM, etc.)
- **Número de interfaces de rede** (único Wi-Fi vs múltiplos ethernet/VPN)

Mesmo se você estiver atrás de um NAT, isso revela sua **estrutura de rede interna**.

**2. Candidatos Reflexivos de Servidor (IP Público via STUN)**

O navegador envia uma requisição STUN para um servidor STUN público, que responde com seu **endereço IP público** como visto da internet:

```javascript
// Candidato reflexivo de servidor (SEU IP PÚBLICO REAL!)
candidate:4 1 UDP 1694498815 203.0.113.45 54321 typ srflx raddr 192.168.1.100 rport 54321
```

**O que isso revela:**

- Seu **endereço IP público real** (aquele que você está tentando esconder com um proxy!)
- Seu **tipo de NAT** e mapeamento de porta externa
- Seu **ISP** (via geolocalização IP/WHOIS)

**Este é o vazamento** do qual todos falam: seu proxy mostra `198.51.100.5` mas o WebRTC revela `203.0.113.45` (seu IP real).

**3. Candidatos de Retransmissão (Endereços de retransmissão TURN)**

Se o P2P direto falhar, o navegador aloca um endereço de retransmissão de um servidor TURN:

```javascript
// Candidato de retransmissão (Endereço do servidor TURN)
candidate:5 1 UDP 16777215 198.51.100.10 61234 typ relay raddr 203.0.113.45 rport 54321
```

**O que isso revela:**

- **Servidor TURN** sendo usado (pode revelar seu provedor de VoIP, etc.)
- **Ainda contém seu IP real** no campo `raddr` (endereço remoto)

### Protocolo STUN: O Mecanismo de Descoberta de IP

STUN (Session Traversal Utilities for NAT), definido na RFC 5389, é um protocolo simples de requisição-resposta sobre UDP que descobre seu endereço IP público perguntando a um servidor "qual IP você vê de mim?"

**Estrutura da Mensagem STUN**:

```python
# Requisição STUN Binding (simplificada)
{
    'message_type': 0x0001,  # Binding Request
    'message_length': 0,      # Sem atributos adicionais
    'magic_cookie': 0x2112A442,  # Valor fixo (RFC 5389)
    'transaction_id': b'\x01\x02\x03...\x0c'  # 12 bytes aleatórios
}

# Enviado via UDP para servidor STUN (ex: stun.l.google.com:19302)
```

**Resposta STUN Binding**:

```python
# Resposta STUN Binding Success
{
    'message_type': 0x0101,  # Binding Success Response
    'message_length': 12,     # Atributo XOR-MAPPED-ADDRESS
    'magic_cookie': 0x2112A442,
    'transaction_id': b'\x01\x02\x03...\x0c',  # Mesmo da requisição
    'attributes': {
        'XOR-MAPPED-ADDRESS': {
            'family': 'IPv4',
            'port': 54321,
            'address': '203.0.113.45'  # SEU IP PÚBLICO REAL!
        }
    }
}
```

**Por que XOR-MAPPED-ADDRESS?**
O endereço IP é "XORado" com o magic cookie e o ID da transação para **compatibilidade com NAT**. Alguns dispositivos NAT modificam incorretamente endereços IP em payloads de pacotes, quebrando o STUN. O XOR ofusca o IP, prevenindo interferência do NAT.

**Servidores STUN Públicos** (comumente usados por navegadores):

- `stun.l.google.com:19302` (Google)
- `stun1.l.google.com:19302` (Google)
- `stun.services.mozilla.com` (Mozilla)
- `stun.stunprotocol.org:3478` (Servidor STUN aberto)

### Por que Proxies Não Podem Parar Vazamentos WebRTC

**1. Protocolo UDP**: WebRTC usa **UDP**, a maioria dos proxies lida apenas com **TCP**

   - Proxies HTTP: Apenas TCP
   - HTTPS CONNECT: Apenas túnel TCP
   - SOCKS4: Apenas TCP
   - Apenas **SOCKS5** suporta UDP (mas o navegador deve ser configurado para usá-lo)

**2. Implementação em Nível de Navegador**: WebRTC é uma **API de navegador**, não um recurso HTTP

   - Opera abaixo da camada HTTP
   - Acessa diretamente a pilha de rede do SO
   - Contorna configurações de proxy configuradas para HTTP/HTTPS

**3. Acesso Direto à Rede do SO**: Consultas STUN vão **diretamente para a interface de rede**

   - Configurações de proxy do navegador não se aplicam ao STUN
   - Tabela de roteamento do SO determina o caminho (não a config. de proxy do navegador)
   - Apenas roteamento em nível de VPN pode interceptar

**4. Enumeração de Múltiplas Interfaces**: WebRTC enumera **todas** as interfaces de rede

   - Ethernet física, Wi-Fi, adaptadores VPN, pontes de VM
   - Mesmo interfaces não usadas para navegação
   - Vaza topologia de rede interna

**5. Acessibilidade JavaScript**: Páginas web podem **ler candidatos ICE** via JavaScript

   - Evento `RTCPeerConnection.onicecandidate`
   - Extrai endereços IP das strings de candidatos
   - Envia seu IP real para o servidor deles

### Prevenindo Vazamentos WebRTC no Pydoll

O Pydoll fornece múltiplas estratégias para prevenir vazamentos de IP via WebRTC:

**Método 1: Forçar WebRTC a Usar Apenas Rotas Proxyadas (Recomendado)**

```python
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
options.webrtc_leak_protection = True  # Adiciona --force-webrtc-ip-handling-policy=disable_non_proxied_udp
```

O Pydoll fornece uma propriedade conveniente `webrtc_leak_protection` que gerencia o argumento `--force-webrtc-ip-handling-policy=disable_non_proxied_udp` automaticamente.

**O que isso faz:**

- Desabilita UDP se nenhum proxy o suportar
- Força o WebRTC a usar **apenas retransmissores TURN** (sem P2P direto)
- Previne consultas STUN para servidores públicos
- **Trade-off**: Quebra P2P direto (latência mais alta para chamadas de vídeo)

**Método 2: Desabilitar WebRTC Inteiramente**

```python
options.add_argument('--disable-features=WebRTC')
```

**O que isso faz:**

- Desabilita completamente a API WebRTC
- Nenhum vazamento de IP possível
- **Trade-off**: Quebra todos os sites dependentes de WebRTC (videoconferência, chamadas de voz)

**Método 3: Restringir WebRTC via Preferências do Navegador**

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

**O que isso faz:**

- `ip_handling_policy`: Mesmo que o Método 1, mas via preferências
- `multiple_routes_enabled`: Previne o uso de múltiplos caminhos de rede
- `nonproxied_udp_enabled`: Bloqueia UDP que não passa pelo proxy

**Método 4: Usar Proxy SOCKS5 com Suporte UDP**

```python
options.add_argument('--proxy-server=socks5://proxy.example.com:1080')
# Para proxies com autenticação:
# options.add_argument('--proxy-server=socks5://usuario:senha@proxy.example.com:1080')
options.add_argument('--force-webrtc-ip-handling-policy=default_public_interface_only')
```

**O que isso faz:**

- SOCKS5 pode proxyar UDP (via comando `UDP ASSOCIATE`)
- WebRTC usa proxy para consultas STUN
- **Requer**: Proxy deve suportar UDP (nem todos os proxies SOCKS5 suportam)

### Testando Vazamentos WebRTC

**Teste Manual:**

1.  Visite **https://browserleaks.com/webrtc**
2.  Verifique a seção "Public IP Address"
3.  Se você vir **seu IP real** (não o IP do proxy), você está vazando

**Teste Automatizado com Pydoll:**

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
        
        # Esperar resultados carregarem
        await asyncio.sleep(3)
        
        # Extrair IPs detectados
        ips = await tab.execute_script(```
            return Array.from(document.querySelectorAll('.ip-address'))
                .map(el => el.textContent.trim());
        ```)
        
        print("IPs Detectados:", ips)
        # Deve mostrar apenas IP do proxy, não seu IP real

asyncio.run(test_webrtc_leak())
```

!!! danger "Sempre Teste Vazamentos WebRTC"
    **Nunca assuma** que sua configuração de proxy previne vazamentos WebRTC. Sempre teste com https://browserleaks.com/webrtc ou https://ipleak.net para verificar se seu IP real não está exposto.
    
    Até mesmo um único vazamento WebRTC instantaneamente **compromete toda a sua configuração de proxy**. Sites agora sabem sua localização real, ISP e topologia de rede.

### Avançado: Detecção de Vazamento WebRTC por Sites

Sites usam JavaScript para intencionalmente disparar o WebRTC e extrair seu IP real:

```javascript
// Código de site malicioso para extrair IP real via WebRTC
const pc = new RTCPeerConnection({
    iceServers: [{urls: 'stun:stun.l.google.com:19302'}]
});

pc.createDataChannel('');  // Criar canal de dados fictício
pc.createOffer().then(offer => pc.setLocalDescription(offer));

pc.onicecandidate = (event) => {
    if (event.candidate) {
        const ipRegex = /([0-9]{1,3}(\.[0-9]{1,3}){3})/;
        const ipMatch = event.candidate.candidate.match(ipRegex);
        
        if (ipMatch) {
            const realIP = ipMatch[1];
            // Enviar IP real para o servidor
            fetch(`/track?real_ip=${realIP}&proxy_ip=${window.clientIP}`);
        }
    }
};
```

Este código:

1.  Cria um RTCPeerConnection (objeto de conexão WebRTC)
2.  Dispara a coleta de candidatos ICE (contata servidores STUN)
3.  Extrai endereços IP dos candidatos com regex
4.  Envia seu IP real para o servidor de rastreamento deles

**Sua defesa:** Desabilitar o WebRTC ou forçar rotas apenas proxyadas, como mostrado acima.

## Resumo e Leitura Adicional

Entender os fundamentos de rede (camadas OSI, características TCP/UDP e arquitetura ponto-a-ponto do WebRTC) é **essencial** para implementar anonimato eficaz baseado em proxy.

**Pontos Chave:**

- Proxies operam em **camadas específicas** (HTTP na Camada 7, SOCKS na Camada 5), determinando suas capacidades
- **Fingerprints TCP** (tamanho da janela, opções, TTL) vazam de camadas inferiores, revelando seu SO real
- **Tráfego UDP** (WebRTC, DNS) frequentemente contorna proxies a menos que explicitamente configurado
- **WebRTC** é a fonte nº 1 de vazamento de IP. Sempre teste com browserleaks.com
- Apenas **SOCKS5** ou **VPN** podem proxyar tráfego UDP eficazmente

**Próximos Passos:**

- **[Proxies HTTP/HTTPS](./http-proxies.md)** - Mergulhe em proxying de camada de aplicação
- **[Proxies SOCKS](./socks-proxies.md)** - Aprenda proxying agnóstico a protocolo de camada de sessão
- **[Network Fingerprinting](../fingerprinting/network-fingerprinting.md)** - Técnicas de fingerprinting TCP/IP
- **[Configuração de Proxy](../../features/configuration/proxy.md)** - Configuração prática de proxy no Pydoll

## Referências

- **RFC 793**: Transmission Control Protocol (TCP) - https://tools.ietf.org/html/rfc793
- **RFC 768**: User Datagram Protocol (UDP) - https://tools.ietf.org/html/rfc768
- **RFC 5389**: Session Traversal Utilities for NAT (STUN) - https://tools.ietf.org/html/rfc5389
- **RFC 8445**: Interactive Connectivity Establishment (ICE) - https://tools.ietf.org/html/rfc8445
- **RFC 5766**: Traversal Using Relays around NAT (TURN) - https://tools.ietf.org/html/rfc5766
- **RFC 6528**: Defending Against Sequence Number Attacks - https://tools.ietf.org/html/rfc6528
- **W3C WebRTC 1.0**: Real-Time Communication Between Browsers - https://www.w3.org/TR/webrtc/
- **BrowserLeaks**: Teste de Vazamento WebRTC - https://browserleaks.com/webrtc
- **IPLeak**: Teste Abrangente de Vazamento - https://ipleak.net