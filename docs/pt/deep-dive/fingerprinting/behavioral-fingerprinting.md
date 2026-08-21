# Behavioral fingerprinting

O behavioral fingerprinting analisa como um usuário interage com uma página, e não quais ferramentas ele usa. Fingerprints de rede e de navegador podem ser forjados ao definir os valores certos, mas o comportamento humano segue padrões biomecânicos difíceis de replicar de forma convincente. Os sistemas de detecção coletam movimento do mouse, ritmo das teclas, comportamento de rolagem e sequências de interação, e então usam modelos estatísticos para separar humanos de automação. Esta página explica essas técnicas, a ciência por trás delas e como a humanização do Pydoll aborda cada uma.

## Análise de movimento do mouse

O movimento do mouse é um dos indicadores comportamentais mais fortes, porque o controle motor humano segue leis biomecânicas que uma automação simples não reproduz. Os sistemas de detecção coletam eventos `mousemove` (cada um com coordenadas x, y e um timestamp) e analisam a trajetória em busca de propriedades que separam o movimento orgânico do teletransporte programático do cursor.

### Lei de Fitts

A Lei de Fitts descreve o tempo necessário para mover um ponteiro até um alvo. A formulação de Shannon (MacKenzie, 1992) é a mais amplamente usada:

```
T = a + b * log2(D/W + 1)
```

`T` é o tempo de movimento, `a` é uma constante de início/reação, `b` é a velocidade inerente do dispositivo de entrada, `D` é a distância até o alvo e `W` é a largura do alvo. O logaritmo significa que dobrar a distância adiciona uma quantidade fixa de tempo, e reduzir o tamanho do alvo pela metade adiciona a mesma quantidade fixa.

A implicação para a detecção é direta. Humanos demoram mais para alcançar alvos pequenos e distantes, e alcançam alvos grandes e próximos rapidamente. Eles aceleram no início, atingem o pico de velocidade por volta do meio do caminho e desaceleram ao chegar. Um bot que se move em tempo constante independentemente da distância e do tamanho do alvo viola a Lei de Fitts e é trivialmente detectável. Os sistemas de detecção medem o tempo de movimento antes de cada clique, calculam o tempo que a Lei de Fitts prevê a partir da distância e do tamanho do alvo, e marcam movimentos que são muito mais rápidos do que o previsto ou que não mostram correlação entre distância/tamanho e tempo.

### Formato da trajetória

Os movimentos da mão humana entre dois pontos não são linhas retas. Abend, Bizzi e Morasso (1982) mostraram que os caminhos da mão são curvos por causa das articulações e músculos do braço. Flash e Hogan (1985) mostraram que os movimentos de alcance seguem trajetórias de mínimo jerk, minimizando a integral do jerk (a derivada da aceleração) ao longo do movimento. O perfil de velocidade tem formato de sino, descrito por um polinômio quíntico:

```
x(t) = x0 + (xf - x0) * (10t^3 - 15t^4 + 6t^5)
```

onde `t` é o tempo normalizado de 0 a 1 e `x0`/`xf` são as posições de início e fim. Isso gera uma aceleração suave a partir do repouso, pico de velocidade perto do meio do caminho e desaceleração suave de volta ao repouso.

Os sistemas de detecção analisam curvatura, velocidade e aceleração em busca de quatro indícios:

- **Caminhos em linha reta.** Curvatura zero em cada amostra é o sinal de bot mais óbvio; os caminhos humanos sempre curvam porque o braço gira em torno das articulações.
- **Velocidade constante.** Humanos mostram um perfil de velocidade em formato de sino. Velocidade constante indica interpolação linear, o padrão na maioria das ferramentas de automação.
- **Ausência de submovimentos.** Movimentos longos são construídos a partir de submovimentos sobrepostos (Meyer et al., 1988), cada um com seu próprio pico de velocidade. Um movimento de 500 pixels com um único pico suave é suspeito; os reais mostram de 2 a 4 picos.
- **Ausência de overshoot.** Humanos frequentemente ultrapassam o alvo em 5 a 15 pixels e corrigem de volta. Pousar exatamente no alvo toda vez é estatisticamente improvável.

### Entropia do movimento

A entropia aqui mede o quão imprevisível é o caminho. Os sistemas de detecção dividem a trajetória em segmentos, medem a mudança de direção em cada ponto e calculam a entropia de Shannon sobre a distribuição dessas mudanças. Uma linha reta tem entropia zero; uma caminhada aleatória tem entropia máxima; o movimento humano fica no meio, combinando intenção com variabilidade involuntária. Entropia baixa em muitos movimentos numa sessão é um forte sinal de bot, mesmo quando os movimentos individuais parecem plausivelmente curvos.

### Como o Pydoll humaniza o mouse

