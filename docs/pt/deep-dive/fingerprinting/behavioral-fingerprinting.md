# Fingerprinting Comportamental

Este documento explora o fingerprinting comportamental, a camada mais sofisticada de detecção de bots que analisa **como os usuários interagem** com aplicações web, em vez de **quais ferramentas eles usam**. Embora o fingerprinting de rede e de navegador possa ser falsificado com conhecimento técnico suficiente, o comportamento humano é notoriamente difícil de replicar de forma convincente.

!!! info "Navegação do Módulo"
    - **[← Visão Geral de Fingerprinting](./index.md)** - Introdução e filosofia do módulo
    - **[← Network Fingerprinting (Fingerprinting de Rede)](./network-fingerprinting.md)** - Fingerprinting em nível de protocolo
    - **[← Browser Fingerprinting (Fingerprinting de Navegador)](./browser-fingerprinting.md)** - Fingerprinting em nível de aplicação
    - **[→ Técnicas de Evasão](./evasion-techniques.md)** - Contramedidas práticas
    
    Para automação prática semelhante à humana, veja **[Interações Semelhantes a Humanas](../../features/automation/human-interactions.md)**.

!!! danger "A Fronteira Final"
    O fingerprinting comportamental é a **última linha de defesa** contra a automação. Mesmo com fingerprints de rede e navegador perfeitos, movimentos de mouse não naturais, inserção instantânea de texto ou padrões de rolagem robóticos podem revelar instantaneamente a automação.

## Por que o Fingerprinting Comportamental Existe

A detecção tradicional de bots focava em fingerprints técnicos — assinaturas TLS, cabeçalhos HTTP, propriedades JavaScript. Mas à medida que as ferramentas de automação evoluíram para falsificar essas características, os sistemas anti-bot precisaram de uma nova abordagem: **analisar o próprio comportamento**.

A percepção fundamental: **Humanos são bagunçados, bots são precisos**.

- Humanos movem o mouse em trajetórias levemente curvas com aceleração variável
- Humanos digitam com intervalos irregulares influenciados pela destreza dos dedos e bigramas (pares de letras)
- Humanos rolam (scroll) com inércia e momentum que seguem leis físicas
- Humanos pausam, hesitam, corrigem erros e interagem organicamente

Bots, por padrão, executam ações com precisão de máquina, movimentos de mouse perfeitamente retos, velocidades de digitação constantes, rolagem instantânea e operações sequenciais sem variabilidade humana.

