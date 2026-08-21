# Browser fingerprinting

O browser fingerprinting identifica clientes pelas propriedades que eles expõem através de APIs JavaScript, cabeçalhos HTTP e do motor de renderização. Enquanto o [network fingerprinting](network-fingerprinting.md) examina sinais de nível de protocolo vindos do kernel do sistema operacional e da biblioteca TLS, o browser fingerprinting mira a camada de aplicação: o navegador específico, sua versão, sua configuração e o hardware em que ele roda. Qualquer site pode ler esses sinais através de APIs web padrão, e a combinação de um número suficiente deles cria um fingerprint que, com frequência, é único entre milhões de visitantes.

## Propriedades do navigator em JavaScript

O objeto `navigator` é a fonte única mais rica de dados de browser fingerprinting. Ele expõe dezenas de propriedades que revelam o navegador, suas capacidades e o sistema em que ele roda. Os sistemas de detecção coletam essas propriedades, cruzam umas com as outras e com os cabeçalhos HTTP, e marcam as inconsistências.

O JavaScript a seguir coleta o conjunto central de propriedades que os sistemas de fingerprinting normalmente examinam:

```javascript
const fingerprint = {
    // Identidade
    userAgent: navigator.userAgent,
    platform: navigator.platform,
    vendor: navigator.vendor,

    // Idioma e localidade
    language: navigator.language,
    languages: navigator.languages,

    // Hardware
    hardwareConcurrency: navigator.hardwareConcurrency,
    deviceMemory: navigator.deviceMemory,
    maxTouchPoints: navigator.maxTouchPoints,

    // Recursos
    cookieEnabled: navigator.cookieEnabled,
    doNotTrack: navigator.doNotTrack,
    webdriver: navigator.webdriver,

    // Tela
    screenWidth: screen.width,
    screenHeight: screen.height,
    colorDepth: screen.colorDepth,
    devicePixelRatio: window.devicePixelRatio,

    // Chrome da janela (dimensões de barra de ferramentas, barra de rolagem)
    chromeHeight: window.outerHeight - window.innerHeight,
    chromeWidth: window.outerWidth - window.innerWidth,

    // Fuso horário
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    timezoneOffset: new Date().getTimezoneOffset(),
};
```

Várias dessas propriedades merecem atenção individual, porque carregam mais peso de fingerprinting ou são configuradas erradas com mais frequência pelas ferramentas de automação.

### Consistência de platform e User-Agent

A propriedade `navigator.platform` retorna uma string como `Win32`, `MacIntel` ou `Linux x86_64`. Os sistemas de detecção comparam isso com o cabeçalho User-Agent. Se o User-Agent HTTP alega `Windows NT 10.0` mas `navigator.platform` retorna `Linux x86_64`, a divergência é um forte sinal. Esse é um dos erros mais comuns em automação: definir um User-Agent customizado via `--user-agent=` sem também sobrescrever a plataforma.

### Propriedades de hardware

`navigator.hardwareConcurrency` retorna o número de núcleos lógicos de CPU. Um valor de 1 ou 2 sugere uma VM ou container mínimo, e não a máquina de um usuário real. `navigator.deviceMemory` reporta a RAM aproximada em gigabytes (0.25, 0.5, 1, 2, 4, 8). Essa propriedade só está disponível em navegadores Chromium; Firefox e Safari retornam `undefined`. Ambos os valores devem ser consistentes com o dispositivo alegado: um User-Agent que alega um desktop moderno mas reporta 1 núcleo e 0.5 GB de RAM é suspeito.

### Propriedade WebDriver

A propriedade `navigator.webdriver` é `true` quando o navegador é controlado por automação baseada em WebDriver (Selenium, Playwright em modo WebDriver). Esse é o indicador de automação mais óbvio de todos. O Chrome moderno define a propriedade como um getter que retorna `false` numa sessão normal, e só a inverte para `true` sob flags de automação. O Pydoll dirige o Chrome através do CDP sem essas flags, então `navigator.webdriver` reporta `false`, o mesmo que a sessão de um usuário normal. Não é `undefined`; um valor `undefined` seria por si só incomum e não é o que o Pydoll produz.

