# API Reference

Esta seção documenta as classes públicas que você usa diretamente. Os guias ensinam como usá-las; esta referência especifica o que cada uma expõe. Cada página traz um link de volta para o guia correspondente.

## Navegador

| Classe | O que faz | Guia |
|--------|-----------|------|
| [`Chrome`](browser/chrome.md) | Inicia e controla um navegador Chrome | [Primeiros passos](../getting-started.md) |
| [`Edge`](browser/edge.md) | Inicia e controla um navegador Microsoft Edge | [Primeiros passos](../getting-started.md) |
| [`ChromiumOptions`](browser/options.md) | Configura o navegador antes de iniciar | [Opções do navegador](../guides/browser-options.md) |
| [`Tab`](browser/tab.md) | Controla uma aba: navegar, buscar, entrada, eventos, rede | [Conceitos fundamentais](../guides/core-concepts.md) |
| [`Request`](browser/requests.md) | Faz requisições HTTP na sessão do navegador | [Requisições HTTP](../guides/http-requests.md) |

## Elementos

| Classe | O que faz | Guia |
|--------|-----------|------|
| [`WebElement`](elements/web_element.md) | Interage com um elemento localizado | [Pesquisa de elementos](../guides/element-finding.md) |
| [`ShadowRoot`](elements/shadow_root.md) | Consulta dentro de um shadow root | [Navegação no DOM](../guides/dom-traversal.md#shadow-dom) |

## Extração e conexão

| Classe | O que faz | Guia |
|--------|-----------|------|
| [`ExtractionModel`, `Field`](extraction.md) | Mapeia o DOM em objetos tipados e validados | [Extração estruturada](../guides/structured-extraction.md) |
| [`ConnectionHandler`](connection/connection.md) | Gerencia a conexão WebSocket do CDP | [Conexões remotas](../guides/remote-connections.md) |

## Core

| Referência | O que contém | Guia |
|------------|--------------|------|
| [Constants](core/constants.md) | Enums como `By`, `Key` e `PermissionType` | [Seletores](../basics/selectors.md) |
| [Exceptions](core/exceptions.md) | Erros que a Pydoll lança, como `ElementNotFound` | [Pesquisa de elementos](../guides/element-finding.md#handle-missing-elements) |

Toda operação da Pydoll é assíncrona e totalmente tipada. Veja [Async Python](../basics/async-python.md) para o básico de `async`/`await`.
