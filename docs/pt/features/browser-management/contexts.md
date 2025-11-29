# Contextos de Navegador (Browser Contexts)

Contextos de Navegador são a solução do Pydoll para criar ambientes de navegação completely isolados dentro de um único processo de navegador. Pense neles como "janelas anônimas" separadas, mas com controle programático total. Cada contexto mantém seus próprios cookies, armazenamento, cache e estado de autenticação.

## Guia Rápido

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def basic_context_example():
    async with Chrome() as browser:
        # Inicia o navegador com a aba inicial no contexto padrão
        initial_tab = await browser.start()
        await initial_tab.go_to('https://example.com')
        
        # Cria um contexto isolado
        context_id = await browser.create_browser_context()
        
        # Nova aba no contexto isolado
        isolated_tab = await browser.new_tab('https://example.com', browser_context_id=context_id)
        
        # Ambas as abas estão completamente isoladas - cookies, armazenamento, etc. diferentes
        await initial_tab.execute_script("localStorage.setItem('user', 'Alice')")
        await isolated_tab.execute_script("localStorage.setItem('user', 'Bob')")
        
        # Verifica o isolamento
        user_default = await initial_tab.execute_script("return localStorage.getItem('user')")
        user_isolated = await isolated_tab.execute_script("return localStorage.getItem('user')")
        
        print(f"Contexto padrão: {user_default}")  # Alice
        print(f"Contexto isolado: {user_isolated}")  # Bob

asyncio.run(basic_context_example())
```

## O que são Contextos de Navegador?

Um contexto de navegador é um ambiente de navegação isolado dentro de um único processo de navegador. Cada contexto mantém separadamente:

| Componente | Descrição | Nível de Isolamento |
|---|---|---|
| **Cookies** | Cookies HTTP e dados de sessão | ✓ Totalmente isolado |
| **Local Storage** | `localStorage` e `sessionStorage` | ✓ Totalmente isolado |
| **IndexedDB** | Banco de dados do lado do cliente | ✓ Totalmente isolado |
| **Cache** | Cache HTTP e recursos | ✓ Totalmente isolado |
| **Permissões** | Geolocalização, notificações, câmera, etc. | ✓ Totalmente isolado |
| **Autenticação** | Sessões de login e tokens de autenticação | ✓ Totalmente isolado |
| **Service Workers** | Scripts em segundo plano | ✓ Totalmente isolado |

```mermaid
graph LR
    Browser[Processo do Navegador] --> Default[Contexto Padrao]
    Browser --> Context1[Contexto 1]
    Browser --> Context2[Contexto 2]
    
    Default --> T1[Aba A]
    Default --> T2[Aba B]
    Context1 --> T3[Aba C]
    Context2 --> T4[Aba D]
