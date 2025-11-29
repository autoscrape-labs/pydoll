# Operações com Arquivos

Uploads de arquivos são um dos aspectos mais desafiadores da automação de navegadores. Ferramentas tradicionais frequentemente têm dificuldades com as caixas de diálogo de arquivo do nível do sistema operacional, exigindo soluções complexas ou bibliotecas externas. O Pydoll oferece duas abordagens diretas para lidar com uploads de arquivos, cada uma adequada para cenários diferentes.

## Métodos de Upload

O Pydoll suporta dois métodos principais para uploads de arquivos:

1.  **Entrada direta de arquivo** (`set_input_files()`): Rápido e direto, funciona com elementos `<input type="file">`
2.  **Gerenciador de contexto de seletor de arquivo** (`expect_file_chooser()`): Intercepta a caixa de diálogo de arquivo, funciona com qualquer gatilho de upload

## Entrada Direta de Arquivo

A abordagem mais simples é usar `set_input_files()` diretamente em elementos de entrada de arquivo. Este método é rápido, confiável e ignora totalmente a caixa de diálogo de arquivo do sistema operacional.

### Uso Básico

```python
import asyncio
from pathlib import Path
from pydoll.browser.chromium import Chrome

async def direct_file_upload():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/upload')
        
        # Encontrar o elemento de entrada de arquivo
        file_input = await tab.find(tag_name='input', type='file')
        
        # Definir o arquivo diretamente
        file_path = Path('path/to/document.pdf')
        await file_input.set_input_files(file_path)
        
        # Enviar o formulário
        submit_button = await tab.find(id='submit-button')
        await submit_button.click()
        
        print("Arquivo enviado com sucesso!")

asyncio.run(direct_file_upload())
```

!!! tip "Path vs String"
    Embora objetos `Path` do `pathlib` sejam recomendados como melhor prática para melhor manipulação de caminhos e compatibilidade entre plataformas, você também pode usar strings simples, se preferir:
    ```python
    await file_input.set_input_files('path/to/document.pdf')  # Também funciona!
    ```

### Múltiplos Arquivos

Para entradas que aceitam múltiplos arquivos (`<input type="file" multiple>`), passe uma lista de caminhos de arquivo:

```python
import asyncio
from pathlib import Path
from pydoll.browser.chromium import Chrome

async def upload_multiple_files():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/multi-upload')
        
        file_input = await tab.find(tag_name='input', type='file')
        
        # Fazer upload de múltiplos arquivos de uma vez
        files = [
            Path('documents/report.pdf'),
            Path('images/screenshot.png'),
            Path('data/results.csv')
        ]
        await file_input.set_input_files(files)
        
        # Processar normalmente
        upload_btn = await tab.find(id='upload-btn')
        await upload_btn.click()

asyncio.run(upload_multiple_files())
```

### Resolução Dinâmica de Caminho

Objetos `Path` facilitam a construção dinâmica de caminhos e lidam com a compatibilidade entre plataformas:

```python
import asyncio
from pathlib import Path
from pydoll.browser.chromium import Chrome

async def upload_with_dynamic_paths():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/upload')
        
        file_input = await tab.find(tag_name='input', type='file')
        
        # Construir caminhos dinamicamente
        project_dir = Path(__file__).parent
        file_path = project_dir / 'uploads' / 'data.json'

        await file_input.set_input_files(file_path)
        # Ou usar o diretório home
        user_file = Path.home() / 'Documents' / 'report.pdf'
        await file_input.set_input_files(user_file)

asyncio.run(upload_with_dynamic_paths())
```

!!! tip "Quando Usar a Entrada Direta de Arquivo"
    Use `set_input_files()` quando:
    
    - O input de arquivo está diretamente acessível no DOM
    - Você quer velocidade e simplicidade máximas
    - O upload não dispara uma caixa de diálogo de seletor de arquivo
    - Você está trabalhando com elementos `<input type="file">` padrão

## Gerenciador de Contexto de Seletor de Arquivo

Alguns sites escondem o input de arquivo e usam botões personalizados ou áreas de arrastar e soltar que disparam a caixa de diálogo de seletor de arquivo do sistema operacional. Para esses casos, use o gerenciador de contexto `expect_file_chooser()`.

### Como Funciona

O gerenciador de contexto `expect_file_chooser()`:

1.  Habilita a interceptação do seletor de arquivo
2.  Espera a caixa de diálogo do seletor de arquivo abrir
3.  Define automaticamente os arquivos quando a caixa de diálogo aparece
4.  Limpa os recursos após a conclusão da operação

### Uso Básico

```python
import asyncio
from pathlib import Path
from pydoll.browser.chromium import Chrome

async def file_chooser_upload():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/custom-upload')
        
        # Preparar o caminho do arquivo
        file_path = Path.cwd() / 'document.pdf'
        
        # Usar gerenciador de contexto para lidar com o seletor de arquivo
        async with tab.expect_file_chooser(files=file_path):
            # Clicar no botão de upload personalizado
            upload_button = await tab.find(class_name='custom-upload-btn')
            await upload_button.click()
            # O arquivo é definido automaticamente quando a caixa de diálogo abre
        
        # Continuar com sua automação
        print("Arquivo selecionado via seletor!")

asyncio.run(file_chooser_upload())
```

### Múltiplos Arquivos com Seletor de Arquivo

