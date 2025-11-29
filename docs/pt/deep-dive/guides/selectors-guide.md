# Seletores CSS vs XPath: Um Guia Completo

Ao usar o método `query()`, você tem duas poderosas linguagens de seletores à sua disposição: Seletores CSS e XPath. Entender quando e como usar cada um é crucial para a localização eficaz de elementos.

## Diferenças Fundamentais

| Aspecto | Seletor CSS | XPath |
|---|---|---|
| **Sintaxe** | Simples, semelhante a CSS | Linguagem de caminho XML |
| **Desempenho** | Mais rápido (suporte nativo do navegador) | Ligeiramente mais lento |
| **Direção** | Atravessa apenas para baixo e lateralmente | Pode atravessar em qualquer direção |
| **Correspondência de Texto** | Limitada (pseudo-seletores) | Funções de texto poderosas |
| **Complexidade** | Melhor para casos simples a moderados | Excelente em relacionamentos complexos |
| **Legibilidade** | Mais intuitivo para desenvolvedores web | Curva de aprendizado mais íngreme |

## Quando Usar Seletores CSS

Seletores CSS são ideais para:

- Seleção simples de elementos por ID, classe ou tag
- Relacionamentos diretos pai-filho
- Correspondência de atributos com padrões simples
- Cenários críticos de desempenho
- Ao atravessar para baixo no DOM

```python
# Exemplos de CSS limpos e performáticos
await tab.query("#login-form")
await tab.query(".submit-button")
await tab.query("div.container > p.intro")
await tab.query("input[type='email'][required]")
await tab.query("ul.menu li:first-child")
```

## Quando Usar XPath

XPath é ideal para:

- Correspondência de texto complexa e buscas parciais de texto
- Atravessar para cima até elementos pais
- Encontrar elementos relativos a irmãos
- Lógica condicional em seletores
- Relacionamentos DOM complexos

```python
# Exemplos poderosos de XPath
await tab.query("//button[contains(text(), 'Submit')]")
await tab.query("//input[@name='email']/parent::div")
await tab.query("//td[text()='John']/following-sibling::td[2]")
await tab.query("//div[contains(@class, 'product') and @data-price > 100]")
```

## Referência de Sintaxe de Seletor CSS

### Seletores Básicos

```python
# Seletor de elemento
await tab.query("div")              # Primeiro elemento <div>
await tab.query("div", find_all=True)  # Todos os elementos <div>
await tab.query("button")           # Primeiro elemento <button>

# Seletor de ID
await tab.query("#username")        # Elemento com id="username"

# Seletor de classe
await tab.query(".submit-btn")      # Primeiro elemento com class="submit-btn"
await tab.query(".submit-btn", find_all=True)  # Todos os elementos com a classe
await tab.query(".btn.primary")     # Primeiro elemento com ambas as classes

# Seletor universal
await tab.query("*", find_all=True) # Todos os elementos
```

### Combinadores

```python
# Combinador descendente (espaço)
await tab.query("div p")            # Primeiro <p> dentro de <div>
await tab.query("div p", find_all=True)  # Todos os <p> dentro de <div> (qualquer profundidade)

# Combinador filho (>)
await tab.query("div > p")          # Primeiro <p> que é filho direto de <div>
await tab.query("div > p", find_all=True)  # Todos os <p> que são filhos diretos

# Combinador irmão adjacente (+)
await tab.query("h1 + p")           # <p> imediatamente após <h1>

# Combinador irmão geral (~)
await tab.query("h1 ~ p")           # Primeiro <p> irmão após <h1>
await tab.query("h1 ~ p", find_all=True)  # Todos os <p> irmãos após <h1>
```

### Seletores de Atributo

```python
# Atributo existe
await tab.query("input[required]")                # Primeiro input com 'required'
await tab.query("input[required]", find_all=True) # Todos os inputs com 'required'

# Atributo igual
await tab.query("input[type='email']")            # Primeiro input de email
await tab.query("input[type='email']", find_all=True)  # Todos os inputs de email

# Atributo contém palavra
await tab.query("div[class~='active']")           # Primeiro div com classe 'active'

# Atributo começa com
await tab.query("a[href^='https://']")            # Primeiro link HTTPS
await tab.query("a[href^='https://']", find_all=True)  # Todos os links HTTPS

# Atributo termina com
await tab.query("img[src$='.png']")               # Primeira imagem PNG
await tab.query("img[src$='.png']", find_all=True)     # Todas as imagens PNG

# Atributo contém substring
await tab.query("a[href*='example']")             # Primeiro link com 'example'
await tab.query("a[href*='example']", find_all=True)   # Todos os links com 'example'

# Correspondência insensível a maiúsculas/minúsculas (case-insensitive)
await tab.query("input[type='text' i]")           # Correspondência case-insensitive
```

