# Detecção de proxy

A detecção de proxy é probabilística: um site combina dezenas de sinais fracos, de uma simples consulta de reputação de IP à análise da pilha TCP/IP, em uma pontuação de confiança. Nenhum sinal isolado é prova, mas o bastante deles juntos produz uma decisão de alta confiança. Esta página cobre as principais técnicas, como elas funcionam, e o que significam para automação.

Ela se apoia no resto da seção de rede: [Fundamentos de rede](network-fundamentals.md) para as camadas envolvidas, e [Proxies HTTP/HTTPS](http-proxies.md) e [Proxies SOCKS](socks-proxies.md) para como cada tipo de proxy se comporta.

## Reputação de IP

A reputação de IP é a técnica mais amplamente empregada. Ela combina dados públicos (registros de ASN, WHOIS, bancos de dados de geolocalização) com inteligência proprietária para ordenar endereços IP em categorias de risco.

### Classificação por ASN

Todo IP pertence a um Sistema Autônomo, identificado por um ASN, e o tipo de AS que possui um IP é o indicador isolado mais forte de se ele é ou não um proxy.

IPs de provedores de nuvem e hospedagem (AWS, DigitalOcean, OVH, Hetzner) são marcados como alto risco, porque usuários reais não navegam a partir de servidores em datacenter. IPs de ISPs residenciais (Comcast, Deutsche Telekom, BT) são baixo risco, porque parecem conexões domésticas. IPs de operadoras móveis (Verizon Wireless, AT&T Mobility) são o risco mais baixo, porque o NAT de operadora os torna difíceis de distinguir de usuários móveis reais.

Grandes provedores de proxy residencial não rodam seus próprios ASNs; eles roteiam através de IPs residenciais reais que pertencem a ASNs de ISPs. É exatamente isso que torna proxies residenciais mais difíceis de detectar do que os de datacenter.

Sistemas de detecção consultam bancos de dados de ASN (Team Cymru, RIPE NCC, ARIN) e APIs comerciais de inteligência de IP para classificar cada IP que conecta. IPs de datacenter são pegos com cerca de 95% de precisão porque o ASN é inequívoco. Proxies residenciais são bem mais difíceis (cerca de 40% a 70%) porque os IPs genuinamente pertencem a ISPs, e proxies móveis são os mais difíceis de todos (cerca de 20% a 40%). Esse gradiente de precisão é o motivo de proxies residenciais e móveis custarem muitas vezes mais do que proxies de datacenter.

### Bancos de dados de proxies conhecidos