### Plugins

A propriedade `navigator.plugins` foi historicamente um forte vetor de fingerprinting, porque navegadores e configurações de SO diferentes expunham listas de plugins diferentes. Os navegadores Chromium modernos (Chrome 90+) retornam uma lista fixa de cinco plugins relacionados a PDF, independentemente do estado real de plugins:

```javascript
// O Chrome moderno sempre retorna estes 5 plugins:
// 1. PDF Viewer
// 2. Chrome PDF Viewer
// 3. Chromium PDF Viewer
// 4. Microsoft Edge PDF Viewer
// 5. WebKit built-in PDF
console.log(navigator.plugins.length); // 5
```

Uma crença equivocada comum afirma que os navegadores modernos retornam arrays vazios para `navigator.plugins`. Isso está incorreto. Retornar um array vazio é por si só um sinal de detecção que sugere modo headless ou um cliente HTTP que não é navegador.

### Dimensões de tela e janela

A diferença entre `window.outerWidth`/`outerHeight` e `window.innerWidth`/`innerHeight` representa o chrome do navegador (barras de ferramentas, barras de rolagem, moldura da janela). Navegadores headless frequentemente reportam diferença zero porque não têm UI visível. Os sistemas de detecção marcam clientes em que `outerWidth` é igual a `innerWidth` como potencialmente headless. De forma parecida, `screen.width` casando exatamente com `innerWidth` sugere uma janela headless maximizada, e não uma sessão de desktop normal.

O `devicePixelRatio` varia por display: monitores padrão reportam `1.0`, telas Retina de MacBook reportam `2.0`, e smartphones reportam `2.0` a `3.0`. Esse valor deve ser consistente com o dispositivo alegado no User-Agent.

## User-Agent client hints

Os navegadores Chromium modernos (Chrome, Edge, Opera) complementam a string tradicional do User-Agent com cabeçalhos Client Hints: `Sec-CH-UA`, `Sec-CH-UA-Platform`, `Sec-CH-UA-Mobile` e (sob demanda) valores de maior entropia como `Sec-CH-UA-Full-Version-List`, `Sec-CH-UA-Arch` e `Sec-CH-UA-Bitness`.

```http
Sec-CH-UA: "Chromium";v="120", "Google Chrome";v="120", "Not:A-Brand";v="99"
Sec-CH-UA-Mobile: ?0
Sec-CH-UA-Platform: "Windows"
```

Os Client Hints fornecem dados estruturados e legíveis por máquina, mais difíceis de forjar de forma inconsistente. Um servidor pode comparar o cabeçalho `Sec-CH-UA-Platform` com `navigator.platform`, a string do User-Agent e o fingerprint TCP/IP. Qualquer inconsistência entre essas camadas é um sinal de detecção.

O equivalente do lado do JavaScript é `navigator.userAgentData`, que expõe `brands`, `mobile` e `platform` como valores de baixa entropia, e `getHighEntropyValues()` para informações detalhadas de versão, arquitetura e bitness:

```javascript
// Baixa entropia (sempre disponível, sem necessidade de permissão)
console.log(navigator.userAgentData.brands);
// [{brand: "Chromium", version: "120"}, {brand: "Google Chrome", version: "120"}, ...]
console.log(navigator.userAgentData.platform); // "Windows"
console.log(navigator.userAgentData.mobile);   // false

// Alta entropia (requer promise, pode exigir permissão)
const highEntropy = await navigator.userAgentData.getHighEntropyValues([
    'architecture', 'bitness', 'platformVersion', 'uaFullVersion'
]);
// {architecture: "x86", bitness: "64", platformVersion: "15.0.0", ...}
```

!!! warning "Suporte dos navegadores"
    Client Hints são um recurso exclusivo do Chromium. Firefox e Safari não enviam cabeçalhos `Sec-CH-UA` e não expõem `navigator.userAgentData`. Se o User-Agent alega Firefox mas o servidor recebe cabeçalhos Client Hints, o cliente não é o Firefox.