```python
import asyncio
from pathlib import Path
from pydoll.browser.chromium import Chrome

async def multiple_files_chooser():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/gallery-upload')
        
        # Preparar múltiplos arquivos
        photos_dir = Path.home() / 'photos'
        files = [
            photos_dir / 'img1.jpg',
            photos_dir / 'img2.jpg',
            photos_dir / 'img3.jpg'
        ]
        
        async with tab.expect_file_chooser(files=files):
            # Disparar upload via botão personalizado
            add_photos_btn = await tab.find(text='Add Photos')
            await add_photos_btn.click()
        
        print(f"{len(files)} arquivos selecionados!")

asyncio.run(multiple_files_chooser())
```

### Seleção Dinâmica de Arquivos

```python
import asyncio
from pathlib import Path
from pydoll.browser.chromium import Chrome

async def dynamic_file_selection():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/batch-upload')
        
        # Encontrar todos os arquivos CSV em um diretório usando Path.glob()
        data_dir = Path('data')
        csv_files = list(data_dir.glob('*.csv'))
        
        async with tab.expect_file_chooser(files=csv_files):
            upload_area = await tab.find(class_name='drop-zone')
            await upload_area.click()
        
        print(f"Selecionados {len(csv_files)} arquivos CSV")

asyncio.run(dynamic_file_selection())
```

!!! tip "Quando Usar o Seletor de Arquivo"
    Use `expect_file_chooser()` quando:
    
    - O input de arquivo está oculto ou não diretamente acessível
    - Botões personalizados disparam a caixa de diálogo do seletor de arquivo
    - Trabalhando com áreas de upload de arrastar e soltar
    - O site usa JavaScript para abrir caixas de diálogo de arquivo

## Comparação: Direto vs Seletor de Arquivo

| Característica | `set_input_files()` | `expect_file_chooser()` |
|---|---|---|
| **Velocidade** | ⚡ Instantâneo | 🕐 Espera pela caixa de diálogo |
| **Complexidade** | Simples | Requer gerenciador de contexto |
| **Requisitos** | Input de arquivo visível | Qualquer gatilho de upload |
| **Caso de Uso** | Formulários padrão | UIs de upload personalizadas |
| **Manejo de Eventos** | Não necessário | Usa eventos de página |

## Exemplo Completo

Aqui está um exemplo abrangente combinando ambas as abordagens:

```python
import asyncio
from pathlib import Path
from pydoll.browser.chromium import Chrome

async def comprehensive_upload_example():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/upload-form')
        
        # Cenário 1: Entrada direta para foto de perfil (arquivo único)
        avatar_input = await tab.find(id='avatar-upload')
        avatar_path = Path.home() / 'Pictures' / 'profile.jpg'
        await avatar_input.set_input_files(avatar_path)
        
        # Esperar um pouco para a pré-visualização carregar
        await asyncio.sleep(1)
        
        # Cenário 2: Seletor de arquivo para upload de documento
        document_path = Path.cwd() / 'documents' / 'resume.pdf'
        async with tab.expect_file_chooser(files=document_path):
            # Botão estilizado personalizado que dispara o seletor de arquivo
            upload_btn = await tab.find(class_name='btn-upload-document')
            await upload_btn.click()
        
        # Esperar pela confirmação do upload
        await asyncio.sleep(2)
        
        # Cenário 3: Múltiplos arquivos via seletor de arquivo
        certs_dir = Path('certs')
        certificates = [
            certs_dir / 'certificate1.pdf',
            certs_dir / 'certificate2.pdf',
            certs_dir / 'certificate3.pdf'
        ]
        async with tab.expect_file_chooser(files=certificates):
            add_certs_btn = await tab.find(text='Add Certificates')
            await add_certs_btn.click()
        
        # Enviar o formulário completo
        submit_button = await tab.find(type='submit')
        await submit_button.click()
        
        # Esperar pela mensagem de sucesso
        success_msg = await tab.find(class_name='success-message', timeout=10)
        message_text = await success_msg.text
        print(f"Resultado do upload: {message_text}")

asyncio.run(comprehensive_upload_example())
```

!!! info "Resumo dos Métodos"
    Este exemplo demonstra a flexibilidade do sistema de upload de arquivos do Pydoll:
    
    - **Arquivos únicos**: Passe `Path` ou `str` diretamente (não precisa de lista)
    - **Múltiplos arquivos**: Passe uma lista de objetos `Path` ou `str`
    - **Entrada direta**: Rápido para elementos `<input>` visíveis
    - **Seletor de arquivo**: Funciona com botões de upload personalizados e inputs ocultos

## Aprenda Mais

Para um entendimento mais profundo dos mecanismos de upload de arquivos:

- **[Sistema de Eventos](../advanced/event-system.md)**: Aprenda sobre os eventos de página usados pelo `expect_file_chooser()`
- **[Análise Profunda: Domínio da Aba](../../deep-dive/tab-domain.md#file-chooser-handling)**: Detalhes técnicos sobre a interceptação do seletor de arquivo
- **[Análise Profunda: Sistema de Eventos](../../deep-dive/event-system.md#file-chooser-events)**: Como os eventos do seletor de arquivo funcionam internamente

As operações com arquivos no Pydoll eliminam um dos maiores pontos problemáticos na automação de navegadores, fornecendo métodos limpos e confiáveis tanto para cenários de upload simples quanto complexos.