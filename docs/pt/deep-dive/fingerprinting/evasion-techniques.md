# Técnicas de Evasão

Este documento cobre técnicas práticas para evadir detecção de fingerprinting usando o Pydoll. As seções anteriores descreveram como a detecção funciona em cada camada: [network fingerprinting](./network-fingerprinting.md) (TCP/IP, TLS, HTTP/2), [browser fingerprinting](./browser-fingerprinting.md) (Canvas, WebGL, propriedades do navigator) e [behavioral fingerprinting](./behavioral-fingerprinting.md) (mouse, teclado, scroll). Esta seção foca em contramedidas.

O princípio central é consistência entre camadas. Passar em uma camada de detecção enquanto falha em outra ainda resulta em sinalização. Um IP residencial com um fingerprint TCP incompatível, ou um fingerprint de navegador perfeito com movimentos de mouse robóticos, será detectado por qualquer sistema que correlacione sinais.

!!! info "Navegação do Módulo"
    - [Network Fingerprinting](./network-fingerprinting.md): Identificação em nível de protocolo
    - [Browser Fingerprinting](./browser-fingerprinting.md): Detecção na camada de aplicação
    - [Behavioral Fingerprinting](./behavioral-fingerprinting.md): Análise de comportamento humano

## O que o Pydoll Fornece por Padrão

Antes de configurar qualquer coisa, é útil entender o que o Pydoll te dá gratuitamente ao usar uma instância real do Chrome via CDP.

**Fingerprints de rede autênticos.** A pilha TCP/IP do Chrome, implementação TLS (BoringSSL) e pilha HTTP/2 produzem fingerprints genuínos. O TLS ClientHello, frame HTTP/2 SETTINGS, ordem de pseudo-cabeçalhos e prioridades de stream correspondem a um navegador Chrome real. Ferramentas que constroem requisições HTTP programaticamente (requests, httpx, curl) produzem fingerprints não-navegador nessas camadas. Com o Pydoll, eles são autênticos por padrão.

**Fingerprints de navegador autênticos.** Fingerprints de Canvas, WebGL e AudioContext vêm de hardware real de GPU e áudio. Propriedades do navigator, plugins (os 5 plugins PDF padrão) e tipos MIME refletem estado genuíno do navegador. Não há nada para configurar aqui.

**Sem `navigator.webdriver`.** Selenium, Playwright e Puppeteer definem `navigator.webdriver` como `true`. O Pydoll usa CDP diretamente, que não define esta flag. A propriedade é `undefined`, correspondendo a uma sessão normal de usuário.

**Sequências de eventos completas.** Quando o Pydoll despacha eventos de entrada através do domínio Input do CDP, o Chrome gera a cadeia completa de eventos (pointermove, pointerdown, mousedown, pointerup, mouseup, click) exatamente como faria para entrada real do usuário.

## Consistência de User-Agent

A inconsistência de fingerprinting mais comum em automação é uma incompatibilidade entre o cabeçalho HTTP `User-Agent`, `navigator.userAgent` no JavaScript, `navigator.platform` e cabeçalhos Client Hints (`Sec-CH-UA`, `Sec-CH-UA-Platform`). Definir `--user-agent=` como flag do Chrome apenas muda o cabeçalho HTTP, deixando propriedades JavaScript e Client Hints inalterados.

O Pydoll resolve isso automaticamente. Quando detecta `--user-agent=` nos argumentos do navegador, ele:

1. Analisa a string UA para extrair nome do navegador, versão e SO.
2. Chama `Emulation.setUserAgentOverride` via CDP com o `userAgent` completo, o valor correto de `platform` (ex: `Win32` para Windows) e `userAgentMetadata` completo (dados de Client Hints incluindo `Sec-CH-UA`, `Sec-CH-UA-Platform`, `Sec-CH-UA-Full-Version-List`).
3. Injeta sobrescritas de `navigator.vendor` e `navigator.appVersion` via `Page.addScriptToEvaluateOnNewDocument`, garantindo consistência mesmo em abas recém-abertas.