## Canvas fingerprinting

O canvas fingerprinting explora o fato de que a API HTML5 Canvas produz uma saída de pixels sutilmente diferente entre combinações diferentes de GPU, driver gráfico, SO e navegador. A variação vem de diferenças na rasterização de fontes (renderização sub-pixel, hinting, anti-aliasing), da execução de shaders específica da GPU, da precisão de ponto flutuante no pipeline gráfico e das bibliotecas de renderização de texto no nível do SO (DirectWrite no Windows, Core Text no macOS, FreeType no Linux).

A técnica desenha texto, formas e gradientes num canvas oculto, extrai os dados de pixels e faz o hash deles:

```javascript
function generateCanvasFingerprint() {
    const canvas = document.createElement('canvas');
    canvas.width = 220;
    canvas.height = 30;
    const ctx = canvas.getContext('2d');

    // Retângulo colorido (expõe diferenças de blending)
    ctx.fillStyle = '#f60';
    ctx.fillRect(125, 1, 62, 20);

    // Texto com emoji (maximiza a variação de renderização)
    ctx.font = '14px Arial';
    ctx.textBaseline = 'alphabetic';
    ctx.fillStyle = '#069';
    ctx.fillText('Cwm fjordbank glyphs vext quiz, 😃', 2, 15);

    // Sobreposição semitransparente (expõe diferenças de composição alfa)
    ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
    ctx.fillText('Cwm fjordbank glyphs vext quiz, 😃', 4, 17);

    return canvas.toDataURL();
}
```

O pangrama "Cwm fjordbank glyphs vext quiz" é escolhido porque usa combinações incomuns de caracteres que estressam a renderização de fontes. O emoji adiciona outra dimensão porque a renderização de emoji varia entre sistemas operacionais. A sobreposição semitransparente testa a composição alfa, que difere entre implementações de GPU.

O canvas fingerprinting é eficaz para distinguir categorias amplas de dispositivos, mas sua unicidade às vezes é superestimada. A pesquisa de Laperdrix et al. (2016) constatou que os fingerprints de canvas isolados fornecem poder de distinção moderado, e seu valor real vem de combinar com outros sinais (WebGL, propriedades do navigator, fuso horário) para alcançar alta unicidade.

!!! note "Injeção de ruído no canvas"
    Algumas ferramentas de privacidade injetam ruído aleatório na saída do canvas para quebrar o fingerprinting. Os sistemas de detecção rebatem isso solicitando o fingerprint de canvas várias vezes na mesma sessão. Se o hash muda entre as solicitações, há injeção de ruído presente, o que é por si só um sinal de detecção. Aleatorizar a saída do canvas é, portanto, contraproducente: não impede a identificação e revela o uso de ferramentas anti-fingerprinting.

Como o Pydoll controla uma instância real do Chrome com renderização de GPU de verdade, o fingerprint de canvas é autêntico e consistente entre leituras repetidas. Nenhuma injeção ou spoofing é necessário.

## WebGL fingerprinting

O WebGL fingerprinting estende o canvas fingerprinting para dentro do pipeline de renderização 3D. Ele é mais revelador porque expõe diretamente identificadores de hardware que são difíceis de forjar.

Os dados mais distintivos vêm da extensão `WEBGL_debug_renderer_info`, que revela o fabricante e o modelo da GPU:

```javascript
function getWebGLFingerprint() {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl');
    if (!gl) return null;

    // Identificação da GPU (mais distintiva)
    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
    const vendor = debugInfo
        ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL)
        : gl.getParameter(gl.VENDOR);
    const renderer = debugInfo
        ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL)
        : gl.getParameter(gl.RENDERER);

    return {
        vendor,    // ex.: "Google Inc. (NVIDIA)"
        renderer,  // ex.: "ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Direct3D11 vs_5_0 ps_5_0)"
        version: gl.getParameter(gl.VERSION),
        shadingLanguageVersion: gl.getParameter(gl.SHADING_LANGUAGE_VERSION),
        maxTextureSize: gl.getParameter(gl.MAX_TEXTURE_SIZE),
        extensions: gl.getSupportedExtensions(),
    };
}
```

