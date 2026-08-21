# Técnicas de evasão

Os sistemas de detecção correlacionam sinais entre camadas: o fingerprint de rede (TCP/TLS/HTTP2), o fingerprint do navegador (canvas, WebGL, navigator) e o comportamento (mouse, teclado, tempo). Passar em uma camada e falhar em outra ainda te sinaliza. Um IP residencial com um fingerprint TCP incompatível, ou um fingerprint de navegador perfeito com cliques robóticos, é pego por qualquer coisa que faça verificação cruzada. Esta página cobre o que o Pydoll te dá de graça e as alavancas que você controla para manter as camadas consistentes.

<iframe src="/docs/resources/visuals/evasion-layers.html" aria-label="Como as camadas de rede, navegador, comportamento e IP têm todas que permanecer consistentes para passar" style="width: 100%; height: 320px; border: 0;" loading="lazy"></iframe>

## O que você ganha de graça

Como o Pydoll controla um Chrome real via CDP em vez de sintetizar requisições, várias camadas são autênticas sem nenhuma configuração:

- **Fingerprints de rede reais.** A stack TCP/IP do Chrome, o TLS (BoringSSL) e a stack HTTP/2 produzem fingerprints genuínos: o TLS ClientHello, o frame `SETTINGS` do HTTP/2, a ordem dos pseudo-headers e as prioridades de stream, tudo corresponde a um Chrome real. Ferramentas que constroem requisições programaticamente (requests, httpx, curl) não.
- **Fingerprints de navegador reais.** Canvas, WebGL e AudioContext vêm de hardware de GPU e áudio reais. As propriedades do navigator, os plugins de PDF embutidos e os tipos MIME refletem o estado genuíno do navegador.
- **`navigator.webdriver` é `false`.** Selenium, Playwright e Puppeteer o definem como `true`. O Pydoll inicia sem flags de automação, então ele reporta `false`, igual a uma sessão normal. Você não precisa aplicar patch nisso.
- **Sequências completas de eventos de input.** O input despachado via CDP gera a cadeia completa de eventos (`pointermove`, `pointerdown`, `mousedown`, `pointerup`, `mouseup`, `click`) exatamente como um usuário real faria.

O resto desta página são as camadas que você de fato controla.

## Mantenha o User-Agent consistente

O indício de automação mais comum é um User-Agent que discorda de si mesmo: o header HTTP `User-Agent` dizendo uma coisa enquanto `navigator.userAgent`, `navigator.platform` e os Client Hints (`Sec-CH-UA`, `Sec-CH-UA-Platform`) dizem outra. Definir `--user-agent=` como uma flag simples do Chrome muda apenas o header HTTP e deixa o JavaScript e os Client Hints intocados, o que é uma incompatibilidade que um detector lê imediatamente.

O Pydoll corrige isso para você. Quando ele vê um argumento `--user-agent=`, ele aplica `Emulation.setUserAgentOverride` com o `platform` correspondente e os metadados completos de Client Hints, e injeta `navigator.vendor` / `navigator.appVersion`, de modo que todas as camadas concordem, inclusive em novas abas.

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions


async def main():
    options = ChromiumOptions()
    options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/130.0.0.0 Safari/537.36'
    )

    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://browserleaks.com/javascript')

