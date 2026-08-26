# O managed challenge do Cloudflare

O managed challenge do Cloudflare, o interstício "Just a moment…", é o teste mais rigoroso de um fingerprint no mundo real. Ele correlaciona todas as camadas de uma vez e decide no próprio servidor, então pega contradições que um bot score de página única deixa passar. Esta página é um estudo de caso completo: a matriz de aprovação/bloqueio, por que cada incompatibilidade é pega, e o que é preciso para passar no challenge em headless, onde a identidade tem que permanecer coerente até dentro do iframe cross-origin em que o challenge roda.

Ela aplica o fingerprinting de [rede](network-fingerprinting.md) e de [navegador](browser-fingerprinting.md) e [os limites do spoofing](spoofing-limits.md) a um alvo ao vivo. Leia aqueles para os mecanismos; leia este para como eles se combinam num único veredito do lado do servidor, e como fazer todas as camadas concordarem.

<p align="center">
  <img src="/docs/resources/images/cloudflare-headless-bypass.gif" alt="Chrome headless passando por um managed challenge do Cloudflare, do interstício até a página liberada" width="760" />
</p>
<p align="center"><sub>Chrome headless passando por um managed challenge ao vivo, gravado com o CDP screencast (<code>Page.startScreencast</code>). O interstício está em português porque o locale do perfil combina com o IP de saída brasileiro, a mesma coerência que o challenge verifica.</sub></p>

<iframe scrolling="no" src="/docs/resources/visuals/cloudflare-matrix.html" aria-label="A coherent headful identity passes Cloudflare; flip any single field (IP, host OS, Chrome version, headless) and a different layer catches it, so only coherence of everything passes" style="width: 100%; height: 760px; border: 0;" loading="lazy"></iframe>

## O teste controlado

Uma máquina, um binário do Chrome 151, um IP residencial. As únicas coisas que mudam entre as execuções são o perfil e a flag de headless; [`apply_fingerprint()`](../../stealth/fingerprint-injection.md) é aplicado antes de navegar.

| Perfil | Modo | Major do Chrome no UA | Resultado |
|---|---|---|---|
| macOS (combina com o host) | headful | 151 (combina com o binário) | passa |
| macOS | headless | 151 | bloqueado |
| macOS | headful | 140 (incompatível) | bloqueado |
| Windows (sistema operacional incompatível) | headful | 151 | bloqueado |
| Windows | headless | 151 | bloqueado |

