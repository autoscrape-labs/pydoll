# Interação com Cloudflare Turnstile

O Pydoll oferece suporte nativo para interagir com captchas Cloudflare Turnstile realizando cliques realistas do navegador. Isso **não é um bypass ou evasão**. Ele simplesmente automatiza a mesma ação de clique que um humano realizaria na caixa de seleção do captcha.

!!! warning "O que esta Funcionalidade Realmente Faz"
    Esta funcionalidade **clica** na caixa de seleção do captcha Cloudflare Turnstile usando interações padrão do navegador. É isso. Não há:
    
    - **NÃO**: Bypass mágico ou evasão
    - **NÃO**: Resolução de desafios (seleção de imagens, quebra-cabeças, etc.)
    - **NÃO**: Manipulação de pontuação ou falsificação de fingerprint
    - **SIM**: Apenas um clique realista no contêiner do captcha
    
    **O sucesso depende inteiramente do seu ambiente** (reputação do IP, fingerprint do navegador, padrões de comportamento). O Pydoll fornece o mecanismo para clicar; seu ambiente determina se o clique é aceito.

!!! info "O que é o Cloudflare Turnstile?"
    O Cloudflare Turnstile é um sistema de captcha moderno que analisa o ambiente do navegador e sinais comportamentais para determinar se você é humano. Ele geralmente aparece como uma caixa de seleção que os usuários devem clicar. O sistema analisa:
    
    - **Reputação do IP**: Seu endereço IP está sinalizado ou é suspeito?
    - **Fingerprint do Navegador**: Seu navegador parece legítimo?
    - **Padrões Comportamentais**: Você se comporta como um humano?
    
    Quando a pontuação de confiança é alta o suficiente, o clique na caixa de seleção é aceito. Quando está muito baixa, o Turnstile pode mostrar um desafio (que o Pydoll **não pode resolver**) ou bloqueá-lo totalmente.

## Guia Rápido

### Gerenciador de Contexto (Recomendado)

O gerenciador de contexto espera o captcha aparecer, clica nele e espera pela resolução antes de continuar:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def turnstile_example():
    options = ChromiumOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        # Gerenciador de contexto lida com o captcha automaticamente
        async with tab.expect_and_bypass_cloudflare_captcha():
            await tab.go_to('https://site-with-turnstile.com')
        
        # Este código só roda após o captcha ser clicado
        print("Interação com o captcha Turnstile concluída!")
        
        # Continue com sua automação
        content = await tab.find(id='protected-content')
        print(await content.text)

asyncio.run(turnstile_example())
```

### Processamento em Segundo Plano

Habilite o clique automático do captcha em segundo plano:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def background_turnstile():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Habilitar clique automático antes de navegar
        await tab.enable_auto_solve_cloudflare_captcha()
        
        # Navegar para o site protegido
        await tab.go_to('https://site-with-turnstile.com')
        
        # Esperar o captcha ser processado em segundo plano
        await asyncio.sleep(5)
        
        print("Página carregada com manejo de captcha em segundo plano")
        
        # Desabilitar quando não for mais necessário
        await tab.disable_auto_solve_cloudflare_captcha()

asyncio.run(background_turnstile())
```

## Personalizando a Interação com o Captcha

### Seletor Personalizado

Alguns sites usam nomes de classe ou invólucros (wrappers) diferentes para o captcha:

```python
from pydoll.constants import By

async def custom_selector_example():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Use um seletor personalizado se o padrão não funcionar
        custom_selector = (By.CLASS_NAME, 'custom-captcha-wrapper')
        
        async with tab.expect_and_bypass_cloudflare_captcha(
            custom_selector=custom_selector
        ):
            await tab.go_to('https://site-with-custom-turnstile.com')
        
        print("Seletor personalizado usado com sucesso!")

asyncio.run(custom_selector_example())
```

!!! tip "Encontrando o Seletor Correto"
    Para encontrar o seletor correto:
    
    1. Abra o site no Chrome DevTools
    2. Inspecione o iframe/contêiner do captcha
    3. Procure por nomes de classe ou IDs únicos
    4. Use esse seletor com o parâmetro `custom_selector`
    
    O seletor padrão é `(By.CLASS_NAME, 'cf-turnstile')`, que funciona para a maioria das implementações padrão do Cloudflare Turnstile.

### Configuração de Tempo (Timing)

A caixa de seleção do captcha nem sempre aparece imediatamente. Ajuste o tempo para corresponder ao comportamento do site:

```python
async def timing_configuration_example():
    async with Chrome() as browser:
        tab = await browser.start()
        
        async with tab.expect_and_bypass_cloudflare_captcha(
            time_before_click=3,      # Esperar 3 segundos antes de clicar (padrão: 2)
            time_to_wait_captcha=10   # Esperar até 10 segundos pelo captcha aparecer (padrão: 5)
        ):
            await tab.go_to('https://site-with-slow-turnstile.com')
        
        print("Interação com o captcha concluída com tempo personalizado!")

asyncio.run(timing_configuration_example())
```

**Referência de Parâmetros:**

