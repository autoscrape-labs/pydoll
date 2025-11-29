# Fingerprinting em Nível de Navegador

Este documento explora o fingerprinting na camada de aplicação (HTTP/2, JavaScript, Canvas, WebGL). Enquanto o fingerprinting em nível de rede identifica o **SO e a pilha de rede**, o fingerprinting em nível de navegador revela o **navegador específico, versão e configuração**.

!!! info "Navegação do Módulo"
    - **[← Visão Geral de Fingerprinting](./index.md)** - Introdução e filosofia do módulo
    - **[← Network Fingerprinting (Fingerprinting de Rede)](./network-fingerprinting.md)** - Fingerprinting em nível de protocolo
    - **[→ Técnicas de Evasão](./evasion-techniques.md)** - Contramedidas práticas
    
    Para configuração prática do navegador, veja **[Opções do Navegador](../../features/configuration/browser-options.md)** e **[Preferências do Navegador](../../features/configuration/browser-preferences.md)**.

!!! warning "Consistência é Chave"
    O fingerprinting de navegador é a **principal camada de detecção** para a maioria dos sistemas anti-bot. Uma única inconsistência (como um User-Agent do Chrome com artefatos de canvas do Firefox) dispara o bloqueio imediato.

## Fingerprinting em Nível de Navegador

Enquanto o fingerprinting em nível de rede opera no nível do protocolo, o fingerprinting em nível de navegador explora características do próprio ambiente do navegador. Esta seção cobre técnicas modernas usadas para identificar navegadores, incluindo análise de HTTP/2, APIs JavaScript, motores de renderização e estratégias de evasão baseadas em CDP.

## Fingerprinting HTTP/2

