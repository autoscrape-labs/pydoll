# Injeção de fingerprint

`tab.apply_fingerprint()` sobrescreve os sinais de identidade do navegador que os scripts de fingerprinting leem: User-Agent e Client Hints, propriedades do `navigator`, WebGL, métricas de tela, fontes, áudio, fuso horário e locale. Os valores sobrescritos têm que permanecer consistentes entre si e com as camadas que `apply_fingerprint()` não controla (veja [Consistência entre camadas](#consistency-is-the-whole-game)). Um fingerprint inconsistente é mais detectável do que um navegador sem modificações.

Isto é substituição de identidade, não anonimato: não muda o fingerprint da camada de rede nem o IP de saída.

## Início rápido

Chame `apply_fingerprint()` antes da primeira navegação. Os overrides em JavaScript são registrados com `Page.addScriptToEvaluateOnNewDocument`, então eles só se aplicam a documentos carregados depois da chamada.

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
        print('Fingerprint applied.')
        await asyncio.sleep(5)

asyncio.run(spoof_fingerprint())
```

`FingerprintConfig` (de `pydoll.protocol.fingerprint.types`) é um dicionário tipado. Apenas os campos presentes são sobrescritos; o restante mantém os valores reais do navegador. Os perfis em `examples/fingerprints.py` são referências completas e internamente consistentes para o formato da config (veja [Fornecendo seus próprios perfis](#bring-your-own-fingerprints)).

!!! note "De onde vem `FINGERPRINTS`"
    O Pydoll não inclui perfis de fingerprint. `FINGERPRINTS` fica em `examples/fingerprints.py` no [repositório do pydoll](https://github.com/autoscrape-labs/pydoll), como perfis de referência para o formato de `FingerprintConfig`. Copie esse arquivo para o seu projeto para usá-los, depois adapte cada perfil à sua própria máquina e IP (o checklist abaixo explica por quê). Um perfil reutilizado como está é uma assinatura compartilhada, não um disfarce.

## Veja a diferença: um teste de bot score ao vivo {#see-the-difference-a-live-bot-score-test}

Se um fingerprint ajuda ou atrapalha é mensurável. O [fingerprint-scan.com](https://fingerprint-scan.com/), criado pelo engenheiro por trás do blog anti-bot da Castle, roda um teste de fingerprinting e detecção de bots dentro da página e reporta um **bot score** de 0 a 100, onde mais baixo é lido como mais humano. As três execuções abaixo são da mesma máquina (um Mac com Apple Silicon, Chrome 151, headful), capturadas com o Pydoll controlando o navegador e tirando o screenshot.

**Sem fingerprint**, o Pydoll controlando um Chrome real sem nada aplicado: score 15/100.

<p align="center">
  <img src="/docs/resources/images/fp-scan-no-fingerprint.png" alt="fingerprint-scan.com reportando um bot score de 15/100 para o Pydoll sem nenhum fingerprint aplicado" width="760" />
</p>
<p align="center"><sub>Um Chrome real via CDP já é lido como humano: 15/100.</sub></p>

O Pydoll começa baixo por conta própria. Ele controla um Chrome real via CDP, então a GPU, o canvas e o TLS são autênticos e `navigator.webdriver` é `false`. Fechar a distância restante até 0 é uma área que ainda está sendo aprimorada.

**Um perfil de macOS no Mac**, uma identidade que combina com o sistema operacional: score 15/100.

<p align="center">
  <img src="/docs/resources/images/fp-scan-mac-on-mac.png" alt="fingerprint-scan.com reportando um bot score de 15/100 para um fingerprint de macOS aplicado num host macOS" width="760" />
</p>
<p align="center"><sub>Um perfil de macOS que combina: ainda 15/100, consistente, não invisível.</sub></p>

Aplicar um perfil de Mac num Mac muda a identidade reportada sem contradizer o hardware por baixo, então o score não se move. Um perfil que combina é consistente, não invisível.

**Um perfil de Windows no Mac**, um campo em desacordo: score 57/100.

<p align="center">
  <img src="/docs/resources/images/fp-scan-windows-on-mac.png" alt="fingerprint-scan.com reportando um bot score de 57/100 para um fingerprint de Windows aplicado num host macOS" width="760" />
</p>
<p align="center"><sub>Uma contradição de sistema operacional quase quadruplica o score: 57/100.</sub></p>

Mesma injeção, mesma máquina; o perfil agora afirma ser Windows num host cujo kernel, GPU e renderização de texto são macOS. Essa única contradição quase quadruplica o score.

| Execução (mesmo Mac, Chrome 151, headful) | Bot score |
|---|---|
| Sem fingerprint | 15 / 100 |
| Perfil de macOS no macOS (combinando) | 15 / 100 |
| Perfil de Windows no macOS (incompatível) | 57 / 100 |

Duas conclusões. A injeção torna o fingerprint consistente; ela não torna o navegador invisível: mesmo a execução que combina marca 15, não 0, e fechar essa distância ainda está sendo trabalhado. E o valor está em *combinar*, e é por isso que um perfil inconsistente marca pior do que nenhum perfil, e por que toda regra no checklist abaixo é sobre concordância entre camadas.

!!! warning "Esses números são um retrato de um momento"
    Uma máquina, um IP, uma build do Chrome, um ponto no tempo. Os seus vão diferir, e os sites de detecção mudam a pontuação deles. Encare os scores como uma demonstração da direção (o que combina fica baixo, o incompatível dispara), não como um resultado garantido.

O mesmo teste em modo headless começa bem mais alto. Sem perfil, o Chrome headless marca o máximo:

<p align="center">
  <img src="/docs/resources/images/fp-scan-headless-nofp.png" alt="fingerprint-scan.com reportando um bot score de 100/100 para o Chrome headless sem fingerprint" width="760" />
</p>
<p align="center"><sub>Headless, sem perfil: o máximo, 100/100.</sub></p>

Aplique o perfil de macOS e a mesma execução headless cai para 15, no mesmo nível do resultado headful:

<p align="center">
  <img src="/docs/resources/images/fp-scan-headless-mac.png" alt="fingerprint-scan.com reportando um bot score de 15/100 para o Chrome headless com um fingerprint de macOS aplicado" width="760" />
</p>
<p align="center"><sub>Headless com um perfil de macOS: 15/100, no nível do headful.</sub></p>

No modo headless o perfil muda o resultado mais do que em qualquer outro caso, do máximo até o score do headful. A seção [Modo headless](#headless-mode) cobre quais sinais ele neutraliza.

## O override, tornado visível

A maneira mais fácil de confirmar que um perfil surtiu efeito é ler de volta um sinal de hardware. O [browserleaks.com/webgl](https://browserleaks.com/webgl) reporta a GPU por trás do WebGL. Neste MacBook, sem perfil aplicado, ele lê o chip real, um Apple M4, com um User-Agent de macOS:

<p align="center">
  <img src="/docs/resources/images/browserleaks-webgl-real.png" alt="Relatório WebGL do browserleaks mostrando um User-Agent de macOS e o renderer sem máscara ANGLE (Apple, Apple M4)" width="760" />
</p>
<p align="center"><sub>Sem perfil: o Apple M4 real e um User-Agent de macOS.</sub></p>

Aplique o perfil de Windows e a mesma página, na mesma máquina, reporta uma NVIDIA GeForce RTX 3060 e um User-Agent de Windows:

<p align="center">
  <img src="/docs/resources/images/browserleaks-webgl-rtx3060.png" alt="Relatório WebGL do browserleaks mostrando um User-Agent de Windows e o renderer sem máscara ANGLE (NVIDIA, NVIDIA GeForce RTX 3060)" width="760" />
</p>
<p align="center"><sub>Perfil de Windows, mesma máquina: uma NVIDIA RTX 3060 e um User-Agent de Windows.</sub></p>

`apply_fingerprint()` definiu o vendor e o renderer sem máscara do WebGL através dos overrides injetados, junto com o User-Agent e os Client Hints. Um limite honesto fica visível nas mesmas duas capturas: o **WebGL Image Hash é idêntico** (`52497E30...`). A *string* do renderer agora diz NVIDIA, mas os pixels ainda são desenhados pela GPU Apple real, então o fingerprint da imagem renderizada não se move. Sobrescrever a string é necessário, mas não suficiente: um detector que rasteriza a saída e a passa por hash ainda vê o hardware real. É exatamente por isso que afirmar uma GPU NVIDIA numa máquina Apple é a contradição que empurrou o score para 57 acima, e por que o checklist insiste que o sistema operacional e a GPU do perfil combinem com o host.

## Checklist

Regras para um perfil que não é detectado. A maioria descreve uma camada que `apply_fingerprint()` não consegue controlar, então o perfil tem que ser escolhido para combinar com ela em vez de brigar com ela.

- Sistema operacional do perfil = sistema operacional do host. Não rode um perfil de Windows no macOS nem o contrário; a stack TCP/IP do kernel e a renderização de GPU/texto expõem o sistema operacional real em camadas que o CDP não alcança ([Incompatibilidade de sistema operacional](#case-study-an-os-mismatch-triggering-cloudflares-managed-challenge)).
- Versão do Chrome no User-Agent = versão do binário real. Mantenha `CHROME_DESKTOP` / `CHROME_MOBILE` iguais à major de `browser.get_version()`, e atualize-os a cada upgrade do Chrome ([Incompatibilidade de versão do Chrome](#case-study-a-chrome-version-mismatch-triggering-cloudflares-challenge)).
- Locale, fuso horário e geolocalização = país do IP de saída. `Accept-Language` e o fuso horário são cruzados com o IP ([Incompatibilidade de locale/IP](#case-study-a-locale-mismatch-triggering-googles-captcha)).
- Vendor/renderer do WebGL = família de GPU do host (um renderer Apple em hardware Apple, e assim por diante). Os pixels renderizados vêm da GPU real e não podem ser forjados.
- Aplique o fingerprint antes da primeira navegação.
- Uma identidade por contexto de navegador; use contextos separados para identidades diferentes ([Múltiplos fingerprints entre contextos](#multiple-fingerprints-across-contexts)).
- Não combine a opção `--user-agent` com `apply_fingerprint()`; o fingerprint é o dono do User-Agent.
- Use um IP residencial limpo. A injeção não muda a reputação do IP.

## Overrides

Os overrides são aplicados através de dois mecanismos.

### Overrides via CDP

Os sinais que o próprio Chrome consegue sobrescrever são definidos através do domínio `Emulation` do DevTools Protocol. O navegador os aplica abaixo da camada JavaScript, então o getter que um script de detecção lê continua sendo o nativo e não há nenhum wrapper JavaScript para inspecionar. Quando existe um override de CDP para um sinal, ele é usado em vez de um override em JavaScript.

| Sinal | Comando CDP |
|--------|-------------|
| User-Agent, `navigator.platform` / `vendor` / `appVersion`, Client Hints (`Sec-CH-UA*`) | `Emulation.setUserAgentOverride` |
| Fuso horário (`Intl`, `Date`) | `Emulation.setTimezoneOverride` |
| Geolocalização | `Emulation.setGeolocationOverride` |
| Tamanho de tela, `devicePixelRatio`, viewport, orientação | `Emulation.setDeviceMetricsOverride` |
| Locale (formatação `Intl`) | `Emulation.setLocaleOverride` |
| `navigator.hardwareConcurrency` | `Emulation.setHardwareConcurrencyOverride` |

`hardwareConcurrency` ilustra a diferença: um getter JavaScript é detectável (veja abaixo), enquanto `Emulation.setHardwareConcurrencyOverride` muda o valor com o getter permanecendo nativo.

### Overrides via JavaScript

Os sinais que o CDP não alcança são definidos por um script injetado antes de qualquer script da página em todo novo documento, e replicado em Web Workers. Isso cobre:

- extras do `navigator`: `deviceMemory`, `maxTouchPoints`, `doNotTrack`, `pdfViewerEnabled`
- `screen.availWidth` / `availHeight` (o CDP força esses iguais ao tamanho da tela, um sinal de headless), `colorDepth`, `pixelDepth` e `window.outerWidth` / `outerHeight`
- vendor, renderer e valores de parâmetro/precisão do WebGL
- `navigator.mediaDevices`, Web Audio, vozes de `speechSynthesis`
- disponibilidade de fontes (`document.fonts.check` / `FontFace.load`)
- `navigator.connection` (Network Information API)
- resultados de consultas de `navigator.permissions`
- política de tratamento de IP do WebRTC

O readback de canvas e WebGL não é modificado. Os sistemas de detecção requisitam o fingerprint repetidamente, então um valor que muda entre leituras é, por si só, um sinal de automação; o canvas de um Chrome real é estável. As strings de vendor e renderer do WebGL são sobrescritas para combinar com a plataforma declarada, mas os pixels renderizados são deixados inalterados.

## Detectando overrides em JavaScript

Os scripts de fingerprinting não leem apenas o valor de uma propriedade; eles inspecionam como ela foi definida e se os objetos ao redor foram modificados. Três verificações são padrão, e um override ingênuo falha em todas as três. O CreepJS é a implementação de referência.

Propriedade própria vs accessor no prototype. Num navegador real, `hardwareConcurrency` é um accessor em `Navigator.prototype`, não uma propriedade de dados na instância `navigator`:

```javascript
Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
// navigator.hasOwnProperty('hardwareConcurrency') === true   (Chrome real: false)
```

`Object.getOwnPropertyNames(navigator)` ou uma comparação com o prototype expõe a propriedade própria adicionada.

`toString` do getter. Um getter nativo se reporta como código nativo:

```javascript
Object.getOwnPropertyDescriptor(Navigator.prototype, 'hardwareConcurrency').get.toString();
// real:    "function get hardwareConcurrency() { [native code] }"
// ingênuo: "() => 8"
```

`Function.prototype.toString` retorna o código-fonte JavaScript de um getter escrito à mão, então uma única chamada o expõe.

Leituras entre realms. Um `iframe` de mesma origem ou um Web Worker é um realm novo cujo `navigator` e prototypes estão intocados por um hook instalado apenas no realm principal. Um `WorkerNavigator` de um worker reportando o valor real enquanto a página reporta o override é uma contradição.

### Como o pydoll evita esses sinais

- Os getters são definidos no prototype (`Navigator.prototype`, `Screen.prototype`), então a instância não ganha propriedades próprias.
- Os getters e métodos com patch se reportam como nativos sob `toString`, e o próprio patch de `toString` não se torna um novo sinal.
- Os overrides são replicados em dedicated, shared e service workers, então a página e os realms que ela gera reportam os mesmos valores.

É por isso que um perfil injetado passa nas verificações de detecção de mentiras, de prototype, de worker e de fontes do CreepJS, em vez de apenas mudar os valores visíveis.

A verificação de worker é a que um override ingênuo falha com mais frequência. O CreepJS lê cada sinal na página principal e depois roda o fingerprint inteiro de novo dentro de um Web Worker, um realm separado que um hook da thread principal nunca alcança. Os screenshots abaixo são deste Mac com o perfil de Windows aplicado.

Na página principal, a seção `navigator` reporta a identidade de Windows de ponta a ponta: platform `Win32`, `Windows 11`, o User-Agent de Windows e o `appVersion`, além das listas de plugins e mimeTypes, memória do dispositivo e contagem de núcleos.

<p align="center">
  <img src="/docs/resources/images/creepjs-navigator-windows.png" alt="Seção navigator do CreepJS na página principal reportando platform Win32, Windows 11, um User-Agent e appVersion de Windows, plugins e núcleos/ram" width="760" />
</p>
<p align="center"><sub>Página principal: o navigator reporta a identidade Windows 11.</sub></p>

Sua seção WebGL lê uma NVIDIA GeForce RTX 3060 com alta confiança, com as métricas de tela do perfil ao lado:

<p align="center">
  <img src="/docs/resources/images/creepjs-webgl-windows.png" alt="Seções WebGL e Screen do CreepJS na página principal lendo uma NVIDIA GeForce RTX 3060 com alta confiança e uma tela 1920x1080" width="760" />
</p>
<p align="center"><sub>Página principal: o WebGL lê a NVIDIA RTX 3060.</sub></p>

O mesmo fingerprint, relido dentro de um service worker, reporta a mesma GPU ao lado de um User-Agent de Windows, `Win32` e Windows 11:

<p align="center">
  <img src="/docs/resources/images/creepjs-worker-windows.png" alt="Painel Worker do CreepJS mostrando a identidade injetada replicada dentro do ServiceWorkerGlobalScope: um User-Agent de Windows, uma NVIDIA GeForce RTX 3060 com alta confiança, Win32 e Windows 11, tudo num Mac da Apple" width="760" />
</p>
<p align="center"><sub>Dentro de um service worker: a mesma identidade, replicada.</sub></p>

Um override instalado apenas no realm principal vazaria os valores reais de macOS e da GPU Apple naquele painel de worker, e a divergência entre a página e o seu worker é exatamente a contradição que o CreepJS reporta como mentira. Como o Pydoll replica os overrides em dedicated, shared e service workers, os dois realms concordam.

## Modo headless {#headless-mode}

O Chrome headless expõe sinais que um navegador headful não expõe, e é por isso que as verificações de bot costumavam falhar antes da injeção de fingerprint:

- Renderer do WebGL. Sem passthrough de GPU, o Chrome headless renderiza através de um rasterizador de software (SwiftShader). `UNMASKED_RENDERER_WEBGL` reporta `ANGLE (Google, Vulkan 1.3.0 (SwiftShader))` ou `Google SwiftShader` em vez de uma string de GPU real como `ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11)` ou `Apple M3`. Sobrescrever apenas a string é insuficiente: a superfície de capacidades da GPU (extensões suportadas, precisão de shader, tamanho máximo de textura) ainda reflete o renderer de software e é cruzada com a GPU declarada.
- `navigator.plugins` / `mimeTypes` vazios, onde o Chrome headful expõe as entradas do visualizador de PDF embutido.
- Uma tela virtual fixa de `800x600`: `availWidth` / `availHeight` iguais ao tamanho da tela (sem espaço de taskbar ou dock), `availTop` igual a `0` (sem barra de menu) e a janela externa zerada. O `setDeviceMetricsOverride` corrige o `window.screen` da própria página, mas é limitado à sessão, então um iframe cross-origin (um iframe fora do processo, OOPIF) continua lendo essa tela `800x600` crua e contradiz a página que o embute.
- Dispositivos de mídia ausentes, e diferenças de rasterização de fontes/áudio em relação a uma máquina com display.
- No antigo `--headless`, um token `HeadlessChrome` no User-Agent (removido no `--headless=new`; os sinais de renderização acima permanecem).

`apply_fingerprint()` sobrescreve o vendor/renderer do WebGL e a superfície de parâmetro/precisão, reporta `availWidth`/`availHeight` com um espaço de taskbar, restaura dispositivos de mídia e fontes, e fixa o User-Agent através do CDP. No headless ele também remodela a tela virtual global do navegador (`Emulation.updateScreen`), então a página principal e os iframes cross-origin leem uma única tela coerente, com o mesmo tamanho, `devicePixelRatio`, `colorDepth` e uma área de trabalho real de barra de menu/dock (`availTop`). Com um perfil aplicado, os sites de detecção testados reportam o navegador como headful.

Cada frame lê seu próprio `window.screen`. Sem a remodelagem, um iframe cross-origin lê a tela `800x600` crua do headless; com ela, o iframe combina com a página:

<iframe src="/docs/resources/visuals/headless-screen-oopif.html" aria-label="Uma página headless e seu iframe cross-origin lendo window.screen; alternar a remodelagem faz o iframe passar da tela 800x600 crua do headless para combinar com a página" style="width: 100%; height: 460px; border: 0;" loading="lazy"></iframe>

A área de trabalho vem do `avail_top` / `avail_left` do perfil (e `avail_width` / `avail_height`); o perfil macOS reserva uma barra de menu de 25px, o perfil Windows uma taskbar embaixo. A tela virtual headless só aceita um `devicePixelRatio` inteiro, então um dpr fracionário (mobile, escalonamento de tela do Windows) é arredondado para os iframes, enquanto a página principal mantém o valor exato.

Como o [teste de bot score acima](#see-the-difference-a-live-bot-score-test) mostra, o headless vai de 100/100 sem perfil para 15/100 com o perfil de macOS, o mesmo que a execução headful. É isso que permite que uma busca simples no Google rode em modo headless:

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.constants import Key

from examples.fingerprints import FINGERPRINTS

async def headless_google_search():
    async with Chrome() as browser:
        tab = await browser.start(headless=True)

        # Neutraliza os sinais de renderização do headless antes da primeira navegação.
        await tab.apply_fingerprint(FINGERPRINTS['windows11_rtx3060_nyc'])

        await tab.go_to('https://www.google.com')
        search_box = await tab.find(tag_name='textarea', name='q')
        await search_box.type_text('pydoll', humanize=True)
        await tab.keyboard.press(Key.ENTER)
        await asyncio.sleep(3)
        print('Google search completed in headless mode.')

asyncio.run(headless_google_search())
```

A injeção de fingerprint remove apenas os sinais de renderização do headless. Ela não muda o IP: um IP de datacenter com má reputação continua sendo desafiado tanto em headless quanto em headful (veja [O que determina o sucesso](captcha-bypass.md)).

Para o Cloudflare Turnstile, a falha mais comum com um fingerprint aplicado é uma incompatibilidade de versão do Chrome, não o headless (veja [Incompatibilidade de versão do Chrome](#case-study-a-chrome-version-mismatch-triggering-cloudflares-challenge)). O Turnstile em headless ainda está sendo validado; prefira headful para ele.

## Consistência entre camadas {#consistency-is-the-whole-game}

Os sistemas anti-bot correlacionam sinais entre camadas. `apply_fingerprint()` mantém consistentes as camadas que ele controla, mas três camadas ficam fora do alcance do CDP e têm que ser combinadas separadamente:

1. Versão do binário do Chrome. O fingerprint da camada de rede (TLS JA3/JA4, `SETTINGS` do HTTP/2) e a versão do motor JavaScript vêm do binário real e não podem ser sobrescritos. Um perfil que afirma ser Chrome 145 tem que rodar num binário Chrome 145 (veja [Incompatibilidade de versão do Chrome](#case-study-a-chrome-version-mismatch-triggering-cloudflares-challenge)).
2. Geografia do IP de saída. O header `Accept-Language` e o fuso horário são verificados contra o país do IP. Uma identidade dos EUA num IP brasileiro é uma contradição (veja [Incompatibilidade de locale/IP](#case-study-a-locale-mismatch-triggering-googles-captcha)).
3. Sistema operacional do host. A stack TCP/IP do kernel é um fingerprint passivo do sistema operacional (TTL inicial 64 no macOS/Linux, 128 no Windows), e a renderização de GPU/texto também reflete o sistema operacional real. Nenhum dos dois é alcançável através do CDP. Um perfil de Windows num Mac é uma contradição de sistema operacional (veja [Incompatibilidade de sistema operacional](#case-study-an-os-mismatch-triggering-cloudflares-managed-challenge)).

Para o modelo de correlação, veja [Fingerprinting de navegador](../deep-dive/fingerprinting/index.md) e [Técnicas de evasão](evasion-techniques.md).

## Incompatibilidade de locale/IP (Google) {#case-study-a-locale-mismatch-triggering-googles-captcha}

Aplicar um perfil dos EUA fez uma busca simples no Google retornar um captcha; remover a chamada `apply_fingerprint()` removeu o bloqueio. O perfil passou em todos os sites dedicados de fingerprinting, então o gatilho era específico do Google.

O perfil declarava uma identidade dos EUA (`locale.languages = ['en-US', 'en']`) numa máquina por trás de um IP brasileiro com um idioma de sistema operacional brasileiro. O Google cruza o header `Accept-Language` e os Client Hints com o país do IP. `en-US` a partir de um IP de São Paulo é uma combinação incomum, e os headers da requisição estavam inconsistentes com os outros sinais, derrubando a pontuação de confiança abaixo do limiar do captcha.

O campo `locale` controla:

- o header HTTP `Accept-Language` enviado em toda requisição,
- `navigator.language` e `navigator.languages`,
- os padrões de formatação do `Intl` (datas, números, moeda).

Todos os três são lidos por sistemas anti-abuso e têm que concordar com o fuso horário e o IP. Definir um locale brasileiro (combinando com o IP) removeu o bloqueio sem nenhuma outra mudança.

<p align="center">
  <img src="/docs/resources/images/fingerprint-inconsistent-captcha.png" alt="Google servindo um captcha porque o locale dos EUA do fingerprint injetado contradiz o IP de saída brasileiro" width="720" />
</p>
<p align="center"><sub>Locale dos EUA sobre um IP brasileiro: o Google retorna um captcha.</sub></p>

## Incompatibilidade de versão do Chrome (Cloudflare Turnstile) {#case-study-a-chrome-version-mismatch-triggering-cloudflares-challenge}

Para combinar a interação do [Cloudflare Turnstile](captcha-bypass.md) com um fingerprint, a versão do Chrome anunciada tem que corresponder ao binário real. Esta é a causa mais comum de falha do Turnstile com um fingerprint aplicado.

Aplicar o perfil `macos_m3_new_york` fez o Turnstile falhar até em headful: a página ficou presa no interstício "Just a moment…", e remover a chamada `apply_fingerprint()` fez ele passar. O perfil fixava o Chrome 145 no User-Agent enquanto o binário era o Chrome 151; `apply_fingerprint()` definiu `navigator.userAgent`, `Sec-CH-UA` e `navigator.userAgentData` para 145 enquanto o handshake TLS/HTTP2 e o motor permaneciam em 151. Uma bisseção de variável única confirmou: mudar apenas a major anunciada de 145 para 151 transformou toda falha em aprovação.

Duas camadas reportam a versão real e não podem ser sobrescritas através do CDP:

- O fingerprint TLS (JA3/JA4) e o frame `SETTINGS` do HTTP/2, produzidos pelo binário real antes de qualquer JavaScript rodar.
- A superfície do motor JavaScript (APIs disponíveis e seu comportamento), que reflete a build real do V8/Blink.

O managed challenge do Cloudflare compara a versão anunciada (User-Agent + Client Hints) com a versão observada (handshake e motor). Um navegador real não anuncia uma versão que não está rodando, então 145 sobre um handshake 151 é uma inconsistência e o interstício não se limpa.

Leia a versão do binário e combine o User-Agent do perfil com ela:

```python
async with Chrome() as browser:
    tab = await browser.start()

    version = await browser.get_version()
    print(version['product'])  # ex. 'Chrome/151.0.7922.137'
```

Em `examples/fingerprints.py`, `CHROME_DESKTOP` e `CHROME_MOBILE` definem a versão no User-Agent de cada perfil. Defina-os para a major do binário (a build completa alimenta `Sec-CH-UA-Full-Version-List`; `navigator.userAgent` é reduzido a `Chrome/<MAJOR>.0.0.0`). Atualize-os quando o Chrome atualizar.

## Incompatibilidade de sistema operacional (Cloudflare) {#case-study-an-os-mismatch-triggering-cloudflares-managed-challenge}

Com a versão do Chrome alinhada, um segundo perfil ainda falhou. Neste host (Apple Silicon, Chrome 151, IP brasileiro), `macos_m3_new_york` passa no Cloudflare e `windows11_rtx3060_nyc` falha. As versões combinam (ambas 151), e o perfil que falha é o que é geograficamente consistente com o IP, então nem a versão nem o locale são a causa. A diferença é o sistema operacional anunciado.

Uma bisseção de variável única do perfil que passa em direção ao que falha rastreou apenas o sistema operacional no User-Agent:

- User-Agent/platform de Windows para macOS no perfil que falha: passa.
- User-Agent/platform de macOS para Windows no perfil que passa: falha.
- Um User-Agent de Linux: falha.
- GPU/WebGL (renderer, params, extensões), canvas, fontes, tela, hardware, áudio, vozes, geo, locale: nenhum efeito.

Qualquer sistema operacional que não seja macOS falha neste host macOS. Um perfil de macOS anunciando uma GPU NVIDIA passa; um perfil de Windows anunciando a GPU Apple real falha.

Medição por camada, ambos os perfis, mesmo Chrome:

- TCP/IP: o servidor observa o mesmo TTL inicial de 64 (macOS/Unix) para ambos os perfis; um host Windows emite 128. Não alcançável através do CDP.
- TLS (JA3/JA4): varia por conexão (o toggle de extensão de padding do Chrome); a baseline sem fingerprint produz ambas as variantes. Não codifica o sistema operacional.
- HTTP/2 (Akamai): idêntico entre os perfis. Não codifica o sistema operacional.
- Client Hints: totalmente sobrescritos para o sistema operacional anunciado (o Windows reporta `architecture` `x86`, sem vazamento de `arm`).
- Canvas/WebGL: o hash da imagem renderizada é idêntico entre os perfis (pixels da GPU Apple real em ambos). Não é o diferenciador.

Tudo o que `apply_fingerprint()` controla reporta Windows; a stack TCP/IP do kernel reporta macOS. O managed challenge do Cloudflare compara o sistema operacional anunciado com a assinatura passiva da stack e mantém o interstício quando eles discordam.

O TTL, o window scaling e a ordem das opções TCP vêm do kernel do host, não do navegador, e nenhum override de CDP ou JavaScript os alcança. A renderização de GPU e as métricas de texto (CoreText no macOS) também são do host. Clientes que forjam TLS (curl_cffi, tls-client) não ajudam aqui: a falha não está no TLS, e eles ainda usam a stack TCP/IP do kernel do host.

Para passar, combine o sistema operacional do perfil (e a família de GPU) com o host: um perfil de macOS neste Mac, um perfil de Windows num host Windows. Um proxy de encaminhamento (SOCKS5/HTTP CONNECT) reorigina a conexão TCP a partir do kernel do proxy, então o sistema operacional observado passa a ser o do host do proxy; um perfil de Windows então exige um proxy rodando em Windows (um proxy Linux dá uma assinatura de Linux, ainda inconsistente com um User-Agent de Windows).

## Múltiplos fingerprints entre contextos {#multiple-fingerprints-across-contexts}

Service e shared workers são compartilhados entre todas as abas de um contexto de navegador, então um contexto guarda uma única identidade. Aplicar um fingerprint diferente a um contexto que já tem um levanta `FingerprintContextConflict`:

```python
from pydoll.exceptions import FingerprintContextConflict

# Mesmo contexto, dois fingerprints diferentes -> conflito
tab_a = await browser.start()
await tab_a.apply_fingerprint(FINGERPRINTS['windows11_rtx3060_nyc'])

tab_b = await browser.new_tab()               # mesmo contexto (padrão)
try:
    await tab_b.apply_fingerprint(FINGERPRINTS['macos_m3_new_york'])
except FingerprintContextConflict:
    print('One context holds one identity.')
```

Para rodar fingerprints diferentes simultaneamente, use um contexto de navegador separado por identidade:

```python
ctx_id = await browser.create_browser_context()
tab_us = await browser.start()
tab_br = await browser.new_tab(browser_context_id=ctx_id)

await tab_us.apply_fingerprint(FINGERPRINTS['windows11_rtx3060_nyc'])
await tab_br.apply_fingerprint(FINGERPRINTS['android_s24_ultra_sao_paulo'])
```

!!! warning "Telas em headless são globais do navegador"
    No modo headless, a tela virtual é compartilhada por todo o processo do navegador, não por contexto. Dois perfis com geometria de tela diferente (como os perfis Windows e Android acima) entram em conflito: a página principal de cada contexto continua correta, mas seus iframes cross-origin leem a última tela aplicada. Rode cada identidade com tela distinta em um processo de navegador separado.

Veja [Contextos de navegador](../guides/browser-contexts.md) para entender como os contextos isolados funcionam.

## Fornecendo seus próprios perfis {#bring-your-own-fingerprints}

O Pydoll não gera nem inclui fingerprints. Os perfis em `examples/fingerprints.py` são uma referência para a coerência que um perfil exige e para o formato de `FingerprintConfig`; eles não são um catálogo para implantar como está.

Um perfil tem que combinar com o seu ambiente:

- o binário do Chrome em uso (a camada de rede é autêntica e não pode ser sobrescrita), e
- a geografia do IP de saída (locale, fuso horário, geolocalização).

Um perfil público reutilizado amplamente se torna uma assinatura compartilhada em vez de um disfarce.

## Relacionados

- [Técnicas de evasão](evasion-techniques.md): consistência do User-Agent, idioma, proteção contra vazamento de WebRTC e o que o Pydoll te dá de graça.
- [Fingerprinting de navegador](../deep-dive/fingerprinting/browser-fingerprinting.md): a superfície de detecção (canvas, WebGL, navigator, fontes) que esta página sobrescreve.
- [Fingerprinting de rede](../deep-dive/fingerprinting/network-fingerprinting.md): a camada TLS/TCP/HTTP2 que a injeção não alcança.
- [Contextos de navegador](../guides/browser-contexts.md): rode uma identidade por contexto.
- [Proxies](../guides/proxies.md): combine o IP de saída com a geografia do perfil.
