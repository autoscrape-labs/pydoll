# Opções do Navegador (ChromiumOptions)

`ChromiumOptions` é seu hub central de configuração para personalizar o comportamento do navegador. Ele controla tudo, desde argumentos de linha de comando e localização do binário até estados de carregamento de página e preferências de conteúdo.

!!! info "Documentação Relacionada"
    - **[Preferências do Navegador](browser-preferences.md)** - Análise profunda do sistema interno de preferências do Chromium
    - **[Gerenciamento do Navegador](../browser-management/tabs.md)** - Trabalhando com instâncias e abas do navegador
    - **[Contextos](../browser-management/contexts.md)** - Contextos de navegação isolados

## Guia Rápido

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.constants import PageLoadState

async def main():
    # Criar e configurar opções
    options = ChromiumOptions()
    
    # Configuração básica
    options.headless = True
    options.start_timeout = 15
    options.page_load_state = PageLoadState.INTERACTIVE
    
    # Adicionar argumentos de linha de comando
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    # Métodos auxiliares para configurações comuns
    options.block_notifications = True
    options.block_popups = True
    options.set_default_download_directory('/tmp/downloads')
    
    # Usar as opções configuradas
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')

asyncio.run(main())
```

## Propriedades Principais

### Argumentos de Linha de Comando

O Chromium suporta centenas de "switches" (opções) de linha de comando que controlam o comportamento do navegador no nível mais profundo. Use `add_argument()` para passar flags diretamente para o processo do navegador.

```python
options = ChromiumOptions()

# Adicionar argumento único
options.add_argument('--disable-blink-features=AutomationControlled')

# Adicionar argumento com valor
options.add_argument('--window-size=1920,1080')
options.add_argument('--user-agent=Mozilla/5.0 ...')

# Remover argumento se necessário
options.remove_argument('--window-size=1920,1080')

# Obter todos os argumentos
all_args = options.arguments
```

!!! tip "Formato dos Argumentos"
    - Argumentos começando com `--` são flags: `--headless`, `--disable-gpu`
    - Argumentos com `=` têm valores: `--window-size=1920,1080`
    - Alguns aceitam múltiplos valores: `--disable-features=Feature1,Feature2`

**Veja a [Referência de Argumentos de Linha de Comando](#referência-de-argumentos-de-linha-de-comando) abaixo para listas abrangentes.**

### Localização do Binário

Especifique um executável de navegador personalizado em vez de usar o padrão do sistema:

```python
options = ChromiumOptions()

# Linux
options.binary_location = '/opt/google/chrome-beta/chrome'

# macOS
options.binary_location = '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary'

# Windows
options.binary_location = r'C:\Program Files\Google\Chrome Beta\Application\chrome.exe'
```

!!! info "Quando Definir a Localização do Binário"
    - Testar diferentes versões do Chrome (Estável, Beta, Canary)
    - Usar o Chromium em vez do Chrome
    - Usar instalações portáteis do navegador
    - Executar compilações específicas para depuração

### Timeout de Inicialização

Controle quanto tempo o Pydoll espera para o navegador iniciar e responder:

```python
options = ChromiumOptions()
options.start_timeout = 20  # segundos (padrão: 10)
```

!!! warning "Considerações sobre Timeout"
    - **Muito baixo**: O navegador pode não inicializar completamente, causando falhas na inicialização
    - **Muito alto**: Travamentos bloquearão sua automação por mais tempo
    - **Recomendado**: 10-15s para a maioria dos casos, 20-30s para sistemas lentos ou perfis de navegador pesados

### Modo Headless (Sem Interface Gráfica)

Execute o navegador sem uma interface de usuário visível:

```python
options = ChromiumOptions()
options.headless = True  # Adiciona automaticamente o argumento --headless

# Ou manualmente
options.add_argument('--headless')
options.add_argument('--headless=new')  # Novo modo headless (Chrome 109+)
```

| Modo | Argumento | Descrição |
|---|---|---|
| **Headful** (Com UI) | (nenhum) | Janela do navegador visível (padrão) |
| **Headless Clássico** | `--headless` | Modo headless legado |
| **Novo Headless** | `--headless=new` | Modo headless moderno (Chrome 109+, melhor compatibilidade) |

!!! tip "Novo Modo Headless"
    O modo `--headless=new` (Chrome 109+) oferece melhor compatibilidade com recursos web modernos e é mais difícil de detectar. Use-o para automação em produção.

### Estado de Carregamento da Página

Controle quando o `tab.go_to()` considera uma página "carregada":

```python
from pydoll.constants import PageLoadState

