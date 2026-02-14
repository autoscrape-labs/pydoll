# Guia de Funcionalidades

Bem-vindo à documentação abrangente de funcionalidades do Pydoll! Aqui você descobrirá tudo o que torna o Pydoll uma ferramenta de automação de navegador poderosa e flexível. Esteja você apenas começando ou procurando aproveitar capacidades avançadas, você encontrará guias detalhados, exemplos práticos e melhores práticas para cada funcionalidade.

## O Que Você Encontrará Aqui

Este guia está organizado em seções lógicas que refletem sua jornada na automação: de conceitos básicos a técnicas avançadas. Cada página é projetada para ser autocontida, para que você possa pular diretamente para o que lhe interessa ou seguir sequencialmente.

## Conceitos Principais

Antes de mergulhar em funcionalidades específicas, vale a pena entender o que diferencia o Pydoll. Esses conceitos fundamentais informam como toda a biblioteca funciona.

**[Conceitos Principais](core-concepts.md)**: Descubra as decisões arquitetônicas que tornam o Pydoll diferente: a abordagem "zero-webdriver" que elimina dores de cabeça de compatibilidade, o design "async-first" que permite operações concorrentes verdadeiras, e o suporte nativo para múltiplos navegadores baseados em Chromium.

## Localização e Interação com Elementos

Encontrar e interagir com elementos da página é o pão com manteiga da automação. O Pydoll torna isso surpreendentemente intuitivo com APIs modernas que simplesmente fazem sentido.

**[Localização de Elementos](element-finding.md)**: Domine as estratégias de localização de elementos do Pydoll, desde o intuitivo método `find()` que usa atributos HTML naturais, até o poderoso método `query()` para seletores CSS e XPath. Você também aprenderá sobre auxiliares de travessia do DOM que permitem navegar pela estrutura da página eficientemente.

## Capacidades de Automação

Estas são as funcionalidades que dão vida à sua automação: simular interações do usuário, controle de teclado, lidar com operações de arquivo, trabalhar com iframes e capturar conteúdo visual.

**[Interações Semelhantes a Humanas](automation/human-interactions.md)**: Aprenda como criar interações que parecem genuinamente humanas: digitar com variações naturais de tempo, clicar com movimentos realistas do mouse e usar atalhos de teclado exatamente como um usuário real faria. Isso é crucial para evitar detecção em sites sensíveis à automação.

**[Controle de Teclado](automation/keyboard-control.md)**: Domine as interações de teclado com suporte abrangente para combinações de teclas, modificadores e teclas especiais. Essencial para formulários, atalhos e testes de acessibilidade.

**[Operações com Arquivos](automation/file-operations.md)**: O manuseio de arquivos pode ser complicado na automação de navegador. O Pydoll fornece soluções robustas tanto para uploads quanto para downloads, com o gerenciador de contexto `expect_download` oferecendo um manuseio elegante da conclusão assíncrona de downloads.

**[Interação com IFrames](automation/iframes.md)**: Trate iframes como qualquer elemento—encontre o iframe e continue pesquisando a partir dele. Sem targets extras, sem abas adicionais.

**[Capturas de Tela e PDF](automation/screenshots-and-pdfs.md)**: Capture conteúdo visual de suas sessões de automação. Se você precisa de capturas de tela de página inteira para testes de regressão visual, capturas de elementos específicos para depuração, ou exportações de PDF para arquivamento, o Pydoll tem o que você precisa.

## Funcionalidades de Rede

As capacidades de rede do Pydoll são onde ele realmente brilha, dando a você visibilidade e controle sem precedentes sobre o tráfego HTTP.

**[Monitoramento de Rede](network/monitoring.md)**: Observe e analise toda a atividade de rede em sua sessão de navegador. Extraia respostas de API, rastreie o tempo de requisição, identifique requisições falhas e entenda exatamente quais dados estão sendo trocados. Essencial para depuração, testes e extração de dados.

**[Interceptação de Requisições](network/interception.md)**: Vá além da observação para modificar ativamente o comportamento da rede. Bloqueie recursos indesejados, injete cabeçalhos personalizados, modifique payloads de requisição, ou até mesmo atenda requisições com dados mockados. Isso é poderoso para testes, otimização e controle de privacidade.