| Parâmetro | Tipo | Padrão | Descrição |
|---|---|---|---|
| `custom_selector` | `Optional[tuple[By, str]]` | `(By.CLASS_NAME, 'cf-turnstile')` | Seletor CSS para o contêiner do captcha |
| `time_before_click` | `int` | `2` | Segundos para esperar antes de clicar (simula tempo de pensamento humano) |
| `time_to_wait_captcha` | `int` | `5` | Segundos máximos para esperar o captcha aparecer |

!!! info "Por que o Tempo Importa"
    - **`time_before_click`**: Simula o tempo de reação humano. Clicar muito rápido pode parecer suspeito.
    - **`time_to_wait_captcha`**: Alguns sites carregam o captcha assincronamente. Se o captcha não aparecer dentro desse tempo, a interação é pulada.

## Outros Sistemas de Captcha

### reCAPTCHA v3 (Invisível)

O reCAPTCHA v3 é **completamente invisível** e **não requer interação**. Apenas navegue normalmente:

```python
async def recaptcha_v3_example():
    options = ChromiumOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        # Nenhum tratamento especial necessário - apenas navegue
        await tab.go_to('https://site-with-recaptcha-v3.com')
        
        # reCAPTCHA v3 roda em segundo plano, analisando seu comportamento
        await asyncio.sleep(3)
        
        # Continue com o envio do formulário
        submit_button = await tab.find(id='submit-btn')
        await submit_button.click()

asyncio.run(recaptcha_v3_example())
```

!!! note "Fatores de Sucesso do reCAPTCHA v3"
    Como o reCAPTCHA v3 é inteiramente passivo (sem interação), o sucesso depende de:
    
    - **Reputação do IP**: Use proxies residenciais com boa reputação
    - **Fingerprint do Navegador**: Configure preferências de navegador realistas
    - **Padrões Comportamentais**: Passe tempo na página, role naturalmente, digite realisticamente
    
    Se sua pontuação for muito baixa, alguns sites podem mostrar um desafio reCAPTCHA v2 (que o Pydoll **não pode resolver**).

## O que Determina o Sucesso?

O sucesso da interação com o captcha depende **inteiramente do seu ambiente**, não do Pydoll. O sistema de captcha analisa:

### 1. Reputação do IP (Mais Crítico)

| Tipo de IP | Nível de Confiança | Comportamento Esperado |
|---|---|---|
| **IP Residencial (limpo)** | Alto | Geralmente aceito sem desafios |
| **IP Móvel** | Alto | Geralmente aceito sem desafios |
| **IP de Datacenter** | Baixo | Frequentemente bloqueado ou desafiado |
| **IP previamente bloqueado** | Muito Baixo | Quase sempre bloqueado ou desafiado |

!!! danger "Reputação do IP é Tudo"
    **Nenhuma ferramenta pode superar um endereço IP ruim.** Se seu IP estiver sinalizado, você será bloqueado ou desafiado, independentemente de quão realista seu navegador pareça.
    
    Use proxies residenciais com boa reputação para melhores resultados.

### 2. Fingerprint do Navegador

Configure seu navegador para parecer legítimo:

```python
import time
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def stealth_configuration():
    options = ChromiumOptions()
    
    # Argumentos de furtividade
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--window-size=1920,1080')
    
    # Preferências de navegador realistas
    current_time = int(time.time())
    options.browser_preferences = {
        'profile': {
            'last_engagement_time': str(current_time - (3 * 60 * 60)),  # 3 horas atrás
            'exited_cleanly': True,
            'exit_type': 'Normal',
        },
        'safebrowsing': {'enabled': True},
    }
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        async with tab.expect_and_bypass_cloudflare_captcha():
            await tab.go_to('https://site-with-turnstile.com')

asyncio.run(stealth_configuration())
```

### 3. Padrões Comportamentais

Sistemas de captcha analisam como você interage com a página:

```python
async def realistic_behavior():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://site-with-turnstile.com')
        
        # Simular comportamento humano antes do captcha aparecer
        await asyncio.sleep(2)  # Ler conteúdo da página
        await tab.execute_script('window.scrollBy(0, 300)')  # Rolar
        await asyncio.sleep(1)
        
        # Agora interagir com o captcha
        async with tab.expect_and_bypass_cloudflare_captcha():
            # A interação com o captcha acontece aqui
            pass
        
        print("Captcha passado com comportamento realista!")

asyncio.run(realistic_behavior())
```

!!! tip "Fingerprinting Comportamental"
    Para um entendimento aprofundado de como os padrões comportamentais afetam o sucesso do captcha, veja **[Fingerprinting Comportamental](../../deep-dive/fingerprinting/behavioral-fingerprinting.md)**. Este guia explica:
    
    - Padrões de movimento do mouse e detecção
    - Análise de tempo de pressionamento de teclas
    - Física do comportamento de rolagem
    - Análise de sequência de eventos
    
    Entender esses conceitos pode ajudá-lo a construir uma automação mais realista que alcança taxas de sucesso mais altas.

## Solução de Problemas

### Captcha Não Está Sendo Clicado

**Sintomas**: O captcha aparece, mas nunca é clicado, a página permanece no desafio.

**Causas Possíveis:**

