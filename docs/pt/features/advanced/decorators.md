# Decorator Retry

Web scraping é inerentemente imprevisível. Redes falham, páginas carregam lentamente, elementos aparecem e desaparecem, limites de taxa entram em ação e CAPTCHAs surgem inesperadamente. O decorator `@retry` fornece uma solução robusta e testada em produção para lidar com essas falhas inevitáveis de forma elegante.

## Por Que Usar o Decorator Retry?

No scraping em produção, falhas não são exceções—são a norma. Em vez de deixar todo o seu trabalho de scraping travar por causa de uma falha temporária de rede ou um elemento ausente, o decorator retry permite que você:

- **Recupere-se automaticamente** de falhas transitórias
- **Implemente estratégias sofisticadas de retry** com backoff exponencial
- **Execute lógica de recuperação** antes de tentar novamente (atualizar página, trocar proxy, reiniciar navegador)
- **Mantenha sua lógica de negócio limpa** sem poluí-la com código de tratamento de erros

## Início Rápido

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.decorators import retry
from pydoll.exceptions import WaitElementTimeout, NetworkError

@retry(max_retries=3, exceptions=[WaitElementTimeout, NetworkError])
async def scrape_product_page(url: str):
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to(url)
        
        # Isso pode falhar devido a problemas de rede ou carregamento lento
        product_title = await tab.find(class_name='product-title', timeout=5)
        return await product_title.text

asyncio.run(scrape_product_page('https://example.com/product/123'))
```

Se `scrape_product_page` falhar com `WaitElementTimeout` ou `NetworkError`, ela automaticamente tentará novamente até 3 vezes antes de desistir.

## Boa Prática: Sempre Especifique Exceções

!!! warning "Boa Prática Crítica"
    **SEMPRE** especifique quais exceções devem acionar um retry. Usar o padrão `exceptions=Exception` vai capturar **tudo**, incluindo bugs no seu código que deveriam falhar imediatamente.

**Ruim (captura tudo, incluindo bugs):**

```python
@retry(max_retries=3)  # NÃO FAÇA ISSO
async def scrape_data():
    data = response['items'][0]  # Se 'items' não existir, retries não vão ajudar!
    return data
```

**Bom (só tenta novamente em falhas esperadas):**

```python
from pydoll.exceptions import ElementNotFound, WaitElementTimeout, NetworkError

@retry(
    max_retries=3,
    exceptions=[ElementNotFound, WaitElementTimeout, NetworkError]
)
async def scrape_data():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        return await tab.find(id='data-container', timeout=10)
```

Ao especificar exceções, você garante que:

- **Erros de lógica falham rapidamente** (typos, seletores errados, bugs de código)
- **Apenas erros recuperáveis são retentados** (problemas de rede, timeouts, elementos ausentes)
- **Depuração é mais fácil** (você sabe exatamente o que deu errado)

## Parâmetros

### max_retries

Número máximo de tentativas de retry antes de desistir.

```python
from pydoll.exceptions import WaitElementTimeout

@retry(max_retries=5, exceptions=[WaitElementTimeout])
async def fetch_data():
    # Tentará até 5 vezes no total
    pass
```

### exceptions

Tipos de exceção que devem acionar um retry. Pode ser uma única exceção ou uma lista.

```python
from pydoll.exceptions import (
    ElementNotFound,
    WaitElementTimeout,
    NetworkError,
    ElementNotInteractable
)

# Exceção única
@retry(exceptions=[WaitElementTimeout])
async def example1():
    pass

# Múltiplas exceções
@retry(exceptions=[WaitElementTimeout, NetworkError, ElementNotFound, ElementNotInteractable])
async def example2():
    pass
```

!!! tip "Exceções Comuns de Scraping"
    Para web scraping com Pydoll, você normalmente vai querer retry em:

    - `WaitElementTimeout` - Timeout esperando elemento aparecer
    - `ElementNotFound` - Elemento não existe no DOM
    - `ElementNotVisible` - Elemento existe mas não está visível
    - `ElementNotInteractable` - Elemento não pode receber interação
    - `NetworkError` - Problemas de conectividade de rede
    - `ConnectionFailed` - Falha ao conectar ao navegador
    - `PageLoadTimeout` - Timeout no carregamento de página
    - `ClickIntercepted` - Click interceptado por outro elemento

### delay

Tempo de espera entre tentativas de retry (em segundos).

```python
from pydoll.exceptions import WaitElementTimeout

