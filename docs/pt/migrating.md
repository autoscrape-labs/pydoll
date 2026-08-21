# Migrando do Selenium e do Playwright

Se você já automatiza navegadores, a maior parte do que você sabe se aproveita. Esta página mapeia os comandos que você usa todo dia para os equivalentes no Pydoll, e aponta onde o Pydoll funciona de forma diferente.

Três coisas mudam, não importa de qual ferramenta você venha:

- **Sem webdriver ou navegador embutido.** O Pydoll controla o Chrome ou o Edge que já está na sua máquina pelo DevTools Protocol. Não há `chromedriver` para instalar ou casar versões.
- **Sem esperas explícitas.** `find()` e `query()` esperam pelo elemento sozinhos, então a dança de `WebDriverWait` e `expected_conditions` desaparece.
- **Assíncrono por padrão.** Toda chamada é `await`ada dentro de um `async def`, iniciada com `asyncio.run()`. Novo nisso? Veja [Python assíncrono na prática](basics/async-python.md).

## Do Selenium

| Tarefa | Selenium | Pydoll |
|------|----------|--------|
| Iniciar | `driver = webdriver.Chrome()` | `async with Chrome() as browser: tab = await browser.start()` |
| Abrir uma URL | `driver.get(url)` | `await tab.go_to(url)` |
| Encontrar por id | `driver.find_element(By.ID, 'q')` | `await tab.find(id='q')` |
| Encontrar por CSS | `driver.find_element(By.CSS_SELECTOR, '.item')` | `await tab.query('.item')` |
| Encontrar por XPath | `driver.find_element(By.XPATH, '//a')` | `await tab.query('//a')` |
| Encontrar por texto | `driver.find_element(By.XPATH, "//*[text()='Login']")` | `await tab.find(text='Login')` |
| Encontrar vários | `driver.find_elements(By.CSS_SELECTOR, '.item')` | `await tab.query('.item', find_all=True)` |
| Esperar por um elemento | `WebDriverWait(driver, 10).until(EC.presence_of_element_located(...))` | `await tab.find(id='q', timeout=10)` |
| Clicar | `el.click()` | `await el.click()` |
| Digitar | `el.send_keys('text')` | `await el.type_text('text')` |
| Pressionar uma tecla | `el.send_keys(Keys.ENTER)` | `await tab.keyboard.press(Key.ENTER)` |
| Ler texto | `el.text` | `await el.text` |
| Ler um atributo | `el.get_attribute('href')` | `el.get_attribute('href')` |
| Captura de tela | `driver.save_screenshot('s.png')` | `await tab.take_screenshot('s.png')` |
| Rodar JavaScript | `driver.execute_script('return document.title')` | `await tab.execute_script('return document.title')` |
| Encerrar | `driver.quit()` | saia do bloco `async with`, ou `await browser.stop()` |

Um fluxo de login em Selenium e sua versão em Pydoll:

```python
# Selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Chrome()
driver.get('https://quotes.toscrape.com/login')
driver.find_element(By.ID, 'username').send_keys('tester')
driver.find_element(By.ID, 'password').send_keys('secret')
driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.LINK_TEXT, 'Logout')))
driver.quit()
```

```python
# Pydoll
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://quotes.toscrape.com/login')

        await (await tab.find(id='username')).type_text('tester')
        await (await tab.find(id='password')).type_text('secret')
        await (await tab.find(tag_name='input', type='submit')).click()

        await tab.find(text='Logout', timeout=5)

asyncio.run(main())
```

!!! note "`get_attribute` é síncrono"
    Diferente do Selenium, onde tudo no elemento é uma ida e volta pela rede, o Pydoll lê os atributos do elemento que já localizou, então `get_attribute()` é um método comum, sem `await`. O texto ainda é awaitado (`await el.text`).

## Do Playwright

| Tarefa | Playwright | Pydoll |
|------|------------|--------|
| Iniciar | `browser = await p.chromium.launch(); page = await browser.new_page()` | `async with Chrome() as browser: tab = await browser.start()` |
| Abrir uma URL | `await page.goto(url)` | `await tab.go_to(url)` |
| Encontrar por CSS | `page.locator('.item')` | `await tab.query('.item')` |
| Encontrar por texto | `page.get_by_text('Login')` | `await tab.find(text='Login')` |
| Encontrar por role/label | `page.get_by_role('button')` | `await tab.find(tag_name='button')` |
| Encontrar vários | `page.locator('.item').all()` | `await tab.query('.item', find_all=True)` |
| Clicar | `await page.locator('.btn').click()` | `await (await tab.find(class_name='btn')).click()` |
| Preencher um input | `await page.fill('#q', 'text')` | `await (await tab.find(id='q')).type_text('text')` |
| Ler texto | `await page.locator('.title').text_content()` | `await (await tab.find(class_name='title')).text` |
| Ler um atributo | `await loc.get_attribute('href')` | `el.get_attribute('href')` |
| Nova aba | `await context.new_page()` | `await browser.new_tab()` |
| Captura de tela | `await page.screenshot(path='s.png')` | `await tab.take_screenshot('s.png')` |
| Fechar | `await browser.close()` | saia do bloco `async with`, ou `await browser.stop()` |

Ambos são assíncronos e ambos esperam automaticamente, então migrar é, na maior parte, renomear. A principal diferença conceitual é o que uma busca retorna:

- Um **locator** do Playwright é preguiçoso: ele re-resolve o elemento toda vez que você age sobre ele.
- Um `find()` / `query()` do Pydoll retorna um **`WebElement`** resolvido uma vez, ali na hora. Chame `find()` de novo se a página substituiu o elemento.

```python
# Playwright
from playwright.async_api import async_playwright

async with async_playwright() as p:
    browser = await p.chromium.launch()
    page = await browser.new_page()
    await page.goto('https://quotes.toscrape.com')
    quote = await page.locator('.quote .text').first.text_content()
    print(quote)
    await browser.close()
```

```python
# Pydoll
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://quotes.toscrape.com')

        quote = await tab.query('.quote .text')
        print(await quote.text)

asyncio.run(main())
```

!!! tip "Comportamento que você mantém do Playwright, e um que você ganha"
    A espera automática e o async passam direto. O que o Pydoll adiciona é o `humanize=True` em cliques e digitação, que move o cursor por uma trajetória curva e digita com timing variável. Veja [Interações humanizadas](stealth/human-like-interactions.md).

## Próximos passos

- [Sua primeira automação](first-automation.md): um fluxo completo, do login à extração tipada.
- [Encontrando elementos](guides/element-finding.md): todas as formas de localizar elementos no Pydoll.
- [Passando despercebido](stealth/index.md): a história anti-bot, se é por isso que você está mudando.