!!! info "Adoção pela Indústria"
    Os principais fornecedores anti-bot mudaram o foco para a análise comportamental:
    
    - **[DataDome](https://datadome.co/)**: Usa machine learning em mais de 2.5 bilhões de sinais comportamentais
    - **[PerimeterX (Human Security)](https://www.humansecurity.com/)**: Analisa dinâmica do mouse, eventos de toque e padrões de interação
    - **[Akamai Bot Manager](https://www.akamai.com/products/bot-manager)**: Combina fingerprinting TLS com biometria comportamental
    - **[Cloudflare Bot Management](https://www.cloudflare.com/application-services/products/bot-management/)**: Usa modelos de machine learning treinados em bilhões de requisições
    - **[Shape Security (F5)](https://www.f5.com/products/security/shape-defense)**: Pioneiros em análise comportamental desde 2011

## Análise de Movimento do Mouse

O movimento do mouse é um dos indicadores comportamentais mais poderosos porque o controle motor humano segue **leis biomecânicas** que são difíceis para bots replicarem com precisão.

### Lei de Fitts e Controle Motor Humano

A [Lei de Fitts](https://en.wikipedia.org/wiki/Fitts%27s_law) (1954) descreve o tempo necessário para mover-se até um alvo:

```
T = a + b × log₂(D/W + 1)
```

Onde:
- `T` = tempo para completar o movimento
- `a` = tempo de início/parada (tempo de reação)
- `b` = velocidade inerente do dispositivo
- `D` = distância até o alvo
- `W` = largura do alvo

**Implicações chave para detecção de bots:**

1.  **Aceleração/Desaceleração**: Humanos aceleram no início do movimento e desaceleram perto do alvo
2.  **Ultrapassagem e Correção**: Humanos frequentemente ultrapassam ligeiramente os alvos, depois corrigem
3.  **Sub-movimentos**: Movimentos longos são compostos de múltiplos sub-movimentos, não um movimento contínuo
4.  **Variabilidade**: Não existem dois movimentos idênticos, mesmo para o mesmo alvo

### Detectando Movimentos Automatizados do Mouse

```python
class MouseMovementAnalyzer:
    """
    Analisa padrões de movimento do mouse para detectar automação.
    """
    
    def analyze_trajectory(self, points: list[tuple[int, int, float]]) -> dict:
        """
        Analisa a trajetória do movimento do mouse.
        
        Args:
            points: Lista de tuplas (x, y, timestamp)
            
        Returns:
            Resultados da análise com flags de detecção
        """
        import math
        
        if len(points) < 3:
            return {'error': 'Pontos de dados insuficientes'}
        
        # Calcular velocidades
        velocities = []
        for i in range(1, len(points)):
            x1, y1, t1 = points[i-1]
            x2, y2, t2 = points[i]
            
            distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            time_delta = t2 - t1
            
            if time_delta > 0:
                velocity = distance / time_delta
                velocities.append(velocity)
        
        # Calcular acelerações
        accelerations = []
        for i in range(1, len(velocities)):
            accel = velocities[i] - velocities[i-1]
            accelerations.append(abs(accel))
        
        # Calcular curvatura do caminho
        curvatures = []
        for i in range(1, len(points) - 1):
            x1, y1, _ = points[i-1]
            x2, y2, _ = points[i]
            x3, y3, _ = points[i+1]
            
            # Calcular ângulo no ponto do meio
            angle1 = math.atan2(y2 - y1, x2 - x1)
            angle2 = math.atan2(y3 - y2, x3 - x2)
            curve = abs(angle2 - angle1)
            curvatures.append(curve)
        
        # Flags de detecção
        flags = []
        
        # Flag 1: Linha perfeitamente reta
        if len(curvatures) > 0 and max(curvatures) < 0.01:
            flags.append('PERFECTLY_STRAIGHT_LINE')
        
        # Flag 2: Velocidade constante (sem aceleração/desaceleração)
        if len(velocities) > 2:
            velocity_variance = self._variance(velocities)
            if velocity_variance < 10:  # Variância muito baixa
                flags.append('CONSTANT_VELOCITY')
        
        # Flag 3: Sem sub-movimentos
        # Movimentos humanos têm múltiplos "picos" de velocidade
        velocity_peaks = self._count_peaks(velocities)
        total_distance = sum(math.sqrt((points[i][0] - points[i-1][0])**2 + 
                                      (points[i][1] - points[i-1][1])**2)
                           for i in range(1, len(points)))
        
        if total_distance > 200 and velocity_peaks < 2:
            flags.append('NO_SUBMOVEMENTS')
        
        # Flag 4: Salto instantâneo (teletransporte)
        max_velocity = max(velocities) if velocities else 0
        if max_velocity > 10000:  # Pixels por segundo
            flags.append('INSTANT_JUMP')
        
        return {
            'total_points': len(points),
            'total_distance': total_distance,
            'avg_velocity': sum(velocities) / len(velocities) if velocities else 0,
            'max_velocity': max_velocity,
            'velocity_variance': self._variance(velocities),
            'avg_curvature': sum(curvatures) / len(curvatures) if curvatures else 0,
            'velocity_peaks': velocity_peaks,
            'detection_flags': flags,
            'is_suspicious': len(flags) > 1,
        }
    
    @staticmethod
    def _variance(values: list[float]) -> float:
        """Calcula a variância de uma lista."""
        if not values:
            return 0
        mean = sum(values) / len(values)
        return sum((x - mean)**2 for x in values) / len(values)
    
    @staticmethod
    def _count_peaks(values: list[float], threshold: float = 0.8) -> int:
        """Conta o número de picos no perfil de velocidade."""
        if len(values) < 3:
            return 0
        
        max_val = max(values)
        peak_count = 0
        
        for i in range(1, len(values) - 1):
            if values[i] > values[i-1] and values[i] > values[i+1]:
                if values[i] > max_val * threshold:
                    peak_count += 1
        
        return peak_count


# Exemplo de uso
points = [
    (100, 100, 0.0),
    (200, 100, 0.1),    # Linha horizontal perfeitamente reta
    (300, 100, 0.2),
    (400, 100, 0.3),
    (500, 100, 0.4),
]

analyzer = MouseMovementAnalyzer()
result = analyzer.analyze_trajectory(points)

print(f"Flags de Detecção: {result['detection_flags']}")
# Saída: ['PERFECTLY_STRAIGHT_LINE', 'CONSTANT_VELOCITY', 'NO_SUBMOVEMENTS']
# → Altamente suspeito!
```

### Curvas de Bezier e Simulação de Movimento Humano

**Curvas de Bezier**, desenvolvidas pelo engenheiro francês [Pierre Bézier](https://en.wikipedia.org/wiki/Pierre_B%C3%A9zier) nos anos 1960 para o design de carrocerias da Renault, são curvas paramétricas que produzem trajetórias suaves e de aparência natural entre dois pontos.

#### Por que Ferramentas de Automação Usam Curvas de Bezier

O problema fundamental com o movimento do mouse de bots:

```
Movimento do Bot (Linear):
A ──────────────────────► B
(Perfeitamente reto, velocidade constante)

Movimento Humano (Bezier):
A ─╮        ╭──► B
   ╰────────╯
(Ligeiramente curvo, velocidade variável)
```

**Pesquisa sobre Curvas Naturais:**

- **Flash, T., & Hogan, N. (1985)**: "The Coordination of Arm Movements: An Experimentally Confirmed Mathematical Model" - Journal of Neuroscience. Demonstrou que movimentos humanos de alcance seguem **trajetórias de mínimo jerk (solavanco)**, que são bem aproximadas por polinômios cúbicos.

- **Abend, W., Bizzi, E., & Morasso, P. (1982)**: "Human Arm Trajectory Formation" - Brain. Mostrou que os caminhos da mão entre dois pontos são tipicamente curvos, não retos, devido a restrições biomecânicas.

#### Estratégia de Posicionamento de Ponto de Controle

A chave para uma simulação realista é **randomizar os pontos de controle** enquanto se mantém restrições naturais:

**Restrições Geométricas:**

1.  **Desvio proporcional à distância**: Pontos de controle devem desviar no máximo 20-30% da distância total
    - Muito desvio → curvas em S não naturais
    - Pouco desvio → quase linear (como bot)

2.  **Assimetria bilateral**: P₁ e P₂ não devem ser simétricos
    - Humanos não produzem curvas perfeitamente simétricas
    - Deslocamentos aleatórios quebram a simetria especular

3.  **Espaçamento temporal**: Posicionar P₁ mais perto do início (t ≈ 0.33), P₂ mais perto do fim (t ≈ 0.66)
    - Imita fases de aceleração/desaceleração
    - Alinha-se com as previsões da Lei de Fitts

**Exemplo de Implementação:**

```python
import random
import math

def generate_realistic_control_points(start, end):
    """
    Gera pontos de controle seguindo restrições biomecânicas.
    Baseado no modelo de mínimo jerk de Flash & Hogan (1985).
    """
    x1, y1 = start
    x4, y4 = end
    
    # Calcular distância e ângulo
    distance = math.sqrt((x4 - x1)**2 + (y4 - y1)**2)
    angle = math.atan2(y4 - y1, x4 - x1)
    
    # Ponto de controle 1: 1/3 ao longo do caminho com deslocamento perpendicular
    t1 = 0.33
    offset_1 = random.uniform(-distance * 0.25, distance * 0.25)
    x2 = x1 + (x4 - x1) * t1 + offset_1 * math.sin(angle)
    y2 = y1 + (y4 - y1) * t1 - offset_1 * math.cos(angle)
    
    # Ponto de controle 2: 2/3 ao longo do caminho com deslocamento diferente
    t2 = 0.66
    offset_2 = random.uniform(-distance * 0.2, distance * 0.2)
    x3 = x1 + (x4 - x1) * t2 + offset_2 * math.sin(angle)
    y3 = y1 + (y4 - y1) * t2 - offset_2 * math.cos(angle)
    
    return (x2, y2), (x3, y3)

# Avaliação de Bezier Cúbico usando algoritmo de De Casteljau
def evaluate_bezier(t, p0, p1, p2, p3):
    """Avalia Bezier cúbico no parâmetro t."""
    u = 1 - t
    x = u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0]
    y = u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1]
    return (x, y)
```

#### Perfis de Velocidade e Funções de Suavização (Easing)

Além da forma da curva, a **distribuição de velocidade** ao longo da curva é crítica. O movimento humano segue um **perfil de velocidade em forma de sino** (aceleração → pico → desaceleração).

**Funções de Suavização Comuns:**

| Função | Fórmula | Característica |
|---|---|---|
| **Linear** | f(t) = t | Velocidade constante (robótico) |
| **Ease-in-out** | f(t) = 3t² - 2t³ | Aceleração/desaceleração suaves |
| **Cúbica** | f(t) = 4t³ (t < 0.5)<br/>1 - 4(1-t)³ (t ≥ 0.5) | Aceleração mais pronunciada |
| **Exponencial** | f(t) = (e^(kt) - 1) / (e^k - 1) | Imita movimento biológico |

**Visualização do Perfil de Velocidade:**

```
Linear (Bot):
V │    ████████████████
  │    
  └────────────────────► t
     (Velocidade constante)

Humano (Ease-in-out):
V │      ╱╲
  │     ╱  ╲
  │    ╱    ╲
  └────────────────────► t
   (Aceleração → Desaceleração)
```

#### Algoritmo de De Casteljau

Embora a fórmula explícita funcione, o **[algoritmo de De Casteljau](https://en.wikipedia.org/wiki/De_Casteljau%27s_algorithm)** (desenvolvido por Paul de Casteljau na Citroën em 1959) é numericamente mais estável e geometricamente mais intuitivo:

**Subdivisão recursiva:**

```
Dados os pontos P₀, P₁, P₂, P₃ e o parâmetro t:

Nível 1 (Interpolação linear):
Q₀ = (1-t)P₀ + tP₁
Q₁ = (1-t)P₁ + tP₂  
Q₂ = (1-t)P₂ + tP₃

Nível 2:
R₀ = (1-t)Q₀ + tQ₁
R₁ = (1-t)Q₁ + tQ₂

Nível 3 (Ponto final):
B(t) = (1-t)R₀ + tR₁
```

Essa interpolação de três níveis produz o mesmo resultado, mas evita polinômios de alta potência, reduzindo erros de ponto flutuante.

!!! warning "Detecção de Curva de Bezier"
    Embora as curvas de Bezier produzam caminhos mais naturais do que linhas retas, sistemas anti-bot sofisticados podem **detectar o uso excessivo de curvas de Bezier**:
    
    **Técnicas de Detecção:**
    
    1.  **Consistência da Curvatura**: Curvas de Bezier têm **curvatura monotônica** (a curvatura apenas aumenta ou diminui, nunca oscila). Movimentos humanos reais frequentemente têm **variações locais de curvatura** devido a correções musculares.
    
    2.  **Análise de Sub-movimento**: Humanos realizam movimentos como uma série de **sub-movimentos sobrepostos** ([Meyer et al., 1988](https://pubmed.ncbi.nlm.nih.gov/3411362/)). Curvas de Bezier puras carecem dessas micro-correções.
    
    3.  **Fingerprinting Estatístico**: Se 90%+ dos movimentos do mouse de um usuário seguem padrões de Bezier cúbicos com distribuições de pontos de controle semelhantes, é estatisticamente suspeito.
    
    4.  **Ultrapassagem de Velocidade (Overshoot)**: Humanos reais frequentemente **ultrapassam** ligeiramente os alvos, depois corrigem. Combinações perfeitamente ajustadas de Bezier+easing não têm isso.
    
    **Pesquisa:**

    - **Chou, Y. et al. (2017)**: "A Study of Web Bot Detection by Analyzing Mouse Trajectories": demonstrou que movimentos gerados por Bezier se agrupam de forma diferente dos movimentos orgânicos no espaço de características.

!!! tip "Além do Bezier Simples"
    Simulação de mouse de nível de produção requer:
    
    - **Curvas compostas**: Encadear múltiplos segmentos Bezier com pontos de controle variados
    - **Injeção de "Jitter" (tremulação)**: Adicionar pequenos desvios perpendiculares aleatórios (±2-5px)
    - **Micro-pausas**: Paradas breves ocasionais (50-150ms) no meio do movimento
    - **Ultrapassagem + correção**: Ultrapassar intencionalmente o alvo em 5-15px, depois corrigir
    - **Suavização (easing) aleatória**: Nem sempre usar a mesma função de easing
    
    Ferramentas populares usando Bezier:

    - **[Puppeteer Ghost Cursor](https://github.com/Xetera/ghost-cursor)**: Combina Bezier com ultrapassagem aleatória
    - **[Pyautogui](https://pyautogui.readthedocs.io/)**: Interpolação básica (facilmente detectável)
    - **[Humanize.js](https://github.com/HumanSignal/label-studio-frontend/blob/master/src/utils/utilities.js)**: Curvas compostas avançadas

!!! success \"Implementação Pydoll\"
    O Pydoll implementa **Curvas de Bezier Cúbicas** para seu motor de scroll, garantindo que todos os movimentos de rolagem sigam perfis naturais de aceleração e desaceleração. Isso é combinado com jitter aleatório, micro-pausas e correção de overshoot para derrotar análise comportamental avançada.

### Entropia do Movimento do Mouse

**O que é Entropia neste Contexto?**

Na teoria da informação, **entropia** mede a quantidade de aleatoriedade ou imprevisibilidade nos dados. Aplicada aos movimentos do mouse, ela quantifica quão "variado" ou "imprevisível" é o caminho.

**Por que Medir Entropia:**

- **Entropia alta** = Muita variação, muitas direções diferentes, mudanças imprevisíveis → Semelhante a humano
- **Entropia baixa** = Padrões repetitivos, movimentos previsíveis, poucas mudanças de direção → Semelhante a bot

Pense desta forma:

- Uma linha perfeitamente reta tem **entropia zero** (completamente previsível)
- Um passeio aleatório (random walk) tem **entropia alta** (difícil prever o próximo ponto)
- O movimento humano tem **entropia moderada a alta** (um tanto aleatório, mas não completamente caótico)

**A Fórmula da Entropia de Shannon (Simplificada):**

Entropia mede "surpresa". Se cada direção é igualmente provável, a entropia é maximizada. Se os movimentos sempre vão na mesma direção, a entropia é zero.

```
H = -Σ(p × log₂(p))

Onde:
- p = probabilidade de cada direção
- H alto = muitas direções diferentes (humano)
- H baixo = poucas direções ou repetitivo (bot)
```

**Detecção Prática:**

Sistemas de detecção dividem o caminho em segmentos, medem o ângulo em cada ponto e contam quantas vezes cada ângulo aparece. Um bot movendo-se em linha reta terá o mesmo ângulo todas as vezes (baixa entropia), enquanto um humano terá ângulos variados (alta entropia).

```python
import math
from collections import Counter


def calculate_mouse_entropy(points: List[Tuple[int, int]]) -> float:
    """
    Calcula a entropia de Shannon das mudanças de direção do movimento do mouse.
    
    Baixa entropia = movimentos previsíveis/robóticos
    Alta entropia = variabilidade humana natural
    """
    if len(points) < 3:
        return 0.0
    
    # Calcular mudanças de direção
    directions = []
    for i in range(1, len(points) - 1):
        x1, y1 = points[i-1]
        x2, y2 = points[i]
        x3, y3 = points[i+1]
        
        # Calcular ângulos
        angle1 = math.atan2(y2 - y1, x2 - x1)
        angle2 = math.atan2(y3 - y2, x3 - x2)
        
        # Quantizar mudança de ângulo em "bins" (categorias)
        angle_diff = angle2 - angle1
        bin_index = int((angle_diff + math.pi) / (2 * math.pi / 8))  # 8 bins
        directions.append(bin_index)
    
    # Calcular entropia de Shannon
    total = len(directions)
    if total == 0:
        return 0.0
    
    freq = Counter(directions)
    entropy = -sum((count / total) * math.log2(count / total) 
                   for count in freq.values())
    
    return entropy


# Exemplo
human_points = [(i + random.randint(-5, 5), i + random.randint(-5, 5)) 
                for i in range(100)]
bot_points = [(i, i) for i in range(100)]  # Diagonal perfeita

human_entropy = calculate_mouse_entropy(human_points)
bot_entropy = calculate_mouse_entropy(bot_points)

print(f"Entropia humana: {human_entropy:.3f}")  # ~2.5-3.0 (alta)
print(f"Entropia do bot: {bot_entropy:.3f}")      # ~0.0-0.5 (baixa)
```

!!! info "Pesquisa em Dinâmica do Mouse"
    Pesquisa acadêmica sobre dinâmica do mouse para autenticação:
    
    - **Ahmed, A. A. E., & Traore, I. (2007)**: "A New Biometric Technology Based on Mouse Dynamics" - IEEE Transactions on Dependable and Secure Computing
    - **Gamboa, H., & Fred, A. (2004)**: "A Behavioral Biometric System Based on Human-Computer Interaction" - International Society for Optical Engineering
    - **Zheng, N., Paloski, A., & Wang, H. (2011)**: "An Efficient User Verification System via Mouse Movements" - ACM Conference on Computer and Communications Security
    
    Esses artigos estabelecem que a dinâmica do mouse pode alcançar **90-98% de precisão de autenticação**.

## Dinâmica de Teclado (Cadência de Digitação)

A dinâmica de teclado, também chamada de **biometria de digitação**, analisa os padrões de tempo da entrada do teclado. Esta é uma das técnicas biométricas comportamentais mais antigas, datando dos operadores de telégrafo nos anos 1850, que podiam identificar uns aos outros por seu "punho de código Morse".

### Características de Tempo de Teclado

Sistemas modernos de dinâmica de teclado medem:

| Característica | Descrição | Valor de Detecção |
|---|---|---|
| **Dwell Time** (Tempo de Permanência) | Tempo entre pressionar e soltar a tecla (`keydown` → `keyup`) | Humanos: 50-200ms, Bots: frequentemente 0ms ou constante |
| **Flight Time** (Tempo de Voo) | Tempo entre soltar uma tecla e pressionar a próxima (`keyup` → `keydown`) | Varia por bigrama (ex: "th" mais rápido que "pz") |
| **Latência de Dígrafo** | Tempo total para sequência de duas teclas | Dependente do bigrama (memória motora) |
| **Latência de Trígrafo** | Tempo para sequência de três teclas | Mostra ritmo de digitação |
| **Taxa de Erro** | Frequência de backspace/delete | Humanos cometem erros, bots não |
| **Padrão de Maiúsculas** | Uso de Shift vs Caps Lock | Revela hábitos de digitação |

### Detectando Digitação Automatizada

```python
from typing import List, Tuple
import statistics


class KeystrokeAnalyzer:
    """
    Analisa a dinâmica de teclado para detectar automação.
    """
    
    # Velocidades de digitação humanas esperadas (milissegundos)
    HUMAN_DWELL_TIME = (50, 200)      # Duração do pressionamento da tecla
    HUMAN_FLIGHT_TIME = (80, 400)     # Tempo entre teclas
    HUMAN_WPM_RANGE = (20, 120)       # Palavras por minuto
    
    def analyze_typing(
        self,
        events: List[Tuple[str, str, float]]
    ) -> dict:
        """
        Analisa eventos de teclado para detecção de bot.
        
        Args:
            events: Lista de tuplas (event_type, key, timestamp)
                   event_type: 'keydown' ou 'keyup'
                   
        Returns:
            Análise com flags de detecção
        """
        if len(events) < 4:
            return {'error': 'Dados de teclado insuficientes'}
        
        dwell_times = []
        flight_times = []
        
        keydown_times = {}
        last_keyup_time = None
        
        for event_type, key, timestamp in events:
            if event_type == 'keydown':
                keydown_times[key] = timestamp
                
                # Calcular flight time (tempo desde a última tecla solta)
                if last_keyup_time is not None:
                    flight_time = (timestamp - last_keyup_time) * 1000  # ms
                    flight_times.append(flight_time)
            
            elif event_type == 'keyup':
                if key in keydown_times:
                    # Calcular dwell time
                    dwell_time = (timestamp - keydown_times[key]) * 1000  # ms
                    dwell_times.append(dwell_time)
                    
                    last_keyup_time = timestamp
                    del keydown_times[key]
        
        # Calcular velocidade de digitação (WPM - Palavras Por Minuto)
        if len(events) >= 2:
            total_time = events[-1][2] - events[0][2]  # segundos
            char_count = len([e for e in events if e[0] == 'keydown'])
            wpm = (char_count / 5) / (total_time / 60) if total_time > 0 else 0
        else:
            wpm = 0
        
        # Flags de detecção
        flags = []
        
        # Flag 1: Dwell time zero (soltura instantânea da tecla)
        if dwell_times and min(dwell_times) < 1:
            flags.append('ZERO_DWELL_TIME')
        
        # Flag 2: Tempo constante (sem variabilidade humana)
        if len(dwell_times) > 3:
            dwell_variance = statistics.variance(dwell_times)
            if dwell_variance < 10:  # Muito consistente
                flags.append('CONSTANT_DWELL_TIME')
        
        if len(flight_times) > 3:
            flight_variance = statistics.variance(flight_times)
            if flight_variance < 10:
                flags.append('CONSTANT_FLIGHT_TIME')
        
        # Flag 3: Velocidade de digitação impossível
        if wpm > 150:  # Recorde mundial é ~170 WPM
            flags.append('SUPERHUMAN_SPEED')
        
        # Flag 4: Muito consistente (sem erros, sem pausas)
        if len(events) > 50:
            backspaces = sum(1 for e in events if e[1] in ['Backspace', 'Delete'])
            if backspaces == 0:
                flags.append('NO_TYPING_ERRORS')
        
        return {
            'total_keystrokes': len([e for e in events if e[0] == 'keydown']),
            'avg_dwell_time': statistics.mean(dwell_times) if dwell_times else 0,
            'avg_flight_time': statistics.mean(flight_times) if flight_times else 0,
            'dwell_variance': statistics.variance(dwell_times) if len(dwell_times) > 1 else 0,
            'flight_variance': statistics.variance(flight_times) if len(flight_times) > 1 else 0,
            'typing_speed_wpm': wpm,
            'detection_flags': flags,
            'is_suspicious': len(flags) >= 2,
        }


# Exemplo: Digitação de bot (intervalos constantes)
bot_events = []
t = 0.0
for char in "automated_text":
    bot_events.append(('keydown', char, t))
    bot_events.append(('keyup', char, t + 0.001))  # 1ms dwell (muito rápido)
    t += 0.05  # Intervalos perfeitos de 50ms

analyzer = KeystrokeAnalyzer()
result = analyzer.analyze_typing(bot_events)
print(f"Flags de detecção do bot: {result['detection_flags']}")
# Saída: ['ZERO_DWELL_TIME', 'CONSTANT_DWELL_TIME', 'CONSTANT_FLIGHT_TIME', 'SUPERHUMAN_SPEED']
```

### Padrões de Tempo de Dígrafos (Bigramas)

**O que é um Bigrama?**

Um **bigrama** (ou dígrafo) é simplesmente um par de caracteres consecutivos. Na análise de digitação, bigramas revelam padrões que são únicos para cada pessoa e impossíveis para bots simples replicarem.

**Por que o Tempo dos Bigramas Importa:**

Quando você digita a palavra "the" (em inglês), você não está pressionando três teclas independentes, está executando uma sequência motora memorizada. Seu cérebro e dedos aprenderam que "th" e "he" são padrões comuns, tornando-os mais rápidos do que combinações raras como "xq" ou "zp".

**A Ciência Por Trás Disso:**

Pesquisas em aprendizado motor mostram:

- **Bigramas digitados frequentemente** (como "th", "in", "er" em inglês) são armazenados como **"pedaços motores"** (motor chunks) na memória procedural
- **Bigramas na mesma mão** são frequentemente mais rápidos do que alternando mãos (menos coordenação necessária)
- **Linha guia para linha guia** é mais rápido do que alcançar teclas distantes
- **Combinações de dedos desajeitadas** (como dedo anelar → dedo mínimo na mesma mão) são naturalmente mais lentas

Isso cria uma **assinatura de tempo única** para cada pessoa com base em:

1.  Seu estilo de digitação (digitação por toque vs "caça e cata")
2.  Familiaridade com o layout do teclado
3.  Idioma nativo (falantes de português têm bigramas diferentes dos falantes de inglês)
4.  Características físicas da mão

**Exemplo de Diferenças de Tempo:**

```python
# Tempos comuns de bigramas em inglês (milissegundos)
BIGRAM_TIMINGS = {
    # Bigramas rápidos (mesma mão, sequências comuns)
    'th': 80,
    'he': 85,
    'in': 90,
    'er': 85,
    'an': 95,
    'ed': 100,
    
    # Bigramas médios (alternância de mãos)
    'to': 120,
    'es': 125,
    'or': 130,
    
    # Bigramas lentos (posições de dedos desajeitadas)
    'pz': 250,
    'qx': 280,
    'zq': 300,
    
    # Muito lentos (exigem reposicionamento da mão)
    'ju': 180,
    'mp': 170,
}


def estimate_bigram_time(bigram: str) -> float:
    """
    Estima o tempo realista para um bigrama.
    Retorna o tempo em segundos com pequena variação aleatória.
    """
    import random
    
    base_time = BIGRAM_TIMINGS.get(bigram.lower(), 150)  # Padrão 150ms
    
    # Adicionar 10-20% de variação aleatória
    variation = random.uniform(0.9, 1.2)
    
    return (base_time / 1000) * variation


def simulate_human_typing(text: str) -> List[Tuple[str, str, float]]:
    """
    Simula digitação humana realista com tempo consciente de bigramas.
    """
    events = []
    t = 0.0
    
    for i, char in enumerate(text):
        # keydown
        events.append(('keydown', char, t))
        
        # Dwell time (50-150ms com variação)
        dwell = random.uniform(0.05, 0.15)
        
        # keyup
        events.append(('keyup', char, t + dwell))
        
        # Flight time (próximo keydown)
        if i < len(text) - 1:
            bigram = text[i:i+2]
            flight = estimate_bigram_time(bigram)
            t += dwell + flight
        else:
            t += dwell
    
    return events
```

!!! info "Referências de Dinâmica de Teclado"
    - **Monrose, F., & Rubin, A. D. (2000)**: "Keystroke Dynamics as a Biometric for Authentication" - Future Generation Computer Systems
    - **Banerjee, S. P., & Woodard, D. L. (2012)**: "Biometric Authentication and Identification using Keystroke Dynamics" - IEEE Survey
    - **Hu, J., Gingrich, D., & Sentosa, A. (2008)**: "A k-Nearest Neighbor Approach for User Authentication through Biometric Keystroke Dynamics" - IEEE International Conference on Communications
    
    Esses estudos mostram que a dinâmica de teclado pode alcançar **95%+ de precisão de autenticação** com apenas 50-100 pressionamentos de tecla.

### O Problema da "Detecção de Colar"

Um dos indicadores de bot mais fáceis é a **inserção de texto sem eventos de teclado**:

```javascript
// Detecção do lado do servidor (pseudocódigo)
function detectPastedText(input_events) {
    // Verifica se o campo de input mudou sem eventos de tecla correspondentes
    
    if (input.value.length > 0 && key_events.length == 0) {
        return 'TEXT_PASTED';  // input.value = "text" ou evento paste
    }
    
    if (input.value.length > key_events.length * 2) {
        return 'MISSING_KEYSTROKES';  // Algum texto apareceu sem teclas
    }
    
    return 'OK';
}
```

**Padrões de bot:**

- Usar `element.send_keys("text")` sem eventos de tecla individuais
- Injeção de JavaScript `input.value = "text"`
- Colar da área de transferência sem evento `paste` ou eventos de tecla precedentes

**Padrões humanos:**

- Eventos `keydown`/`keyup` individuais para cada caractere
- Eventos `paste` ocasionais (Ctrl+V) com modificadores de teclado correspondentes
- Erros de digitação seguidos por backspace

## Padrões de Rolagem (Scroll) e Física

**Por que Rolagem é Difícil de Falsificar:**

Quando você rola com a roda do mouse ou trackpad, você não está apenas movendo pixels, está **aplicando força física** a um dispositivo de entrada mecânico ou capacitivo. Essa interação física cria padrões naturais que seguem as leis da física.

**A Física da Rolagem Humana:**

1.  **Momentum Inicial**: Quando você gira a roda do mouse ou desliza o dedo no trackpad, você transmite energia cinética
2.  **Fricção/Arrasto**: O sistema aplica "fricção" virtual que gradualmente desacelera a rolagem
3.  **Desaceleração**: A velocidade diminui exponencialmente (não linearmente) até parar
4.  **Inércia**: Especialmente em touchpads, o conteúdo continua rolando brevemente após o dedo levantar

Isso é idêntico a deslizar um objeto sobre uma mesa, ele começa rápido e gradualmente desacelera devido à fricção.

**Problemas da Rolagem de Bots:**

```python
# Rolagem de bot (salto instantâneo):
window.scrollTo(0, 1000)  # Teletransporte!

# Ou rolagem em velocidade constante:
for i in range(10):
    window.scrollBy(0, 100)  # Mesmo delta, mesmo tempo
    sleep(0.1)               # Intervalos perfeitos
```

Ambos são fisicamente impossíveis para humanos — sem momentum, sem desaceleração, sem variação.

**Diferenças Observáveis:**

| Característica | Humano | Bot |
|---|---|---|
| **Perfil de velocidade** | Decaimento exponencial | Constante ou instantâneo |
| **Intervalos de eventos** | Variáveis (dependentes de frame) | Perfeitos/previsíveis |
| **Distância de rolagem** | Variável por evento | Constante por evento |
| **Desaceleração** | Gradual, suave | Parada abrupta ou nenhuma |
| **Ultrapassagem (Overshoot)** | Às vezes | Nunca |

### Análise de Eventos de Rolagem

```python
import math
from typing import List, Tuple


class ScrollAnalyzer:
    """
    Analisa o comportamento de rolagem para detectar automação.
    """
    
    def analyze_scroll_events(
        self,
        events: List[Tuple[float, int, float]]  # (timestamp, delta_y, velocity)
    ) -> dict:
        """
        Analisa eventos de rolagem para detecção de bot.
        
        Args:
            events: Lista de tuplas (timestamp, delta_y, velocity)
                   delta_y: Pixels rolados
                   velocity: Velocidade de rolagem naquele momento
                   
        Returns:
            Análise com flags de detecção
        """
        if len(events) < 3:
            return {'error': 'Dados de rolagem insuficientes'}
        
        # Extrair características
        deltas = [e[1] for e in events]
        velocities = [abs(e[2]) for e in events]
        timestamps = [e[0] for e in events]
        
        # Calcular intervalos de tempo
        intervals = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
        
        flags = []
        
        # Flag 1: Delta de rolagem constante (sem momentum da roda)
        if len(set(deltas)) == 1 and len(deltas) > 5:
            flags.append('CONSTANT_SCROLL_DELTA')
        
        # Flag 2: Rolagem instantânea (sem momentum/inércia)
        # Rolagens humanas têm desaceleração gradual
        if len(velocities) > 3:
            # Checar se a velocidade cai abruptamente para zero (sem inércia)
            has_inertia = any(velocities[i] < velocities[i-1] * 0.8 
                            for i in range(1, len(velocities)))
            
            if not has_inertia and max(velocities) > 100:
                flags.append('NO_SCROLL_INERTIA')
        
        # Flag 3: Intervalos de tempo perfeitos
        if len(intervals) > 2:
            interval_variance = self._variance(intervals)
            if interval_variance < 0.001:  # Menos de 1ms de variância
                flags.append('CONSTANT_SCROLL_TIMING')
        
        # Flag 4: Distância de rolagem impossível
        total_scroll = sum(abs(d) for d in deltas)
        total_time = timestamps[-1] - timestamps[0]
        
        if total_time > 0:
            scroll_speed = total_scroll / total_time  # pixels/segundo
            if scroll_speed > 10000:  # Irrealisticamente rápido
                flags.append('IMPOSSIBLE_SCROLL_SPEED')
        
        # Flag 5: Sem desaceleração no final
        if len(velocities) > 3:
            # Últimas 3 velocidades deveriam mostrar desaceleração
            if velocities[-1] >= velocities[-3]:
                flags.append('NO_DECELERATION')
        
        return {
            'total_scroll_distance': sum(abs(d) for d in deltas),
            'scroll_event_count': len(events),
            'avg_scroll_delta': sum(abs(d) for d in deltas) / len(deltas),
            'avg_velocity': sum(velocities) / len(velocities),
            'detection_flags': flags,
            'is_suspicious': len(flags) >= 2,
        }
    
    @staticmethod
    def _variance(values: List[float]) -> float:
        """Calcula a variância."""
        if not values or len(values) < 2:
            return 0
        mean = sum(values) / len(values)
        return sum((x - mean)**2 for x in values) / len(values)


# Exemplo: Rolagem de bot (salto instantâneo)
bot_scroll = [
    (0.0, 1000, 1000),  # Rolagem instantânea de 1000px
    (0.001, 0, 0),      # Para imediatamente
]

# Exemplo: Rolagem humana (momentum + inércia)
human_scroll = [
    (0.0, 120, 800),    # Momentum inicial
    (0.05, 100, 650),   # Desaceleração
    (0.1, 80, 520),
    (0.15, 60, 390),
    (0.2, 40, 250),
    (0.25, 20, 120),
    (0.3, 10, 50),      # Parada gradual
    (0.35, 0, 0),
]

analyzer = ScrollAnalyzer()
bot_result = analyzer.analyze_scroll_events(bot_scroll)
human_result = analyzer.analyze_scroll_events(human_scroll)

print(f"Flags do bot: {bot_result['detection_flags']}")
# Saída: ['NO_SCROLL_INERTIA', 'NO_DECELERATION', 'IMPOSSIBLE_SCROLL_SPEED']

print(f"Flags humanas: {human_result['detection_flags']}")
# Saída: []  (rolagem natural)
```

### Simulando Rolagem Realista

```python
def simulate_human_scroll(target_distance: int, direction: int = 1) -> List[Tuple[float, int, float]]:
    """
    Simula rolagem semelhante à humana com momentum e inércia.
    
    Args:
        target_distance: Total de pixels a rolar
        direction: 1 para baixo, -1 para cima
        
    Returns:
        Lista de eventos de rolagem (timestamp, delta_y, velocity)
    """
    import random
    
    events = []
    
    # Velocidade inicial (aleatória dentro da faixa humana)
    velocity = random.uniform(500, 1200)  # pixels/segundo
    
    # Taxa de desaceleração (fricção)
    deceleration = random.uniform(800, 1500)  # pixels/segundo²
    
    scrolled = 0
    t = 0.0
    dt = 0.016  # ~60 FPS
    
    while scrolled < target_distance and velocity > 10:
        # Calcular delta de rolagem para este frame
        delta = int(velocity * dt) * direction
        
        # Adicionar pequena variação aleatória
        delta += random.randint(-2, 2)
        
        events.append((t, delta, velocity))
        
        scrolled += abs(delta)
        
        # Aplicar desaceleração (fricção/inércia)
        velocity -= deceleration * dt
        velocity = max(0, velocity)
        
        # Adicionar pequena flutuação aleatória de velocidade
        velocity += random.uniform(-20, 20)
        
        t += dt
    
    return events
```

!!! tip "Física da Rolagem"
    O comportamento real da rolagem segue o padrão **"easing-out"** (desaceleração suave):
    
    1.  **Momentum inicial**: Alta velocidade da entrada do usuário (roda do mouse, deslize no trackpad)
    2.  **Desaceleração**: Decaimento exponencial devido à fricção
    3.  **Micro-ajustes**: Pequenas correções perto do alvo
    
    Isso é implementado na rolagem suave dos navegadores via CSS `scroll-behavior: smooth` usando **funções de suavização bezier**.

## Análise de Sequência de Eventos

Além das ações individuais, sistemas anti-bot analisam a **sequência e o tempo** dos eventos. Humanos seguem padrões de interação previsíveis, enquanto bots frequentemente pulam etapas ou as executam em ordens não naturais.

### Sequências de Interação Natural

```python
class EventSequenceAnalyzer:
    """
    Analisa sequências de eventos para detectar padrões de interação não naturais.
    """
    
    # Padrões de interação humana natural
    NATURAL_SEQUENCES = {
        'click': ['mousemove', 'mousedown', 'mouseup', 'click'],
        'text_input': ['focus', 'keydown', 'keypress', 'keyup', 'input'],
        'navigation': ['mousemove', 'mousedown', 'mouseup', 'click', 'unload'],
        'form_submit': ['focus', 'input', 'blur', 'submit'],
    }
    
    def analyze_click_sequence(self, events: List[Tuple[str, float]]) -> dict:
        """
        Analisa eventos que levam a um clique.
        
        Args:
            events: Lista de tuplas (event_type, timestamp)
            
        Returns:
            Análise com flags de detecção
        """
        flags = []
        
        # Extrair tipos de eventos em ordem
        event_types = [e[0] for e in events]
        
        # Encontrar eventos de clique
        click_indices = [i for i, e in enumerate(event_types) if e == 'click']
        
        for click_idx in click_indices:
            # Analisar eventos antes do clique
            start_idx = max(0, click_idx - 10)  # Olhar últimos 10 eventos
            preceding_events = event_types[start_idx:click_idx]
            
            # Flag 1: Clique sem mousemove precedente
            if 'mousemove' not in preceding_events:
                flags.append(f'CLICK_WITHOUT_MOUSEMOVE_at_{click_idx}')
            
            # Flag 2: Clique sem mousedown/mouseup
            if 'mousedown' not in preceding_events or 'mouseup' not in preceding_events:
                flags.append(f'INCOMPLETE_CLICK_SEQUENCE_at_{click_idx}')
            
            # Flag 3: Clique instantâneo (sem tempo para o cursor alcançar o alvo)
            if click_idx > 0:
                time_since_last_move = None
                for i in range(click_idx - 1, max(0, click_idx - 10), -1):
                    if event_types[i] == 'mousemove':
                        time_since_last_move = events[click_idx][1] - events[i][1]
                        break
                
                if time_since_last_move is not None and time_since_last_move < 0.05:
                    # Menos de 50ms do mousemove para o clique (rápido demais)
                    flags.append(f'INSTANT_CLICK_at_{click_idx}')
        
        return {
            'total_events': len(events),
            'total_clicks': len(click_indices),
            'detection_flags': flags,
            'is_suspicious': len(flags) > 0,
        }
    
    def analyze_typing_sequence(self, events: List[Tuple[str, str, float]]) -> dict:
        """
        Analisa sequência de entrada de texto para padrões não naturais.
        
        Args:
            events: Lista de tuplas (event_type, key, timestamp)
        """
        flags = []
        
        # Agrupar por campo de input (simplificado)
        for i in range(len(events)):
            event_type, key, timestamp = events[i]
            
            if event_type == 'input':
                # Checar se houve eventos keydown precedentes
                preceding = events[max(0, i-5):i]
                has_keydown = any(e[0] == 'keydown' for e in preceding)
                
                if not has_keydown:
                    flags.append(f'INPUT_WITHOUT_KEYDOWN_at_{i}')
        
        # Checar por evento focus antes de digitar
        has_focus = any(e[0] == 'focus' for e in events[:10])
        has_typing = any(e[0] in ['keydown', 'keyup'] for e in events)
        
        if has_typing and not has_focus:
            flags.append('TYPING_WITHOUT_FOCUS')
        
        return {
            'detection_flags': flags,
            'is_suspicious': len(flags) > 0,
        }


# Exemplo: Clique de bot (sem mousemove)
bot_click_events = [
    ('mousedown', 1.0),
    ('mouseup', 1.001),
    ('click', 1.002),  # Sem mousemove precedente!
]

# Exemplo: Clique humano (sequência natural)
human_click_events = [
    ('mousemove', 0.5),
    ('mousemove', 0.55),
    ('mousemove', 0.6),
    ('mousemove', 0.7),
    ('mousedown', 0.85),
    ('mouseup', 0.95),
    ('click', 0.96),
]

analyzer = EventSequenceAnalyzer()
bot_result = analyzer.analyze_click_sequence(bot_click_events)
human_result = analyzer.analyze_click_sequence(human_click_events)

print(f"Flags do bot: {bot_result['detection_flags']}")
# Saída: ['CLICK_WITHOUT_MOUSEMOVE_at_2', 'INCOMPLETE_CLICK_SEQUENCE_at_2']

print(f"Flags humanas: {human_result['detection_flags']}")
# Saída: []
```

### Análise de Tempo: Intervalos Entre Eventos

**O que são Intervalos Entre Eventos?**

Um **intervalo entre eventos** (inter-event interval) é simplesmente o tempo entre ações consecutivas — o intervalo entre um clique do mouse e o próximo, ou entre pressionar uma tecla e pressionar outra.

**Por que Isso Importa:**

Humanos têm variabilidade natural no tempo devido a:
- **Processamento cognitivo**: Pensar sobre o que fazer a seguir (100-500ms)
- **Busca visual**: Encontrar o próximo alvo na tela (200-800ms)
- **Execução motora**: O tempo de movimento físico varia (Lei de Fitts: 100-1000ms dependendo da distância)
- **Fadiga e atenção**: Mais lento quando cansado, mais rápido quando focado
- **Complexidade da decisão**: Ações simples são rápidas, decisões complexas são lentas

**Sinais de Bot:**

1.  **Regularidade perfeita**: Eventos espaçados em intervalos de exatamente 100ms
2.  **Rápido demais**: Nenhum humano pode clicar 10 vezes por segundo consistentemente
3.  **Sem variação**: Desvio padrão próximo de zero (humanos variam em 20-50%)
4.  **Falta de "tempo de pensamento"**: Bots executam a próxima ação imediatamente após a conclusão da anterior

**Exemplo Real:**

```
Humano clicando 5 botões:
Clique 1 → 0.0s
Clique 2 → 0.8s   (variado: lendo, movendo o mouse)
Clique 3 → 1.3s   (0.5s depois)
Clique 4 → 2.7s   (1.4s depois - hesitação?)
Clique 5 → 3.2s   (0.5s depois)

Bot clicando 5 botões:
Clique 1 → 0.0s
Clique 2 → 0.1s   (tempo perfeito)
Clique 3 → 0.2s   (tempo perfeito)
Clique 4 → 0.3s   (tempo perfeito)
Clique 5 → 0.4s   (tempo perfeito)
```

Os intervalos perfeitos de 100ms do bot são estatisticamente impossíveis para humanos.

```python
def analyze_event_timing(events: List[Tuple[str, float]]) -> dict:
    """
    Analisa o tempo entre eventos para detectar padrões robóticos.
    """
    import statistics
    
    if len(events) < 3:
        return {'error': 'Eventos insuficientes'}
    
    # Calcular intervalos entre eventos
    intervals = []
    for i in range(1, len(events)):
        interval = events[i][1] - events[i-1][1]
        intervals.append(interval)
    
    flags = []
    
    # Flag 1: Tempo perfeito (sem variação)
    if len(intervals) > 3:
        variance = statistics.variance(intervals)
        if variance < 0.0001:  # Menos de 0.1ms de variação
            flags.append('PERFECT_TIMING')
    
    # Flag 2: Intervalos suspeitosamente regulares
    # Checar se intervalos seguem um padrão
    if len(intervals) > 5:
        rounded = [round(i, 2) for i in intervals]
        unique_intervals = len(set(rounded))
        
        if unique_intervals < len(intervals) / 3:
            flags.append('REPETITIVE_TIMING')
    
    # Flag 3: Velocidade impossível (eventos muito próximos)
    min_interval = min(intervals)
    if min_interval < 0.001:  # Menos de 1ms
        flags.append('IMPOSSIBLE_SPEED')
    
    return {
        'avg_interval': statistics.mean(intervals),
        'interval_variance': statistics.variance(intervals) if len(intervals) > 1 else 0,
        'min_interval': min_interval,
        'max_interval': max(intervals),
        'detection_flags': flags,
        'is_suspicious': len(flags) > 1,
    }
```

!!! danger "O Detector de "Tempo de Pensamento""
    Sistemas anti-bot avançados medem o **tempo até a primeira interação**:
    
    ```python
    # Tempo do carregamento da página até a primeira ação do usuário
    time_to_first_action = first_event_timestamp - page_load_timestamp
    
    if time_to_first_action < 0.5:  # Menos de 500ms
        # Humanos precisam de tempo para ler, entender, localizar elementos
        return 'BOT_DETECTED'  # Rápido demais para ser humano
    ```
    
    **Humanos reais**:

    - Escaneiam a página (1-3 segundos)
    - Leem o conteúdo (2-10 segundos)
    - Movem o cursor para o alvo (0.3-1 segundo)
    - Clicam (0.05-0.2 segundos)
    
    **Total**: 3.5-14+ segundos do carregamento da página até o primeiro clique
    
    **Bots**:

    - Executam imediatamente após o DOMContentLoaded
    - Tempo total: 0.1-0.5 segundos

## Machine Learning na Detecção Comportamental

Sistemas anti-bot modernos usam **modelos de machine learning (aprendizado de máquina)** treinados em bilhões de interações para classificar o comportamento como humano ou bot. Esses sistemas não dependem de detecção simples baseada em regras, eles aprendem padrões através de aprendizado supervisionado em conjuntos de dados massivos.

### Como Funciona a Detecção Baseada em ML

**Fase de Treinamento:**

1.  **Coleta de Dados**: Milhões de sessões confirmadas de humanos e bots
2.  **Extração de Features (Características)**: 100-500+ features por sessão:
    - Mouse: variância da velocidade, entropia da curvatura, padrões de aceleração
    - Teclado: distribuições de dwell/flight time, tempo de bigramas, taxa de erro
    - Rolagem: coeficientes de momentum, curvas de desaceleração
    - Tempo: intervalos entre eventos, sequências de ações, padrões de hesitação
3.  **Treinamento do Modelo**: Random Forests, Gradient Boosting, Redes Neurais
4.  **Validação**: Testado contra conjuntos de dados de validação (holdout) para minimizar falsos positivos

**Fase de Detecção:**

1.  **Extração de Features em Tempo Real**: Interações do usuário capturadas no navegador
2.  **Inferência do Modelo**: Features alimentadas no modelo treinado (< 50ms)
3.  **Pontuação de Confiança**: Probabilidade de ser bot (0.0-1.0)
4.  **Decisão**: Bloquear, desafiar ou permitir com base no limiar

### Categorias de Features Usadas por Sistemas Comerciais

| Categoria | Features de Exemplo | Sinal de Detecção |
|---|---|---|
| **Dinâmica do Mouse** | Variância da velocidade, entropia da trajetória, contagem de sub-movimentos | Baixa variância = bot |
| **Padrões de Teclado** | Desvio padrão do Dwell time, tempo de bigramas, taxa de erro | Tempo perfeito = bot |
| **Comportamento de Rolagem** | Coeficiente de momentum, taxa de desaceleração, presença de inércia | Rolagem instantânea = bot |
| **Sequências de Eventos** | Mousemove antes do clique, foco antes de digitar, tempo de pensamento | Etapas faltando = bot |
| **Padrões de Sessão** | Total de eventos, duração da sessão, densidade de interação | Rápido demais = bot |
| **Consistência do Dispositivo** | Consistência toque vs mouse, mudanças de orientação da tela | Inconsistência = bot |

!!! info "Sistemas de Detecção de Bot Baseados em ML"
    Sistemas comerciais de detecção de bot usando ML:
    
    - **DataDome**: Alega **99.99% de precisão** usando modelos de ML comportamentais treinados em 2.5B+ de sinais
    - **PerimeterX (Human Security)**: "Behavioral Fingerprinting™" com 400+ sinais comportamentais
    - **Akamai Bot Manager**: Analisa 200+ características comportamentais por sessão
    - **Castle.io**: Inferência de ML em tempo real com latência sub-100ms
    - **Arkose Labs**: Combina análise comportamental com desafios CAPTCHA interativos
    - **Cloudflare Bot Management**: Usa modelos ensemble (Random Forest + Redes Neurais)
    
    **Arquiteturas de ML Comuns:**

    - **Random Forests**: Inferência rápida, features interpretáveis, bom para dados tabulares
    - **Gradient Boosting (XGBoost/LightGBM)**: Alta precisão, lida com valores ausentes
    - **Redes Neurais Recorrentes (LSTM/GRU)**: Captura sequências temporais (trajetórias do mouse)
    - **Métodos Ensemble**: Combina múltiplos modelos para maior precisão

**Por que ML é Eficaz:**

1.  **Aprendizado Adaptativo**: Modelos atualizam à medida que técnicas de bot evoluem
2.  **Alta Dimensionalidade**: 500+ features são impossíveis de falsificar consistentemente
3.  **Padrões Sutis**: Detecta correlações que humanos não podem ver (ex: relação velocidade-curvatura)
4.  **Baixa Taxa de Falsos Positivos**: Treinado em milhões de usuários reais
5.  **Desempenho em Tempo Real**: Otimizado para inferência < 50ms

**Limitação para Evasores:**

Você **não pode** replicar a detecção baseada em ML localmente. Os modelos são proprietários, treinados em conjuntos de dados massivos e constantemente retreinados. Sua melhor abordagem é **focar em comportamento realista** em vez de tentar fazer engenharia reversa em seus modelos.

## Conclusão

O fingerprinting comportamental representa a **vanguarda** da detecção de bots. É a linha final de defesa que até mesmo bots sofisticados têm dificuldade em superar de forma convincente.

**Pontos Chave:**

1.  **Humanos são bagunçados**: Variabilidade, erros e hesitação são características, não bugs
2.  **Bots são precisos**: Tempo constante, linhas retas e execução perfeita são sinais de alerta
3.  **A física importa**: Movimento segue leis biomecânicas (Lei de Fitts, inércia, momentum)
4.  **O contexto importa**: Ações devem ocorrer em sequências naturais com tempo realista
5.  **ML está em toda parte**: Sistemas modernos não usam detecção baseada em regras, eles aprendem padrões

**A Vantagem do Pydoll:**

Diferente do Selenium/Puppeteer que expõem `navigator.webdriver` e têm características CDP detectáveis, o Pydoll fornece:

- **Sem flag webdriver** (fingerprint mais limpo)
- **Controle total do CDP** (manipulação profunda do navegador)
- **Arquitetura assíncrona** (padrões de tempo naturais)
- **Interceptação de requisições** (consistência de cabeçalhos)

Para técnicas práticas de evasão e estratégias de implementação, veja o guia [Técnicas de Evasão](./evasion-techniques.md).

## Leitura Adicional

### Pesquisa Acadêmica

- **Ahmed, A. A. E., & Traore, I. (2007)**: "A New Biometric Technology Based on Mouse Dynamics" - IEEE TDSC
- **Monrose, F., & Rubin, A. D. (2000)**: "Keystroke Dynamics as a Biometric for Authentication" - Future Generation Computer Systems
- **Zheng, N., Paloski, A., & Wang, H. (2011)**: "An Efficient User Verification System via Mouse Movements" - ACM CCS
- **Gamboa, H., & Fred, A. (2004)**: "A Behavioral Biometric System Based on Human-Computer Interaction" - SPIE
- **Fitts, P. M. (1954)**: "The Information Capacity of the Human Motor System" - Journal of Experimental Psychology

### Recursos da Indústria

- **[DataDome Bot Detection](https://datadome.co/)**: Detecção comercial de bots com ML comportamental
- **[PerimeterX (Human Security)](https://www.humansecurity.com/)**: Fingerprinting comportamental e gerenciamento de bots
- **[Akamai Bot Manager](https://www.akamai.com/products/bot-manager)**: Detecção de bots empresarial
- **[Cloudflare Bot Management](https://www.cloudflare.com/application-services/products/bot-management/)**: Detecção de bots baseada em ML
- **[F5 Shape Security](https://www.f5.com/products/security/shape-defense)**: Pioneiros em análise comportamental

### Documentação Técnica

- **[Lei de Fitts Wikipedia](https://en.wikipedia.org/wiki/Fitts%27s_law)**: Fundamentos de controle motor
- **[MDN: Pointer Events](https://developer.mozilla.org/en-US/docs/Web/API/Pointer_events)**: Documentação de eventos do navegador
- **[MDN: Keyboard Events](https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent)**: API de eventos de teclado
- **[CSS Easing Functions](https://developer.mozilla.org/en-US/docs/Web/CSS/easing-function)**: Tempos de rolagem/animação

### Guias Práticos

- **[Pydoll: Interações Semelhantes a Humanas](../../features/automation/human-interactions.md)**: Automação comportamental prática
- **[Pydoll: Contorno de Captcha Comportamental](../../features/advanced/behavioral-captcha-bypass.md)**: Usando comportamento para passar em desafios
- **[Técnicas de Evasão](./evasion-techniques.md)**: Guia completo de evasão de fingerprinting