### Pseudo-classes

```python
# Pseudo-classes estruturais
await tab.query("li:first-child")                 # Primeiro <li> que é primeiro filho
await tab.query("li:last-child")                  # Primeiro <li> que é último filho
await tab.query("li:nth-child(2)")                # Primeiro <li> que é 2º filho
await tab.query("li:nth-child(odd)", find_all=True)  # Todos os <li> ímpares
await tab.query("li:nth-child(even)", find_all=True)  # Todos os <li> pares
await tab.query("li:nth-child(3n)", find_all=True)    # A cada 3º <li>

# Pseudo-classes baseadas em tipo
await tab.query("p:first-of-type")                # Primeiro <p> entre irmãos
await tab.query("p:last-of-type")                 # Último <p> entre irmãos
await tab.query("p:nth-of-type(2)")               # Segundo <p> entre irmãos

# Pseudo-classes de estado
await tab.query("input:enabled")                  # Primeiro input habilitado
await tab.query("input:enabled", find_all=True)   # Todos os inputs habilitados
await tab.query("input:disabled")                 # Primeiro input desabilitado
await tab.query("input:checked")                  # Primeiro checkbox/radio marcado
await tab.query("input:focus")                    # Input atualmente focado

# Outras pseudo-classes úteis
await tab.query("div:empty")                      # Primeiro elemento vazio
await tab.query("div:empty", find_all=True)       # Todos os elementos vazios
await tab.query("div:not(.exclude)")              # Primeiro div sem a classe
await tab.query("div:not(.exclude)", find_all=True)  # Todos os divs sem a classe
```

## Referência de Sintaxe XPath

### Expressões de Caminho Básicas

```python
# Caminho absoluto (da raiz)
await tab.query("/html/body/div")                 # Primeiro div no caminho exato

# Caminho relativo (de qualquer lugar)
await tab.query("//div")                          # Primeiro elemento <div>
await tab.query("//div", find_all=True)           # Todos os elementos <div>
await tab.query("//div/p")                        # Primeiro <p> dentro de qualquer <div>
await tab.query("//div/p", find_all=True)         # Todos os <p> dentro de qualquer <div>

# Nó atual
await tab.query("./div")                          # Primeiro <div> relativo ao atual

# Nó pai
await tab.query("..")                             # Pai do nó atual
```

### Seleção de Atributo

```python
# Correspondência básica de atributo
await tab.query("//input[@type='email']")         # Primeiro input de email
await tab.query("//input[@type='email']", find_all=True)  # Todos os inputs de email
await tab.query("//div[@id='content']")           # Div com id='content'

# Múltiplos atributos
await tab.query("//input[@type='text' and @required]")  # Primeira correspondência
await tab.query("//input[@type='text' and @required]", find_all=True)  # Todas as correspondências
await tab.query("//div[@class='card' or @class='panel']")  # Primeiro card ou panel

# Atributo existe
await tab.query("//button[@disabled]")            # Primeiro botão desabilitado
await tab.query("//button[@disabled]", find_all=True)  # Todos os botões desabilitados
```

## Eixos (Axes) XPath (Navegação Direcional)

O poder real do XPath vem de sua habilidade de navegar em qualquer direção através da árvore DOM.

### Tabela de Referência de Eixos

| Eixo | Direção | Descrição | Exemplo |
|---|---|---|---|
| `child::` | Para baixo | Apenas filhos diretos | `//div/child::p` |
| `descendant::` | Para baixo | Todos os descendentes (qualquer profundidade) | `//div/descendant::a` |
| `parent::` | Para cima | Pai imediato | `//input/parent::div` |
| `ancestor::` | Para cima | Todos os ancestrais (qualquer profundidade) | `//span/ancestor::div` |
| `following-sibling::` | Lateralmente | Irmãos após o atual | `//h1/following-sibling::p` |
| `preceding-sibling::` | Lateralmente | Irmãos antes do atual | `//p/preceding-sibling::h1` |
| `following::` | Para frente | Todos os nós após o atual | `//h1/following::*` |
| `preceding::` | Para trás | Todos os nós antes do atual | `//h1/preceding::*` |
| `ancestor-or-self::` | Para cima | Ancestrais + atual | `//div/ancestor-or-self::*` |
| `descendant-or-self::` | Para baixo | Descendentes + atual | `//div/descendant-or-self::*` |
| `self::` | Atual | Apenas o nó atual | `//div/self::div` |
| `attribute::` | Atributo | Atributos do atual | `//div/attribute::class` |

