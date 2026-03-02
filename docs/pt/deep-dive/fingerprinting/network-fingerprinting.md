# Network Fingerprinting

O network fingerprinting identifica clientes analisando características da pilha TCP/IP, handshake TLS e conexão HTTP/2. Esses sinais são definidos pelo kernel do sistema operacional e pela biblioteca TLS, não pelo ambiente JavaScript do navegador, o que os torna mais difíceis de falsificar que fingerprints de nível de navegador. Um proxy ou VPN muda seu endereço IP mas não altera seu tamanho de janela TCP, sua lista de cipher suites TLS ou seu frame HTTP/2 SETTINGS. Sistemas de detecção exploram essa lacuna.

!!! info "Navegação do Módulo"
    - [Browser Fingerprinting](./browser-fingerprinting.md): Canvas, WebGL, AudioContext
    - [Técnicas de Evasão](./evasion-techniques.md): Contramedidas multi-camada

    Para fundamentos de protocolo, veja [Fundamentos de Rede](../network/network-fundamentals.md). Para contexto de detecção de proxy, veja [Detecção de Proxy](../network/proxy-detection.md).

## TCP/IP Fingerprinting

Cada sistema operacional implementa a pilha TCP/IP de forma diferente. O pacote SYN que inicia uma conexão TCP carrega informação suficiente para identificar o SO com alta confiança: o TTL inicial, o tamanho da janela TCP, o Maximum Segment Size e a ordem e seleção de opções TCP. Nenhum desses valores é controlado pelo navegador. Eles vêm do kernel.

### TTL (Time To Live)

O TTL inicial é um dos identificadores de SO mais simples. Linux e macOS definem como 64, Windows define como 128, e dispositivos de rede (roteadores, firewalls) tipicamente usam 255. Cada salto de roteador decrementa o TTL em um, então um pacote chegando com TTL 118 provavelmente começou em 128 (Windows) e cruzou 10 saltos.

O valor de fingerprinting do TTL vem da referência cruzada com o User-Agent. Se o navegador alega ser Chrome no Windows mas o pacote chega com TTL próximo de 64, a conexão está ou sendo proxy através de um servidor Linux ou o User-Agent está falsificado. Sistemas de detecção arredondam o TTL observado para cima até o valor inicial conhecido mais próximo (64, 128, 255) e comparam contra o SO declarado.

Quando o tráfego flui através de um proxy, o TTL reinicia porque o kernel do proxy gera uma nova conexão TCP para o destino. O destino vê o TTL do proxy, não o seu. É por isso que incompatibilidades de TTL são um sinal de detecção de proxy: o User-Agent diz Windows (TTL 128) mas o fingerprint TCP mostra Linux (TTL 64).

### Tamanho da Janela TCP e Escalonamento

O tamanho inicial da janela TCP no pacote SYN varia por SO e versão do kernel. Kernels Linux modernos (3.x e posteriores) tipicamente enviam uma janela inicial de 29200 bytes, que é `20 * MSS` onde MSS é 1460 para Ethernet padrão. Alguns kernels mais novos (5.x, 6.x) podem usar 64240 dependendo da configuração e ajustes de `initcwnd`. Windows 10 e 11 tipicamente enviam 65535 com escalonamento de janela habilitado, embora o valor exato dependa da configuração de auto-tuning e nível de patch. macOS também usa 65535 como padrão.

O fator de escala de janela (uma opção TCP) multiplica o campo de tamanho de janela de 16 bits para suportar janelas de recebimento maiores. Linux comumente usa fator de escala 7 (permitindo janelas de até 8MB), enquanto Windows frequentemente usa 8. Combinado com o tamanho base da janela, o fator de escala cria um fingerprint mais granular do que qualquer valor isolado.

### Ordem de Opções TCP

