# Técnicas de Evasão de Fingerprinting

Este documento fornece **técnicas práticas e acionáveis** para evadir o fingerprinting usando a integração CDP do Pydoll, sobrescritas de JavaScript e interceptação de requisições. Tudo descrito aqui foi testado e validado.

!!! info "Navegação do Módulo"
    - **[← Visão Geral de Fingerprinting](./index.md)** - Introdução e filosofia do módulo
    - **[← Network Fingerprinting (Fingerprinting de Rede)](./network-fingerprinting.md)** - Fingerprinting em nível de protocolo
    - **[← Browser Fingerprinting (Fingerprinting de Navegador)](./browser-fingerprinting.md)** - Fingerprinting na camada de aplicação
    - **[← Behavioral Fingerprinting (Fingerprinting Comportamental)](./behavioral-fingerprinting.md)** - Análise de comportamento humano
    
    Para uso prático do Pydoll, veja **[Interações Semelhantes a Humanas](../../features/automation/human-interactions.md)** e **[Contorno de Captcha Comportamental](../../features/advanced/behavioral-captcha-bypass.md)**.

!!! warning "Teoria → Prática"
    É aqui que tudo o que você aprendeu sobre fingerprinting de rede e navegador é aplicado. Cada técnica inclui **exemplos de código funcionais** prontos para integrar com o Pydoll.

## Evasão de Fingerprinting Baseada em CDP

O Chrome DevTools Protocol (CDP) fornece métodos poderosos para modificar o comportamento do navegador em um nível profundo, muito além do que a injeção de JavaScript pode alcançar. Isso torna a automação baseada em CDP (como o Pydoll) **significativamente mais furtiva** do que o Selenium ou o Puppeteer.

### O Problema da Incompatibilidade do User-Agent

Uma das inconsistências de fingerprinting **mais comuns** na automação é a incompatibilidade entre:

1. **Cabeçalho HTTP `User-Agent`** (enviado com cada requisição)
2. **Propriedade `navigator.userAgent`** (acessível via JavaScript)
3. **Cabeçalhos `Sec-CH-UA` Client Hints** (enviados por navegadores Chromium)

Sem tratamento adequado, definir `--user-agent=...` modifica apenas os cabeçalhos HTTP enquanto `navigator.userAgent` e Client Hints permanecem inalterados — criando uma incompatibilidade trivialmente detectável.

### Consistência Automática do User-Agent

O Pydoll **automaticamente** sincroniza todas as camadas do User-Agent quando você define `--user-agent=`. Nenhuma sobrescrita manual é necessária:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions


async def main():
    options = ChromiumOptions()
    options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.6099.109 Safari/537.36'
    )

    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')

asyncio.run(main())
```

Quando o Pydoll detecta `--user-agent=` nos argumentos do navegador, ele automaticamente:

1. **Analisa a string UA** para extrair informações de navegador, versão e sistema operacional
2. **Envia `Emulation.setUserAgentOverride`** via CDP com:
    - `userAgent` — a string UA completa (cabeçalho HTTP + `navigator.userAgent`)
    - `platform` — o valor correto de `navigator.platform` (ex: `Win32`, `MacIntel`, `Linux x86_64`)
    - `userAgentMetadata` — dados completos de Client Hints (`Sec-CH-UA`, `Sec-CH-UA-Platform`, `Sec-CH-UA-Full-Version-List`, etc.)
3. **Injeta JavaScript** via `Page.addScriptToEvaluateOnNewDocument` para sobrescrever:
    - `navigator.vendor` — mapeado do tipo de navegador (ex: `Google Inc.`)
    - `navigator.appVersion` — derivado da string UA

Isso garante **consistência completa** em todas as camadas:

| Camada | Propriedade | Status |
|--------|-------------|--------|
| HTTP | Cabeçalho `User-Agent` | ✅ Consistente |
| HTTP | Cabeçalho `Sec-CH-UA` | ✅ Consistente |
| HTTP | Cabeçalho `Sec-CH-UA-Platform` | ✅ Consistente |
| HTTP | Cabeçalho `Sec-CH-UA-Full-Version-List` | ✅ Consistente |
| JS | `navigator.userAgent` | ✅ Consistente |
| JS | `navigator.platform` | ✅ Consistente |
| JS | `navigator.vendor` | ✅ Consistente |
| JS | `navigator.appVersion` | ✅ Consistente |
| JS | `navigator.userAgentData` | ✅ Consistente |

!!! tip "Funciona em todas as abas"
    A sobrescrita é aplicada automaticamente à aba inicial de `browser.start()`, novas abas de `browser.new_tab()` e quaisquer abas descobertas via `browser.get_opened_tabs()`.

!!! info "Navegadores e plataformas suportados"
    O parser trata corretamente:

    - **Navegadores**: Google Chrome, Microsoft Edge
    - **Plataformas**: Windows (NT 6.1–10.0), macOS, Linux, Android, iOS (iPhone/iPad), Chrome OS
    - **Client Hints GREASE**: Geração correta de marcas GREASE seguindo a especificação do Chromium

### Técnicas de Modificação de Fingerprint

Além da consistência automática do User-Agent, você pode personalizar ainda mais seu fingerprint usando sobrescritas de JavaScript e opções do navegador:

#### 1. Sobrescrita de Fuso Horário (via JavaScript)

```python
async def set_timezone(tab, timezone_id: str):
    """
    Sobrescreve o fuso horário via JavaScript.
    Exemplo: 'America/New_York', 'Europe/London', 'Asia/Tokyo'
    
    Nota: Isso sobrescreve a API JavaScript, mas não afeta o fuso horário
    em nível de sistema. Use o argumento de linha de comando --tz para emulação completa.
    """
    script = f```
        // Sobrescreve Intl.DateTimeFormat
        const originalDateTimeFormat = Intl.DateTimeFormat;
        Intl.DateTimeFormat = function(...args) {{
            const options = args[1] || {{}};
            options.timeZone = '{timezone_id}';
            return new originalDateTimeFormat(args[0], options);
        }};
        
        // Sobrescreve Date.prototype.getTimezoneOffset
        const timezoneOffsets = {{
            'America/New_York': 300,
            'Europe/London': 0,
            'Asia/Tokyo': -540,
            'America/Los_Angeles': 480,
        }};
        Date.prototype.getTimezoneOffset = function() {{
            return timezoneOffsets['{timezone_id}'] || 0;
        }};
    ```
    await tab.execute_script(script)


