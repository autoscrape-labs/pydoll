# Injeção de fingerprint

## Introdução

`tab.apply_fingerprint()` dá ao navegador uma nova identidade. Ele sobrescreve os sinais que os scripts de fingerprinting leem, User-Agent e Client Hints, `navigator`, WebGL e WebGPU, métricas de tela, fontes, áudio, permissões, fuso horário e locale, na página, nos seus workers (incluindo os aninhados) e nos seus cross-origin iframes, antes da primeira navegação. Você não monta um fingerprint na mão nem faz patch de `navigator`; você passa um perfil e o Pydoll o aplica de forma coerente, pelos comandos de override do próprio navegador onde existe um e por JavaScript reforçado só onde não existe nenhum.

O ganho é concreto. Com um perfil compatível, o Chrome headless deixa de ser sinalizado como bot na hora e passa a ler como um desktop comum, o suficiente para [passar o desafio gerenciado do Cloudflare em modo headless](#clear-cloudflares-challenge-headless).

Um limite honesto de saída: isto é substituição de identidade, não anonimato. Não muda o seu IP de saída nem o fingerprint da camada de rede, e um perfil inconsistente é mais detectável do que um navegador sem modificações. Fazer o perfil *combinar* com a sua máquina e o seu IP é o trabalho todo, e [as regras abaixo](#making-a-profile-pass) são esse checklist.

!!! warning "Nada disto é garantia"
    Tudo nesta página, e nos deep dives para os quais ela aponta, descreve o que um detector *pode* ler: as checagens que a literatura e os agentes de engenharia reversa documentam. Quais delas um site específico roda, e quanto cada uma pesa, é segredo daquele site. Um perfil mínimo (User-Agent, locale e fuso horário combinando com o host e o IP) passa em muitos alvos sozinho, e uma pequena inconsistência residual pode nunca ser lida. Comece simples, teste contra o site real e adicione campos só quando uma medição disser que um sinal específico é o que te bloqueia. Perseguir consistência total por si só é esforço que um alvo pode nunca recompensar.

**Você vai aprender**

- [Como aplicar um fingerprint](#quick-start)
- [Como ele passa o Cloudflare headless](#clear-cloudflares-challenge-headless)
- [Como provar que está funcionando](#prove-it-with-a-bot-score)
- [Como fazer um perfil passar](#making-a-profile-pass)
- [O que é nativo e o que é JavaScript](#native-first)
- [Como usar seus próprios perfis](#bring-your-own-profiles)
- [O que um container pode e não pode alegar](#containers)

## Quick start {#quick-start}

Chame `apply_fingerprint()` antes da primeira navegação. Só os campos presentes no perfil são sobrescritos; o resto mantém os valores reais do navegador.

```python
import asyncio

from pydoll.browser.chromium import Chrome

from examples.fingerprints import FINGERPRINTS

async def spoof_fingerprint():
    async with Chrome() as browser:
        tab = await browser.start()

        # Aplique antes da primeira navegação.
        await tab.apply_fingerprint(FINGERPRINTS['macos_m3_new_york'])

        await tab.go_to('https://abrahamjuliot.github.io/creepjs/')
        await asyncio.sleep(5)

asyncio.run(spoof_fingerprint())
```

!!! note "De onde vem `FINGERPRINTS`"
    O Pydoll não distribui perfis de fingerprint. `FINGERPRINTS` fica em `examples/fingerprints.py` no [repositório do pydoll](https://github.com/autoscrape-labs/pydoll), como perfis de referência para o formato `FingerprintConfig` (um typed dict de `pydoll.protocol.fingerprint.types`). Copie esse arquivo para o seu projeto e adapte cada perfil à sua máquina e ao seu IP, [as regras abaixo](#making-a-profile-pass) explicam por quê. Um perfil reusado como está é uma assinatura compartilhada, não um disfarce.

## Passar o desafio do Cloudflare headless {#clear-cloudflares-challenge-headless}

O Chrome headless normalmente falha em checagens de bot de cara: um renderizador WebGL por software, uma tela fixa de 800x600, listas de plugins vazias. Um perfil compatível neutraliza esses sinais de renderização, então uma sessão headless lê como headful. Com a identidade também replicada no cross-origin iframe do desafio (`cross_origin_iframes`, ligado por padrão), isso basta para passar o desafio gerenciado do Cloudflare, sem nenhum solver de captcha.

<p align="center">
  <img src="/docs/resources/images/cloudflare-headless-bypass.gif" alt="Pydoll em modo headless carregando um site protegido pelo Cloudflare e passando o desafio gerenciado com um fingerprint aplicado" width="760" />
</p>
<p align="center"><sub>Headless não tem janela visível; isto é o screencast do CDP dele. Com um fingerprint compatível, o desafio gerenciado passa.</sub></p>

```python
async with Chrome() as browser:
    tab = await browser.start(headless=True)

    # Combine o perfil com ESTE host e IP (veja as regras abaixo).
    await tab.apply_fingerprint(FINGERPRINTS['macos_m3_new_york'])

    await tab.go_to('https://a-site-behind-cloudflare.com')
    # O interstitial passa quando a identidade é coerente.
```

Duas condições fazem isso funcionar, ambas [nas regras abaixo](#making-a-profile-pass): o perfil precisa ser coerente (OS, versão do Chrome e locale todos combinando com o seu host e IP), e o IP precisa estar limpo. Um IP de datacenter com reputação ruim continua sendo desafiado em headless e headful igualmente. Num IP marginal, prefira headful, ou headful sob Xvfb.

Por baixo, o headless ainda tem um vazamento client-side que um cross-origin frame lê direto: o seu próprio `window.screen`. Sem o reshape, o frame lê a tela headless crua de 800x600 e contradiz a página; com ele, elas batem.

<iframe scrolling="no" src="/docs/resources/visuals/headless-screen-oopif.html" aria-label="Uma página headless e seu cross-origin iframe lendo cada um o window.screen; alternar o reshape vira o iframe da tela headless crua de 800x600 para bater com a página" style="width: 100%; height: 460px; border: 0;" loading="lazy"></iframe>

Para o detalhamento completo do que o desafio lê e por que a coerência passa, veja [O desafio gerenciado do Cloudflare](../deep-dive/fingerprinting/cloudflare-challenge.md).

## Provar com um bot score {#prove-it-with-a-bot-score}

Se um fingerprint ajuda ou atrapalha é mensurável. O [fingerprint-scan.com](https://fingerprint-scan.com/), feito pelo engenheiro por trás do blog antibot da Castle, reporta um **bot score** de 0 a 100, quanto menor, mais humano. O headless é a demonstração mais nítida: sem perfil, o Chrome headless pontua o máximo; um perfil compatível derruba para o nível do headful.

| Execução (mesmo Mac, Chrome 151) | Bot score |
|---|---|
| Headless, sem perfil | 100 / 100 |
| Headless, perfil macOS compatível | 15 / 100 |
| Headful, sem perfil | 15 / 100 |
| Headful, perfil macOS compatível | 15 / 100 |
| Headful, perfil Windows incompatível | 57 / 100 |

<p align="center">
  <img src="/docs/resources/images/fp-scan-headless-nofp.png" alt="fingerprint-scan.com reportando um bot score de 100/100 para o Chrome headless sem fingerprint" width="380" />
  <img src="/docs/resources/images/fp-scan-headless-mac.png" alt="fingerprint-scan.com reportando um bot score de 15/100 para o Chrome headless com um fingerprint macOS aplicado" width="380" />
</p>
<p align="center"><sub>Headless: 100/100 sem perfil, 15/100 com um perfil macOS compatível.</sub></p>

Duas coisas que isso prova. O perfil não deixa o navegador invisível: mesmo compatível, pontua 15, não 0 (o Chrome real sobre CDP já lê como humano, e fechar essa última lacuna é um ponto em aberto). E um perfil *incompatível* pontua pior do que perfil nenhum, a última linha pula para 57 porque um campo (o OS) contradiz o hardware por baixo. É exatamente por isso que essas regras existem.

!!! warning "Esses números são um retrato"
    Uma máquina, um IP, uma build do Chrome, um momento. Os seus vão diferir e sites de detecção mudam a pontuação. Trate como direção (compatível fica baixo, incompatível pula), não como resultado garantido.

Para o método de auditoria completo, ler um sinal de volta e comparar realms, veja [Auditar um fingerprint](../deep-dive/fingerprinting/auditing.md).

## Fazer um perfil passar {#making-a-profile-pass}

Um perfil passa quando concorda com a máquina e o IP em que roda. A maioria destas regras descreve uma camada que `apply_fingerprint()` não alcança, então você combina com ela em vez de brigar. No fundo são todas a mesma regra: **coerência entre todas as camadas**.

### Combine o OS do perfil com o OS do host

A pilha TCP/IP do kernel e a renderização de texto do OS expõem o OS real em camadas que nenhum override alcança. Um perfil Windows num Mac é uma contradição na qual o Cloudflare barra, e a incompatibilidade que empurrou o bot score para 57 acima. Rode um perfil macOS no macOS, um perfil Windows no Windows. Um proxy de encaminhamento re-origina a conexão TCP a partir do kernel do proxy, então um perfil Windows passa a exigir um proxy rodando em Windows. Medição completa: [The OS must match the host](../deep-dive/fingerprinting/cloudflare-challenge.md#the-os-must-match-the-host).

### Combine a versão do Chrome com o seu binário

O handshake TLS e o motor JavaScript reportam a versão real do binário; o User-Agent é a única parte que `apply_fingerprint()` muda. Um perfil dizendo Chrome 145 num binário Chrome 151 é uma contradição, e a causa mais comum de falha no Turnstile com um fingerprint aplicado. Leia a versão do binário e mantenha o major de `CHROME_DESKTOP` / `CHROME_MOBILE` do perfil igual a ela, atualizando a cada upgrade do Chrome.

```python
version = await browser.get_version()
print(version['product'])  # ex.: 'Chrome/151.0.7922.137'
```

Detalhamento completo: [The Chrome version must match the binary](../deep-dive/fingerprinting/cloudflare-challenge.md#the-chrome-version-must-match-the-binary).

### Combine locale e fuso horário com o IP de saída {#match-locale-and-timezone-to-your-egress-ip}

`Accept-Language`, `navigator.languages` e o fuso horário são cruzados com o país do IP. Um perfil US atrás de um IP brasileiro fez uma busca simples no Google retornar um captcha; ajustar para um locale brasileiro, combinando com o IP, removeu o bloqueio sem nenhuma outra mudança.

<p align="center">
  <img src="/docs/resources/images/fingerprint-inconsistent-captcha.png" alt="Google servindo um captcha porque o locale US do fingerprint injetado contradiz o IP de saída brasileiro" width="640" />
</p>
<p align="center"><sub>Locale US sobre um IP brasileiro: o Google retorna um captcha.</sub></p>

### Cubra os cross-origin iframes

Deixe `cross_origin_iframes` ligado (o padrão) para que um frame de desafio ou captcha no próprio processo leia a identidade injetada, não a máquina real. Ele é escopado aos frames que de fato leem um fingerprint, então não deixa iframes de terceiros comuns mais lentos.

```python
# Padrão: a identidade também cobre cross-origin iframes.
await tab.apply_fingerprint(FINGERPRINTS['macos_m3_new_york'])

# Desligue para cobrir só a página de topo, frames same-origin e workers.
await tab.apply_fingerprint(FINGERPRINTS['macos_m3_new_york'], cross_origin_iframes=False)
```

Como a identidade chega a cada realm: [Workers and cross-origin iframes](../deep-dive/fingerprinting/execution-realms.md).

### Scripts de service worker e de worker aninhado {#service-worker-and-nested-worker-scripts}

Duas requisições são feitas pelo processo do navegador antes de existir qualquer target de worker: o fetch do script de um service worker e o fetch de um worker criado de dentro de outro worker. Nenhum override por sessão as alcança, então, sozinhas, elas saem com o User-Agent e o `Accept-Language` reais enquanto toda outra requisição carrega os do perfil, e um site que registra um service worker vê as duas identidades no servidor dele. O Pydoll fecha isso a partir da conexão do navegador: ele pausa apenas as requisições que o Chrome tipa como `Other` (esses dois fetches de script, favicons e afins; documentos, scripts, imagens e fetches da página nunca são pausados) com o domínio `Fetch` e reescreve os dois headers a partir do fingerprint registrado para o browser context da requisição. Medido no servidor de teste local, os dois scripts passam a chegar com a identidade do perfil, sem nenhuma flag de lançamento envolvida.

Se você também definir `--user-agent`, mantenha-o igual ao User-Agent reduzido do perfil (`Chrome/MAJOR.0.0.0`); um valor diferente registra um warning no log.

### Fixe os Client Hints que o User-Agent não consegue carregar

Desde a redução do User-Agent, a string é congelada (`Mac OS X 10_15_7`, `Android 10; K`, `Chrome/152.0.0.0`) enquanto o Chrome real continua reportando a versão verdadeira do OS, o modelo do dispositivo e o form factor em `Sec-CH-UA-Platform-Version`, `Sec-CH-UA-Model` e `navigator.userAgentData.getHighEntropyValues()`. O parser preenche padrões plausíveis por OS. Defina `client_hints` para fixar os valores exatos lidos do dispositivo que você está imitando: hosts Windows 11 reportam `'13.0.0'` para cima dependendo da build, um Galaxy S24 Ultra reporta `'SM-S928B'`. Leia-os numa máquina real com `navigator.userAgentData.getHighEntropyValues(['platformVersion', 'model'])` em vez de adivinhar.

```python
fingerprint = FingerprintConfig(
    user_agent=UA_WINDOWS,
    client_hints=ClientHintsFingerprint(platform_version='15.0.0'),
)
```

A brand greased (`"Not?A_Brand";v="24"`) e a ordem das três brands também não são texto livre. O Chromium calcula as duas a partir da versão major, então um detector consegue recalcular o `Sec-CH-UA` exato que um Chrome real daquele major envia. O Pydoll roda o mesmo algoritmo; você nunca escreve brands na mão.

### Combine as fontes que você alega com as fontes que você instala

A seção `fonts` cobre a sonda de presença via `FontFace.load()` (`document.fonts.check()` fica nativo: o Chrome real responde `true` para qualquer família, então forçar `false` ali é por si só uma denúncia). A sonda de fontes mais antiga não lê nenhuma das duas: ela mede a largura de um span de texto na família alegada contra um fallback, e o motor de layout responde com as fontes realmente instaladas. Num Mac, um perfil Windows mede Segoe UI e Calibri como ausentes e Menlo e Helvetica Neue como presentes, diga o perfil o que disser. Para passar nessa sonda, as fontes alegadas têm que estar instaladas no host, e `available_fonts` tem que listar o que está instalado, nada mais.

### Um fingerprint por browser context {#one-fingerprint-per-browser-context}

Service e shared workers são compartilhados dentro de um browser context, então um context guarda uma identidade. Aplicar um segundo fingerprint no mesmo context levanta `FingerprintContextConflict`. Rode identidades diferentes em contexts separados.

```python
ctx_id = await browser.create_browser_context()
tab_us = await browser.start()
tab_br = await browser.new_tab(browser_context_id=ctx_id)

await tab_us.apply_fingerprint(FINGERPRINTS['windows11_rtx3060_nyc'])
await tab_br.apply_fingerprint(FINGERPRINTS['android_s24_ultra_sao_paulo'])
```

Veja [Browser contexts](../guides/browser-contexts.md).

Algumas regras menores completam: aplique o fingerprint antes da primeira navegação; se você definir a opção `--user-agent`, mantenha-a igual à do perfil (o perfil é dono do User-Agent); combine o vendor/renderer do WebGL, o adapter do WebGPU e o color-gamut com a GPU e o display do host, capturando os limites e as features do WebGPU de um dispositivo real daquela classe; use um IP residencial limpo. Sobre por que alguns sinais podem ser sobrescritos e outros não dá para forjar, veja [The limits of spoofing](../deep-dive/fingerprinting/spoofing-limits.md).

### Modo headless {#headless-mode}

O Chrome headless tem uma única tela virtual fixa (800x600, sem área de trabalho) e uma janela sem chrome. A seção `screen` de um perfil remodela as duas de forma nativa: `Emulation.updateScreen` define o tamanho da tela virtual, a área de trabalho (`availTop`, `availHeight`), a profundidade de cor e o pixel ratio inteiro para todo frame do navegador, cross-origin iframes incluídos, e `Browser.setWindowBounds` dimensiona a janela para `outer_width` x `outer_height`, então `outerWidth`, `innerWidth` e todo valor de `screen.*` vêm do próprio Chrome, sem nenhum getter JavaScript por trás. Um `device_pixel_ratio` fracionário (escala de display do Windows) é o único valor que a tela virtual não comporta; ele é aplicado à página via `setDeviceMetricsOverride` e arredondado para os cross-origin iframes.

Em modo headful a tela real é real, então `screen.width`, `screen.height` e o pixel ratio são sobrescritos via `setDeviceMetricsOverride`, a janela é redimensionada para `outer_*`, e só os extras da área de trabalho (`availHeight`, `availTop`, `colorDepth`) mantêm um getter JavaScript.

### Containers e servidores sem GPU {#containers}

Um perfil muda o que o navegador reporta, não o que o host computa. Num container sem GPU, uma alegação de placa dedicada é contradita por uma checagem de uma linha (o contexto sem caveat é recusado, o hash de renderização é o do SwiftShader, o adapter WebGPU é `null` sem flags), então conte uma história de renderização por software em vez disso, faça as APIs existirem com `--enable-unsafe-swiftshader` e `--use-fake-device-for-media-stream`, instale as fontes do OS alegado e fique atrás de uma saída residencial. O Xvfb remove os sinais de display, não os de GPU. Por quê, e em que ordem isso importa para um alvo específico: [GPU, containers e o que um perfil não alcança](../deep-dive/fingerprinting/gpu-and-containers.md).

## Nativo primeiro, JavaScript por último {#native-first}

Todo sinal que o Chrome consegue sobrescrever pelo próprio protocolo é aplicado ali, e o JavaScript do perfil nunca o toca: o User-Agent, `navigator.platform` / `appVersion` / `vendor`, `navigator.language` e `languages` (todos definidos por `Emulation.setUserAgentOverride`), os Client Hints, `hardwareConcurrency`, fuso horário, geolocalização, locale, as media features CSS, eventos de toque, permissões (`Browser.setPermission`, então `navigator.permissions.query()` retorna um `PermissionStatus` genuíno e `Notification.permission` concorda com ele) e, em headless, a tela inteira.

Um override nativo não tem função nenhuma por trás. Isso importa para a única checagem que um getter JavaScript não consegue passar: chame o getter sobre um objeto estranho e leia a stack. Um accessor nativo lança `Illegal invocation` sem nenhum frame próprio; um accessor JavaScript lança o mesmo erro com uma linha extra `at get userAgent`. Fornecedores de detecção descrevem exatamente essa sonda. Mover a identidade para overrides nativos remove esse frame para todos os sinais acima.

O que fica em JavaScript é o conjunto para o qual o Chrome não oferece comando: `deviceMemory`, `maxTouchPoints`, WebGL, WebGPU, dispositivos de mídia, vozes de síntese de fala, as capacidades do dispositivo de áudio, `navigator.connection`, fontes, a política de WebRTC e os extras da área de trabalho em headful. Cada um é escrito na forma nativa. Getters e métodos reportam `[native code]` sob `toString`, vivem no prototype real, chamam primeiro o nativo original para que um receiver estranho lance o erro real, e nunca criam propriedades próprias: um microfone falso é um `InputDeviceInfo`, uma voz falsa é uma `SpeechSynthesisVoice`, ambos com `Object.getOwnPropertyNames()` vazio. Os valores continuam fisicamente possíveis: um `OfflineAudioContext` reporta a taxa de amostragem com que foi construído, uma extensão WebGL que a GPU não tem é removida da lista em vez de forjada como um objeto vazio, e `WEBGL_debug_shaders` é escondida porque a fonte traduzida do shader nomeia o backend real.

Um resíduo é inerente: esses getters JavaScript continuam sendo funções, então o frame extra de stack existe para eles. Não dá para removê-lo a partir do JavaScript; a estratégia acima mantém esse conjunto tão pequeno quanto o Chrome permite. Leia um sinal de duas formas para ver onde você está: [Auditar um fingerprint](../deep-dive/fingerprinting/auditing.md).

## Trazer seus próprios perfis {#bring-your-own-profiles}

O Pydoll não gera nem distribui fingerprints. Os perfis em `examples/fingerprints.py` são uma referência para a coerência que um perfil exige e para o formato `FingerprintConfig`, não um catálogo para usar como está. Um perfil precisa combinar com o binário do Chrome em uso (a camada de rede é autêntica e não dá para sobrescrever) e com a geografia do IP de saída (locale, fuso horário, geolocalização). Um perfil público reusado em massa vira uma assinatura compartilhada, não um disfarce.

## Próximos passos

- [Auditar um fingerprint](../deep-dive/fingerprinting/auditing.md): ler um sinal de volta, comparar realms e confirmar que um perfil pegou.
- [O desafio gerenciado do Cloudflare](../deep-dive/fingerprinting/cloudflare-challenge.md): o detalhamento por camada do que passa headless e por quê.
- [The limits of spoofing](../deep-dive/fingerprinting/spoofing-limits.md): quais sinais dá para sobrescrever com segurança e quais não dá para forjar.
- [Workers and cross-origin iframes](../deep-dive/fingerprinting/execution-realms.md): como a identidade é replicada em cada realm.
- [Network fingerprinting](../deep-dive/fingerprinting/network-fingerprinting.md): a camada TLS/TCP/HTTP2 que a injeção não alcança.
- [Evasion techniques](evasion-techniques.md): consistência de User-Agent, proteção contra vazamento de WebRTC, e o que o Pydoll te dá de graça.
