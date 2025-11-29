# Mixins de Elementos

O módulo de mixins (mixins) fornece funcionalidade reutilizável que pode ser misturada em classes de elementos para estender suas capacidades.

## Mixin Find Elements

O `FindElementsMixin` fornece capacidades de localização de elementos para as classes que o incluem.

::: pydoll.elements.mixins.find_elements_mixin
    options:
      show_root_heading: true
      show_source: false
      heading_level: 2
      filters:
        - "!^_"
        - "!^__"

## Uso

Mixins são tipicamente usados internamente pela biblioteca para compor funcionalidades. O `FindElementsMixin` é usado por classes como `Tab` e `WebElement` para fornecer métodos de localização de elementos:

```python
# Estes métodos vêm do FindElementsMixin
element = await tab.find(id="username")
elements = await tab.find(class_name="item", find_all=True)
element = await tab.query("#submit-button")
```

## Métodos Disponíveis

O `FindElementsMixin` fornece vários métodos para encontrar elementos:

- `find()` - Localização de elementos moderna com argumentos nomeados (keyword arguments)
- `query()` - Consultas de seletor CSS e XPath
- `find_element()` - Método de localização de elemento legado
- `find_elements()` - Método legado para encontrar múltiplos elementos

!!! tip "Moderno vs. Legado"
    O método `find()` é a abordagem moderna e recomendada para encontrar elementos. Os métodos `find_element()` e `find_elements()` são mantidos para compatibilidade com versões anteriores.