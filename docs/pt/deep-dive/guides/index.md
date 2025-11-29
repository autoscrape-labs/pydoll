# Guias Práticos

**A teoria encontra a prática, padrões acionáveis para desafios reais de automação.**

Enquanto as outras seções de Análise Profunda exploram **fundamentos** e **arquitetura**, esta seção fornece **guias práticos e testados em batalha** para cenários comuns de automação. Estes não são exercícios acadêmicos, são padrões refinados através do uso em produção.

## O Propósito dos Guias

Você aprendeu:

- **[Fundamentos](../fundamentals/cdp.md)** - CDP, async, tipos
- **[Arquitetura](../architecture/browser-domain.md)** - Padrões de design interno
- **[Rede](../network/index.md)** - Protocolos e proxies
- **[Fingerprinting](../fingerprinting/index.md)** - Detecção e evasão

E agora? **Como você aplica esse conhecimento a problemas reais?**

É para isso que servem os guias: **fazer a ponte entre teoria e prática**.

!!! quote "Sabedoria Prática"
    **"Na teoria, teoria e prática são a mesma coisa. Na prática, não são."** - Yogi Berra
    
    Os guias destilam conhecimento técnico complexo em **padrões acionáveis** que você pode usar imediatamente. Eles mostram **o que funciona** em produção, não apenas o que é teoricamente possível.

## Guias Atuais

### Seletores CSS vs XPath
**[→ Leia o Guia de Seletores](./selectors-guide.md)**

**O eterno debate, resolvido com dados e melhores práticas.**

Escolher entre seletores CSS e XPath não é sobre preferência. É sobre entender **trocas (tradeoffs)**, **características de desempenho** e **manutenibilidade**.

**O que você aprenderá**:

- **Comparação de sintaxe** - Exemplos lado a lado para padrões comuns
- **Benchmarks de desempenho** - Medições reais, não mitos
- **Poder vs simplicidade** - Quando o CSS não é suficiente (correspondência de texto, eixos)
- **Suporte do navegador** - Compatibilidade e casos extremos
- **Melhores práticas** - Quando usar cada um, anti-padrões a evitar
- **Exemplos complexos** - Desafios de seletores do mundo real resolvidos

**Por que isso importa**: A localização de elementos é a **base** da automação. Escolha a ferramenta errada, e você lutará com seus seletores para sempre. Escolha sabiamente, e a automação se torna direta.

---

## Em Breve

### Asyncio e Automação Concorrente
**Chegando em futuras versões**

**Análise profunda do asyncio do Python: internos do loop de eventos, padrões práticos de concorrência e exemplos do mundo real.**

Entender o asyncio é fundamental para o Pydoll. Este guia fornece uma análise abrangente do loop de eventos do Python, primitivas de concorrência e como aplicá-las à automação de navegador sem armadilhas (footguns).

**Cobrirá**:

- **Internos do Loop de Eventos**: Como `asyncio.run()` funciona, agendamento de tarefas e fluxo de execução
- **Análise Profunda de Async/Await**: Corrotinas, futuros (futures) e a máquina de estados assíncrona
- **Primitivas de Concorrência**: `gather()`, `create_task()`, `TaskGroup`, e quando usar cada um
- **Limitação de Taxa (Rate Limiting)**: Semáforos, filas e estratégias de throttling
- **Exemplos do Mundo Real**: Raspagem multi-abas, preenchimento de formulário paralelo, instâncias de navegador coordenadas
- **Armadilhas Comuns**: Bloquear o loop de eventos, cancelamento de tarefas, propagação de exceções
- **Análise de Desempenho**: Profiling de código assíncrono, identificando gargalos, otimizando I/O

**Por que isso importa**: O Asyncio move a arquitetura do Pydoll. Domine-o, e você desbloqueará a verdadeira automação concorrente sem condições de corrida (race conditions) ou corrupção de estado.

---

### Padrões Arquiteturais e Seletores Robustos
**Chegando em futuras versões**

**Padrão PageObject, seletores sustentáveis e abordagens arquiteturais para automação escalável.**

Vá além de scripts ad-hoc para arquiteturas de automação estruturadas e sustentáveis. Aprenda padrões que escalam de scripts simples para sistemas de produção.

**Cobrirá**:

- **Padrão PageObject**: Encapsulando estrutura da página, reduzindo duplicação, melhorando manutenibilidade
- **Estratégias de Seletores Robustos**: Construindo seletores que sobrevivem a mudanças na página, evitando localizadores frágeis
- **Abstração de Componentes**: Componentes reutilizáveis para padrões comuns de UI (modais, dropdowns, tabelas)
- **Estratégias de Espera**: Padrões de espera inteligentes além de simples timeouts
- **Gerenciamento de Estado**: Gerenciando o estado da automação através de páginas e fluxos
- **Padrões de Teste**: Como estruturar código de automação para testabilidade
- **Arquitetura do Mundo Real**: Estrutura e organização de projeto prontas para produção

**Por que isso importa**: A diferença entre scripts descartáveis e sistemas de automação sustentáveis é a arquitetura. Aprenda padrões que tornam seu código resiliente a mudanças.

---

## Filosofia dos Guias

Os guias seguem princípios consistentes:

### 1. Código Pronto para Produção
Todos os exemplos são **completos e testados**, não pseudocódigo ou demonstrações simplificadas. Você pode copiar, colar e adaptar às suas necessidades.

### 2. Cenários do Mundo Real
Os guias abordam **problemas reais** encontrados na automação de produção, não exemplos artificiais.

### 3. Análise de Tradeoffs (Trocas)
Quando existem múltiplas abordagens, os guias as **comparam** objetivamente com prós/contras, não apenas "aqui está uma maneira".

### 4. Complexidade Progressiva
Comece simples, adicione complexidade incrementalmente. Padrão básico primeiro, depois casos extremos e variações avançadas.

### 5. Anti-Padrões Destacados
Mostra **o que NÃO fazer** explicitamente, erros comuns pegos através de revisão de código ou depuração em produção.

## Como Usar os Guias

Guias são **material de referência**, não tutoriais sequenciais:

- **Examine** em busca de padrões relevantes para o seu problema atual
- **Marque (Bookmark)** guias que você precisará repetidamente
- **Adapte** exemplos ao seu contexto específico
- **Combine** padrões de múltiplos guias

Não leia sequencialmente de capa a capa.
Não copie cegamente sem entender os tradeoffs.
Não use padrões desatualizados (verifique a data de publicação).

## Contribuindo com Guias

Tem um padrão que vale a pena compartilhar? Os guias são **impulsionados pela comunidade**:

**O que faz um bom guia**:

- Resolve um **problema real** encontrado em produção
- Fornece **código funcional**, não apenas conceitos
- Compara **múltiplas abordagens** com tradeoffs
- Destaca **erros comuns** explicitamente
- Explica **por quê**, não apenas **como**

Veja [Contribuindo](../../CONTRIBUTING.md) para diretrizes de submissão.

## Guias vs Documentação de Funcionalidades

**Confuso sobre a diferença?**

|| Documentação de Funcionalidades | Guias de Análise Profunda |
|---|---|---|
| **Propósito** | Ensinar o que o Pydoll pode fazer | Mostrar como resolver problemas |
| **Escopo** | Método/funcionalidade única | Múltiplas funcionalidades combinadas |
| **Profundidade** | Referência de API + exemplos | Padrões + tradeoffs + melhores práticas |
| **Ordem** | Estruturado por componente | Estruturado por problema |
| **Exemplos** | Simples, isolados | Complexos, prontos para produção |

**Use Funcionalidades para**: Aprender a API do Pydoll
**Use Guias para**: Resolver desafios reais de automação

## Além dos Guias

Após dominar os padrões práticos:

- **[Arquitetura](../architecture/browser-domain.md)** - Entenda por que os padrões funcionam
- **[Rede](../network/index.md)** - Otimização em nível de rede
- **[Fingerprinting](../fingerprinting/evasion-techniques.md)** - Técnicas anti-detecção

Guias fornecem **valor imediato**. Arquitetura fornece **entendimento profundo**. Ambos tornam você eficaz.

---

## Pronto para Padrões Práticos?

Comece com **[Seletores CSS vs XPath](./selectors-guide.md)** para dominar a localização de elementos, a fundação de toda automação.

**Mais guias em breve. Marque o repositório com estrela (Star) para se manter atualizado!**

---

!!! tip "Solicite um Guia"
    Tem um padrão de automação que você gostaria de ver documentado? Abra uma issue intitulada "Solicitação de Guia: [Tópico]" descrevendo:
    
    - O problema que você está tentando resolver
    - O que você tentou até agora
    - Por que a documentação existente não cobre isso
    
    Nós priorizamos guias com base na necessidade da comunidade.

## Referência Rápida

**Disponível Agora:**

- [Seletores CSS vs XPath](./selectors-guide.md)

**Em Breve:**

- Asyncio e Automação Concorrente
- Padrões Arquiteturais e Seletores Robustos

**Cronograma**: Novos guias adicionados com base no feedback da comunidade e aprendizados de produção.