```

## Por que Usar Contextos de Navegador?

### 1. Teste de Múltiplas Contas

Teste diferentes contas de usuário simultaneamente sem interferência:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def perform_login(tab, email, password):
    """
    Função auxiliar para navegar até a página de login
    e enviar as credenciais da conta.
    """
    print(f"Tentando login com: {email}...")
    await tab.go_to('https://app.example.com/login')

    # Encontrar elementos
    email_field = await tab.find(id='email')
    password_field = await tab.find(id='password')
    login_btn = await tab.find(id='login-btn')

    # Preencher credenciais e clicar
    await email_field.type_text(email)
    await password_field.type_text(password)
    await login_btn.click()

    # Esperar o login processar
    await asyncio.sleep(2)
    print(f"Login bem-sucedido para {email}.")


async def multi_account_test():
    """
    Script principal para testar logins simultâneos
    usando contextos de navegador isolados.
    """
    accounts = [
        {"email": "user1@example.com", "password": "pass1"},
        {"email": "user2@example.com", "password": "pass2"},
        {"email": "admin@example.com", "password": "admin_pass"}
    ]

    # Esta lista armazenará informações de cada sessão de usuário ativa.
    user_sessions = []

    async with Chrome() as browser:
        first_account = accounts[0]
        initial_tab = await browser.start()
        await perform_login(initial_tab, first_account['email'], first_account['password'])
        user_sessions.append({
            "email": first_account['email'],
            "tab": initial_tab,
            "context_id": None  # 'None' representa o contexto padrão do navegador
        })

        # Iterar sobre o restante das contas
        for account in accounts[1:]:
            context_id = await browser.create_browser_context()
            new_tab = await browser.new_tab(browser_context_id=context_id)
            await perform_login(new_tab, account['email'], account['password'])

            # Adicionar esta nova informação de sessão à lista
            user_sessions.append({
                "email": account['email'],
                "tab": new_tab,
                "context_id": context_id
            })

        print("\n--- Verificando todas as sessões activas ---")
        for session in user_sessions:
            tab = session["tab"]
            email = session["email"]
            await tab.go_to('https://app.example.com/dashboard')
            username = await tab.find(class_name='username')
            username_text = await username.text
            print(f"[Conta: {email}] -> Logado como: {username_text}")
            await asyncio.sleep(0.5)

        print("\n--- Limpando contextos ---")
        for session in user_sessions:
            # Fechar apenas os contextos que criamos (diferentes de None)
            if session["context_id"] is not None:
                print(f"Fechando contexto para: {session['email']}")
                await session["tab"].close()
                await browser.delete_browser_context(session["context_id"])
        
        # O contexto padrão (None) é fechado automaticamente
        # pelo 'async with Chrome() as browser'

asyncio.run(multi_account_test())
```

### 2. Teste de Geo-Localização com Proxies Específicos do Contexto

Cada contexto pode ter sua própria configuração de proxy:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def geo_location_testing():
    async with Chrome() as browser:
        # Inicia o navegador e usa a aba inicial para o primeiro teste (contexto padrão, sem proxy)
        initial_tab = await browser.start()
        await initial_tab.go_to('https://api.ipify.org')
        await asyncio.sleep(2)
        default_ip = await initial_tab.execute_script('return document.body.textContent')
        print(f"IP Padrão (sem proxy): {default_ip}")
        
        # Contexto dos EUA com proxy dos EUA
        us_context = await browser.create_browser_context(
            proxy_server='http://us-proxy.example.com:8080'
        )
        us_tab = await browser.new_tab('https://api.ipify.org', browser_context_id=us_context)
        await asyncio.sleep(2)
        us_ip = await us_tab.execute_script('return document.body.textContent')
        print(f"IP dos EUA: {us_ip}")
        
        # Contexto da UE com proxy da UE
        eu_context = await browser.create_browser_context(
            proxy_server='http://eu-proxy.example.com:8080'
        )
        eu_tab = await browser.new_tab('https://api.ipify.org', browser_context_id=eu_context)
        await asyncio.sleep(2)
        eu_ip = await eu_tab.execute_script('return document.body.textContent')
        print(f"IP da UE: {eu_ip}")
        
        # Limpeza (pular aba inicial)
        await us_tab.close()
        await eu_tab.close()
        await browser.delete_browser_context(us_context)
        await browser.delete_browser_context(eu_context)

asyncio.run(geo_location_testing())
```

!!! tip "Autenticação de Proxy"
    O Pydoll lida automaticamente com a autenticação de proxy para contextos. Apenas inclua as credenciais na URL:
    ```python
    context_id = await browser.create_browser_context(
        proxy_server='http://username:password@proxy.example.com:8080'
    )
    ```
    As credenciais são higienizadas dos comandos CDP e usadas apenas quando o navegador solicita autenticação.

### 3. Teste A/B

Compare diferentes experiências de usuário em paralelo:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def ab_testing():
    async with Chrome() as browser:
        # Inicia o navegador com a aba inicial (Grupo de Controle no contexto padrão)
        initial_tab = await browser.start()
        await initial_tab.go_to('https://example.com')
        await initial_tab.execute_script("localStorage.setItem('experiment', 'control')")
        
        # Grupo de Tratamento em contexto isolado
        context_b = await browser.create_browser_context()
        tab_b = await browser.new_tab('https://example.com', browser_context_id=context_b)
        await tab_b.execute_script("localStorage.setItem('experiment', 'treatment')")
        
        # Navega ambos para a página da funcionalidade
        await initial_tab.go_to('https://example.com/feature')
        await tab_b.go_to('https://example.com/feature')
        
        # Compara os resultados
        result_a = await initial_tab.find(class_name='experiment-result')
        result_b = await tab_b.find(class_name='experiment-result')
        
        print(f"Resultado do grupo de controle: {await result_a.text}")
        print(f"Resultado do grupo de tratamento: {await result_b.text}")
        
        # Limpeza
        await tab_b.close()
        await browser.delete_browser_context(context_b)

asyncio.run(ab_testing())
```

