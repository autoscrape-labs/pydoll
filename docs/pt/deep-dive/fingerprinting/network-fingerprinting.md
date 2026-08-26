# Network fingerprinting

O network fingerprinting identifica clientes analisando características da pilha TCP/IP, do handshake TLS e da conexão HTTP/2. Esses sinais são definidos pelo kernel do sistema operacional e pela biblioteca TLS, não pelo ambiente JavaScript do navegador, o que os torna mais difíceis de forjar do que os fingerprints de nível de navegador. Um proxy ou VPN muda o seu endereço de IP, mas não altera o seu tamanho de janela TCP, a sua lista de cipher suites TLS nem o seu frame SETTINGS de HTTP/2. Os sistemas de detecção exploram essa lacuna.

Esta é a teoria por trás dos guias de [Stealth](../../stealth/index.md). Ela se combina com o [Browser fingerprinting](browser-fingerprinting.md) (os sinais visíveis ao JavaScript) e o [Behavioral fingerprinting](behavioral-fingerprinting.md) (como você se move e digita). Para saber como os próprios protocolos funcionam, veja [Network fundamentals](../network/network-fundamentals.md).

<iframe scrolling="no" src="/docs/resources/visuals/network-fingerprinting.html" aria-label="Below the JavaScript layer, the TLS ClientHello and HTTP/2 SETTINGS form a JA3 and JA4 fingerprint the page cannot spoof; a real Chrome matches its User-Agent while a Python client contradicts it" style="width: 100%; height: 900px; border: 0;" loading="lazy"></iframe>

## TCP/IP fingerprinting

Todo sistema operacional implementa a pilha TCP/IP de forma diferente. O pacote SYN que inicia uma conexão TCP carrega informação suficiente para identificar o SO com alta confiança: o TTL inicial, o tamanho da janela TCP, o Maximum Segment Size e a ordem e seleção das opções TCP. Nenhum desses valores é controlado pelo navegador. Eles vêm do kernel.

### TTL (time to live)

O TTL inicial é um dos identificadores de SO mais simples. Linux e macOS o definem como 64, o Windows o define como 128, e dispositivos de rede (roteadores, firewalls) tipicamente usam 255. Cada salto de roteador decrementa o TTL em um, então um pacote que chega com TTL 118 provavelmente começou em 128 (Windows) e cruzou 10 saltos.

O valor de fingerprinting do TTL vem de cruzá-lo com o User-Agent. Se o navegador alega ser Chrome no Windows mas o pacote chega com um TTL perto de 64, a conexão ou está com proxy através de um servidor Linux, ou o User-Agent foi forjado. Os sistemas de detecção arredondam o TTL observado para cima até o valor inicial conhecido mais próximo (64, 128, 255) e o comparam com o SO alegado.

Quando o tráfego flui através de um proxy, o TTL é reiniciado, porque o kernel do proxy gera uma nova conexão TCP para o alvo. O alvo vê o TTL do proxy, não o seu. É por isso que divergências de TTL são um sinal de detecção de proxy: o User-Agent diz Windows (TTL 128), mas o fingerprint TCP mostra Linux (TTL 64).

### Tamanho de janela TCP e scaling

O tamanho inicial da janela TCP no pacote SYN varia por SO e versão de kernel. Kernels Linux modernos (3.x e posteriores) tipicamente enviam uma janela inicial de 29200 bytes, que é `20 * MSS`, onde o MSS é 1460 para Ethernet padrão. Alguns kernels mais novos (5.x, 6.x) podem usar 64240 dependendo da configuração e dos ajustes de `initcwnd`. Windows 10 e 11 tipicamente enviam 65535 com window scaling ativado, embora o valor exato dependa da configuração de auto-tuning e do nível de patch. O macOS também usa 65535 por padrão.

O fator de window scale (uma opção TCP) multiplica o campo de tamanho de janela de 16 bits para suportar janelas de recepção maiores. O Linux comumente usa um fator de scale de 7 (permitindo janelas de até 8MB), enquanto o Windows frequentemente usa 8. Combinado com o tamanho de janela base, o fator de scale cria um fingerprint mais granular do que qualquer um dos valores isolados.

### Ordem das opções TCP

A seleção e a ordenação das opções TCP no pacote SYN são altamente distintivas. Cada SO organiza as opções numa ordem fixa e específica da versão, que o kernel não expõe como um parâmetro configurável. O Linux envia `MSS, SACK_PERM, TIMESTAMP, NOP, WSCALE`. O Windows envia `MSS, NOP, WSCALE, NOP, NOP, SACK_PERM` e omite a opção TIMESTAMP nas configurações padrão. O macOS envia `MSS, NOP, WSCALE, NOP, NOP, TIMESTAMP, SACK_PERM`.

