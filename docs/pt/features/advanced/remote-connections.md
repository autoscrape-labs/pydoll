# Conexões Remotas e Automação Híbrida

O Pydoll permite que você se conecte a navegadores já em execução via WebSocket, habilitando cenários de controle remoto e automação híbrida. Isso é perfeito para pipelines de CI/CD, ambientes contêinerizados, sessões de depuração e integração do Pydoll com ferramentas CDP existentes.

!!! info "Nenhuma Configuração Necessária"
    Diferente da automação tradicional que inicia navegadores, conexões remotas permitem controlar navegadores que já estão rodando. Nenhum gerenciamento de processo é necessário!

## Por que Conexões Remotas?

Conexões remotas desbloqueiam cenários poderosos de automação:

| Caso de Uso | Benefício |
|---|---|
| **Pipelines de CI/CD** | Conecte-se a contêineres de navegador sem gerenciar processos |
| **Ambientes Docker** | Controle navegadores rodando em contêineres separados |
| **Depuração Remota** | Automatize navegadores em servidores remotos ou VMs |
| **Ferramental Híbrido** | Integre o Pydoll com sua infraestrutura CDP existente |
| **Desenvolvimento** | Anexe ao seu navegador local para testes rápidos |
| **Automação Multi-Ferramenta** | Compartilhe sessões de navegador entre diferentes ferramentas |

## Configurando um Servidor de Navegador Remoto