### 4. Raspagem Web Paralela

Raspe múltiplos sites com diferentes configurações:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def parallel_scraping():
    websites = [
        {'url': 'https://news.ycombinator.com', 'selector': '.storylink'},
        {'url': 'https://reddit.com/r/python', 'selector': '.title'},
        {'url': 'https://github.com/trending', 'selector': '.h3'},
    ]
    
    async with Chrome() as browser:
        # Inicia o navegador e obtém a aba inicial
        initial_tab = await browser.start()
        
        # Cria contextos para os sites restantes (o primeiro usa o contexto padrão)
        contexts = [None] + [await browser.create_browser_context() for _ in websites[1:]]
        
        # Cria abas (reutilizando a aba inicial para o primeiro site)
        tabs = [initial_tab] + [
            await browser.new_tab(browser_context_id=ctx) for ctx in contexts[1:]
        ]
        
        async def scrape_site(tab, site, context_id):
            """Raspa um único site dentro da aba e contexto fornecidos."""
            try:
                await tab.go_to(site['url'])
                await asyncio.sleep(3)
                
                # Extrai títulos usando seletor CSS
                elements = await tab.query(site['selector'], find_all=True)
                titles = [await elem.text for elem in elements[:5]]
                
                return {'url': site['url'], 'titles': titles}
            finally:
                # Limpa o contexto (pula o contexto padrão da aba inicial)
                if context_id is not None:
                    await tab.close()
                    await browser.delete_browser_context(context_id)
        
        # Raspa todos os sites concorrentemente
        results = await asyncio.gather(*[
            scrape_site(tab, site, ctx) for tab, site, ctx in zip(tabs, websites, contexts)
        ])
        
        # Exibe os resultados
        for result in results:
            print(f"\n{result['url']}:")
            for i, title in enumerate(result['titles'], 1):
                print(f"  {i}. {title}")

asyncio.run(parallel_scraping())
```

## Entendendo o Desempenho do Contexto

### Contextos São Leves

!!! info "Características de Desempenho"
    Criar um contexto de navegador é **significativamente mais rápido e leve** do que lançar um novo processo de navegador:
    
    - **Criação de contexto**: ~50-100ms, sobrecarga mínima de memória
    - **Novo processo de navegador**: ~2-5 segundos, 50-150 MB de memória base
    
    Para 10 ambientes isolados:

    - **10 contextos em 1 navegador**: ~500ms de inicialização, ~500 MB no total
    - **10 navegadores separados**: ~30 segundos de inicialização, ~1-1.5 GB no total

```python
import asyncio
import time
from pydoll.browser.chromium import Chrome

async def benchmark_contexts_vs_browsers():
    # Benchmark de contextos
    start = time.time()
    async with Chrome() as browser:
        # Inicia o navegador (aba inicial não usada neste exemplo)
        await browser.start()
        
        contexts = []
        for i in range(10):
            context_id = await browser.create_browser_context()
            contexts.append(context_id)
        
        print(f"10 contextos criados em: {time.time() - start:.2f}s")
        
        # Limpeza
        for context_id in contexts:
            await browser.delete_browser_context(context_id)