Além da classificação por ASN, serviços especializados (IPQualityScore, proxycheck.io, Spur.us) mantêm bancos de dados em tempo real de IPs conhecidos de proxy, VPN e saída Tor. A lista de saída do Tor é pública em [check.torproject.org](https://check.torproject.org/torbulkexitlist).

Esses bancos de dados também rastreiam comportamento: IPs que rotacionam com frequência (típico de pools de proxy), IPs com contagens de sessões concorrentes anormalmente altas (um IP residencial normalmente tem um punhado de conexões, não centenas), e IPs vistos anteriormente em atividade de bot.

### Consistência de geolocalização

Proxies frequentemente se entregam por contradições geográficas: o IP aponta para um lugar enquanto sinais reportados pelo navegador apontam para outro.

As divergências comuns são entre a localização do IP e o timezone do navegador (`Intl.DateTimeFormat().resolvedOptions().timeZone`), entre o país do IP e o header `Accept-Language`, e entre a localização desta sessão e a da anterior. Um usuário em Los Angeles com timezone `Europe/Berlin` é suspeito. Um usuário em Tóquio dez minutos depois de sua última sessão ter sido em Nova York é impossível.

!!! note "Falsos positivos de geolocalização"
    Casos legítimos disparam esses alarmes: viajantes em VPNs, expatriados mantendo as configurações do país de origem, usuários de VPN corporativa, e usuários multilíngues com preferências de idioma não padrão. Bons sistemas usam pontuação de risco em vez de bloqueio binário para absorver esses casos.

## Análise de headers HTTP

Headers são o vetor de detecção mais simples. Proxies transparentes e anônimos adicionam headers como `Via`, `X-Forwarded-For`, `X-Real-IP` e `Forwarded` (RFC 7239) que revelam o uso de proxy diretamente. Proxies elite os removem, mas a ausência deles sozinha não é prova de uma conexão direta.

A detecção vai além de procurar por headers de proxy. Headers faltando que um navegador real sempre envia (`Accept-Language`, `Accept-Encoding`, um `User-Agent` realista) são suspeitos, e a ordem dos headers importa: navegadores enviam headers em uma ordem consistente e específica da versão, e ferramentas que montam headers à mão frequentemente erram. O header legado `Proxy-Connection: keep-alive` é outro indício clássico.

Proxies são tradicionalmente classificados por comportamento de header, embora a distinção importe menos agora que a reputação de IP e o fingerprinting dominam. Um proxy elite em um IP de datacenter ainda é pego instantaneamente por consulta de ASN:

| Nível | Comportamento | Detecção |
|-------|----------|-----------|
| Transparente | Encaminha seu IP real em `X-Forwarded-For`, adiciona `Via` | Trivial |
| Anônimo | Esconde seu IP mas adiciona `Via` ou outros headers de proxy | Fácil |
| Elite | Remove todos os headers que identificam proxy | Exige análise mais profunda |

## Fingerprinting de rede

O fingerprinting na camada de rede opera abaixo do proxy, então pode expor um proxy mesmo quando o próprio proxy está configurado perfeitamente. Esta é a teoria coberta em profundidade em [Fingerprinting de rede](../fingerprinting/network-fingerprinting.md); aqui está como ela alimenta a detecção de proxy.

**Fingerprinting de TCP/IP.** Todo SO tem uma pilha TCP distinta. O tamanho de janela inicial, a ordem das opções TCP, o TTL e o window scale são definidos pelo kernel, não pelo navegador, e um proxy não pode mudá-los. Se o `User-Agent` alega Windows 10 (TTL 128, window 65535) mas o fingerprint TCP mostra Linux (TTL 64, window em torno de 29200), a divergência é um sinal forte de proxy. O TTL também decresce em um a cada salto, então um valor que não se encaixa na contagem de saltos esperada para a localização do IP sugere roteamento através de um proxy.

**Fingerprinting de TLS (JA3/JA4).** O TLS ClientHello é enviado em texto claro e carrega parâmetros suficientes (versão, cipher suites, extensões, curvas) para identificar o cliente. Sistemas de detecção comparam seu hash JA3/JA4 contra bancos de dados de navegadores conhecidos. Uma nuance chave: proxies SOCKS5 e túneis HTTP CONNECT passam o ClientHello sem modificação, então o servidor vê o fingerprint real do navegador; só um proxy MITM que termina o TLS o altera, e aí o fingerprint pertence ao software do proxy, o que é em si um sinal.

**Fingerprinting de HTTP/2.** O frame `SETTINGS` do HTTP/2, a ordem dos pseudo-headers, e as prioridades de stream variam por navegador. Frameworks de automação e proxies com suas próprias pilhas HTTP/2 frequentemente produzem um fingerprint que não corresponde a nenhum navegador real.

**Latência.** O tempo de ida e volta durante o handshake revela o caminho físico. Se o IP geolocaliza em Nova York mas o RTT sugere um caminho pela Ásia, a conexão é provavelmente proxiada. Sistemas também podem rodar desafios de timing em JavaScript e comparar a latência observada pelo navegador contra a observada pelo servidor; uma grande diferença implica um intermediário.

## Detecção comportamental

Os sistemas mais avançados examinam o comportamento: timing das requisições, movimento do mouse (via listeners em JavaScript), rolagem, cadência de digitação, e padrões gerais de navegação. Modelos de machine learning treinados em milhões de sessões reais combinam dezenas de características (padrões de navegação, duração da sessão, posições de clique, timing de formulários) para separar humanos de automação.

As interações humanizadas do Pydoll (caminhos de mouse em curva com timing pela Lei de Fitts, digitação variável) miram nesta camada. Veja [Interações humanas](../../stealth/human-like-interactions.md) para o lado prático e [Fingerprinting comportamental](../fingerprinting/behavioral-fingerprinting.md) para a teoria.

## Pontuação de risco multi-sinal

Sistemas modernos não dependem de uma técnica. Eles dobram cada sinal em uma pontuação de risco (tipicamente 0 a 100) e aplicam um limiar que varia por contexto. A reputação de IP normalmente carrega o maior peso (é o sinal mais barato e confiável), seguida pelo fingerprinting de rede, análise de header e protocolo, pontuação comportamental, e checagens de consistência.

Os limiares seguem o negócio. Bancos bloqueiam agressivamente, e-commerce apresenta CAPTCHAs em pontuações moderadas, e sites de conteúdo tendem a ser permissivos. A lição para automação é que passar por uma camada não basta: um IP residencial com um fingerprint TCP divergente e comportamento robótico ainda é sinalizado. A consistência entre camadas é o que importa.

## Detecção por tipo de proxy

| Tipo de proxy | Dificuldade de detecção | Métodos principais |
|------------|----------------------|-----------------|
| HTTP Transparente | Trivial | Headers (`Via`, `X-Forwarded-For`) |
| HTTP Anônimo | Fácil | Headers + reputação de IP |
| HTTP Elite (datacenter) | Média | Reputação de IP (ASN) |
| SOCKS5 de datacenter | Média | Reputação de IP (ASN) |
| Residencial | Difícil | Comportamento, padrões de conexão, latência |
| Móvel | Muito difícil | Majoritariamente comportamental, poucos sinais de rede |
| Rotativo | Difícil | Inconsistências de sessão, padrões de rotação |

## O que a consistência exige

Evasão tem a ver com concordância entre camadas, não com aperfeiçoar uma delas. Na prática isso significa: prefira IPs residenciais ou móveis quando o stealth importa; case o timezone, o idioma e o locale do navegador com a localização do IP; mantenha uma sessão em um único IP em vez de rotacionar no meio da sessão; rode a automação no mesmo SO que você alega no `User-Agent` para que o fingerprint TCP concorde; humanize o comportamento; e teste vazamentos de WebRTC, DNS e timezone antes de rodar em escala. As [Técnicas de evasão](../../stealth/evasion-techniques.md) do Pydoll cobrem as alavancas práticas, incluindo proteção contra vazamento de WebRTC e o casamento do locale.

!!! warning "Nenhum proxy é indetectável"
    Com recursos suficientes, qualquer proxy pode ser detectado. Até proxies residenciais de primeira linha alcançam apenas cerca de 70% a 90% de sucesso contra sistemas sofisticados como Akamai, Cloudflare Enterprise e DataDome. A questão prática é se detectar você vale o custo para o alvo.

## Relacionado

- [Fundamentos de rede](network-fundamentals.md): as camadas pelas quais uma requisição passa.
- [Proxies HTTP/HTTPS](http-proxies.md) e [Proxies SOCKS](socks-proxies.md): como cada tipo de proxy se comporta.
- [Fingerprinting de rede](../fingerprinting/network-fingerprinting.md): assinaturas de TCP/IP, TLS e HTTP/2 em detalhe.
- [Proxies](../../guides/proxies.md): configurando um proxy no Pydoll.
- [Técnicas de evasão](../../stealth/evasion-techniques.md): as alavancas que você controla.

## Referências

- MaxMind GeoIP2: https://www.maxmind.com/en/geoip2-services-and-databases
- IPQualityScore Proxy Detection: https://www.ipqualityscore.com/proxy-vpn-tor-detection-service
- Spur.us (anonymous IP detection): https://spur.us/
- Team Cymru IP to ASN mapping: https://www.team-cymru.com/ip-asn-mapping
- Salesforce Engineering, TLS fingerprinting with JA3 and JA3S: https://engineering.salesforce.com/tls-fingerprinting-with-ja3-and-ja3s-247362855967/
- Akamai, Passive Fingerprinting of HTTP/2 Clients (Black Hat EU 2017): https://blackhat.com/docs/eu-17/materials/eu-17-Shuster-Passive-Fingerprinting-Of-HTTP2-Clients-wp.pdf
- Incolumitas, TCP/IP fingerprinting for VPN and proxy detection: https://incolumitas.com/2021/03/13/tcp-ip-fingerprinting-for-vpn-and-proxy-detection/
- Incolumitas, detecting proxies and VPNs with latencies: https://incolumitas.com/2021/06/07/detecting-proxies-and-vpn-with-latencies/
- BrowserLeaks HTTP/2 fingerprint: https://browserleaks.com/http2
- RFC 7239, Forwarded HTTP Extension: https://www.rfc-editor.org/rfc/rfc7239.html
- RFC 9110, HTTP Semantics: https://www.rfc-editor.org/rfc/rfc9110.html