!!! tip "Já Tem um Serviço de Navegador Remoto?"
    Se você está usando um serviço de navegador na nuvem (BrowserStack, Selenium Grid, LambdaTest, etc.) ou já tem uma instância do Chrome rodando com uma URL WebSocket, você pode **pular esta seção inteira** e ir direto para [Métodos de Conexão](#métodos-de-conexão) para aprender como se conectar com o Pydoll.

Antes de poder se conectar remotamente, você precisa iniciar o Chrome com a depuração habilitada e configurado corretamente para aceitar conexões externas.

### Configuração Básica do Servidor (Linux)

Inicie o Chrome com depuração remota em um servidor:

```bash
# Configuração básica - acessível apenas do localhost
google-chrome \
  --remote-debugging-port=9222 \
  --headless=new \
  --no-sandbox \
  --disable-dev-shm-usage \
  --user-data-dir=/tmp/chrome-profile

# Configuração do servidor - acessível de outras máquinas
google-chrome \
  --remote-debugging-port=9222 \
  --remote-debugging-address=0.0.0.0 \
  --headless=new \
  --no-sandbox \
  --disable-dev-shm-usage \
  --user-data-dir=/tmp/chrome-profile
```

!!! warning "Criticidade de Segurança"
    Usar `--remote-debugging-address=0.0.0.0` torna a porta de depuração acessível de **qualquer interface de rede**. Isso é necessário para conexões remotas, mas cria um risco de segurança significativo se exposto à internet.

### Configuração Recomendada do Servidor

```bash
# Configuração pronta para produção
google-chrome \
  --remote-debugging-port=9222 \
  --remote-debugging-address=0.0.0.0 \
  --headless=new \
  --no-sandbox \
  --disable-dev-shm-usage \
  --disable-gpu \
  --disable-software-rasterizer \
  --disable-extensions \
  --disable-background-networking \
  --disable-background-timer-throttling \
  --disable-client-side-phishing-detection \
  --disable-popup-blocking \
  --disable-prompt-on-repost \
  --disable-sync \
  --metrics-recording-only \
  --no-first-run \
  --safebrowsing-disable-auto-update \
  --user-data-dir=/tmp/chrome-remote-$(date +%s)
```

**Flags chave explicadas:**

| Flag | Propósito |
|---|---|
| `--remote-debugging-port=9222` | Habilita o CDP na porta 9222 |
| `--remote-debugging-address=0.0.0.0` | Permite conexões externas (risco de segurança!) |
| `--headless=new` | Executa sem GUI (modo servidor) |
| `--no-sandbox` | Necessário em Docker/contêineres (trade-off de segurança) |
| `--disable-dev-shm-usage` | Previne problemas de memória /dev/shm em contêineres |
| `--disable-gpu` | Sem aceleração por GPU (recomendado para headless) |
| `--user-data-dir=/tmp/...` | Perfil isolado por instância |

!!! warning "Sobre a Flag --no-sandbox"
    A flag `--no-sandbox` desabilita o sandbox de segurança do Chrome, que isola o processo do navegador do sistema. Esta flag é **necessária** na maioria dos ambientes Docker/contêineres devido a restrições de capacidade do kernel, mas traz implicações de segurança:
    
    - **Risco**: Remove o isolamento entre o navegador e o sistema
    - **Quando usar**: Contêineres Docker, ambientes restritos
    - **Mitigação**: Garanta isolamento em nível de contêiner (namespaces, cgroups) e evite rodar como root
    
    Considere usar `--no-sandbox` apenas quando absolutamente necessário e implemente camadas adicionais de segurança no nível do contêiner.

### Configuração do Docker

Crie um servidor Chrome contêinerizado:

!!! tip "Usando Imagens Prontas"
    Para produção, considere usar imagens oficiais pré-construídas em vez de construir a sua própria:
    
    - **Imagens Selenium**: `selenium/standalone-chrome` (inclui WebDriver)
    - **Zenika Alpine Chrome**: `zenika/alpine-chrome` (leve, ~200MB)
    - **Browserless**: `browserless/chrome` (pronto para produção com monitoramento)
    
    Essas imagens são atualizadas regularmente, testadas em segurança e otimizadas para ambientes de contêiner.

**Dockerfile (Build Personalizado):**
```dockerfile
FROM ubuntu:22.04

# Instalar Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Expor porta de depuração
EXPOSE 9222

# Iniciar Chrome com depuração remota
CMD ["google-chrome", \
     "--remote-debugging-port=9222", \
     "--remote-debugging-address=0.0.0.0", \
     "--headless=new", \
     "--no-sandbox", \
     "--disable-dev-shm-usage", \
     "--disable-gpu", \
     "--user-data-dir=/tmp/chrome-profile"]
```

**docker-compose.yml:**
```yaml
services:
  chrome-server:
    build: .
    ports:
      - "127.0.0.1:9222:9222"
    
    # Descomente a linha abaixo SOMENTE se precisar de acesso remoto
    # E tiver protegido a porta com firewall ou proxy.
    # - "9222:9222"

    shm_size: '2gb'  # Crítico: Chrome usa /dev/shm para memória compartilhada
                      # O shm_size padrão do Docker (64MB) é insuficiente
    restart: unless-stopped
    environment:
      - DISPLAY=:99
    networks:
      - automation-network
    # Opcional: Limites de recursos para produção
    # deploy:
    #   resources:
    #     limits:
    #       cpus: '2'
    #       memory: 4G

  automation-client:
    image: python:3.11
    depends_on:
      - chrome-server
    volumes:
      - ./:/app
    working_dir: /app
    command: python automation_script.py
    environment:
      - CHROME_WS=ws://chrome-server:9222/devtools/browser
    networks:
      - automation-network

networks:
  automation-network:
    driver: bridge
```

**Uso:**
```bash
# Iniciar a stack
docker-compose up -d

# Verificar se o Chrome está rodando
curl http://localhost:9222/json/version

# Conectar do cliente de automação (dentro da rede Docker)
# ws://chrome-server:9222/devtools/browser/...
```

### Serviço Systemd (Servidor Linux)

Crie um serviço Chrome persistente:

**/etc/systemd/system/chrome-remote.service:**
```ini
[Unit]
Description=Chrome Remote Debugging Server
After=network.target

[Service]
Type=simple
User=chrome-user
Group=chrome-user
Environment="DISPLAY=:99"
ExecStart=/usr/bin/google-chrome \
    --remote-debugging-port=9222 \
    --remote-debugging-address=0.0.0.0 \
    --headless=new \
    --no-sandbox \
    --disable-dev-shm-usage \
    --disable-gpu \
    --user-data-dir=/var/lib/chrome-remote
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Configuração e gerenciamento:**
```bash
# Criar usuário dedicado
sudo useradd -r -s /bin/false chrome-user
sudo mkdir -p /var/lib/chrome-remote
sudo chown chrome-user:chrome-user /var/lib/chrome-remote

# Instalar e habilitar serviço
sudo systemctl daemon-reload
sudo systemctl enable chrome-remote
sudo systemctl start chrome-remote

# Verificar status
sudo systemctl status chrome-remote

# Ver logs
sudo journalctl -u chrome-remote -f

# Reiniciar serviço
sudo systemctl restart chrome-remote
```

### Configuração de Segurança de Rede

#### Regras de Firewall (iptables)

```bash
# Permitir que apenas IPs específicos acessem a porta 9222
sudo iptables -A INPUT -p tcp --dport 9222 -s 192.168.1.100 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 9222 -j DROP

# Salvar regras
sudo iptables-save > /etc/iptables/rules.v4
```

#### Regras de Firewall (ufw)

```bash
# Negar todo o acesso à porta 9222 por padrão
sudo ufw deny 9222

# Permitir IP específico
sudo ufw allow from 192.168.1.100 to any port 9222

# Permitir sub-rede específica
sudo ufw allow from 192.168.1.0/24 to any port 9222

# Habilitar firewall
sudo ufw enable
```

#### Proxy Reverso Nginx (com Autenticação)

Proteja a depuração do Chrome com autenticação HTTP:

**/etc/nginx/sites-available/chrome-remote:**
```nginx
server {
    listen 80;
    server_name chrome.example.com;

    # Autenticação básica
    auth_basic "Chrome Remote Debugging";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass http://localhost:9222;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400;
    }
}
```

**Configuração:**
```bash
# Criar arquivo de senha
sudo htpasswd -c /etc/nginx/.htpasswd admin