```python
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
options.add_argument(
    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/120.0.6099.109 Safari/537.36'
)

async with Chrome(options=options) as browser:
    tab = await browser.start()
    # Todas as camadas agora são consistentes:
    # - Cabeçalho HTTP User-Agent
    # - navigator.userAgent / navigator.platform / navigator.appVersion
    # - Sec-CH-UA / Sec-CH-UA-Platform / Sec-CH-UA-Full-Version-List
    # - navigator.userAgentData.brands / .platform
    await tab.go_to('https://example.com')
```

Essa sobrescrita é aplicada automaticamente à aba inicial, novas abas de `browser.new_tab()`, e quaisquer abas descobertas via `browser.get_opened_tabs()`.

!!! note "Plataformas Suportadas"
    O parser de UA lida com Chrome, Edge, Windows (NT 6.1 até 10.0), macOS, Linux, Android, iOS e Chrome OS. Ele gera valores de marca GREASE adequados seguindo a especificação do Chromium.

## Consistência de Timezone e Locale

Ao usar um proxy, o timezone e idioma do navegador devem corresponder à localização geográfica do IP do proxy. Um IP geolocalizado em Tóquio com timezone `America/New_York` e `Accept-Language: en-US` é uma inconsistência detectável.

### Configuração de Idioma

O idioma é configurado através de flags do Chrome e da API de opções do Pydoll:

```python
options = ChromiumOptions()
options.add_argument('--lang=ja-JP')
options.set_accept_languages('ja-JP,ja;q=0.9,en;q=0.8')
```

Isso define tanto o cabeçalho HTTP `Accept-Language` quanto `navigator.language` / `navigator.languages`.

### Sobrescrita de Timezone

O Pydoll atualmente não encapsula o comando `Emulation.setTimezoneOverride` do CDP, então a sobrescrita de timezone requer injeção de JavaScript. As APIs críticas para sobrescrever são `Intl.DateTimeFormat().resolvedOptions().timeZone` e `Date.prototype.getTimezoneOffset()`:

```python
async def set_timezone(tab, timezone_id: str, offset_minutes: int):
    """
    Sobrescreve timezone via JavaScript.

    Args:
        timezone_id: Nome de timezone IANA (ex: 'Asia/Tokyo')
        offset_minutes: Offset UTC em minutos (ex: -540 para JST)
    """
    script = f'''
        const _origDTF = Intl.DateTimeFormat;
        Intl.DateTimeFormat = function(...args) {{
            const opts = args[1] || {{}};
            opts.timeZone = '{timezone_id}';
            return new _origDTF(args[0], opts);
        }};
        Object.defineProperty(Intl.DateTimeFormat, 'prototype', {{
            value: _origDTF.prototype
        }});
        Date.prototype.getTimezoneOffset = function() {{ return {offset_minutes}; }};
    '''
    await tab.execute_script(script)
```

!!! warning "`execute_script` vs `addScriptToEvaluateOnNewDocument`"
    `tab.execute_script()` executa JavaScript no contexto da página atual. Se a página navegar, a sobrescrita é perdida. Para sobrescritas que devem persistir entre navegações, use `Page.addScriptToEvaluateOnNewDocument` do CDP, que injeta o script antes de qualquer JavaScript da página executar em cada novo carregamento de documento. O Pydoll usa isso internamente para sobrescritas de User-Agent. Para timezone, você pode enviar o comando CDP diretamente:

    ```python
    await tab._connection_handler.execute_command(
        'Page.addScriptToEvaluateOnNewDocument',
        {'source': script}
    )
    ```

### Sobrescrita de Geolocalização

Para sites que solicitam permissão de geolocalização, a API de Geolocation pode ser sobrescrita via JavaScript:

```python
async def set_geolocation(tab, latitude: float, longitude: float):
    script = f'''
        navigator.geolocation.getCurrentPosition = function(success) {{
            success({{
                coords: {{
                    latitude: {latitude}, longitude: {longitude},
                    accuracy: 1, altitude: null, altitudeAccuracy: null,
                    heading: null, speed: null
                }},
                timestamp: Date.now()
            }});
        }};
        navigator.geolocation.watchPosition = function(success) {{
            return navigator.geolocation.getCurrentPosition(success);
        }};
    '''
    await tab.execute_script(script)
```

## Proteção contra Vazamento WebRTC

O WebRTC pode expor o endereço IP real do cliente mesmo ao usar um proxy, através de requisições a servidores STUN/TURN que ignoram o túnel do proxy. O Pydoll fornece uma opção integrada para prevenir isso:

```python
options = ChromiumOptions()
options.webrtc_leak_protection = True
# Adiciona: --force-webrtc-ip-handling-policy=disable_non_proxied_udp
```

Isso força o Chrome a rotear todo o tráfego WebRTC através do proxy, prevenindo vazamento de IP. Deve ser habilitado sempre que usar um proxy para automação stealth.

## Humanização Comportamental

O Pydoll implementa interações humanizadas para mouse, teclado e scroll através do parâmetro `humanize=True`. Estes não são recursos futuros ou soluções manuais; estão integrados ao framework.

### Mouse

```python
# Clique humanizado: caminho com curva Bezier, tempo pela Lei de Fitts,
# velocidade de jerk mínimo, tremor, overshoot + correção
await element.click(humanize=True)
```

Quando `humanize=True` é passado para o `click()` de um WebElement, o Pydoll gera um movimento completo do mouse da posição atual do cursor até o elemento usando uma curva Bezier cúbica com pontos de controle aleatorizados. A velocidade segue um perfil de jerk mínimo. Tremor fisiológico, overshoot (70% de probabilidade) e micro-pausas são adicionados. A duração do movimento é calculada pela Lei de Fitts baseada na distância e tamanho do alvo. Veja [Behavioral Fingerprinting](./behavioral-fingerprinting.md#humanização-de-mouse-do-pydoll) para descrições detalhadas dos parâmetros.

### Teclado

```python
# Digitação humanizada: atrasos variáveis, erros realistas (~2%),
# pausas de pontuação, pausas de pensamento, pausas de distração
await element.type_text("Hello, world!", humanize=True)
```

A digitação humanizada usa atrasos inter-tecla variáveis (distribuição uniforme de 30-120ms), pausas de pontuação, pausas de pensamento (2% de probabilidade), pausas de distração (0.5% de probabilidade) e erros de digitação realistas com cinco tipos de erro distintos e sequências de correção naturais. Veja [Behavioral Fingerprinting](./behavioral-fingerprinting.md#humanização-de-teclado-do-pydoll) para o detalhamento completo dos parâmetros.

### Scroll

```python
from pydoll.interactions.scroll import Scroll, ScrollPosition

scroll = Scroll(connection_handler)
# Scroll humanizado: easing Bezier, jitter, micro-pausas, overshoot
await scroll.by(ScrollPosition.Y, 800, humanize=True)
```

O scroll humanizado usa curvas de easing Bezier, jitter por frame (±3px), micro-pausas (5% de probabilidade) e correção de overshoot (15% de probabilidade). Grandes distâncias são divididas em múltiplos gestos de "flick". Veja [Behavioral Fingerprinting](./behavioral-fingerprinting.md#humanização-de-scroll-do-pydoll) para detalhes.

## Interceptação de Requisições

O Pydoll suporta interceptação de requisições via domínio Fetch do CDP, permitindo modificar cabeçalhos, bloquear requisições ou fornecer respostas personalizadas antes que cheguem ao servidor:

```python
from pydoll.protocol.fetch.events import FetchEvent

async def handle_request(event):
    request_id = event['params']['requestId']
    request = event['params']['request']
    headers = request.get('headers', {})

    # Exemplo: garantir que suporte a Brotli é anunciado
    if 'Accept-Encoding' in headers and 'br' not in headers['Accept-Encoding']:
        headers['Accept-Encoding'] = 'gzip, deflate, br, zstd'

    header_list = [{'name': k, 'value': v} for k, v in headers.items()]
    await tab.continue_request(request_id=request_id, headers=header_list)

await tab.enable_fetch_events()
await tab.on(FetchEvent.REQUEST_PAUSED, handle_request)
```

Na prática, modificação de cabeçalhos é raramente necessária com o Pydoll porque o Chrome gera cabeçalhos corretos nativamente. A interceptação de requisições é mais útil para bloquear scripts de rastreamento, modificar conteúdo de resposta ou depuração.

## Preferências do Navegador para Realismo

O Chrome armazena preferências do usuário que sistemas de fingerprinting podem inspecionar. Um perfil de navegador novo sem histórico, sem preferências salvas e tudo padrão parece diferente de um perfil que foi usado por semanas. A opção `browser_preferences` do Pydoll permite pré-popular estas:

```python
import time

options = ChromiumOptions()
options.browser_preferences = {
    'profile': {
        'created_by_version': '120.0.6099.130',
        'creation_time': str(time.time() - 90 * 86400),  # 90 dias atrás
        'exit_type': 'Normal',
    },
    'profile.default_content_setting_values': {
        'cookies': 1,
        'images': 1,
        'javascript': 1,
        'notifications': 2,  # "Perguntar" (padrão realista)
    },
}
```

## Erros Comuns

### Randomizar Tudo

Gerar um fingerprint aleatório do zero (hardwareConcurrency aleatório, deviceMemory aleatório, tamanho de tela aleatório) cria combinações impossíveis. Dispositivos reais têm configurações restritas: uma máquina de 4 núcleos com 8 GB de RAM, tela 1920x1080 e Windows 10 é um perfil plausível. Uma máquina de 17 núcleos com 0.5 GB de RAM, tela 3840x2160 e `navigator.platform: Linux armv7l` não é. Use perfis capturados de navegadores reais em vez de geração aleatória.

### Injeção de Ruído no Canvas

Adicionar ruído aleatório à saída do canvas para prevenir fingerprinting é contraproducente. Sistemas de detecção solicitam o fingerprint múltiplas vezes. Se o hash muda entre requisições, injeção de ruído é detectada, o que é em si um sinal forte de automação. Com o Pydoll, o fingerprint de canvas é autêntico e consistente. Deixe-o como está.

### User-Agents Desatualizados

Usar um User-Agent de uma versão de navegador com 6+ meses é detectável porque a versão carece de recursos e valores de Client Hints que a versão atual teria. Mantenha strings de User-Agent atuais dentro das últimas 2-3 versões principais do Chrome.

### Ignorar Comportamento em Nível de Sessão

Mesmo com fingerprints perfeitos e interações humanizadas, o comportamento em nível de sessão importa. Carregar 100 páginas em 60 segundos, nunca scrollar, clicar apenas em botões (nunca links) e manter foco constante por horas sem uma única troca de aba ou período ocioso são todas anomalias comportamentais. Adicione atrasos de leitura entre navegações, varie o ritmo de workflows de múltiplas páginas e inclua períodos naturais de inatividade.

## Verificação

Antes de implantar automação em escala, verifique seu fingerprint usando estas ferramentas:

| Ferramenta | URL | Testes |
|------|-----|-------|
| BrowserLeaks | https://browserleaks.com/ | Canvas, WebGL, fontes, IP, WebRTC, HTTP/2 |
| CreepJS | https://abrahamjuliot.github.io/creepjs/ | Detecção de mentiras, verificações de consistência |
| Fingerprint.com | https://fingerprint.com/demo/ | Identificação de nível comercial |
| PixelScan | https://pixelscan.net/ | Análise de detecção de bots |
| IPLeak | https://ipleak.net/ | WebRTC, DNS, vazamentos de IP |

Um script básico de verificação com o Pydoll:

```python
async def verify_fingerprint(tab):
    result = await tab.execute_script('''
        return {
            userAgent: navigator.userAgent,
            platform: navigator.platform,
            webdriver: navigator.webdriver,
            languages: navigator.languages,
            plugins: navigator.plugins.length,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            colorDepth: screen.colorDepth,
            deviceMemory: navigator.deviceMemory,
            hardwareConcurrency: navigator.hardwareConcurrency,
        };
    ''')
    fp = result['result']['result']['value']

    # Verificar problemas óbvios
    assert fp['webdriver'] is None, 'navigator.webdriver deveria ser undefined'
    assert fp['plugins'] == 5, f'Esperados 5 plugins, obtidos {fp["plugins"]}'
    assert 'HeadlessChrome' not in fp['userAgent'], 'Headless detectado no UA'
```

## Referências

- Chrome DevTools Protocol, Emulation Domain: https://chromedevtools.github.io/devtools-protocol/tot/Emulation/
- Chrome DevTools Protocol, Fetch Domain: https://chromedevtools.github.io/devtools-protocol/tot/Fetch/
- Chromium Source, Inspector Emulation Agent: https://source.chromium.org/chromium/chromium/src/+/main:third_party/blink/renderer/core/inspector/inspector_emulation_agent.cc
