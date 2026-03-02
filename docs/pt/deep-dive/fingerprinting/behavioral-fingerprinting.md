# Fingerprinting Comportamental

O fingerprinting comportamental analisa como os usuários interagem com aplicações web, em vez de quais ferramentas eles usam. Enquanto fingerprints de rede e navegador podem ser falsificados definindo os valores corretos, o comportamento humano segue padrões biomecânicos difíceis de replicar de forma convincente. Sistemas de detecção coletam movimentos de mouse, tempos de digitação, comportamento de scroll e sequências de interação, e então usam modelos estatísticos para distinguir humanos de automação.

Este documento cobre as técnicas de detecção, a ciência por trás delas, e como os recursos de humanização do Pydoll abordam cada vetor.

!!! info "Navegação do Módulo"
    - [Network Fingerprinting](./network-fingerprinting.md): Fingerprinting de protocolo TCP/IP, TLS, HTTP/2
    - [Browser Fingerprinting](./browser-fingerprinting.md): Canvas, WebGL, propriedades do navigator
    - [Técnicas de Evasão](./evasion-techniques.md): Contramedidas práticas

## Análise de Movimento do Mouse

O movimento do mouse é um dos indicadores comportamentais mais poderosos porque o controle motor humano segue leis biomecânicas que automação simples não consegue replicar. Sistemas de detecção coletam eventos `mousemove` (cada um contendo coordenadas x, y e um timestamp) e analisam a trajetória em busca de propriedades que distinguem movimento orgânico de teleporte programático do cursor.

### Lei de Fitts

A Lei de Fitts descreve o tempo necessário para mover um ponteiro até um alvo. A formulação de Shannon (MacKenzie, 1992), que é a versão mais amplamente utilizada, estabelece:

```
T = a + b * log2(D/W + 1)
```

Onde `T` é o tempo de movimento, `a` é uma constante representando tempo de reação/início, `b` é uma constante representando a velocidade inerente do dispositivo de entrada, `D` é a distância até o alvo, e `W` é a largura (tamanho) do alvo. A relação logarítmica significa que dobrar a distância adiciona uma quantidade fixa de tempo, enquanto reduzir pela metade o tamanho do alvo adiciona a mesma quantidade fixa.

As implicações para detecção de bots são significativas. Humanos levam mais tempo para alcançar alvos pequenos e distantes e alcançam alvos grandes e próximos rapidamente. Eles aceleram no início de um movimento, atingem velocidade máxima aproximadamente no meio do caminho e desaceleram ao se aproximar do alvo. Bots que movem o cursor em tempo constante independentemente da distância e tamanho do alvo violam a Lei de Fitts e são trivialmente detectáveis.

Sistemas de detecção medem o tempo de movimento para cada evento de clique, calculam o tempo esperado a partir da distância e tamanho do alvo, e sinalizam movimentos significativamente mais rápidos do que a Lei de Fitts prevê ou que não mostram correlação entre distância/tamanho e tempo de movimento.

### Forma da Trajetória

Movimentos humanos da mão entre dois pontos não são linhas retas. A pesquisa de Abend, Bizzi e Morasso (1982) mostrou que os caminhos das mãos são tipicamente curvados devido a restrições biomecânicas das articulações e músculos do braço. Flash e Hogan (1985) demonstraram que movimentos de alcance humanos seguem trajetórias de jerk mínimo, onde a trajetória minimiza a integral do jerk (a derivada da aceleração) ao longo da duração do movimento. O perfil de velocidade resultante tem forma de sino e é descrito por um polinômio quíntico (grau 5):

```
x(t) = x0 + (xf - x0) * (10t^3 - 15t^4 + 6t^5)
```

onde `t` é o tempo normalizado de 0 a 1, e `x0`/`xf` são as posições inicial e final. Isso produz aceleração suave a partir do repouso, velocidade máxima aproximadamente no meio do caminho e desaceleração suave de volta ao repouso.

Sistemas de detecção analisam curvatura da trajetória, perfis de velocidade e padrões de aceleração. Os sinais específicos que procuram incluem:

