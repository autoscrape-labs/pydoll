# Injeção de fingerprint

## Introdução

`tab.apply_fingerprint()` dá ao navegador uma nova identidade. Ele sobrescreve os sinais que os scripts de fingerprinting leem, User-Agent e Client Hints, `navigator`, WebGL, métricas de tela, fontes, áudio, fuso horário e locale, na página, nos seus workers e nos seus cross-origin iframes, antes da primeira navegação. Você não monta um fingerprint na mão nem faz patch de `navigator`; você passa um perfil e o Pydoll o aplica de forma coerente.

O ganho é concreto. Com um perfil compatível, o Chrome headless deixa de ser sinalizado como bot na hora e passa a ler como um desktop comum, o suficiente para [passar o desafio gerenciado do Cloudflare em modo headless](#clear-cloudflares-challenge-headless).

Um limite honesto de saída: isto é substituição de identidade, não anonimato. Não muda o seu IP de saída nem o fingerprint da camada de rede, e um perfil inconsistente é mais detectável do que um navegador sem modificações. Fazer o perfil *combinar* com a sua máquina e o seu IP é o trabalho todo, e [as regras abaixo](#making-a-profile-pass) são esse checklist.

**Você vai aprender**

- [Como aplicar um fingerprint](#quick-start)
- [Como ele passa o Cloudflare headless](#clear-cloudflares-challenge-headless)
- [Como provar que está funcionando](#prove-it-with-a-bot-score)
- [Como fazer um perfil passar](#making-a-profile-pass)
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

### Combine locale e fuso horário com o IP de saída

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

### Um fingerprint por browser context

Service e shared workers são compartilhados dentro de um browser context, então um context guarda uma identidade. Aplicar um segundo fingerprint no mesmo context levanta `FingerprintContextConflict`. Rode identidades diferentes em contexts separados.

```python
ctx_id = await browser.create_browser_context()
tab_us = await browser.start()
tab_br = await browser.new_tab(browser_context_id=ctx_id)

await tab_us.apply_fingerprint(FINGERPRINTS['windows11_rtx3060_nyc'])
await tab_br.apply_fingerprint(FINGERPRINTS['android_s24_ultra_sao_paulo'])
```

Veja [Browser contexts](../guides/browser-contexts.md).

Algumas regras menores completam: aplique o fingerprint antes da primeira navegação; não combine a opção `--user-agent` com `apply_fingerprint()` (o perfil é dono do User-Agent); combine o vendor/renderer do WebGL e o color-gamut com a GPU e o display do host; use um IP residencial limpo. Sobre por que alguns sinais podem ser sobrescritos e outros não dá para forjar, veja [The limits of spoofing](../deep-dive/fingerprinting/spoofing-limits.md).

## Trazer seus próprios perfis {#bring-your-own-profiles}

O Pydoll não gera nem distribui fingerprints. Os perfis em `examples/fingerprints.py` são uma referência para a coerência que um perfil exige e para o formato `FingerprintConfig`, não um catálogo para usar como está. Um perfil precisa combinar com o binário do Chrome em uso (a camada de rede é autêntica e não dá para sobrescrever) e com a geografia do IP de saída (locale, fuso horário, geolocalização). Um perfil público reusado em massa vira uma assinatura compartilhada, não um disfarce.

## Próximos passos

- [Auditar um fingerprint](../deep-dive/fingerprinting/auditing.md): ler um sinal de volta, comparar realms e confirmar que um perfil pegou.
- [O desafio gerenciado do Cloudflare](../deep-dive/fingerprinting/cloudflare-challenge.md): o detalhamento por camada do que passa headless e por quê.
- [The limits of spoofing](../deep-dive/fingerprinting/spoofing-limits.md): quais sinais dá para sobrescrever com segurança e quais não dá para forjar.
- [Workers and cross-origin iframes](../deep-dive/fingerprinting/execution-realms.md): como a identidade é replicada em cada realm.
- [Network fingerprinting](../deep-dive/fingerprinting/network-fingerprinting.md): a camada TLS/TCP/HTTP2 que a injeção não alcança.
- [Evasion techniques](evasion-techniques.md): consistência de User-Agent, proteção contra vazamento de WebRTC, e o que o Pydoll te dá de graça.