asyncio.run(main())
```

Mantenha o `Chrome/<version>` na string igual ao Chrome que você realmente executa; uma versão que você não está rodando é, por si só, uma incompatibilidade. O override se aplica à primeira aba, às abas de `browser.new_tab()` e às abas encontradas via `browser.get_opened_tabs()`.

## Combine idioma, fuso horário e geolocalização com o IP

Por trás de um proxy, o idioma, o fuso horário e a localização do navegador devem concordar com o país do IP. Um IP em Tóquio com `Accept-Language: en-US` e um fuso `America/New_York` é uma contradição.

O idioma é uma opção independente:

```python
options = ChromiumOptions()
options.add_argument('--lang=ja-JP')
options.set_accept_languages('ja-JP,ja;q=0.9,en;q=0.8')
```

Isso define tanto o header `Accept-Language` quanto `navigator.language` / `navigator.languages`. O fuso horário e a geolocalização também têm que combinar, e precisam permanecer consistentes com o sistema operacional do User-Agent e com o IP, tudo ao mesmo tempo. Defini-los de forma coerente a partir de um único perfil é para isso que serve `apply_fingerprint()`; veja [Injeção de fingerprint](fingerprint-injection.md).

## Impeça o WebRTC de vazar o seu IP

O WebRTC pode revelar o IP real mesmo por trás de um proxy, através de requisições STUN que pulam o túnel do proxy. Ative a proteção embutida sempre que usar um proxy para stealth:

```python
options = ChromiumOptions()
options.webrtc_leak_protection = True   # --force-webrtc-ip-handling-policy=disable_non_proxied_udp
```

## Comporte-se como uma pessoa

Cliques instantâneos e teclas perfeitamente regulares são um fingerprint comportamental. Passe `humanize=True` para mover o cursor por um caminho curvo, com tempo humano, e digitar com ritmo variável e erros de digitação ocasionais que são corrigidos:

```python
field = await tab.find(id='search')
await field.type_text('browser automation', humanize=True)
await field.click(humanize=True)
```

Veja [Interações humanizadas](human-like-interactions.md) para o modelo de tempo e como ajustá-lo.

## Pareça um perfil já usado

Um perfil novinho em folha, sem histórico e com todos os recursos desativados, não se parece em nada com o de um usuário real. Pré-popule o perfil através de `browser_preferences` (timestamps envelhecidos, uma versão do Chrome correspondente, recursos ativados), abordado em [Preferências do navegador](../guides/browser-preferences.md#build-a-realistic-profile-for-stealth).

## Erros comuns

**Randomizar tudo.** Um `hardwareConcurrency`, `deviceMemory` e tamanho de tela aleatórios produzem dispositivos impossíveis. Máquinas reais são limitadas: 4 núcleos com 8 GB de RAM e uma tela 1920x1080 é plausível; 17 núcleos com 0,5 GB de RAM e uma tela 4K não é. Use perfis capturados de navegadores reais, não valores aleatórios.

**Injetar ruído no canvas.** Adicionar ruído à saída do canvas sai pela culatra: os detectores amostram o fingerprint repetidamente, e um valor que muda entre leituras é, por si só, um sinal de automação. O canvas do Pydoll é autêntico e estável; deixe-o quieto.

**User-Agents desatualizados.** Um UA de uma release do Chrome de seis meses atrás carece de recursos e Client Hints que a versão atual tem. Fique dentro das últimas duas ou três versões principais, e combine com o binário que você executa.

**Ignorar o comportamento da sessão.** Mesmo com um fingerprint limpo, carregar 100 páginas num minuto, nunca rolar a página e nunca ficar ocioso são anomalias. Adicione delays de leitura, varie o ritmo e inclua pausas naturais.

## Verifique a sua configuração

Cheque o seu fingerprint nestes sites antes de rodar em escala:

| Ferramenta | URL | Testa |
|------|-----|-------|
| BrowserLeaks | `https://browserleaks.com/` | Canvas, WebGL, fontes, IP, WebRTC, HTTP/2 |
| CreepJS | `https://abrahamjuliot.github.io/creepjs/` | Detecção de mentiras, verificações de consistência |
| Pixelscan | `https://pixelscan.net/` | Análise de detecção de bots |
| IPLeak | `https://ipleak.net/` | WebRTC, DNS, vazamentos de IP |

Uma verificação rápida com o Pydoll:

```python
result = await tab.execute_script('''
    return {
        userAgent: navigator.userAgent,
        webdriver: navigator.webdriver,
        languages: navigator.languages,
        plugins: navigator.plugins.length,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    };
''')
fp = result['result']['result']['value']

assert fp['webdriver'] is False, 'navigator.webdriver should be false'
assert 'HeadlessChrome' not in fp['userAgent'], 'headless leaking in the UA'
```

## O que vem a seguir

- [Injeção de fingerprint](fingerprint-injection.md): aplique uma identidade coerente (User-Agent, WebGL, fuso horário, locale) a partir de um único perfil.
- [Interações humanizadas](human-like-interactions.md): a camada comportamental em profundidade.
- [Proxies](../guides/proxies.md): mude e verifique o seu IP de saída.
- [Fingerprinting (aprofundamento)](../deep-dive/fingerprinting/index.md): a teoria de detecção por trás dessas alavancas.
