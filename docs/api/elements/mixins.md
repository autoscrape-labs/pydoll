# Element Mixins

The mixins module provides reusable functionality that can be mixed into element classes to extend their capabilities.

## Find Elements Mixin

The `FindElementsMixin` provides element finding capabilities to classes that include it.

::: pydoll.elements.mixins.find_elements_mixin
    options:
      show_root_heading: true
      show_source: false
      heading_level: 2
      filters:
        - "!^_"
        - "!^__"

## Usage

Mixins are typically used internally by the library to compose functionality. The `FindElementsMixin` is used by classes like `Tab` and `WebElement` to provide element finding methods:

```python
# These methods come from FindElementsMixin
element = await tab.find(id="username")
elements = await tab.find(class_name="item", find_all=True)
element = await tab.query("#submit-button")
```

## Available Methods

The `FindElementsMixin` provides several methods for finding elements:

- `find()` - Modern element finding with keyword arguments
- `query()` - CSS selector and XPath queries
- `find_element()` - Legacy element finding method
- `find_elements()` - Legacy method for finding multiple elements

!!! tip "Modern vs Legacy"
    The `find()` method is the modern, recommended approach for finding elements. The `find_element()` and `find_elements()` methods are maintained for backward compatibility. 