# Detecção de Proxy

A detecção de proxy é um processo probabilístico. Sites combinam dezenas de sinais para avaliar se uma conexão está sendo proxyada, desde simples consultas de reputação de IP até análise da pilha TCP/IP e perfil comportamental. Nenhum sinal isolado fornece prova definitiva, mas combinar sinais fracos suficientes produz decisões de alta confiança.

Este documento cobre as principais técnicas de detecção, como elas funcionam em nível técnico e o que significam para automação de navegador com o Pydoll.

!!! info "Navegação do Módulo"
    - [Proxies SOCKS](./socks-proxies.md): Proxying na camada de sessão
    - [Proxies HTTP/HTTPS](./http-proxies.md): Proxying na camada de aplicação
    - [Fundamentos de Rede](./network-fundamentals.md): TCP/IP, UDP, WebRTC

    Para detalhes sobre fingerprinting, veja [Network Fingerprinting](../fingerprinting/network-fingerprinting.md) e [Browser Fingerprinting](../fingerprinting/browser-fingerprinting.md).

## Reputação de IP

A análise de reputação de IP é a técnica de detecção de proxy mais amplamente implantada. Ela combina dados publicamente disponíveis (registros ASN, WHOIS, bancos de dados de geolocalização) com inteligência proprietária para classificar endereços IP em categorias de risco.

### Classificação por ASN

Todo endereço IP pertence a um Sistema Autônomo (AS), identificado por um ASN. O tipo de AS que possui um IP é o indicador individual mais forte de que ele é um proxy.

IPs pertencentes a provedores de nuvem e hospedagem (AWS, DigitalOcean, OVH, Hetzner) são sinalizados como alto risco porque usuários reais não navegam na web a partir de servidores de datacenter. IPs de ISPs residenciais (Comcast, Deutsche Telekom, BT) são baixo risco porque parecem conexões domésticas normais. IPs de operadoras móveis (Verizon Wireless, AT&T Mobility) são o risco mais baixo porque são os mais difíceis de distinguir de usuários móveis reais.

Alguns ASNs estão associados a infraestrutura conhecida de proxy, embora isso seja mais nuançado do que possa parecer. Grandes provedores de proxy residencial como BrightData ou Smartproxy não operam seus próprios ASNs; eles roteiam tráfego através de IPs residenciais reais pertencentes a ASNs de ISPs. Isso é precisamente o que torna proxies residenciais mais difíceis de detectar do que proxies de datacenter.

Sistemas de detecção consultam bancos de dados de ASN (Team Cymru, RIPE NCC, ARIN) e APIs comerciais de inteligência de IP para classificar cada IP conectando. IPs de datacenter são detectados com aproximadamente 95%+ de precisão porque a classificação por ASN é inequívoca. A detecção de proxy residencial é muito mais difícil (aproximadamente 40-70% de precisão) porque os IPs genuinamente pertencem a ISPs. A detecção de proxy móvel é a mais difícil (aproximadamente 20-40%) porque o NAT de operadoras móveis faz muitos usuários reais compartilharem IPs.

Esse gradiente de precisão é o motivo pelo qual proxies residenciais e móveis custam de 10 a 100 vezes o preço dos proxies de datacenter.

### Bancos de Dados de Proxies Conhecidos

