# Operações com arquivos

Fazer upload e download de arquivos significa lidar com diálogos em nível de sistema operacional que a maioria das ferramentas de automação não consegue alcançar. O Pydoll cuida dos dois para você: ele define os arquivos que um seletor de arquivos pede, e captura um download sem que você fique consultando o sistema de arquivos esperando ele terminar.

## Fazer upload para um input de arquivo

Quando a página tem um `<input type="file">` de verdade, encontre-o e chame `set_input_files()`. Isso define os arquivos diretamente, sem abrir o diálogo do sistema operacional.

```python
import asyncio
from pathlib import Path

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://the-internet.herokuapp.com/upload')

        file_input = await tab.find(id='file-upload')
        await file_input.set_input_files(Path('report.pdf'))

        submit = await tab.find(id='file-submit')
        await submit.click()

        result = await tab.find(tag_name='h3')
        print(await result.text)   # "File Uploaded!"

asyncio.run(main())
```

`set_input_files()` aceita uma `str`, um `pathlib.Path`, ou uma lista deles. Um `Path` é a escolha mais portável, mas uma string simples também funciona:

```python
await file_input.set_input_files('report.pdf')
await file_input.set_input_files(Path.home() / 'Documents' / 'report.pdf')
```

### Fazer upload de vários arquivos de uma vez

Para um input marcado como `multiple`, passe uma lista. Você pode montar essa lista como quiser, inclusive com `Path.glob()`:

```python
await file_input.set_input_files([
    Path('report.pdf'),
    Path('cover.png'),
])

# todo CSV em uma pasta
csv_files = list(Path('data').glob('*.csv'))
await file_input.set_input_files(csv_files)
```

## Fazer upload por um diálogo seletor de arquivos

Muitos sites escondem o input de arquivo atrás de um botão estilizado ou de uma zona de arrastar e soltar, então clicar nele abre o seletor de arquivos do sistema operacional. O `set_input_files()` não tem o que mirar ali. Em vez disso, envolva o clique em `expect_file_chooser()`: ele intercepta o diálogo e define seus arquivos quando ele abre.

```python
import asyncio
from pathlib import Path

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example-uploads.test/gallery')

        async with tab.expect_file_chooser(files=Path('cover.png')):
            upload_button = await tab.find(class_name='upload-button')
            await upload_button.click()

        print('File selected through the chooser.')

asyncio.run(main())
```

O clique que abre o diálogo vai **dentro** do bloco `async with`. Quando o seletor de arquivos abre, o Pydoll o preenche com seus arquivos; você nunca vê o diálogo nativo. `files` recebe a mesma `str`, `Path` ou lista que `set_input_files()` aceita.

!!! tip "Qual método de upload?"
    Use `set_input_files()` quando há um `<input type="file">` de verdade no DOM; é instantâneo e não precisa de diálogo. Use `expect_file_chooser()` quando o input está escondido e um controle personalizado abre o seletor do sistema operacional.

## Baixar um arquivo

Envolva a ação que inicia um download em `expect_download()`. O Pydoll espera o download terminar e te entrega um handle para lê-lo, então você não fica consultando um diretório esperando o arquivo aparecer.

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://the-internet.herokuapp.com/download')

        async with tab.expect_download() as download:
            link = await tab.query('.example a')
            await link.click()
            data = await download.read_bytes()

        print(f'Downloaded {len(data)} bytes')

asyncio.run(main())
```

Leia o arquivo **dentro** do bloco. Por padrão, o download vai parar em um diretório temporário que é limpo quando o bloco termina, então `read_bytes()` (ou `read_base64()`) é como você captura o conteúdo. O gatilho, aqui um clique em link, também vai dentro do bloco.

### Manter o arquivo em disco

Passe `keep_file_at` com um diretório para persistir o download em vez de usar um diretório temporário descartável. O arquivo permanece depois que o bloco termina, e `download.file_path` te diz onde ele foi parar:

```python
async with tab.expect_download(keep_file_at='downloads/') as download:
    link = await tab.query('.example a')
    await link.click()
    await download.wait_finished()

print(f'Saved to {download.file_path}')
```

`expect_download()` espera até 60 segundos por padrão; passe `timeout` em segundos para mudar isso. O handle também oferece `read_base64()` quando você precisa do conteúdo como uma string base64.

## Próximos passos

- [Eventos](events.md): os eventos de página em que `expect_file_chooser()` e `expect_download()` se apoiam.
- [Capturas de tela e PDFs](screenshots-and-pdfs.md): salve uma página como PDF em vez de baixar um.
- [Encontrar elementos](element-finding.md): localize os inputs e links sobre os quais essas operações atuam.
