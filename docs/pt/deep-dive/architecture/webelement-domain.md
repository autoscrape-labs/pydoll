# Arquitetura do Domínio WebElement

O domínio WebElement faz a ponte entre o código de automação de alto nível e a interação DOM de baixo nível através do Chrome DevTools Protocol. Este documento explora sua arquitetura interna, padrões de design e decisões de engenharia.

!!! info "Uso Prático"
    Para exemplos de uso e padrões de interação, veja:
    
    - [Guia de Localização de Elementos](../features/element-finding.md)
    - [Interações Humanizadas](../features/automation/human-interactions.md)
    - [Operações com Arquivos](../features/automation/file-operations.md)

## Visão Geral da Arquitetura

O WebElement representa uma **referência de objeto remoto** para um elemento DOM através do mecanismo `objectId` do CDP:

```
Código do Usuário → WebElement → ConnectionHandler → CDP Runtime → DOM do Navegador
```

**Principais características:**

- **Assíncrono por design**: Todas as operações seguem o padrão async/await do Python
- **Referência remota**: Mantém o `objectId` do CDP para o elemento no lado do navegador
- **Herança de Mixin**: Herda `FindElementsMixin` para buscas de elementos filhos
- **Estado híbrido**: Combina atributos em cache com consultas DOM em tempo real

### Estado Principal (Core)

```python
class WebElement(FindElementsMixin):
    def __init__(self, object_id: str, connection_handler: ConnectionHandler, ...):
        self._object_id = object_id              # Referência de objeto remoto CDP
        self._connection_handler = connection_handler  # Comunicação WebSocket
        self._attributes: dict[str, str] = {}    # Atributos HTML em cache
        self._search_method = method             # Como o elemento foi encontrado (debug)
        self._selector = selector                # Seletor original (debug)
```

**Por que atributos em cache?** A localização inicial do elemento retorna atributos HTML. O cache fornece acesso síncrono rápido a propriedades comuns (`id`, `class`, `tag_name`) sem chamadas CDP adicionais.

## Padrões de Design

### 1. Padrão de Comando (Command Pattern)

Todas as interações de elementos são traduzidas para comandos CDP:

| Operação do Usuário | Domínio CDP | Comando |
|----------------|-----------|---------|
| `element.click()` | Input | `Input.dispatchMouseEvent` |
| `element.text` | Runtime | `Runtime.callFunctionOn` |
| `element.bounds` | DOM | `DOM.getBoxModel` |
| `element.take_screenshot()` | Page | `Page.captureScreenshot` |

### 2. Padrão de Ponte (Bridge Pattern)

O WebElement abstrai a complexidade do protocolo CDP:

```python
async def click(self, x_offset=0, y_offset=0, hold_time=0.1):
    # API de alto nível
    
    # → Traduz para comandos CDP de baixo nível:
    # 1. DOM.getBoxModel (obter posição)
    # 2. Input.dispatchMouseEvent (pressionar)
    # 3. Input.dispatchMouseEvent (soltar)
```

### 3. Herança de Mixin para Buscas de Filhos

**Por que herdar FindElementsMixin?** Permite buscas relativas ao elemento:

```python
form = await tab.find(id='login-form')
username = await form.find(name='username')  # Busca dentro do formulário
```

**Decisão de design:** Composição (`form.finder.find()`) seria mais flexível, mas menos ergonômica. A herança foi escolhida pela simplicidade da API.

## Sistema de Propriedades Híbrido

**Inovação arquitetural:** O WebElement combina acesso a propriedades síncronas e assíncronas.

### Propriedades Síncronas (Atributos em Cache)

```python
@property
def id(self) -> str:
    return self._attributes.get('id')  # Dos atributos HTML em cache

@property  
def class_name(self) -> str:
    return self._attributes.get('class_name')  # 'class' → 'class_name' (palavra-chave do Python)
```

**Fonte:** Lista plana da resposta de localização do elemento CDP, analisada durante o `__init__`.

### Propriedades Assíncronas (Estado DOM em Tempo Real)

```python
@property
async def text(self) -> str:
    outer_html = await self.inner_html  # Chamada CDP
    soup = BeautifulSoup(outer_html, 'html.parser')
    return soup.get_text(strip=True)

@property
async def bounds(self) -> dict:
    response = await self._execute_command(DomCommands.get_box_model(self._object_id))
    # Analisar e retornar limites (bounds)
```

**Justificativa:** Texto e limites (bounds) são **dinâmicos** - eles mudam conforme a página é atualizada. Atributos são **estáticos** - capturados no momento da localização.