# Uso
await set_timezone(tab, 'America/Los_Angeles')

# Verificar
result = await tab.execute_script('return Intl.DateTimeFormat().resolvedOptions().timeZone')
tz = result['result']['result']['value']
print(f"Timezone: {tz}")  # America/Los_Angeles
```

#### 2. Sobrescrita de Localidade (via Opções do Navegador)

```python
# Definir localidade via argumentos de linha de comando
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
options.add_argument('--lang=pt-BR')
options.set_accept_languages('pt-BR,pt;q=0.9,en;q=0.8')

async with Chrome(options=options) as browser:
    tab = await browser.start()
    
    # Verificar
    result = await tab.execute_script('return navigator.language')
    locale = result['result']['result']['value']
    print(f"Locale: {locale}")  # pt-BR
```

#### 3. Sobrescrita de Geolocalização (via JavaScript)

```python
async def set_geolocation(tab, latitude: float, longitude: float, accuracy: int = 1):
    """
    Sobrescreve geolocalização via JavaScript.
    """
    script = f```
        navigator.geolocation.getCurrentPosition = function(success) {{
            const position = {{
                coords: {{
                    latitude: {latitude},
                    longitude: {longitude},
                    accuracy: {accuracy},
                    altitude: null,
                    altitudeAccuracy: null,
                    heading: null,
                    speed: null
                }},
                timestamp: Date.now()
            }};
            success(position);
        }};
    ```
    await tab.execute_script(script)


# Exemplo: Cidade de Nova York
await set_geolocation(tab, 40.7128, -74.0060)
```

#### 4. Métricas do Dispositivo (via Opções do Navegador)

```python
# Emulação móvel via argumentos de linha de comando
options = ChromiumOptions()
options.add_argument('--window-size=393,852')
options.add_argument('--device-scale-factor=3')
options.add_argument('--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1')

async with Chrome(options=options) as browser:
    tab = await browser.start()
    
    # Sobrescrever propriedades móveis adicionais
    mobile_script = ```
        Object.defineProperty(Navigator.prototype, 'maxTouchPoints', {
            get: () => 5
        });
        
        // Sobrescrever propriedades da tela
        Object.defineProperty(window.screen, 'width', { get: () => 393 });
        Object.defineProperty(window.screen, 'height', { get: () => 852 });
        Object.defineProperty(window.screen, 'availWidth', { get: () => 393 });
        Object.defineProperty(window.screen, 'availHeight', { get: () => 852 });
    ```
    await tab.execute_script(mobile_script)
