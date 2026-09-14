# Os limites do spoofing

A injeção de fingerprint muda o que o navegador reporta, mas nem todo sinal pode ser mudado, e forçar o errado torna você mais fácil de detectar, não mais difícil. Esta página traça a linha: quais sinais um spoof move de forma limpa, quais ele não consegue mover de jeito nenhum, e por que sobrescrever os que ele não consegue deixa uma contradição que um detector lê na hora.

É a teoria por trás do checklist de [Injeção de fingerprint](../../stealth/fingerprint-injection.md). Leia aquele primeiro para os passos práticos; leia este para entender por que o checklist tem a forma que tem.

## Overrides nativos são lidos como a verdade

Um sinal do navegador costuma ter mais de um caminho de leitura. `matchMedia('(color-gamut: p3)')` e uma regra CSS `@media (color-gamut: p3)` fazem a mesma pergunta, e a resposta vem do mesmo lugar: o motor de renderização, em C++, abaixo do JavaScript que você consegue alcançar.

É isso que separa um bom override de um detectável:

- Um **override nativo** muda o valor no motor. O Pydoll aplica esses através dos domínios `Emulation` e `Browser` do CDP, para o User-Agent e `navigator.platform` / `appVersion` / `vendor` / `languages`, os Client Hints, o fuso horário, a geolocalização, a tela, o locale, o `hardwareConcurrency`, o toque, as permissões e as media features CSS. Todo caminho de leitura então retorna o novo valor, e eles concordam. Não há nenhum wrapper JavaScript para inspecionar, nem nenhum frame JavaScript num stack trace.
- Um **override em JavaScript** envolve uma API, um getter de `navigator` ou o `matchMedia`. Ele muda esse único caminho. Qualquer outro caminho que leia o mesmo sinal ainda retorna o valor real.

Uma media feature vive no `MediaValues` do motor, e ambos os caminhos de leitura resolvem contra ele. Alterne o tipo de override abaixo para ver quais caminhos cada um alcança:

<iframe scrolling="no" src="/docs/resources/visuals/media-read-paths.html" aria-label="Um override de CDP edita o MediaValues do motor, então o matchMedia e a cascata CSS mudam ambos; um override em JavaScript envolve apenas o matchMedia, deixando o caminho CSS lendo o valor real" style="width: 100%; height: 430px; border: 0;" loading="lazy"></iframe>

Um override de CDP edita o `MediaValues`, então o `matchMedia` e a cascata `@media` retornam ambos o novo valor. Um override em JavaScript substitui a função `matchMedia`; a cascata nunca a chama, então o CSS continua resolvendo contra o `MediaValues` real. Essa lacuna é a contradição.

A demonstração abaixo roda no seu próprio display. Ambos os cartões leem o seu `dynamic-range` real e concordam. Aplique um override em JavaScript e só o `matchMedia` mente; a regra `@media` do motor continua reportando a verdade.

<iframe scrolling="no" src="/docs/resources/visuals/js-override-lie.html" aria-label="o matchMedia e uma regra CSS @media leem o mesmo dynamic-range; um override em JavaScript faz apenas o matchMedia mentir enquanto o caminho CSS permanece verdadeiro" style="width: 100%; height: 340px; border: 0;" loading="lazy"></iframe>

É exatamente por isso que o Pydoll não forja o `dynamic-range`. O Chrome mantém uma allowlist fixa de media features sobrescrevíveis. No `MediaFeatureOverrides::SetOverride` do Blink, sete nomes são tratados, `color-gamut`, `prefers-color-scheme`, `prefers-contrast`, `prefers-reduced-motion`, `prefers-reduced-data`, `prefers-reduced-transparency` e `forced-colors`, e qualquer outro nome passa direto e não muda nada. `dynamic-range`, `inverted-colors` e `monochrome` não têm ramo ali, então o comando CDP é aceito e descartado silenciosamente. É um caminho de código ausente no motor, não um problema de formato de valor.