# Habilitar site
sudo ln -s /etc/nginx/sites-available/chrome-remote /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Conectar com autenticação
# ws://admin:password@chrome.example.com/devtools/browser/...
```

### Conectando de Outro Computador

Uma vez que seu servidor esteja configurado, conecte-se da sua máquina cliente:

```python
import asyncio
import aiohttp
from pydoll.browser.chromium import Chrome

async def connect_to_remote_server():
    """Conectar ao Chrome rodando em um servidor remoto."""
    # IP e porta do servidor
    server_ip = "192.168.1.100"
    server_port = 9222

    async with aiohttp.ClientSession() as session:
        # Consultar o servidor por alvos disponíveis
        url = f"http://{server_ip}:{server_port}/json/version"
        
        async with session.get(url) as response:
            data = await response.json()
            ws_url = data['webSocketDebuggerUrl']
            
            print(f"Informações do servidor:")
            print(f"  Navegador: {data.get('Browser')}")
            print(f"  Protocolo: {data.get('Protocol-Version')}")
            print(f"  WebSocket: {ws_url}")
    
    # 2. Conectar ao navegador
    chrome = Chrome()
    tab = await chrome.connect(ws_url)
    
    print(f"\n[SUCESSO] Conectado ao servidor Chrome remoto!")
    
    # 3. Usar normalmente
    await tab.go_to('https://example.com')
    title = await tab.execute_script('return document.title')
    print(f"Título da página: {title}")
    
    # 4. Limpeza
    await chrome.close()

asyncio.run(connect_to_remote_server())
```

### Testando a Configuração do Seu Servidor

```bash
# 1. Verificar se o Chrome está rodando
ps aux | grep chrome

# 2. Verificar se a porta está escutando
netstat -tulpn | grep 9222
# Ou
ss -tulpn | grep 9222

