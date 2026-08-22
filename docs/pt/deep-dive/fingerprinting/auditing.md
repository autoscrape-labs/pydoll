# Auditando um fingerprint

Você não consegue melhorar o que não consegue medir. Uma vez que um perfil é aplicado, a questão é quais sinais agora são lidos como um dispositivo real e quais ainda vazam, e nenhuma quantidade de leitura do código responde isso tão bem quanto apontar um detector para o navegador. Esta página cobre como medir isso, de um bot score gratuito até ler exatamente o que um detector comercial coleta.

Ela se apoia em [Os limites do spoofing](spoofing-limits.md): aquela página explica o que pode e o que não pode ser forjado, esta mostra como verificar o que a sua configuração de fato fez.

## Leia o bot score

O [fingerprint-scan.com](https://fingerprint-scan.com/) roda um teste de fingerprinting e detecção de bots dentro da página e reporta um score de 0 a 100, onde mais baixo é lido como mais humano. Dirija-o com o Pydoll e tire um screenshot do resultado:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from examples.fingerprints import FINGERPRINTS

async def scan(profile):
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.apply_fingerprint(FINGERPRINTS[profile])
        await tab.go_to('https://fingerprint-scan.com/')
        await asyncio.sleep(15)          # let the score finish computing
        await tab.take_screenshot(f'{profile}.png')

asyncio.run(scan('macos_m3_new_york'))
```

O número por si só significa pouco. Seu valor está na comparação: rode a mesma máquina com e sem o perfil, e com um perfil combinando versus um deliberadamente incompatível, e compare os scores. É assim que você atribui uma mudança a um sinal específico em vez de adivinhar.

O exemplo mais claro é o headless. Sem perfil, o Chrome headless marca o máximo:

<p align="center">
  <img src="/docs/resources/images/fp-scan-headless-nofp.png" alt="fingerprint-scan.com reportando um bot score de 100/100 para o Chrome headless sem fingerprint" width="720" />
</p>

Aplique um perfil que combina e a mesma execução headless cai para o score do headful:

<p align="center">
  <img src="/docs/resources/images/fp-scan-headless-mac.png" alt="fingerprint-scan.com reportando um bot score de 15/100 para o Chrome headless com um fingerprint de macOS aplicado" width="720" />
</p>

!!! warning "Um bot score é um retrato de um momento"
    Uma máquina, um IP, uma build do Chrome, um ponto no tempo. Os sites de detecção também mudam a pontuação deles. Leia a *direção* que uma mudança move o score, não o número absoluto.

## Cruze os detectores de mentira

Um bot score é uma opinião. O [CreepJS](https://abrahamjuliot.github.io/creepjs/) é uma segunda e mais rigorosa: ele não apenas lê cada sinal, ele inspeciona como cada um foi definido e lê o fingerprint inteiro uma segunda vez dentro de um Web Worker, e depois reporta as contradições como *mentiras*.

Essa passagem pelo worker é a que um override ingênuo falha. O CreepJS lê a identidade na página e de novo num `WorkerNavigator`, um realm separado que um hook da thread principal nunca alcança. Se a página diz Windows e o worker diz o macOS real, essa divergência é a mentira. Um perfil aplicado corretamente reporta a mesma identidade em ambos:

<p align="center">
  <img src="/docs/resources/images/creepjs-worker-windows.png" alt="Painel Worker do CreepJS reproduzindo a identidade de Windows injetada: um User-Agent de Windows, uma NVIDIA GeForce RTX 3060, Win32 e Windows 11, tudo dentro de um service worker num Mac da Apple" width="720" />
</p>

O [SannySoft](https://bot.sannysoft.com/) e o [BrowserScan](https://www.browserscan.net/bot-detection) são verificações mais rápidas para as flags de headless e de automação. Use-os como uma passagem rápida, não como a palavra final.

## Compare os caminhos de leitura você mesmo

A auditoria mais forte não precisa de um site de terceiros. Para qualquer sinal, leia-o de duas formas e verifique se elas concordam, porque uma divergência costuma ser um vazamento que os seus próprios overrides criaram:

```python
result = await tab.execute_script('''
    document.head.insertAdjacentHTML('beforeend',
        '<style>.probe{--g: srgb} @media (color-gamut: p3){.probe{--g: p3}}</style>');
    const probe = document.createElement('div');
    probe.className = 'probe';
    document.body.appendChild(probe);
    return {
        matchMedia: matchMedia('(color-gamut: p3)').matches ? 'p3' : 'srgb',
        css: getComputedStyle(probe).getPropertyValue('--g').trim(),
    };
''', return_by_value=True)
```

Se o `matchMedia` e o caminho CSS discordam, um override está mentindo em apenas um caminho, o modo de falha que [Os limites do spoofing](spoofing-limits.md) percorre. O mesmo teste se aplica entre realms (página versus worker) e entre APIs (a string do WebGL versus o adapter do WebGPU). Um perfil coerente passa em todos eles; uma contradição é um sinal que você introduziu.

## Leia o que um detector real coleta

A auditoria mais profunda é parar de adivinhar quais sinais importam e ler a lista que um detector de produção de fato lê. Esses agentes são distribuídos fortemente ofuscados, mas a superfície que eles medem é API pública do navegador, então ela pode passar por engenharia reversa.

Uma análise pública do **Fingerprint Pro v4** (build `jsl/4.0.0`), medida contra o tenant de demonstração público do fornecedor numa máquina em agosto de 2026, cataloga cerca de **143 sinais individuais**, entre tela e display, hardware, `navigator`, GPU (WebGL e WebGPU), áudio, fontes, mídia, armazenamento e flags de automação. Esses números são específicos daquela build, daquele tenant e daquele momento, não uma lei universal, mas duas descobertas remodelam como você audita:

- **A maior parte da superfície não decide a identidade por conta própria.** Nas execuções testadas, mover canvas, WebGL, o User-Agent, a tela e o locale juntos não cunhou de forma independente um novo visitante; o fuzzy match o tolerou. Mudar os digests do canvas moveu sim a confiança reportada, de cerca de 0.99 para 0.97, sem cunhar um novo id. Então a maior parte do esforço de spoofing é desperdiçada na identidade.
- **O sinal de identidade mais forte não é um fingerprint.** É um bearer token, `s56`, que o tenant emite no GET inicial do agente e o cliente retransmite em todo POST. Uma vez vinculado, o payload responde como aquele visitante independentemente de canvas, GPU ou User-Agent.

!!! note "Identidade é um problema de token de sessão, não de fingerprint"
    Para se apresentar como um novo visitante, comece a partir de um [contexto de navegador](../../guides/browser-contexts.md) limpo, para que nenhum token `s56` anterior seja retransmitido e o agente emita um novo. Para persistir uma identidade, reutilize o contexto para que o mesmo token volte. Nesta análise, forjar canvas, WebGL e o User-Agent não mudou de forma independente o id do visitante, então esse esforço é mais bem gasto em coerência do que numa nova identidade. O IP de saída foi excluído da análise de identidade; ele alimenta um sinal separado de bot e de proxy, então rotacionar apenas o IP não muda quem o token diz que você é.

## Capture o que o agente envia

!!! warning "Manuseie um payload capturado com cuidado"
    Um payload capturado carrega tokens de sessão, identificadores de armazenamento, o seu IP e outros dados que identificam você. Capture apenas contra um site que você está autorizado a testar, rode isso sob uma identidade descartável que você possa jogar fora, e oculte os tokens, os ids de armazenamento e o IP antes de armazenar, compartilhar ou colar o payload em qualquer lugar.

O agente não só lê esses sinais, ele os empacota e os envia via POST para o seu servidor, e esse payload é legível. Um agente típico serializa os sinais para JSON, os codifica numa forma compacta de bytes, comprime tudo o que passa de cerca de um kilobyte com DEFLATE puro, e envolve o resultado num envelope emoldurado cuja chave viaja dentro do quadro. Esse último passo é ofuscação, não criptografia; não há segredo nenhum que você esteja perdendo.

Então a auditoria mais profunda é uma captura. Use a [interceptação de requisições](../../guides/request-interception.md) para pegar o corpo do POST do agente, reverter o enquadramento e descomprimi-lo. O que sai é o conjunto exato de sinais que o detector construiu para a sua sessão, lido direto do código que te pontua. Essa é a verdade de base para saber quais dos seus overrides seguraram e quais vazaram, e é mais confiável do que qualquer bot score, porque é a entrada do score, e não a saída.

## Relacionado

- [Os limites do spoofing](spoofing-limits.md): o que um spoof consegue e não consegue mover.
- [Injeção de fingerprint](../../stealth/fingerprint-injection.md): aplicando um perfil coerente.
- [Contextos de navegador](../../guides/browser-contexts.md): uma identidade por contexto, a alavanca real para um novo visitante.