options = ChromiumOptions()
options.page_load_state = PageLoadState.INTERACTIVE  # ou PageLoadState.COMPLETE
```

| Estado | Quando a Navegação Completa | Caso de Uso |
|---|---|---|
| `COMPLETE` (padrão) | Evento `load` disparado, todos os recursos carregados | Esperar por imagens, fontes, scripts |
| `INTERACTIVE` | `DOMContentLoaded` disparado, DOM pronto | Navegação mais rápida, interagir com o DOM imediatamente |

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.constants import PageLoadState

async def compare_load_states():
    # Modo Complete - espera por tudo
    options_complete = ChromiumOptions()
    options_complete.page_load_state = PageLoadState.COMPLETE
    
    async with Chrome(options=options_complete) as browser:
        tab = await browser.start()
        
        import time
        start = time.time()
        await tab.go_to('https://example.com')
        complete_time = time.time() - start
        print(f"Modo COMPLETE: {complete_time:.2f}s")
    
    # Modo Interactive - DOM pronto é suficiente
    options_interactive = ChromiumOptions()
    options_interactive.page_load_state = PageLoadState.INTERACTIVE
    
    async with Chrome(options=options_interactive) as browser:
        tab = await browser.start()
        
        start = time.time()
        await tab.go_to('https://example.com')
        interactive_time = time.time() - start
        print(f"Modo INTERACTIVE: {interactive_time:.2f}s")

asyncio.run(compare_load_states())
```

!!! tip "Quando Usar INTERACTIVE"
    Use `INTERACTIVE` quando:
    
    - Você só precisa de acesso ao DOM, não de imagens/fontes
    - Raspagem de conteúdo de texto e estrutura
    - A velocidade é crítica
    - A página tem muitos recursos de carregamento lento
    
    Mantenha `COMPLETE` (padrão) quando:
    
    - Tirando screenshots (precisa de imagens carregadas)
    - Esperando aplicações pesadas em JavaScript inicializarem completamente
    - Testando o desempenho de carregamento da página

## Referência de Argumentos de Linha de Comando

O Chromium suporta centenas de "switches" de linha de comando. Abaixo estão os mais úteis para automação, organizados por categoria.