A presença ou ausência de opções específicas importa tanto quanto a ordem. O Windows historicamente omitia os timestamps TCP, que Linux e macOS incluem por padrão. O SACK (Selective Acknowledgment) é suportado por todos os sistemas modernos, mas sistemas mais antigos ou embarcados podem não o anunciar. A combinação de quais opções aparecem e em que ordem cria uma assinatura que ferramentas como o p0f casam contra um banco de dados de fingerprints de SO conhecidos.

### p0f

O [p0f](https://lcamtuf.coredump.cx/p0f3/) é a ferramenta padrão para TCP/IP fingerprinting passivo. Ele observa o tráfego sem gerar nenhum pacote, analisando pacotes SYN e SYN+ACK contra um banco de dados de assinaturas. Seu formato de assinatura codifica os campos-chave de fingerprinting:

```
version:ittl:olen:mss:wsize,scale:olayout:quirks:pclass
```

O `ittl` é o TTL inicial inferido, o `mss` é o Maximum Segment Size, o `wsize,scale` é o tamanho de janela (que pode ser absoluto, ou relativo ao MSS como `mss*20`), e o `olayout` é o layout das opções TCP usando nomes abreviados (`mss`, `nop`, `ws`, `sok`, `sack`, `ts`, `eol+N`). O campo `quirks` captura comportamentos incomuns como a flag Don't Fragment (`df`) ou um IP ID não nulo em pacotes DF (`id+`).

Uma assinatura típica de Linux 4.x+ no p0f se parece com `4:64:0:*:mss*20,7:mss,sok,ts,nop,ws:df,id+:0`. Uma assinatura de Windows 10 pode se parecer com `4:128:0:*:65535,8:mss,nop,ws,nop,nop,sok:df,id+:0`. Os serviços anti-bot mantêm bancos de dados parecidos internamente, casando as conexões que chegam contra perfis de SO conhecidos e marcando divergências com o User-Agent declarado.

## TLS fingerprinting

A mensagem ClientHello do TLS é transmitida antes de a criptografia ser estabelecida, então ela é visível para qualquer observador no caminho da rede. Ela contém a versão do TLS, as cipher suites suportadas, as extensões TLS, as curvas elípticas suportadas (named groups) e os formatos de ponto EC. Cada navegador e biblioteca TLS produz uma combinação característica desses campos.

### JA3

O JA3, desenvolvido na Salesforce por John Althouse, Jeff Atkinson e Josh Atkins, foi o primeiro método de TLS fingerprinting amplamente adotado. Ele concatena cinco campos do ClientHello (versão do TLS, cipher suites, extensões, curvas elípticas, formatos de ponto EC), junta os valores dentro de cada campo com hífens, separa os cinco campos com vírgulas e calcula o hash MD5 da string resultante.

```
JA3 string: 771,4865-4866-4867-49195-49199-49196-49200-52393-52392,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0
JA3 hash:   cd08e31494b9531f560d64c695473da9
```

Uma sutileza: o campo "versão do TLS" no JA3 usa `ClientHello.legacy_version`, não a extensão `supported_versions`. Como o TLS 1.3 (RFC 8446) exige que os clientes definam `legacy_version` como `0x0303` (TLS 1.2) por compatibilidade retroativa, o campo de versão do JA3 é quase sempre `771` para clientes modernos, mesmo quando eles suportam TLS 1.3. A negociação real do TLS 1.3 acontece através da extensão 43 (`supported_versions`), mas o JA3 usa o campo do cabeçalho.

O JA3 precisa filtrar os valores GREASE antes de fazer o hash. O GREASE (RFC 8701) é um mecanismo em que os navegadores inserem valores reservados selecionados aleatoriamente nas cipher suites, extensões e outros campos para prevenir a ossificação do protocolo. Os valores GREASE válidos são `0x0a0a`, `0x1a1a`, `0x2a2a`, e assim por diante até `0xfafa`. Cada valor tem dois bytes idênticos em que o nibble baixo de cada byte é `0x0a`. Um filtro GREASE correto verifica ambas as condições:

```python
def is_grease(value: int) -> bool:
    return (value & 0x0f0f) == 0x0a0a and (value >> 8) == (value & 0xff)
```

!!! warning "Limitações do JA3 com navegadores modernos"
    Desde o Chrome 110 (janeiro de 2023) e o Firefox 114, os navegadores aleatorizam a ordem das extensões TLS em toda conexão. Isso significa que o mesmo navegador produz hashes JA3 diferentes a cada conexão, tornando o JA3 efetivamente inútil para identificar navegadores modernos. O JA3 continua útil para fazer o fingerprinting de clientes que não são navegadores (`requests` do Python, `curl`, bots customizados) e que não implementam a aleatorização de extensões.

### JA4

O JA4 é o sucessor do JA3, desenvolvido pelo mesmo autor principal (John Althouse) na FoxIO. Ele foi projetado especificamente para sobreviver à aleatorização de extensões TLS ao ordenar as extensões e as cipher suites antes de fazer o hash. O formato consiste em três seções separadas por underscores: `a_b_c`.

A seção `a` é uma string legível de metadados: o protocolo (`t` para TCP, `q` para QUIC), a versão do TLS (`12` ou `13`), se o SNI está presente (`d` para domínio, `i` para IP), o número de cipher suites (dois dígitos), o número de extensões (dois dígitos) e o primeiro e o último valor de ALPN (`h2` para HTTP/2, `00` se nenhum). Por exemplo, `t13d1516h2` significa TCP TLS 1.3 com SNI, 15 cipher suites, 16 extensões e ALPN HTTP/2.

A seção `b` é um hash SHA-256 truncado das cipher suites ordenadas. A seção `c` é um hash SHA-256 truncado das extensões ordenadas concatenadas com os algoritmos de assinatura. Como ambas as listas são ordenadas antes do hash, a aleatorização de extensões não afeta a saída.

Cloudflare, AWS e outras grandes plataformas adotaram o JA4. A suíte JA4+ completa também inclui JA4S (fingerprinting de servidor), JA4H (fingerprinting de cliente HTTP), JA4X (fingerprinting de certificado X.509) e JA4SSH (fingerprinting de SSH). A especificação e as ferramentas estão disponíveis em [github.com/FoxIO-LLC/ja4](https://github.com/FoxIO-LLC/ja4).

### JA3S (fingerprinting de servidor)

O JA3S aplica o mesmo conceito à mensagem ServerHello, mas o formato é mais simples porque o servidor seleciona uma única cipher suite em vez de oferecer uma lista. A string do JA3S é `version,cipher,extensions` e seu hash MD5 identifica a implementação TLS do servidor. Emparelhar o JA3 (ou JA4) com o JA3S cria um fingerprint bidirecional: um cliente específico conversando com um servidor específico produz um par JA3+JA3S previsível, que é mais distintivo do que qualquer um dos fingerprints isolados.

### Como os proxies interagem com os fingerprints TLS

O tipo de proxy determina se o fingerprint TLS é preservado. Proxies SOCKS5 e túneis HTTP CONNECT retransmitem o fluxo TCP sem terminar o TLS, então o servidor alvo vê o fingerprint TLS do cliente original inalterado. Essa é a principal vantagem desses tipos de proxy para a consistência do fingerprint.

Proxies MITM (que terminam o TLS e reestabelecem uma nova conexão com o alvo) substituem o fingerprint TLS do cliente pelo seu próprio. O alvo vê as cipher suites e extensões do software de proxy, não as do navegador. Se o proxy usa uma biblioteca TLS padrão como OpenSSL ou BoringSSL com configurações padrão, o fingerprint não vai casar com nenhum navegador conhecido, o que é por si só um sinal de detecção.

É por isso que a abordagem do Pydoll de usar `--proxy-server` (que cria um túnel CONNECT, preservando o fingerprint TLS do navegador) é preferível a configurações externas de proxy MITM para automação stealth.

## HTTP/2 fingerprinting

As conexões HTTP/2 expõem um conjunto separado de sinais de fingerprinting que são distintos do TLS. O primeiro frame enviado pelo cliente é um frame SETTINGS contendo parâmetros como `HEADER_TABLE_SIZE`, `ENABLE_PUSH`, `MAX_CONCURRENT_STREAMS`, `INITIAL_WINDOW_SIZE`, `MAX_FRAME_SIZE` e `MAX_HEADER_LIST_SIZE`. Cada navegador usa valores padrão diferentes e inclui subconjuntos diferentes desses parâmetros.

Além do SETTINGS, o tamanho do frame WINDOW_UPDATE, a prioridade/peso do stream inicial e a ordem dos pseudo-cabeçalhos HTTP/2 (`:method`, `:authority`, `:scheme`, `:path`) variam entre implementações. Chrome, Firefox e Safari produzem, cada um, uma combinação distintiva desses valores.

A Akamai publicou a pesquisa fundamental sobre HTTP/2 fingerprinting na Black Hat Europe 2017. O formato de fingerprint deles concatena os valores de SETTINGS, o tamanho do WINDOW_UPDATE, os frames PRIORITY e a ordem dos pseudo-cabeçalhos. A suíte JA4+ inclui o `JA4H` para fingerprinting no nível HTTP, cobrindo a ordem e os valores dos cabeçalhos.

O HTTP/2 fingerprinting é particularmente eficaz contra ferramentas de automação, porque muitos frameworks de bot e bibliotecas HTTP implementam suas próprias pilhas HTTP/2 com parâmetros padrão que não casam com nenhum navegador real. Mesmo quando uma ferramenta forja corretamente o fingerprint TLS (usando curl-impersonate ou similar), o seu frame SETTINGS de HTTP/2 pode a entregar.

Você pode checar o seu fingerprint HTTP/2 em [browserleaks.com/http2](https://browserleaks.com/http2). Como o Pydoll controla uma instância real do Chrome via CDP, o fingerprint HTTP/2 é sempre autêntico, o que é uma vantagem inerente sobre ferramentas que constroem requisições HTTP programaticamente.

## Implicações para a automação de navegador

O ponto prático para a automação com o Pydoll é que o network fingerprinting é uma área em que controlar um navegador real é uma vantagem. A pilha TCP/IP do Chrome, a sua implementação TLS (BoringSSL) e a sua pilha HTTP/2 produzem fingerprints autênticos por padrão. O principal risco é a divergência ambiental: rodar o Chrome num servidor Linux enquanto o User-Agent alega Windows cria uma inconsistência no fingerprint TCP/IP (TTL 64 em vez de 128, ordem das opções TCP do Linux em vez da do Windows).

Para configurações baseadas em proxy, o fluxo do fingerprint é: a pilha TCP/IP da sua máquina gera a conexão com o proxy (que o operador do proxy pode ver, mas o alvo não), e a pilha TCP/IP do proxy gera a conexão com o alvo. O alvo vê o TTL e as opções TCP do servidor de proxy. Se o proxy roda Linux (como a maioria roda), o fingerprint TCP vai indicar Linux independentemente do User-Agent. Esse é um sinal de detecção bem conhecido que os proxies residenciais mitigam parcialmente (o endpoint do proxy é a máquina de um usuário real, então o seu fingerprint TCP é plausível), mas que os proxies de datacenter não conseguem.

Os fingerprints TLS e HTTP/2, por outro lado, passam pelos túneis SOCKS5 e CONNECT sem modificação. Esses são os fingerprints do navegador, não os do proxy. Então, com o Pydoll através de um túnel CONNECT, o alvo vê fingerprints TLS e HTTP/2 autênticos do Chrome emparelhados com o fingerprint TCP/IP do proxy. Essa combinação é consistente com um usuário real navegando através de uma VPN ou proxy corporativo, o que é um padrão comum e legítimo.

## Relacionado

- [Browser fingerprinting](browser-fingerprinting.md): sinais de canvas, WebGL e navigator.
- [Behavioral fingerprinting](behavioral-fingerprinting.md): análise de mouse, teclado e timing.
- [Network fundamentals](../network/network-fundamentals.md): como TCP, TLS e HTTP realmente funcionam.
- [Evasion techniques](../../stealth/evasion-techniques.md): o que o Pydoll faz a respeito desses sinais, na prática.
- [Fingerprint injection](../../stealth/fingerprint-injection.md): aplicar uma identidade coerente entre as camadas.

## Referências

- Salesforce Engineering: TLS Fingerprinting with JA3 and JA3S - https://engineering.salesforce.com/tls-fingerprinting-with-ja3-and-ja3s-247362855967/
- FoxIO JA4+ Network Fingerprinting - https://github.com/FoxIO-LLC/ja4
- Cloudflare: JA4 Signals - https://blog.cloudflare.com/ja4-signals/
- Akamai: Passive Fingerprinting of HTTP/2 Clients (Black Hat EU 2017) - https://blackhat.com/docs/eu-17/materials/eu-17-Shuster-Passive-Fingerprinting-Of-HTTP2-Clients-wp.pdf
- p0f v3: Passive OS Fingerprinting - https://lcamtuf.coredump.cx/p0f3/
- RFC 8446: TLS 1.3 - https://datatracker.ietf.org/doc/html/rfc8446
- RFC 8701: GREASE for TLS - https://datatracker.ietf.org/doc/html/rfc8701
- RFC 6528: Defending against Sequence Number Attacks - https://datatracker.ietf.org/doc/html/rfc6528
- BrowserLeaks HTTP/2 Fingerprint - https://browserleaks.com/http2
- Stamus Networks: JA3 Fingerprints Fade as Browsers Embrace Extension Randomization - https://www.stamus-networks.com/blog/ja3-fingerprints-fade-browsers-embrace-tls-extension-randomization
