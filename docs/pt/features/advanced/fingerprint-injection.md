# Injeção de Fingerprint

O Pydoll pode fazer o navegador **reportar uma identidade diferente e totalmente consistente** com uma única chamada: `tab.apply_fingerprint()`. Ele sobrescreve toda a superfície que os scripts de fingerprinting leem (User-Agent e Client Hints, `navigator`, WebGL, tela, fontes, áudio, fuso horário e locale) e alinha cada camada para que o navegador conte uma história coerente.

!!! warning "Isso é spoofing, não anonimato"
    Um fingerprint esconde *qual* máquina real você é apresentando uma alternativa plausível e autoconsistente. Ele **não** te torna invisível, e não conserta um IP marcado nem uma contradição na camada de rede (veja [Consistência é Tudo](#consistency-is-the-whole-game)). Usado sem cuidado, um fingerprint inconsistente é *mais* detectável do que um navegador intocado.

## Início Rápido

Aplique o fingerprint **antes** de navegar. As sobrescritas em JavaScript são registradas via `Page.addScriptToEvaluateOnNewDocument`, então só têm efeito em documentos carregados após a chamada.

```python
import asyncio

from pydoll.browser.chromium import Chrome

from examples.fingerprints import FINGERPRINTS

async def spoof_fingerprint():
    async with Chrome() as browser:
        tab = await browser.start()

        # Aplique antes da primeira navegação.
        await tab.apply_fingerprint(FINGERPRINTS['windows11_rtx3060_nyc'])

        await tab.go_to('https://abrahamjuliot.github.io/creepjs/')
        print('Fingerprint aplicado.')
        await asyncio.sleep(5)

asyncio.run(spoof_fingerprint())
```

O argumento é um `FingerprintConfig` (um dicionário tipado de `pydoll.protocol.fingerprint.types`) que descreve a identidade. Apenas os campos que você define são sobrescritos; todo o resto mantém o valor real do navegador. Os perfis em `examples/fingerprints.py` são referências completas e internamente consistentes que você pode ler para entender o formato (veja [Traga Seus Próprios Fingerprints](#bring-your-own-fingerprints)).

## O Que é Falsificado, e Como

O Pydoll sobrescreve a identidade por dois mecanismos, e a escolha entre eles é deliberada.

### Via CDP (aplicado nativamente pelo navegador)

Tudo o que o Chrome consegue sobrescrever por conta própria é sobrescrito pelo domínio `Emulation` do DevTools Protocol. Isso é sempre preferível: o navegador aplica a mudança **abaixo do JavaScript**, então o getter que um script de detecção lê continua sendo o nativo genuíno. Não há wrapper JavaScript para inspecionar.

| Sinal | Comando CDP |
|--------|-------------|
| User-Agent, `navigator.platform` / `vendor` / `appVersion`, Client Hints (`Sec-CH-UA*`) | `Emulation.setUserAgentOverride` |
| Fuso horário (`Intl`, `Date`) | `Emulation.setTimezoneOverride` |
| Geolocalização | `Emulation.setGeolocationOverride` |
| Tamanho da tela, `devicePixelRatio`, viewport, orientação | `Emulation.setDeviceMetricsOverride` |
| Locale (formatação `Intl`) | `Emulation.setLocaleOverride` |
| `navigator.hardwareConcurrency` | `Emulation.setHardwareConcurrencyOverride` |

!!! tip "Por que o nativo vence o JavaScript"
    Definir `navigator.hardwareConcurrency` com um getter JavaScript deixa uma falsificação que um script consegue pegar (veja abaixo). Defini-lo com `Emulation.setHardwareConcurrencyOverride` muda o valor enquanto o getter permanece nativo byte a byte. Quando existe uma sobrescrita via CDP, o Pydoll a usa e pula o caminho JavaScript por completo.

### Via injeção de JavaScript

Tudo o que o CDP não alcança é injetado como um script que roda antes de qualquer script da página em cada novo documento (e é reaplicado dentro dos Web Workers, veja abaixo). Isso cobre:

- Extras do `navigator`: `deviceMemory`, `maxTouchPoints`, `doNotTrack`, `pdfViewerEnabled`
- `screen.availWidth` / `availHeight` (o CDP força esses iguais ao tamanho da tela, um indício de headless), `colorDepth`, `pixelDepth`, e `window.outerWidth` / `outerHeight`
- Valores de vendor, renderer, parâmetros e precisão do WebGL
- `navigator.mediaDevices`, Web Audio, vozes do `speechSynthesis`
- Disponibilidade de fontes (`document.fonts.check` / `FontFace.load`)
- `navigator.connection` (Network Information API)
- Resultados de consulta de `navigator.permissions`
- Política de tratamento de IP do WebRTC

!!! note "O canvas é deixado autêntico de propósito"
    O Pydoll **não** adiciona ruído ao canvas nem à leitura do WebGL. Sistemas de detecção pedem o fingerprint várias vezes; um hash que muda entre leituras é, por si só, um forte sinal de automação. O canvas autêntico de um Chrome real é consistente e sem nada de anormal. O que importa é que o *vendor/renderer do WebGL* que você declara seja coerente com a plataforma que você declara, que é exatamente o que a sobrescrita alinha.

## O Problema do Prototype

A parte difícil do spoofing não é mudar um valor, é **não ser pego mudando**. Scripts anti-bot modernos (o CreepJS é a implementação de referência) não apenas leem `navigator.hardwareConcurrency`; eles inspecionam *como* essa propriedade foi definida e se a maquinaria ao redor foi adulterada. Três indícios se tornaram padrão, e o spoofing ingênuo falha nos três.

**1. Propriedade própria onde deveria haver um getter no prototype.** Em um navegador real, `hardwareConcurrency` é um accessor em `Navigator.prototype`, não uma propriedade de dados na instância `navigator`. A abordagem ingênua cria uma propriedade própria:

```javascript
// Detectável: cria uma propriedade própria na instância
Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });

// navigator.hasOwnProperty('hardwareConcurrency')  ->  true   (Chrome real: false)
```

Um script que percorre `Object.getOwnPropertyNames(navigator)` ou compara a instância com seu prototype vê a anomalia imediatamente.

**2. Um `toString` que entrega a falsificação.** Todo getter nativo se reporta como código nativo:

```javascript
Object.getOwnPropertyDescriptor(Navigator.prototype, 'hardwareConcurrency')
    .get.toString();
// real:    "function get hardwareConcurrency() { [native code] }"
// ingênuo: "() => 8"   ou   "function () { ... }"
```

`Function.prototype.toString` em um getter escrito à mão retorna seu código-fonte JavaScript, então uma única chamada `.toString()` expõe a sobrescrita.

**3. Vazamentos entre realms.** Uma página pode criar um novo realm JavaScript (um `iframe` de mesma origem, ou um Web Worker) cujos `navigator` e prototypes não foram tocados por um hook instalado apenas no realm principal. Um worker tem seu próprio `WorkerNavigator`; se ele reporta o `hardwareConcurrency` real enquanto a página reporta um falso, os dois discordam e a mentira fica provada.

### Como o Pydoll resolve isso

- **Os getters são definidos no prototype**, onde os nativos vivem (`Navigator.prototype`, `Screen.prototype`), então a instância não fica com propriedades próprias anômalas.
- **Funções injetadas se reportam como nativas sob `toString`.** A sobrescrita é instalada de modo que a introspecção via `toString` dos getters modificados seja indistinguível de um accessor genuíno com `[native code]`, e o patch no próprio `toString` não se torne um novo indício.
- **A identidade é reaplicada dentro dos workers.** O Pydoll se auto-anexa a workers dedicados, compartilhados e de serviço e aplica as mesmas sobrescritas a cada `WorkerNavigator`, para que a página e cada realm que ela cria contem a mesma história.

É isso que permite que um fingerprint do Pydoll passe nas verificações de detecção de mentira, prototype, workers e fontes do CreepJS, em vez de apenas mudar os números visíveis.

## Modo Headless

Antes da injeção de fingerprint, o Chrome headless era fácil de detectar, e é exatamente por isso que verificações de bot e captchas tantas vezes falhavam em headless: o navegador parecia um bot antes de qualquer interação. Rodar sem uma tela e GPU reais muda sinais mensuráveis:

- **Renderer do WebGL (o indício decisivo).** Sem passagem de GPU, o Chrome headless renderiza por um rasterizador de software (SwiftShader). `UNMASKED_RENDERER_WEBGL` reporta algo como `ANGLE (Google, Vulkan 1.3.0 (SwiftShader))` ou `Google SwiftShader` em vez de uma string de GPU real como `ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11)` ou `Apple M3`. Esse indício é mortal porque corrigir só a string não resolve: toda a superfície de capacidade da GPU (extensões suportadas, precisão de shader, tamanho máximo de textura) continua refletindo o rasterizador de software e é cruzada com a GPU declarada.
- **`navigator.plugins` / `mimeTypes` vazios**, enquanto o Chrome desktop real expõe entradas do visualizador de PDF embutido.
- **`screen.availWidth` / `availHeight` iguais ao tamanho total da tela** (sem a folga da barra de tarefas ou dock), além de uma janela externa fixa ou zerada.
- **Dispositivos de mídia ausentes, e rasterização de fontes/áudio** que difere de uma máquina com tela real.
- No antigo `--headless`, um token `HeadlessChrome` no User-Agent (removido no `--headless=new`, mas todos os indícios de renderização acima permanecem).

A injeção de fingerprint neutraliza isso. Ela sobrescreve o vendor e o renderer do WebGL **e** a superfície de parâmetros e precisão, para que toda a história da GPU fique coerente, não só a string; reporta `availWidth` / `availHeight` com uma folga de barra de tarefas realista; restaura dispositivos de mídia e fontes; e fixa o User-Agent via CDP para que nenhum token `HeadlessChrome` sobreviva. Com um perfil aplicado, **todos os sites de detecção testados reportam o navegador como um Chrome comum e com interface**, e rodar em headless deixa de mudar o resultado.

Na prática, é isso que permite rodar uma busca simples no Google em modo headless: a mesma automação que o Google bloqueava em headless passa quando o fingerprint faz o navegador parecer real.

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.constants import Key

from examples.fingerprints import FINGERPRINTS

async def headless_google_search():
    async with Chrome() as browser:
        tab = await browser.start(headless=True)

        # Neutraliza os indícios de renderização headless antes da primeira navegação.
        await tab.apply_fingerprint(FINGERPRINTS['windows11_rtx3060_nyc'])

        await tab.go_to('https://www.google.com')
        search_box = await tab.find(tag_name='textarea', name='q')
        await search_box.type_text('pydoll', humanize=True)
        await tab.keyboard.press(Key.ENTER)
        await asyncio.sleep(3)
        print('Busca no Google concluída em modo headless.')

asyncio.run(headless_google_search())
```

!!! note "Combinando isso com o Cloudflare Turnstile"
    O motivo mais comum de o Turnstile falhar com um fingerprint aplicado é uma **incompatibilidade de versão do Chrome**, não o headless, veja [Estudo de Caso: uma Incompatibilidade de Versão do Chrome Disparando o Desafio do Cloudflare](#case-study-a-chrome-version-mismatch-triggering-cloudflares-challenge). Faça a versão do perfil bater com o binário real primeiro. Mesmo com isso corrigido, o Turnstile em **headless** de forma confiável ainda está sendo validado, então prefira rodar com interface para o Turnstile por enquanto. Veja [Cloudflare Turnstile](behavioral-captcha-bypass.md).

!!! warning "Renderização, não reputação"
    A injeção de fingerprint remove os indícios de *renderização* do headless; ela não muda o seu IP. Um IP de datacenter com reputação ruim continua sendo desafiado em headless e com interface igualmente (veja [Cloudflare Turnstile, O Que Determina o Sucesso](behavioral-captcha-bypass.md#what-determines-success)). Combine um fingerprint consistente com um IP residencial limpo.

## Consistência é Tudo {#consistency-is-the-whole-game}

Um fingerprint é tão forte quanto sua camada mais fraca, e sistemas anti-bot correlacionam sinais de todas elas. Um navegador que renderiza como macOS enquanto seu `Accept-Language` diz português do Brasil, seu fuso horário diz Tóquio e seu IP geolocaliza na Alemanha é *mais* suspeito do que um navegador que você nunca tocou.

O `apply_fingerprint()` mantém as camadas **que ele controla** internamente consistentes. Você é dono das duas que ele não controla:

1. **O binário do Chrome que você dirige.** O fingerprint da camada de rede (TLS JA3/JA4, `SETTINGS` do HTTP/2) é produzido pelo navegador real e não pode ser falsificado via CDP, e nem a versão verdadeira do engine JavaScript. Um perfil declarando Chrome 145 precisa rodar em um binário Chrome 145, ou o User-Agent contradiz o handshake real. É exatamente isso que bloqueia o Cloudflare Turnstile, veja [Estudo de Caso: uma Incompatibilidade de Versão do Chrome Disparando o Desafio do Cloudflare](#case-study-a-chrome-version-mismatch-triggering-cloudflares-challenge).
2. **A geografia do seu IP de saída.** O header `Accept-Language` e o fuso horário são cruzados com o país do IP. Uma identidade dos EUA em um IP brasileiro é uma contradição (é exatamente a falha documentada em [Estudo de Caso: uma Incompatibilidade de Locale Disparando o Captcha do Google](#case-study-a-locale-mismatch-triggering-googles-captcha)).

!!! tip "A Regra de Ouro"
    **Cada camada deve contar a mesma história.** Veja [Fingerprinting do Navegador](../../deep-dive/fingerprinting/index.md) para o princípio e [Técnicas de Evasão, Consistência de Fuso Horário e Locale](../../deep-dive/fingerprinting/evasion-techniques.md) para como locale, fuso horário e geolocalização do IP são correlacionados.

## Estudo de Caso: uma Incompatibilidade de Locale Disparando o Captcha do Google {#case-study-a-locale-mismatch-triggering-googles-captcha}

Durante os testes, aplicar um perfil de fingerprint dos EUA fez uma busca simples no Google começar a retornar um captcha. Comentar a única linha `apply_fingerprint()` fazia o bloqueio sumir. O fingerprint passava em todos os sites dedicados de fingerprinting, então o que era diferente no Google?

**A incompatibilidade.** O perfil declarava uma identidade dos EUA (`locale.languages = ['en-US', 'en']`), mas a máquina rodava atrás de um **IP brasileiro** com um **idioma de sistema brasileiro**. O Google cruza o header `Accept-Language` e os Client Hints com o país do IP. Um navegador `en-US` chegando de um IP de São Paulo não é uma combinação que um usuário real costuma produzir, e os headers da requisição chegavam inconsistentes com o resto dos sinais. Essa única contradição foi suficiente para derrubar o score de confiança abaixo do limiar de captcha do Google.

**O que o `locale` realmente controla.** Não é cosmético. O campo `locale` dirige:

- o **header HTTP** `Accept-Language` enviado em toda requisição,
- `navigator.language` e `navigator.languages`,
- os padrões de formatação do `Intl` (datas, números, moeda).

Todos os três são lidos por sistemas anti-abuso, e todos os três têm que concordar com o fuso horário e o IP. Corrigir o perfil para um locale brasileiro (batendo com o IP e o sistema) removeu o bloqueio sem mudar mais nada.

<!-- PLACEHOLDER: substitua por uma captura de tela do captcha do Google produzido pelo fingerprint inconsistente (locale dos EUA em IP do BR). Arquivo sugerido: docs/resources/images/fingerprint-inconsistent-captcha.png -->
<p align="center">
  <img src="../../resources/images/fingerprint-inconsistent-captcha.png" alt="Google servindo um captcha porque o locale dos EUA do fingerprint injetado contradiz o IP de saída brasileiro" width="720" />
</p>
<p align="center"><sub>Fingerprint inconsistente: um locale dos EUA sobre um IP brasileiro. O Google retorna um captcha.</sub></p>

<!-- PLACEHOLDER: substitua por uma captura de tela de uma página normal de resultados do Google após o locale ser alinhado ao IP. Arquivo sugerido: docs/resources/images/fingerprint-consistent-pass.png -->
<p align="center">
  <img src="../../resources/images/fingerprint-consistent-pass.png" alt="Google retornando resultados normais de busca quando o locale do fingerprint bate com o país do IP de saída" width="720" />
</p>
<p align="center"><sub>Fingerprint consistente: locale, fuso horário e IP todos concordam. A busca passa.</sub></p>

!!! danger "A lição"
    Um fingerprint que passa em todos os testes de fingerprinting ainda pode ser bloqueado se **uma** camada contradiz seu ambiente. Detecção é sobre correlação, não sobre qualquer valor isolado. Alinhe `locale`, `timezone` e geolocalização ao seu IP de saída antes de culpar o fingerprint.

## Estudo de Caso: uma Incompatibilidade de Versão do Chrome Disparando o Desafio do Cloudflare {#case-study-a-chrome-version-mismatch-triggering-cloudflares-challenge}

Para usar a interação com o [Cloudflare Turnstile](behavioral-captcha-bypass.md) **junto com** um fingerprint, a versão declarada pelo navegador precisa bater com o binário real do Chrome que você dirige. Isso não é opcional, e errar nisso é a forma mais comum de a injeção de fingerprint quebrar o Turnstile.

**A observação.** Aplicar o perfil `macos_m3_new_york` fazia o Cloudflare Turnstile falhar mesmo **sem headless**: a página ficava travada na tela intermediária "Just a moment…" e nunca liberava. Remover a única chamada `apply_fingerprint()` fazia passar em quatro segundos. Então o problema não era o headless, e nem a injeção de JavaScript (que passa em toda suíte dedicada de fingerprinting): era algo que a sobrescrita introduziu.

**A incompatibilidade.** O perfil fixava **Chrome 145** em seu User-Agent, mas a máquina dirigia um binário **Chrome 151** real. O `apply_fingerprint()` sobrescrevia `navigator.userAgent`, `Sec-CH-UA` e `navigator.userAgentData` para declarar 145, enquanto o handshake TLS/HTTP2 genuíno e o engine JavaScript permaneciam 151. Uma bissecção de variável única confirmou: mantendo tudo o mais constante e trocando apenas a major declarada de 145 para 151, toda falha virou aprovação.

**Por que a versão precisa bater.** Duas camadas reportam a versão real do navegador e **não podem ser falsificadas** via CDP:

- **O handshake de rede.** O fingerprint TLS (JA3/JA4) e o frame `SETTINGS` do HTTP/2 são produzidos pela build real do Chrome antes de qualquer JavaScript rodar. Eles codificam a versão real do engine.
- **A superfície do engine JavaScript.** O conjunto de APIs disponíveis e seu comportamento refletem a build real do V8/Blink.

O desafio gerenciado do Cloudflare cruza a versão que você **declara** (User-Agent + Client Hints) com a versão que ele consegue **observar** (o handshake e o engine). Um navegador real nunca declara uma versão diferente da que ele roda, então declarar 145 sobre um handshake 151 é uma contradição que nenhum cliente genuíno produz. O Turnstile derruba o score de confiança e a tela intermediária nunca libera.

**Como fazer bater.** Leia a versão real do binário e faça o User-Agent do perfil concordar com ela:

```python
async with Chrome() as browser:
    tab = await browser.start()

    version = await browser.get_version()
    print(version['product'])  # ex.: 'Chrome/151.0.7922.137'
```

Em `examples/fingerprints.py`, as constantes `CHROME_DESKTOP` / `CHROME_MOBILE` definem a versão embutida no User-Agent de cada perfil. Defina-as para a major que seu binário reporta (a build completa alimenta o `Sec-CH-UA-Full-Version-List`; o `navigator.userAgent` visível é reduzido para `Chrome/<MAJOR>.0.0.0` automaticamente). Quando você atualizar o Chrome, aumente-as, ou o próximo desafio vai pegar a defasagem.

!!! danger "A regra para Cloudflare + fingerprint"
    Um fingerprint cuja versão do Chrome não bate com o binário real **será** desafiado pelo Turnstile, com ou sem interface. Alinhe a versão do perfil ao `browser.get_version()` antes de combinar a injeção de fingerprint com a interação do Cloudflare.

## Múltiplos Fingerprints e Contextos de Navegador

Workers de serviço e compartilhados são **compartilhados entre todas as abas de um contexto de navegador**, então um contexto só pode carregar uma identidade coerente. O Pydoll impõe isso: aplicar um fingerprint *diferente* a um contexto que já tem um lança `FingerprintContextConflict`.

```python
from pydoll.exceptions import FingerprintContextConflict

# Mesmo contexto, dois fingerprints diferentes -> conflito
tab_a = await browser.start()
await tab_a.apply_fingerprint(FINGERPRINTS['windows11_rtx3060_nyc'])

tab_b = await browser.new_tab()               # mesmo contexto (padrão)
try:
    await tab_b.apply_fingerprint(FINGERPRINTS['macos_m3_new_york'])
except FingerprintContextConflict:
    print('Um contexto carrega uma identidade.')
```

Para rodar fingerprints **diferentes** lado a lado, coloque cada um em seu próprio contexto de navegador:

```python
ctx_id = await browser.create_browser_context()
tab_us = await browser.start()
tab_br = await browser.new_tab(browser_context_id=ctx_id)

await tab_us.apply_fingerprint(FINGERPRINTS['windows11_rtx3060_nyc'])
await tab_br.apply_fingerprint(FINGERPRINTS['android_s24_ultra_sao_paulo'])
```

Veja [Contextos de Navegador](../browser-management/contexts.md) para como contextos isolados funcionam.

## Traga Seus Próprios Fingerprints {#bring-your-own-fingerprints}

!!! important "O Pydoll não gera nem distribui fingerprints"
    Os perfis em `examples/fingerprints.py` existem **apenas como referência**: eles mostram o quão coerente um perfil precisa ser e o formato exato do `FingerprintConfig` que você passa para `apply_fingerprint()`. Não são um catálogo para usar como está, e não são gerados para você.

    Um fingerprint utilizável é um que você constrói para o **seu** ambiente. Ele precisa bater com:

    - o **binário real do Chrome** que você dirige (a camada de rede é autêntica e não falsificável), e
    - a **geografia do seu IP de saída** (locale, fuso horário, geolocalização).

    Reutilize um perfil público amplamente o suficiente e ele deixa de ser um disfarce e vira uma assinatura. Construa o seu.

## Veja Também

- **[Fingerprinting do Navegador](../../deep-dive/fingerprinting/index.md)** - A Regra de Ouro e como a detecção funciona camada por camada
- **[Técnicas de Evasão](../../deep-dive/fingerprinting/evasion-techniques.md)** - Consistência de fuso horário/locale, consistência de User-Agent, proteção contra vazamento de WebRTC
- **[Fingerprinting do Navegador (superfície de detecção)](../../deep-dive/fingerprinting/browser-fingerprinting.md)** - Canvas, WebGL, navigator e detecção de fontes em profundidade
- **[Contextos de Navegador](../browser-management/contexts.md)** - Rodando múltiplas identidades isoladamente
- **[Configuração de Proxy](../configuration/proxy.md)** - Alinhando seu IP de saída à geografia do fingerprint