@retry(max_retries=3, exceptions=[WaitElementTimeout], delay=2.0)
async def scrape_with_delay():
    # Espera 2 segundos entre cada retry
    pass
```

### exponential_backoff

Quando `True`, aumenta o delay exponencialmente com cada tentativa de retry.

```python
from pydoll.exceptions import NetworkError

@retry(
    max_retries=5,
    exceptions=[NetworkError],
    delay=1.0,
    exponential_backoff=True
)
async def scrape_with_backoff():
    # Tentativa 1: falha → espera 1 segundo
    # Tentativa 2: falha → espera 2 segundos
    # Tentativa 3: falha → espera 4 segundos
    # Tentativa 4: falha → espera 8 segundos
    # Tentativa 5: falha → lança exceção
    pass
```

**O que é Exponential Backoff?**

Exponential backoff é uma estratégia de retry onde o tempo de espera entre tentativas aumenta exponencialmente. Em vez de bombardear um servidor com requisições a cada segundo, você dá progressivamente mais tempo para ele se recuperar:

- **Tentativa 1**: Espera `delay` segundos (ex: 1s)
- **Tentativa 2**: Espera `delay * 2` segundos (ex: 2s)
- **Tentativa 3**: Espera `delay * 4` segundos (ex: 4s)
- **Tentativa 4**: Espera `delay * 8` segundos (ex: 8s)

Isso é especialmente útil quando:

- Lidando com **limites de taxa** (dê tempo ao servidor para resetar)
- Lidando com **sobrecarga temporária do servidor** (não piore a situação)
- Esperando **conteúdo dinâmico de carregamento lento**
- Evitando **detecção como bot** (padrões de retry com aparência natural)

### on_retry

Uma função callback executada após cada tentativa falhada, antes do próximo retry. Deve ser uma **função async**.

```python
from pydoll.exceptions import WaitElementTimeout

@retry(
    max_retries=3,
    exceptions=[WaitElementTimeout],
    on_retry=my_recovery_function
)
async def scrape_data():
    pass
```

O callback pode ser:

- **Uma função async standalone**
- **Um método de classe** (recebe `self` automaticamente)

## O Callback on_retry: Seu Mecanismo de Recuperação

O callback `on_retry` é onde a verdadeira mágica acontece. Esta é sua oportunidade de **restaurar o estado da aplicação** antes da próxima tentativa de retry.

### Função Standalone

```python
import asyncio
from pydoll.decorators import retry
from pydoll.exceptions import WaitElementTimeout

async def log_retry():
    print("Tentativa de retry falhou, esperando antes da próxima tentativa...")
    await asyncio.sleep(1)

@retry(max_retries=3, exceptions=[WaitElementTimeout], on_retry=log_retry)
async def scrape_page():
    # Sua lógica de scraping
    pass
```

### Método de Classe

Ao usar o decorator dentro de uma classe, o callback pode ser um método de classe. Ele receberá automaticamente `self` como primeiro argumento.

```python
import asyncio
from pydoll.decorators import retry
from pydoll.exceptions import WaitElementTimeout

class DataCollector:
    def __init__(self):
        self.retry_count = 0
    
    # IMPORTANTE: Defina o callback ANTES do método decorado
    async def log_retry(self):
        self.retry_count += 1
        print(f"Tentativa {self.retry_count} falhou, tentando novamente...")
        await asyncio.sleep(1)
    
    @retry(
        max_retries=3,
        exceptions=[WaitElementTimeout],
        on_retry=log_retry  # Sem prefixo 'self.' necessário
    )
    async def fetch_data(self):
        # Sua lógica de scraping aqui
        pass
```

!!! warning "Ordem de Definição de Métodos Importa"
    Ao usar `on_retry` com métodos de classe, **você deve definir o método callback ANTES do método decorado** na definição da sua classe. Python precisa saber sobre o callback quando o decorator é aplicado.

    **Errado (vai falhar):**

    ```python
    class Scraper:
        @retry(on_retry=handle_retry)  # handle_retry ainda não existe!
        async def scrape(self):
            pass
        
        async def handle_retry(self):  # Definido muito tarde
            pass
    ```

    **Correto:**

    ```python
    class Scraper:
        async def handle_retry(self):  # Definido primeiro
            pass
        
        @retry(on_retry=handle_retry)  # Agora existe
        async def scrape(self):
            pass
    ```

## Casos de Uso do Mundo Real

### 1. Atualização de Página e Recuperação de Estado

**Este é o uso mais poderoso do `on_retry`**: recuperar de falhas atualizando a página e restaurando o estado da sua aplicação. Este exemplo demonstra por que o decorator retry é tão valioso para scraping em produção.

```python
from pydoll.browser.chromium import Chrome
from pydoll.decorators import retry
from pydoll.exceptions import ElementNotFound, WaitElementTimeout
from pydoll.constants import Key
import asyncio