O Pydoll expõe seis dos sete. A exceção é o `prefers-reduced-data`: ele está na allowlist mas foi lançado desativado no Chrome, então o `matchMedia` não reporta correspondência para valor nenhum, e defini-lo alegaria algo que um Chrome real nunca retorna. A única alavanca que sobra para as features não listadas é o JavaScript, que só consegue mentir em um caminho, então o Pydoll deixa o `dynamic-range` real e pede que você combine o `color-gamut` com ele.

!!! note "Quando um override em JavaScript é seguro"
    O Pydoll usa sim overrides em JS, para `deviceMemory`, `maxTouchPoints`, WebGL, dispositivos de mídia, vozes, fontes e os extras da área de trabalho em headful. Eles são usados apenas onde o CDP não consegue alcançar o sinal **e** nenhum segundo caminho de leitura os contradiz, e cada um é escrito na forma nativa: `[native code]` sob `toString`, o prototype real, nenhuma propriedade própria, o nativo original chamado primeiro para que um receiver estranho lance o `Illegal invocation` real, e valores que continuam fisicamente possíveis (veja [Nativo primeiro, JavaScript por último](../../stealth/fingerprint-injection.md#native-first)). A regra: um override em JS é seguro apenas quando é a única fonte da verdade para aquele sinal.

    Uma denúncia sobrevive mesmo a isso: um getter JavaScript é uma função, então um erro lançado enquanto ele roda carrega um frame extra de stack que um accessor nativo não tem. É por isso que o Pydoll move tudo o que consegue para overrides nativos e mantém o conjunto em JavaScript tão pequeno quanto o Chrome permite.

## O piso intransponível: sinais que nenhum override consegue forjar {#the-hard-floor-signals-no-override-can-fake}

Alguns sinais não são um valor que o navegador armazena. Eles são a saída de uma computação que o detector roda no seu hardware real e depois passa por hash:

- O **canvas** desenha um texto e formas fixos num canvas fora da tela, lê os pixels de volta com `getImageData` e faz o hash deles. O anti-aliasing sub-pixel depende da GPU, do driver e da renderização de texto do SO, então o hash é estável numa máquina e difere entre máquinas.
- O **áudio** renderiza um tom através de um `OfflineAudioContext`, um oscilador dentro de um `DynamicsCompressorNode`, lê a saída com `getChannelData` e faz o hash dela. O resultado de DSP em ponto flutuante varia por plataforma.
- O **WebGL e o WebGPU** renderizam uma cena, fazem o hash da imagem e cronometram quanto tempo a GPU levou.

Não há override de CDP para nenhum desses, e um override em JavaScript não consegue alcançar a saída passada por hash, apenas a API ao redor dela. O Chrome até expõe um domínio WebAudio no DevTools Protocol, mas ele só observa o grafo de áudio; não tem comando para reescrever as amostras. Nem mesmo o protocolo consegue mover essa camada.

A saída ingênua, dar hook na API de readback para adicionar ruído de modo que o hash mude a cada leitura, é ela mesma a denúncia. Uma verificação padrão renderiza o mesmo canvas duas vezes e compara: uma GPU real retorna pixels idênticos byte a byte nas duas vezes, então um valor que difere entre duas leituras é um hook em JavaScript, e essa instabilidade marca a sessão de forma mais clara do que um hash real e estável jamais marcaria.

!!! warning "Não adicione ruído de canvas ou áudio"
    Um fingerprint real e estável é menos suspeito do que um que oscila entre leituras. Aleatorizar a saída de canvas ou áudio marca a sessão como automatizada em vez de escondê-la.

O que esses sinais expõem é *qual máquina*, não *que é um bot*. Para um scraper isso significa que eles importam para vincular suas sessões umas às outras entre execuções, não para um veredito único de bot. O único jeito de torná-los coerentes com um dispositivo alegado é rodar naquele hardware.

## Um spoof é tão forte quanto sua camada mais fraca

Um fingerprint é lido entre camadas e correlacionado. Sobrescrever uma camada enquanto outra ainda reporta a verdade é uma contradição, e uma contradição pontua pior do que um navegador sem modificações.

Tome uma GPU. Um perfil de WebGL nomeia uma placa, mas a mesma GPU é descrita uma segunda vez pelo WebGPU: `navigator.gpu.requestAdapter()` expõe `adapter.info` (`vendor`, `architecture`), cerca de trinta `adapter.limits` e um conjunto de features. Aplicando um perfil de Windows com NVIDIA neste host (Apple M4, Chrome 152) com apenas a seção de WebGL definida, medido:

| Sinal | Lê | Vem de |
|--------|-------|------------|
| String do renderer do WebGL | `ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 ...)` | o override |
| Vendor do adapter do WebGPU | `apple` | a GPU real |
| `maxBufferSize` do WebGPU | `4294967292` | a GPU real |
| `maxComputeWorkgroupStorageSize` do WebGPU | `32768` | a GPU real |
| Hash de canvas, este perfil vs o perfil de macOS | idêntico | a GPU real |

O WebGL diz NVIDIA; o WebGPU e o canvas dizem Apple. Os fornecedores de detecção cruzam exatamente esse par. A seção `webgpu` do perfil fecha a metade reportada: o adapter real é mantido, então `requestDevice()` e a renderização continuam funcionando, e os objetos `info`, `limits` e `features` dele respondem com os valores do perfil através de getters nos prototypes reais de `GPUAdapterInfo` / `GPUSupportedLimits` / `GPUSupportedFeatures`, sem propriedades próprias e com os brand checks nativos intactos.

### O que um perfil de WebGPU tem que ser

O conjunto de limites e a lista de features são uma assinatura física de GPU, driver e backend, e o Chrome não os publica por placa. Um conjunto adivinhado é mais fácil de sinalizar do que a verdade, então os valores têm que ser uma captura de um dispositivo real da classe alegada, lida com `requestAdapter()` naquela máquina (o perfil de exemplo de macOS é uma captura de um Apple M4). O que nenhuma seção consegue mover é o que a GPU computa: uma carga de WebGPU renderizada ou cronometrada continua descrevendo o host. Num host sem adapter nenhum não há onde ancorar os valores, e o perfil não pode alegar uma GPU.

É por isso que o [checklist de Injeção de fingerprint](../../stealth/fingerprint-injection.md#making-a-profile-pass) insiste que a família de GPU do perfil combine com o host. Você pode mover todo valor reportado, mas a saída renderizada permanece real, então os valores têm que descrever hardware da classe que está de fato ali.

### O sistema operacional é o que você não consegue mover

O sinal mais claro que você só consegue combinar, nunca forjar, é o sistema operacional. Defina o User-Agent, o `navigator.platform` e os Client Hints e o navegador diz Windows de imediato, mas o sistema operacional vaza através de camadas que nenhum override alcança, e através de mais de uma ao mesmo tempo.

A mais distante do alcance é a stack TCP/IP do kernel. O pacote SYN de toda conexão carrega o TTL inicial (64 no macOS e no Linux, 128 no Windows), o tamanho e a escala da janela TCP e a ordem das opções, tudo definido pelo kernel do host antes de qualquer JavaScript rodar. Um User-Agent de Windows chegando por uma conexão com TTL 64 é uma contradição lida no servidor, a partir dos próprios pacotes, e nenhum override de CDP ou JavaScript a toca. O [Fingerprinting de rede](network-fingerprinting.md) cobre essa stack em profundidade. Se é esse o sinal que o Cloudflare pondera quando um perfil de Windows num Mac falha no managed challenge ainda não foi isolado: aquela execução mudou fontes, canvas, WebGPU e a stack do kernel de uma vez. O experimento que os separa é um perfil de Windows num Mac através de um proxy hospedado em Windows (remove apenas a contradição de TCP).

A renderização carrega o sistema operacional também, então o canvas faz parte da resposta. O canvas e as fontes desenham através da renderização de texto do SO, CoreText no macOS, DirectWrite no Windows, então um canvas renderizado num Mac sob um perfil de Windows já descreve o sistema operacional errado. Esse vazamento de canvas é real mas não forjável, e na execução medida do Cloudflare ele não foi o sinal decisivo, a stack do kernel foi. O mesmo canvas resultou no hash `d65506c6...` tanto sob o perfil de Windows quanto sob o de macOS neste Mac, enquanto o `navigator.platform` lia `Win32` e `MacIntel`. Hashes idênticos só mostram que o perfil não alterou o canvas, não que o canvas concorda com a alegação de Windows; ele é o do Mac real, um sinal renderizado vindo do [piso intransponível](#the-hard-floor-signals-no-override-can-fake). A stack TCP/IP do kernel por baixo vaza o sistema operacional uma segunda vez, e é igualmente intocável. Como um challenge real pondera esses sinais, camada por camada, está no [estudo de caso do Cloudflare](cloudflare-challenge.md).

Um proxy de encaminhamento é a única alavanca. Ele reorigina a conexão TCP a partir do kernel do proxy, então o sistema operacional observado passa a ser o do host do proxy. Um perfil de Windows então precisa de um proxy rodando em Windows; um proxy Linux dá uma assinatura de Linux e a contradição volta.

!!! note "A única regra por trás de tudo isso"
    Combine o perfil com o host. Nunca alegue um hardware ou um sistema operacional que você não tem. Toda regra no checklist é um caso especial dela.

## O que você consegue de fato mover

Os sinais que você consegue mudar de forma limpa são os que um override nativo alcança, ou que um override em JavaScript consegue possuir sem um segundo caminho o contradizer: identidade (User-Agent, platform, Client Hints), fuso horário, locale, tela, `hardwareConcurrency`, `deviceMemory`, permissões e as media features CSS. Torne esses coerentes uns com os outros e com o seu IP e sistema operacional.

O piso intransponível, canvas e áudio e GPU, você só torna coerente rodando em hardware real e compatível. Tudo no meio é uma troca que pode sair pela culatra, então gaste o esforço em consistência, não em forjar mais.

!!! note "Tudo isto é um modelo, não um veredito"
    Toda checagem nesta página vem de pesquisa pública, de write-ups de fornecedores e de agentes de engenharia reversa. Ela descreve o que um detector *pode* ler, não o que um site específico *lê* de fato. Cada sistema anti-bot tem o próprio conjunto de checagens e os próprios pesos, uma pequena inconsistência pode nunca ser olhada, e um perfil simples com três campos muitas vezes passa onde um totalmente ajustado nem era necessário. Trate a coerência como um orçamento a gastar onde um alvo prova que importa, e meça cada site por conta própria: rode o perfil contra ele, mude uma coisa, rode de novo.

## O que ainda está em aberto

Passado o piso intransponível, as lacunas restantes são de ambiente, não de overrides, e cada uma tem uma solução conhecida fora do navegador:

- **Fontes.** A sonda de fontes baseada em largura lê as fontes instaladas no host. Alegar Windows a partir do Linux significa instalar o conjunto de fontes do Windows e listar exatamente isso em `available_fonts`. A rasterização de texto ainda difere (FreeType e DirectWrite não desenham os mesmos pixels a partir da mesma fonte), então um canvas que desenha texto continua descrevendo o host.
- **GPU.** Parâmetros, extensões e precisão do WebGL e o adapter do WebGPU podem todos ser definidos a partir de uma captura real, mas a saída renderizada e cronometrada continua sendo a do host. Um host com uma GPU do mesmo vendor do perfil é o único jeito de fazê-los concordar; um host sem GPU não pode alegar uma.
- **O kernel.** Uma saída de proxy rodando o sistema operacional alegado, ou um reescritor de pacotes no host, é a única alavanca para o SYN. Quais detectores o ponderam é a medição em aberto acima.
- **O resíduo em JavaScript.** Os getters para os quais o Chrome não oferece comando mantêm o frame extra de stack. Menos deles é a única direção.

## Relacionado

- [Injeção de fingerprint](../../stealth/fingerprint-injection.md): o guia prático para aplicar um perfil coerente.
- [Fingerprinting de navegador](browser-fingerprinting.md): a superfície de detecção que esses overrides tocam.
- [GPU, containers e o que um perfil não alcança](gpu-and-containers.md): a divisão reportado/computado aplicada a hardware, containers e Xvfb.
- [Auditando um fingerprint](auditing.md): meça quais dos seus sinais vazam, e veja o que um detector comercial real lê.