```

#### 5. Eventos de Toque (via JavaScript)

```python
async def enable_touch_events(tab, max_touch_points: int = 5):
    """
    Sobrescreve propriedades relacionadas ao toque.
    """
    script = f```
        Object.defineProperty(Navigator.prototype, 'maxTouchPoints', {{
            get: () => {max_touch_points}
        }});
        
        // Adiciona suporte a eventos de toque
        if (!window.TouchEvent) {{
            window.TouchEvent = class TouchEvent extends UIEvent {{}};
        }}
    ```
    await tab.execute_script(script)


# Verificar
result = await tab.execute_script('return navigator.maxTouchPoints')
touch_points = result['result']['result']['value']
print(f"Max Touch Points: {touch_points}")  # 5
```

### Interceptação de Requisições para Modificação de Cabeçalho

O Pydoll fornece suporte nativo para interceptação de requisições através do domínio Fetch. Isso permite modificar cabeçalhos, bloquear requisições ou fornecer respostas personalizadas:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.protocol.fetch.events import FetchEvent


async def setup_request_interception(tab):
    """
    Intercepta todas as requisições e modifica cabeçalhos usando métodos nativos do Pydoll.
    """
    # Habilita o domínio Fetch para interceptação de requisições
    await tab.enable_fetch_events()
    
    # Ouve eventos de requisição pausada
    async def handle_request(event):
        """Lida com requisições interceptadas."""
        request_id = event['params']['requestId']
        request = event['params']['request']
        
        # Obtém cabeçalhos atuais
        headers = request.get('headers', {})
        
        # Corrige inconsistências comuns
        if 'Accept-Encoding' in headers:
            # Garante suporte a Brotli
            if 'br' not in headers['Accept-Encoding']:
                headers['Accept-Encoding'] = 'gzip, deflate, br, zstd'
        
        # Remove marcadores de automação
        headers.pop('X-Requested-With', None)
        
        # Converte cabeçalhos para o formato HeaderEntry
        header_list = [{'name': k, 'value': v} for k, v in headers.items()]
        
        # Continua a requisição com cabeçalhos modificados
        await tab.continue_request(
            request_id=request_id,
            headers=header_list
        )
    
    # Registra ouvinte de eventos para eventos de requisição pausada
    await tab.on(FetchEvent.REQUEST_PAUSED, handle_request)


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Configura interceptação antes da navegação
        await setup_request_interception(tab)
        
        # Todas as requisições agora terão cabeçalhos modificados
        await tab.go_to('https://example.com')

asyncio.run(main())
```

### Exemplo Completo de Evasão de Fingerprint

Aqui está um exemplo abrangente combinando todas as técnicas usando a API do Pydoll:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions


