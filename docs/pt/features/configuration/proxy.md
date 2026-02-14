# Configuração de Proxy

Proxies são essenciais para a automação web profissional, permitindo contornar limites de requisições (rate limits), acessar conteúdo geo-restrito e manter o anonimato. O Pydoll oferece suporte nativo a proxies com tratamento automático de autenticação.

!!! info "Documentação Relacionada"
    - **[Opções do Navegador](browser-options.md)** - Argumentos de proxy via linha de comando
    - **[Interceptação de Requisições](../network/interception.md)** - Como a autenticação de proxy funciona internamente
    - **[Automação Furtiva](../automation/human-interactions.md)** - Combine proxies com anti-detecção
    - **[Análise Profunda da Arquitetura de Proxy](../../deep-dive/proxy-architecture.md)** - Fundamentos de rede, protocolos, segurança e construção do seu próprio proxy

## Por que Usar Proxies?

Proxies oferecem capacidades críticas para automação:

| Benefício | Descrição | Caso de Uso |
|---|---|---|
| **Rotação de IP** | Distribui requisições por múltiplos IPs | Evitar limites de requisição, raspar em escala |
| **Acesso Geográfico** | Acessa conteúdo bloqueado por região | Testar recursos geo-direcionados, contornar restrições |
| **Anonimato** | Esconde seu endereço IP real | Automação focada em privacidade, análise de concorrentes |
| **Distribuição de Carga** | Espalha o tráfego por múltiplos endpoints | Raspagem de alto volume, testes de estresse |
| **Evitar Banimento** | Previne banimentos permanentes de IP | Automação de longa duração, raspagem agressiva |

!!! tip "Quando Usar Proxies"
    **Sempre use proxies para:**
    
    - Raspagem web em produção (>100 requisições/hora)
    - Acessar conteúdo geo-restrito
    - Contornar limites de requisição ou bloqueios baseados em IP
    - Testar de diferentes regiões
    - Manter o anonimato
    
    **Você pode pular os proxies para:**
    
    - Desenvolvimento e testes locais
    - Automação interna/corporativa
    - Automação de baixo volume (<50 requisições/dia)
    - Quando raspando sua própria infraestrutura

## Tipos de Proxy

Diferentes protocolos de proxy servem a propósitos distintos:

| Tipo | Porta | Autenticação | Velocidade | Segurança | Caso de Uso |
|---|---|---|---|---|---|
| **HTTP** | 80, 8080 | Opcional | Rápido | Baixa | Raspagem web básica, dados não sensíveis |
| **HTTPS** | 443, 8443 | Opcional | Rápido | Média | Raspagem web segura, tráfego criptografado |
| **SOCKS5** | 1080, 1081 | Opcional | Média | Alta | Suporte total TCP/UDP, casos de uso avançados |

### Proxies HTTP/HTTPS

Proxies web padrão, ideais para a maioria das tarefas de automação:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def http_proxy_example():
    options = ChromiumOptions()
    
    # Proxy HTTP (não criptografado)
    options.add_argument('--proxy-server=http://proxy.example.com:8080')
    
    # Ou proxy HTTPS (criptografado)
    # options.add_argument('--proxy-server=https://proxy.example.com:8443')
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        # Todo o tráfego passa pelo proxy
        await tab.go_to('https://httpbin.org/ip')
        
        # Verificar IP do proxy
        ip = await tab.execute_script('return document.body.textContent')
        print(f"IP Atual: {ip}")

asyncio.run(http_proxy_example())
```

**Prós:**

- Rápido e eficiente
- Amplo suporte em todos os serviços
- Fácil de configurar

**Contras:**

- HTTP: Sem criptografia (tráfego visível para o proxy)
- Pode ser detectado mais facilmente que o SOCKS5

### Proxies SOCKS5

Proxies avançados com suporte total a TCP/UDP:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def socks5_proxy_example():
    options = ChromiumOptions()
    
    # Proxy SOCKS5
    options.add_argument('--proxy-server=socks5://proxy.example.com:1080')
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://httpbin.org/ip')

asyncio.run(socks5_proxy_example())
```