# 3. Testar acesso local
curl http://localhost:9222/json/version

# 4. Testar acesso remoto (da máquina cliente)
curl http://SERVER_IP:9222/json/version

# 5. Verificar URL do WebSocket
curl http://SERVER_IP:9222/json/version | jq -r '.webSocketDebuggerUrl'

# 6. Listar todos os alvos disponíveis (abas/páginas)
curl http://SERVER_IP:9222/json/list
```

### Configuração de Múltiplas Instâncias

Execute múltiplas instâncias do Chrome em portas diferentes:

```bash
#!/bin/bash
# start-chrome-pool.sh

for port in 9222 9223 9224 9225; do
    google-chrome \
        --remote-debugging-port=$port \
        --remote-debugging-address=0.0.0.0 \
        --headless=new \
        --no-sandbox \
        --disable-dev-shm-usage \
        --user-data-dir=/tmp/chrome-$port &
    
    echo "Iniciado Chrome na porta $port"
done

echo "Pool de Chrome pronto. Portas: 9222-9225"
```

**Cliente Python com pool:**
```python
import asyncio
from pydoll.browser.chromium import Chrome
import aiohttp

async def connect_to_pool(server_ip: str, ports: list[int]):
    """Conectar a múltiplas instâncias do Chrome."""
    tasks = []
    
    for port in ports:
        task = connect_to_instance(server_ip, port)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return results

async def connect_to_instance(server_ip: str, port: int):
    """Conectar a uma única instância do Chrome."""
    # Obter URL do WebSocket
    async with aiohttp.ClientSession() as session:
        url = f"http://{server_ip}:{port}/json/version"
        async with session.get(url) as response:
            data = await response.json()
            ws_url = data['webSocketDebuggerUrl']
    
    # Conectar
    chrome = Chrome()
    tab = await chrome.connect(ws_url)
    
    # Rodar automação
    await tab.go_to('https://example.com')
    title = await tab.execute_script('return document.title')
    
    print(f"Porta {port}: {title}")
    
    await chrome.close()
    return title

# Uso
asyncio.run(connect_to_pool('192.168.1.100', [9222, 9223, 9224, 9225]))
```

## Métodos de Conexão

O Pydoll oferece duas abordagens para conexões remotas, cada uma adequada para cenários diferentes.

### Método 1: Conexão no Nível do Navegador

Conecte-se a um navegador em execução usando seu endpoint WebSocket e tenha acesso a todas as abas abertas:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def connect_to_remote_browser():
    chrome = Chrome()
    
    # Conectar ao navegador remoto via WebSocket
    tab = await chrome.connect('ws://localhost:9222/devtools/browser/XXXX')
    
    # A aba retornada é a primeira aba disponível
    print(f"Conectado à aba: {await tab.execute_script('return document.title')}")
    
    # Você pode obter todas as outras abas também
    all_tabs = await chrome.get_opened_tabs()
    print(f"Total de abas disponíveis: {len(all_tabs)}")
    
    # Use a aba normalmente
    await tab.go_to('https://example.com')
    element = await tab.find(id='main-content')
    text = await element.text
    print(f"Conteúdo: {text}")
    
    # Limpeza
    await chrome.close()

asyncio.run(connect_to_remote_browser())
```

!!! tip "Obtendo a URL do WebSocket"
    Inicie o Chrome com a depuração habilitada:
    ```bash
    # Linux/Mac
    google-chrome --remote-debugging-port=9222
    
    # Windows
    "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
    ```
    
    **Para conexões locais** (mesma máquina):
    
    - Visite `http://localhost:9222/json/version` no seu navegador para obter a URL do WebSocket no campo `webSocketDebuggerUrl`
    - Ou consulte programaticamente como mostrado no exemplo acima usando `aiohttp`
    - Para depuração rápida, você também pode verificar `browser._connection_port` após iniciar uma instância local do navegador
    
    **Para conexões remotas** (máquina diferente):
    
    - Consulte `http://SERVER_IP:9222/json/version` da sua máquina cliente
    - Use a `webSocketDebuggerUrl` da resposta, substituindo `localhost` pelo IP real do servidor, se necessário