Com `humanize=True`, o Pydoll gera movimentos que respondem a cada um dos indícios acima. O caminho segue uma curva de Bezier cúbica com pontos de controle aleatorizados, então ele curva em vez de correr reto. A velocidade ao longo dele segue o perfil de mínimo jerk (`10t^3 - 15t^4 + 6t^5`), gerando a curva em formato de sino que a Lei de Fitts prevê, e a duração é calculada a partir da própria Lei de Fitts. O tremor fisiológico é adicionado como ruído de posição escalado inversamente à velocidade (mais visível quando o cursor se move devagar, combinando com a fisiologia real), o overshoot acontece com uma probabilidade definida antes de uma correção, e micropausas ocasionais simulam breves hesitações.

```python
await element.click(humanize=True)
await tab.mouse.click(500, 300, humanize=True)   # forma com coordenadas
```

O modelo de timing é configurável através de `MouseTimingConfig` atribuído a `tab.mouse.timing`. Veja [Human-like interactions](../../stealth/human-like-interactions.md) para o guia prático.

!!! note "O que isto não modela"
    O caminho do mouse do Pydoll é um único segmento de Bezier; ele não divide movimentos muito longos em múltiplos submovimentos. Para interações web típicas (abaixo de cerca de 500 pixels) isso é suficiente. Travessias diagonais de tela cheia são o caso em que os submovimentos importariam.

## Dinâmica de digitação

A dinâmica de digitação analisa o timing da entrada do teclado. A ideia é antiga: na década de 1850, os operadores de telégrafo reconheciam uns aos outros pelo seu "fist" no Morse, um padrão característico de timing. Os sistemas modernos medem a mesma coisa com precisão de milissegundos através dos eventos `keydown` e `keyup`.

### Características de timing

As duas medições fundamentais são o dwell time (do `keydown` ao `keyup` numa mesma tecla, geralmente de 50 a 200ms) e o flight time (de soltar uma tecla até pressionar a próxima, geralmente de 80 a 400ms). O dwell e o flight de um par consecutivo de teclas é uma latência de dígrafo, e ela não é uniforme, porque digitar é uma habilidade motora em que as sequências comuns residem na memória procedural:

- **Alternância de mãos.** Bigramas digitados com mãos alternadas (como "th" no QWERTY) são mais rápidos do que os de mesma mão (como "de"), porque a segunda mão começa a se mover enquanto a primeira ainda está terminando.
- **Deslocamento dos dedos.** Transições de home-row para home-row são as mais rápidas; alcançar a linha de cima ou de baixo custa tempo proporcional à distância.
- **Independência dos dedos.** Combinações de anelar e mindinho são mais lentas do que de indicador e médio, porque esses dedos compartilham tendões e se movem com menos independência.
- **Frequência.** Bigramas digitados com frequência ("th", "er", "in") saem mais rápido da memória motora, independentemente do layout.

### Sinais de detecção

- **Dwell time zero ou constante.** Muitas ferramentas disparam `keydown` e `keyup` com atraso quase nulo; pressionamentos reais têm dwell mensurável e variável.
- **Flight time uniforme.** Um intervalo fixo entre as teclas produz um timing perfeitamente regular, trivial de detectar. Os flight times humanos variam por bigrama, fadiga e carga.
- **Ausência de erros de digitação.** Em mais de 50 caracteres, uma ausência total de backspace é incomum; humanos erram em torno de 1 a 5%.
- **Velocidade sobre-humana.** Digitação sustentada acima de 150 WPM está além de todos, exceto os digitadores de elite, então qualquer coisa mais rápida é marcada.

### Como o Pydoll humaniza a digitação

Com `type_text(humanize=True)`, os atrasos entre as teclas são extraídos de uma distribuição, e não de um intervalo fixo. A pontuação recebe um atraso extra, simulando a pausa que um digitador faz na estrutura da frase; pausas ocasionais de reflexão e pausas de distração mais raras simulam momentos de pensamento ou interrupção. Erros de digitação realistas ocorrem em torno de 2% por caractere ao longo de cinco tipos de erro ponderados pela frequência no mundo real (tecla adjacente, transposição, pressionamento duplo, caractere pulado, espaço perdido), cada um seguido por uma sequência natural de correção.

```python
await element.type_text('Hello, world!', humanize=True)
```

Veja [Human-like interactions](../../stealth/human-like-interactions.md) para saber como ajustá-lo.

!!! note "O que isto não modela"
    O Pydoll usa atrasos aleatórios variáveis, não um timing consciente de bigramas, e não modela o dwell por tecla nem as diferenças de alternância de mãos. Para preenchimento de formulários e consultas de busca isso é suficiente. Evadir biometria de digitação de nível de autenticação exigiria um modelo de timing customizado.

## Comportamento de rolagem

O fingerprinting de rolagem analisa como um usuário se move pelo conteúdo da página. Um `window.scrollTo()` programático é um salto instantâneo e discreto, enquanto uma rolagem humana (roda, trackpad ou toque) é um fluxo de pequenos eventos incrementais com momentum e desaceleração.

