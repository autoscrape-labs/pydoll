# Guias

Um guia por recurso, cada um com exemplos executáveis. Comece por [Conceitos centrais](core-concepts.md) se você está começando, ou vá direto para a tarefa que precisa.

## Conceitos centrais

- [Conceitos centrais](core-concepts.md): os objetos tab e browser, o modelo assíncrono, e o que "sem webdriver" significa na prática.

## Encontrando e extraindo

- [Encontrar elementos](element-finding.md): localize elementos com `find()` (por atributos) e `query()` (CSS ou XPath).
- [Navegação no DOM](dom-traversal.md): vá de um elemento para seus filhos, irmãos e shadow roots.
- [Extração estruturada](structured-extraction.md): obtenha dados tipados e validados de uma página com um modelo.

## Interagindo

- [Teclado](keyboard.md): digite texto e pressione teclas, com timing humanizado.
- [Mouse](mouse.md): clique em elementos ou controle coordenadas brutas, com movimento humanizado.
- [Operações com arquivos](file-operations.md): envie arquivos e lide com downloads.
- [Iframes](iframes.md): encontre e controle elementos dentro de frames.
- [Screenshots e PDFs](screenshots-and-pdfs.md): capture a página, um elemento ou um PDF.

## Rede

- [Monitoramento de rede](network-monitoring.md): observe requisições e respostas conforme acontecem.
- [Interceptação de requisições](request-interception.md): bloqueie, modifique ou simule requisições.
- [Requisições HTTP no contexto do navegador](http-requests.md): chame APIs a partir da sessão do navegador, com seus cookies e autenticação.
- [Gravação de HAR](network-recording.md): grave uma sessão em um arquivo HAR.

## Gerenciando o navegador

- [Abas](tabs.md): abra, feche e controle várias abas ao mesmo tempo.
- [Contextos de navegador](browser-contexts.md): sessões isoladas em um só navegador, cada uma com seus próprios cookies.
- [Cookies e sessões](cookies-and-sessions.md): leia, defina e persista cookies entre execuções.
- [Opções do navegador](browser-options.md): flags de linha de comando, headless e a configuração de inicialização.
- [Preferências do navegador](browser-preferences.md): o dicionário interno de preferências do Chromium.
- [Proxies](proxies.md): roteie o tráfego por um proxy, com autenticação.
- [Conexões remotas](remote-connections.md): conecte-se a um navegador que já está em execução.

## Reagindo a eventos

- [Eventos](events.md): execute callbacks quando eventos de página e de rede disparam.
- [Repetição](retrying.md): repita passos instáveis com o decorador `retry`.

## Próximos passos

- [Ficando indetectável](../stealth/index.md): comportamento humanizado, tratamento de captcha e fingerprinting.
- [Referência da API](../api/index.md): cada classe e método público.