class FingerprintEvader:
    """
    Evasão abrangente de fingerprint usando opções de navegador e JavaScript.
    """
    
    def __init__(self, profile: dict):
        """
        Inicializa com o perfil alvo (SO, localização, dispositivo, etc.)
        """
        self.profile = profile
        self.options = ChromiumOptions()
        self._configure_browser_options()
    
    def _configure_browser_options(self):
        """Configura opções de inicialização do navegador com base no perfil."""
        # 1. User-Agent
        self.options.add_argument(f'--user-agent={self.profile["userAgent"]}')
        
        # 2. Idioma e localidade
        self.options.add_argument(f'--lang={self.profile["locale"]}')
        self.options.set_accept_languages(self.profile["acceptLanguage"])
        
        # 3. Tamanho da janela (dimensões da tela)
        screen = self.profile['screen']
        self.options.add_argument(f'--window-size={screen["width"]},{screen["height"]}')
        
        # 4. Fator de escala do dispositivo (para telas high-DPI)
        if screen.get('deviceScaleFactor', 1.0) != 1.0:
            self.options.add_argument(f'--device-scale-factor={screen["deviceScaleFactor"]}')
    
    async def apply_to_tab(self, tab):
        """
        Aplica sobrescritas de JavaScript na aba após o lançamento.
        """
        script = f```
            // Sobrescreve User-Agent (para consistência)
            Object.defineProperty(Navigator.prototype, 'userAgent', {{
                get: () => '{self.profile["userAgent"]}'
            }});
            
            // Sobrescreve plataforma
            Object.defineProperty(Navigator.prototype, 'platform', {{
                get: () => '{self.profile["platform"]}'
            }});
            
            // Sobrescreve concorrência de hardware
            Object.defineProperty(Navigator.prototype, 'hardwareConcurrency', {{
                get: () => {self.profile.get('hardwareConcurrency', 8)}
            }});
            
            // Sobrescreve memória do dispositivo
            Object.defineProperty(Navigator.prototype, 'deviceMemory', {{
                get: () => {self.profile.get('deviceMemory', 8)}
            }});
            
            // Sobrescreve idiomas
            Object.defineProperty(Navigator.prototype, 'languages', {{
                get: () => {self.profile['languages']}
            }});
            
            // Sobrescreve fornecedor (vendor)
            Object.defineProperty(Navigator.prototype, 'vendor', {{
                get: () => '{self.profile.get('vendor', 'Google Inc.')}'
            }});
            
            // Sobrescreve max touch points (para mobile)
            Object.defineProperty(Navigator.prototype, 'maxTouchPoints', {{
                get: () => {self.profile.get('maxTouchPoints', 0)}
            }});
        ```
        
        await tab.execute_script(script)
        
        # Aplica geolocalização se fornecida
        if 'geolocation' in self.profile:
            await self._override_geolocation(tab)
        
        # Aplica fuso horário se fornecido
        if 'timezone' in self.profile:
            await self._override_timezone(tab)
    
    async def _override_geolocation(self, tab):
        """Sobrescreve API de geolocalização."""
        geo = self.profile['geolocation']
        script = f```
            navigator.geolocation.getCurrentPosition = function(success) {{
                const position = {{
                    coords: {{
                        latitude: {geo['latitude']},
                        longitude: {geo['longitude']},
                        accuracy: 1,
                        altitude: null,
                        altitudeAccuracy: null,
                        heading: null,
                        speed: null
                    }},
                    timestamp: Date.now()
                }};
                success(position);
            }};
        ```
        await tab.execute_script(script)
    
    async def _override_timezone(self, tab):
        """Sobrescreve funções relacionadas ao fuso horário."""
        timezone = self.profile['timezone']
        # Mapa de fuso horário para deslocamento em minutos
        offsets = {{
            'America/New_York': 300,
            'Europe/London': 0,
            'Asia/Tokyo': -540,
            'America/Los_Angeles': 480,
        }}
        offset = offsets.get(timezone, 0)
        
        script = f```
            // Sobrescreve Intl.DateTimeFormat
            const originalDateTimeFormat = Intl.DateTimeFormat;
            Intl.DateTimeFormat = function(...args) {{
                const options = args[1] || {{}};
                options.timeZone = '{timezone}';
                return new originalDateTimeFormat(args[0], options);
            }};
            
            // Sobrescreve Date.prototype.getTimezoneOffset
            Date.prototype.getTimezoneOffset = function() {{
                return {offset};
            }};
        ```
        await tab.execute_script(script)


# Exemplo de uso
async def main():
    # Define o perfil alvo
    profile = {{
        'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'platform': 'Win32',
        'acceptLanguage': 'en-US,en;q=0.9',
        'languages': ['en-US', 'en'],
        'timezone': 'America/New_York',
        'locale': 'en-US',
        'geolocation': {{
            'latitude': 40.7128,
            'longitude': -74.0060
        }},
        'screen': {{
            'width': 1920,
            'height': 1080,
            'deviceScaleFactor': 1.0
        }},
        'hardwareConcurrency': 8,
        'deviceMemory': 8,
        'vendor': 'Google Inc.',
        'maxTouchPoints': 0,  # Desktop
    }}
    
    # Cria evasor com perfil
    evader = FingerprintEvader(profile)
    
    # Inicia navegador com opções configuradas
    async with Chrome(options=evader.options) as browser:
        tab = await browser.start()
        
        # Aplica sobrescritas JavaScript
        await evader.apply_to_tab(tab)
        
        # Navega com fingerprint consistente
        await tab.go_to('https://example.com')
        
        # Verifica fingerprint
        result = await tab.execute_script(```
            return {
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                languages: navigator.languages,
                hardwareConcurrency: navigator.hardwareConcurrency,
                deviceMemory: navigator.deviceMemory,
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                maxTouchPoints: navigator.maxTouchPoints,
            };
        ```)
        
        fingerprint = result['result']['result']['value']
        
        print("Fingerprint Aplicado:")
        for key, value in fingerprint.items():
            print(f"  {key}: {value}")