A string do renderer nomeia diretamente o hardware da GPU. Um cliente que alega ser um dispositivo móvel mas reporta uma GPU de desktop é inconsistente. Máquinas virtuais frequentemente reportam renderizadores de software como "SwiftShader" ou "llvmpipe", que usuários reais quase nunca têm.

Além dos metadados, o WebGL pode renderizar uma cena 3D (um triângulo com gradiente, por exemplo) e fazer o hash da saída de pixels, produzindo um render fingerprint análogo ao canvas fingerprinting, mas no pipeline 3D. A combinação de identificadores de GPU, extensões suportadas, limites de parâmetros (`MAX_TEXTURE_SIZE`, `MAX_VIEWPORT_DIMS`) e formatos de precisão de shader cria um fingerprint detalhado da pilha gráfica.

## AudioContext fingerprinting

A Web Audio API gera fingerprints processando áudio e medindo a saída. A técnica padrão cria um `OscillatorNode`, o roteia através de um `DynamicsCompressorNode` e lê as amostras de áudio resultantes de um `AnalyserNode` ou `OfflineAudioContext`. Diferenças nas implementações de processamento de áudio entre navegadores e pilhas de áudio do SO produzem saídas distintas.

```javascript
function getAudioFingerprint() {
    const ctx = new OfflineAudioContext(1, 44100, 44100);
    const oscillator = ctx.createOscillator();
    oscillator.type = 'triangle';
    oscillator.frequency.setValueAtTime(10000, ctx.currentTime);

    const compressor = ctx.createDynamicsCompressor();
    compressor.threshold.setValueAtTime(-50, ctx.currentTime);
    compressor.knee.setValueAtTime(40, ctx.currentTime);
    compressor.ratio.setValueAtTime(12, ctx.currentTime);
    compressor.attack.setValueAtTime(0, ctx.currentTime);
    compressor.release.setValueAtTime(0.25, ctx.currentTime);

    oscillator.connect(compressor);
    compressor.connect(ctx.destination);
    oscillator.start(0);

    return ctx.startRendering().then(buffer => {
        const data = buffer.getChannelData(0);
        // Faz o hash de um subconjunto das amostras de áudio
        let hash = 0;
        for (let i = 4500; i < 5000; i++) {
            hash += Math.abs(data[i]);
        }
        return hash;
    });
}
```

O AudioContext fingerprinting é menos difundido do que o canvas ou o WebGL fingerprinting, mas adiciona outra dimensão ao fingerprint geral. O sinal é particularmente útil para distinguir navegadores no mesmo SO, já que o processamento de áudio varia mais entre motores de navegador do que entre versões do SO.

## Battery Status API

A Battery Status API (`navigator.getBattery()`) expõe o nível da bateria do dispositivo, o status de carregamento e os tempos estimados de carga/descarga. Esses valores criam um fingerprint efêmero mas único durante a sessão.

Essa API só está disponível em navegadores Chromium. O Firefox a removeu na versão 52 (2017) citando preocupações de privacidade, e o Safari nunca a implementou. Sistemas de detecção que veem resultados da Battery API vindos de um cliente que alega ser Firefox ou Safari sabem que o cliente está distorcendo sua identidade.

## HTTP header fingerprinting

Além das APIs JavaScript, os cabeçalhos HTTP fornecem sinais de fingerprinting visíveis ao servidor antes de qualquer JavaScript executar.

### Ordem dos cabeçalhos

Os navegadores enviam os cabeçalhos HTTP numa ordem consistente e específica da versão. O Chrome coloca os cabeçalhos `Sec-CH-UA` no início, antes do `User-Agent`. O Firefox começa com `User-Agent` seguido de `Accept` e `Accept-Language`. Bibliotecas HTTP automatizadas como o `requests` ou o `httpx` do Python enviam os cabeçalhos em outra ordem ainda, tipicamente começando com `Host` e `Connection`.