**Detecção de linha reta.** Um caminho perfeitamente reto entre dois pontos (curvatura zero em cada amostra) é o sinal de bot mais óbvio. Caminhos humanos sempre têm alguma curvatura devido às articulações rotacionais do braço.

**Velocidade constante.** Humanos mostram um perfil de velocidade em forma de sino (acelerar, pico, desacelerar). Uma velocidade constante durante todo o movimento indica interpolação linear, que é o comportamento padrão da maioria das ferramentas de automação.

**Ausência de sub-movimentos.** Movimentos longos são compostos por múltiplos sub-movimentos sobrepostos (Meyer et al., 1988), cada um com seu próprio pico de velocidade. Um movimento cobrindo 500+ pixels com um único pico de velocidade suave é suspeito; movimentos reais dessa distância tipicamente mostram 2-4 picos de velocidade.

**Sem overshoot.** Humanos frequentemente ultrapassam o alvo ligeiramente (por 5-15 pixels) e fazem uma pequena correção de volta. Movimentos perfeitamente precisos que acertam exatamente no alvo toda vez são estatisticamente improváveis.

### Entropia de Movimento

Entropia, neste contexto, mede a imprevisibilidade do caminho do mouse. Sistemas de detecção dividem a trajetória em segmentos, medem a mudança de direção em cada ponto e calculam a entropia de Shannon sobre a distribuição de mudanças de direção. Uma linha reta tem entropia zero (cada segmento aponta na mesma direção). Uma caminhada aleatória tem entropia máxima. O movimento humano tem entropia moderada a alta, refletindo a combinação de direção intencional e variabilidade involuntária.

Entropia baixa em muitos movimentos de mouse em uma sessão é um sinal forte de bot, mesmo que movimentos individuais tenham curvatura plausível.

### Humanização de Mouse do Pydoll

O Pydoll implementa humanização abrangente do mouse através do parâmetro `humanize=True` em operações de clique. Quando habilitado, o módulo de mouse gera movimentos que abordam cada um dos vetores de detecção descritos acima:

O caminho segue uma curva Bezier cúbica com pontos de controle aleatorizados, produzindo curvatura natural em vez de linhas retas. A velocidade ao longo do caminho segue um perfil de jerk mínimo (`10t^3 - 15t^4 + 6t^5`), produzindo a curva de velocidade em forma de sino que a Lei de Fitts prevê. A duração do movimento é calculada usando a Lei de Fitts com constantes configuráveis (`a=0.070`, `b=0.150` por padrão).

Tremor fisiológico é simulado adicionando ruído Gaussiano às posições do cursor, com amplitude inversamente proporcional à velocidade (tremor é mais visível quando a mão se move lentamente, o que corresponde à fisiologia real). Overshoot ocorre com 70% de probabilidade, ultrapassando o alvo em 3-12% da distância total antes de fazer um movimento de correção. Micro-pausas (15-40ms) ocorrem com 3% de probabilidade durante o movimento, simulando hesitações breves.

```python
# Clique humanizado básico
await element.click(humanize=True)

# A classe Mouse também pode ser usada diretamente para mais controle
from pydoll.interactions.mouse import Mouse

mouse = Mouse(connection_handler)
await mouse.click(500, 300, humanize=True)
```

!!! note "O que o Pydoll Não Faz"
    A humanização de mouse do Pydoll atualmente não modela sub-movimentos para distâncias muito longas (o caminho é um único segmento Bezier). Para a maioria das interações web, onde distâncias são menores que 500 pixels, isso é suficiente. Movimentos extremamente longos (travessias diagonais de tela inteira) podem se beneficiar de suporte futuro a múltiplos segmentos.

## Dinâmica de Digitação

A dinâmica de digitação analisa os padrões de tempo da entrada do teclado. A técnica remonta aos operadores de telégrafo na década de 1850, que podiam identificar uns aos outros pelo "punho" do código Morse (padrão de tempo característico). Sistemas modernos medem o tempo com precisão de milissegundos através de eventos `keydown` e `keyup`.

### Características de Tempo

As duas medições fundamentais são tempo de permanência (a duração entre `keydown` e `keyup` para uma única tecla, tipicamente 50-200ms para humanos) e tempo de voo (a duração entre soltar uma tecla e pressionar a próxima, tipicamente 80-400ms). A combinação de tempos de permanência e voo para pares de teclas consecutivas é chamada de latência de digrafo.

