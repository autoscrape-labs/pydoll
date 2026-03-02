# Browser Fingerprinting

O browser fingerprinting identifica clientes analisando propriedades expostas através de APIs JavaScript, cabeçalhos HTTP e motores de renderização. Diferentemente do network fingerprinting, que examina sinais de nível de protocolo do kernel do SO e biblioteca TLS, o browser fingerprinting tem como alvo a camada de aplicação: o navegador específico, sua versão, sua configuração e o hardware em que roda. Esses sinais são acessíveis a qualquer site através de APIs web padrão, e a combinação de propriedades suficientes cria um fingerprint que é frequentemente único entre milhões de visitantes.

!!! info "Navegação do Módulo"
    - [Network Fingerprinting](./network-fingerprinting.md): Fingerprinting de protocolo TCP/IP, TLS, HTTP/2
    - [Behavioral Fingerprinting](./behavioral-fingerprinting.md): Análise de mouse, teclado, scroll
    - [Técnicas de Evasão](./evasion-techniques.md): Contramedidas práticas

## Propriedades JavaScript do Navigator

O objeto `navigator` é a fonte mais rica de dados de fingerprinting de navegador. Ele expõe dezenas de propriedades que revelam o navegador, suas capacidades e o sistema em que roda. Sistemas de detecção coletam essas propriedades, fazem referência cruzada entre elas e contra cabeçalhos HTTP, e sinalizam inconsistências.

O seguinte JavaScript coleta o conjunto central de propriedades que sistemas de fingerprinting tipicamente examinam:

```javascript
const fingerprint = {
    // Identidade
    userAgent: navigator.userAgent,
    platform: navigator.platform,
    vendor: navigator.vendor,

    // Idioma e locale
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

    // Chrome do navegador (barra de ferramentas, dimensões da scrollbar)
    chromeHeight: window.outerHeight - window.innerHeight,
    chromeWidth: window.outerWidth - window.innerWidth,

    // Timezone
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    timezoneOffset: new Date().getTimezoneOffset(),
};
```

Várias dessas propriedades merecem atenção individual porque carregam mais peso de fingerprinting ou são mais comumente mal configuradas por ferramentas de automação.

### Consistência de Platform e User-Agent

A propriedade `navigator.platform` retorna uma string como `Win32`, `MacIntel` ou `Linux x86_64`. Sistemas de detecção comparam isso com o cabeçalho User-Agent. Se o User-Agent HTTP afirma `Windows NT 10.0` mas `navigator.platform` retorna `Linux x86_64`, a inconsistência é um sinal forte. Este é um dos erros mais comuns em automação: definir um User-Agent personalizado via `--user-agent=` sem também sobrescrever a plataforma.

### Propriedades de Hardware

`navigator.hardwareConcurrency` retorna o número de núcleos lógicos de CPU. Um valor de 1 ou 2 sugere uma VM ou container mínimo em vez de uma máquina real de usuário. `navigator.deviceMemory` reporta RAM aproximada em gigabytes (0.25, 0.5, 1, 2, 4, 8). Esta propriedade só está disponível em navegadores Chromium; Firefox e Safari retornam `undefined`. Ambos os valores devem ser consistentes com o dispositivo declarado: um User-Agent alegando um desktop moderno mas reportando 1 núcleo e 0.5 GB de RAM é suspeito.

### Propriedade WebDriver

A propriedade `navigator.webdriver` é `true` quando o navegador é controlado por automação baseada em WebDriver (Selenium, Playwright em modo WebDriver). Este é o indicador de automação mais óbvio. O Pydoll usa CDP (Chrome DevTools Protocol) diretamente, que não define esta flag. Em um navegador controlado pelo Pydoll, `navigator.webdriver` é `undefined`, correspondendo ao comportamento de uma sessão normal de usuário.

### Plugins

A propriedade `navigator.plugins` foi historicamente um forte vetor de fingerprinting porque diferentes navegadores e configurações de SO expunham diferentes listas de plugins. Navegadores Chromium modernos (Chrome 90+) retornam uma lista fixa de cinco plugins relacionados a PDF independentemente do estado real dos plugins:

```javascript
// Chrome moderno sempre retorna estes 5 plugins:
// 1. PDF Viewer
// 2. Chrome PDF Viewer
// 3. Chromium PDF Viewer
// 4. Microsoft Edge PDF Viewer
// 5. WebKit built-in PDF
console.log(navigator.plugins.length); // 5
```

Um equívoco comum alega que navegadores modernos retornam arrays vazios para `navigator.plugins`. Isto é incorreto. Retornar um array vazio é em si um sinal de detecção que sugere modo headless ou um cliente HTTP não-navegador.

