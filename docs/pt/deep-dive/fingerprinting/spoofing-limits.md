# Os limites do spoofing

A injeção de fingerprint muda o que o navegador reporta, mas nem todo sinal pode ser mudado, e forçar o errado torna você mais fácil de detectar, não mais difícil. Esta página traça a linha: quais sinais um spoof move de forma limpa, quais ele não consegue mover de jeito nenhum, e por que sobrescrever os que ele não consegue deixa uma contradição que um detector lê na hora.

É a teoria por trás do checklist de [Injeção de fingerprint](../../stealth/fingerprint-injection.md). Leia aquele primeiro para os passos práticos; leia este para entender por que o checklist tem a forma que tem.

## Overrides nativos são lidos como a verdade

Um sinal do navegador costuma ter mais de um caminho de leitura. `matchMedia('(color-gamut: p3)')` e uma regra CSS `@media (color-gamut: p3)` fazem a mesma pergunta, e a resposta vem do mesmo lugar: o motor de renderização, em C++, abaixo do JavaScript que você consegue alcançar.

É isso que separa um bom override de um detectável:

- Um **override nativo** muda o valor no motor. O Pydoll aplica esses através do domínio `Emulation` do CDP, para o User-Agent, o fuso horário, a tela, o locale, o `hardwareConcurrency` e as media features CSS. Todo caminho de leitura então retorna o novo valor, e eles concordam. Não há nenhum wrapper JavaScript para inspecionar.
- Um **override em JavaScript** envolve uma API, um getter de `navigator` ou o `matchMedia`. Ele muda esse único caminho. Qualquer outro caminho que leia o mesmo sinal ainda retorna o valor real.

Uma media feature vive no `MediaValues` do motor, e ambos os caminhos de leitura resolvem contra ele. Alterne o tipo de override abaixo para ver quais caminhos cada um alcança:

<iframe src="/docs/resources/visuals/media-read-paths.html" aria-label="Um override de CDP edita o MediaValues do motor, então o matchMedia e a cascata CSS mudam ambos; um override em JavaScript envolve apenas o matchMedia, deixando o caminho CSS lendo o valor real" style="width: 100%; height: 430px; border: 0;" loading="lazy"></iframe>

Um override de CDP edita o `MediaValues`, então o `matchMedia` e a cascata `@media` retornam ambos o novo valor. Um override em JavaScript substitui a função `matchMedia`; a cascata nunca a chama, então o CSS continua resolvendo contra o `MediaValues` real. Essa lacuna é a contradição.

A demonstração abaixo roda no seu próprio display. Ambos os cartões leem o seu `dynamic-range` real e concordam. Aplique um override em JavaScript e só o `matchMedia` mente; a regra `@media` do motor continua reportando a verdade.

<iframe src="/docs/resources/visuals/js-override-lie.html" aria-label="o matchMedia e uma regra CSS @media leem o mesmo dynamic-range; um override em JavaScript faz apenas o matchMedia mentir enquanto o caminho CSS permanece verdadeiro" style="width: 100%; height: 340px; border: 0;" loading="lazy"></iframe>

É exatamente por isso que o Pydoll não forja o `dynamic-range`. O Chrome mantém uma allowlist fixa de media features sobrescrevíveis. No `MediaFeatureOverrides::SetOverride` do Blink, sete nomes são tratados, `color-gamut`, `prefers-color-scheme`, `prefers-contrast`, `prefers-reduced-motion`, `prefers-reduced-data`, `prefers-reduced-transparency` e `forced-colors`, e qualquer outro nome passa direto e não muda nada. `dynamic-range`, `inverted-colors` e `monochrome` não têm ramo ali, então o comando CDP é aceito e descartado silenciosamente. É um caminho de código ausente no motor, não um problema de formato de valor.

O Pydoll expõe seis dos sete. A exceção é o `prefers-reduced-data`: ele está na allowlist mas foi lançado desativado no Chrome, então o `matchMedia` não reporta correspondência para valor nenhum, e defini-lo alegaria algo que um Chrome real nunca retorna. A única alavanca que sobra para as features não listadas é o JavaScript, que só consegue mentir em um caminho, então o Pydoll deixa o `dynamic-range` real e pede que você combine o `color-gamut` com ele.