!!! info "Referência Completa"
    Lista completa de todos os switches do Chromium: [Switches de Linha de Comando do Chromium por Peter Beverloo](https://peter.sh/experiments/chromium-command-line-switches/)

### Desempenho e Gerenciamento de Recursos

Otimize o desempenho do navegador para uma automação mais rápida:

```python
options = ChromiumOptions()

# Desabilitar aceleração de GPU (headless, Docker, CI/CD)
options.add_argument('--disable-gpu')
options.add_argument('--disable-software-rasterizer')

# Reduzir uso de memória
options.add_argument('--disable-dev-shm-usage')  # Docker: supera o limite de tamanho do /dev/shm
options.add_argument('--disable-extensions')
options.add_argument('--disable-background-networking')

# Desabilitar recursos desnecessários
options.add_argument('--disable-sync')  # Sincronização de conta Google
options.add_argument('--disable-translate')
options.add_argument('--disable-background-timer-throttling')
options.add_argument('--disable-backgrounding-occluded-windows')
options.add_argument('--disable-renderer-backgrounding')

# Otimizações de rede
options.add_argument('--disable-features=NetworkPrediction')
options.add_argument('--dns-prefetch-disable')

# Janela e renderização
options.add_argument('--window-size=1920,1080')
options.add_argument('--window-position=0,0')
options.add_argument('--force-device-scale-factor=1')
```

| Argumento | Efeito | Quando Usar |
|---|---|---|
| `--disable-gpu` | Sem aceleração por GPU | Headless, Docker, servidores sem GPU |
| `--disable-dev-shm-usage` | Usar `/tmp` em vez de `/dev/shm` | Contêineres Docker com memória compartilhada pequena |
| `--disable-extensions` | Não carregar nenhuma extensão | Navegador limpo e rápido para automação |
| `--window-size=W,H` | Definir dimensões iniciais da janela | Screenshots, viewport consistente |
| `--force-device-scale-factor=1` | Desabilitar escalonamento high-DPI | Renderização consistente entre sistemas |

### Furtividade (Stealth) e Fingerprinting

Torne sua automação mais difícil de detectar com estes argumentos de linha de comando:

| Argumento | Propósito | Exemplo |
|---|---|---|
| `--disable-blink-features=AutomationControlled` | Remove a flag `navigator.webdriver` | Essencial para furtividade |
| `--user-agent=...` | Define um user agent realista e comum | Corresponder à região/dispositivo alvo |
| `--use-gl=swiftshader` | Renderizador WebGL por software | Evitar fingerprints de GPU únicos |
| `--force-webrtc-ip-handling-policy=...` | Prevenir vazamentos de IP via WebRTC | Usar `disable_non_proxied_udp` |
| `--lang=en-US` | Definir idioma do navegador | Corresponder ao locale alvo |
| `--accept-lang=en-US,en;q=0.9` | Cabeçalho Accept-Language | Preferências de idioma realistas |
| `--tz=America/New_York` | Definir fuso horário | Corresponder à região alvo |
| `--no-first-run` | Pular assistentes de primeira execução | Automação mais limpa |
| `--no-default-browser-check` | Pular aviso de navegador padrão | Evitar interrupções na UI |
| `--disable-reading-from-canvas` | Mitigação de fingerprinting de Canvas | Reduzir singularidade |
| `--disable-features=AudioServiceOutOfProcess` | Mitigação de fingerprinting de Áudio | Reduzir singularidade |

!!! warning "Corrida Armamentista da Detecção"
    Nenhuma técnica isolada garante a indetectabilidade. Combine múltiplas estratégias:
    
    1.  **Argumentos de linha de comando** (esta tabela)
    2.  **Preferências do navegador** - [Preferências do Navegador - Furtividade e Fingerprinting](browser-preferences.md#stealth-fingerprinting)
    3.  **Interações semelhantes a humanas** - [Interações Semelhantes a Humanas](../automation/human-interactions.md)
    4.  **Boa reputação de IP** - Use proxies residenciais com histórico limpo

### Segurança e Privacidade

Controle recursos de segurança e configurações de privacidade:

```python
options = ChromiumOptions()

# Sandbox (desabilite apenas para Docker/CI)
options.add_argument('--no-sandbox')  # RISCO DE SEGURANÇA - use apenas em ambientes controlados
options.add_argument('--disable-setuid-sandbox')

# HTTPS/SSL
options.add_argument('--ignore-certificate-errors')  # Ignorar erros SSL
options.add_argument('--ignore-ssl-errors')
options.add_argument('--allow-insecure-localhost')

# Privacidade
options.add_argument('--disable-features=Translate')
options.add_argument('--disable-sync')
options.add_argument('--incognito')  # Abrir em modo anônimo

# Concessão automática de permissões (para testes)
options.add_argument('--use-fake-ui-for-media-stream')  # Conceder automaticamente câmera/microfone
options.add_argument('--use-fake-device-for-media-stream')  # Usar dispositivos falsos
```

!!! danger "Avisos sobre o Sandbox"
    **`--no-sandbox` é um risco de segurança!** Use-o apenas quando:
    
    - Rodando em contêineres Docker (sandbox conflita com isolamento do contêiner)
    - Ambientes de CI/CD com permissões restritas
    - Você confia totalmente no conteúdo sendo carregado
    
    **Nunca** use `--no-sandbox` quando:
    
    - Visitando sites não confiáveis
    - Rodando código enviado por usuários
    - Em ambientes de produção com entrada externa

| Argumento | Efeito | Impacto na Segurança |
|---|---|---|
| `--no-sandbox` | Desabilita o sandbox do Chrome | **ALTO RISCO** - Permite execução de código |
| `--ignore-certificate-errors` | Pula validação SSL | **RISCO MÉDIO** - Possibilita ataques MITM |
| `--incognito` | Modo de navegação privada | Mais seguro - sem estado persistente |

### Depuração e Desenvolvimento

Ferramentas para depurar automação e desenvolvimento:

```python
options = ChromiumOptions()

# DevTools
options.add_argument('--auto-open-devtools-for-tabs')

# Logging
options.add_argument('--enable-logging')
options.add_argument('--v=1')  # Nível de verbosidade (0-3)
options.add_argument('--log-level=0')  # 0=INFO, 1=WARNING, 2=ERROR

# Tratamento de falhas
options.add_argument('--disable-crash-reporter')
options.add_argument('--no-crash-upload')

# Habilitar recursos experimentais
options.add_argument('--enable-features=NetworkService,NetworkServiceInProcess')
options.add_argument('--enable-experimental-web-platform-features')

# Depuração de JavaScript
options.add_argument('--js-flags=--expose-gc')  # Expõe o coletor de lixo
```

!!! tip "Depuração Remota"
    O Pydoll gerencia automaticamente a porta de depuração remota. Para acessar o Chrome DevTools:
    
    ```python
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Obter a porta de depuração
        port = browser._connection_port
        print(f"DevTools disponível em: http://localhost:{port}")
        
        # Abra esta URL no seu navegador para acessar o DevTools
    ```
    
    **Não** use o argumento `--remote-debugging-port` - ele entrará em conflito com o gerenciamento interno do Pydoll!

### Exibição e Renderização

Controle como o navegador renderiza o conteúdo:

```python
options = ChromiumOptions()

# Viewport e janela
options.add_argument('--window-size=1920,1080')
options.add_argument('--window-position=0,0')
options.add_argument('--start-maximized')
options.add_argument('--start-fullscreen')

# Telas High DPI
options.add_argument('--force-device-scale-factor=1')
options.add_argument('--high-dpi-support=1')

# Cor e renderização
options.add_argument('--force-color-profile=srgb')
options.add_argument('--disable-accelerated-2d-canvas')
options.add_argument('--disable-accelerated-video-decode')

# Renderização de fontes
options.add_argument('--font-render-hinting=none')
options.add_argument('--disable-font-subpixel-positioning')

# Animações
options.add_argument('--disable-animations')
options.add_argument('--wm-window-animations-disabled')
```

| Argumento | Efeito | Caso de Uso |
|---|---|---|
| `--window-size=W,H` | Define as dimensões da janela | Screenshots, viewport consistente |
| `--start-maximized` | Abre a janela maximizada | Testes de UI, capturas de tela cheia |
| `--force-device-scale-factor=1` | Desabilita escalonamento DPI | Renderização consistente entre sistemas |
| `--disable-animations` | Sem animações CSS/UI | Testes mais rápidos, reduz instabilidade |

### Configuração de Proxy

Configure proxies para todo o tráfego de rede:

```python
options = ChromiumOptions()

# Proxy HTTP/HTTPS
options.add_argument('--proxy-server=http://proxy.example.com:8080')

# Proxy autenticado
options.add_argument('--proxy-server=http://user:pass@proxy.example.com:8080')

# Proxy SOCKS
options.add_argument('--proxy-server=socks5://proxy.example.com:1080')

# Ignorar proxy para hosts específicos
options.add_argument('--proxy-bypass-list=localhost,127.0.0.1,*.local')

# Arquivo de auto-configuração de proxy (PAC)
options.add_argument('--proxy-pac-url=http://proxy.example.com/proxy.pac')
```

!!! info "Autenticação de Proxy"
    Para proxies que exigem autenticação, o Pydoll lida automaticamente com os desafios de autenticação ao usar o argumento `--proxy-server` com credenciais.
    
    Veja **[Interceptação de Requisições](../network/interception.md)** para detalhes sobre a interação do domínio Fetch com proxies.

## Métodos Auxiliares

`ChromiumOptions` fornece métodos convenientes para tarefas comuns de configuração:

### Gerenciamento de Downloads

```python
options = ChromiumOptions()

# Definir diretório de download
options.set_default_download_directory('/home/user/downloads')

# Perguntar pelo local de download
options.prompt_for_download = True  # Perguntar ao usuário onde salvar
options.prompt_for_download = False  # Baixar silenciosamente (padrão)

# Permitir múltiplos downloads automáticos
options.allow_automatic_downloads = True  # Permitir sem perguntar
options.allow_automatic_downloads = False  # Bloquear ou perguntar (padrão)
```

### Bloqueio de Conteúdo

```python
options = ChromiumOptions()

# Bloquear pop-ups
options.block_popups = True  # Bloquear (padrão na maioria dos casos)
options.block_popups = False  # Permitir

# Bloquear notificações
options.block_notifications = True  # Bloquear pedidos
options.block_notifications = False  # Permitir que sites perguntem
```

### Controles de Privacidade

```python
options = ChromiumOptions()

# Gerenciador de senhas
options.password_manager_enabled = False  # Desabilitar avisos de salvar senha
options.password_manager_enabled = True  # Habilitar (padrão)
```

### Manuseio de Arquivos

```python
options = ChromiumOptions()

# Comportamento de PDF
options.open_pdf_externally = True  # Baixar PDFs em vez de visualizar
options.open_pdf_externally = False  # Visualizar no navegador (padrão)
```

### Internacionalização

```python
options = ChromiumOptions()

# Idiomas aceitos (afeta o cabeçalho Content-Language)
options.set_accept_languages('en-US,en;q=0.9,pt-BR;q=0.8')
```

## Exemplos de Configuração Completa

### Configuração para Raspagem Rápida

Otimizado para velocidade e eficiência de recursos:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.constants import PageLoadState

def create_fast_scraping_options() -> ChromiumOptions:
    """Configuração ultrarrápida para web scraping."""
    options = ChromiumOptions()
    
    # Headless para velocidade
    options.headless = True
    
    # Carregamentos de página mais rápidos (DOM pronto é suficiente para scraping)
    options.page_load_state = PageLoadState.INTERACTIVE
    
    # Desabilitar recursos desnecessários
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-background-networking')
    options.add_argument('--disable-sync')
    options.add_argument('--disable-translate')
    
    # Bloquear conteúdo que retarda o carregamento
    options.block_notifications = True
    options.block_popups = True
    
    # Desabilitar imagens para carregamento ainda mais rápido (se você não precisar delas)
    options.add_argument('--blink-settings=imagesEnabled=false')
    
    # Otimizações de rede
    options.add_argument('--disable-features=NetworkPrediction')
    options.add_argument('--dns-prefetch-disable')
    
    return options

async def fast_scraping_example():
    options = create_fast_scraping_options()
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        # Navegação e raspagem super rápidas
        urls = ['https://example.com', 'https://example.org', 'https://example.net']
        
        for url in urls:
            await tab.go_to(url)
            title = await tab.execute_script('return document.title')
            print(f"{url}: {title}")

asyncio.run(fast_scraping_example())
```

### Configuração Completa de Furtividade (Stealth)

Para máxima indetectabilidade, combine argumentos de linha de comando com preferências do navegador:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

def create_full_stealth_options() -> ChromiumOptions:
    """Configuração completa de furtividade combinando argumentos e preferências."""
    options = ChromiumOptions()
    
    # ===== Argumentos de Linha de Comando =====
    
    # Furtividade principal
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-features=IsolateOrigins,site-per-process')
    
    # User agent (use um recente e comum)
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36')
    
    # Idioma e locale
    options.add_argument('--lang=en-US')
    options.add_argument('--accept-lang=en-US,en;q=0.9')
    
    # WebGL (renderizador por software para evitar assinaturas de GPU únicas)
    options.add_argument('--use-gl=swiftshader')
    options.add_argument('--disable-features=WebGLDraftExtensions')
    
    # Prevenção de vazamento de IP via WebRTC
    options.add_argument('--force-webrtc-ip-handling-policy=disable_non_proxied_udp')
    
    # Permissões e primeira execução
    options.add_argument('--no-first-run')
    options.add_argument('--no-default-browser-check')
    
    # Tamanho da janela (resolução comum)
    options.add_argument('--window-size=1920,1080')
    
    # ===== Preferências do Navegador =====
    # Para configuração abrangente de preferências do navegador, veja:
    # https://pydoll.tech/docs/features/configuration/browser-preferences/#stealth-fingerprinting
    
    return options

async def stealth_automation_example():
    options = create_full_stealth_options()
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        # Testar em sites de detecção de bots
        await tab.go_to('https://bot.sannysoft.com')
        await asyncio.sleep(5)
        
        # Sua automação aqui...

asyncio.run(stealth_automation_example())
```

!!! warning "Consistência do User-Agent é Crítica"
    Definir `--user-agent` altera apenas o **cabeçalho HTTP**, mas os sistemas de detecção também verificam `navigator.userAgent`, `navigator.platform`, `navigator.vendor` e outras propriedades JavaScript. **Inconsistências entre esses valores são um forte indicador de bot.**
    
    Por exemplo, se o seu User-Agent HTTP diz "Windows" mas o `navigator.platform` diz "Linux", você será sinalizado imediatamente.
    
    **Solução**: Você deve também sobrescrever as propriedades JavaScript via CDP para manter a consistência. Veja **[Fingerprinting do Navegador - Consistência do User-Agent](../../deep-dive/fingerprinting/browser-fingerprinting.md#user-agent-consistency)** para explicação detalhada e implementação usando `Page.addScriptToEvaluateOnNewDocument`.
    
    É por isso que a furtividade abrangente requer tanto argumentos de linha de comando QUANTO configuração de preferências do navegador.

!!! tip "Estratégia Completa de Furtividade"
    Argumentos de linha de comando são apenas parte da solução. Para máxima furtividade:
    
    1.  **Use os argumentos acima** (navigator.webdriver, WebGL, WebRTC)
    2.  **Configure as preferências do navegador** - Veja [Preferências do Navegador - Furtividade e Fingerprinting](browser-preferences.md#stealth-fingerprinting)
    3.  **Interações semelhantes a humanas** - Veja [Interações Semelhantes a Humanas](../automation/human-interactions.md)
    4.  **Boa reputação de IP/proxy** - Use proxies residenciais

### Configuração para Docker/CI

Para ambientes contêinerizados:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.constants import PageLoadState

def create_docker_options() -> ChromiumOptions:
    """Configuração para contêineres Docker e CI/CD."""
    options = ChromiumOptions()
    
    # Necessário para Docker
    options.headless = True
    options.add_argument('--no-sandbox')  # Sandbox conflita com isolamento do contêiner
    options.add_argument('--disable-dev-shm-usage')  # Supera o limite de tamanho do /dev/shm
    
    # Estabilidade
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-software-rasterizer')
    
    # Otimização de memória
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-background-networking')
    
    # Carregamentos de página mais rápidos para CI
    options.page_load_state = PageLoadState.INTERACTIVE
    
    # Aumentar timeout para runners de CI lentos
    options.start_timeout = 20
    
    # Tratamento de falhas
    options.add_argument('--disable-crash-reporter')
    
    return options

async def ci_testing_example():
    options = create_docker_options()
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        # Rode seus testes...
        await tab.go_to('https://example.com')
        assert await tab.execute_script('return document.title') == 'Example Domain'

asyncio.run(ci_testing_example())
```

## Solução de Problemas

### O Navegador Não Inicia

```python
# Aumente o timeout
options.start_timeout = 30

# Verifique a localização do binário
options.binary_location = '/path/to/chrome'

# Problemas com Docker/CI
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
```

### Desempenho Lento

```python
# Desabilite a GPU se não for necessária
options.add_argument('--disable-gpu')

# Desabilite imagens
options.add_argument('--blink-settings=imagesEnabled=false')

# Use o estado de carregamento INTERACTIVE
options.page_load_state = PageLoadState.INTERACTIVE

# Desabilite recursos desnecessários
options.add_argument('--disable-extensions')
options.add_argument('--disable-background-networking')
```

### Problemas de Memória no Docker

```python
# Essencial para Docker
options.add_argument('--disable-dev-shm-usage')

# Reduzir consumo de memória
options.add_argument('--disable-extensions')
options.add_argument('--disable-gpu')
options.add_argument('--single-process')  # Último recurso (pode ser instável)
```

## Leitura Adicional

- **[Preferências do Navegador](browser-preferences.md)** - Sistema interno de preferências do Chromium
- **[Automação Furtiva](../automation/human-interactions.md)** - Interações semelhantes a humanas
- **[Contextos](../browser-management/contexts.md)** - Contextos de navegação isolados
- **[Interceptação de Rede](../network/interception.md)** - Manipulação de requisições/respostas

!!! tip "Experimentação é Chave"
    A configuração do navegador é altamente dependente do seu caso de uso específico. Comece com os exemplos aqui, depois ajuste com base em suas necessidades. Use `browser._connection_port` para acessar o DevTools e inspecionar o que está acontecendo dentro do navegador.