!!! info "Sintaxe Abreviada"
    - `//div` é abreviação de `//descendant-or-self::div`
    - `//div/p` é abreviação de `//div/child::p`
    - `@id` é abreviação de `attribute::id`
    - `..` é abreviação de `parent::node()`

### Exemplos Práticos de Eixos

```python
# Navegar para o pai
await tab.query("//input[@name='email']/parent::div")
await tab.query("//span[@class='error']/..")       # Abreviação

# Encontrar ancestral
await tab.query("//input/ancestor::form")          # Primeiro <form> ancestral
await tab.query("//button/ancestor::div[@class='modal']")

# Navegação entre irmãos
await tab.query("//label[text()='Email:']/following-sibling::input")
await tab.query("//h2/following-sibling::p[1]")    # Primeiro <p> após <h2>
await tab.query("//h2/following-sibling::p", find_all=True)  # Todos os <p> após <h2>
await tab.query("//button/preceding-sibling::input[last()]")

# Relacionamentos complexos
await tab.query("//tr/td[1]/following-sibling::td[2]")  # 3ª célula na primeira linha
await tab.query("//tr/td[1]/following-sibling::td[2]", find_all=True)  # 3ª célula em todas as linhas
```

## Funções XPath

### Funções de Texto

```python
# Correspondência exata de texto
await tab.query("//button[text()='Submit']")

# Contém texto
await tab.query("//p[contains(text(), 'welcome')]")

# Começa com
await tab.query("//a[starts-with(@href, 'https://')]")

# Normalização de texto (remove espaços em branco extras)
await tab.query("//button[normalize-space(text())='Submit']")

# Comprimento da string
await tab.query("//input[string-length(@value) > 5]")

# Concatenação
await tab.query("//div[concat(@data-first, @data-last)='JohnDoe']")
```

### Funções Numéricas

```python
# Correspondência de posição
await tab.query("//li[position()=1]")              # Primeiro <li>
await tab.query("//li[position() > 3]", find_all=True)  # Todos os <li> após o 3º
await tab.query("//li[last()]")                    # Último <li>
await tab.query("//li[last()-1]")                  # Penúltimo

# Contagem
await tab.query("//ul[count(li) > 5]")             # Primeiro <ul> com mais de 5 itens
await tab.query("//ul[count(li) > 5]", find_all=True)  # Todos os <ul> com > 5 itens

# Operações numéricas
await tab.query("//div[@data-price > 100]")        # Primeiro div com preço > 100
await tab.query("//div[@data-price > 100]", find_all=True)  # Todos os divs
await tab.query("//div[number(@data-stock) = 0]")  # Primeiro com estoque = 0
```

### Funções Booleanas

```python
# Lógica booleana
await tab.query("//div[@visible='true' and @enabled='true']")  # Primeira correspondência
await tab.query("//input[@type='text' or @type='email']")  # Primeiro text ou email
await tab.query("//input[@type='text' or @type='email']", find_all=True)  # Todos
await tab.query("//button[not(@disabled)]")        # Primeiro botão habilitado
await tab.query("//button[not(@disabled)]", find_all=True)  # Todos os botões habilitados

# Verificações de existência
await tab.query("//div[child::p]")                 # Primeiro div com filhos <p>
await tab.query("//div[child::p]", find_all=True)  # Todos os divs com filhos <p>
await tab.query("//div[not(child::*)]")            # Primeiro div vazio
await tab.query("//div[not(child::*)]", find_all=True)  # Todos os divs vazios
```

## Predicados XPath

Predicados filtram conjuntos de nós usando condições entre colchetes `[]`.

```python
# Predicados de posição
await tab.query("(//div)[1]")                      # Primeiro <div> no documento
await tab.query("(//div)[last()]")                 # Último <div> no documento
await tab.query("//ul/li[3]")                      # Primeiro 3º <li> em um <ul>
await tab.query("//ul/li[3]", find_all=True)       # Todos os 3º <li> em cada <ul>

# Múltiplos predicados (lógica E)
await tab.query("//input[@type='text'][@required]")  # Primeira correspondência
await tab.query("//div[@class='product'][position() < 4]", find_all=True)  # Os 3 primeiros

# Predicados de atributo
await tab.query("//div[@data-id='123']")
await tab.query("//a[contains(@class, 'button')]")  # Primeiro link correspondente
await tab.query("//input[starts-with(@name, 'user')]")  # Primeiro input correspondente
```