Os sistemas de detecção registram a ordem dos primeiros 10 a 15 cabeçalhos e comparam com assinaturas conhecidas de navegadores. Mesmo que todos os valores individuais dos cabeçalhos estejam corretos, enviá-los na ordem errada revela que a requisição não foi gerada pelo navegador alegado. Como o Pydoll controla uma instância real do Chrome, a ordem dos cabeçalhos é autêntica.

### Accept-Encoding

Os navegadores modernos suportam compressão Brotli (`br`) além de `gzip` e `deflate`. O Chrome também suporta `zstd`. O `Accept-Encoding` do Chrome moderno se parece com `gzip, deflate, br, zstd`. Um cliente que alega ser Chrome mas está sem Brotli está desatualizado ou é automatizado.

### Consistência de Accept-Language

O cabeçalho `Accept-Language` deve ser consistente com `navigator.language`, `navigator.languages`, o fuso horário e a geolocalização do IP. Uma requisição com `Accept-Language: en-US` de um IP em Tóquio com fuso horário `Asia/Tokyo` é plausível para um viajante, mas suspeita em combinação com outros sinais. Uma requisição com `Accept-Language: zh-CN` e fuso horário `America/New_York` de um IP de datacenter chinês é um forte indicador de proxy.

## Implicações para o Pydoll

Como o Pydoll dirige um navegador Chromium real através do CDP, todos os fingerprints de nível de navegador são autênticos por padrão. Os fingerprints de canvas, WebGL e AudioContext vêm de hardware de GPU e áudio de verdade. As propriedades do navigator, os plugins e as dimensões de tela refletem o estado real do navegador. Os cabeçalhos HTTP, incluindo sua ordem, são gerados pela pilha de rede do Chrome.

O principal risco em automação é a inconsistência entre camadas. Definir um User-Agent customizado sem sincronizar as propriedades relacionadas cria divergências trivialmente detectáveis. O Pydoll cuida disso automaticamente: quando ele detecta `--user-agent=` nos argumentos do navegador, usa `Emulation.setUserAgentOverride` para sincronizar a string do User-Agent, a plataforma e os metadados completos de Client Hints em todas as camadas. Ele também injeta sobrescritas de `navigator.vendor` e `navigator.appVersion` via `Page.addScriptToEvaluateOnNewDocument` para garantir consistência em abas recém-abertas.

Os cabeçalhos de idioma vêm da flag `--lang` e de `set_accept_languages()`, e `webrtc_leak_protection` impede que o WebRTC exponha o IP real por trás de um proxy. O fuso horário e a geolocalização precisam casar com a localização do IP do proxy e permanecer consistentes com todo o resto; [`tab.apply_fingerprint()`](../../stealth/fingerprint-injection.md) os aplica junto com a localidade, o User-Agent e os Client Hints, a partir de um único perfil coerente.

O princípio é que o Pydoll te dá o fingerprint autêntico do navegador como linha de base, e você só precisa manter as camadas configuráveis (User-Agent, fuso horário, idioma, geolocalização) consistentes entre si e com o proxy.

## Relacionado

- [Network fingerprinting](network-fingerprinting.md): a camada de protocolo abaixo dessas APIs.
- [Behavioral fingerprinting](behavioral-fingerprinting.md): como mouse, teclado e timing são analisados.
- [Evasion techniques](../../stealth/evasion-techniques.md): as alavancas práticas que você controla.
- [Fingerprint injection](../../stealth/fingerprint-injection.md): aplique uma identidade coerente em todas as camadas.

## Referências

- Laperdrix, P., Rudametkin, W., & Baudry, B. (2016). Beauty and the Beast: Diverting Modern Web Browsers to Build Unique Browser Fingerprints. IEEE S&P.
- Mowery, K., & Shacham, H. (2012). Pixel Perfect: Fingerprinting Canvas in HTML5. USENIX Security.
- Eckersley, P. (2010). How Unique Is Your Web Browser? Privacy Enhancing Technologies Symposium.
- W3C Client Hints Infrastructure: https://wicg.github.io/client-hints-infrastructure/
- BrowserLeaks: https://browserleaks.com/
- CreepJS: https://abrahamjuliot.github.io/creepjs/