### Dimensões de Tela e Janela

A diferença entre `window.outerWidth`/`outerHeight` e `window.innerWidth`/`innerHeight` representa o chrome do navegador (barras de ferramentas, scrollbars, moldura da janela). Navegadores headless frequentemente reportam diferença zero porque não têm UI visível. Sistemas de detecção sinalizam clientes onde `outerWidth` é igual a `innerWidth` como potencialmente headless. Da mesma forma, `screen.width` correspondendo a `innerWidth` exatamente sugere uma janela headless maximizada em vez de uma sessão desktop normal.

O `devicePixelRatio` varia por display: monitores padrão reportam `1.0`, displays Retina de MacBook reportam `2.0`, e smartphones reportam `2.0` a `3.0`. Este valor deve ser consistente com o dispositivo declarado no User-Agent.

## User-Agent Client Hints

Navegadores Chromium modernos (Chrome, Edge, Opera) complementam a string User-Agent tradicional com cabeçalhos Client Hints: `Sec-CH-UA`, `Sec-CH-UA-Platform`, `Sec-CH-UA-Mobile`, e (sob demanda) valores de maior entropia como `Sec-CH-UA-Full-Version-List`, `Sec-CH-UA-Arch` e `Sec-CH-UA-Bitness`.

```http
Sec-CH-UA: "Chromium";v="120", "Google Chrome";v="120", "Not:A-Brand";v="99"
Sec-CH-UA-Mobile: ?0
Sec-CH-UA-Platform: "Windows"
```

Client Hints fornecem dados estruturados e legíveis por máquina que são mais difíceis de falsificar de forma inconsistente. Um servidor pode comparar o cabeçalho `Sec-CH-UA-Platform` com `navigator.platform`, a string User-Agent e o fingerprint TCP/IP. Qualquer inconsistência entre essas camadas é um sinal de detecção.

O equivalente no lado JavaScript é `navigator.userAgentData`, que expõe `brands`, `mobile` e `platform` como valores de baixa entropia, e `getHighEntropyValues()` para informações detalhadas de versão, arquitetura e bitness:

```javascript
// Baixa entropia (sempre disponível, sem necessidade de permissão)
console.log(navigator.userAgentData.brands);
// [{brand: "Chromium", version: "120"}, {brand: "Google Chrome", version: "120"}, ...]
console.log(navigator.userAgentData.platform); // "Windows"
console.log(navigator.userAgentData.mobile);   // false

// Alta entropia (requer promise, pode requerer permissão)
const highEntropy = await navigator.userAgentData.getHighEntropyValues([
    'architecture', 'bitness', 'platformVersion', 'uaFullVersion'
]);
// {architecture: "x86", bitness: "64", platformVersion: "15.0.0", ...}
```

!!! warning "Suporte de Navegador"
    Client Hints são um recurso exclusivo do Chromium. Firefox e Safari não enviam cabeçalhos `Sec-CH-UA` e não expõem `navigator.userAgentData`. Se o User-Agent alega Firefox mas o servidor recebe cabeçalhos Client Hints, o cliente não é Firefox.

## Canvas Fingerprinting

O canvas fingerprinting explora o fato de que a API Canvas do HTML5 produz saída de pixels sutilmente diferente em diferentes combinações de GPU, driver gráfico, SO e navegador. A variação vem de diferenças na rasterização de fontes (renderização sub-pixel, hinting, anti-aliasing), execução de shader específica da GPU, precisão de ponto flutuante no pipeline gráfico e bibliotecas de renderização de texto no nível do SO (DirectWrite no Windows, Core Text no macOS, FreeType no Linux).

A técnica desenha texto, formas e gradientes em um canvas oculto, extrai os dados de pixel e faz hash:

```javascript
function generateCanvasFingerprint() {
    const canvas = document.createElement('canvas');
    canvas.width = 220;
    canvas.height = 30;
    const ctx = canvas.getContext('2d');

    // Retângulo colorido (expõe diferenças de blending)
    ctx.fillStyle = '#f60';
    ctx.fillRect(125, 1, 62, 20);

    // Texto com emoji (maximiza variação de renderização)
    ctx.font = '14px Arial';
    ctx.textBaseline = 'alphabetic';
    ctx.fillStyle = '#069';
    ctx.fillText('Cwm fjordbank glyphs vext quiz, 😃', 2, 15);

    // Sobreposição semi-transparente (expõe diferenças de composição alfa)
    ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
    ctx.fillText('Cwm fjordbank glyphs vext quiz, 😃', 4, 17);

    return canvas.toDataURL();
}
```