Latências de digrafo não são uniformes. Elas dependem do par de teclas específico (bigrama) sendo digitado, porque digitação é uma habilidade motora onde sequências comuns são armazenadas como memória procedural. Os fatores biomecânicos chave são:

**Alternância de mãos.** Bigramas digitados com mãos alternadas (como "th", onde "t" é mão esquerda e "h" é mão direita no QWERTY) são geralmente mais rápidos que bigramas da mesma mão (como "de", onde ambas as teclas são na mão esquerda). A mão alternada pode começar seu movimento enquanto a primeira mão ainda está completando sua tecla.

**Distância dos dedos.** Transições de tecla inicial para tecla inicial são mais rápidas. Alcançar a fileira superior ou inferior adiciona tempo proporcional à distância física que o dedo deve percorrer.

**Independência dos dedos.** Combinações de dedo anelar e mínimo na mesma mão são mais lentas que combinações de indicador e médio, porque o anelar e o mínimo compartilham tendões e têm menos controle motor independente.

**Efeitos de frequência.** Bigramas frequentemente digitados (como "th", "er", "in" em inglês) são executados mais rapidamente devido à memória motora, independentemente de seu layout físico.

### Sinais de Detecção

Sistemas de detecção procuram vários sinais que distinguem digitação humana de automação:

**Tempo de permanência zero ou constante.** Muitas ferramentas de automação despacham eventos `keydown` e `keyup` com atraso zero ou quase zero entre eles (menos de 5ms). Pressionamentos reais de teclas têm tempos de permanência mensuráveis. Tempo de permanência constante em todas as teclas é igualmente suspeito.

**Tempo de voo uniforme.** Definir um intervalo fixo entre teclas (como `type_text("hello", interval=0.1)`) produz tempo perfeitamente regular que é trivialmente detectável. Tempos de voo humanos variam por bigrama, fadiga e carga cognitiva.

**Sem erros de digitação.** Em entrada de texto extensa (50+ caracteres), a ausência completa de pressionamentos de backspace ou delete é incomum. Humanos cometem erros a uma taxa de aproximadamente 1-5% dependendo da proficiência de digitação e complexidade do texto.

**Velocidade sobre-humana.** Digitação sustentada acima de 150 WPM está além da capacidade de todos exceto digitadores competitivos de elite. Ferramentas de automação que despacham caracteres mais rápido que isso são imediatamente sinalizadas.

### Humanização de Teclado do Pydoll

O `type_text(humanize=True)` do Pydoll aborda cada vetor de detecção com parâmetros configuráveis:

Atrasos entre teclas são extraídos de uma distribuição uniforme (30-120ms por padrão) em vez de um intervalo fixo. Caracteres de pontuação (`.!?;:,`) recebem atraso adicional (80-180ms), simulando a pausa que ocorre quando um digitador considera a estrutura da frase. Pausas de pensamento (300-700ms) ocorrem com 2% de probabilidade, simulando breves momentos de reflexão. Pausas de distração (500-1200ms) ocorrem com 0.5% de probabilidade, simulando o digitador desviando o olhar ou sendo brevemente interrompido.

Erros de digitação realistas ocorrem com aproximadamente 2% de probabilidade por caractere, com cinco tipos de erro distintos ponderados por sua frequência no mundo real: erros de tecla adjacente (55%, pressionar uma tecla vizinha no QWERTY), transposições (20%, trocar dois caracteres consecutivos), pressionamentos duplos (12%, pressionar uma tecla duas vezes), caracteres pulados (8%, hesitar antes de digitar corretamente) e espaços esquecidos (5%, esquecer um espaço entre palavras). Cada tipo de erro inclui uma sequência de recuperação realista (pausa, backspace, correção) com tempo apropriado.