asyncio.run(main())
```

!!! tip "Consistência do Fingerprint é Chave"
    O aspecto mais importante da evasão de fingerprint é a **consistência em todas as camadas**:
    
    1.  **Cabeçalhos HTTP** (User-Agent, Accept-Language, Sec-CH-UA)
    2.  **Propriedades do Navigator** (userAgent, platform, languages)
    3.  **Propriedades do Sistema** (fuso horário, localidade, resolução de tela)
    4.  **Fingerprint de Rede** (TLS, configurações HTTP/2)
    
    Uma única inconsistência pode revelar a automação!

!!! info "Referências de Emulação CDP"
    - **[Chrome DevTools Protocol: Domínio Emulation](https://chromedevtools.github.io/devtools-protocol/tot/Emulation/)** - Documentação oficial Emulation CDP
    - **[Chrome DevTools Protocol: Domínio Fetch](https://chromedevtools.github.io/devtools-protocol/tot/Fetch/)** - Documentação de interceptação de requisições
    - **[Fonte do Chromium Emulation](https://source.chromium.org/chromium/chromium/src/+/main:third_party/blink/renderer/core/inspector/inspector_emulation_agent.cc)** - Implementação de emulação no Chromium
    - **[Guia CDP Pydoll](./cdp.md)** - Usando CDP com Pydoll

## Estratégias de Evasão Comportamental

Dada a arquitetura baseada em CDP do Pydoll, o fingerprinting comportamental requer atenção cuidadosa aos padrões de interação semelhantes aos humanos. Para background teórico sobre detecção comportamental, veja [Fingerprinting Comportamental](./behavioral-fingerprinting.md).

### Estado Atual: Randomização Manual Necessária

Como documentado em [Interações Semelhantes a Humanas](../../features/automation/human-interactions.md), o Pydoll **atualmente requer implementação manual** de realismo comportamental:

- **Movimentos do mouse**: Devem ser implementados com curvas de Bezier e randomização
- **Digitação**: Requer entrada caractere por caractere com intervalos variáveis
- **Rolagem (Scrolling)**: Precisa de JavaScript manual com simulação de momentum
- **Sequências de eventos**: Deve garantir ordenação adequada (mousemove → mousedown → mouseup → click)

### Melhorias Futuras

Versões futuras do Pydoll incluirão realismo comportamental automatizado:

```python
# API Futura (ainda não implementada)
await element.click(
    realistic=True,              # Movimento automático de curva de Bezier
    offset='random',             # Deslocamento aleatório dentro dos limites
    thinking_time=(1.0, 3.0)     # Atraso aleatório antes da ação
)

await input_field.type_text(
    "human-like text",
    realistic=True,              # Velocidade de digitação variável com tempo de bigrama
    error_rate=0.05              # 5% de chance de erro de digitação + backspace
)

await tab.scroll_to(
    target_y=1000,
    realistic=True,              # Simulação de Momentum + inércia
    speed='medium'               # Velocidade de rolagem semelhante à humana
)
```

### Implementação Prática Agora

Até que a automação esteja embutida, siga estas práticas:

#### 1. Movimento do Mouse Antes de Cliques

```python
# Ruim: Clique instantâneo sem movimento
await element.click()  # Teleporta cursor e clica no centro

# Bom: Movimento realista primeiro
# (Implementação manual necessária)
await move_mouse_realistically(element)
await asyncio.sleep(random.uniform(0.1, 0.3))
await element.click(x_offset=random.randint(-10, 10))
```

#### 2. Velocidade de Digitação Variável

```python
# Ruim: Intervalo constante
await input.type_text("text", interval=0.1)  # Tempo robótico

# Bom: Intervalos variáveis por caractere
for char in "text":
    await input.type_text(char, interval=0)
    await asyncio.sleep(random.uniform(0.08, 0.22))
```

#### 3. Tempo de Pensamento (Thinking Time)

```python
# Ruim: Ação instantânea após carregamento da página
await tab.go_to('https://example.com')
await button.click()  # Rápido demais!

# Bom: Atraso natural para leitura/escaneamento
await tab.go_to('https://example.com')
await asyncio.sleep(random.uniform(2.0, 5.0))  # Ler página
await random_mouse_movement()  # Escanear com cursor
await button.click()  # Então agir
```

#### 4. Rolagem com Momentum

```python
# Ruim: Rolagem instantânea
await tab.execute_script("window.scrollTo(0, 1000)")

# Bom: Rolagem gradual com desaceleração
scroll_events = simulate_human_scroll(target=1000)
for delta, delay in scroll_events:
    await tab.execute_script(f"window.scrollBy(0, {delta})")
    await asyncio.sleep(delay)