O pangrama "Cwm fjordbank glyphs vext quiz" é escolhido porque usa combinações incomuns de caracteres que estressam a renderização de fontes. O emoji adiciona outra dimensão porque a renderização de emoji varia significativamente entre sistemas operacionais. A sobreposição semi-transparente testa composição alfa, que difere entre implementações de GPU.

O canvas fingerprinting é eficaz para distinguir categorias amplas de dispositivos, mas sua unicidade é às vezes exagerada. A pesquisa de Laperdrix et al. (2016) encontrou que fingerprints de canvas sozinhos fornecem poder de distinção moderado, e seu verdadeiro valor vem da combinação com outros sinais (WebGL, propriedades do navigator, timezone) para alcançar alta unicidade.

!!! note "Injeção de Ruído no Canvas"
    Algumas ferramentas de privacidade injetam ruído aleatório na saída do canvas para quebrar o fingerprinting. Sistemas de detecção contra-atacam solicitando o fingerprint do canvas múltiplas vezes na mesma sessão. Se o hash muda entre requisições, injeção de ruído está presente, o que é em si um sinal de detecção. Randomizar a saída do canvas é, portanto, contraproducente: não previne a identificação e revela o uso de ferramentas anti-fingerprinting.

Como o Pydoll controla uma instância real do Chrome com renderização GPU real, o fingerprint de canvas é autêntico e consistente entre leituras repetidas. Nenhuma injeção ou falsificação é necessária.

## WebGL Fingerprinting

O WebGL fingerprinting estende o canvas fingerprinting para o pipeline de renderização 3D. É mais poderoso porque expõe diretamente identificadores de hardware que são difíceis de falsificar.

Os dados mais distintivos vêm da extensão `WEBGL_debug_renderer_info`, que revela o fabricante e modelo da GPU:

```javascript
function getWebGLFingerprint() {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl');
    if (!gl) return null;

    // Identificação da GPU (mais distintivo)
    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
    const vendor = debugInfo
        ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL)
        : gl.getParameter(gl.VENDOR);
    const renderer = debugInfo
        ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL)
        : gl.getParameter(gl.RENDERER);

    return {
        vendor,    // ex: "Google Inc. (NVIDIA)"
        renderer,  // ex: "ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Direct3D11 vs_5_0 ps_5_0)"
        version: gl.getParameter(gl.VERSION),
        shadingLanguageVersion: gl.getParameter(gl.SHADING_LANGUAGE_VERSION),
        maxTextureSize: gl.getParameter(gl.MAX_TEXTURE_SIZE),
        extensions: gl.getSupportedExtensions(),
    };
}
```

A string do renderer nomeia diretamente o hardware da GPU. Um cliente alegando ser um dispositivo móvel mas reportando uma GPU desktop é obviamente inconsistente. Máquinas virtuais frequentemente reportam renderizadores de software como "SwiftShader" ou "llvmpipe", que usuários reais quase nunca têm.

Além de metadados, o WebGL pode renderizar uma cena 3D (um triângulo gradiente, por exemplo) e fazer hash da saída de pixels, produzindo um fingerprint de renderização análogo ao canvas fingerprinting mas no pipeline 3D. A combinação de identificadores de GPU, extensões suportadas, limites de parâmetros (`MAX_TEXTURE_SIZE`, `MAX_VIEWPORT_DIMS`) e formatos de precisão de shader cria um fingerprint detalhado da pilha gráfica.

## AudioContext Fingerprinting