class DataScraper:
    def __init__(self):
        self.browser = None
        self.tab = None
        self.current_page = 1
    
    async def recover_from_failure(self):
        """Atualizar página e restaurar estado antes do retry"""
        print(f"Recuperando... atualizando página {self.current_page}")
        
        if self.tab:
            # Atualiza a página para recuperar de elementos obsoletos ou estado ruim
            await self.tab.refresh()
            await asyncio.sleep(2)  # Esperar a página carregar
            
            # Restaurar estado: navegar de volta para a página correta
            if self.current_page > 1:
                page_input = await self.tab.find(id='page-number')
                await page_input.insert_text(str(self.current_page))
                await self.tab.keyboard.press(Key.ENTER)
                await asyncio.sleep(1)
    
    @retry(
        max_retries=3,
        exceptions=[ElementNotFound, WaitElementTimeout],
        on_retry=recover_from_failure,
        delay=1.0
    )
    async def scrape_page_data(self):
        """Fazer scraping dos dados da página atual"""
        if not self.browser:
            self.browser = Chrome()
            self.tab = await self.browser.start()
            await self.tab.go_to('https://example.com/data')
        
        # Navegar para página específica
        page_input = await self.tab.find(id='page-number')
        await page_input.insert_text(str(self.current_page))
        await self.tab.keyboard.press(Key.ENTER)
        await asyncio.sleep(1)
        
        # Fazer scraping dos dados (pode falhar se elementos ficarem obsoletos)
        items = await self.tab.find(class_name='data-item', find_all=True)
        return [await item.text for item in items]
    
    async def scrape_multiple_pages(self, start_page: int, end_page: int):
        """Fazer scraping de múltiplas páginas com retry automático em falhas"""
        results = []
        for page_num in range(start_page, end_page + 1):
            self.current_page = page_num
            data = await self.scrape_page_data()
            results.extend(data)
        return results

# Uso
async def main():
    scraper = DataScraper()
    try:
        # Fazer scraping das páginas 1-10 com recuperação automática em falhas
        all_data = await scraper.scrape_multiple_pages(1, 10)
        print(f"Coletados {len(all_data)} itens")
    finally:
        if scraper.browser:
            await scraper.browser.stop()
```

**O que torna isso poderoso:**

- `recover_from_failure()` realmente **restaura o estado** atualizando e navegando de volta
- O método `scrape_page_data()` fica limpo, focado apenas na lógica de scraping
- Se elementos ficarem obsoletos ou desaparecerem, o mecanismo de retry lida com a recuperação automaticamente
- O navegador persiste entre as tentativas via `self.browser` e `self.tab`

### 2. Recuperação de Modal de Diálogo

Às vezes um modal ou overlay aparece inesperadamente e bloqueia sua automação. Feche-o e tente novamente.

```python
from pydoll.browser.chromium import Chrome
from pydoll.decorators import retry
from pydoll.exceptions import ElementNotFound

class ModalAwareScraper:
    def __init__(self):
        self.tab = None
    
    async def close_modals(self):
        """Fechar quaisquer modals bloqueadores antes do retry"""
        print("Verificando modals bloqueadores...")
        
        # Tentar encontrar e fechar modals comuns
        modal_close = await self.tab.find(
            class_name='modal-close',
            timeout=2,
            raise_exc=False
        )
        if modal_close:
            print("Modal encontrado, fechando...")
            await modal_close.click()
            await asyncio.sleep(0.5)
    
    @retry(
        max_retries=3,
        exceptions=[ElementNotFound],
        on_retry=close_modals,
        delay=0.5
    )
    async def click_button(self, button_id: str):
        button = await self.tab.find(id=button_id)
        await button.click()