## Exemplos do Mundo Real: Localização Complexa de Elementos

Vamos trabalhar com uma estrutura HTML realista para demonstrar seletores avançados.

### Estrutura HTML de Exemplo

```html
<div class="dashboard">
    <header>
        <h1>User Dashboard</h1>
        <nav class="menu">
            <a href="/home" class="active">Home</a>
            <a href="/profile">Profile</a>
            <a href="/settings">Settings</a>
        </nav>
    </header>
    
    <main>
        <section class="products">
            <h2>Available Products</h2>
            <table id="products-table">
                <thead>
                    <tr>
                        <th>Product Name</th>
                        <th>Price</th>
                        <th>Stock</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <tr data-product-id="101">
                        <td>Laptop</td>
                        <td class="price">$999</td>
                        <td class="stock">15</td>
                        <td>
                            <button class="btn-edit">Edit</button>
                            <button class="btn-delete">Delete</button>
                        </td>
                    </tr>
                    <tr data-product-id="102">
                        <td>Mouse</td>
                        <td class="price">$25</td>
                        <td class="stock">0</td>
                        <td>
                            <button class="btn-edit">Edit</button>
                            <button class="btn-delete" disabled>Delete</button>
                        </td>
                    </tr>
                    <tr data-product-id="103">
                        <td>Keyboard</td>
                        <td class="price">$75</td>
                        <td class="stock">8</td>
                        <td>
                            <button class="btn-edit">Edit</button>
                            <button class="btn-delete">Delete</button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </section>
        
        <section class="user-form">
            <h2>User Information</h2>
            <form id="user-form">
                <div class="form-group">
                    <label for="username">Username:</label>
                    <input type="text" id="username" name="username" required>
                    <span class="error-message" style="display:none;">Invalid username</span>
                </div>
                <div class="form-group">
                    <label for="email">Email:</label>
                    <input type="email" id="email" name="email" required>
                    <span class="error-message" style="display:none;">Invalid email</span>
                </div>
                <div class="form-group">
                    <input type="checkbox" id="newsletter" name="newsletter">
                    <label for="newsletter">Subscribe to newsletter</label>
                </div>
                <button type="submit" class="btn-primary">Save Changes</button>
                <button type="button" class="btn-secondary">Cancel</button>
            </form>
        </section>
    </main>
</div>
```

### Desafio 1: Encontrar Link de Navegação Ativo

**Objetivo**: Encontrar o link de navegação atualmente ativo.

```python
# Seletor CSS
active_link = await tab.query("nav.menu a.active")

# XPath
active_link = await tab.query("//nav[@class='menu']//a[@class='active']")

# Obter seu texto
text = await active_link.text
print(text)  # "Home"
```

### Desafio 2: Encontrar Botão de Edição para Produto Específico

**Objetivo**: Encontrar o botão "Edit" para o produto "Mouse" (sem saber sua posição na linha).

```python
# XPath (recomendado para este caso)
edit_button = await tab.query(
    "//tr[td[text()='Mouse']]//button[contains(@class, 'btn-edit')]"
)

# Alternativa: Usando following-sibling
edit_button = await tab.query(
    "//td[text()='Mouse']/following-sibling::td//button[@class='btn-edit']"
)
```

!!! tip "Por que XPath Aqui?"
    Seletores CSS não podem atravessar para cima para encontrar a linha e depois para baixo até o botão. A habilidade do XPath de se mover livremente pelo DOM torna isso trivial.

### Desafio 3: Encontrar Todos os Produtos com Preço Acima de $50

**Objetivo**: Obter todas as linhas da tabela onde o preço é maior que $50.

```python
# XPath com comparação numérica
expensive_products = await tab.query(
    "//tr[number(translate(td[@class='price'], '$,', '')) > 50]",
    find_all=True
)

# Versão mais legível: usando contains para casos mais simples
# Isso encontra produtos com preço contendo valores específicos
products = await tab.query("//tr[contains(td[@class='price'], '$75')]", find_all=True)
```

!!! note "Conversão de Texto para Número"
    A função `translate()` remove os caracteres `$` e `,`, então `number()` converte para numérico para comparação.

### Desafio 4: Encontrar Todos os Produtos Fora de Estoque

**Objetivo**: Encontrar todos os produtos onde o estoque é 0.

