# Injeção de Fingerprint

`tab.apply_fingerprint()` sobrescreve os sinais de identidade do navegador que os scripts de fingerprinting leem: User-Agent e Client Hints, propriedades do `navigator`, WebGL, métricas de tela, fontes, áudio, fuso horário e locale. Os valores sobrescritos precisam permanecer consistentes entre si e com as camadas que o `apply_fingerprint()` não controla (veja [Consistência entre camadas](#consistency-is-the-whole-game)). Um fingerprint inconsistente é mais detectável do que um navegador não modificado.

Isso é substituição de identidade, não anonimato: não muda o fingerprint da camada de rede nem o IP de saída.

## Início Rápido

Chame `apply_fingerprint()` antes da primeira navegação. As sobrescritas em JavaScript são registradas com `Page.addScriptToEvaluateOnNewDocument`, então só valem para documentos carregados após a chamada.

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

`FingerprintConfig` (de `pydoll.protocol.fingerprint.types`) é um dicionário tipado. Apenas os campos presentes são sobrescritos; o resto mantém os valores reais do navegador. Os perfis em `examples/fingerprints.py` são referências completas e internamente consistentes do formato do config (veja [Fornecendo seus próprios perfis](#bring-your-own-fingerprints)).

## Checklist

Regras para um perfil que não é detectado. A maioria descreve uma camada que o `apply_fingerprint()` não controla, então o perfil tem que ser escolhido para bater com ela, não para brigar com ela.

- SO do perfil = SO do host. Não rode um perfil Windows em macOS nem o contrário; o stack TCP/IP do kernel e a renderização de GPU/texto expõem o SO real em camadas que o CDP não alcança ([Incompatibilidade de SO](#case-study-an-os-mismatch-triggering-cloudflares-managed-challenge)).
- Versão do Chrome no User-Agent = versão do binário real. Mantenha `CHROME_DESKTOP` / `CHROME_MOBILE` iguais à major de `browser.get_version()`, e atualize a cada upgrade do Chrome ([Incompatibilidade de versão do Chrome](#case-study-a-chrome-version-mismatch-triggering-cloudflares-challenge)).
- Locale, fuso horário e geolocalização = país do IP de saída. `Accept-Language` e fuso horário são cruzados com o IP ([Incompatibilidade de locale/IP](#case-study-a-locale-mismatch-triggering-googles-captcha)).
- Vendor/renderer do WebGL = família de GPU do host (renderer Apple em hardware Apple, e assim por diante). Os pixels renderizados vêm da GPU real e não podem ser forjados.
- Aplique o fingerprint antes da primeira navegação.
- Uma identidade por contexto de navegador; use contextos separados para identidades diferentes ([Múltiplos fingerprints entre contextos](#multiple-fingerprints-across-contexts)).
- Não combine a opção `--user-agent` com `apply_fingerprint()`; o fingerprint é o dono do User-Agent.
- Use um IP residencial limpo. A injeção não muda a reputação do IP.

## Sobrescritas

As sobrescritas são aplicadas por dois mecanismos.

### Sobrescritas via CDP

Sinais que o Chrome consegue sobrescrever sozinho são definidos pelo domínio `Emulation` do DevTools Protocol. O navegador aplica isso abaixo da camada JavaScript, então o getter que um script de detecção lê continua sendo o nativo e não há wrapper JavaScript para inspecionar. Quando existe uma sobrescrita via CDP para um sinal, ela é usada no lugar de uma sobrescrita em JavaScript.

| Sinal | Comando CDP |
|--------|-------------|
| User-Agent, `navigator.platform` / `vendor` / `appVersion`, Client Hints (`Sec-CH-UA*`) | `Emulation.setUserAgentOverride` |
| Fuso horário (`Intl`, `Date`) | `Emulation.setTimezoneOverride` |
| Geolocalização | `Emulation.setGeolocationOverride` |
| Tamanho da tela, `devicePixelRatio`, viewport, orientação | `Emulation.setDeviceMetricsOverride` |
| Locale (formatação `Intl`) | `Emulation.setLocaleOverride` |
| `navigator.hardwareConcurrency` | `Emulation.setHardwareConcurrencyOverride` |

`hardwareConcurrency` ilustra a diferença: um getter em JavaScript é detectável (veja abaixo), enquanto `Emulation.setHardwareConcurrencyOverride` muda o valor com o getter permanecendo nativo.

### Sobrescritas via JavaScript

Sinais que o CDP não alcança são definidos por um script injetado antes de qualquer script da página em cada novo documento, e reaplicado nos Web Workers. Isso cobre:

- Extras do `navigator`: `deviceMemory`, `maxTouchPoints`, `doNotTrack`, `pdfViewerEnabled`
- `screen.availWidth` / `availHeight` (o CDP força esses iguais ao tamanho da tela, um sinal de headless), `colorDepth`, `pixelDepth`, e `window.outerWidth` / `outerHeight`
- Valores de vendor, renderer, parâmetros e precisão do WebGL
- `navigator.mediaDevices`, Web Audio, vozes do `speechSynthesis`
- Disponibilidade de fontes (`document.fonts.check` / `FontFace.load`)
- `navigator.connection` (Network Information API)
- Resultados de consulta de `navigator.permissions`
- Política de tratamento de IP do WebRTC

O canvas e a leitura do WebGL não são modificados. Sistemas de detecção pedem o fingerprint repetidamente, então um valor que muda entre leituras é, por si só, um sinal de automação; o canvas de um Chrome real é estável. As strings de vendor e renderer do WebGL são sobrescritas para bater com a plataforma declarada, mas os pixels renderizados são deixados intactos.

## Detecção de sobrescritas em JavaScript

Scripts de fingerprinting não apenas leem o valor de uma propriedade; eles inspecionam como ela foi definida e se os objetos ao redor foram modificados. Três verificações são padrão, e uma sobrescrita ingênua falha nas três. O CreepJS é a implementação de referência.

Propriedade própria vs accessor no prototype. Em um navegador real, `hardwareConcurrency` é um accessor em `Navigator.prototype`, não uma propriedade de dados na instância `navigator`:

```javascript
Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
// navigator.hasOwnProperty('hardwareConcurrency') === true   (Chrome real: false)
```

`Object.getOwnPropertyNames(navigator)` ou uma comparação com o prototype expõe a propriedade própria adicionada.

`toString` do getter. Um getter nativo se reporta como código nativo:

```javascript
Object.getOwnPropertyDescriptor(Navigator.prototype, 'hardwareConcurrency').get.toString();
// real:  "function get hardwareConcurrency() { [native code] }"
// ingênuo: "() => 8"
```

`Function.prototype.toString` retorna o código-fonte JavaScript de um getter escrito à mão, então uma única chamada o expõe.

Leituras entre realms. Um `iframe` de mesma origem ou um Web Worker é um realm novo cujos `navigator` e prototypes não foram tocados por um hook instalado apenas no realm principal. O `WorkerNavigator` de um worker reportando o valor real enquanto a página reporta a sobrescrita é uma contradição.

### Como o pydoll evita esses sinais

- Os getters são definidos no prototype (`Navigator.prototype`, `Screen.prototype`), então a instância não ganha propriedades próprias.
- Getters e métodos modificados se reportam como nativos sob `toString`, e o patch no próprio `toString` não vira um novo sinal.
- As sobrescritas são reaplicadas em workers dedicados, compartilhados e de serviço, então a página e os realms que ela cria reportam os mesmos valores.

É por isso que um perfil injetado passa nas verificações de detecção de mentira, prototype, workers e fontes do CreepJS, em vez de apenas mudar os valores visíveis.

## Modo headless

O Chrome headless expõe sinais que um navegador com interface não expõe, e é por isso que verificações de bot frequentemente falhavam antes da injeção de fingerprint:

- Renderer do WebGL. Sem passagem de GPU, o Chrome headless renderiza por um rasterizador de software (SwiftShader). `UNMASKED_RENDERER_WEBGL` reporta `ANGLE (Google, Vulkan 1.3.0 (SwiftShader))` ou `Google SwiftShader` em vez de uma string de GPU real como `ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11)` ou `Apple M3`. Sobrescrever só a string é insuficiente: a superfície de capacidade da GPU (extensões suportadas, precisão de shader, tamanho máximo de textura) continua refletindo o rasterizador de software e é cruzada com a GPU declarada.
- `navigator.plugins` / `mimeTypes` vazios, enquanto o Chrome com interface expõe as entradas do visualizador de PDF embutido.
- `screen.availWidth` / `availHeight` iguais ao tamanho total da tela (sem a folga da barra de tarefas ou dock), e uma janela externa zerada.
- Dispositivos de mídia ausentes, e diferenças de rasterização de fontes/áudio em relação a uma máquina com tela.
- No antigo `--headless`, um token `HeadlessChrome` no User-Agent (removido no `--headless=new`; os sinais de renderização acima permanecem).

O `apply_fingerprint()` sobrescreve o vendor/renderer do WebGL e a superfície de parâmetros/precisão, reporta `availWidth`/`availHeight` com uma folga de barra de tarefas, restaura dispositivos de mídia e fontes, e fixa o User-Agent via CDP. Com um perfil aplicado, os sites de detecção testados reportam o navegador como sendo com interface, e o headless deixa de mudar o resultado. É isso que permite uma busca no Google rodar em modo headless:

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.constants import Key

from examples.fingerprints import FINGERPRINTS

async def headless_google_search():
    async with Chrome() as browser:
        tab = await browser.start(headless=True)

        # Neutraliza os sinais de renderização headless antes da primeira navegação.
        await tab.apply_fingerprint(FINGERPRINTS['windows11_rtx3060_nyc'])

        await tab.go_to('https://www.google.com')
        search_box = await tab.find(tag_name='textarea', name='q')
        await search_box.type_text('pydoll', humanize=True)
        await tab.keyboard.press(Key.ENTER)
        await asyncio.sleep(3)
        print('Busca no Google concluída em modo headless.')

asyncio.run(headless_google_search())
```

A injeção de fingerprint remove apenas os sinais de renderização do headless. Ela não muda o IP: um IP de datacenter com reputação ruim continua sendo desafiado em headless e com interface igualmente (veja [O que determina o sucesso](behavioral-captcha-bypass.md#what-determines-success)).

Para o Cloudflare Turnstile, a falha mais comum com um fingerprint aplicado é uma incompatibilidade de versão do Chrome, não o headless (veja [Incompatibilidade de versão do Chrome](#case-study-a-chrome-version-mismatch-triggering-cloudflares-challenge)). O Turnstile em headless ainda está sendo validado; prefira rodar com interface para ele.

## Consistência entre camadas {#consistency-is-the-whole-game}

Sistemas anti-bot correlacionam sinais entre camadas. O `apply_fingerprint()` mantém consistentes as camadas que ele controla, mas três camadas estão fora do alcance do CDP e têm que ser batidas separadamente:

1. Versão do binário do Chrome. O fingerprint da camada de rede (TLS JA3/JA4, `SETTINGS` do HTTP/2) e a versão do engine JavaScript vêm do binário real e não podem ser sobrescritos. Um perfil declarando Chrome 145 tem que rodar em um binário Chrome 145 (veja [Incompatibilidade de versão do Chrome](#case-study-a-chrome-version-mismatch-triggering-cloudflares-challenge)).
2. Geografia do IP de saída. O header `Accept-Language` e o fuso horário são cruzados com o país do IP. Uma identidade dos EUA em um IP brasileiro é uma contradição (veja [Incompatibilidade de locale/IP](#case-study-a-locale-mismatch-triggering-googles-captcha)).
3. SO do host. O stack TCP/IP do kernel é um fingerprint passivo de SO (TTL inicial 64 no macOS/Linux, 128 no Windows), e a renderização de GPU/texto também reflete o SO real. Nenhum dos dois é alcançável via CDP. Um perfil Windows em um Mac é uma contradição de SO (veja [Incompatibilidade de SO](#case-study-an-os-mismatch-triggering-cloudflares-managed-challenge)).

Para o modelo de correlação, veja [Fingerprinting do Navegador](../../deep-dive/fingerprinting/index.md) e [Consistência de Fuso Horário e Locale](../../deep-dive/fingerprinting/evasion-techniques.md).

## Incompatibilidade de locale/IP (Google) {#case-study-a-locale-mismatch-triggering-googles-captcha}

Aplicar um perfil dos EUA fez uma busca simples no Google retornar um captcha; remover a chamada `apply_fingerprint()` removeu o bloqueio. O perfil passava em todos os sites dedicados de fingerprinting, então o gatilho era específico do Google.

O perfil declarava uma identidade dos EUA (`locale.languages = ['en-US', 'en']`) em uma máquina atrás de um IP brasileiro com idioma de sistema brasileiro. O Google cruza o header `Accept-Language` e os Client Hints com o país do IP. `en-US` vindo de um IP de São Paulo é uma combinação incomum, e os headers da requisição estavam inconsistentes com os outros sinais, derrubando o score de confiança abaixo do limiar de captcha.

O campo `locale` dirige:

- o header HTTP `Accept-Language` enviado em toda requisição,
- `navigator.language` e `navigator.languages`,
- os padrões de formatação do `Intl` (datas, números, moeda).

Todos os três são lidos por sistemas anti-abuso e têm que concordar com o fuso horário e o IP. Definir um locale brasileiro (batendo com o IP) removeu o bloqueio sem nenhuma outra mudança.

<p align="center">
  <img src="../../../../resources/images/fingerprint-inconsistent-captcha.png" alt="Google servindo um captcha porque o locale dos EUA do fingerprint injetado contradiz o IP de saída brasileiro" width="720" />
</p>
<p align="center"><sub>Locale dos EUA sobre um IP brasileiro: o Google retorna um captcha.</sub></p>

## Incompatibilidade de versão do Chrome (Cloudflare Turnstile) {#case-study-a-chrome-version-mismatch-triggering-cloudflares-challenge}

Para combinar a interação com o [Cloudflare Turnstile](behavioral-captcha-bypass.md) com um fingerprint, a versão declarada do Chrome tem que bater com o binário real. Essa é a causa mais comum de falha do Turnstile com um fingerprint aplicado.

Aplicar o perfil `macos_m3_new_york` fazia o Turnstile falhar mesmo com interface: a página ficava na tela intermediária "Just a moment…", e remover a chamada `apply_fingerprint()` fazia passar. O perfil fixava Chrome 145 no User-Agent enquanto o binário era Chrome 151; o `apply_fingerprint()` definia `navigator.userAgent`, `Sec-CH-UA` e `navigator.userAgentData` como 145 enquanto o handshake TLS/HTTP2 e o engine permaneciam 151. Uma bissecção de variável única confirmou: trocar só a major declarada de 145 para 151 transformou toda falha em aprovação.

Duas camadas reportam a versão real e não podem ser sobrescritas via CDP:

- O fingerprint TLS (JA3/JA4) e o frame `SETTINGS` do HTTP/2, produzidos pelo binário real antes de qualquer JavaScript rodar.
- A superfície do engine JavaScript (APIs disponíveis e seu comportamento), que reflete a build real do V8/Blink.

O desafio gerenciado do Cloudflare compara a versão declarada (User-Agent + Client Hints) com a versão observada (handshake e engine). Um navegador real não declara uma versão que não está rodando, então 145 sobre um handshake 151 é uma inconsistência e a tela intermediária não libera.

Leia a versão do binário e faça o User-Agent do perfil bater com ela:

```python
async with Chrome() as browser:
    tab = await browser.start()

    version = await browser.get_version()
    print(version['product'])  # ex.: 'Chrome/151.0.7922.137'
```

Em `examples/fingerprints.py`, `CHROME_DESKTOP` e `CHROME_MOBILE` definem a versão no User-Agent de cada perfil. Defina-as para a major do binário (a build completa alimenta o `Sec-CH-UA-Full-Version-List`; o `navigator.userAgent` é reduzido para `Chrome/<MAJOR>.0.0.0`). Atualize-as quando o Chrome atualizar.

## Incompatibilidade de SO (Cloudflare) {#case-study-an-os-mismatch-triggering-cloudflares-managed-challenge}

Com a versão do Chrome alinhada, um segundo perfil ainda falhava. Neste host (Apple Silicon, Chrome 151, IP brasileiro), o `macos_m3_new_york` passa no Cloudflare e o `windows11_rtx3060_nyc` falha. As versões batem (ambas 151), e o perfil que falha é o que é geograficamente consistente com o IP, então nem a versão nem o locale são a causa. A diferença é o SO declarado.

Uma bissecção de variável única do perfil que passa em direção ao que falha acompanhou apenas o SO no User-Agent:

- User-Agent/platform de Windows para macOS no perfil que falha: passa.
- User-Agent/platform de macOS para Windows no perfil que passa: falha.
- Um User-Agent de Linux: falha.
- GPU/WebGL (renderer, params, extensões), canvas, fontes, tela, hardware, áudio, vozes, geo, locale: sem efeito.

Qualquer SO diferente de macOS falha neste host macOS. Um perfil macOS declarando uma GPU NVIDIA passa; um perfil Windows declarando a GPU Apple real falha.

Medição por camada, ambos os perfis, mesmo Chrome:

- TCP/IP: o servidor observa o mesmo TTL inicial de 64 (macOS/Unix) para ambos os perfis; um host Windows emite 128. Não alcançável via CDP.
- TLS (JA3/JA4): varia por conexão (o toggle da extensão de padding do Chrome); o baseline sem fingerprint produz as duas variantes. Não codifica o SO.
- HTTP/2 (Akamai): idêntico entre os perfis. Não codifica o SO.
- Client Hints: totalmente sobrescritos para o SO declarado (Windows reporta `architecture` `x86`, sem vazar `arm`).
- Canvas/WebGL: o hash da imagem renderizada é idêntico entre os perfis (pixels da GPU Apple real nos dois). Não é o diferenciador.

Tudo que o `apply_fingerprint()` controla reporta Windows; o stack TCP/IP do kernel reporta macOS. O desafio gerenciado do Cloudflare compara o SO declarado com a assinatura passiva do stack e mantém a tela intermediária quando eles não batem.

O TTL, o window scaling e a ordem das opções de TCP vêm do kernel do host, não do navegador, e nenhuma sobrescrita de CDP ou JavaScript os alcança. A renderização de GPU e as métricas de texto (CoreText no macOS) também são do host. Clientes que forjam TLS (curl_cffi, tls-client) não ajudam aqui: a falha não é no TLS, e eles ainda usam o stack TCP/IP do kernel do host.

Para passar, faça o SO do perfil (e a família de GPU) bater com o host: um perfil macOS neste Mac, um perfil Windows em um host Windows. Um proxy de encaminhamento (SOCKS5/HTTP CONNECT) reorigina a conexão TCP a partir do kernel do proxy, então o SO observado passa a ser o do host do proxy; um perfil Windows então exige um proxy rodando em Windows (um proxy Linux dá uma assinatura Linux, ainda inconsistente com um User-Agent Windows).

## Múltiplos fingerprints entre contextos {#multiple-fingerprints-across-contexts}

Workers de serviço e compartilhados são compartilhados entre todas as abas de um contexto de navegador, então um contexto carrega uma única identidade. Aplicar um fingerprint diferente a um contexto que já tem um lança `FingerprintContextConflict`:

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

Para rodar fingerprints diferentes ao mesmo tempo, use um contexto de navegador separado por identidade:

```python
ctx_id = await browser.create_browser_context()
tab_us = await browser.start()
tab_br = await browser.new_tab(browser_context_id=ctx_id)

await tab_us.apply_fingerprint(FINGERPRINTS['windows11_rtx3060_nyc'])
await tab_br.apply_fingerprint(FINGERPRINTS['android_s24_ultra_sao_paulo'])
```

Veja [Contextos de Navegador](../browser-management/contexts.md) para como contextos isolados funcionam.

## Fornecendo seus próprios perfis {#bring-your-own-fingerprints}

O pydoll não gera nem distribui fingerprints. Os perfis em `examples/fingerprints.py` são uma referência da coerência que um perfil exige e do formato do `FingerprintConfig`; não são um catálogo para usar como está.

Um perfil tem que bater com o ambiente:

- o binário do Chrome em uso (a camada de rede é autêntica e não pode ser sobrescrita), e
- a geografia do IP de saída (locale, fuso horário, geolocalização).

Um perfil público reutilizado amplamente vira uma assinatura compartilhada em vez de um disfarce.

## Veja Também

- [Fingerprinting do Navegador](../../deep-dive/fingerprinting/index.md) - detecção camada por camada
- [Técnicas de Evasão](../../deep-dive/fingerprinting/evasion-techniques.md) - consistência de fuso horário/locale, consistência de User-Agent, proteção contra vazamento de WebRTC
- [Fingerprinting do Navegador (superfície de detecção)](../../deep-dive/fingerprinting/browser-fingerprinting.md) - canvas, WebGL, navigator e detecção de fontes
- [Contextos de Navegador](../browser-management/contexts.md) - identidades isoladas
- [Configuração de Proxy](../configuration/proxy.md) - alinhando o IP de saída ao perfil