```python
# Digitação humanizada
await element.type_text("Hello, world!", humanize=True)

# Com configuração de tempo personalizada
from pydoll.interactions.keyboard import Keyboard, TimingConfig, TypoConfig

config = TimingConfig(
    keystroke_min=0.04,
    keystroke_max=0.15,
    thinking_probability=0.03,
)
keyboard = Keyboard(connection_handler, timing_config=config)
await keyboard.type_text("Custom timing example", humanize=True)
```

!!! note "O que o Pydoll Não Faz"
    A humanização de teclado do Pydoll usa atrasos aleatórios uniformes em vez de temporização ciente de bigramas. Não modela variação de tempo de permanência por tecla ou diferenças de velocidade de alternância de mãos. Para a maioria dos cenários de automação (preenchimento de formulários, consultas de busca), variação uniforme é suficiente para passar na detecção comportamental. Aplicações que requerem evasão de biometria de digitação em nível de autenticação precisariam de modelos de tempo personalizados.

## Análise de Comportamento de Scroll

O fingerprinting de scroll analisa como os usuários navegam verticalmente (e horizontalmente) pelo conteúdo da página. A distinção entre scroll humano e automatizado é marcante: chamadas programáticas `window.scrollTo()` produzem saltos instantâneos e discretos, enquanto scroll humano via roda do mouse, trackpad ou toque produz um fluxo de pequenos eventos incrementais com momentum e desaceleração.

### Características Físicas do Scroll

Scroll por roda do mouse produz eventos `wheel` discretos com valores de delta consistentes (tipicamente 100 ou 120 pixels por notch, dependendo do SO e navegador). Os eventos chegam em intervalos irregulares refletindo quão rapidamente o usuário gira a roda. Scroll por trackpad produz muitos eventos pequenos com deltas decrescentes, simulando momentum físico. Scroll por toque é similar ao trackpad mas com deltas iniciais maiores e caudas de desaceleração mais longas.

Sistemas de detecção analisam a distribuição de delta, timing entre eventos e curva de desaceleração. Uma chamada `scrollTo(0, 5000)` produz um único salto sem eventos intermediários, que é fundamentalmente diferente das centenas de eventos incrementais que um scroll humano gera.

### Sinais de Detecção

**Scroll instantâneo.** Usar `window.scrollTo()` ou `window.scrollBy()` com valores grandes produz zero eventos de scroll intermediários. Sistemas de detecção que escutam eventos `scroll` veem a posição de scroll mudar em um único frame.

**Deltas uniformes.** Simulação programática de scroll que despacha eventos wheel com valores de delta constantes (ex: sempre 100 pixels) carece da variação natural no scroll humano, onde valores de delta flutuam em 10-30% devido à pressão inconsistente dos dedos.

**Sem desaceleração.** Scroll humano, especialmente em trackpads, tem uma fase de momentum onde o scroll continua após o usuário levantar o dedo, com velocidade exponencialmente decrescente. Scroll automatizado que para abruptamente carece dessa cauda de desaceleração.

**Ausência de mudanças de direção.** Humanos frequentemente scrollam demais e scrollam de volta ligeiramente, ou pausam no meio de uma página para ler conteúdo. Scroll automatizado que se move em uma direção com velocidade constante sem pausas ou reversões é suspeito.

### Humanização de Scroll do Pydoll

O módulo de scroll do Pydoll implementa scroll humanizado através de `scroll.by(position, distance, humanize=True)`:

O scroll segue uma curva de easing Bezier cúbica (pontos de controle `0.645, 0.045, 0.355, 1.0` por padrão), produzindo aceleração e desaceleração naturais. Jitter por frame de ±3 pixels adiciona variação aos valores de delta. Micro-pausas (20-50ms) ocorrem com 5% de probabilidade, simulando paradas breves de leitura. Overshoot ocorre com 15% de probabilidade, scrollando 2-8% além do alvo e corrigindo de volta. Para grandes distâncias, o scroll é dividido em múltiplos gestos de "flick" (100-1200 pixels cada), simulando como um usuário real scrolla por uma página longa com deslizes repetidos em vez de um único movimento contínuo.

```python
from pydoll.interactions.scroll import Scroll, ScrollPosition

scroll = Scroll(connection_handler)

# Scroll humanizado para baixo 800 pixels
await scroll.by(ScrollPosition.Y, 800, humanize=True)

# Scroll até o topo/fundo usa múltiplos flicks semelhantes a humanos
await scroll.to_bottom(humanize=True)
```