```

!!! warning "Detecção Comportamental é Potencializada por ML"
    Sistemas anti-bot modernos usam machine learning treinado em bilhões de interações. Eles não usam regras simples — eles detectam **padrões estatísticos**. Foque em:
    
    1.  **Variabilidade**: Nenhuma duas ações devem ser idênticas
    2.  **Contexto**: Ações devem seguir sequências naturais
    3.  **Tempo**: Intervalos realistas baseados na biomecânica humana
    4.  **Consistência**: Não misture padrões de bot com padrões humanos

## Melhores Práticas para Evasão de Fingerprint

Com base em todas as técnicas cobertas neste guia, aqui estão as melhores práticas essenciais para evasão de fingerprinting bem-sucedida em automação web:

### 1. Comece com Perfis de Navegador Reais

Não invente fingerprints do zero. Capture perfis de navegadores reais e use-os:

```python
# Capture um fingerprint real do seu próprio navegador
# Visite https://browserleaks.com/ e colete todos os dados
REAL_PROFILES = {
    'windows_chrome': {
        'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
        'platform': 'Win32',
        'hardwareConcurrency': 8,
        'deviceMemory': 8,
        'canvas_hash': 'captured_from_real_browser',
        # ... todas as outras propriedades
    }
}
```

### 2. Mantenha Consistência em Todas as Camadas

**Verifique estes pontos de consistência:**

- User-Agent bate com navigator.userAgent
- Plataforma bate com SO do User-Agent
- Idioma bate com fuso horário/geolocalização
- Resolução de tela é realista para o dispositivo alegado
- Especificações de hardware batem com a plataforma alegada (núcleos de CPU, RAM)
- Fingerprints de Canvas/WebGL são estáveis (não randomizados)
- Fuso horário bate com cabeçalho Accept-Language
- Client Hints batem com User-Agent

### 3. Use Preferências do Navegador para Furtividade

Aproveite as preferências de navegador do Pydoll (veja [Preferências do Navegador](../features/configuration/browser-preferences.md)):

```python
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
options.browser_preferences = {
    # Simular histórico de uso
    'profile': {
        'created_by_version': '120.0.6099.130',
        'creation_time': str(time.time() - (90 * 24 * 60 * 60)),  # 90 dias atrás
        'exit_type': 'Normal',
    },
    
    # Configurações de conteúdo realistas
    'profile.default_content_setting_values': {
        'cookies': 1,
        'images': 1,
        'javascript': 1,
        'notifications': 2,  # Perguntar (realista)
    },
    
    # Manuseio de IP WebRTC (prevenir vazamentos)
    'webrtc': {
        'ip_handling_policy': 'disable_non_proxied_udp',
    },
}
```

### 4. Rotacione Fingerprints com Sabedoria

**Não** mude fingerprints com muita frequência no mesmo site:

```python
# Ruim: Novo fingerprint a cada requisição
for url in urls:
    fingerprint = generate_random_fingerprint()  # Suspeito!
    apply_fingerprint(tab, fingerprint)
    await tab.go_to(url)

# Bom: Fingerprint consistente por sessão
fingerprint = select_fingerprint_for_target(target_site)
apply_fingerprint(tab, fingerprint)

for url in urls:
    await tab.go_to(url)  # Mesmo fingerprint
```

### 5. Teste Seu Fingerprint

Use estas ferramentas para verificar seu fingerprint antes de implantar:

| Ferramenta | URL | Testa |
|---|---|---|
| **BrowserLeaks** | https://browserleaks.com/ | Abrangente: Canvas, WebGL, Fontes, IP, WebRTC |
| **AmIUnique** | https://amiunique.org/ | Análise de unicidade do fingerprint |
| **CreepJS** | https://abrahamjuliot.github.io/creepjs/ | Detecção avançada de mentiras |
| **Fingerprint.com Demo** | https://fingerprint.com/demo/ | Detecção de nível comercial |
| **PixelScan** | https://pixelscan.net/ | Análise de detecção de bot |
| **IPLeak** | https://ipleak.net/ | Vazamentos WebRTC, DNS, IP |

**Script de verificação:**

```python
async def verify_fingerprint(tab):
    """
    Verifica a consistência do fingerprint antes do uso real.
    """
    tests = []
    
    # Teste 1: Consistência User-Agent
    nav_ua = await tab.execute_script('return navigator.userAgent')
    print(f"User-Agent: {nav_ua[:50]}...")
    
    # Teste 2: Consistência Fuso Horário/Idioma
    tz = await tab.execute_script('return Intl.DateTimeFormat().resolvedOptions().timeZone')
    lang = await tab.execute_script('return navigator.language')
    print(f"Timezone: {tz}, Language: {lang}")
    
    # Teste 3: Detecção WebDriver
    webdriver = await tab.execute_script('return navigator.webdriver')
    if webdriver:
        print("navigator.webdriver é true! (DETECTADO)")
        tests.append(False)
    else:
        print("navigator.webdriver é undefined (OK)")
        tests.append(True)
    
    # Teste 4: Consistência Canvas
    canvas1 = await get_canvas_fingerprint(tab)
    await asyncio.sleep(0.5)
    canvas2 = await get_canvas_fingerprint(tab)
    if canvas1 == canvas2:
        print("Fingerprint Canvas é consistente (OK)")
        tests.append(True)
    else:
        print("Fingerprint Canvas inconsistente, ruído detectado (DETECTADO)")
        tests.append(False)
    
    # Teste 5: Plugins
    plugins = await tab.execute_script('return navigator.plugins.length')
    print(f"Plugins: {plugins}")
    
    return all(tests)