```

### 3. Reinício de Navegador e Rotação de Proxy

Para trabalhos pesados de scraping, você pode precisar reiniciar completamente o navegador e trocar proxies após falhas.

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.decorators import retry
from pydoll.exceptions import NetworkError, PageLoadTimeout

class RobustScraper:
    def __init__(self):
        self.browser = None
        self.tab = None
        self.proxy_list = [
            'proxy1.example.com:8080',
            'proxy2.example.com:8080',
            'proxy3.example.com:8080',
        ]
        self.current_proxy_index = 0
    
    async def restart_with_new_proxy(self):
        """Reiniciar navegador com um proxy diferente"""
        print("Reiniciando navegador com novo proxy...")
        
        # Fechar navegador atual
        if self.browser:
            await self.browser.stop()
            await asyncio.sleep(2)
        
        # Rotacionar para o próximo proxy
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
        proxy = self.proxy_list[self.current_proxy_index]
        
        print(f"Usando proxy: {proxy}")
        
        # Iniciar novo navegador com novo proxy
        options = ChromiumOptions()
        options.add_argument(f'--proxy-server={proxy}')
        
        self.browser = Chrome(options=options)
        self.tab = await self.browser.start()
    
    @retry(
        max_retries=3,
        exceptions=[NetworkError, PageLoadTimeout],
        on_retry=restart_with_new_proxy,
        delay=5.0,
        exponential_backoff=True
    )
    async def scrape_protected_site(self, url: str):
        if not self.browser:
            await self.restart_with_new_proxy()
        
        await self.tab.go_to(url)
        await asyncio.sleep(3)
        
        # Sua lógica de scraping aqui
        content = await self.tab.find(id='content')
        return await content.text
```

### 4. Detecção de Ociosidade da Rede com Retry

Esperar que toda atividade de rede seja concluída, com lógica de retry se a página nunca estabilizar.

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.decorators import retry
from pydoll.exceptions import TimeoutException

class NetworkAwareScraper:
    def __init__(self):
        self.tab = None
    
    async def reload_page(self):
        """Recarregar página se a rede nunca estabilizou"""
        print("Página não estabilizou, recarregando...")
        if self.tab:
            await self.tab.refresh()
            await asyncio.sleep(2)
    
    @retry(
        max_retries=2,
        exceptions=[TimeoutException],
        on_retry=reload_page,
        delay=3.0
    )
    async def wait_for_page_ready(self):
        """Esperar todas as requisições de rede completarem"""
        await self.tab.enable_network_events()
        
        # Esperar rede ociosa (sem requisições por 2 segundos)
        idle_time = 0
        max_wait = 10
        
        while idle_time < max_wait:
            # Verificar se há requisições em andamento
            # (Implementação depende do seu rastreamento de eventos)
            await asyncio.sleep(0.5)
            idle_time += 0.5
        
        if idle_time >= max_wait:
            raise TimeoutException("Rede nunca estabilizou")
```

### 5. Detecção e Recuperação de CAPTCHA

Detectar quando um CAPTCHA aparece e tomar a ação apropriada.

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.decorators import retry
from pydoll.exceptions import ElementNotFound

class CaptchaScraper:
    def __init__(self):
        self.tab = None
        self.captcha_count = 0
    
    async def handle_captcha(self):
        """Lidar com CAPTCHA esperando ou mudando estratégia"""
        self.captcha_count += 1
        print(f"CAPTCHA detectado (contagem: {self.captcha_count})")
        
        if self.captcha_count > 2:
            print("Muitos CAPTCHAs, pode precisar mudar estratégia...")
            # Poderia mudar para uma abordagem diferente aqui
        
        # Esperar mais tempo entre tentativas
        await asyncio.sleep(30)
        
        # Atualizar a página
        await self.tab.refresh()
        await asyncio.sleep(5)
    
    @retry(
        max_retries=3,
        exceptions=[ElementNotFound],
        on_retry=handle_captcha,
        delay=10.0,
        exponential_backoff=True
    )
    async def scrape_protected_content(self, url: str):
        if not self.tab:
            browser = Chrome()
            self.tab = await browser.start()
        
        await self.tab.go_to(url)
        
        # Verificar CAPTCHA
        captcha = await self.tab.find(
            class_name='g-recaptcha',
            timeout=2,
            raise_exc=False
        )
        
        if captcha:
            raise ElementNotFound("CAPTCHA detectado")
        
        # Lógica de scraping normal
        content = await self.tab.find(class_name='article-content')
        return await content.text
```

## Padrões Avançados