asyncio.run(benchmark_contexts_vs_browsers())
```

### Headless vs Headed: O Comportamento da Janela

!!! warning "Importante: Janelas de Contexto no Modo Headed"
    Ao rodar em **modo headed** (com UI do navegador visível), há um comportamento importante a entender:
    
    **A primeira aba criada em um novo contexto abrirá uma nova janela do sistema operacional.**
    
    - Isso acontece porque o contexto precisa de uma "janela hospedeira" para renderizar sua primeira página
    - Abas subsequentes nesse contexto podem abrir como abas dentro dessa janela
    - Esta é uma limitação do CDP/Chromium, não uma escolha de design do Pydoll
    
    **No modo headless**, isso não importa—nenhuma janela é criada, tudo roda em segundo plano.

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def demonstrate_window_behavior():
    # Modo headed - verá janelas
    options_headed = ChromiumOptions()
    options_headed.headless = False
    
    async with Chrome(options=options_headed) as browser:
        # Inicia o navegador com a aba inicial (abre a primeira janela no contexto padrão)
        initial_tab = await browser.start()
        await initial_tab.go_to('https://example.com')
        
        # Cria novo contexto - a primeira aba abrirá uma NOVA janela
        context = await browser.create_browser_context()
        tab2 = await browser.new_tab('https://github.com', browser_context_id=context)
        
        # Segunda aba no mesmo contexto - abre como aba na janela existente
        tab3 = await browser.new_tab('https://google.com', browser_context_id=context)
        
        await asyncio.sleep(10)  # Observe as janelas
        
        await tab2.close()
        await tab3.close()
        await browser.delete_browser_context(context)

# Modo headless - sem janelas, contextos são invisíveis mas ainda isolados
async def headless_contexts():
    options = ChromiumOptions()
    options.headless = True  # Sem janelas visíveis
    
    async with Chrome(options=options) as browser:
        # Inicia o navegador com a aba inicial no contexto padrão
        initial_tab = await browser.start()
        await initial_tab.go_to('https://example.com/page0')
        
        # Cria mais 4 contextos - nenhuma janela aberta, tudo em segundo plano
        contexts = []
        for i in range(1, 5):
            context_id = await browser.create_browser_context()
            tab = await browser.new_tab(f'https://example.com/page{i}', browser_context_id=context_id)
            contexts.append((context_id, tab))
        
        print(f"Criados {len(contexts) + 1} contextos isolados (1 padrão + {len(contexts)} personalizados, invisíveis)")
        
        # Limpeza
        for context_id, tab in contexts:
            await tab.close()
            await browser.delete_browser_context(context_id)

asyncio.run(headless_contexts())
```

!!! tip "Melhor Prática: Use Headless para Contextos"
    Para máxima eficiência com múltiplos contextos:
    
    - **Desenvolvimento/Depuração**: Use o modo headed para ver o que está acontecendo
    - **Produção/CI/CD**: Use o modo headless para execução mais rápida e leve
    - **Múltiplos contextos**: Prefira fortemente o headless para evitar a complexidade do gerenciamento de janelas

## Gerenciamento de Contexto

### Criando Contextos

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def create_context_example():
    async with Chrome() as browser:
        await browser.start()
        
        # Criar contexto básico
        context_id = await browser.create_browser_context()
        print(f"Contexto criado: {context_id}")
        
        # Criar contexto com proxy
        proxied_context = await browser.create_browser_context(
            proxy_server='http://proxy.example.com:8080',
            proxy_bypass_list='localhost,127.0.0.1'
        )
        print(f"Contexto com proxy criado: {proxied_context}")
        
        # Criar contexto com proxy autenticado
        auth_context = await browser.create_browser_context(
            proxy_server='http://user:pass@proxy.example.com:8080'
        )
        print(f"Contexto com autenticação criado: {auth_context}")