**[Requisições HTTP no Contexto do Navegador](network/http-requests.md)**: Faça requisições HTTP que executam dentro do contexto JavaScript do navegador, herdando automaticamente estado de sessão, cookies e autenticação. Esta abordagem híbrida combina a familiaridade da biblioteca `requests` do Python com os benefícios da execução no contexto do navegador.

## Gerenciamento do Navegador

O gerenciamento eficaz do navegador e das abas é essencial para cenários complexos de automação, processamento paralelo e testes multiusuário.

**[Gerenciamento de Múltiplas Abas](browser-management/tabs.md)**: Trabalhe com múltiplas abas do navegador simultaneamente, garantindo o uso eficiente de recursos enquanto lhe dá controle total sobre o ciclo de vida das abas, detecção de abas abertas pelo usuário e operações de scraping concorrentes.

**[Contextos do Navegador](browser-management/contexts.md)**: Crie ambientes de navegação completamente isolados dentro de um único processo de navegador. Cada contexto mantém cookies, armazenamento, cache e permissões separados: perfeito para testes de múltiplas contas, testes A/B, ou scraping paralelo com diferentes configurações.


**[Cookies e Sessões](browser-management/cookies-sessions.md)**: Gerencie o estado da sessão tanto no nível do navegador quanto no da aba. Defina cookies programaticamente, extraia dados de sessão e mantenha diferentes sessões entre contextos de navegador para cenários de testes sofisticados.


## Configuração

Personalize cada aspecto do comportamento do navegador para corresponder às suas necessidades de automação, desde preferências de baixo nível do Chromium até argumentos de linha de comando e estratégias de carregamento de página.

**[Opções do Navegador](configuration/browser-options.md)**: Configure os parâmetros de inicialização do Chromium, argumentos de linha de comando e controle do estado de carregamento da página. Ajuste fino do comportamento do navegador, ative recursos experimentais e otimize o desempenho para suas necessidades de automação.

**[Preferências do Navegador](configuration/browser-preferences.md)**: O acesso direto ao sistema interno de preferências do Chromium lhe dá controle sobre centenas de configurações. Configure downloads, desative funcionalidades, otimize o desempenho ou crie fingerprints de navegador realistas para automação furtiva.

**[Configuração de Proxy](configuration/proxy.md)**: Suporte nativo a proxy com capacidades completas de autenticação. Essencial para projetos de web scraping que exigem rotação de IP, testes geo-direcionados ou automação focada em privacidade.


## Funcionalidades Avançadas

Estas capacidades sofisticadas abordam desafios complexos de automação e casos de uso especializados.

**[Contorno de Captcha Comportamental](advanced/behavioral-captcha-bypass.md)**: O manejo nativo de captcha comportamental do Pydoll é uma de suas funcionalidades mais solicitadas. Aprenda como interagir com Cloudflare Turnstile, reCAPTCHA v3 e desafios invisíveis hCaptcha usando duas abordagens - gerenciador de contexto síncrono para conclusão garantida, e processamento em segundo plano para operação não bloqueante.

**[Sistema de Eventos](advanced/event-system.md)**: Construa automação reativa que responde a eventos do navegador em tempo real. Monitore carregamentos de página, atividade de rede, mudanças no DOM e execução de JavaScript para criar scripts de automação inteligentes e adaptativos.

**[Conexões Remotas](advanced/remote-connections.md)**: Conecte-se a navegadores já em execução via WebSocket para cenários de automação híbrida. Perfeito para pipelines de CI/CD, ambientes contêinerizados, ou integração do Pydoll em ferramentas CDP existentes.


## Como Usar Este Guia

Cada página de funcionalidade segue uma estrutura consistente:

1.  **Visão Geral** - O que a funcionalidade faz e por que ela é importante
2.  **Uso Básico** - Comece rapidamente com exemplos simples
3.  **Padrões Avançados** - Aproveite todo o potencial da funcionalidade
4.  **Melhores Práticas** - Dicas para uso eficaz e eficiente
5.  **Armadilhas Comuns** - Aprenda com os erros comuns

Sinta-se à vontade para explorar as funcionalidades em qualquer ordem com base em suas necessidades. Os exemplos de código são completos e estão prontos para rodar - apenas copie, cole e adapte ao seu caso de uso.

Pronto para mergulhar fundo nas capacidades do Pydoll? Escolha uma funcionalidade que lhe interessa e comece a explorar! 🚀