A seleção e ordenação de opções TCP no pacote SYN é altamente distintiva. Cada SO organiza as opções em uma ordem fixa e específica por versão que o kernel não expõe como parâmetro configurável. Linux envia `MSS, SACK_PERM, TIMESTAMP, NOP, WSCALE`. Windows envia `MSS, NOP, WSCALE, NOP, NOP, SACK_PERM` e notavelmente omite a opção TIMESTAMP nas configurações padrão. macOS envia `MSS, NOP, WSCALE, NOP, NOP, TIMESTAMP, SACK_PERM`.

A presença ou ausência de opções específicas importa tanto quanto a ordem. Windows historicamente omitiu timestamps TCP, que Linux e macOS incluem por padrão. SACK (Selective Acknowledgment) é suportado por todos os sistemas modernos, mas sistemas mais antigos ou embarcados podem não anunciá-lo. A combinação de quais opções aparecem e em que ordem cria uma assinatura que ferramentas como p0f comparam contra um banco de dados de fingerprints de SO conhecidos.

### p0f

[p0f](https://lcamtuf.coredump.cx/p0f3/) é a ferramenta padrão para fingerprinting TCP/IP passivo. Ele observa tráfego sem gerar nenhum pacote, analisando pacotes SYN e SYN+ACK contra um banco de dados de assinaturas. Seu formato de assinatura codifica os campos chave de fingerprinting:

```
version:ittl:olen:mss:wsize,scale:olayout:quirks:pclass
```

O `ittl` é o TTL inicial inferido, `mss` é o Maximum Segment Size, `wsize,scale` é o tamanho da janela (que pode ser absoluto, ou relativo ao MSS como `mss*20`), e `olayout` é o layout de opções TCP usando nomes abreviados (`mss`, `nop`, `ws`, `sok`, `sack`, `ts`, `eol+N`). O campo `quirks` captura comportamentos incomuns como a flag Don't Fragment (`df`) ou IP ID não-zero em pacotes DF (`id+`).

Uma assinatura típica de Linux 4.x+ no p0f se parece com `4:64:0:*:mss*20,7:mss,sok,ts,nop,ws:df,id+:0`. Uma assinatura de Windows 10 pode parecer `4:128:0:*:65535,8:mss,nop,ws,nop,nop,sok:df,id+:0`. Serviços anti-bot mantêm bancos de dados similares internamente, comparando conexões de entrada contra perfis de SO conhecidos e sinalizando incompatibilidades com o User-Agent declarado.

## TLS Fingerprinting

A mensagem TLS ClientHello é transmitida antes da criptografia ser estabelecida, então é visível para qualquer observador no caminho de rede. Ela contém a versão TLS, cipher suites suportadas, extensões TLS, curvas elípticas suportadas (named groups) e formatos de ponto EC. Cada navegador e biblioteca TLS produz uma combinação característica desses campos.

### JA3

JA3, desenvolvido na Salesforce por John Althouse, Jeff Atkinson e Josh Atkins, foi o primeiro método de fingerprinting TLS amplamente adotado. Ele concatena cinco campos do ClientHello (versão TLS, cipher suites, extensões, curvas elípticas, formatos de ponto EC), junta valores dentro de cada campo com hífens, separa os cinco campos com vírgulas e tira o hash MD5 da string resultante.

```
String JA3: 771,4865-4866-4867-49195-49199-49196-49200-52393-52392,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0
Hash JA3:   cd08e31494b9531f560d64c695473da9
```

Uma sutileza: o campo "versão TLS" no JA3 usa `ClientHello.legacy_version`, não a extensão `supported_versions`. Como TLS 1.3 (RFC 8446) requer que clientes definam `legacy_version` como `0x0303` (TLS 1.2) para compatibilidade retroativa, o campo de versão JA3 é quase sempre `771` para clientes modernos, mesmo quando suportam TLS 1.3. A negociação real de TLS 1.3 acontece através da extensão 43 (`supported_versions`), mas o JA3 usa o campo do cabeçalho.

O JA3 deve filtrar valores GREASE antes do hashing. GREASE (RFC 8701) é um mecanismo onde navegadores inserem valores reservados selecionados aleatoriamente em cipher suites, extensões e outros campos para prevenir ossificação de protocolo. Os valores GREASE válidos são `0x0a0a`, `0x1a1a`, `0x2a2a` e assim por diante até `0xfafa`. Cada valor tem dois bytes idênticos onde o nibble inferior de cada byte é `0x0a`. Um filtro GREASE correto verifica ambas as condições:

```python
def is_grease(value: int) -> bool:
    return (value & 0x0f0f) == 0x0a0a and (value >> 8) == (value & 0xff)
```

!!! warning "Limitações do JA3 com Navegadores Modernos"
    Desde o Chrome 110 (janeiro 2023) e Firefox 114, navegadores randomizam a ordem das extensões TLS em cada conexão. Isso significa que o mesmo navegador produz hashes JA3 diferentes em cada conexão, tornando o JA3 efetivamente inútil para identificar navegadores modernos. O JA3 permanece útil para fingerprinting de clientes não-navegador (Python `requests`, `curl`, bots personalizados) que não implementam randomização de extensões.

### JA4

JA4 é o sucessor do JA3, desenvolvido pelo mesmo autor principal (John Althouse) na FoxIO. Foi projetado especificamente para sobreviver à randomização de extensões TLS ordenando extensões e cipher suites antes do hashing. O formato consiste em três seções separadas por underscores: `a_b_c`.

Seção `a` é uma string legível de metadados: o protocolo (`t` para TCP, `q` para QUIC), a versão TLS (`12` ou `13`), se SNI está presente (`d` para domínio, `i` para IP), o número de cipher suites (dois dígitos), o número de extensões (dois dígitos) e o primeiro e último valor ALPN (`h2` para HTTP/2, `00` se nenhum). Por exemplo, `t13d1516h2` significa TCP TLS 1.3 com SNI, 15 cipher suites, 16 extensões e HTTP/2 ALPN.

Seção `b` é um hash SHA-256 truncado das cipher suites ordenadas. Seção `c` é um hash SHA-256 truncado das extensões ordenadas concatenadas com os algoritmos de assinatura. Como ambas as listas são ordenadas antes do hashing, a randomização de extensões não afeta a saída.

Cloudflare, AWS e outras plataformas principais adotaram o JA4. A suíte completa JA4+ também inclui JA4S (fingerprinting de servidor), JA4H (fingerprinting de cliente HTTP), JA4X (fingerprinting de certificado X.509) e JA4SSH (fingerprinting SSH). A especificação e ferramentas estão disponíveis em [github.com/FoxIO-LLC/ja4](https://github.com/FoxIO-LLC/ja4).

### JA3S (Fingerprinting de Servidor)

JA3S aplica o mesmo conceito à mensagem ServerHello, mas o formato é mais simples porque o servidor seleciona uma única cipher suite em vez de oferecer uma lista. A string JA3S é `version,cipher,extensions` e seu hash MD5 identifica a implementação TLS do servidor. Parear JA3 (ou JA4) com JA3S cria um fingerprint bidirecional: um cliente específico conversando com um servidor específico produz um par JA3+JA3S previsível, que é mais distintivo do que qualquer fingerprint isolado.

### Como Proxies Interagem com Fingerprints TLS

O tipo de proxy determina se o fingerprint TLS é preservado. Proxies SOCKS5 e túneis HTTP CONNECT retransmitem o stream TCP sem encerrar o TLS, então o servidor destino vê o fingerprint TLS original do cliente inalterado. Esta é a principal vantagem desses tipos de proxy para consistência de fingerprint.

Proxies MITM (que encerram o TLS e reestabelecem uma nova conexão para o destino) substituem o fingerprint TLS do cliente pelo seu próprio. O destino vê as cipher suites e extensões do software proxy, não as do navegador. Se o proxy usa uma biblioteca TLS padrão como OpenSSL ou BoringSSL com configurações padrão, o fingerprint não corresponderá a nenhum navegador conhecido, o que é em si um sinal de detecção.

É por isso que a abordagem do Pydoll de usar `--proxy-server` (que cria um túnel CONNECT, preservando o fingerprint TLS do navegador) é preferível a configurações de proxy MITM externo para automação stealth.

## HTTP/2 Fingerprinting

Conexões HTTP/2 expõem um conjunto separado de sinais de fingerprinting distintos do TLS. O primeiro frame enviado pelo cliente é um frame SETTINGS contendo parâmetros como `HEADER_TABLE_SIZE`, `ENABLE_PUSH`, `MAX_CONCURRENT_STREAMS`, `INITIAL_WINDOW_SIZE`, `MAX_FRAME_SIZE` e `MAX_HEADER_LIST_SIZE`. Cada navegador usa valores padrão diferentes e inclui subconjuntos diferentes desses parâmetros.

Além do SETTINGS, o tamanho do frame WINDOW_UPDATE, a prioridade/peso do stream inicial e a ordem dos pseudo-cabeçalhos HTTP/2 (`:method`, `:authority`, `:scheme`, `:path`) variam entre implementações. Chrome, Firefox e Safari cada um produz uma combinação distintiva desses valores.

A Akamai publicou a pesquisa fundamental sobre fingerprinting HTTP/2 no Black Hat Europe 2017. Seu formato de fingerprint concatena os valores SETTINGS, tamanho do WINDOW_UPDATE, frames PRIORITY e ordem dos pseudo-cabeçalhos. A suíte JA4+ inclui `JA4H` para fingerprinting em nível HTTP, cobrindo ordem e valores de cabeçalhos.

O fingerprinting HTTP/2 é particularmente eficaz contra ferramentas de automação porque muitos frameworks de bot e bibliotecas HTTP implementam suas próprias pilhas HTTP/2 com parâmetros padrão que não correspondem a nenhum navegador real. Mesmo quando uma ferramenta falsifica corretamente o fingerprint TLS (usando curl-impersonate ou similar), seu frame HTTP/2 SETTINGS pode traí-la.

Você pode verificar seu fingerprint HTTP/2 em [browserleaks.com/http2](https://browserleaks.com/http2). Como o Pydoll controla uma instância real do Chrome via CDP, o fingerprint HTTP/2 é sempre autêntico, o que é uma vantagem inerente sobre ferramentas que constroem requisições HTTP programaticamente.

## Implicações para Automação de Navegador

A conclusão prática para automação com o Pydoll é que o network fingerprinting é uma área onde controlar um navegador real fornece uma vantagem significativa. A pilha TCP/IP do Chrome, implementação TLS (BoringSSL) e pilha HTTP/2 produzem fingerprints autênticos por padrão. O principal risco é incompatibilidade ambiental: executar o Chrome em um servidor Linux enquanto o User-Agent alega Windows cria uma inconsistência de fingerprint TCP/IP (TTL 64 ao invés de 128, ordem de opções TCP do Linux ao invés do Windows).

Para configurações baseadas em proxy, o fluxo de fingerprint é: a pilha TCP/IP da sua máquina gera a conexão para o proxy (que o operador do proxy pode ver mas o destino não), e a pilha TCP/IP do proxy gera a conexão para o destino. O destino vê o TTL e opções TCP do servidor proxy. Se o proxy roda Linux (como a maioria faz), o fingerprint TCP indicará Linux independentemente do User-Agent. Este é um sinal de detecção bem conhecido que proxies residenciais mitigam parcialmente (o endpoint do proxy é a máquina de um usuário real, então seu fingerprint TCP é plausível) mas proxies de datacenter não podem.

Os fingerprints TLS e HTTP/2, por outro lado, passam por túneis SOCKS5 e CONNECT sem modificação. Estes são os fingerprints do navegador, não do proxy. Então com o Pydoll através de um túnel CONNECT, o destino vê fingerprints TLS e HTTP/2 autênticos do Chrome pareados com o fingerprint TCP/IP do proxy. Esta combinação é consistente com um usuário real navegando através de uma VPN ou proxy corporativo, que é um padrão comum e legítimo.

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