As capacidades de enquadramento binário (binary framing) e multiplexação do HTTP/2 introduziram novos vetores de fingerprinting. Empresas como [Akamai](https://www.akamai.com/) foram pioneiras em técnicas de fingerprinting HTTP/2 para detectar bots e ferramentas automatizadas.

### Fingerprinting de Frame SETTINGS

O frame `SETTINGS` do HTTP/2, enviado durante a inicialização da conexão, revela preferências específicas da implementação. Navegadores diferentes enviam configurações distintamente diferentes.

**SETTINGS do Chrome (a partir da v120+):**

```python
chrome_http2_settings = {
    'SETTINGS_HEADER_TABLE_SIZE': 65536,        # 0x1
    'SETTINGS_MAX_CONCURRENT_STREAMS': 1000,    # 0x3
    'SETTINGS_INITIAL_WINDOW_SIZE': 6291456,    # 0x4 (6MB)
    'SETTINGS_MAX_HEADER_LIST_SIZE': 262144,    # 0x6
}
```

**SETTINGS do Firefox (a partir da v120+):**

```python
firefox_http2_settings = {
    'SETTINGS_HEADER_TABLE_SIZE': 65536,        # 0x1
    'SETTINGS_INITIAL_WINDOW_SIZE': 131072,     # 0x4 (128KB - muito menor!)
    'SETTINGS_MAX_FRAME_SIZE': 16384,           # 0x5 (16KB)
}
```

**Principais diferenças:**

| Configuração | Chrome | Firefox | Safari | curl | 
|---|---|---|---|---|
| **HEADER_TABLE_SIZE** | 65536 | 65536 | 4096 | 4096 |
| **MAX_CONCURRENT_STREAMS** | 1000 | 100 | 100 | 100 |
| **INITIAL_WINDOW_SIZE** | 6291456 | 131072 | 2097152 | 65535 |
| **MAX_FRAME_SIZE** | 16384 | 16384 | 16384 | 16384 |
| **MAX_HEADER_LIST_SIZE** | 262144 | (não definido) | (não definido) | (não definido) |

!!! warning "Detecção de Configurações HTTP/2"
    Ferramentas automatizadas como `requests`, `httpx`, e até `curl` enviam configurações HTTP/2 **diferentes** das de navegadores reais. Esta é uma das maneiras mais fáceis de detectar automação.

### Análise de Frame WINDOW_UPDATE

O HTTP/2 usa frames `WINDOW_UPDATE` para controle de fluxo. O **tamanho** e o **tempo** dessas atualizações variam por implementação:

```python
# Atualizações de janela em nível de conexão
http2_window_updates = {
    'Chrome': 15 * 1024 * 1024,      # 15MB
    'Firefox': 12 * 1024 * 1024,     # 12MB  
    'curl': 32 * 1024 * 1024,        # 32MB (suspeito!)
    'Python httpx': 65535,           # 64KB (padrão, suspeito!)
}
```

**Técnica de detecção:**

```python
# Pseudocódigo de fingerprinting HTTP/2 no lado do servidor
def fingerprint_http2_client(connection):
    """
    Analisa características HTTP/2 para identificar o cliente.
    """
    fingerprint = {
        'settings': parse_settings_frame(connection),
        'window_update': get_initial_window_update(connection),
        'priority_tree': analyze_stream_priorities(connection),
        'header_order': get_pseudo_header_order(connection),
    }
    
    # Compara contra fingerprints de navegadores conhecidos
    if fingerprint['window_update'] > 20_000_000:
        return 'Provavelmente curl ou httpx (muito grande)'
    
    if 'MAX_CONCURRENT_STREAMS' not in fingerprint['settings']:
        return 'Provavelmente biblioteca Python/Go (configuração ausente)'
    
    if fingerprint['settings']['INITIAL_WINDOW_SIZE'] == 6291456:
        return 'Provavelmente Chrome/Chromium'
    
    return 'Cliente desconhecido'
```

### Prioridade e Dependência de Stream

O HTTP/2 permite aos clientes especificar prioridades e dependências de stream usando frames `PRIORITY`. Navegadores criam árvores de prioridade sofisticadas para otimizar o carregamento da página.

**Árvore de prioridade do Chrome (simplificada):**

```
Stream 0 (conexão)
├─ Stream 3 (Documento HTML) - peso: 256
├─ Stream 5 (CSS) - peso: 220, depende do Stream 3
├─ Stream 7 (JavaScript) - peso: 220, depende do Stream 3
├─ Stream 9 (Imagem) - peso: 110, depende do Stream 3
└─ Stream 11 (Fonte) - peso: 110, depende do Stream 3
```

**Python requests/httpx (sem prioridades):**

```
Stream 0 (conexão)
└─ Stream 3 (requisição) - sem prioridade, sem dependências
```

!!! danger "Incompatibilidade da Árvore de Prioridade"
    Clientes HTTP automatizados raramente implementam árvores de prioridade sofisticadas. Prioridades ausentes ou simplistas são **fortes indicadores** de automação.

### Ordenação de Pseudo-Cabeçalhos

O HTTP/2 substitui a linha de requisição do HTTP/1.1 por pseudo-cabeçalhos (`:method`, `:path`, `:authority`, `:scheme`). A **ordem** desses cabeçalhos varia:

```python
# Ordem Chrome/Edge
chrome_order = [':method', ':path', ':authority', ':scheme']

# Ordem Firefox  
firefox_order = [':method', ':path', ':authority', ':scheme']

# Ordem Safari
safari_order = [':method', ':scheme', ':path', ':authority']

# Ordem curl/httpx (frequentemente diferente)
automated_order = [':method', ':authority', ':scheme', ':path']
```

**Código de detecção:**

```python
def detect_pseudo_header_order(headers: list[tuple[str, str]]) -> str:
    """Detecta cliente com base na ordem dos pseudo-cabeçalhos."""
    pseudo_headers = [h[0] for h in headers if h[0].startswith(':')]
    order_str = ','.join(pseudo_headers)
    
    patterns = {
        ':method,:path,:authority,:scheme': 'Chrome/Edge/Firefox',
        ':method,:scheme,:path,:authority': 'Safari',
        ':method,:authority,:scheme,:path': 'Ferramenta automatizada (curl/httpx)',
    }
    
    return patterns.get(order_str, 'Desconhecido')
```

### Analisando HTTP/2 com Python

```python
from h2.connection import H2Connection
from h2.config import H2Configuration
from h2.events import SettingsAcknowledged, WindowUpdated
import socket
import ssl


class HTTP2Analyzer:
    """
    Analisa características de conexão HTTP/2.
    """
    
    def __init__(self, hostname: str, port: int = 443):
        self.hostname = hostname
        self.port = port
        self.settings = {}
        self.window_updates = []
    
    def analyze_server_http2(self) -> dict:
        """
        Conecta ao servidor e analisa sua implementação HTTP/2.
        """
        # Cria socket
        sock = socket.create_connection((self.hostname, self.port))
        
        # Envolve com TLS
        context = ssl.create_default_context()
        context.set_alpn_protocols(['h2'])
        sock = context.wrap_socket(sock, server_hostname=self.hostname)
        
        # Cria conexão H2
        config = H2Configuration(client_side=True)
        conn = H2Connection(config=config)
        conn.initiate_connection()
        
        # Envia dados iniciais
        sock.sendall(conn.data_to_send())
        
        # Recebe prefácio do servidor
        data = sock.recv(65535)
        events = conn.receive_data(data)
        
        # Analisa eventos
        for event in events:
            if isinstance(event, SettingsAcknowledged):
                # Servidor confirmou nossas configurações
                pass
            elif isinstance(event, WindowUpdated):
                self.window_updates.append({
                    'stream_id': event.stream_id,
                    'delta': event.delta,
                })
        
        # Extrai configurações do servidor
        server_settings = conn.remote_settings
        
        sock.close()
        
        return {
            'settings': dict(server_settings),
            'window_updates': self.window_updates,
            'alpn_protocol': sock.selected_alpn_protocol(),
        }


# Uso
analyzer = HTTP2Analyzer('www.google.com')
result = analyzer.analyze_server_http2()
print(f"Configurações HTTP/2 do Servidor: {result['settings']}")
print(f"Atualizações de Janela: {result['window_updates']}")
```

!!! info "Referências de Fingerprinting HTTP/2"
    - **[Understanding HTTP/2 Fingerprinting](https://www.trickster.dev/post/understanding-http2-fingerprinting/)** por Trickster Dev - Guia abrangente sobre fingerprinting HTTP/2
    - **[HTTP/2 Fingerprinting](https://lwthiker.com/networks/2022/06/17/http2-fingerprinting.html)** por lwthiker - Análise técnica profunda das características HTTP/2
    - **[Akamai Bot Manager](https://www.akamai.com/products/bot-manager)** - Solução comercial usando fingerprinting HTTP/2
    - **[Guia de Fingerprinting HTTP/2 da Multilogin](https://multilogin.com/glossary/http2-fingerprinting/)** - Perspectiva prática sobre detecção HTTP/2

## Consistência de Cabeçalhos HTTP

Além de frames específicos do HTTP/2, cabeçalhos HTTP padrão fornecem ricos dados de fingerprinting. A chave é a **consistência** através de múltiplas características.

### Análise do Cabeçalho User-Agent

O cabeçalho `User-Agent` é o vetor de fingerprinting mais óbvio, mas também é o mais comumente falsificado:

```python
# User-Agent típico do Chrome
chrome_ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# User-Agent típico do Firefox
firefox_ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0'

# User-Agent suspeito (versão desatualizada)
suspicious_ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.0.0 Safari/537.36'
```

**Problemas comuns com User-Agents falsificados:**

1.  **Versão desatualizada**: Alega ser Chrome 90 em 2025
2.  **Incompatibilidade de SO**: Alega "Windows NT 10.0" mas envia valores TTL de Linux
3.  **Inconsistência de plataforma**: Alega "Windows" mas `navigator.platform` retorna "Linux"
4.  **Recursos do navegador ausentes**: Alega ser Chrome 120 mas não suporta recursos introduzidos na v110

### Consistência do Accept-Language

O cabeçalho `Accept-Language` deve corresponder às configurações de idioma do navegador/SO:

```python
# Exemplos de inconsistência
inconsistencies = {
    # Cabeçalho diz Inglês, mas fuso horário é GMT+9 (Japão)
    'accept_language': 'en-US,en;q=0.9',
    'timezone': 'Asia/Tokyo',  # Suspeito!
    
    # Cabeçalho tem um único idioma, mas navigator.languages tem muitos
    'header': 'en-US',
    'navigator_languages': ['en-US', 'en', 'pt-BR', 'pt', 'es'],  # Incompatibilidade!
}
```

**Configuração adequada:**

```python
import pytz
from datetime import datetime

def generate_consistent_accept_language(primary_lang: str, timezone_str: str) -> dict:
    """
    Gera cabeçalhos de idioma consistentes com base no fuso horário.
    """
    # Mapeamentos idioma-fuso horário (simplificado)
    tz_to_lang = {
        'America/New_York': 'en-US,en;q=0.9',
        'Europe/London': 'en-GB,en;q=0.9',
        'Asia/Tokyo': 'ja-JP,ja;q=0.9,en;q=0.8',
        'Europe/Berlin': 'de-DE,de;q=0.9,en;q=0.8',
        'America/Sao_Paulo': 'pt-BR,pt;q=0.9,en;q=0.8',
    }
    
    expected_lang = tz_to_lang.get(timezone_str, 'en-US,en;q=0.9')
    
    if primary_lang not in expected_lang:
        print(f"Aviso: Idioma {primary_lang} inconsistente com fuso horário {timezone_str}")
    
    return {
        'accept_language_header': expected_lang,
        'navigator_languages': expected_lang.replace(';q=0.9', '').replace(';q=0.8', '').split(','),
        'timezone': timezone_str,
    }


# Exemplo
config = generate_consistent_accept_language('ja', 'Asia/Tokyo')
print(config)
# Saída:
# {
#     'accept_language_header': 'ja-JP,ja;q=0.9,en;q=0.8',
#     'navigator_languages': ['ja-JP', 'ja', 'en'],
#     'timezone': 'Asia/Tokyo'
# }
```

### Cabeçalho Accept-Encoding

Navegadores modernos suportam algoritmos de compressão específicos:

```python
# Chrome/Edge (suporte a Brotli)
chrome_encoding = 'gzip, deflate, br, zstd'

# Firefox  
firefox_encoding = 'gzip, deflate, br'

# Ferramentas antigas/automatizadas (sem Brotli)
automated_encoding = 'gzip, deflate'  # Suspeito em 2024+
```

!!! warning "Detecção de Suporte a Brotli"
    Qualquer navegador moderno (2024+) **deve** suportar Brotli (`br`). A falta de Brotli indica uma ferramenta automatizada ou um navegador muito desatualizado.

### Sec-CH-UA (Client Hints)

Navegadores Chromium modernos enviam cabeçalhos [Client Hints](https://developer.mozilla.org/en-US/docs/Web/HTTP/Client_hints):

```http
Sec-CH-UA: "Chromium";v="120", "Google Chrome";v="120", "Not:A-Brand";v="99"
Sec-CH-UA-Mobile: ?0
Sec-CH-UA-Platform: "Windows"
Sec-CH-UA-Platform-Version: "15.0.0"
Sec-CH-UA-Arch: "x86"
Sec-CH-UA-Bitness: "64"
Sec-CH-UA-Full-Version: "120.0.6099.130"
Sec-CH-UA-Model: ""
```

**Verificações de consistência:**

```python
def validate_client_hints(headers: dict, navigator_props: dict) -> list[str]:
    """
    Valida a consistência dos Client Hints com as propriedades do navigator.
    """
    issues = []
    
    # Extrai Sec-CH-UA
    sec_ch_ua = headers.get('sec-ch-ua', '')
    sec_ch_platform = headers.get('sec-ch-ua-platform', '').strip('"')
    sec_ch_mobile = headers.get('sec-ch-ua-mobile', '')
    
    # Verifica consistência da plataforma
    nav_platform = navigator_props.get('platform', '')
    if sec_ch_platform == 'Windows' and 'Win' not in nav_platform:
        issues.append(f"Incompatibilidade de plataforma: Sec-CH-UA diz {sec_ch_platform}, navigator.platform diz {nav_platform}")
    
    # Verifica consistência móvel
    nav_mobile = navigator_props.get('userAgentData', {}).get('mobile', False)
    if sec_ch_mobile == '?1' and not nav_mobile:
        issues.append("Incompatibilidade móvel: Sec-CH-UA-Mobile diz móvel, mas navigator diz desktop")
    
    # Verifica consistência da marca com User-Agent
    user_agent = headers.get('user-agent', '')
    if 'Chrome' in sec_ch_ua and 'Chrome' not in user_agent:
        issues.append("Incompatibilidade de marca: Sec-CH-UA menciona Chrome, mas User-Agent não")
    
    return issues


# Exemplo
headers = {
    'sec-ch-ua': '"Chromium";v="120", "Google Chrome";v="120"',
    'sec-ch-ua-platform': '"Windows"',
    'sec-ch-ua-mobile': '?0',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

navigator = {
    'platform': 'Win32',
    'userAgentData': {'mobile': False},
}

issues = validate_client_hints(headers, navigator)
if issues:
    print("Inconsistências detectadas:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("Client Hints estão consistentes")
```

### Fingerprinting de Ordem de Cabeçalhos

A **ordem** dos cabeçalhos HTTP é específica do navegador e frequentemente ignorada ao falsificar:

```python
# Ordem de cabeçalhos do Chrome (típica)
chrome_header_order = [
    ':method',
    ':path',
    ':authority',
    ':scheme',
    'cache-control',
    'sec-ch-ua',
    'sec-ch-ua-mobile',
    'sec-ch-ua-platform',
    'upgrade-insecure-requests',
    'user-agent',
    'accept',
    'sec-fetch-site',
    'sec-fetch-mode',
    'sec-fetch-dest',
    'referer',
    'accept-encoding',
    'accept-language',
    'cookie',
]

# Ordem de cabeçalhos do Firefox (diferente!)
firefox_header_order = [
    ':method',
    ':path',
    ':authority',
    ':scheme',
    'user-agent',
    'accept',
    'accept-language',
    'accept-encoding',
    'referer',
    'dnt',
    'connection',
    'upgrade-insecure-requests',
    'sec-fetch-dest',
    'sec-fetch-mode',
    'sec-fetch-site',
    'cookie',
]
```

**Detecção:**

```python
def fingerprint_by_header_order(request_headers: list[tuple[str, str]]) -> str:
    """
    Identifica o navegador com base na ordem dos cabeçalhos.
    """
    header_names = [h[0].lower() for h in request_headers]
    order_signature = ','.join(header_names[:10])  # Primeiros 10 cabeçalhos
    
    # Assinaturas de navegadores conhecidos
    signatures = {
        ':method,:path,:authority,:scheme,cache-control,sec-ch-ua': 'Chrome/Edge',
        ':method,:path,:authority,:scheme,user-agent,accept': 'Firefox',
        'host,connection,accept,user-agent,referer': 'Requests/httpx (suspeito!)',
    }
    
    for sig, browser in signatures.items():
        if order_signature.startswith(sig):
            return browser
    
    return 'Desconhecido (possivelmente falsificado)'
```

!!! info "Referências de Fingerprinting de Cabeçalho HTTP"
    - **[HTTP Fingerprinting](https://www.yeswehack.com/learn-bug-bounty/recon-series-http-fingerprinting)** por YesWeHack - Guia para reconhecimento baseado em HTTP
    - **[Client Hints (MDN)](https://developer.mozilla.org/en-US/docs/Web/HTTP/Client_hints)** - Documentação oficial sobre cabeçalhos Sec-CH-UA
    - **[HTTP Header Order Fingerprinting](https://lwthiker.com/networks/2022/06/17/tls-fingerprinting.html)** - Discussão sobre técnicas de ordenação de cabeçalhos

## Fingerprinting de Propriedades JavaScript

O JavaScript fornece acesso extensivo a propriedades do navegador e do sistema através dos objetos `window` e `navigator`. Essas propriedades são os atributos de fingerprinting mais comumente usados.

### Propriedades do Objeto Navigator

O objeto `navigator` expõe dezenas de propriedades que revelam características do navegador:

```javascript
// Propriedades centrais do navigator
const fingerprint = {
    // User Agent
    userAgent: navigator.userAgent,
    appVersion: navigator.appVersion,
    platform: navigator.platform,
    
    // Idioma
    language: navigator.language,
    languages: navigator.languages,
    
    // Hardware
    hardwareConcurrency: navigator.hardwareConcurrency,  // Núcleos de CPU
    deviceMemory: navigator.deviceMemory,  // RAM em GB (aproximação)
    
    // Recursos
    cookieEnabled: navigator.cookieEnabled,
    doNotTrack: navigator.doNotTrack,
    maxTouchPoints: navigator.maxTouchPoints,
    
    // Fornecedor (Vendor)
    vendor: navigator.vendor,
    vendorSub: navigator.vendorSub,
    
    // Produto
    product: navigator.product,
    productSub: navigator.productSub,
    
    // OS CPU (legado, mas ainda disponível)
    oscpu: navigator.oscpu,  // Apenas Firefox
};
```

**Propriedades específicas do Chrome:**

```javascript
// Chrome User Agent Data (API Client Hints)
if (navigator.userAgentData) {
    const uaData = {
        brands: navigator.userAgentData.brands,
        mobile: navigator.userAgentData.mobile,
        platform: navigator.userAgentData.platform,
    };
    
    // Solicita valores de alta entropia (requer permissão)
    navigator.userAgentData.getHighEntropyValues([
        'architecture',
        'bitness',
        'model',
        'platformVersion',
        'uaFullVersion',
    ]).then(highEntropyValues => {
        console.log('Valores de Alta Entropia:', highEntropyValues);
        // {
        //     architecture: "x86",
        //     bitness: "64",
        //     model: "",
        //     platformVersion: "15.0.0",
        //     uaFullVersion: "120.0.6099.130"
        // }
    });
}
```

### Propriedades de Tela (Screen) e Janela (Window)

Características de exibição são altamente distintas:

```javascript
const screenFingerprint = {
    // Dimensões da tela
    width: screen.width,
    height: screen.height,
    availWidth: screen.availWidth,
    availHeight: screen.availHeight,
    
    // Profundidade de cor
    colorDepth: screen.colorDepth,
    pixelDepth: screen.pixelDepth,
    
    // Proporção de pixels do dispositivo (Telas Retina)
    devicePixelRatio: window.devicePixelRatio,
    
    // Dimensões da janela
    innerWidth: window.innerWidth,
    innerHeight: window.innerHeight,
    outerWidth: window.outerWidth,
    outerHeight: window.outerHeight,
    
    // Orientação da tela
    orientation: {
        type: screen.orientation?.type,
        angle: screen.orientation?.angle,
    },
};
```

**Detecção de ambientes virtualizados/headless:**

```python
def detect_headless_chrome(properties: dict) -> list[str]:
    """
    Detecta Chrome headless com base em inconsistências de propriedades.
    """
    issues = []
    
    # Chrome Headless tem outerWidth/Height = innerWidth/Height (sem bordas de UI)
    if properties['outerWidth'] == properties['innerWidth']:
        issues.append("outerWidth == innerWidth (suspeito para navegador com UI)")
    
    # Headless frequentemente tem dimensões de tela == dimensões da janela
    if properties['screen']['width'] == properties['innerWidth']:
        issues.append("Largura da tela == largura da janela (possivelmente headless)")
    
    # Chrome Headless reporta user agent específico
    if 'HeadlessChrome' in properties.get('userAgent', ''):
        issues.append("User-Agent diz explicitamente HeadlessChrome")
    
    # navigator.webdriver deve ser undefined em navegadores reais
    if properties.get('webdriver') == True:
        issues.append("navigator.webdriver é true (automação detectada)")
    
    return issues
```

### Plugins e Tipos MIME (Legado)

Navegadores modernos descontinuaram a enumeração de plugins, mas ainda é um vetor de fingerprinting:

```javascript
// Plugins (obsoleto, mas ainda exposto)
const plugins = [];
for (let i = 0; i < navigator.plugins.length; i++) {
    plugins.push({
        name: navigator.plugins[i].name,
        description: navigator.plugins[i].description,
        filename: navigator.plugins[i].filename,
    });
}

// Tipos MIME (obsoleto)
const mimeTypes = [];
for (let i = 0; i < navigator.mimeTypes.length; i++) {
    mimeTypes.push({
        type: navigator.mimeTypes[i].type,
        description: navigator.mimeTypes[i].description,
        suffixes: navigator.mimeTypes[i].suffixes,
    });
}
```

!!! warning "Detecção de Enumeração de Plugin"
    **Chrome/Firefox Modernos**: Retornam arrays vazios para `navigator.plugins` e `navigator.mimeTypes` para prevenir fingerprinting.
    
    **Chrome Headless**: Frequentemente retorna arrays **vazios** mesmo quando plugins existem, revelando automação.
    
    **Detecção**: Se o navegador alega ser Chrome mas não tem plugins, é suspeito.

### Propriedades de Fuso Horário (Timezone) e Data

Informações de fuso horário são surpreendentemente reveladoras:

```javascript
const timezoneFingerprint = {
    // Deslocamento de fuso horário em minutos
    timezoneOffset: new Date().getTimezoneOffset(),
    
    // Nome do fuso horário IANA (ex: "America/New_York")
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    
    // Localidade (Locale)
    locale: Intl.DateTimeFormat().resolvedOptions().locale,
    
    // Formatação de data
    dateFormat: new Date().toLocaleDateString(),
    timeFormat: new Date().toLocaleTimeString(),
};
```

**Verificação de consistência:**

```python
def validate_timezone_consistency(tz_offset: int, tz_name: str, accept_language: str) -> list[str]:
    """
    Valida consistência do fuso horário com idioma/localização.
    """
    issues = []
    
    # Mapeamentos esperados fuso horário-idioma
    tz_to_languages = {
        'America/New_York': ['en-US', 'en'],
        'Europe/London': ['en-GB', 'en'],
        'Asia/Tokyo': ['ja-JP', 'ja'],
        'Europe/Berlin': ['de-DE', 'de'],
    }
    
    expected_langs = tz_to_languages.get(tz_name, [])
    primary_lang = accept_language.split(',')[0].split(';')[0]
    
    if expected_langs and primary_lang not in expected_langs:
        issues.append(f"Fuso horário {tz_name} inconsistente com idioma {primary_lang}")
    
    # Validação de deslocamento de fuso horário
    expected_offsets = {
        'America/New_York': -300,  # EST (minutos)
        'Europe/London': 0,        # GMT
        'Asia/Tokyo': -540,        # JST
    }
    
    expected_offset = expected_offsets.get(tz_name)
    if expected_offset and tz_offset != expected_offset:
        issues.append(f"Deslocamento {tz_offset} não bate com {tz_name}")
    
    return issues
```

### Permissões e API de Bateria

Algumas APIs requerem permissão do usuário, mas ainda podem aplicar fingerprinting:

```javascript
// API de Bateria (se disponível)
if (navigator.getBattery) {
    navigator.getBattery().then(battery => {
        const batteryInfo = {
            charging: battery.charging,
            chargingTime: battery.chargingTime,
            dischargingTime: battery.dischargingTime,
            level: battery.level,
        };
        // Nível da bateria pode ser usado como entropia
    });
}

// Permissões
navigator.permissions.query({name: 'geolocation'}).then(result => {
    console.log('Permissão de Geolocalização:', result.state);
    // 'granted', 'denied', 'prompt'
});
```

!!! danger "Detecção de navigator.webdriver"
    A propriedade `navigator.webdriver` é o indicador de automação **mais óbvio**:
    
    ```javascript
    if (navigator.webdriver === true) {
        alert('Automação detectada!');
    }
    ```
    
    **Selenium, Puppeteer, Playwright** todos definem isso como `true` por padrão. Automação CDP (como Pydoll) **não** define esta propriedade, tornando-a mais furtiva.

### Implementação Python: Coletando Propriedades do Navegador

```python
async def collect_browser_fingerprint(tab) -> dict:
    """
    Coleta fingerprint abrangente do navegador usando Pydoll.
    """
    fingerprint = await tab.execute_script(```
        () => {
            return {
                // Navigator
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                language: navigator.language,
                languages: navigator.languages,
                hardwareConcurrency: navigator.hardwareConcurrency,
                deviceMemory: navigator.deviceMemory,
                maxTouchPoints: navigator.maxTouchPoints,
                vendor: navigator.vendor,
                cookieEnabled: navigator.cookieEnabled,
                doNotTrack: navigator.doNotTrack,
                webdriver: navigator.webdriver,
                
                // Screen
                screen: {
                    width: screen.width,
                    height: screen.height,
                    availWidth: screen.availWidth,
                    availHeight: screen.availHeight,
                    colorDepth: screen.colorDepth,
                    pixelDepth: screen.pixelDepth,
                },
                
                // Window
                window: {
                    innerWidth: window.innerWidth,
                    innerHeight: window.innerHeight,
                    outerWidth: window.outerWidth,
                    outerHeight: window.outerHeight,
                    devicePixelRatio: window.devicePixelRatio,
                },
                
                // Timezone
                timezone: {
                    offset: new Date().getTimezoneOffset(),
                    name: Intl.DateTimeFormat().resolvedOptions().timeZone,
                },
                
                // Plugins (legado, mas ainda checado)
                plugins: Array.from(navigator.plugins).map(p => ({
                    name: p.name,
                    description: p.description,
                })),
                
                // User Agent Data (Chrome)
                userAgentData: navigator.userAgentData ? {
                    brands: navigator.userAgentData.brands,
                    mobile: navigator.userAgentData.mobile,
                    platform: navigator.userAgentData.platform,
                } : null,
            };
        }
    ```)
    
    return fingerprint


# Exemplo de uso
import asyncio
from pydoll.browser.chromium import Chrome

async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        
        fingerprint = await collect_browser_fingerprint(tab)
        
        print("Browser Fingerprint:")
        print(f"  User-Agent: {fingerprint['userAgent']}")
        print(f"  Platform: {fingerprint['platform']}")
        print(f"  Languages: {fingerprint['languages']}")
        print(f"  Hardware Concurrency: {fingerprint['hardwareConcurrency']}")
        print(f"  Screen: {fingerprint['screen']['width']}x{fingerprint['screen']['height']}")
        print(f"  Timezone: {fingerprint['timezone']['name']}")
        print(f"  Webdriver: {fingerprint['webdriver']}")

asyncio.run(main())
```

!!! info "Referências de Propriedades JavaScript"
    - **[Fingerprint.com: Técnicas de Fingerprinting de Navegador](https://fingerprint.com/blog/browser-fingerprinting-techniques/)** - Guia abrangente de todos os métodos de fingerprinting
    - **[NordLayer: Guia de Fingerprinting de Navegador](https://nordlayer.com/learn/browser-security/browser-fingerprinting/)** - Como funciona o fingerprinting de navegador
    - **[AIMultiple: Melhores Práticas de Fingerprinting de Navegador](https://research.aimultiple.com/browser-fingerprinting/)** - Análise técnica de técnicas de fingerprinting
    - **[Bureau.id: Top 9 Técnicas de Fingerprinting](https://www.bureau.id/blog/browser-fingerprinting-techniques)** - Detalhamento de métodos de detecção

## Fingerprinting de Canvas

O fingerprinting de Canvas explora diferenças sutis em como navegadores renderizam gráficos no elemento HTML5 `<canvas>`. Essas diferenças surgem de variações em hardware (GPU), drivers gráficos, sistemas operacionais e implementações do navegador.

### Como Funciona o Fingerprinting de Canvas

A técnica envolve:
1.  Desenhar texto/formas específicas em um canvas
2.  Extrair os dados de pixel com `toDataURL()` ou `getImageData()`
3.  Aplicar hash ao resultado para criar um fingerprint único

**Fatores que afetam a renderização do canvas:**
- **GPU e drivers**: GPUs diferentes renderizam anti-aliasing de forma diferente
- **Sistema Operacional**: Renderização de fontes varia (ClearType no Windows, FreeType no Linux)
- **Motor do navegador**: WebKit vs Blink vs Gecko têm pipelines de renderização diferentes
- **Bibliotecas gráficas**: Skia (Chrome) vs Cairo (Firefox)

### Técnica de Fingerprinting de Canvas

```javascript
function generateCanvasFingerprint() {
    // Cria canvas
    const canvas = document.createElement('canvas');
    canvas.width = 220;
    canvas.height = 30;
    
    const ctx = canvas.getContext('2d');
    
    // Renderização de texto (mais distinta)
    ctx.textBaseline = 'top';
    ctx.font = '14px "Arial"';
    ctx.textBaseline = 'alphabetic';
    
    // Adiciona gradientes de cor (expõe diferenças de renderização)
    ctx.fillStyle = '#f60';
    ctx.fillRect(125, 1, 62, 20);
    
    // Adiciona cor semitransparente (diferenças de blending)
    ctx.fillStyle = '#069';
    ctx.fillText('Cwm fjordbank glyphs vext quiz, 😃', 2, 15);
    
    ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
    ctx.fillText('Cwm fjordbank glyphs vext quiz, 😃', 4, 17);
    
    // Extrai data URL
    const dataURL = canvas.toDataURL();
    
    // Gera hash (MD5, SHA-256, etc.)
    return hashString(dataURL);
}

// Função de hash mais simples para demo
function hashString(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Converte para inteiro de 32 bits
    }
    return hash.toString(16);
}
```

**Por que a string de teste específica?**

- **"Cwm fjordbank glyphs vext quiz"**: Pangrama com caracteres incomuns para maximizar variações de renderização de fonte
- **Emoji (😃)**: Renderização de emoji varia significativamente entre sistemas
- **Fontes/tamanhos mistos**: Aumenta a entropia

### Unicidade do Fingerprint de Canvas

Pesquisa da [USENIX](https://www.usenix.org/conference/usenixsecurity12/technical-sessions/presentation/mowery) mostra:
- **5.5% de chance** de dois usuários aleatórios terem o mesmo fingerprint de canvas
- Quando combinado com outras técnicas, a unicidade aumenta para **99.24%**

### Detectando Fingerprinting de Canvas

Sites detectam tentativas de modificação de fingerprint:

```javascript
// Detecta se o canvas está sendo bloqueado/modificado
const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;

HTMLCanvasElement.prototype.toDataURL = function() {
    // Verifica se o fingerprint é consistente
    const result = originalToDataURL.apply(this, arguments);
    
    // Se o resultado muda a cada chamada → fingerprint falso detectado
    return result;
};

// Detecção avançada: Checa por injeção de ruído
function detectCanvasNoise(canvas) {
    const ctx = canvas.getContext('2d');
    
    // Desenha padrão conhecido
    ctx.fillStyle = '#ff0000';
    ctx.fillRect(0, 0, 10, 10);
    
    // Lê pixels de volta
    const imageData = ctx.getImageData(0, 0, 10, 10);
    const pixels = imageData.data;
    
    // Checa se é exatamente vermelho (255, 0, 0) ou se há ruído
    for (let i = 0; i < pixels.length; i += 4) {
        if (pixels[i] !== 255 || pixels[i + 1] !== 0 || pixels[i + 2] !== 0) {
            return true;  // Ruído detectado = bloqueio de fingerprint
        }
    }
    
    return false;  // Canvas limpo
}
```

### Implementação Python com Pydoll

```python
import hashlib
import asyncio
from pydoll.browser.chromium import Chrome


async def get_canvas_fingerprint(tab) -> str:
    """
    Gera fingerprint de canvas usando Pydoll.
    """
    fingerprint = await tab.execute_script(```
        () => {
            const canvas = document.createElement('canvas');
            canvas.width = 220;
            canvas.height = 30;
            
            const ctx = canvas.getContext('2d');
            
            // Renderização de texto
            ctx.textBaseline = 'top';
            ctx.font = '14px "Arial"';
            ctx.textBaseline = 'alphabetic';
            
            // Blocos de cor
            ctx.fillStyle = '#f60';
            ctx.fillRect(125, 1, 62, 20);
            
            // Texto com emoji
            ctx.fillStyle = '#069';
            ctx.fillText('Cwm fjordbank glyphs vext quiz, 😃', 2, 15);
            
            ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
            ctx.fillText('Cwm fjordbank glyphs vext quiz, 😃', 4, 17);
            
            // Retorna data URL
            return canvas.toDataURL();
        }
    ```)
    
    # Aplica hash aos dados do canvas
    canvas_hash = hashlib.sha256(fingerprint.encode()).hexdigest()
    
    return canvas_hash


async def compare_canvas_consistency(tab, iterations: int = 3) -> bool:
    """
    Verifica se o fingerprint de canvas é consistente (não gerado aleatoriamente).
    """
    fingerprints = []
    
    for _ in range(iterations):
        fp = await get_canvas_fingerprint(tab)
        fingerprints.append(fp)
        await asyncio.sleep(0.1)
    
    # Todos os fingerprints devem ser idênticos
    is_consistent = len(set(fingerprints)) == 1
    
    if not is_consistent:
        print("Fingerprint de Canvas inconsistente (possível falsificação)")
        print(f"  Valores únicos: {len(set(fingerprints))}")
    
    return is_consistent


# Uso
async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        
        canvas_fp = await get_canvas_fingerprint(tab)
        print(f"Canvas Fingerprint: {canvas_fp}")
        
        is_consistent = await compare_canvas_consistency(tab)
        print(f"Verificação de consistência: {'PASS' if is_consistent else 'FAIL'}")

asyncio.run(main())
```

!!! warning "Detecção de Bloqueio de Fingerprint de Canvas"
    Muitas ferramentas anti-fingerprinting injetam **ruído aleatório** nos dados do canvas para prevenir rastreamento. No entanto, isso cria um **fingerprint inconsistente** que muda a cada requisição, o que é em si detectável!
    
    **Técnica de detecção:**

    1.  Solicita fingerprint de canvas múltiplas vezes
    2.  Se os valores diferem → injeção de ruído detectada
    3.  Sinaliza como "bloqueio de fingerprint = comportamento suspeito"

## Fingerprinting de WebGL

O fingerprinting de WebGL é mais poderoso que o de Canvas porque expõe informações detalhadas sobre a **GPU, drivers e pilha gráfica**.

### Informações do Renderizador WebGL

Os dados WebGL mais distintos vêm da extensão `WEBGL_debug_renderer_info`:

```javascript
function getWebGLFingerprint() {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    
    if (!gl) {
        return null;  // WebGL não suportado
    }
    
    const fingerprint = {
        // Obter info de debug (mais distinto)
        debugInfo: (() => {
            const ext = gl.getExtension('WEBGL_debug_renderer_info');
            if (ext) {
                return {
                    vendor: gl.getParameter(ext.UNMASKED_VENDOR_WEBGL),
                    renderer: gl.getParameter(ext.UNMASKED_RENDERER_WEBGL),
                };
            }
            return {
                vendor: gl.getParameter(gl.VENDOR),
                renderer: gl.getParameter(gl.RENDERER),
            };
        })(),
        
        // Extensões suportadas
        extensions: gl.getSupportedExtensions(),
        
        // Parâmetros WebGL
        parameters: {
            version: gl.getParameter(gl.VERSION),
            shadingLanguageVersion: gl.getParameter(gl.SHADING_LANGUAGE_VERSION),
            maxTextureSize: gl.getParameter(gl.MAX_TEXTURE_SIZE),
            maxViewportDims: gl.getParameter(gl.MAX_VIEWPORT_DIMS),
            maxRenderbufferSize: gl.getParameter(gl.MAX_RENDERBUFFER_SIZE),
            maxVertexAttribs: gl.getParameter(gl.MAX_VERTEX_ATTRIBS),
            maxVertexUniformVectors: gl.getParameter(gl.MAX_VERTEX_UNIFORM_VECTORS),
            maxFragmentUniformVectors: gl.getParameter(gl.MAX_FRAGMENT_UNIFORM_VECTORS),
            maxVaryingVectors: gl.getParameter(gl.MAX_VARYING_VECTORS),
            aliasedLineWidthRange: gl.getParameter(gl.ALIASED_LINE_WIDTH_RANGE),
            aliasedPointSizeRange: gl.getParameter(gl.ALIASED_POINT_SIZE_RANGE),
        },
        
        // Formatos de precisão
        precisionFormats: {
            vertexShader: {
                highFloat: getShaderPrecisionFormat(gl, gl.VERTEX_SHADER, gl.HIGH_FLOAT),
                mediumFloat: getShaderPrecisionFormat(gl, gl.VERTEX_SHADER, gl.MEDIUM_FLOAT),
                lowFloat: getShaderPrecisionFormat(gl, gl.VERTEX_SHADER, gl.LOW_FLOAT),
            },
            fragmentShader: {
                highFloat: getShaderPrecisionFormat(gl, gl.FRAGMENT_SHADER, gl.HIGH_FLOAT),
                mediumFloat: getShaderPrecisionFormat(gl, gl.FRAGMENT_SHADER, gl.MEDIUM_FLOAT),
                lowFloat: getShaderPrecisionFormat(gl, gl.FRAGMENT_SHADER, gl.LOW_FLOAT),
            },
        },
    };
    
    return fingerprint;
}

function getShaderPrecisionFormat(gl, shaderType, precisionType) {
    const format = gl.getShaderPrecisionFormat(shaderType, precisionType);
    return {
        rangeMin: format.rangeMin,
        rangeMax: format.rangeMax,
        precision: format.precision,
    };
}
```

**Saída de exemplo:**

```json
{
    "debugInfo": {
        "vendor": "Google Inc. (NVIDIA)",
        "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Direct3D11 vs_5_0 ps_5_0)"
    },
    "extensions": [
        "ANGLE_instanced_arrays",
        "EXT_blend_minmax",
        "EXT_color_buffer_half_float",
        "EXT_disjoint_timer_query",
        "EXT_float_blend",
        "EXT_frag_depth",
        "EXT_shader_texture_lod",
        "EXT_texture_compression_bptc",
        "EXT_texture_filter_anisotropic",
        "WEBKIT_EXT_texture_filter_anisotropic",
        "EXT_sRGB",
        "OES_element_index_uint",
        "OES_fbo_render_mipmap",
        "OES_standard_derivatives",
        "OES_texture_float",
        "OES_texture_float_linear",
        "OES_texture_half_float",
        "OES_texture_half_float_linear",
        "OES_vertex_array_object",
        "WEBGL_color_buffer_float",
        "WEBGL_compressed_texture_s3tc",
        "WEBGL_compressed_texture_s3tc_srgb",
        "WEBGL_debug_renderer_info",
        "WEBGL_debug_shaders",
        "WEBGL_depth_texture",
        "WEBGL_draw_buffers",
        "WEBGL_lose_context",
        "WEBGL_multi_draw"
    ],
    "parameters": {
        "version": "WebGL 1.0 (OpenGL ES 2.0 Chromium)",
        "shadingLanguageVersion": "WebGL GLSL ES 1.0 (OpenGL ES GLSL ES 1.0 Chromium)",
        "maxTextureSize": 16384,
        "maxViewportDims": [32767, 32767],
        "maxRenderbufferSize": 16384
    }
}
```

### Fingerprint de Renderização WebGL

Além de metadados, o WebGL pode renderizar uma cena 3D e analisar a saída de pixels:

```javascript
function getWebGLRenderFingerprint() {
    const canvas = document.createElement('canvas');
    canvas.width = 256;
    canvas.height = 128;
    
    const gl = canvas.getContext('webgl');
    
    // Vertex shader
    const vertexShaderSource = `
        attribute vec2 position;
        void main() {
            gl_Position = vec4(position, 0.0, 1.0);
        }
    `;
    
    // Fragment shader com gradiente
    const fragmentShaderSource = `
        precision mediump float;
        void main() {
            gl_FragColor = vec4(gl_FragCoord.x/256.0, gl_FragCoord.y/128.0, 0.5, 1.0);
        }
    `;
    
    // Compila shaders
    const vertexShader = gl.createShader(gl.VERTEX_SHADER);
    gl.shaderSource(vertexShader, vertexShaderSource);
    gl.compileShader(vertexShader);
    
    const fragmentShader = gl.createShader(gl.FRAGMENT_SHADER);
    gl.shaderSource(fragmentShader, fragmentShaderSource);
    gl.compileShader(fragmentShader);
    
    // Linka programa
    const program = gl.createProgram();
    gl.attachShader(program, vertexShader);
    gl.attachShader(program, fragmentShader);
    gl.linkProgram(program);
    gl.useProgram(program);
    
    // Desenha triângulo
    const vertices = new Float32Array([-1, -1, 1, -1, 0, 1]);
    const buffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);
    
    const position = gl.getAttribLocation(program, 'position');
    gl.enableVertexAttribArray(position);
    gl.vertexAttribPointer(position, 2, gl.FLOAT, false, 0, 0);
    
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    
    // Extrai imagem renderizada
    return canvas.toDataURL();
}
```

### Implementação Python com Pydoll

```python
async def get_webgl_fingerprint(tab) -> dict:
    """
    Coleta dados de fingerprinting WebGL.
    """
    fingerprint = await tab.execute_script(```
        () => {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            
            if (!gl) {
                return null;
            }
            
            // Obter info de debug
            const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
            const vendor = debugInfo ? 
                gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) : 
                gl.getParameter(gl.VENDOR);
            const renderer = debugInfo ? 
                gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : 
                gl.getParameter(gl.RENDERER);
            
            return {
                vendor: vendor,
                renderer: renderer,
                version: gl.getParameter(gl.VERSION),
                shadingLanguageVersion: gl.getParameter(gl.SHADING_LANGUAGE_VERSION),
                extensions: gl.getSupportedExtensions(),
                maxTextureSize: gl.getParameter(gl.MAX_TEXTURE_SIZE),
                maxViewportDims: gl.getParameter(gl.MAX_VIEWPORT_DIMS),
            };
        }
    ```)
    
    return fingerprint


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        
        webgl_fp = await get_webgl_fingerprint(tab)
        
        if webgl_fp:
            print("WebGL Fingerprint:")
            print(f"  Vendor: {webgl_fp['vendor']}")
            print(f"  Renderer: {webgl_fp['renderer']}")
            print(f"  Version: {webgl_fp['version']}")
            print(f"  Extensions: {len(webgl_fp['extensions'])} available")
        else:
            print("WebGL not available")

asyncio.run(main())
```

!!! danger "Bloqueio de Fingerprint WebGL"
    Algumas ferramentas de privacidade tentam bloquear o fingerprinting de WebGL ao:
    
    1.  **Desabilitar a extensão WEBGL_debug_renderer_info**
    2.  **Retornar renderizador "SwiftShader" genérico** (renderização por software)
    3.  **Falsificar strings de fornecedor/renderizador da GPU**
    
    No entanto, **dados WebGL ausentes ou genéricos são suspeitos** porque:
    - 97% dos navegadores suportam WebGL
    - Renderizadores genéricos têm implicações de desempenho (detectáveis via tempo)
    - Ausência de extensões comuns revela bloqueio

!!! info "Referências de Fingerprinting de Canvas e WebGL"
    - **[USENIX: Pixel Perfect Browser Fingerprinting](https://www.usenix.org/conference/usenixsecurity12/technical-sessions/presentation/mowery)** - Pesquisa acadêmica original sobre fingerprinting de canvas (2012)
    - **[Fingerprint.com: Canvas Fingerprinting](https://fingerprint.com/blog/canvas-fingerprinting/)** - Técnicas modernas de fingerprinting de canvas
    - **[BrowserLeaks WebGL Report](https://browserleaks.com/webgl)** - Teste seu fingerprint WebGL
    - **[Implementação WebGL do Chromium](https://source.chromium.org/chromium/chromium/src/+/main:third_party/blink/renderer/modules/webgl/)** - Código-fonte do WebGL no Chromium