!!! note "Quando um override em JavaScript é seguro"
    O Pydoll usa sim overrides em JS, para `deviceMemory`, strings do WebGL, plugins e mais. Eles são seguros porque o CDP não consegue alcançar esses sinais **e** nenhum segundo caminho de leitura os contradiz, e cada um é reforçado para sobreviver à inspeção de `toString`, de prototype e de worker (veja [Detectando overrides em JavaScript](../../stealth/fingerprint-injection.md#detecting-javascript-overrides)). A regra: um override em JS é seguro apenas quando é a única fonte da verdade para aquele sinal.

## O piso intransponível: sinais que nenhum override consegue forjar

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

Tome uma GPU. O Pydoll sobrescreve a string do renderer do WebGL, então um perfil pode nomear uma placa NVIDIA, mas não toca no WebGPU. Aplicando o perfil de Windows neste host (Apple M3, Chrome 151) e lendo ambas as APIs, medido:

| Sinal | Lê | Vem de |
|--------|-------|------------|
| String do renderer do WebGL | `ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 ...)` | o override |
| Vendor do adapter do WebGPU | `apple` | a GPU real |
| `maxBufferSize` do WebGPU | `4294967292` | a GPU real |
| `maxComputeWorkgroupStorageSize` do WebGPU | `32768` | a GPU real |
| Hash de canvas, este perfil vs o perfil de macOS | idêntico | a GPU real |

O WebGL diz NVIDIA; o WebGPU, seus limites e o canvas dizem todos Apple. O override moveu uma string e deixou todo o resto dos sinais renderizados e reportados descrevendo a GPU real, então um perfil de Windows em hardware Apple contradiz a si mesmo. Uma GPU forjada pela metade é mais detectável do que a real.

### Por que o Pydoll deixa o WebGPU em paz

Você poderia tentar fechar essa lacuna forjando o WebGPU para combinar, a string do vendor e depois os cerca de trinta limites do adapter. O Pydoll construiu exatamente isso e reverteu. Cada limite tem que ser um valor fisicamente real para a placa que você alega, a mesma restrição que faz de um parâmetro errado do WebGL uma denúncia; os conjuntos reais de limites por GPU não são publicados, então você estaria adivinhando; a lista muda a cada versão do Chrome; e nem mesmo um conjunto perfeito consegue mover o hash de timing da GPU, que é renderizado, não reportado.

Então a decisão honesta de engenharia foi não forjar essa camada de jeito nenhum. Perseguir uma coerência que você não consegue manter troca um ganho pequeno e frágil por um grande custo de manutenção e um jeito novo de ser pego. O Pydoll sobrescreve a string do renderer do WebGL e deixa o WebGPU e a saída renderizada reais, o que significa que o perfil tem que nomear a família de GPU que está de fato presente.

É por isso que o [checklist de Injeção de fingerprint](../../stealth/fingerprint-injection.md#checklist) insiste que o sistema operacional e a GPU do perfil combinem com o host. Você pode mover uma string, mas a saída renderizada permanece real, então a string tem que descrever o hardware que está de fato ali.

### O sistema operacional é o que você não consegue mover

O sinal mais claro que você só consegue combinar, nunca forjar, é o sistema operacional. Defina o User-Agent, o `navigator.platform` e os Client Hints e o navegador diz Windows de imediato, mas o sistema operacional vaza através de camadas que nenhum override alcança, e através de mais de uma ao mesmo tempo.

A decisiva é a stack TCP/IP do kernel. O pacote SYN de toda conexão carrega o TTL inicial (64 no macOS e no Linux, 128 no Windows), o tamanho e a escala da janela TCP e a ordem das opções, tudo definido pelo kernel do host antes de qualquer JavaScript rodar. Um User-Agent de Windows chegando por uma conexão com TTL 64 é uma contradição lida na camada de transporte, e nenhum override de CDP ou JavaScript a toca. O [Fingerprinting de rede](network-fingerprinting.md) cobre essa stack em profundidade; é por isso que um perfil de Windows num Mac falha no managed challenge do Cloudflare.

A renderização carrega o sistema operacional também, através da renderização de texto (CoreText no macOS, DirectWrite no Windows), então é justo perguntar se o canvas é a entrega. Não é, neste caso. O mesmo canvas resultou no hash `d65506c6...` tanto sob o perfil de Windows quanto sob o perfil de macOS neste Mac, enquanto o `navigator.platform` reportou corretamente `Win32` e `MacIntel`. O canvas renderiza no Mac real de qualquer forma, então os pixels são idênticos, reais e não uma contradição. O que denuncia a incompatibilidade é a stack do kernel por baixo, não os pixels. O detalhamento medido, camada por camada, está no [estudo de caso de incompatibilidade de sistema operacional](../../stealth/fingerprint-injection.md#case-study-an-os-mismatch-triggering-cloudflares-managed-challenge).

Um proxy de encaminhamento é a única alavanca. Ele reorigina a conexão TCP a partir do kernel do proxy, então o sistema operacional observado passa a ser o do host do proxy. Um perfil de Windows então precisa de um proxy rodando em Windows; um proxy Linux dá uma assinatura de Linux e a contradição volta.

!!! note "A única regra por trás de tudo isso"
    Combine o perfil com o host. Nunca alegue um hardware ou um sistema operacional que você não tem. Toda regra no checklist é um caso especial dela.

## O que você consegue de fato mover

Os sinais que você consegue mudar de forma limpa são os que um override nativo alcança, ou que um override em JavaScript consegue possuir sem um segundo caminho o contradizer: identidade (User-Agent, platform, Client Hints), fuso horário, locale, tela, `hardwareConcurrency`, `deviceMemory` e as media features CSS. Torne esses coerentes uns com os outros e com o seu IP e sistema operacional.

O piso intransponível, canvas e áudio e GPU, você só torna coerente rodando em hardware real e compatível. Tudo no meio é uma troca que pode sair pela culatra, então gaste o esforço em consistência, não em forjar mais.

## Relacionado

- [Injeção de fingerprint](../../stealth/fingerprint-injection.md): o guia prático para aplicar um perfil coerente.
- [Fingerprinting de navegador](browser-fingerprinting.md): a superfície de detecção que esses overrides tocam.
- [Auditando um fingerprint](auditing.md): meça quais dos seus sinais vazam, e veja o que um detector comercial real lê.