### Combinando Múltiplas Estratégias de Recuperação

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.decorators import retry
from pydoll.exceptions import ElementNotFound, WaitElementTimeout, NetworkError

class AdvancedScraper:
    def __init__(self):
        self.tab = None
        self.attempt = 0
        self.strategies = [
            self.strategy_refresh,
            self.strategy_clear_cache,
            self.strategy_restart_browser,
        ]
    
    async def strategy_refresh(self):
        """Estratégia 1: Atualização simples"""
        print("Estratégia 1: Atualizando página")
        await self.tab.refresh()
        await asyncio.sleep(2)
    
    async def strategy_clear_cache(self):
        """Estratégia 2: Limpar cache e atualizar"""
        print("Estratégia 2: Limpando cache")
        await self.tab.execute_command('Network.clearBrowserCache')
        await self.tab.refresh()
        await asyncio.sleep(3)
    
    async def strategy_restart_browser(self):
        """Estratégia 3: Reinício completo do navegador"""
        print("Estratégia 3: Reiniciando navegador")
        if self.tab:
            await self.tab._browser.stop()
        
        browser = Chrome()
        self.tab = await browser.start()
    
    async def adaptive_recovery(self):
        """Tentar diferentes estratégias de recuperação baseado no número da tentativa"""
        strategy_index = min(self.attempt, len(self.strategies) - 1)
        strategy = self.strategies[strategy_index]
        
        print(f"Tentativa {self.attempt + 1}: Usando {strategy.__name__}")
        await strategy()
        
        self.attempt += 1
    
    @retry(
        max_retries=3,
        exceptions=[ElementNotFound, WaitElementTimeout, NetworkError],
        on_retry=adaptive_recovery,
        delay=2.0
    )
    async def scrape_with_adaptive_retry(self, url: str):
        await self.tab.go_to(url)
        return await self.tab.find(id='target-content')
```

### Exceção Customizada para Falha Específica

```python
import asyncio
from pydoll.decorators import retry
from pydoll.exceptions import PydollException

class RateLimitError(PydollException):
    """Lançado quando limite de taxa é detectado"""
    message = "Limite de taxa da API excedido"

class APIScraper:
    async def wait_for_rate_limit_reset(self):
        """Esperar mais quando limitado por taxa"""
        print("Limite de taxa detectado, esperando 60 segundos...")
        await asyncio.sleep(60)
    
    @retry(
        max_retries=5,
        exceptions=[RateLimitError],
        on_retry=wait_for_rate_limit_reset,
        delay=10.0,
        exponential_backoff=True
    )
    async def fetch_api_data(self, endpoint: str):
        response = await self.tab.request.get(endpoint)
        
        if response.status == 429:  # Too Many Requests
            raise RateLimitError("Limite de taxa da API excedido")
        
        return response.json()
```

## Resumo de Melhores Práticas

1. **Sempre especifique exceções explicitamente** - Nunca use o padrão `exceptions=Exception`
2. **Use exponential backoff para serviços externos** - Dê tempo aos servidores para se recuperarem
3. **Mantenha contagens de retry razoáveis** - Geralmente 3-5 tentativas são suficientes
4. **Registre tentativas de retry** - Use `on_retry` para registrar o que está acontecendo
5. **Defina callbacks antes dos métodos decorados** - Ordem importa em definições de classe
6. **Faça callbacks async** - O decorator requer callbacks async
7. **Restaure estado nos callbacks** - Use `on_retry` para navegar de volta para onde você estava
8. **Considere o custo dos retries** - Cada retry consome tempo e recursos
9. **Combine com outros tratamentos de erro** - Retries não substituem blocos try/except
10. **Teste sua lógica de retry** - Certifique-se de que callbacks de recuperação realmente funcionam

## Saiba Mais

- **[Tratamento de Exceções](../core-concepts.md#error-handling)** - Entendendo exceções do Pydoll
- **[Eventos de Rede](../network/monitoring.md)** - Rastrear e lidar com falhas de rede
- **[Opções do Navegador](../configuration/browser-options.md)** - Configurar proxies e outras configurações
- **[Sistema de Eventos](event-system.md)** - Construir estratégias de retry reativas

O decorator retry é uma ferramenta poderosa que transforma scripts de scraping frágeis em aplicações prontas para produção. Ao combiná-lo com estratégias de recuperação bem pensadas, você pode construir scrapers que lidam graciosamente com o caos da web real.