### Método 2: Controle Direto de Elemento (Abordagem Híbrida)

Se você já tem sua própria integração CDP ou ferramentas de baixo nível, pode envolver elementos existentes com a API de alto nível do Pydoll:

```python
import asyncio
import json
from pydoll.connection.connection_handler import ConnectionHandler
from pydoll.elements.web_element import WebElement

async def custom_cdp_integration():
    """Use o Pydoll junto com sua implementação CDP personalizada."""
    # Sua configuração CDP existente encontrou um elemento
    page_ws = 'ws://localhost:9222/devtools/page/ABC123'
    
    # Você usou Runtime.evaluate para encontrar um elemento
    # e obteve seu objectId
    element_object_id = '{\"injectedScriptId\":1,\"id\":1}'
    
    # Criar conexão Pydoll
    connection = ConnectionHandler(ws_address=page_ws)
    
    # Envolver o elemento
    button = WebElement(
        object_id=element_object_id,
        connection_handler=connection
    )
    
    # Usar os métodos de alto nível do Pydoll
    await button.wait_until(is_visible=True, timeout=5)
    await button.wait_until(is_interactable=True)
    
    # Clicar com deslocamento realista
    await button.click(offset_x=5, offset_y=5)
    
    # Obter propriedades computadas facilmente
    is_enabled = await button.is_enabled()
    bounds = await button.bounds
    
    print(f"Botão clicado! Habilitado: {is_enabled}, Limites: {bounds}")
    
    # Limpeza
    await connection.close()

asyncio.run(custom_cdp_integration())
```

!!! tip "Formato do Object ID"
    O `objectId` é uma string retornada por comandos CDP como `Runtime.evaluate` ou `DOM.resolveNode`. Geralmente é uma string JSON com campos como `injectedScriptId` e `id`.


!!! info "O Melhor dos Dois Mundos"
    Esta abordagem híbrida permite que você aproveite sua infraestrutura CDP existente enquanto se beneficia da API ergonômica de elementos do Pydoll para interações, esperas e acesso a propriedades.

## Considerações de Segurança

!!! danger "Ambientes de Produção"
    Portas de depuração remota expõem **controle total** sobre o navegador, incluindo:
    
    - Acesso a todas as páginas e dados
    - Capacidade de executar JavaScript arbitrário
    - Acesso a cookies e sessões
    - Acesso ao sistema de arquivos via downloads
    
    **Nunca exponha portas de depuração à internet sem autenticação adequada e segurança de rede!**

### Práticas de Segurança Recomendadas

| Prática | Por quê | Como |
|---|---|---|
| **Túneis SSH** | Criptografa o tráfego e autentica | `ssh -L 9222:localhost:9222 user@host` |
| **VPN** | Segurança em nível de rede | Conectar via VPN corporativa/privada |
| **Regras de Firewall** | Restringir acesso | Permitir apenas IPs específicos |
| **Redes Docker** | Isolamento de contêiner | Usar redes Docker privadas |
| **Sem Exposição Pública** | Prevenir ataques | Nunca fazer bind para `0.0.0.0` em produção |

## Leitura Adicional

- **[Sistema de Eventos](event-system.md)** - Monitore eventos remotos do navegador
- **[Monitoramento de Rede](../network/monitoring.md)** - Rastreie requisições em navegadores remotos
- **[Opções do Navegador](../configuration/browser-options.md)** - Configure navegadores locais antes de iniciar

!!! tip "Comece Local, Escale Remotamente"
    Desenvolva sua automação localmente com `browser.start()` para iterações rápidas, depois implante com `browser.connect()` para pipelines de CI/CD de produção e ambientes contêinerizados.