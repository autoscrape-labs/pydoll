# Controle de Teclado

A API de Teclado fornece controle completo sobre a entrada de teclado no nível da página, permitindo que você simule digitação realista, execute atalhos e controle sequências complexas de teclas. Diferente dos métodos de teclado em nível de elemento, a API de Teclado opera globalmente na página, dando a você a flexibilidade de interagir com qualquer elemento focado ou acionar ações de teclado em nível de página.

!!! info "Interface de Teclado Centralizada"
    Todas as operações de teclado são acessíveis via `tab.keyboard`, fornecendo uma API limpa e unificada para todas as interações de teclado.

!!! warning "Limitação Importante do CDP: Atalhos de UI do Navegador Não Funcionam"
    **Problema Conhecido**: Eventos injetados via Chrome DevTools Protocol são marcados como "não confiáveis" e **não** acionam ações da UI do navegador ou criam gestos de usuário.
    
    **O que NÃO funciona:**

    - Atalhos do navegador (Ctrl+T, Ctrl+W, Ctrl+N)
    - Atalhos de DevTools (F12, Ctrl+Shift+I)
    - Navegação do navegador (Ctrl+Shift+T para reabrir abas)
    - Qualquer atalho que modifica a UI ou janelas do navegador
    
    **O que funciona perfeitamente:**

    - Atalhos em nível de página (Ctrl+A, Ctrl+C, Ctrl+V, Ctrl+F)
    - Seleção e manipulação de texto
    - Navegação em formulários (Tab, Enter, teclas de seta)
    - Interações com campos de entrada
    - Atalhos personalizados de aplicações (em web apps)
    
    **Razão técnica**: Eventos CDP não criam "gestos de usuário" necessários pela segurança do navegador. Veja [chromium issue #615341](https://bugs.chromium.org/p/chromium/issues/detail?id=615341) e [documentação CDP](https://chromedevtools.github.io/devtools-protocol/tot/Input/#method-dispatchKeyEvent).
    
    Para automação em nível de navegador, use comandos CDP do navegador diretamente (como `tab.close()`, `browser.new_tab()`) ao invés de atalhos de teclado.

## Início Rápido

A API de Teclado fornece três métodos principais:

```python
from pydoll.browser import Chrome
from pydoll.constants import Key

async with Chrome() as browser:
    tab = await browser.start()
    await tab.go_to('https://example.com')
    
    # Pressionar e soltar uma tecla
    await tab.keyboard.press(Key.ENTER)
    
    # Executar uma combinação de atalho
    await tab.keyboard.hotkey(Key.CONTROL, Key.S)  # Ctrl+S
    
    # Controle manual
    await tab.keyboard.down(Key.SHIFT)
    await tab.keyboard.press(Key.ARROWRIGHT)
    await tab.keyboard.up(Key.SHIFT)
```

## Métodos Principais

### Press: Ação Completa de Tecla

O método `press()` executa um ciclo completo de pressionamento de tecla (pressionar → aguardar → soltar):

```python
from pydoll.constants import Key

# Pressionamento básico de tecla
await tab.keyboard.press(Key.ENTER)
await tab.keyboard.press(Key.TAB)
await tab.keyboard.press(Key.ESCAPE)

# Pressionar com modificadores
await tab.keyboard.press(Key.S, modifiers=2)  # Ctrl+S (modificador manual)

# Duração personalizada de manutenção
await tab.keyboard.press(Key.SPACE, interval=0.5)  # Manter por 500ms
```

**Parâmetros:**

- `key`: Tecla a ser pressionada (do enum `Key`)
- `modifiers` (opcional): Flags de modificadores (Alt=1, Ctrl=2, Meta=4, Shift=8)
- `interval` (opcional): Duração para manter a tecla em segundos (padrão: 0.1)

### Down: Pressionar Tecla Sem Soltar

O método `down()` pressiona uma tecla sem soltá-la, útil para manter modificadores ou criar sequências de teclas:

```python
from pydoll.constants import Key

# Manter Shift enquanto pressiona outras teclas
await tab.keyboard.down(Key.SHIFT)
await tab.keyboard.press(Key.ARROWRIGHT)  # Selecionar texto
await tab.keyboard.press(Key.ARROWRIGHT)  # Continuar selecionando
await tab.keyboard.up(Key.SHIFT)

# Pressionar com flags de modificador
await tab.keyboard.down(Key.A, modifiers=2)  # Ctrl+A (selecionar tudo)
```

**Parâmetros:**
- `key`: Tecla a ser pressionada
- `modifiers` (opcional): Flags de modificadores a aplicar

### Up: Soltar uma Tecla

O método `up()` solta uma tecla previamente pressionada:

```python
from pydoll.constants import Key

# Sequência manual de teclas
await tab.keyboard.down(Key.CONTROL)
await tab.keyboard.down(Key.SHIFT)
await tab.keyboard.press(Key.T)  # Ctrl+Shift+T
await tab.keyboard.up(Key.SHIFT)
await tab.keyboard.up(Key.CONTROL)
```

**Parâmetros:**
- `key`: Tecla a ser solta

!!! tip "Quando Usar Cada Método"

    - **`press()`**: Ações de tecla única (Enter, Tab, letras)
    - **`hotkey()`**: Atalhos de teclado (Ctrl+C, Ctrl+Shift+T)
    - **`down()`/`up()`**: Sequências complexas, manter modificadores, temporização personalizada

## Hotkeys: Atalhos de Teclado Simplificados

O método `hotkey()` detecta automaticamente teclas modificadoras e executa atalhos corretamente:

### Hotkeys Básicos

```python
from pydoll.constants import Key

# Atalhos comuns
await tab.keyboard.hotkey(Key.CONTROL, Key.C)  # Copiar
await tab.keyboard.hotkey(Key.CONTROL, Key.V)  # Colar
await tab.keyboard.hotkey(Key.CONTROL, Key.X)  # Recortar
await tab.keyboard.hotkey(Key.CONTROL, Key.Z)  # Desfazer
await tab.keyboard.hotkey(Key.CONTROL, Key.Y)  # Refazer
await tab.keyboard.hotkey(Key.CONTROL, Key.A)  # Selecionar tudo
await tab.keyboard.hotkey(Key.CONTROL, Key.S)  # Salvar

```

### Combinações de Três Teclas

```python
from pydoll.constants import Key

# Atalhos de edição de texto (estes funcionam!)
await tab.keyboard.hotkey(Key.CONTROL, Key.SHIFT, Key.ARROWLEFT)  # Selecionar palavra à esquerda
await tab.keyboard.hotkey(Key.CONTROL, Key.SHIFT, Key.ARROWRIGHT)  # Selecionar palavra à direita
await tab.keyboard.hotkey(Key.CONTROL, Key.SHIFT, Key.HOME)  # Selecionar até o início do documento
await tab.keyboard.hotkey(Key.CONTROL, Key.SHIFT, Key.END)  # Selecionar até o fim do documento

# Atalhos específicos de aplicação (se suportados pelo web app)
await tab.keyboard.hotkey(Key.CONTROL, Key.SHIFT, Key.Z)  # Refazer em muitos apps
await tab.keyboard.hotkey(Key.CONTROL, Key.SHIFT, Key.S)  # Salvar Como (se o app suportar)
```

### Atalhos Específicos de Plataforma

```python
import sys
from pydoll.constants import Key

# Usar Meta (Command) no macOS, Control no Windows/Linux
modifier = Key.META if sys.platform == 'darwin' else Key.CONTROL

await tab.keyboard.hotkey(modifier, Key.C)  # Copiar (consciente da plataforma)
await tab.keyboard.hotkey(modifier, Key.V)  # Colar (consciente da plataforma)
```

### Como Funcionam os Hotkeys

O método `hotkey()` lida inteligentemente com teclas modificadoras:

1. **Detecta modificadores**: Identifica automaticamente Ctrl, Shift, Alt, Meta
2. **Calcula flags**: Combina modificadores usando OR bit a bit (Ctrl=2, Shift=8 → 10)
3. **Aplica corretamente**: Pressiona teclas não-modificadoras com flags de modificador aplicadas
4. **Liberação limpa**: Solta teclas em ordem reversa

```python
from pydoll.constants import Key

# Nos bastidores para hotkey(Key.CONTROL, Key.SHIFT, Key.T):
# 1. Detecta: modifiers=[CONTROL, SHIFT], keys=[T]
# 2. Calcula: modifier_value = 2 | 8 = 10
# 3. Executa: pressiona T com modifiers=10
# 4. Libera: solta T
```

!!! tip "Valores de Modificador"
    Ao usar o parâmetro `modifiers` manualmente:

    - Alt = 1
    - Ctrl = 2
    - Meta/Command = 4
    - Shift = 8
    
    Combine-os: Ctrl+Shift = 2 + 8 = 10

## Teclas Disponíveis

O enum `Key` fornece cobertura abrangente do teclado:

### Teclas de Letras (A-Z)

```python
from pydoll.constants import Key

# Todas as letras A a Z
await tab.keyboard.press(Key.A)
await tab.keyboard.press(Key.Z)
```

### Teclas Numéricas

```python
from pydoll.constants import Key

# Números da linha superior (0-9)
await tab.keyboard.press(Key.DIGIT0)
await tab.keyboard.press(Key.DIGIT9)

# Números do teclado numérico
await tab.keyboard.press(Key.NUMPAD0)
await tab.keyboard.press(Key.NUMPAD9)
```

### Teclas de Função

```python
from pydoll.constants import Key

# F1 até F12
await tab.keyboard.press(Key.F1)
await tab.keyboard.press(Key.F12)
```

### Teclas de Navegação

```python
from pydoll.constants import Key

await tab.keyboard.press(Key.ARROWUP)
await tab.keyboard.press(Key.ARROWDOWN)
await tab.keyboard.press(Key.ARROWLEFT)
await tab.keyboard.press(Key.ARROWRIGHT)
await tab.keyboard.press(Key.HOME)
await tab.keyboard.press(Key.END)
await tab.keyboard.press(Key.PAGEUP)
await tab.keyboard.press(Key.PAGEDOWN)
```

### Teclas Modificadoras

```python
from pydoll.constants import Key

await tab.keyboard.press(Key.CONTROL)
await tab.keyboard.press(Key.SHIFT)
await tab.keyboard.press(Key.ALT)
await tab.keyboard.press(Key.META)  # Command no macOS, tecla Windows no Windows
```

### Teclas Especiais

```python
from pydoll.constants import Key

await tab.keyboard.press(Key.ENTER)
await tab.keyboard.press(Key.TAB)
await tab.keyboard.press(Key.SPACE)
await tab.keyboard.press(Key.BACKSPACE)
await tab.keyboard.press(Key.DELETE)
await tab.keyboard.press(Key.ESCAPE)
await tab.keyboard.press(Key.INSERT)
```

## Exemplos Práticos

### Navegação em Formulários

```python
from pydoll.browser import Chrome
from pydoll.constants import Key

async def fill_form_with_keyboard():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/form')
        
        # Focar no primeiro campo e digitar
        first_field = await tab.find(id='name')
        await first_field.click()
        await first_field.insert_text('João Silva')
        
        # Navegar para o próximo campo com Tab
        await tab.keyboard.press(Key.TAB)
        await tab.keyboard.press(Key.TAB)  # Pular um campo
        
        # Digitar no campo atualmente focado
        second_field = await tab.find(id='email')
        await second_field.insert_text('joao@example.com')
        
        # Enviar com Enter
        await tab.keyboard.press(Key.ENTER)
```

### Seleção e Manipulação de Texto

```python
from pydoll.constants import Key

async def select_and_replace_text():
    # Selecionar todo o texto
    await tab.keyboard.hotkey(Key.CONTROL, Key.A)
    
    # Copiar seleção
    await tab.keyboard.hotkey(Key.CONTROL, Key.C)
    
    # Mover para o fim
    await tab.keyboard.press(Key.END)
    
    # Selecionar palavra por palavra
    await tab.keyboard.down(Key.CONTROL)
    await tab.keyboard.down(Key.SHIFT)
    await tab.keyboard.press(Key.ARROWLEFT)
    await tab.keyboard.press(Key.ARROWLEFT)
    await tab.keyboard.up(Key.SHIFT)
    await tab.keyboard.up(Key.CONTROL)
    
    # Deletar seleção
    await tab.keyboard.press(Key.DELETE)
```

### Navegação em Dropdown e Select

```python
from pydoll.constants import Key

async def navigate_dropdown():
    # Abrir dropdown
    select = await tab.find(tag_name='select')
    await select.click()
    
    # Navegar opções com teclas de seta
    await tab.keyboard.press(Key.ARROWDOWN)
    await tab.keyboard.press(Key.ARROWDOWN)
    
    # Selecionar com Enter
    await tab.keyboard.press(Key.ENTER)
    
    # Ou cancelar com Escape
    await tab.keyboard.press(Key.ESCAPE)
```

### Sequências Complexas de Teclas

```python
from pydoll.constants import Key
import asyncio

async def complex_editing():
    # Selecionar linha
    await tab.keyboard.press(Key.HOME)  # Ir para o início
    await tab.keyboard.down(Key.SHIFT)
    await tab.keyboard.press(Key.END)  # Selecionar até o fim
    await tab.keyboard.up(Key.SHIFT)
    
    # Recortar
    await tab.keyboard.hotkey(Key.CONTROL, Key.X)
    
    # Mover para baixo e colar
    await tab.keyboard.press(Key.ARROWDOWN)
    await tab.keyboard.hotkey(Key.CONTROL, Key.V)
    
    # Desfazer se necessário
    await tab.keyboard.hotkey(Key.CONTROL, Key.Z)
```

## Melhores Práticas

### 1. Adicione Atrasos para Confiabilidade

```python
from pydoll.constants import Key
import asyncio

# Bom: Aguardar atualização da UI
await tab.keyboard.hotkey(Key.CONTROL, Key.F)  # Abrir busca
await asyncio.sleep(0.2)  # Aguardar diálogo
await tab.keyboard.press(Key.ESCAPE)  # Fechá-lo

# Ruim: Sem atraso, pode não funcionar
await tab.keyboard.hotkey(Key.CONTROL, Key.F)
await tab.keyboard.press(Key.ESCAPE)  # Pode ser rápido demais
```

### 2. Focar Elementos Antes de Digitar

```python
from pydoll.constants import Key

# Bom: Garantir que o elemento está focado
input_field = await tab.find(id='search')
await input_field.click()  # Focá-lo
await input_field.insert_text('consulta')

# Ruim: Entrada de teclado vai para elemento errado
await tab.keyboard.press(Key.A)  # Para onde isso vai?
```

### 3. Use Atalhos Conscientes da Plataforma

```python
import sys
from pydoll.constants import Key

# Bom: Consciente da plataforma
cmd_key = Key.META if sys.platform == 'darwin' else Key.CONTROL
await tab.keyboard.hotkey(cmd_key, Key.C)

# Ruim: Hardcoded (não funcionará no macOS)
await tab.keyboard.hotkey(Key.CONTROL, Key.C)
```

### 4. Limpe Sequências Longas

```python
from pydoll.constants import Key

# Bom: Garantir que modificadores sejam liberados
try:
    await tab.keyboard.down(Key.SHIFT)
    await tab.keyboard.press(Key.ARROWRIGHT)
    # ... mais operações
finally:
    await tab.keyboard.up(Key.SHIFT)  # Sempre liberar

# Ruim: Modificador fica pressionado em erro
await tab.keyboard.down(Key.SHIFT)
await tab.keyboard.press(Key.ARROWRIGHT)
# Erro aqui deixa Shift pressionado!
```

## Tabelas de Referência de Teclas

### Atalhos Comuns em Nível de Página (Estes Funcionam!)

| Ação | Windows/Linux | macOS | Notas |
|------|--------------|-------|-------|
| Copiar | Ctrl+C | Cmd+C | Funciona |
| Colar | Ctrl+V | Cmd+V | Funciona |
| Recortar | Ctrl+X | Cmd+X | Funciona |
| Desfazer | Ctrl+Z | Cmd+Z | Funciona |
| Refazer | Ctrl+Y | Cmd+Y | Funciona |
| Selecionar Tudo | Ctrl+A | Cmd+A | Funciona |
| Localizar | Ctrl+F | Cmd+F | Apenas se o web app implementar |
| Salvar | Ctrl+S | Cmd+S | Apenas se o web app implementar |
| Atualizar | F5 ou Ctrl+R | Cmd+R | Use `await tab.refresh()` |

### Atalhos do Navegador (Estes NÃO Funcionam via CDP)

| Ação | Atalho | Use Ao Invés |
|------|--------|--------------|
| Nova Aba | Ctrl+T | `await browser.new_tab()` |
| Fechar Aba | Ctrl+W | `await tab.close()` |
| Reabrir Aba | Ctrl+Shift+T | Rastreie abas manualmente |
| DevTools | F12, Ctrl+Shift+I | Já disponível via CDP! |
| Barra de Endereço | Ctrl+L | `await tab.go_to(url)` |

### Todas as Teclas Disponíveis

| Categoria | Teclas |
|-----------|--------|
| **Letras** | `Key.A` até `Key.Z` (26 teclas) |
| **Números** | `Key.DIGIT0` até `Key.DIGIT9` (10 teclas) |
| **Teclado Numérico** | `Key.NUMPAD0` até `Key.NUMPAD9`, `NUMPADMULTIPLY`, `NUMPADADD`, `NUMPADSUBTRACT`, `NUMPADDECIMAL`, `NUMPADDIVIDE` |
| **Função** | `Key.F1` até `Key.F12` (12 teclas) |
| **Navegação** | `ARROWUP`, `ARROWDOWN`, `ARROWLEFT`, `ARROWRIGHT`, `HOME`, `END`, `PAGEUP`, `PAGEDOWN` |
| **Modificadores** | `CONTROL`, `SHIFT`, `ALT`, `META` |
| **Especiais** | `ENTER`, `TAB`, `SPACE`, `BACKSPACE`, `DELETE`, `ESCAPE`, `INSERT` |
| **Bloqueios** | `CAPSLOCK`, `NUMLOCK`, `SCROLLLOCK` |
| **Símbolos** | `SEMICOLON`, `EQUALSIGN`, `COMMA`, `MINUS`, `PERIOD`, `SLASH`, `GRAVEACCENT`, `BRACKETLEFT`, `BACKSLASH`, `BRACKETRIGHT`, `QUOTE` |

### Valores de Flag de Modificador

| Modificador | Valor | Binário | Uso |
|-------------|-------|---------|-----|
| Alt | 1 | 0001 | `modifiers=1` |
| Ctrl | 2 | 0010 | `modifiers=2` |
| Meta | 4 | 0100 | `modifiers=4` |
| Shift | 8 | 1000 | `modifiers=8` |
| Ctrl+Shift | 10 | 1010 | `modifiers=10` |
| Ctrl+Alt | 3 | 0011 | `modifiers=3` |
| Ctrl+Shift+Alt | 11 | 1011 | `modifiers=11` |

## Migração dos Métodos WebElement

Os métodos de teclado anteriores em `WebElement` estão depreciados. Veja como migrar:

### Antigo vs Novo

```python
from pydoll.constants import Key

# Antigo (depreciado)
element = await tab.find(id='input')
await element.key_down(Key.A, modifiers=2)
await element.key_up(Key.A)
await element.press_keyboard_key(Key.ENTER)

# Novo (recomendado)
await tab.keyboard.down(Key.A, modifiers=2)
await tab.keyboard.up(Key.A)
await tab.keyboard.press(Key.ENTER)
```

!!! warning "Aviso de Depreciação"
    Os seguintes métodos de `WebElement` estão depreciados:

    - `key_down()` → Use `tab.keyboard.down()`
    - `key_up()` → Use `tab.keyboard.up()`
    - `press_keyboard_key()` → Use `tab.keyboard.press()`
    
    Esses métodos ainda funcionam para compatibilidade retroativa, mas mostrarão avisos de depreciação.

### Por Que Migrar?

- **Centralizado**: Todas as operações de teclado em um só lugar
- **API mais limpa**: Interface consistente para todas as ações de teclado
- **Mais poderoso**: Suporte a hotkey, detecção inteligente de modificadores
- **Melhor tipagem**: Suporte completo a autocompletar da IDE

## Saiba Mais

Para capacidades adicionais de automação:

- **[Interações Humanas](human-interactions.md)**: Cliques, rolagem e movimento de mouse realistas
- **[Manipulação de Formulários](form-handling.md)**: Fluxos completos de automação de formulários
- **[Operações com Arquivos](file-operations.md)**: Automação de upload de arquivos

A API de Teclado elimina a complexidade da automação de teclado, fornecendo métodos limpos e confiáveis para tudo, desde pressionamentos simples de teclas até atalhos complexos e sequências.
