# Injeção de fingerprint

## Introdução

`tab.apply_fingerprint()` dá ao navegador uma nova identidade. Ele sobrescreve os sinais que os scripts de fingerprinting leem, User-Agent e Client Hints, `navigator`, WebGL e WebGPU, métricas de tela, fontes, áudio, permissões, fuso horário e locale, antes da primeira navegação. Você passa um perfil; o Pydoll o aplica pelos comandos de override do próprio navegador onde existe um e por JavaScript reforçado só onde não existe nenhum.

Um limite honesto de saída: isto é substituição de identidade, não anonimato. Não muda o seu IP de saída nem o fingerprint da camada de rede, e um perfil inconsistente é mais detectável do que um navegador sem modificações. Um perfil tem que combinar com a máquina e o IP em que roda.

!!! warning "Nada disto é garantia"
    Cada site lê o próprio subconjunto de sinais e o pondera do próprio jeito. Um perfil mínimo (User-Agent, locale e fuso horário combinando com o host e o IP) passa em muitos alvos sozinho, e uma pequena inconsistência residual pode nunca ser lida. Comece simples, teste contra o site real e adicione campos só quando uma medição disser que um sinal específico é o que te bloqueia.

**Você vai aprender**

- [Como aplicar um fingerprint](#quick-start)
- [O que um perfil pode definir](#what-a-profile-can-set)
- [As regras que mantêm um perfil coerente](#making-a-profile-pass)
- [Como usar seus próprios perfis](#bring-your-own-profiles)

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
    O Pydoll não distribui perfis de fingerprint. `FINGERPRINTS` fica em `examples/fingerprints.py` no [repositório do pydoll](https://github.com/autoscrape-labs/pydoll), como perfis de referência para o formato `FingerprintConfig` (um typed dict de `pydoll.protocol.fingerprint.types`). Copie esse arquivo para o seu projeto e adapte cada perfil à sua máquina e ao seu IP. Um perfil reusado como está é uma assinatura compartilhada, não um disfarce.

## O que um perfil pode definir {#what-a-profile-can-set}

`FingerprintConfig` é um typed dict; toda seção é opcional e cada uma cobre uma superfície que um script de fingerprinting lê.

| Seção | Define |
|---|---|
| `user_agent` | a string do User-Agent, `navigator.platform` / `vendor` / `appVersion` e os Client Hints `Sec-CH-UA*` (as brands e a ordem delas seguem o algoritmo do próprio Chromium para o major) |
| `client_hints` | os hints de alta entropia que a string do User-Agent não consegue carregar: `platform_version`, `model`, `architecture`, `bitness`, `form_factors` |
| `locale` | `navigator.language(s)`, o header `Accept-Language` e o locale do `Intl` |
| `timezone`, `geolocation` | o fuso horário do `Intl`, `Date` e a API de Geolocation |
| `screen` | `screen.*`, `devicePixelRatio`, tamanho da janela e do viewport |
| `hardware` | `hardwareConcurrency`, `deviceMemory`, `maxTouchPoints` (eventos de toque são habilitados para perfis touch) |
| `permissions` | os estados de `navigator.permissions.query()`, em acordo com `Notification.permission` |
| `media_features` | `color-gamut`, `prefers-color-scheme` e as outras media features CSS que o Chrome consegue emular |
| `webgl` | strings de vendor e renderer, limites do WebGL e do WebGL2, extensões, precisão de shader |
| `webgpu` | `adapter.info`, limites e features do adapter real |
| `media_devices`, `speech`, `audio`, `network_connection`, `fonts`, `webrtc_ip_policy` | contagem de dispositivos de mídia, vozes de síntese de fala, capacidades do dispositivo de áudio, `navigator.connection`, fontes locais, a política ICE do WebRTC |

A lista completa de campos, com os valores aceitos e um exemplo por seção, está nas docstrings de `pydoll/protocol/fingerprint/types.py`.

## Fazer um perfil passar {#making-a-profile-pass}

Um perfil passa quando concorda com a máquina e o IP em que roda. No fundo, as regras são todas a mesma regra: coerência entre todas as camadas.

### Combine o OS do perfil com o OS do host

O kernel e a renderização de texto do OS expõem o OS real em camadas que nenhum override alcança. Rode um perfil macOS no macOS, um perfil Windows no Windows. Um proxy de encaminhamento re-origina a conexão a partir do kernel do proxy, então um perfil Windows passa a exigir um proxy rodando em Windows.

### Combine a versão do Chrome com o seu binário

O handshake TLS e o motor JavaScript reportam a versão real do binário; o User-Agent é a única parte que `apply_fingerprint()` muda. Leia a versão do binário e mantenha o major do perfil igual a ela, atualizando a cada upgrade do Chrome.

```python
version = await browser.get_version()
print(version['product'])  # ex.: 'Chrome/152.0.7977.83'
```

### Combine locale e fuso horário com o IP de saída

`Accept-Language`, `navigator.languages`, o fuso horário e a geolocalização são cruzados com o país do IP. Um perfil US atrás de um IP brasileiro fez uma busca simples no Google retornar um captcha; um locale brasileiro, combinando com o IP, removeu o bloqueio sem nenhuma outra mudança.

<p align="center">
  <img src="/docs/resources/images/fingerprint-inconsistent-captcha.png" alt="Google servindo um captcha porque o locale US do fingerprint injetado contradiz o IP de saída brasileiro" width="640" />
</p>
<p align="center"><sub>Locale US sobre um IP brasileiro: o Google retorna um captcha.</sub></p>

### Combine a GPU e as fontes com o host

As seções `webgl` e `webgpu` mudam o que o navegador reporta sobre a GPU; o que a GPU desenha continua real. Nomeie a família de GPU que está de fato na máquina, e capture os limites e as features de um dispositivo real daquela classe em vez de adivinhar. A seção `fonts` cobre as sondas de fontes em JavaScript; o motor de layout mede as fontes realmente instaladas, então liste exatamente o que está instalado.

### Fixe os Client Hints que o User-Agent não consegue carregar

A string do User-Agent é congelada (`Mac OS X 10_15_7`, `Android 10; K`); o Chrome real reporta a versão verdadeira do OS, o modelo do dispositivo e o form factor nos Client Hints. O parser preenche padrões plausíveis; defina `client_hints` para fixar os valores lidos num dispositivo real.

```python
fingerprint = FingerprintConfig(
    user_agent=UA_WINDOWS,
    client_hints=ClientHintsFingerprint(platform_version='15.0.0'),
)
```

### Um fingerprint por browser context

Um browser context guarda uma identidade. Aplicar um segundo fingerprint, diferente, ao mesmo context levanta `FingerprintContextConflict`. Rode identidades diferentes em contexts separados.

```python
ctx_id = await browser.create_browser_context()
tab_us = await browser.start()
tab_br = await browser.new_tab(browser_context_id=ctx_id)

await tab_us.apply_fingerprint(FINGERPRINTS['windows11_rtx3060_nyc'])
await tab_br.apply_fingerprint(FINGERPRINTS['android_s24_ultra_sao_paulo'])
```

Veja [Browser contexts](../guides/browser-contexts.md).

Algumas regras menores completam: aplique o fingerprint antes da primeira navegação; se você definir a opção `--user-agent`, mantenha-a igual à do perfil (um valor diferente registra um warning no log); use um IP residencial limpo; prefira `click(humanize=True)` e as [interações humanizadas](human-like-interactions.md), porque a entrada é o que muitos alvos mais pesam.

## Trazer seus próprios perfis {#bring-your-own-profiles}

O Pydoll não gera nem distribui fingerprints. Os perfis em `examples/fingerprints.py` são uma referência para a coerência que um perfil exige e para o formato `FingerprintConfig`, não um catálogo para usar como está. Um perfil precisa combinar com o binário do Chrome em uso e com a geografia do IP de saída (locale, fuso horário, geolocalização). Um perfil público reusado em massa vira uma assinatura compartilhada, não um disfarce.

## Próximos passos

- [Auditar um fingerprint](../deep-dive/fingerprinting/auditing.md): ler um sinal de volta e confirmar que um perfil pegou.
- [Evasion techniques](evasion-techniques.md): consistência de User-Agent, proteção contra vazamento de WebRTC, e o que o Pydoll te dá de graça.
- [Interações humanizadas](human-like-interactions.md): a camada comportamental.