asyncio.run(create_context_example())
```

### Listando Contextos

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def list_contexts():
    async with Chrome() as browser:
        await browser.start()
        
        # Obter todos os contextos (inclui o padrão)
        contexts = await browser.get_browser_contexts()
        print(f"Contextos iniciais: {len(contexts)}")  # Geralmente 1 (padrão)
        
        # Criar contextos adicionais
        context1 = await browser.create_browser_context()
        context2 = await browser.create_browser_context()
        
        # Listar novamente
        contexts = await browser.get_browser_contexts()
        print(f"Após criar 2 novos contextos: {len(contexts)}")  # 3 no total
        
        for i, context_id in enumerate(contexts):
            print(f"  Contexto {i+1}: {context_id}")
        
        # Limpeza
        await browser.delete_browser_context(context1)
        await browser.delete_browser_context(context2)

asyncio.run(list_contexts())
```

### Deletando Contextos

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def delete_context_example():
    async with Chrome() as browser:
        await browser.start()
        
        # Criar contexto com abas
        context_id = await browser.create_browser_context()
        tab1 = await browser.new_tab('https://example.com', browser_context_id=context_id)
        tab2 = await browser.new_tab('https://github.com', browser_context_id=context_id)
        
        print(f"Contexto {context_id} criado com 2 abas")
        
        # Deletar o contexto fecha todas as suas abas automaticamente
        await browser.delete_browser_context(context_id)
        print("Contexto deletado (todas as abas fechadas automaticamente)")

asyncio.run(delete_context_example())
```

!!! warning "Deletar Contextos Fecha Todas as Abas"
    Quando você deleta um contexto de navegador, **todas as abas pertencentes a esse contexto são fechadas automaticamente**. Esta é uma maneira eficiente de limpar múltiplas abas de uma vez, mas certifique-se de ter salvo quaisquer dados importantes primeiro.

## Contexto Padrão

Todo navegador inicia com um **contexto padrão** que contém a aba inicial:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def default_context_example():
    async with Chrome() as browser:
        # Aba inicial está no contexto padrão
        initial_tab = await browser.start()
        
        # Criar aba sem especificar contexto - usa o padrão
        default_tab = await browser.new_tab('https://example.com')
        
        # Criar contexto personalizado
        custom_context = await browser.create_browser_context()
        custom_tab = await browser.new_tab('https://github.com', browser_context_id=custom_context)
        
        # Contextos padrão e personalizado são isolados
        await default_tab.execute_script("localStorage.setItem('type', 'default')")
        await custom_tab.execute_script("localStorage.setItem('type', 'custom')")
        
        # Verificar isolamento
        default_type = await default_tab.execute_script("return localStorage.getItem('type')")
        custom_type = await custom_tab.execute_script("return localStorage.getItem('type')")
        
        print(f"Contexto padrão: {default_type}")  # 'default'
        print(f"Contexto personalizado: {custom_type}")    # 'custom'
        
        # Limpar contexto personalizado
        await browser.delete_browser_context(custom_context)

asyncio.run(default_context_example())
```

!!! info "Você Não Pode Deletar o Contexto Padrão"
    O contexto padrão do navegador é permanente e não pode ser deletado. Ele existe por toda a sessão do navegador. Apenas contextos personalizados criados com `create_browser_context()` podem ser deletados.

## Padrões Avançados

### Pool de Contextos para Isolamento Reutilizável