```

### 6. Combine com Realismo Comportamental

Evasão de fingerprint sozinha não é suficiente. Combine com:

- **Interações semelhantes a humanas** (veja [Interações Humanas](../features/automation/human-interactions.md))
- **Tempo natural** (atrasos aleatórios, tempo realista de interação com a página)
- **Manuseio de captcha comportamental** (veja [Contorno de Captcha Comportamental](../features/advanced/behavioral-captcha-bypass.md))
- **Cookies realistas** (veja [Cookies e Sessões](../features/browser-management/cookies-sessions.md))

### 7. Monitore por Detecção

Implemente logging para detectar quando sua automação é sinalizada:

```python
async def monitor_detection_signals(tab):
    """
    Monitora por sinais de detecção.
    """
    signals = await tab.execute_script(```
        () => {
            return {
                // Checar por scripts de detecção conhecidos
                fpjs: typeof window.Fingerprint !== 'undefined',
                datadome: typeof window.DD_RUM !== 'undefined',
                perimeter_x: typeof window._pxAppId !== 'undefined',
                cloudflare: document.querySelector('script[src*="challenges.cloudflare.com"]') !== null,
                
                // Checar por páginas de desafio
                is_captcha: document.title.includes('Captcha') || 
                           document.title.includes('Challenge') ||
                           document.body.innerText.includes('verification'),
            };
        }
    ```)
    
    if any(signals.values()):
        print("Sinais de detecção encontrados:")
        for key, value in signals.items():
            if value:
                print(f"  - {key}: detectado")
```

### 8. Use Proxies Corretamente

Fingerprinting em nível de rede requer uso adequado de proxy:

- **Combine localização do proxy** com fuso horário/idioma
- **Use proxies residenciais** para alvos de alto valor
- **Rotacione proxies** mas mantenha consistência de fingerprint por proxy
- **Teste vazamentos WebRTC** (veja [Configuração de Proxy](../features/configuration/proxy.md))

## Erros Comuns a Evitar

### Erro 1: Randomizar Tudo

```python
# Ruim: Fingerprint aleatório que não faz sentido
fingerprint = {
    'userAgent': 'Chrome 120 no Windows',
    'platform': 'Linux x86_64',  # Incompatibilidade!
    'hardwareConcurrency': random.randint(1, 32),  # Aleatório demais
    'deviceMemory': random.choice([0.5, 128]),  # Valores irreais
}
```

**Por que falha**: Navegadores reais têm configurações **consistentes e realistas**. Valores aleatórios criam combinações impossíveis.

### Erro 2: Ignorar Client Hints

```python
# Ruim: Definir User-Agent sem Client Hints
await tab.send_cdp_command('Emulation.setUserAgentOverride', {
    'userAgent': 'Chrome/120...',
    # Faltando userAgentMetadata!
})
# Resultado: Cabeçalhos Sec-CH-UA serão inconsistentes
```

### Erro 3: Injeção de Ruído no Canvas

```python
# Ruim: Adicionar ruído aleatório ao canvas
def add_canvas_noise(ctx):
    # Randomiza valores de pixel
    imageData = ctx.getImageData(0, 0, 100, 100)
    for i in range(len(imageData.data)):
        imageData.data[i] += random.randint(-5, 5)  # Injeção de ruído
    ctx.putImageData(imageData, 0, 0)