A Web Audio API gera fingerprints processando áudio e medindo a saída. A técnica padrão cria um `OscillatorNode`, roteia através de um `DynamicsCompressorNode`, e lê as amostras de áudio resultantes de um `AnalyserNode` ou `OfflineAudioContext`. Diferenças nas implementações de processamento de áudio entre navegadores e pilhas de áudio do SO produzem saída distinta.

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
        // Hash de um subconjunto das amostras de áudio
        let hash = 0;
        for (let i = 4500; i < 5000; i++) {
            hash += Math.abs(data[i]);
        }
        return hash;
    });
}
```

O AudioContext fingerprinting é menos amplamente implantado que canvas ou WebGL fingerprinting, mas adiciona outra dimensão ao fingerprint geral. O sinal é particularmente útil para distinguir navegadores no mesmo SO, já que o processamento de áudio varia mais entre motores de navegador do que entre versões de SO.

## Battery Status API

A Battery Status API (`navigator.getBattery()`) expõe o nível de bateria do dispositivo, status de carregamento e tempos estimados de carga/descarga. Esses valores criam um fingerprint de curta duração mas único para a duração de uma sessão.

Esta API só está disponível em navegadores Chromium. O Firefox a removeu na versão 52 (2017) citando preocupações de privacidade, e o Safari nunca a implementou. Sistemas de detecção que veem resultados da Battery API de um cliente alegando ser Firefox ou Safari sabem que o cliente está representando falsamente sua identidade.

## Fingerprinting de Cabeçalhos HTTP

Além de APIs JavaScript, cabeçalhos HTTP fornecem sinais de fingerprinting visíveis ao servidor antes de qualquer JavaScript executar.

### Ordem dos Cabeçalhos

Navegadores enviam cabeçalhos HTTP em uma ordem consistente e específica por versão. O Chrome coloca cabeçalhos `Sec-CH-UA` cedo, antes de `User-Agent`. O Firefox lidera com `User-Agent` seguido por `Accept` e `Accept-Language`. Bibliotecas HTTP automatizadas como `requests` ou `httpx` do Python enviam cabeçalhos em outra ordem, tipicamente começando com `Host` e `Connection`.

Sistemas de detecção registram a ordem dos primeiros 10-15 cabeçalhos e comparam contra assinaturas de navegadores conhecidos. Mesmo que todos os valores de cabeçalho individuais estejam corretos, enviá-los na ordem errada revela que a requisição não foi gerada pelo navegador declarado. Como o Pydoll controla uma instância real do Chrome, a ordem dos cabeçalhos é autêntica.

### Accept-Encoding

Navegadores modernos suportam compressão Brotli (`br`) além de `gzip` e `deflate`. O Chrome também suporta `zstd`. O `Accept-Encoding` do Chrome moderno se parece com `gzip, deflate, br, zstd`. Um cliente alegando ser Chrome mas sem Brotli é desatualizado ou automatizado.

### Consistência de Accept-Language

O cabeçalho `Accept-Language` deve ser consistente com `navigator.language`, `navigator.languages`, o timezone e a geolocalização do IP. Uma requisição com `Accept-Language: en-US` de um IP em Tóquio com timezone `Asia/Tokyo` é plausível para um viajante mas suspeita em combinação com outros sinais. Uma requisição com `Accept-Language: zh-CN` e timezone `America/New_York` de um IP de datacenter chinês é um forte indicador de proxy.

## Implicações para o Pydoll

Porque o Pydoll controla um navegador Chromium real através do CDP, todos os fingerprints de nível de navegador são autênticos por padrão. Os fingerprints de canvas, WebGL e AudioContext vêm de hardware real de GPU e áudio. As propriedades do navigator, plugins e dimensões de tela refletem o estado real do navegador. Cabeçalhos HTTP, incluindo sua ordem, são gerados pela pilha de rede do Chrome.

O principal risco na automação é inconsistência entre camadas. Definir um User-Agent personalizado sem sincronizar propriedades relacionadas cria incompatibilidades trivialmente detectáveis. O Pydoll lida com isso automaticamente: quando detecta `--user-agent=` nos argumentos do navegador, usa `Emulation.setUserAgentOverride` para sincronizar a string User-Agent, plataforma e metadados completos de Client Hints em todas as camadas. Também injeta sobrescritas de `navigator.vendor` e `navigator.appVersion` via `Page.addScriptToEvaluateOnNewDocument` para garantir consistência em abas recém-abertas.

Para consistência de timezone e geolocalização (para corresponder à localização do IP do proxy), sobrescritas JavaScript podem definir `Intl.DateTimeFormat().resolvedOptions().timeZone` e `Date.prototype.getTimezoneOffset`. A flag `--lang` e `set_accept_languages()` configuram cabeçalhos de idioma. A opção `webrtc_leak_protection` previne que o WebRTC exponha o IP real por trás de um proxy.

O princípio geral é que o Pydoll fornece o fingerprint autêntico do navegador como linha de base, e o desenvolvedor só precisa garantir que as camadas configuráveis (User-Agent, timezone, idioma, geolocalização) sejam consistentes entre si e com as características do proxy.

## Referências

- Laperdrix, P., Rudametkin, W., & Baudry, B. (2016). Beauty and the Beast: Diverting Modern Web Browsers to Build Unique Browser Fingerprints. IEEE S&P.
- Mowery, K., & Shacham, H. (2012). Pixel Perfect: Fingerprinting Canvas in HTML5. USENIX Security.
- Eckersley, P. (2010). How Unique Is Your Web Browser? Privacy Enhancing Technologies Symposium.
- W3C Client Hints Infrastructure: https://wicg.github.io/client-hints-infrastructure/
- BrowserLeaks: https://browserleaks.com/
- CreepJS: https://abrahamjuliot.github.io/creepjs/