| Tipo de Propriedade | Acesso | Fonte | Caso de Uso |
|--------------|--------|--------|----------|
| Síncrona | `element.id` | Atributos em cache | Acesso rápido, dados estáticos |
| Assíncrona | `await element.text` | Consulta CDP ao vivo | Estado atual, dados dinâmicos |

## Implementação do Clique: Pipeline Multi-Estágio

Operações de clique seguem um pipeline sofisticado para garantir confiabilidade:

### 1. Detecção de Elemento Especial

```python
async def click(self, x_offset=0, y_offset=0, hold_time=0.1):
    # Estágio 1: Lidar com elementos especiais
    if self._is_option_tag():
        return await self.click_option_tag()  # <option> precisa de JavaScript para selecionar
```

**Por que tratamento especial?** Elementos `<option>` dentro de `<select>` não respondem a eventos de mouse. Requer JavaScript `selected = true`.

### 2. Verificação de Visibilidade

```python
    # Estágio 2: Verificar se o elemento está visível
    if not await self.is_visible():
        raise ElementNotVisible()
```

**Por que verificar?** Eventos de mouse do CDP miram coordenadas. Elementos ocultos receberiam cliques em posições erradas ou falhariam silenciosamente.

### 3. Cálculo de Posição

```python
    # Estágio 3: Rolar para visualização e obter posição
    await self.scroll_into_view()
    bounds = await self.bounds
    
    # Estágio 4: Calcular coordenadas do clique
    position_to_click = (
        bounds['x'] + bounds['width'] / 2 + x_offset,
        bounds['y'] + bounds['height'] / 2 + y_offset,
    )
```

**Suporte a offset (deslocamento):** Permite posições de clique variadas para comportamento semelhante ao humano (anti-detecção).

### 4. Despacho de Evento de Mouse

```python
    # Estágio 5: Enviar eventos de mouse CDP
    await self._execute_command(InputCommands.mouse_press(*position_to_click))
    await asyncio.sleep(hold_time)  # Espera configurável (padrão 0.1s)
    await self._execute_command(InputCommands.mouse_release(*position_to_click))
```

**Por que dois comandos?** Simula o comportamento real do mouse (pressionar → segurar → soltar). Alguns sites detectam cliques instantâneos como bots.

### Alternativa de Clique (Fallback): JavaScript

```python
async def click_using_js(self):
    """Fallback para elementos que não podem ser clicados via eventos de mouse."""
    await self.execute_script('this.click()')
```

**Quando usar:**
- Elementos ocultos (ex: inputs de arquivo estilizados com CSS)
- Elementos atrás de sobreposições (overlays)
- Cenários críticos de performance (pula verificações de visibilidade/posição)

!!! info "Cliques de Mouse vs. JavaScript"
    Veja [Interações Humanizadas](../features/automation/human-interactions.md) para saber quando usar cada abordagem e as implicações de detecção.

## Arquitetura de Screenshot: Regiões de Corte (Clip)

**Mecanismo chave:** `Page.captureScreenshot` com parâmetro `clip`.

```python
async def take_screenshot(self, path: str, quality: int = 100):
    # 1. Obter limites (bounds) do elemento (posição + dimensões)
    bounds = await self.get_bounds_using_js()
    
    # 2. Criar região de corte (clip)
    clip = Viewport(x=bounds['x'], y=bounds['y'], 
                    width=bounds['width'], height=bounds['height'], scale=1)
    
    # 3. Capturar apenas a região cortada
    screenshot = await self._execute_command(
        PageCommands.capture_screenshot(format=ScreenshotFormat.JPEG, clip=clip, quality=quality)
    )
```

**Por que limites (bounds) com JavaScript?** `DOM.getBoxModel` pode falhar para certos elementos. `getBoundingClientRect()` do JavaScript é uma alternativa (fallback) mais confiável.

**Limitação de formato:** Screenshots de elementos sempre usam JPEG (restrição do CDP com regiões de corte).

!!! info "Capacidades de Screenshot"
    Veja [Screenshots & PDFs](../features/automation/screenshots-and-pdfs.md) para comparação entre screenshots de página inteira vs. elementos.

## Contexto de Execução JavaScript

**Recurso crítico do CDP:** `Runtime.callFunctionOn(objectId, ...)` executa JavaScript **no contexto do elemento** (`this` = elemento).

```python
async def execute_script(self, script: str, return_by_value=False):
    return await self._execute_command(
        RuntimeCommands.call_function_on(self._object_id, script, return_by_value)
    )
```

**Casos de uso:**

- Verificações de visibilidade: `await element.is_visible()` → JavaScript verifica estilos computados
- Manipulação de estilo: `await element.execute_script("this.style.border = '2px solid red'")`
- Acesso a atributos: Algumas propriedades exigem JavaScript (ex: `value` para inputs)