**Prós:**

- Agnóstico a protocolo (funciona com qualquer tráfego TCP/UDP)
- Melhor para casos de uso avançados (WebSockets, WebRTC)
- Mais furtivo (mais difícil de detectar)

**Contras:**

- Ligeiramente mais lento que HTTP/HTTPS
- Menos comum em serviços de proxy gratuitos/baratos

!!! info "SOCKS4 vs SOCKS5"
    **SOCKS5** é recomendado em vez do SOCKS4 porque:
    
    - Suporta autenticação (usuário/senha)
    - Lida com tráfego UDP (para WebRTC, DNS, etc.)
    - Fornece melhor tratamento de erros
    
    Use `socks5://` a menos que você precise especificamente de SOCKS4 (`socks4://`).

## Proxies Autenticados

O Pydoll lida automaticamente com a autenticação de proxy sem intervenção manual.

### Como a Autenticação Funciona

Quando você fornece credenciais na URL do proxy, o Pydoll:

1.  **Intercepta o desafio de autenticação** usando o domínio Fetch
2.  **Responde automaticamente** com as credenciais
3.  **Continua a navegação** sem interrupções

Isso acontece de forma transparente, você não precisa lidar com a autenticação manualmente!

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def authenticated_proxy_example():
    options = ChromiumOptions()
    
    # Proxy com autenticação (usuario:senha)
    options.add_argument('--proxy-server=http://user:pass@proxy.example.com:8080')
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        # Autenticação tratada automaticamente!
        await tab.go_to('https://example.com')
        print("Conectado através de proxy autenticado")

asyncio.run(authenticated_proxy_example())
```

!!! tip "Formato das Credenciais"
    Inclua as credenciais diretamente na URL do proxy:

    - HTTP: `http://username:password@host:port`
    - HTTPS: `https://username:password@host:port`
    - SOCKS5: `socks5://username:password@host:port`

    O Pydoll extrai e usa automaticamente essas credenciais.