As rodas do mouse produzem eventos `wheel` discretos com deltas consistentes (frequentemente 100 ou 120 pixels por entalhe) em intervalos irregulares. Os trackpads produzem muitos eventos pequenos com deltas decrescentes que simulam momentum. O toque é parecido, com deltas iniciais maiores e uma cauda de desaceleração mais longa. Os sistemas de detecção leem a distribuição dos deltas, o timing entre eventos e a curva de desaceleração, e procuram por:

- **Rolagem instantânea.** `scrollTo`/`scrollBy` com valores grandes muda a posição de rolagem num único frame, sem eventos intermediários.
- **Deltas uniformes.** Valores de delta constantes não têm a variação de 10 a 30% da rolagem real.
- **Ausência de desaceleração.** A rolagem humana, especialmente em trackpads, continua se movendo depois que o dedo levanta, com velocidade decrescendo exponencialmente. Uma automação que para bruscamente não tem cauda.
- **Ausência de mudanças de direção.** Humanos rolam demais e corrigem, ou pausam para ler. Rolagem unidirecional em velocidade constante é suspeita.

A rolagem humanizada do Pydoll responde a esses pontos: ela segue uma curva de easing de Bezier para aceleração e desaceleração naturais, adiciona jitter por frame aos deltas, insere micropausas ocasionais, às vezes ultrapassa e corrige, e quebra distâncias longas em múltiplos gestos de "flick" em vez de um movimento contínuo.

```python
from pydoll.constants import ScrollPosition

await tab.scroll.by(ScrollPosition.DOWN, 800, humanize=True)
```

## Outros sinais comportamentais

Além de mouse, teclado e rolagem, alguns sistemas observam vários outros sinais.

**Foco e visibilidade.** A Page Visibility API (`document.visibilityState`) e os eventos de foco revelam se o usuário está visualizando a página ativamente. Uma sessão real tem trocas de aba, minimizações e períodos ociosos; um script que mantém foco contínuo por horas sem um único blur é anômalo.

**Padrões de ociosidade.** Usuários reais pausam para ler e pensar. Uma sessão em que cada ação segue a anterior dentro de 100 a 500ms, sem intervalos mais longos, é estatisticamente distinta da navegação humana, na qual ociosidades de 2 a 30 segundos são normais.

**Integridade da sequência de eventos.** Um clique real produz `pointerdown`, `mousedown`, `pointerup`, `mouseup`, `click` em ordem, precedido por eventos de movimento aproximando-se do alvo. Ferramentas que disparam um `click` cru sem nenhum movimento anterior são detectáveis. O Pydoll dispara a entrada através da própria simulação de entrada do Chrome via CDP, então ele gera a mesma cadeia completa de eventos que a entrada real.

## Detecção por machine learning

Os sistemas anti-bot modernos (DataDome, Akamai Bot Manager, Cloudflare Bot Management, HUMAN Security) não dependem de regras de limiar. Eles treinam modelos em milhões de sessões reais e de bots conhecidos, aprendendo a separá-las por mais de 50 características ao mesmo tempo: a distribuição conjunta de velocidade e curvatura, a correlação entre velocidade de digitação e taxa de erro, a relação entre profundidade de rolagem e tempo de leitura, o ritmo geral de uma sessão. Uma execução que passa em cada checagem individual mas tem correlações sutilmente erradas entre as características ainda pode ser marcada.

A consequência prática é que o realismo comportamental precisa ser consistente entre os tipos de interação, não apenas plausível um de cada vez. O `humanize=True` do Pydoll dá uma camada de humanização coerente entre mouse, teclado e rolagem, mas a plausibilidade de nível mais alto ainda é sua: adicione atrasos de leitura entre carregamentos de página, varie o ritmo de um fluxo de múltiplas páginas e inclua períodos ociosos naturais.

## Relacionado

- [Network fingerprinting](network-fingerprinting.md): a camada de protocolo (TCP/IP, TLS, HTTP/2).
- [Browser fingerprinting](browser-fingerprinting.md): canvas, WebGL, fontes e navigator.
- [Human-like interactions](../../stealth/human-like-interactions.md): o guia prático para `humanize=True`.

## Referências

- Fitts, P. M. (1954). The Information Capacity of the Human Motor System in Controlling the Amplitude of Movement. Journal of Experimental Psychology.
- MacKenzie, I. S. (1992). Fitts' Law as a Research and Design Tool in Human-Computer Interaction. Human-Computer Interaction.
- Flash, T., & Hogan, N. (1985). The Coordination of Arm Movements: An Experimentally Confirmed Mathematical Model. Journal of Neuroscience.
- Abend, W., Bizzi, E., & Morasso, P. (1982). Human Arm Trajectory Formation. Brain.
- Meyer, D. E., Abrams, R. A., Kornblum, S., Wright, C. E., & Smith, J. E. K. (1988). Optimality in Human Motor Performance. Psychological Review.
- Ahmed, A. A. E., & Traore, I. (2007). A New Biometric Technology Based on Mouse Dynamics. IEEE TDSC.