```python
# XPath
out_of_stock = await tab.query(
    "//tr[td[@class='stock' and text()='0']]",
    find_all=True
)

# Alternativa: Encontrar todas as linhas e checar o estoque
rows = await tab.query("//tbody/tr[td[@class='stock']/text()='0']", find_all=True)
```

### Desafio 5: Encontrar Campo de Input pelo Seu Label

**Objetivo**: Encontrar o input de email localizando seu label primeiro.

```python
# XPath usando atributo 'for' do label
email_input = await tab.query("//label[text()='Email:']/following-sibling::input")

# Alternativa: Usando o atributo for
email_input = await tab.query("//input[@id=(//label[text()='Email:']/@for)]")

# Mais genérico: Encontrar pelo texto do label
username_input = await tab.query(
    "//label[contains(text(), 'Username')]/following-sibling::input"
)
```

### Desafio 6: Encontrar Mensagem de Erro Próxima ao Campo de Email

**Objetivo**: Obter o span de mensagem de erro que aparece ao lado do input de email.

```python
# XPath - encontrar irmão de erro do input de email
error_span = await tab.query(
    "//input[@id='email']/following-sibling::span[@class='error-message']"
)

# Alternativa: Navegar a partir da div pai
error_span = await tab.query(
    "//input[@id='email']/parent::div//span[@class='error-message']"
)

# Checar visibilidade
is_visible = await error_span.is_visible()
```

### Desafio 7: Encontrar Botão de Envio (Não o de Cancelar)

**Objetivo**: Encontrar o botão de envio, excluindo o botão de cancelar.

```python
# Seletor CSS (simples)
submit_button = await tab.query("button[type='submit']")
submit_button = await tab.query("button.btn-primary")

# XPath com texto
submit_button = await tab.query("//button[text()='Save Changes']")

# XPath excluindo outros
submit_button = await tab.query(
    "//button[@type='submit' and not(@class='btn-secondary')]"
)
```

### Desafio 8: Encontrar Todos os Campos Obrigatórios do Formulário

**Objetivo**: Obter todos os campos de input obrigatórios no formulário.

```python
# Seletor CSS (limpo)
required_fields = await tab.query(
    "#user-form input[required]",
    find_all=True
)

# XPath
required_fields = await tab.query(
    "//form[@id='user-form']//input[@required]",
    find_all=True
)

# Verificar
for field in required_fields:
    field_name = await field.get_attribute("name")
    print(f"Obrigatório: {field_name}")
```

### Desafio 9: Encontrar Primeiro Botão de Deletar Não Desabilitado

**Objetivo**: Encontrar o primeiro botão de deletar que não está desabilitado.

```python
# Seletor CSS
first_enabled_delete = await tab.query("button.btn-delete:not([disabled])")

# XPath
first_enabled_delete = await tab.query(
    "//button[contains(@class, 'btn-delete') and not(@disabled)]"
)

# Obter todos os botões de deletar habilitados
all_enabled = await tab.query(
    "//button[@class='btn-delete' and not(@disabled)]",
    find_all=True
)
```

### Desafio 10: Encontrar Linha da Tabela por Múltiplas Condições

**Objetivo**: Encontrar produtos com estoque > 0 E preço < $100.

```python
# XPath com lógica complexa
available_affordable = await tab.query(
    """
    //tr[
        number(td[@class='stock']) > 0 
        and 
        number(translate(td[@class='price'], '$', '')) < 100
    ]
    """,
    find_all=True
)

# Para cada produto correspondente
for row in available_affordable:
    cells = await row.query("td", find_all=True)
    product_name = await cells[0].text
    print(f"Disponível: {product_name}")
```

### Desafio 11: Navegar em Relacionamentos Complexos

**Objetivo**: A partir de um botão de deletar, obter o nome do produto na mesma linha.

```python
# Começar com um botão de deletar
delete_button = await tab.query("//tr[@data-product-id='101']//button[@class='btn-delete']")

# Navegar para a linha pai, depois para a primeira célula
product_name_cell = await delete_button.query("./ancestor::tr/td[1]")
product_name = await product_name_cell.text
print(product_name)  # "Laptop"

# Alternativa: Obter a linha inteira primeiro
row = await delete_button.query("./ancestor::tr")
product_id = await row.get_attribute("data-product-id")
print(product_id)  # "101"
```

### Desafio 12: Encontrar Checkbox e Seu Label Juntos

**Objetivo**: Encontrar o checkbox da newsletter e verificar seu label.