## Vetores de Detecção Adicionais

Além da análise de mouse, teclado e scroll, sistemas de detecção sofisticados monitoram vários outros sinais comportamentais.

### Foco e Visibilidade

A API de Visibilidade de Página (`document.visibilityState`) e eventos de foco (`window.onfocus`, `window.onblur`) revelam se o usuário está ativamente visualizando a página. Uma sessão de usuário real inclui trocas de aba, minimizações de janela e períodos de inatividade. Um script de automação que mantém foco contínuo por horas sem um único evento blur é comportamentalmente anômalo. Da mesma forma, `document.hasFocus()` retornando `true` continuamente por períodos prolongados é incomum.

### Padrões de Inatividade

Usuários reais têm períodos naturais de inatividade: lendo conteúdo, pensando antes de agir, sendo distraídos. Sistemas de detecção medem a distribuição de tempos de inatividade entre interações. Uma sessão onde cada ação segue a anterior dentro de 100-500ms sem pausas mais longas segue um padrão que é estatisticamente distinto da navegação humana, onde períodos de inatividade de 2-30 segundos entre ações são normais.

### Integridade de Sequência de Eventos

Navegadores geram sequências de eventos específicas para interações do usuário. Um clique de mouse produz `pointerdown`, `mousedown`, `pointerup`, `mouseup`, `click` nessa ordem, precedido por eventos `pointermove`/`mousemove` mostrando o cursor se aproximando do alvo do clique. Ferramentas de automação que despacham um evento `click` sem o movimento precedente e eventos de ponteiro são detectáveis através de análise de sequência de eventos.

O despacho de eventos baseado em CDP do Pydoll gera sequências completas de eventos porque usa a simulação de entrada do Chrome, que produz a mesma cadeia de eventos que entrada real do usuário.

## Detecção por Machine Learning

Sistemas anti-bot modernos (DataDome, Akamai Bot Manager, Cloudflare Bot Management, PerimeterX/HUMAN Security) não usam regras de limiar simples. Eles treinam modelos de machine learning em milhões de sessões de usuários reais e milhões de sessões de bots conhecidos, aprendendo a distinguir humanos de automação com base em 50+ características simultaneamente.

Esses modelos capturam propriedades estatísticas difíceis de enumerar como regras individuais: a distribuição conjunta de velocidade de movimento e curvatura, a correlação entre velocidade de digitação e taxa de erro, a relação entre profundidade de scroll e tempo de leitura, e o "ritmo" geral de uma sessão de navegação. Um sistema que passa em cada verificação individual mas tem correlações sutilmente erradas entre características ainda pode ser sinalizado por um modelo bem treinado.

A implicação prática é que a evasão comportamental deve ser consistente em todos os tipos de interação, não apenas individualmente plausível. O parâmetro `humanize=True` do Pydoll fornece uma camada de humanização coerente entre interações de mouse, teclado e scroll, mas o desenvolvedor ainda é responsável pela plausibilidade comportamental de nível mais alto: adicionar atrasos de leitura entre carregamentos de página, variar o ritmo de workflows de múltiplas páginas e incluir períodos naturais de inatividade.

## Referências

- Fitts, P. M. (1954). The Information Capacity of the Human Motor System in Controlling the Amplitude of Movement. Journal of Experimental Psychology.
- MacKenzie, I. S. (1992). Fitts' Law as a Research and Design Tool in Human-Computer Interaction. Human-Computer Interaction.
- Flash, T., & Hogan, N. (1985). The Coordination of Arm Movements: An Experimentally Confirmed Mathematical Model. Journal of Neuroscience.
- Abend, W., Bizzi, E., & Morasso, P. (1982). Human Arm Trajectory Formation. Brain.
- Meyer, D. E., Abrams, R. A., Kornblum, S., Wright, C. E., & Smith, J. E. K. (1988). Optimality in Human Motor Performance. Psychological Review.
- Ahmed, A. A. E., & Traore, I. (2007). A New Biometric Technology Based on Mouse Dynamics. IEEE TDSC.