**Alternativa (não usada):** Executar script global com seletor de elemento → Mais lento, arrisca referências obsoletas.

## Pipeline de Verificação de Estado

**Estratégia de confiabilidade:** Pré-verificar o estado do elemento antes de interações para prevenir falhas.

| Verificação | Propósito | Implementação |
|-------|---------|----------------|
| `is_visible()` | Elemento na viewport, não oculto | JavaScript: `offsetWidth > 0 && offsetHeight > 0` |
| `is_on_top()` | Sem sobreposições (overlays) bloqueando o elemento | JavaScript: `document.elementFromPoint(x, y) === this` |
| `is_interactable()` | Visível + no topo | Combina ambas as verificações |

**Por que JavaScript para visibilidade?** CSS `display: none`, `visibility: hidden`, `opacity: 0` todos afetam a visibilidade de formas diferentes. JavaScript fornece uma verificação unificada.

## Estratégias de Performance

### 1. Otimização Específica da Operação

**Princípio:** Escolher a abordagem mais rápida para cada tipo de operação.

| Operação | Abordagem Primária | Justificativa |
|-----------|-----------------|-----------|
| Extração de texto | Análise (parsing) com BeautifulSoup | Mais preciso que o `innerText` do JavaScript |
| Verificação de visibilidade | JavaScript | Chamada CDP única vs. múltiplas consultas DOM |
| Clique | Eventos de mouse CDP | Mais realista, necessário para anti-detecção |
| Limites (Bounds) | `DOM.getBoxModel` | Mais rápido que JavaScript, com JS como fallback |

### 2. Computação Local

**Minimizar viagens de ida e volta ao CDP (round-trips)** computando localmente quando possível:

```python
# Bom: Consulta única de limites (bounds), cálculo local
bounds = await element.bounds
click_x = bounds['x'] + bounds['width'] / 2 + offset_x
click_y = bounds['y'] + bounds['height'] / 2 + offset_y

# Ruim: Múltiplas chamadas CDP para matemática simples
click_x = await element.execute_script('return this.offsetLeft + this.offsetWidth / 2')
click_y = await element.execute_script('return this.offsetTop + this.offsetHeight / 2')
```

### 3. Atributos em Cache

**Decisão de design:** Armazenar atributos estáticos em cache no momento da criação:

```python
# Acesso síncrono rápido (sem chamada CDP)
element_id = element.id
element_class = element.class_name
```

**Tradeoff (Compromisso):** Atributos não refletirão mudanças em tempo de execução. Para propriedades dinâmicas, use assíncrono: `await element.text`.

## Principais Decisões Arquiteturais

| Decisão | Justificativa |
|----------|-----------|
| **Herdar FindElementsMixin** | Permite buscas de filhos, mantém consistência da API |
| **Propriedades híbridas síncronas/assíncronas** | Equilibra performance (síncrono) com dados atualizados (assíncrono) |
| **Alternativas (fallbacks) com JavaScript** | Confiabilidade acima da performance para operações críticas |
| **Detecção de elementos especiais** | `<option>`, `<input type="file">` exigem tratamento único |
| **Verificações de visibilidade pré-clique** | Falhar rápido (fail fast) com erros claros vs. falhas silenciosas |

## Resumo

O domínio WebElement faz a ponte entre o código de automação Python e o DOM do navegador através de:

- **Referências de objetos remotos** via `objectId` do CDP
- **Sistema de propriedades híbrido** equilibrando atributos síncronos e estado assíncrono
- **Pipelines de interação multi-estágio** garantindo confiabilidade
- **Tratamento especializado** para variações de tipos de elementos

**Principais tradeoffs (compromissos):**

| Decisão | Benefício | Custo | Veredito |
|----------|---------|------|---------|
| Herança de Mixin | API limpa | Acoplamento forte | Justificado |
| Atributos em cache | Acesso síncrono rápido | Risco de dados obsoletos | Justificado |
| Alternativas (fallbacks) com JavaScript | Confiabilidade | Perda de performance | Justificado |
| Pré-verificações de visibilidade | Erros claros | Chamadas CDP extras | Justificado |

## Leitura Adicional

**Guias práticos:**

- [Localização de Elementos](../features/element-finding.md) - Localizando elementos, seletores
- [Interações Humanizadas](../features.automation/human-interactions.md) - Clicar, digitar, realismo
- [Operações com Arquivos](../features/automation/file-operations.md) - Uploads e downloads de arquivos

**Análises profundas de arquitetura:**

- [FindElements Mixin](./find-elements-mixin.md) - Pipeline de resolução de seletores
- [Domínio da Aba (Tab)](./tab-domain.md) - A Aba como fábrica de elementos
- [Camada de Conexão](./connection-layer.md) - Comunicação WebSocket