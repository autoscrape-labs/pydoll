# Proxies HTTP e HTTPS

Um proxy HTTP fica entre seu navegador e o servidor de destino e entende HTTP, então pode fazer parse, cachear, filtrar e modificar o tráfego que passa por ele. Esse acoplamento profundo com o protocolo é também seu limite: ele lida só com HTTP, se revela através de headers identificáveis, e não pode carregar UDP, o que deixa WebRTC e QUIC vazarem por fora dele.

Esta página cobre como proxies HTTP movem tráfego, o túnel CONNECT que carrega HTTPS, como a autenticação funciona, e onde protocolos modernos (HTTP/2, HTTP/3) complicam o cenário. Para configurar um proxy no Pydoll, veja [Proxies](../../guides/proxies.md). Fundo relacionado: [Fundamentos de rede](network-fundamentals.md), [Proxies SOCKS](socks-proxies.md) e [Detecção de proxy](proxy-detection.md).

## Como um proxy HTTP funciona

Um proxy HTTP mantém duas conexões TCP separadas: uma do cliente ao proxy, outra do proxy ao destino. Como ele lê HTTP, pode decidir o que fazer com cada requisição em vez de repassar bytes às cegas.

Quando um cliente está configurado para usar o proxy, ele envia a requisição completa ao proxy em vez de ao servidor. O indício é a linha de requisição: ela carrega a URI absoluta, não apenas o caminho. Em vez de `GET /page HTTP/1.1`, o cliente envia `GET http://example.com/page HTTP/1.1`, o que diz ao proxy para onde encaminhar.

```mermaid
sequenceDiagram
    participant Client as Navegador Cliente
    participant Proxy as Proxy HTTP
    participant Server as Servidor de Destino

    Client->>Proxy: GET http://example.com/page HTTP/1.1<br/>Host: example.com<br/>User-Agent: Mozilla/5.0
    Note over Client,Proxy: Conexão TCP #1

    Note over Proxy: Faz parse da requisição, checa auth,<br/>checa cache, aplica regras

    Proxy->>Server: GET /page HTTP/1.1<br/>Host: example.com<br/>Via: 1.1 proxy.example.com<br/>X-Forwarded-For: 192.168.1.100
    Note over Proxy,Server: Conexão TCP #2

    Server->>Proxy: HTTP/1.1 200 OK<br/>[corpo da resposta]

    Proxy->>Client: HTTP/1.1 200 OK<br/>Via: 1.1 proxy.example.com<br/>[corpo possivelmente modificado]
```

O proxy faz parse do método, da URL e dos headers, e então decide: checar credenciais, comparar a URL com uma lista de acesso, procurar uma cópia em cache, reescrever headers. Ele abre sua própria conexão ao servidor e encaminha a requisição. Quando a resposta volta, ele pode cacheá-la conforme `Cache-Control` e `ETag`, filtrar o conteúdo, comprimi-lo, e registrar a transação antes de repassá-la.

### Headers que entregam o proxy

Proxies HTTP comumente adicionam headers que revelam sua presença e o IP real do cliente:

- `Via` (RFC 9110) identifica o proxy na cadeia de requisições.
- `X-Forwarded-For` carrega o IP do cliente original, encadeando se vários proxies estiverem envolvidos. `X-Real-IP` é uma variante mais simples.
- `X-Forwarded-Proto` registra se a requisição original foi HTTP ou HTTPS.
- O header padronizado `Forwarded` (RFC 7239) combina esses em um único campo, embora a maioria dos proxies ainda envie as variantes `X-Forwarded-*`.

Clientes mais antigos também podem enviar `Proxy-Connection: keep-alive` em vez de `Connection: keep-alive`, que é um indicador clássico de proxy.