Além da classificação por ASN, bancos de dados especializados rastreiam IPs que foram observados participando de redes de proxy. Serviços como IPQualityScore, proxycheck.io e Spur.us mantêm bancos de dados em tempo real de IPs conhecidos de proxy, VPN e nós de saída Tor. A lista de nós de saída Tor está disponível publicamente em [check.torproject.org](https://check.torproject.org/torbulkexitlist).

Esses bancos de dados também rastreiam sinais comportamentais: IPs que rotacionam frequentemente (típico de pools de proxy), IPs com contagens anormalmente altas de sessões concorrentes (um IP residencial normalmente tem 1-5 conexões concorrentes, não 100+) e IPs previamente associados a atividade semelhante a bot.

### Consistência de Geolocalização

Proxies frequentemente se revelam através de inconsistências geográficas. O endereço IP aponta para uma localização, mas os sinais reportados pelo navegador apontam para outra.

Os desencontros mais comuns são entre a geolocalização do IP e o fuso horário do navegador (coletado via `Intl.DateTimeFormat().resolvedOptions().timeZone` do JavaScript), entre o país do IP e o cabeçalho `Accept-Language`, e entre a localização da sessão atual e a localização de uma sessão anterior. Um usuário aparecendo em Los Angeles com fuso horário do navegador `Europe/Berlin` é suspeito. Um usuário aparecendo em Tóquio 10 minutos após sua última sessão ter sido em Nova York é fisicamente impossível.

Sistemas de detecção também verificam se a geolocalização do IP corresponde à configuração de localidade do navegador. Um IP de datacenter dos EUA com `Accept-Language: zh-CN` e fuso horário `Asia/Shanghai` sugere fortemente um usuário chinês roteando através de um proxy nos EUA.

!!! note "Falsos Positivos"
    Cenários legítimos disparam alarmes de geolocalização: viajantes usando VPNs, expatriados com configurações de navegador do país de origem, usuários corporativos conectando através de VPNs da empresa e usuários multilíngues com preferências de idioma não padrão. Sistemas sofisticados usam pontuação de risco em vez de bloqueio binário para lidar com esses casos.

## Análise de Cabeçalho HTTP

Cabeçalhos HTTP são o vetor de detecção mais simples. Proxies transparentes e anônimos adicionam cabeçalhos como `Via`, `X-Forwarded-For`, `X-Real-IP` e `Forwarded` (RFC 7239) que revelam diretamente o uso de proxy. Proxies elite removem esses cabeçalhos, mas sua ausência por si só não é prova de uma conexão direta.

A detecção vai além de procurar cabeçalhos específicos de proxy. Cabeçalhos ausentes que navegadores reais sempre enviam (como `Accept-Language`, `Accept-Encoding` ou um `User-Agent` realista) são suspeitos. A ordem dos cabeçalhos também importa: navegadores enviam cabeçalhos em uma ordem consistente e específica da versão, e proxies ou ferramentas de automação que constroem cabeçalhos manualmente frequentemente erram a ordem.

O cabeçalho legado `Proxy-Connection: keep-alive`, enviado por alguns clientes mais antigos ao rotear através de um proxy, é outro sinal clássico de detecção.

### Níveis de Anonimato de Proxy

Proxies são tradicionalmente classificados em três níveis de anonimato com base em seu comportamento de cabeçalhos:

| Nível | Comportamento | Detecção |
|-------|---------------|----------|
| Transparente | Encaminha seu IP real em `X-Forwarded-For`, adiciona cabeçalho `Via` | Trivial |
| Anônimo | Esconde seu IP mas adiciona `Via` ou outros cabeçalhos de proxy | Fácil |
| Elite | Remove todos os cabeçalhos identificadores de proxy | Requer análise mais profunda |

Essa classificação data de uma era em que a análise de cabeçalhos era o método primário de detecção. Sistemas modernos de detecção usam reputação de IP, fingerprinting e análise comportamental, tornando a distinção transparente/anônimo/elite menos significativa. Um proxy elite com IP de datacenter é detectado instantaneamente através de consulta ASN. Um proxy transparente em um IP residencial ainda pode passar despercebido em sites menos sofisticados.

## Network Fingerprinting

O fingerprinting na camada de rede opera abaixo da camada de proxy, o que significa que pode detectar proxies mesmo quando o proxy em si está configurado perfeitamente.

### Fingerprinting de TCP/IP

Cada sistema operacional tem uma implementação única da pilha TCP que se revela durante o handshake TCP. O tamanho inicial da janela, a ordem das opções TCP, o TTL (Time To Live) e o fator de escala de janela são todos definidos pelo kernel, não pelo navegador, e não podem ser alterados por um proxy.

Sistemas de detecção comparam essas características TCP com o cabeçalho `User-Agent`. Se o User-Agent alega Windows 10 mas o fingerprint TCP mostra características de Linux (TTL de 64, tamanho de janela de 29200), o desencontro é um forte indicador de proxy. O Windows usa um TTL padrão de 128 e versões modernas tipicamente mostram um tamanho de janela de 65535, enquanto o Linux usa TTL 64 e tamanhos de janela em torno de 29200.

A análise de TTL adiciona outra camada. O TTL diminui em 1 a cada salto de rede. Se uma conexão Windows chega com TTL de 128, o cliente provavelmente está na mesma rede. Se chega com TTL de 115, cruzou aproximadamente 13 saltos. Se o valor do TTL não se alinha com a contagem esperada de saltos para a localização geográfica do IP, roteamento por proxy é provável.

Para valores detalhados de fingerprint TCP e suas implicações, veja [Network Fingerprinting](../fingerprinting/network-fingerprinting.md).

### Fingerprinting de TLS (JA3/JA4)

A mensagem TLS ClientHello é transmitida em texto plano e contém parâmetros suficientes para identificar unicamente a aplicação cliente: versão TLS, conjuntos de cifras suportados, extensões, curvas elípticas e algoritmos de assinatura. O fingerprint JA3 é um hash MD5 desses parâmetros concatenados em uma ordem específica. JA4 é uma alternativa mais recente e mais granular.

Cada versão de navegador produz um fingerprint JA3/JA4 distinto. Sistemas de detecção mantêm bancos de dados de fingerprints conhecidos para Chrome, Firefox, Safari e outros navegadores. Se o fingerprint JA3 não corresponde a nenhum navegador conhecido, ou não corresponde ao navegador alegado no User-Agent, a conexão é sinalizada.

Uma nuance importante: proxies SOCKS5 e túneis HTTP CONNECT passam o TLS ClientHello sem modificação, então o servidor destino vê o fingerprint real do navegador. O proxy não altera os parâmetros TLS nessas configurações. Apenas proxies MITM (que terminam e reestabelecem TLS) mudam o fingerprint, e nesse caso o fingerprint pertence ao software do proxy, não a um navegador real, o que por si só é um sinal de detecção.

### Fingerprinting de HTTP/2

Conexões HTTP/2 expõem sinais de fingerprinting que são distintos do TLS. O frame SETTINGS enviado no início de uma conexão HTTP/2 contém parâmetros como `HEADER_TABLE_SIZE`, `MAX_CONCURRENT_STREAMS`, `INITIAL_WINDOW_SIZE` e `MAX_HEADER_LIST_SIZE`. Cada navegador usa valores padrão diferentes para essas configurações.

A ordem e prioridade dos pseudo-cabeçalhos (`:method`, `:authority`, `:scheme`, `:path`), o comportamento de compressão HPACK e os pesos de prioridade de stream também variam entre navegadores. Ferramentas como [browserleaks.com/http2](https://browserleaks.com/http2) mostram como é o seu fingerprint HTTP/2.

Frameworks de automação e software de proxy que implementam suas próprias pilhas HTTP/2 frequentemente produzem fingerprints que não correspondem a nenhum navegador real, tornando isso um vetor eficaz de detecção.

### Detecção Baseada em Latência

A latência de rede entre um cliente e um servidor revela informações sobre o caminho físico da rede. Se o IP geolocaliza em Nova York mas o tempo de ida e volta sugere um caminho pela Ásia, a conexão provavelmente está sendo proxyada.

Sistemas de detecção medem o RTT (round-trip time) durante o handshake TCP e comparam com latências esperadas para a localização geográfica do IP. Eles também podem emitir desafios de temporização baseados em JavaScript que medem a latência da perspectiva do navegador, e então comparar com a latência observada pelo servidor. Uma discrepância significativa entre as duas sugere um intermediário (proxy) no caminho.

A análise de desvio de relógio adiciona outra dimensão: ao medir o deslocamento do relógio do cliente via JavaScript (`Date.now()`) ou cabeçalhos HTTP `Date`, sistemas de detecção podem inferir o fuso horário real do cliente e compará-lo com o fuso horário esperado do IP.

## Detecção Comportamental

Os sistemas de detecção mais avançados vão além da análise de rede e protocolo para examinar o comportamento do usuário. Isso inclui temporização de requisições (as requisições estão espaçadas uniformemente, sugerindo automação?), padrões de movimento do mouse (analisados via listeners de eventos JavaScript), comportamento de rolagem, cadência de entrada do teclado e padrões gerais de navegação.

Modelos de machine learning treinados em milhões de sessões de usuários reais podem distinguir comportamento humano de automação com alta precisão. Esses modelos tipicamente combinam 50+ características incluindo padrões de navegação, distribuição de duração de sessão, posições de clique, temporização de interação com formulários e características de execução de JavaScript.

As interações humanizadas do Pydoll (movimento do mouse com curva de Bézier, temporização pela Lei de Fitts, digitação realista) são projetadas especificamente para passar na análise comportamental. Veja [Técnicas de Evasão](../fingerprinting/evasion-techniques.md) para a estratégia completa de evasão multicamada.

## Pontuação de Risco Multi-Sinal

Sistemas modernos de detecção não dependem de nenhuma técnica isolada. Eles combinam todos os sinais disponíveis em uma pontuação de risco, tipicamente de 0 a 100, e aplicam limiares que variam por indústria e contexto.

O peso de cada categoria de sinal varia, mas uma aproximação grosseira é que a reputação de IP representa a maior parcela (é o sinal mais barato e confiável), seguida por network fingerprinting (TCP/IP, TLS, HTTP/2), análise de cabeçalhos e protocolo, pontuação comportamental e verificações de consistência (geolocalização, fuso horário, idioma).

Os limiares dependem do contexto de negócio. Sites bancários bloqueiam agressivamente (pontuação de risco acima de 50), sites de e-commerce apresentam CAPTCHAs em pontuações moderadas (acima de 70), e sites de conteúdo tendem a ser mais permissivos (bloqueando apenas acima de 80) pois dependem de impressões de anúncios.

A implicação para automação é que passar em uma camada de detecção não é suficiente. Um IP residencial (boa reputação de IP) com um fingerprint TCP incompatível e comportamento robótico ainda será sinalizado. Evasão eficaz requer consistência em todas as camadas.

## Detecção por Tipo de Proxy

| Tipo de Proxy | Dificuldade de Detecção | Métodos Primários de Detecção |
|---------------|-------------------------|-------------------------------|
| HTTP Transparente | Trivial | Cabeçalhos HTTP (`Via`, `X-Forwarded-For`) |
| HTTP Anônimo | Fácil | Cabeçalhos HTTP + Reputação de IP |
| HTTP Elite (datacenter) | Médio | Reputação de IP (análise de ASN) |
| SOCKS5 Datacenter | Médio | Reputação de IP (análise de ASN) |
| Proxies residenciais | Difícil | Análise comportamental, padrões de conexão, latência |
| Proxies móveis | Muito difícil | Principalmente comportamental, sinais de rede limitados |
| Proxies rotativos | Difícil | Inconsistências de sessão, padrões de rotação de IP |

## Princípios de Evasão

Evasão eficaz é sobre consistência em todas as camadas de detecção, não sobre aperfeiçoar nenhuma camada individualmente.

Use IPs residenciais ou móveis quando a furtividade importar. Eles são mais difíceis de detectar porque os IPs genuinamente pertencem a ISPs, e o custo premium reflete essa vantagem. Alinhe os sinais de geolocalização do navegador (fuso horário, idioma, localidade) com a localização do IP do proxy. Mantenha persistência de sessão não rotacionando IPs no meio da sessão, o que cria descontinuidades detectáveis. Garanta que seu fingerprint TCP/IP corresponda à alegação do seu User-Agent executando automação no mesmo SO que você está imitando. Use as interações humanizadas do Pydoll para passar na análise comportamental. E sempre teste por vazamentos (WebRTC, DNS, fuso horário) antes de executar automação em escala.

O objetivo não é tornar a detecção impossível, mas sim torná-la cara e incerta. Force o sistema de detecção a usar múltiplos sinais correlacionados, misture-se com padrões de tráfego legítimo e crie negação plausível.

!!! warning "Nenhum Proxy é Indetectável"
    Com recursos suficientes, qualquer proxy pode ser detectado. Mesmo proxies residenciais de primeira linha alcançam aproximadamente 70-90% de taxa de sucesso contra sistemas anti-bot sofisticados como Akamai, Cloudflare Enterprise e DataDome. A questão prática é se a detecção é economicamente viável para o site alvo.

**Próximos passos:**

- [Network Fingerprinting](../fingerprinting/network-fingerprinting.md): Fingerprinting de TCP/IP e TLS em detalhes
- [Browser Fingerprinting](../fingerprinting/browser-fingerprinting.md): Fingerprinting de Canvas, WebGL, HTTP/2
- [Técnicas de Evasão](../fingerprinting/evasion-techniques.md): Estratégia de evasão multicamada
- [Configuração de Proxy](../../features/configuration/proxy.md): Configuração prática de proxy no Pydoll

## Referências

- MaxMind GeoIP2: https://www.maxmind.com/en/geoip2-services-and-databases
- IPQualityScore Proxy Detection: https://www.ipqualityscore.com/proxy-vpn-tor-detection-service
- Spur.us (Anonymous IP Detection): https://spur.us/
- Team Cymru IP to ASN Mapping: https://www.team-cymru.com/ip-asn-mapping
- Salesforce Engineering: TLS Fingerprinting with JA3 and JA3S - https://engineering.salesforce.com/tls-fingerprinting-with-ja3-and-ja3s-247362855967/
- Akamai: Passive Fingerprinting of HTTP/2 Clients (Black Hat EU 2017) - https://blackhat.com/docs/eu-17/materials/eu-17-Shuster-Passive-Fingerprinting-Of-HTTP2-Clients-wp.pdf
- Incolumitas: TCP/IP Fingerprinting for VPN and Proxy Detection - https://incolumitas.com/2021/03/13/tcp-ip-fingerprinting-for-vpn-and-proxy-detection/
- Incolumitas: Detecting Proxies and VPNs with Latencies - https://incolumitas.com/2021/06/07/detecting-proxies-and-vpn-with-latencies/
- BrowserLeaks HTTP/2 Fingerprint: https://browserleaks.com/http2
- BrowserLeaks IP: https://browserleaks.com/ip
- RFC 7239: Forwarded HTTP Extension - https://www.rfc-editor.org/rfc/rfc7239.html
- RFC 9110: HTTP Semantics - https://www.rfc-editor.org/rfc/rfc9110.html