Apenas a execução totalmente consistente e em headful passa *neste perfil básico*, e cada linha incompatível é pega por uma camada diferente, cobertas abaixo. A linha do headless é a que se deve ler com atenção: ela não é um muro intransponível. Este perfil muda apenas o sistema operacional, a versão e a flag de headless, então deixa de fora as duas coisas que uma passagem em headless também precisa, a identidade dentro do iframe cross-origin do challenge e um locale que combine com o IP de saída. Adicione essas e clique no Turnstile, e a execução headless com o sistema operacional compatível também passa no challenge (veja [O que de fato funciona](#what-actually-works)). As linhas do Windows são diferentes: uma incompatibilidade de sistema operacional não é forjável, então elas falham em qualquer modo.

## O sistema operacional tem que combinar com o host {#the-os-must-match-the-host}

Um perfil de Windows num Mac é bloqueado até em headful, porque o sistema operacional vaza através de caminhos que o `apply_fingerprint()` não consegue tocar:

- **Fontes.** A lista de fontes do perfil é um valor JavaScript, mas o `measureText` e o dimensionamento de elementos renderizam através do motor de fontes real do SO. Um navegador "Windows" sem Segoe UI ou Calibri, e com Helvetica Neue presente, é um Mac.
- **Rasterização.** O texto de canvas e WebGL desenha através do CoreText no macOS, do DirectWrite no Windows, do FreeType no Linux. Os pixels diferem, então o hash entrega o sistema operacional real. Este é o [piso intransponível](spoofing-limits.md): um sinal renderizado que nenhum override alcança.
- **A stack TCP/IP.** O kernel define o TTL inicial (64 no macOS e no Linux, 128 no Windows) e outras opções que o navegador não pode mudar. O Cloudflare as lê passivamente na borda (veja [Fingerprinting de rede](network-fingerprinting.md)).

O vazamento de fontes do lado do cliente já basta por si só; o sinal TCP é o piso por baixo dele.

## A versão do Chrome tem que combinar com o binário {#the-chrome-version-must-match-the-binary}

Um User-Agent que alega Chrome 140 num binário 151 é bloqueado, porque a versão vaza através do motor, não apenas da string.

Declare uma versão ainda mais antiga, o Chrome 110, e a superfície de recursos ainda responde como 151: `Promise.withResolvers` (adicionado no Chrome 119), `Array.fromAsync` (121) e `Uint8Array.prototype.toBase64` (140+) estão todos presentes. Uma API mais nova do que a versão que você alega expõe a mentira. O motor a vaza de um segundo jeito: a precisão de `Math` até o último bit, o texto das mensagens de erro e o suporte de sintaxe mudam entre versões do V8, então duas builds do Chrome produzem hashes de fingerprint de `Math` diferentes. A string é forjável; o motor por trás dela não.

Essas duas linhas são [os limites do spoofing](spoofing-limits.md) na prática. A terceira, o headless, é diferente, e é o assunto do resto desta página.

## Anatomia do bloqueio do headless

Sob um perfil que combina, o headful e o headless parecem idênticos entre as ferramentas e sinais abaixo. Esse é o enigma: o challenge passa um e bloqueia o outro, embora estes leiam igual. Tudo nesta tabela foi medido diretamente, idêntico entre as duas execuções:

| Sinal | headful vs headless |
|---|---|
| Relatório completo do CreepJS | idêntico byte a byte (mesmos hashes, "0% headless") |
| Hashes de canvas / WebGL / áudio | idênticos (GPU real; o SwiftShader não é usado no macOS) |
| Renderer do WebGL, adapter do WebGPU | idênticos (Apple Metal) |
| Widevine / EME, codecs (H.264 / AAC / HEVC) | idênticos |
| `navigator.*`, plugins, permissions, `isUVPAA` | idênticos |
| 40+ sinais planos de window / navigator | idênticos |

`navigator.webdriver` é false, não há `--enable-automation`, e o Pydoll nunca chama `Runtime.enable`, então as denúncias clássicas de CDP também estão ausentes. O que quer que separe as duas execuções está abaixo da camada que essas ferramentas leem.

### Os vazamentos plausíveis, e por que são becos sem saída

Dois sinais de fato diferem. Vale registrar ambos para que você não corra atrás deles:

| Sinal | headful | headless | correção tentada | ainda bloqueado? |
|---|---|---|---|---|
| `matchMedia('(color-gamut: p3)')` | true | false | `setEmulatedMedia` / `--force-color-profile` | sim |
| `matchMedia('(dynamic-range: high)')` | true | false | `setEmulatedMedia` | sim |
| Intervalo de `requestAnimationFrame` | 8.3ms (120Hz) | 16.7ms (60Hz) | `--disable-gpu-vsync` (sem efeito) | sim |

O par de media de display é real: um display virtual headless reporta sRGB e SDR. Forçar ambos a combinar não muda nada. A cadência de frames é a assinatura de "nenhum display real": sem nenhuma superfície para apresentar, o compositor do Chrome recorre a uma fonte sintética de 60Hz (`BeginFrameArgs::DefaultInterval()`, um sexagésimo de segundo), enquanto um Mac com ProMotion roda a 120Hz. Mas 60Hz é o que a maioria das máquinas reais reporta, então a cadência sozinha não pode ser o discriminador, e ela não pode ser elevada sem um display. Os três são consequências da mesma raiz, nenhuma superfície apresentada, e nenhum é o sinal decisivo.

### Fazendo engenharia reversa do que o challenge lê

Para parar de adivinhar, instrumente o que o challenge de fato toca. Registre uma sonda com `Page.addScriptToEvaluateOnNewDocument` (ela roda antes do código do próprio challenge) que envolve `matchMedia`, `requestAnimationFrame`, `performance.now`, canvas, o `getParameter` do WebGL e os getters suspeitos de `screen` / `navigator`, e registre todo acesso.

Na página do challenge a thread principal lê quase nada: um `matchMedia('(prefers-color-scheme: dark)')` e um punhado de `Date.now`. O trabalho acontece em outro lugar. Dar hook em `URL.createObjectURL` o pega: o challenge gera dois Web Workers a partir de blobs, e a fonte deles é um pequeno bootstrap.

```js
var _p = self.trustedTypes.createPolicy('Kssz2', { createScript: s => s });
onmessage = e => e.isTrusted && e.origin === '' && e.source === null
                 && eval(_p ? _p.createScript(e.data) : e.data);
```

O worker é um sumidouro de eval: o código de detecção real é enviado a ele a partir da thread principal e rodado dentro do worker, fora da página instrumentável. Para lê-lo, anexe uma sessão CDP ao target do worker (`Target.setAutoAttach` com `waitForDebuggerOnStart`), habilite o `Debugger`, e capture todo script parseado com `Debugger.scriptParsed` e `Debugger.getScriptSource`; ou dê hook em `self.eval` no worker antes de retomá-lo.

Fazer isso revela a reviravolta. No caminho headless bloqueado o worker nunca é alimentado. Ele parseia apenas o próprio bootstrap e fica ocioso (nenhuma mensagem de entrada, nenhum payload passado por eval). O Cloudflare não envia o coletor de segundo estágio uma vez que a telemetria de primeiro estágio já reprovou o cliente. O worker é o estágio depois do veredito, não o detector. É por isso que dar hook no `postMessage` da thread principal não pega nada, e por que o challenge se lê como uma caixa-preta para a instrumentação JavaScript comum.

### O vazamento real do cliente: geometria do iframe cross-origin

O challenge renderiza dentro de um iframe cross-origin em `challenges.cloudflare.com`, um out-of-process iframe (OOPIF) com o próprio processo de renderização e a própria sessão CDP. Scripts injetados na página e o `setDeviceMetricsOverride` nunca o alcançam, que é a camada que toda sonda anterior deixou passar. Anexe à própria sessão do OOPIF e leia o `window.screen` dele diretamente, e o vazamento está ali:

| Leitura dentro do OOPIF | headless | headful |
|---|---|---|
| `screen.width × height` | 800 × 600 | 1440 × 900 |
| `screen.availTop` | 0 | 25 |
| `devicePixelRatio` | 1 | 2 |

800x600 com `availTop` 0 é a tela virtual headless codificada do Chrome: nenhum gerenciador de janelas, impossível para o Mac alegado, e em contradição direta com a página de topo, que reporta o 1440x900 do perfil. O `setDeviceMetricsOverride` corrigiu a página de topo mas tem escopo de sessão; o iframe nunca o viu.

O Pydoll fecha isso com `Emulation.updateScreen` na tela virtual global do navegador, que todo frame lê, OOPIFs incluídos (veja [Injeção de fingerprint → Modo headless](../../stealth/fingerprint-injection.md#headless-mode)). Depois dele, o iframe reporta o mesmo 1440x900 / `availTop 25` / dpr 2 que a página. O único porém é que a tela virtual aceita apenas um `devicePixelRatio` inteiro, então um dpr fracionário é arredondado para o iframe.

A geometria é apenas o primeiro sinal que o iframe expõe. Seu `navigator`, WebGL, fuso horário e idiomas também vêm do próprio processo dele, então o `updateScreen` sozinho os deixa lendo a máquina real. `apply_fingerprint(..., cross_origin_iframes=True)`, o padrão, replica a identidade completa na própria sessão do iframe, então o OOPIF combina com a página em todos os sinais, não apenas na tela (veja [Workers e iframes cross-origin](execution-realms.md)).

### O veredito é um único score aditivo do lado do servidor

Você não consegue ler o score a partir do cliente. O script de primeiro estágio na página do challenge é um interpretador de VM baseado em tabela de strings de ~226KB: sua config vive em `_cf_chl_opt`, ele carrega um decodificador XOR (`o[i] = k[i] ^ s.charCodeAt(i % s.length)`), blobs base64, e scripts canário `honk` preenchidos com espaços em branco. Ele coleta sua telemetria, a criptografa e a envia via POST para `/cdn-cgi/challenge-platform/h/b/fo/<numbers>:<ray>/<token>`; o Cloudflare a pontua no lado do servidor e reentrega o interstício com um Ray ID novo em caso de falha. O payload é opaco, então nenhuma entrada isolada pode ser separada a partir do cliente sem quebrar a criptografia.

O score é aditivo, não um único portão. A reputação do IP, a coerência do fingerprint entre camadas e um termo de display/apresentação alimentam todos ele, e um cliente suspeito é *escalado* para um Turnstile interativo em vez de ser bloqueado de imediato. Duas consequências decorrem disso. Um navegador headless sem display emite um sinal de apresentação mais fraco do que um com uma superfície real, então num IP marginal esse termo é o que empurra o score para além do limite, e ali um display real (headful, ou headful sob o Xvfb num servidor) é a correção. Mas quando o resto do score já é favorável, um fingerprint tornado coerente *e combinado com o IP*, mais o clique no Turnstile, passa nele, incluindo em headless.

Então as alavancas que levam um cliente headless para baixo do limite são cobrir o iframe cross-origin do challenge (`cross_origin_iframes`, ligado por padrão) e combinar o fuso horário, o locale e a geolocalização do perfil com o IP de saída. A identidade do iframe cross-origin é a decisiva: deixada na máquina real, ela contradiz a página e o challenge bloqueia; coberta, com o clique no Turnstile, o headless passa.

!!! note "Ainda depende do IP"
    Um cliente headless coerente passa no challenge num IP residencial limpo; um IP sinalizado é desafiado ou bloqueado por mais coerente que o navegador seja. A coerência do fingerprint remove as contradições que você consegue corrigir. Ela não limpa a reputação de um IP ruim.

## O que de fato funciona {#what-actually-works}

- **Combine com o host e o binário.** O sistema operacional igual ao do host, a major do Chrome igual à major do binário.
- **Combine locale, fuso horário e geolocalização com o IP de saída.** O challenge cruza `Accept-Language` e o fuso horário contra o país do IP (veja [Incompatibilidade de locale/IP](../../stealth/fingerprint-injection.md#case-study-a-locale-mismatch-triggering-googles-captcha)). Num deployment real, essa costuma ser a única alavanca entre bloquear e passar.
- **Cubra o iframe cross-origin.** O challenge lê o fingerprint dentro do próprio frame dele em `challenges.cloudflare.com`; `apply_fingerprint(..., cross_origin_iframes=True)`, o padrão, replica a identidade ali também. Deixado na máquina real, o iframe contradiz a página e o challenge bloqueia; coberto, é o termo que permite que um cliente headless passe.
- **Clique no Turnstile.** O managed challenge agora serve um Turnstile interativo, então a caixa de seleção tem que ser clicada. Use [`expect_and_bypass_cloudflare_captcha()`](../../stealth/captcha-bypass.md); esperar por uma liberação automática deixa você bloqueado.
- **Recorra a um display real num IP marginal.** Quando o IP não é limpo o bastante para um cliente headless coerente passar, rode em headful ou em headful sob o Xvfb num servidor, para que o termo de apresentação pare de contar contra você.
- **Trate a injeção como necessária, não sempre suficiente.** Ela remove as contradições que você consegue corrigir; a reputação do IP não é uma delas.

## Reproduzindo isto

A passagem de engenharia reversa acima é um método que você pode reexecutar em qualquer challenge:

- **A/B em uma variável.** Mude apenas a flag de headless, ou um campo do perfil, entre as execuções e compare o resultado. Atribua um bloqueio a um sinal em vez de adivinhar.
- **Instrumente o cliente, em todo lugar em que ele roda.** O `Page.addScriptToEvaluateOnNewDocument` antes da navegação registra o acesso a APIs da thread principal; hooks em `URL.createObjectURL` pegam os workers de blob; uma sessão CDP por worker e por OOPIF alcança o código que os scripts injetados na página não alcançam, já que nenhum dos dois os herda.
- **Leia o OOPIF na própria sessão dele.** O challenge vive num iframe cross-origin; o `window.screen` dele e toda outra leitura são visíveis apenas através do próprio target dele.
- **Meça, não presuma.** [Auditando um fingerprint](auditing.md) cobre o método de ler-dois-caminhos que transforma "está bloqueado" em "este campo exato vaza".

## Relacionado

- [Os limites do spoofing](spoofing-limits.md): o que um spoof consegue e não consegue mover.
- [Fingerprinting de rede](network-fingerprinting.md): as camadas TCP e TLS que o Cloudflare lê na borda.
- [Fingerprinting de navegador](browser-fingerprinting.md): os sinais de fontes, canvas e GPU que carregam o sistema operacional.
- [Auditando um fingerprint](auditing.md): meça quais dos seus sinais vazam antes de apontá-los para um challenge.
- [Injeção de fingerprint](../../stealth/fingerprint-injection.md): aplicando um perfil coerente.