```

**Por que falha**: Ruído torna o fingerprint **inconsistente**, o que é em si detectável. Sites podem solicitar o fingerprint múltiplas vezes e detectar variações.

### Erro 4: User-Agents Desatualizados

```python
# Ruim: Usar versão antiga do navegador
userAgent = 'Mozilla/5.0 ... Chrome/90.0.0.0'  # 2 anos de idade!
```

**Por que falha**: Versões antigas sem recursos modernos são facilmente detectadas. Use versões dos últimos 3-6 meses.

### Erro 5: Detecção de Modo Headless

```python
# Ruim: Usar headless sem configuração adequada
options = ChromiumOptions()
options.headless = True  # Detectável via dimensões da janela
```

**Correção**: Use `--headless=new` com tamanho de janela realista:

```python
options = ChromiumOptions()
options.add_argument('--headless=new')
options.add_argument('--window-size=1920,1080')
```

## Conclusão

Fingerprinting de navegador e rede é um sofisticado jogo de gato e rato entre desenvolvedores de automação e sistemas anti-bot. O sucesso requer entendimento de fingerprinting em **múltiplas camadas**:

**Nível de Rede:**
- Características TCP/IP (TTL, tamanho da janela, opções)
- Padrões de handshake TLS (JA3, suítes de cifras, GREASE)
- Configurações HTTP/2 e prioridades de stream

**Nível de Navegador:**
- Consistência de cabeçalhos HTTP
- Propriedades da API JavaScript (navigator, screen, etc.)
- Renderização de Canvas e WebGL
- Técnicas de evasão baseadas em CDP

**Nível Comportamental:**
- Padrões de movimento do mouse e física (Lei de Fitts, curvas de Bezier)
- Dinâmica de teclado e ritmo de digitação (bigramas, tempo de permanência/voo)
- Momentum e inércia de rolagem
- Sequências de eventos e análise de tempo

**Pontos Chave:**

1.  **Consistência é primordial** - Um único desencontro pode revelar automação
2.  **Use perfis reais** - Não invente fingerprints do zero
3.  **CDP é poderoso** - Aproveite o domínio Emulation para modificações profundas
4.  **Teste exaustivamente** - Use sites de teste de fingerprinting antes de implantar
5.  **Combine camadas** - Evasão de Rede + Navegador + Comportamental
6.  **Mantenha-se atualizado** - Técnicas de detecção evoluem; mantenha fingerprints atuais

**Vantagens do Pydoll:**

- **Sem `navigator.webdriver`** (diferente de Selenium/Puppeteer)
- **Acesso direto ao CDP** para controle profundo do navegador
- **Interceptação de requisições** via domínio Fetch
- **Preferências do navegador** para histórico/configurações realistas
- **Arquitetura assíncrona** para padrões de tempo naturais

Com as técnicas neste guia, você pode criar automação de navegador **altamente furtiva** que imita o comportamento real do usuário em todos os níveis.

!!! tip "Continue Aprendendo"
    Fingerprinting é uma área de pesquisa ativa. Mantenha-se atualizado:
    
    - Acompanhando conferências de segurança (USENIX, Black Hat, DEF CON)
    - Monitorando fornecedores anti-bot (Akamai, Cloudflare, DataDome)
    - Testando seus fingerprints regularmente em sites de detecção
    - Lendo o código-fonte do Chromium para novos vetores de fingerprinting

## Leitura Adicional

### Guias Abrangentes

- **[Conceitos Principais Pydoll](../features/core-concepts.md)** - Entendendo a arquitetura Pydoll
- **[Chrome DevTools Protocol](./cdp.md)** - Análise profunda do uso do CDP
- **[Network Fingerprinting](./network-fingerprinting.md)** - Técnicas de identificação em nível de protocolo
- **[Browser Fingerprinting](./browser-fingerprinting.md)** - Métodos de detecção na camada de aplicação
- **[Behavioral Fingerprinting](./behavioral-fingerprinting.md)** - Análise e detecção de comportamento humano
- **[Opções do Navegador](../features/configuration/browser-options.md)** - Argumentos de linha de comando para furtividade
- **[Preferências do Navegador](../features/configuration/browser-preferences.md)** - Configurações internas para realismo
- **[Configuração de Proxy](../features/configuration/proxy.md)** - Anonimização em nível de rede
- **[Arquitetura de Proxy](./proxy-architecture.md)** - Fundamentos de rede e detecção
- **[Interações Humanas](../features/automation/human-interactions.md)** - Realismo comportamental
- **[Contorno de Captcha Comportamental](../features/advanced/behavioral-captcha-bypass.md)** - Lidando com desafios modernos

### Recursos Externos

- **[Código-Fonte do Chromium](https://source.chromium.org/chromium/chromium/src)** - Base de código oficial do Chromium
- **[Visualizador do Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/)** - Documentação CDP interativa
- **[Padrões Web W3C](https://www.w3.org/standards/)** - Especificações web oficiais
- **[IETF RFCs](https://www.ietf.org/rfc/)** - Padrões de protocolos de rede

### Artigos Acadêmicos

- **[Mowery, Shacham: "Pixel Perfect" (USENIX 2012)](https://www.usenix.org/conference/usenixsecurity12/technical-sessions/presentation/mowery)** - Pesquisa fundacional sobre fingerprinting de canvas
- **[Eckersley: "How Unique Is Your Browser?" (EFF 2010)](https://panopticlick.eff.org/static/browser-uniqueness.pdf)** - Estudo inicial sobre unicidade de navegadores
- **[Nikiforakis et al.: "Cookieless Monster" (IEEE 2013)](https://securitee.org/files/cookieless_sp2013.pdf)** - Técnicas avançadas de fingerprinting