```python
# Encontrar checkbox
checkbox = await tab.query("#newsletter")

# Obter label associado usando atributo 'for'
label = await tab.query("//label[@for='newsletter']")
label_text = await label.text
print(label_text)  # "Subscribe to newsletter"

# Alternativa: Navegar do checkbox para o label
label = await checkbox.query("//following::label[@for='newsletter']")

# Checar se está marcado
is_checked = await checkbox.is_checked()
```

## Padrão Avançado: Construção Dinâmica de Seletor

Ao lidar com conteúdo dinâmico, você pode precisar construir seletores programaticamente:

```python
async def find_product_by_name(tab, product_name: str):
    """Encontra uma linha de produto pelo nome dinamicamente."""
    # Escapar aspas no nome do produto para prevenir injeção de XPath
    safe_name = product_name.replace("'", "\\'")
    
    xpath = f"//tr[td[text()='{safe_name}']]"
    return await tab.query(xpath)

async def find_table_cell(tab, row_text: str, column_index: int):
    """Encontra uma célula específica pelo conteúdo da linha e posição da coluna."""
    xpath = f"//tr[td[contains(text(), '{row_text}')]]/td[{column_index}]"
    return await tab.query(xpath)

# Uso
product_row = await find_product_by_name(tab, "Laptop")
price_cell = await find_table_cell(tab, "Laptop", 2)
price = await price_cell.text
print(price)  # "$999"
```

## Comparação de Desempenho

```python
import asyncio
import time

async def benchmark_selectors(tab):
    """Comparar desempenho de CSS vs XPath."""
    
    # Aquecimento
    await tab.query("#products-table")
    
    # Benchmark CSS
    start = time.time()
    for _ in range(100):
        await tab.query("#products-table tbody tr", find_all=True)
    css_time = time.time() - start
    
    # Benchmark XPath
    start = time.time()
    for _ in range(100):
        await tab.query("//table[@id='products-table']//tbody//tr", find_all=True)
    xpath_time = time.time() - start
    
    print(f"CSS: {css_time:.3f}s")
    print(f"XPath: {xpath_time:.3f}s")
    print(f"CSS é {xpath_time/css_time:.2f}x mais rápido")

# Resultados típicos: CSS é 1.2-1.5x mais rápido para seletores simples
```

!!! warning "Desempenho vs Legibilidade"
    Embora seletores CSS sejam geralmente mais rápidos, a diferença é usualmente negligenciável (milissegundos) para consultas individuais. Escolha o seletor que torna seu código mais legível e sustentável, especialmente para relacionamentos complexos onde o XPath se destaca.

## Melhores Práticas de Seletores

### 1. Prefira Seletores Estáveis

```python
# Bom: Usando atributos semânticos
await tab.query("#user-email")
await tab.query("[data-testid='submit-button']")
await tab.query("input[name='username']")

# Evite: Seletores frágeis baseados na estrutura
await tab.query("div > div > div:nth-child(3) > input")
await tab.query("body > div:nth-child(2) > form > div:first-child")
```

### 2. Use o Seletor Mais Simples que Funciona

```python
# Bom: Simples e eficiente
await tab.query("#login-form")
await tab.query(".submit-button")

# Evite: Complicado demais quando desnecessário
await tab.query("//div[@id='content']/descendant::form[@id='login-form']")
```

### 3. Combine find() e query() Apropriadamente

```python
# Use find() para correspondência simples de atributos
username = await tab.find(id="username")
submit = await tab.find(tag_name="button", type="submit")

# Use query() para padrões complexos
active_link = await tab.query("nav.menu a.active")
error_msg = await tab.query("//input[@name='email']/following-sibling::span[@class='error']")
```

### 4. Adicione Comentários para Seletores Complexos

```python
# Encontrar o botão "Edit" na linha que contém o produto "Laptop"
# XPath: Navega para a linha com texto "Laptop", depois encontra o botão de edição
edit_button = await tab.query(
    "//tr[td[text()='Laptop']]//button[@class='btn-edit']"
)
```

## Conclusão

Ao entender tanto seletores CSS quanto XPath, juntamente com suas respectivas forças e casos de uso, você pode criar uma automação de navegador robusta e sustentável que lida com as complexidades das aplicações web modernas. Lembre-se:

- **Use seletores CSS** para seleções simples e críticas de desempenho
- **Use XPath** para relacionamentos complexos, correspondência de texto e navegação ascendente
- **Escolha estabilidade** em vez de brevidade ao escrever seletores
- **Comente consultas complexas** para manter a legibilidade do código