!!! warning "Headers confirmam um proxy"
    Sistemas de detecção procuram por `Via`, `X-Forwarded-For` ou `Forwarded`, e confirmam o proxy quando `X-Real-IP` diverge do IP de conexão. Bons proxies removem esses headers, mas muitos serviços comerciais os deixam por padrão. Cheque o seu com uma ferramenta como [browserleaks.com/ip](https://browserleaks.com/ip).

### O que ele pode e não pode fazer

Como faz parse de HTTP, um proxy pode ler e mudar cada parte de uma requisição e resposta não criptografadas (URLs, headers, cookies, corpos), que é o que habilita cache, filtragem de conteúdo, injeção de headers, autenticação e logging detalhado.

O custo desse acoplamento é o escopo. Ele não pode carregar FTP, SSH ou protocolos customizados nativamente (o CONNECT, abaixo, é a solução alternativa), não tem caminho para UDP, então WebRTC, DNS e QUIC o contornam, e inspecionar conteúdo HTTPS exige terminar o TLS, o que quebra a criptografia ponta a ponta.

## O método CONNECT: tunelando HTTPS

O CONNECT (RFC 9110) responde a uma pergunta básica: como um proxy encaminha tráfego criptografado que não consegue ler? Tornando-se um túnel TCP cego. O cliente pede ao proxy para abrir uma conexão TCP crua ao destino; uma vez confirmada, o proxy para de interpretar HTTP e apenas repassa bytes nos dois sentidos.

```mermaid
sequenceDiagram
    participant Client
    participant Proxy
    participant Server

    Client->>Proxy: CONNECT example.com:443 HTTP/1.1<br/>Host: example.com:443<br/>Proxy-Authorization: Basic dXNlcjpwYXNz
    Proxy->>Server: Handshake TCP de três vias
    Proxy->>Client: HTTP/1.1 200 Connection Established
    Note right of Proxy: O proxy é agora um relay TCP<br/>transparente (Camada 4)
    Client->>Server: TLS ClientHello
    Server->>Client: TLS ServerHello, Certificate
    Client->>Server: Requisição HTTP/2 criptografada
    Server->>Client: Resposta HTTP/2 criptografada
```

A requisição CONNECT é mínima: o método é `CONNECT`, o alvo é `host:port` (não um caminho), não há corpo. O proxy valida as credenciais, checa suas regras, abre a conexão TCP, e responde `HTTP/1.1 200 Connection Established` seguido de uma linha em branco. Depois dessa linha, a conversa HTTP acabou e o proxy é um relay.

### O que o proxy vê após o CONNECT

Uma vez que o túnel está de pé, o proxy conhece o host e a porta de destino, e pode observar o timing, o volume de dados em cada sentido, e quando cada lado desliga. Ele também vê o TLS ClientHello, que é enviado em texto claro: a versão do TLS, as cipher suites, as extensões, as curvas, e o hostname SNI. É exatamente isso que o fingerprinting de TLS (JA3/JA4) lê; veja [Fingerprinting de rede](../fingerprinting/network-fingerprinting.md).

O que ele não pode ver são os dados de aplicação criptografados: métodos, URLs, headers, cookies, tokens e corpos estão todos dentro do túnel TLS.

!!! note "SNI e Encrypted Client Hello"
    A extensão SNI revela o hostname de destino em texto claro, redundante com a linha CONNECT aqui mas visível a outros observadores da rede. O Encrypted Client Hello (ECH) visa escondê-lo, mas a adoção ainda é limitada e precisa de suporte tanto do cliente quanto do servidor.

O CONNECT pode tunelar qualquer protocolo TCP (IMAPS, SSH, FTPS), porque depois que o túnel abre o proxy apenas repassa bytes. Na prática, muitos proxies corporativos restringem o CONNECT à porta 443, então `CONNECT example.com:22` frequentemente retorna `403 Forbidden`.

### Túnel vs interceptação

Um proxy enfrenta uma escolha com tráfego criptografado. Um túnel CONNECT preserva a criptografia ponta a ponta: o cliente verifica o certificado do servidor diretamente e o certificate pinning funciona, mas o proxy não pode inspecionar nem cachear o conteúdo. A terminação de TLS (MITM) é a alternativa: o proxy descriptografa, inspeciona, e recriptografa, o que exige instalar seu certificado de CA no cliente, quebra a criptografia ponta a ponta, e é detectável através de pinning e Certificate Transparency. Proxies corporativos tendem a terminar para filtragem de conteúdo; proxies focados em privacidade usam túneis cegos.

Para automação, isso decide qual fingerprint TLS o servidor vê. Através de um túnel CONNECT, o fingerprint é o do seu navegador, de ponta a ponta. Através de um proxy que termina, é o do proxy.

| Aspecto | HTTP (sem CONNECT) | HTTPS (túnel CONNECT) |
|--------|-------------------|------------------------|
| Visibilidade do proxy | Requisição e resposta completas | host:port de destino + TLS ClientHello |
| Criptografia | Nenhuma (a menos que termine o TLS) | TLS ponta a ponta |
| Cache | Sim, por semântica HTTP | Não (criptografado) |
| Filtragem de conteúdo | Sim | Apenas por hostname |
| Visibilidade da URL | URL completa | Apenas hostname (CONNECT e SNI) |
| Suporte a protocolo | Apenas HTTP | Qualquer protocolo TCP |

## Conectando ao proxy sobre TLS

Fazer proxy de tráfego HTTPS é diferente de alcançar o próprio proxy sobre HTTPS. Configure `--proxy-server=https://proxy:port` (em vez de `http://`) e o salto entre seu navegador e o proxy fica criptografado por TLS, o que protege suas credenciais de proxy na rede local e esconde até o hostname do CONNECT de observadores locais. Isso importa mais em redes não confiáveis, onde o salto do cliente ao proxy é o menos protegido.

## Autenticação

Quando um proxy precisa de credenciais, ele responde `407 Proxy Authentication Required` com um header `Proxy-Authenticate` nomeando os esquemas que aceita, e o cliente tenta de novo com um header `Proxy-Authorization`.

- **Basic** (RFC 7617): envia `base64(username:password)`. Base64 é codificação, não criptografia, então é trivialmente reversível e não tem proteção contra replay. Use apenas sobre uma conexão TLS ao proxy.
- **Digest** (RFC 7616): um desafio-resposta sobre um nonce; a senha nunca é enviada e o nonce limita o replay. A forma original em MD5 é fraca (o SHA-256 foi adicionado depois), e raramente é implementada hoje.
- **NTLM**: o desafio-resposta proprietário da Microsoft, comum em redes Windows. É preso à conexão, então quebra com a multiplexação do HTTP/2, e seus hashes são fracos pelos padrões modernos.
- **Negotiate** (RFC 4559): SPNEGO selecionando Kerberos ou NTLM, preferindo Kerberos. O Kerberos é o mais forte, mas precisa de Active Directory, máquinas ligadas ao domínio e relógios sincronizados, o que é difícil de arranjar em automação.

| Esquema | Segurança | Mecanismo | Notas |
|--------|----------|-----------|-------|
| Basic | Baixa | Credenciais em Base64 | Universal. Só sobre TLS. |
| Digest | Média | Desafio-resposta (MD5/SHA-256) | Proteção contra replay. Raro. |
| NTLM | Média | Desafio-resposta (hash NT) | SSO do Windows. Quebra HTTP/2. |
| Negotiate | Alta | Kerberos/SPNEGO | Mais forte. Precisa de Active Directory. |

O Chrome não aceita credenciais embutidas em `--proxy-server`: `http://user:pass@proxy:port` conecta sem o `user:pass`. O Pydoll contorna isso para você (ele remove as credenciais da URL e responde ao desafio `407` via CDP), então você pode passar uma URL de proxy com credenciais. Veja [Proxies](../../guides/proxies.md) para o uso.

## Protocolos modernos

### HTTP/2

O HTTP/2 carrega múltiplos streams concorrentes sobre uma única conexão TCP, com framing binário e compressão de headers HPACK. Para um proxy, isso significa mapear IDs de stream entre os dois lados, manter árvores de prioridade, e fazer controle de fluxo por stream, o que é bem mais envolvido do que o encaminhamento sequencial do HTTP/1.1. Também importa para fingerprinting: os metadados de stream do HTTP/2 (tamanhos de janela, prioridades, ordem dos headers no HPACK) podem identificar clientes individuais mesmo quando muitos compartilham um proxy.

| Recurso | HTTP/1.1 | HTTP/2 |
|---------|----------|--------|
| Conexões | Sequencial por conexão (navegadores abrem ~6 em paralelo) | Streams concorrentes sobre uma conexão |
| Multiplexação | Não | Sim (nível de stream) |
| Compressão de headers | Nenhuma | HPACK |
| Complexidade do proxy | Encaminhamento simples | Mapeamento de streams, prioridades |

### HTTP/3 e QUIC

O HTTP/3 roda sobre o QUIC, um transporte UDP, o que quebra as suposições de proxies baseados em TCP. Proxies tradicionais não conseguem carregar QUIC, suas conexões sobrevivem a mudanças de IP, e ele criptografa quase todos os metadados de transporte. Fazer proxy dele precisa de CONNECT-UDP (RFC 9298), que muitos serviços ainda não suportam, então os navegadores caem para HTTP/2 sobre TCP quando o proxy não consegue fazer QUIC.

!!! warning "O downgrade silencioso vaza metadados"
    Quando um proxy não suporta HTTP/3, o navegador cai silenciosamente para HTTP/2 ou HTTP/1.1, expondo metadados de timing e header que o HTTP/3 teria criptografado. Em automação, considere forçar TCP com a flag `--disable-quic` para que todo o tráfego passe pelo proxy e não haja vazamentos baseados em UDP.

## Proxy HTTP vs SOCKS5

| Necessidade | Proxy HTTP | SOCKS5 |
|------|------------|--------|
| Filtragem de conteúdo / cache | Sim | Não |
| Bloqueio baseado em URL | Sim | Não (só IP:port) |
| Suporte a UDP | Não | Sim |
| Flexibilidade de protocolo | HTTP (CONNECT para túneis TCP) | Qualquer TCP/UDP |
| Privacidade | Baixa (faz parse de HTTP, adiciona headers) | Maior (não faz parse nem modifica) |
| Resolução de DNS | O proxy resolve | O Chrome resolve remotamente para SOCKS5 |

Proxies HTTP servem a ambientes que precisam de controle de conteúdo e cache. Para automação focada em privacidade, o SOCKS5 dá melhor stealth e flexibilidade de protocolo. Em automação, o túnel CONNECT mantém seu fingerprint TLS de ponta a ponta e dá ao proxy apenas visibilidade em nível de hostname.

## Relacionado

- [Proxies SOCKS](socks-proxies.md): proxying agnóstico ao protocolo, na camada de sessão.
- [Detecção de proxy](proxy-detection.md): os sinais que expõem um proxy.
- [Fundamentos de rede](network-fundamentals.md): TCP/IP, UDP, e as camadas por baixo.
- [Fingerprinting de rede](../fingerprinting/network-fingerprinting.md): fingerprinting de TCP/IP e TLS.
- [Proxies](../../guides/proxies.md): configurando proxies no Pydoll.

## Referências

- RFC 9110: HTTP Semantics: https://www.rfc-editor.org/rfc/rfc9110.html
- RFC 9113: HTTP/2: https://www.rfc-editor.org/rfc/rfc9113.html
- RFC 9114: HTTP/3: https://www.rfc-editor.org/rfc/rfc9114.html
- RFC 9000: QUIC: https://www.rfc-editor.org/rfc/rfc9000.html
- RFC 9298: Proxying UDP in HTTP (CONNECT-UDP): https://www.rfc-editor.org/rfc/rfc9298.html
- RFC 7617: Basic Authentication: https://www.rfc-editor.org/rfc/rfc7617.html
- RFC 7616: Digest Authentication: https://www.rfc-editor.org/rfc/rfc7616.html
- RFC 7239: Forwarded HTTP Extension: https://www.rfc-editor.org/rfc/rfc7239.html
- MDN: Proxy servers and tunneling: https://developer.mozilla.org/en-US/docs/Web/HTTP/Proxy_servers_and_tunneling