!!! warning "Limitação da Autenticação SOCKS5"
    **O Chrome não suporta autenticação SOCKS5 nativamente** ([Chromium Issue #40323993](https://issues.chromium.org/issues/40323993)). Credenciais incorporadas em `socks5://user:pass@host:port` são silenciosamente ignoradas — o Chrome envia apenas uma saudação "sem autenticação" para o proxy SOCKS5.

    Isso significa que a autenticação automática de proxy do Pydoll (via `Fetch.authRequired`) **não funciona para SOCKS5**, pois o Chrome nunca emite um desafio HTTP 407 para conexões SOCKS5.

    **Solução — Proxy forwarder local:**

    Execute um proxy SOCKS5 local (sem autenticação) que encaminha para o proxy autenticado remoto. O Pydoll fornece um script pronto para uso:

    ```python
    import asyncio
    from pydoll.utils import SOCKS5Forwarder
    from pydoll.browser.chromium import Chrome
    from pydoll.browser.options import ChromiumOptions

    async def main():
        forwarder = SOCKS5Forwarder(
            remote_host='proxy.example.com',
            remote_port=1080,
            username='myuser',
            password='mypass',
            local_port=1081,
        )
        async with forwarder:
            options = ChromiumOptions()
            options.add_argument('--proxy-server=socks5://127.0.0.1:1081')

            async with Chrome(options=options) as browser:
                tab = await browser.start()
                await tab.go_to('https://httpbin.org/ip')

    asyncio.run(main())
    ```

    O forwarder realiza o handshake de usuário/senha com o proxy remoto enquanto o Chrome se conecta ao localhost sem autenticação.

    Para a explicação técnica completa de por que isso acontece, veja **[Análise Profunda da Autenticação SOCKS5](../../deep-dive/network/socks-proxies.md#autenticacao-socks5-e-chrome)**.

### Detalhes da Implementação da Autenticação

O Pydoll usa o **domínio Fetch** do Chrome no nível do navegador para interceptar e lidar com desafios de autenticação:

```python
# Isso é tratado internamente pelo Pydoll
# Você não precisa escrever este código!

async def _handle_proxy_auth(event):
    """Manipulador interno de autenticação de proxy do Pydoll."""
    if event['params']['authChallenge']['source'] == 'Proxy':
        await browser.continue_request_with_auth(
            request_id=event['params']['requestId'],
            username='user',
            password='pass'
        )
```

!!! info "Nos Bastidores"
    Para detalhes técnicos sobre como o Pydoll intercepta e lida com a autenticação de proxy, veja:
    
    - **[Interceptação de Requisições](../network/interception.md)** - Domínio Fetch e manipulação de requisições
    - **[Sistema de Eventos](../advanced/event-system.md)** - Autenticação orientada a eventos

!!! warning "Conflitos do Domínio Fetch"
    Ao usar **proxies autenticados** + **interceptação de requisições no nível da aba**, esteja ciente:
    
    - O Pydoll habilita o Fetch no **Nível do Navegador** para autenticação de proxy
    - Se você habilitar o Fetch no **Nível da Aba**, eles compartilham o mesmo domínio
    - **Solução**: Chame `tab.go_to()` uma vez antes de habilitar a interceptação no nível da aba
    
    ```python
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        # 1. Primeira navegação dispara autenticação do proxy (Fetch Nível Navegador)
        await tab.go_to('https://example.com')
        
        # 2. Então habilite a interceptação no nível da aba com segurança
        await tab.enable_fetch_events()
        await tab.on('Fetch.requestPaused', my_interceptor)
        
        # 3. Continue com sua automação
        await tab.go_to('https://example.com/page2')
    ```
    
    Veja [Interceptação de Requisição - Proxy + Interceptação](../network/interception.md#private-proxy-request-interception-fetch) para detalhes.

## Lista de Bypass de Proxy

Exclua domínios específicos de usar o proxy:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def proxy_bypass_example():
    options = ChromiumOptions()
    
    # Usar proxy para a maior parte do tráfego
    options.add_argument('--proxy-server=http://proxy.example.com:8080')
    
    # Mas ignorar o proxy para estes domínios
    options.add_argument('--proxy-bypass-list=localhost,127.0.0.1,*.local,internal.company.com')
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        # Usa proxy
        await tab.go_to('https://external-site.com')
        
        # Ignora o proxy (conexão direta)
        await tab.go_to('http://localhost:8000')
        await tab.go_to('http://internal.company.com')

asyncio.run(proxy_bypass_example())
```

**Padrões da lista de bypass:**

| Padrão | Corresponde a | Exemplo |
|---|---|---|
| `localhost` | Apenas Localhost | `http://localhost` |
| `127.0.0.1` | IP de Loopback | `http://127.0.0.1` |
| `*.local` | Todos os domínios `.local` | `http://server.local` |
| `internal.company.com` | Domínio específico | `http://internal.company.com` |
| `192.168.1.*` | Faixa de IP | `http://192.168.1.100` |

!!! tip "Quando Usar a Lista de Bypass"
    Ignore o proxy para:
    
    - **Servidores de desenvolvimento local** (`localhost`, `127.0.0.1`)
    - **Recursos internos da empresa** (VPN, intranet)
    - **Ambientes de teste** (domínios `.local`, `.test`)
    - **Recursos de alta largura de banda** (quando o proxy é lento)

## PAC (Proxy Auto-Config)

Use um arquivo PAC para regras complexas de roteamento de proxy:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def pac_proxy_example():
    options = ChromiumOptions()
    
    # Carregar arquivo PAC de uma URL
    options.add_argument('--proxy-pac-url=http://proxy.example.com/proxy.pac')
    
    # Ou usar arquivo PAC local
    # options.add_argument('--proxy-pac-url=file:///path/to/proxy.pac')
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')

asyncio.run(pac_proxy_example())
```

**Exemplo de arquivo PAC:**

```javascript
function FindProxyForURL(url, host) {
    // Conexão direta para endereços locais
    if (isInNet(host, "192.168.0.0", "255.255.0.0") ||
        isInNet(host, "127.0.0.0", "255.0.0.0")) {
        return "DIRECT";
    }
    
    // Usar proxy específico para certos domínios
    if (dnsDomainIs(host, ".example.com")) {
        return "PROXY proxy1.example.com:8080";
    }
    
    // Proxy padrão para todo o resto
    return "PROXY proxy2.example.com:8080";
}
```

!!! info "Casos de Uso de Arquivo PAC"
    Arquivos PAC são úteis para:
    
    - **Regras de roteamento complexas** (baseadas em domínio, IP)
    - **Failover de proxy** (tentar múltiplos proxies)
    - **Balanceamento de carga** (distribuir entre pool de proxies)
    - **Ambientes corporativos** (gerenciamento centralizado de proxy)

## Rotação de Proxies

Rotacione entre múltiplos proxies para melhor distribuição:

```python
import asyncio
from itertools import cycle
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def rotating_proxy_example():
    # Lista de proxies
    proxies = [
        'http://user:pass@proxy1.example.com:8080',
        'http://user:pass@proxy2.example.com:8080',
        'http://user:pass@proxy3.example.com:8080',
    ]
    
    # Alternar entre os proxies
    proxy_pool = cycle(proxies)
    
    # Raspar múltiplas URLs com diferentes proxies
    urls = [
        'https://example.com/page1',
        'https://example.com/page2',
        'https://example.com/page3',
    ]
    
    for url in urls:
        # Obter próximo proxy
        proxy = next(proxy_pool)
        
        # Configurar opções com este proxy
        options = ChromiumOptions()
        options.add_argument(f'--proxy-server={proxy}')
        
        # Usar proxy para esta instância do navegador
        async with Chrome(options=options) as browser:
            tab = await browser.start()
            await tab.go_to(url)
            
            title = await tab.execute_script('return document.title')
            print(f"[{proxy.split('@')[1]}] {url}: {title}")

asyncio.run(rotating_proxy_example())
```

!!! tip "Estratégias de Rotação de Proxy"
    **Rotação por navegador** (acima):

    - Cada instância do navegador usa um proxy diferente
    - Melhor para isolamento e evitar conflitos de sessão
    
    **Rotação por requisição**:

    - Mais complexo, requer interceptação de requisições
    - Veja [Interceptação de Requisições](../network/interception.md) para implementação

## Proxies Residenciais vs Datacenter

Entender os tipos de proxy ajuda a escolher o serviço certo:

| Característica | Residenciais | Datacenter |
|---|---|---|
| **Fonte do IP** | ISPs residenciais reais | Data centers |
| **Legitimidade** | Alta (usuários reais) | Baixa (faixas conhecidas) |
| **Risco de Detecção** | Muito baixo | Alto |
| **Velocidade** | Média (150-500ms) | Muito rápida (<50ms) |
| **Custo** | Caro ($5-15/GB) | Barato ($0.10-1/GB) |
| **Melhor Para** | Sites anti-bot, e-commerce | APIs, ferramentas internas |

### Proxies Residenciais

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def residential_proxy_example():
    """Usar proxy residencial para sites anti-bot."""
    options = ChromiumOptions()
    
    # Proxy residencial com alta pontuação de confiança
    options.add_argument('--proxy-server=http://user:pass@residential.proxy.com:8080')
    
    # Combinar com opções de furtividade
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36')
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        # Acessar site protegido
        await tab.go_to('https://protected-site.com')
        print("Acessado com sucesso através de proxy residencial")

asyncio.run(residential_proxy_example())
```

**Quando usar Residenciais:**

- Sites com forte proteção anti-bot (Cloudflare, DataDome)
- Raspagem de e-commerce (Amazon, eBay, etc.)
- Automação de mídias sociais
- Serviços financeiros
- Qualquer site que bloqueia ativamente IPs de datacenter

### Proxies Datacenter

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def datacenter_proxy_example():
    """Usar proxy datacenter rápido para APIs e sites não protegidos."""
    options = ChromiumOptions()
    
    # Proxy datacenter rápido
    options.add_argument('--proxy-server=http://user:pass@datacenter.proxy.com:8080')
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        # Raspagem rápida de API
        await tab.go_to('https://api.example.com/data')

asyncio.run(datacenter_proxy_example())
```

**Quando usar Datacenter:**

- APIs públicas sem limites de requisição
- Automação interna/corporativa
- Sites sem medidas anti-bot
- Raspagem de alto volume e crítica em velocidade
- Desenvolvimento e testes

!!! warning "A Qualidade do Proxy Importa"
    **Proxies ruins** causam mais problemas do que resolvem:
    
    - Tempos de resposta lentos (timeouts)
    - Falhas de conexão (taxas de erro)
    - IPs em lista negra (banimentos imediatos)
    - Vazamento do IP real (violação de privacidade)
    
    **Invista em proxies de qualidade** de provedores respeitáveis. Proxies gratuitos quase nunca valem a pena.

## Testando Seu Proxy

Verifique a configuração do proxy antes de rodar a automação em produção:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def test_proxy():
    """Testar conexão e configuração do proxy."""
    proxy_url = 'http://user:pass@proxy.example.com:8080'
    
    options = ChromiumOptions()
    options.add_argument(f'--proxy-server={proxy_url}')
    
    try:
        async with Chrome(options=options) as browser:
            tab = await browser.start()
            
            # Teste 1: Conexão
            print("Testando conexão do proxy...")
            await tab.go_to('https://httpbin.org/ip', timeout=10)
            
            # Teste 2: Verificação de IP
            print("Verificando IP do proxy...")
            ip_response = await tab.execute_script('return document.body.textContent')
            print(f"[OK] IP do Proxy: {ip_response}")
            
            # Teste 3: Localização geográfica (se disponível)
            await tab.go_to('https://ipapi.co/json/')
            geo_data = await tab.execute_script('return document.body.textContent')
            print(f"[OK] Dados geográficos: {geo_data}")
            
            # Teste 4: Teste de velocidade
            import time
            start = time.time()
            await tab.go_to('https://example.com')
            load_time = time.time() - start
            print(f"[OK] Tempo de carregamento: {load_time:.2f}s")
            
            if load_time > 5:
                print("[AVISO] Tempo de resposta do proxy lento")
            
            print("\n[SUCESSO] Todos os testes de proxy passaram!")
            
    except asyncio.TimeoutError:
        print("[ERRO] Timeout na conexão do proxy")
    except Exception as e:
        print(f"[ERRO] Teste de proxy falhou: {e}")

asyncio.run(test_proxy())
```

## Leitura Adicional

- **[Análise Profunda da Arquitetura de Proxy](../../deep-dive/proxy-architecture.md)** - Fundamentos de rede, TCP/UDP, HTTP/2/3, internos do SOCKS5, análise de segurança e construção do seu próprio servidor proxy
- **[Opções do Navegador](browser-options.md)** - Argumentos de linha de comando e configuração
- **[Interceptação de Requisições](../network/interception.md)** - Como a autenticação de proxy funciona
- **[Preferências do Navegador](browser-preferences.md)** - Furtividade e fingerprinting
- **[Contextos](../browser-management/contexts.md)** - Usando diferentes proxies por contexto

!!! tip "Comece Simples"
    Comece com uma configuração de proxy simples, teste exaustivamente, depois adicione complexidade (rotação, lógica de retentativa, monitoramento) conforme necessário. Proxies de qualidade são mais importantes do que estratégias complexas de rotação.
    
    Para aqueles interessados em entender proxies em um nível mais profundo, a **[Análise Profunda da Arquitetura de Proxy](../../deep-dive/proxy-architecture.md)** fornece cobertura abrangente de protocolos de rede, considerações de segurança e até o guia na construção do seu próprio servidor proxy.