1.  **Seletor errado**: O site usa classe/ID de elemento diferente
2.  **Tempo muito curto**: O captcha ainda não carregou quando o Pydoll tenta clicar
3.  **Elemento não visível**: O captcha está oculto ou renderizado de forma diferente

**Soluções:**

```python
async def troubleshooting_example():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Aumentar tempos de espera e usar seletor personalizado
        async with tab.expect_and_bypass_cloudflare_captcha(
            custom_selector=(By.CLASS_NAME, 'your-selector-here'),
            time_before_click=5,     # Atraso maior antes de clicar
            time_to_wait_captcha=15  # Mais tempo para encontrar o captcha
        ):
            await tab.go_to('https://problematic-site.com')

asyncio.run(troubleshooting_example())
```

### Captcha Clicado, mas Mostra Desafio

**Sintomas**: A caixa de seleção mostra a marca de verificação brevemente, depois apresenta um desafio de imagem/quebra-cabeça.

**Causa Raiz**: A pontuação de confiança do seu ambiente está muito baixa.

**Soluções:**

- Use proxies residenciais com boa reputação
- Configure um fingerprint de navegador realista
- Adicione padrões comportamentais mais realistas (rolagem, movimento do mouse, atrasos)
- **Nota**: O Pydoll não pode resolver o desafio em si

### "Acesso Negado" ou Bloqueio Imediato

**Sintomas**: O site mostra imediatamente "Acesso Negado" ou bloqueia você sem mostrar o captcha.

**Causa Raiz**: **Seu endereço IP está sinalizado.**

**Soluções:**

- Use um proxy residencial diferente com boa reputação
- Rotacione IPs entre as requisições
- Teste seu IP em `https://www.cloudflare.com/cdn-cgi/trace`
- **Nota**: Nenhuma configuração de navegador corrigirá um IP sinalizado

### Funciona Localmente, mas Falha no Docker/CI

**Sintomas**: A interação com o captcha funciona na sua máquina, mas falha em ambientes Docker/CI.

**Causa Raiz**: IPs de datacenter são examinados de perto pelos sistemas de captcha.

**Soluções:**

1.  **Use o modo headless com exibição adequada** (para renderização completa):
    ```dockerfile
    FROM python:3.11-slim
   
    RUN apt-get update && apt-get install -y \
        chromium \
        chromium-driver \
        xvfb \
        && rm -rf /var/lib/apt/lists/*
   
    ENV DISPLAY=:99
   
    CMD Xvfb :99 -screen 0 1920x1080x24 & python your_script.py
    ```

2.  **Use proxy residencial** mesmo em CI/CD:
    ```python
    options = ChromiumOptions()
    options.add_argument('--proxy-server=http://user:pass@residential-proxy.com:8080')
    ```

## Melhores Práticas

1.  **Use proxies residenciais**: A reputação do IP é o fator mais crítico
2.  **Configure opções de furtividade**: Remova indicadores de automação
3.  **Adicione padrões comportamentais**: Role, espere, mova o mouse antes de clicar
4.  **Ajuste o tempo**: Dê tempo ao captcha para carregar antes de tentar clicar
5.  **Use seletores personalizados**: Quando o seletor padrão não funcionar
6.  **Lide com falhas graciosamente**: Tenha lógica de fallback para quando o captcha não puder ser passado
7.  **Teste seu ambiente**: Verifique a reputação do IP e o fingerprint do navegador antes da automação

## Diretrizes Éticas

!!! danger "Termos de Serviço e Conformidade Legal"
    Interagir com captchas pode violar os Termos de Serviço de um site, mesmo que tecnicamente possível. **Sempre verifique e respeite os ToS** antes de automatizar qualquer site.
    
    Esta funcionalidade é fornecida **apenas para fins legítimos de automação**:
    
    **Casos de uso apropriados:**
    - Teste automatizado de suas próprias aplicações
    - Serviços de monitoramento que você tem permissão para monitorar
    - Pesquisa e análise de segurança com autorização adequada
    
    **Casos de uso inapropriados:**
    - Raspagem de conteúdo que você não tem permissão para acessar
    - Contornar paywalls ou sistemas de assinatura
    - Ataques de negação de serviço (Denial-of-Service) ou raspagem agressiva
    - Qualquer atividade que viole os Termos de Serviço

## Veja Também

- **[Opções do Navegador](../configuration/browser-options.md)** - Configuração de furtividade
- **[Preferências do Navegador](../configuration/browser-preferences.md)** - Fingerprinting avançado
- **[Configuração de Proxy](../configuration/proxy.md)** - Configurando proxies
- **[Fingerprinting Comportamental](../../deep-dive/fingerprinting/behavioral-fingerprinting.md)** - Entendendo a detecção comportamental
- **[Interações Semelhantes a Humanas](../automation/human-interactions.md)** - Padrões de comportamento realistas

---

**Lembre-se**: O Pydoll fornece o mecanismo para clicar em captchas, mas seu ambiente (IP, fingerprint, comportamento) determina o sucesso. Esta não é uma solução mágica, é uma ferramenta que funciona quando usada no ambiente certo com a configuração adequada.