```python
import asyncio
from pydoll.browser.chromium import Chrome

class ContextPool:
    def __init__(self, browser, size=5):
        self.browser = browser
        self.size = size
        self.contexts = []
        self.in_use = set()
    
    async def initialize(self):
        """Criar pool de contextos"""
        for _ in range(self.size):
            context_id = await self.browser.create_browser_context()
            self.contexts.append(context_id)
        print(f"Pool de contextos inicializado com {self.size} contextos")
    
    async def acquire(self):
        """Obter contexto disponível do pool"""
        for context_id in self.contexts:
            if context_id not in self.in_use:
                self.in_use.add(context_id)
                return context_id
        raise Exception("Nenhum contexto disponível no pool")
    
    def release(self, context_id):
        """Devolver contexto ao pool"""
        self.in_use.discard(context_id)
    
    async def cleanup(self):
        """Deletar todos os contextos no pool"""
        for context_id in self.contexts:
            await self.browser.delete_browser_context(context_id)

async def use_context_pool():
    async with Chrome() as browser:
        await browser.start()
        
        # Criar pool
        pool = ContextPool(browser, size=3)
        await pool.initialize()
        
        # Usar contextos do pool
        async def scrape_with_pool(url):
            context_id = await pool.acquire()
            try:
                tab = await browser.new_tab(url, browser_context_id=context_id)
                await asyncio.sleep(2)
                title = await tab.execute_script('return document.title')
                await tab.close()
                return title
            finally:
                pool.release(context_id)
        
        # Raspar múltiplas URLs usando o pool
        urls = [f'https://example.com/page{i}' for i in range(10)]
        results = await asyncio.gather(*[scrape_with_pool(url) for url in urls])
        
        for i, title in enumerate(results):
            print(f"{urls[i]}: {title}")
        
        # Limpeza
        await pool.cleanup()

asyncio.run(use_context_pool())
```

### Gerenciador de Configuração por Contexto

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def context_config_manager():
    async with Chrome() as browser:
        await browser.start()
        
        # Definir configurações para diferentes cenários
        configs = {
            'us_user': {
                'proxy': 'http://us-proxy.example.com:8080',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
            },
            'eu_user': {
                'proxy': 'http://eu-proxy.example.com:8080',
                'user_agent': 'Mozilla/5.0 (X11; Linux x86_64)'
            },
            'mobile_user': {
                'proxy': None,
                'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'
            }
        }
        
        contexts = {}
        
        # Criar contexto para cada configuração
        for name, config in configs.items():
            if config['proxy']:
                context_id = await browser.create_browser_context(
                    proxy_server=config['proxy']
                )
            else:
                context_id = await browser.create_browser_context()
            
            # Criar aba e definir user agent
            tab = await browser.new_tab(browser_context_id=context_id)
            # Nota: User agent seria definido via CDP ou opções, simplificado aqui
            
            contexts[name] = {'context_id': context_id, 'tab': tab}
        
        # Usar diferentes contextos para diferentes cenários
        for name, data in contexts.items():
            tab = data['tab']
            await tab.go_to('https://httpbin.org/headers')
            await asyncio.sleep(2)
            print(f"\nConfiguração {name} ativa")
        
        # Limpeza
        for data in contexts.values():
            await data['tab'].close()
            await browser.delete_browser_context(data['context_id'])

asyncio.run(context_config_manager())
```

## Melhores Práticas

1.  **Use o modo headless para múltiplos contextos** para evitar a complexidade do gerenciamento de janelas
2.  **Sempre delete os contextos quando terminar** para evitar vazamentos de memória
3.  **Agrupe operações relacionadas no mesmo contexto** para melhor organização
4.  **Prefira contextos a múltiplos processos de navegador** para melhor desempenho
5.  **Use pools de contextos** para cenários que exigem muitos ambientes isolados de curta duração
6.  **Feche as abas antes de deletar os contextos** para uma limpeza mais organizada (embora não seja estritamente necessário)

## Veja Também

- **[Gerenciamento de Múltiplas Abas](tabs.md)** - Gerenciando múltiplas abas dentro de contextos
- **[Análise Profunda: Domínio do Navegador](../../deep-dive/browser-domain.md)** - Detalhes arquitetônicos sobre contextos
- **[Rede: Requisições HTTP](../network/http-requests.md)** - Requisições no contexto do navegador herdam o estado do contexto
- **[Conceitos Principais](../core-concepts.md)** - Entendendo a arquitetura do Pydoll

Contextos de Navegador são uma das funcionalidades mais poderosas do Pydoll para criar fluxos de trabalho de automação sofisticados. Ao entender como eles funcionam—especialmente o comportamento da janela no modo headed e sua natureza leve—você pode construir automação eficiente e escalável que lida com cenários complexos de múltiplos ambientes com facilidade.