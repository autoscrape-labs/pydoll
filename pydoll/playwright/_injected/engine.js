/*
 * Selector and actionability engine for pydoll's Playwright-compatible layer.
 *
 * Ported from Microsoft Playwright's injected script (packages/injected/src:
 * injectedScript.ts, roleUtils.ts, selectorUtils.ts, domUtils.ts and
 * packages/isomorphic/selectorParser.ts, stringUtils.ts), Apache License 2.0,
 * Copyright (c) Microsoft Corporation. Simplified: no layout selectors, no aria
 * snapshots, no custom engines, no hit-target interception.
 *
 * The whole engine is a single expression that evaluates to an object. It keeps
 * every cache local to the invocation, installs no globals, no listeners and
 * mutates nothing in the page.
 */
(function () {
  'use strict';

  const ELEMENT_NODE = 1;
  const TEXT_NODE = 3;
  const COMMENT_NODE = 8;
  const DOCUMENT_NODE = 9;
  const FRAGMENT_NODE = 11;

  // ------------------------------------------------------------------ strings

  function normalizeWhiteSpace(text) {
    return text.replace(/[​­]/g, '').trim().replace(/\s+/g, ' ');
  }

  function trimFlatString(s) {
    return s.trim();
  }

  function asFlatString(s) {
    return s
      .split(' ')
      .map(chunk => chunk.replace(/\r\n/g, '\n').replace(/[​­]/g, '').replace(/\s\s*/g, ' '))
      .join(' ')
      .trim();
  }

  function cssUnquote(s) {
    s = s.substring(1, s.length - 1);
    if (!s.includes('\\'))
      return s;
    const r = [];
    let i = 0;
    while (i < s.length) {
      if (s[i] === '\\' && i + 1 < s.length)
        i++;
      r.push(s[i++]);
    }
    return r.join('');
  }

  class InvalidSelectorError extends Error {}

  // ---------------------------------------------------------------- dom utils

  const cache = {
    style: new Map(),
    styleBefore: new Map(),
    styleAfter: new Map(),
    styleVisibility: new Map(),
    text: new Map(),
    ariaRole: new Map(),
    ariaDisabled: new Map(),
    isHidden: new Map(),
    accessibleName: new Map(),
    accessibleNameHidden: new Map(),
    pseudoContent: new Map(),
    pseudoContentBefore: new Map(),
    pseudoContentAfter: new Map(),
  };

  function parentElementOrShadowHost(element) {
    if (element.parentElement)
      return element.parentElement;
    if (!element.parentNode)
      return undefined;
    if (element.parentNode.nodeType === FRAGMENT_NODE && element.parentNode.host)
      return element.parentNode.host;
    return undefined;
  }

  function enclosingShadowRootOrDocument(element) {
    let node = element;
    while (node.parentNode)
      node = node.parentNode;
    if (node.nodeType === FRAGMENT_NODE || node.nodeType === DOCUMENT_NODE)
      return node;
    return undefined;
  }

  function enclosingShadowHost(element) {
    while (element.parentElement)
      element = element.parentElement;
    return parentElementOrShadowHost(element);
  }

  function closestCrossShadow(element, css, scope) {
    while (element) {
      const closest = element.closest(css);
      if (scope && closest !== scope && closest && closest.contains(scope))
        return undefined;
      if (closest)
        return closest;
      element = enclosingShadowHost(element);
    }
    return undefined;
  }

  function getElementComputedStyle(element, pseudo) {
    const map = pseudo === '::before' ? cache.styleBefore : pseudo === '::after' ? cache.styleAfter : cache.style;
    if (map.has(element))
      return map.get(element);
    const view = element.ownerDocument && element.ownerDocument.defaultView;
    const style = view ? view.getComputedStyle(element, pseudo) : undefined;
    map.set(element, style);
    return style;
  }

  function isVisibleTextNode(node) {
    const range = node.ownerDocument.createRange();
    range.selectNode(node);
    const rect = range.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  }

  function elementSafeTagName(element) {
    const tagName = element.tagName;
    if (typeof tagName === 'string') {
      const firstCharCode = tagName.charCodeAt(0);
      if (firstCharCode >= 97 && firstCharCode <= 122)
        return tagName.toUpperCase();
      return tagName;
    }
    if (element instanceof HTMLFormElement)
      return 'FORM';
    return String(element.tagName).toUpperCase();
  }

  function isElementStyleVisibilityVisible(element, style) {
    const cached = cache.styleVisibility.get(element);
    if (cached !== undefined)
      return cached;
    style = style || getElementComputedStyle(element);
    let result = true;
    if (style) {
      if (Element.prototype.checkVisibility) {
        if (!element.checkVisibility())
          result = false;
      } else {
        const detailsOrSummary = element.closest('details,summary');
        if (detailsOrSummary !== element && detailsOrSummary && detailsOrSummary.nodeName === 'DETAILS' && !detailsOrSummary.open)
          result = false;
      }
      if (result && style.visibility !== 'visible')
        result = false;
    }
    cache.styleVisibility.set(element, result);
    return result;
  }

  function computeBox(element) {
    const style = getElementComputedStyle(element);
    if (!style)
      return { visible: true, inline: false };
    if (style.display === 'contents') {
      for (let child = element.firstChild; child; child = child.nextSibling) {
        if (child.nodeType === ELEMENT_NODE && isElementVisible(child))
          return { visible: true, inline: false };
        if (child.nodeType === TEXT_NODE && isVisibleTextNode(child))
          return { visible: true, inline: true };
      }
      return { visible: false, inline: false };
    }
    if (!isElementStyleVisibilityVisible(element, style))
      return { visible: false, inline: false };
    const rect = element.getBoundingClientRect();
    return { visible: rect.width > 0 && rect.height > 0, inline: style.display === 'inline' };
  }

  function isElementVisible(element) {
    return computeBox(element).visible;
  }

  function sortInDOMOrder(elements) {
    const elementToNodes = new Map();
    const roots = new Set();
    const result = [];
    function append(element) {
      let nodes = elementToNodes.get(element);
      if (nodes)
        return nodes;
      nodes = { children: new Set(), taken: false };
      elementToNodes.set(element, nodes);
      const parent = parentElementOrShadowHost(element);
      if (parent) {
        const parentNodes = append(parent);
        parentNodes.children.add(element);
      } else {
        roots.add(element);
      }
      return nodes;
    }
    elements.forEach(e => append(e).taken = true);
    function visit(element) {
      const nodes = elementToNodes.get(element);
      if (nodes.taken)
        result.push(element);
      if (nodes.children.size > 1) {
        const set = nodes.children;
        const ordered = [];
        if (element.shadowRoot)
          for (const child of element.shadowRoot.querySelectorAll('*'))
            if (set.has(child)) ordered.push(child);
        for (const child of element.querySelectorAll('*'))
          if (set.has(child)) ordered.push(child);
        for (const child of set)
          if (!ordered.includes(child)) ordered.push(child);
        ordered.forEach(visit);
      } else {
        nodes.children.forEach(visit);
      }
    }
    roots.forEach(visit);
    return result;
  }

  // ---------------------------------------------------------- selector parser

  const kNestedSelectorNames = new Set(['internal:has', 'internal:has-not', 'internal:and', 'internal:or', 'internal:chain']);

  function parseSelectorString(selector) {
    let index = 0;
    let quote;
    let start = 0;
    const result = { parts: [] };
    const append = () => {
      const part = selector.substring(start, index).trim();
      const eqIndex = part.indexOf('=');
      let name;
      let body;
      if (eqIndex !== -1 && part.substring(0, eqIndex).trim().match(/^[a-zA-Z_0-9-+:*]+$/)) {
        name = part.substring(0, eqIndex).trim();
        body = part.substring(eqIndex + 1);
      } else if (part.length > 1 && part[0] === '"' && part[part.length - 1] === '"') {
        name = 'text';
        body = part;
      } else if (part.length > 1 && part[0] === "'" && part[part.length - 1] === "'") {
        name = 'text';
        body = part;
      } else if (/^\(*\/\//.test(part) || part.startsWith('..')) {
        name = 'xpath';
        body = part;
      } else {
        name = 'css';
        body = part;
      }
      let capture = false;
      if (name[0] === '*') {
        capture = true;
        name = name.substring(1);
      }
      result.parts.push({ name, body });
      if (capture) {
        if (result.capture !== undefined)
          throw new InvalidSelectorError('Only one of the selectors can capture using * modifier');
        result.capture = result.parts.length - 1;
      }
    };

    if (!selector.includes('>>')) {
      index = selector.length;
      append();
      return result;
    }

    const shouldIgnoreTextSelectorQuote = () => {
      const prefix = selector.substring(start, index);
      const match = prefix.match(/^\s*text\s*=(.*)$/);
      return !!match && !!match[1];
    };

    while (index < selector.length) {
      const c = selector[index];
      if (c === '\\' && index + 1 < selector.length) {
        index += 2;
      } else if (c === quote) {
        quote = undefined;
        index++;
      } else if (!quote && (c === '"' || c === "'" || c === '`') && !shouldIgnoreTextSelectorQuote()) {
        quote = c;
        index++;
      } else if (!quote && c === '>' && selector[index + 1] === '>') {
        append();
        index += 2;
        start = index;
      } else {
        index++;
      }
    }
    append();
    return result;
  }

  function parseSelector(selector) {
    const parsedStrings = parseSelectorString(selector);
    const parts = [];
    for (const part of parsedStrings.parts) {
      if (part.name === 'css' || part.name === 'css:light') {
        parts.push({ name: 'css', body: part.body, source: part.body });
        continue;
      }
      if (kNestedSelectorNames.has(part.name)) {
        let innerSelector;
        try {
          const unescaped = JSON.parse('[' + part.body + ']');
          if (!Array.isArray(unescaped) || unescaped.length !== 1 || typeof unescaped[0] !== 'string')
            throw new InvalidSelectorError('Malformed selector: ' + part.name + '=' + part.body);
          innerSelector = unescaped[0];
        } catch (e) {
          throw new InvalidSelectorError('Malformed selector: ' + part.name + '=' + part.body);
        }
        parts.push({ name: part.name, source: part.body, body: { parsed: parseSelector(innerSelector) } });
        continue;
      }
      parts.push({ name: part.name, body: part.body, source: part.body });
    }
    if (kNestedSelectorNames.has(parts[0].name))
      throw new InvalidSelectorError('"' + parts[0].name + '" selector cannot be first');
    return { capture: parsedStrings.capture, parts };
  }

  function parseAttributeSelector(selector, allowUnquotedStrings) {
    let wp = 0;
    let EOL = selector.length === 0;
    const next = () => selector[wp] || '';
    const eat1 = () => {
      const result = next();
      ++wp;
      EOL = wp >= selector.length;
      return result;
    };
    const syntaxError = stage => {
      if (EOL)
        throw new InvalidSelectorError('Unexpected end of selector while parsing selector `' + selector + '`');
      throw new InvalidSelectorError('Error while parsing selector `' + selector + '` - unexpected symbol "' + next() + '" at position ' + wp + (stage ? ' during ' + stage : ''));
    };
    function skipSpaces() {
      while (!EOL && /\s/.test(next()))
        eat1();
    }
    function isCSSNameChar(char) {
      return (char >= '') || (char >= '0' && char <= '9') || (char >= 'A' && char <= 'Z') || (char >= 'a' && char <= 'z') || char === '_' || char === '-';
    }
    function readIdentifier() {
      let result = '';
      skipSpaces();
      while (!EOL && isCSSNameChar(next()))
        result += eat1();
      return result;
    }
    function readQuotedString(quote) {
      let result = eat1();
      if (result !== quote)
        syntaxError('parsing quoted string');
      while (!EOL && next() !== quote) {
        if (next() === '\\')
          eat1();
        result += eat1();
      }
      if (next() !== quote)
        syntaxError('parsing quoted string');
      result += eat1();
      return result;
    }
    function readRegularExpression() {
      if (eat1() !== '/')
        syntaxError('parsing regular expression');
      let source = '';
      let inClass = false;
      while (!EOL) {
        if (next() === '\\') {
          source += eat1();
          if (EOL)
            syntaxError('parsing regular expression');
        } else if (inClass && next() === ']') {
          inClass = false;
        } else if (!inClass && next() === '[') {
          inClass = true;
        } else if (!inClass && next() === '/') {
          break;
        }
        source += eat1();
      }
      if (eat1() !== '/')
        syntaxError('parsing regular expression');
      let flags = '';
      while (!EOL && next().match(/[dgimsuvy]/))
        flags += eat1();
      try {
        return new RegExp(source, flags);
      } catch (e) {
        throw new InvalidSelectorError('Error while parsing selector `' + selector + '`: ' + e.message);
      }
    }
    function readAttributeToken() {
      let token = '';
      skipSpaces();
      if (next() === "'" || next() === '"')
        token = readQuotedString(next()).slice(1, -1);
      else
        token = readIdentifier();
      if (!token)
        syntaxError('parsing property path');
      return token;
    }
    function readOperator() {
      skipSpaces();
      let op = '';
      if (!EOL)
        op += eat1();
      if (!EOL && (op !== '='))
        op += eat1();
      if (!['=', '*=', '^=', '$=', '|=', '~='].includes(op))
        syntaxError('parsing operator');
      return op;
    }
    function readAttribute() {
      eat1();
      const jsonPath = [];
      jsonPath.push(readAttributeToken());
      skipSpaces();
      while (next() === '.') {
        eat1();
        jsonPath.push(readAttributeToken());
        skipSpaces();
      }
      if (next() === ']') {
        eat1();
        return { name: jsonPath.join('.'), jsonPath, op: '<truthy>', value: null, caseSensitive: false };
      }
      const operator = readOperator();
      let value;
      let caseSensitive = true;
      skipSpaces();
      if (next() === '/') {
        if (operator !== '=')
          throw new InvalidSelectorError('Error while parsing selector `' + selector + '` - cannot use ' + operator + ' in attribute with regular expression');
        value = readRegularExpression();
      } else if (next() === "'" || next() === '"') {
        value = readQuotedString(next()).slice(1, -1);
        skipSpaces();
        if (next() === 'i' || next() === 'I') {
          caseSensitive = false;
          eat1();
        } else if (next() === 's' || next() === 'S') {
          caseSensitive = true;
          eat1();
        }
      } else {
        value = '';
        while (!EOL && (isCSSNameChar(next()) || next() === '+' || next() === '.'))
          value += eat1();
        if (value === 'true') {
          value = true;
        } else if (value === 'false') {
          value = false;
        } else if (!allowUnquotedStrings) {
          value = +value;
          if (Number.isNaN(value))
            syntaxError('parsing attribute value');
        }
      }
      skipSpaces();
      if (next() !== ']')
        syntaxError('parsing attribute value');
      eat1();
      if (operator !== '=' && typeof value !== 'string')
        throw new InvalidSelectorError('Error while parsing selector `' + selector + '` - cannot use ' + operator + ' in attribute with non-string matching value - ' + value);
      return { name: jsonPath.join('.'), jsonPath, op: operator, value, caseSensitive };
    }
    const result = { name: '', attributes: [] };
    result.name = readIdentifier();
    skipSpaces();
    while (next() === '[') {
      result.attributes.push(readAttribute());
      skipSpaces();
    }
    if (!EOL)
      syntaxError(undefined);
    if (!result.name && !result.attributes.length)
      throw new InvalidSelectorError('Error while parsing selector `' + selector + '` - selector cannot be empty');
    return result;
  }

  function matchesAttributePart(value, attr) {
    const objValue = typeof value === 'string' && !attr.caseSensitive ? value.toUpperCase() : value;
    const attrValue = typeof attr.value === 'string' && !attr.caseSensitive ? attr.value.toUpperCase() : attr.value;
    if (attr.op === '<truthy>')
      return !!objValue;
    if (attr.op === '=') {
      if (attrValue instanceof RegExp) {
        attrValue.lastIndex = 0;
        return typeof objValue === 'string' && !!objValue.match(attrValue);
      }
      return objValue === attrValue;
    }
    if (typeof objValue !== 'string' || typeof attrValue !== 'string')
      return false;
    if (attr.op === '*=')
      return objValue.includes(attrValue);
    if (attr.op === '^=')
      return objValue.startsWith(attrValue);
    if (attr.op === '$=')
      return objValue.endsWith(attrValue);
    if (attr.op === '|=')
      return objValue === attrValue || objValue.startsWith(attrValue + '-');
    if (attr.op === '~=')
      return objValue.split(' ').includes(attrValue);
    return false;
  }

  function createAttributeMatcher(part) {
    const { value, caseSensitive } = part;
    if (value instanceof RegExp) {
      return s => {
        value.lastIndex = 0;
        return !!s.match(value);
      };
    }
    if (caseSensitive)
      return s => s === value;
    const lowerCaseValue = String(value).toLowerCase();
    return s => s.toLowerCase().includes(lowerCaseValue);
  }

  // ---------------------------------------------------------------- text

  function shouldSkipForTextMatching(element) {
    const document = element.ownerDocument;
    return element.nodeName === 'SCRIPT' || element.nodeName === 'NOSCRIPT' || element.nodeName === 'STYLE' || (document.head && document.head.contains(element));
  }

  function elementText(root) {
    let value = cache.text.get(root);
    if (value === undefined) {
      value = { full: '', normalized: '', immediate: [] };
      if (!shouldSkipForTextMatching(root)) {
        let currentImmediate = '';
        if ((root instanceof HTMLInputElement) && (root.type === 'submit' || root.type === 'button' || root.type === 'reset')) {
          value = { full: root.value, normalized: normalizeWhiteSpace(root.value), immediate: [root.value] };
        } else {
          for (let child = root.firstChild; child; child = child.nextSibling) {
            if (child.nodeType === TEXT_NODE) {
              value.full += child.nodeValue || '';
              currentImmediate += child.nodeValue || '';
            } else if (child.nodeType === COMMENT_NODE) {
              continue;
            } else {
              if (currentImmediate)
                value.immediate.push(currentImmediate);
              currentImmediate = '';
              if (child.nodeType === ELEMENT_NODE)
                value.full += elementText(child).full;
            }
          }
          if (currentImmediate)
            value.immediate.push(currentImmediate);
          if (root.shadowRoot)
            value.full += elementText(root.shadowRoot).full;
          if (value.full)
            value.normalized = normalizeWhiteSpace(value.full);
        }
      }
      cache.text.set(root, value);
    }
    return value;
  }

  function textMatch(element, matcher) {
    if (shouldSkipForTextMatching(element))
      return 'none';
    if (!matcher(elementText(element)))
      return 'none';
    for (let child = element.firstChild; child; child = child.nextSibling) {
      if (child.nodeType === ELEMENT_NODE && matcher(elementText(child)))
        return 'selfAndChildren';
    }
    if (element.shadowRoot && matcher(elementText(element.shadowRoot)))
      return 'selfAndChildren';
    return 'self';
  }

  function textMatcher(selector, internal) {
    if (selector[0] === '/' && selector.lastIndexOf('/') > 0) {
      const lastSlash = selector.lastIndexOf('/');
      const re = new RegExp(selector.substring(1, lastSlash), selector.substring(lastSlash + 1));
      const matcher = text => {
        re.lastIndex = 0;
        return re.test(text.full);
      };
      return { matcher, kind: 'regex' };
    }
    const unquote = internal ? JSON.parse.bind(JSON) : cssUnquote;
    let strict = false;
    if (selector.length > 1 && selector[0] === '"' && selector[selector.length - 1] === '"') {
      selector = unquote(selector);
      strict = true;
    } else if (internal && selector.length > 1 && selector[0] === '"' && selector[selector.length - 2] === '"' && selector[selector.length - 1] === 'i') {
      selector = unquote(selector.substring(0, selector.length - 1));
      strict = false;
    } else if (internal && selector.length > 1 && selector[0] === '"' && selector[selector.length - 2] === '"' && selector[selector.length - 1] === 's') {
      selector = unquote(selector.substring(0, selector.length - 1));
      strict = true;
    } else if (selector.length > 1 && selector[0] === "'" && selector[selector.length - 1] === "'") {
      selector = unquote(selector);
      strict = true;
    }
    selector = normalizeWhiteSpace(selector);
    if (strict) {
      if (internal)
        return { kind: 'strict', matcher: text => text.normalized === selector };
      const strictTextNodeMatcher = text => {
        if (!selector && !text.immediate.length)
          return true;
        return text.immediate.some(s => normalizeWhiteSpace(s) === selector);
      };
      return { matcher: strictTextNodeMatcher, kind: 'strict' };
    }
    selector = selector.toLowerCase();
    return { kind: 'lax', matcher: text => text.normalized.toLowerCase().includes(selector) };
  }

  function getElementLabels(element) {
    let labels = getAriaLabelledByElements(element);
    if (labels)
      return labels.map(label => elementText(label));
    const ariaLabel = element.getAttribute('aria-label');
    if (ariaLabel !== null && !!ariaLabel.trim())
      return [{ full: ariaLabel, normalized: normalizeWhiteSpace(ariaLabel), immediate: [ariaLabel] }];
    const isNonHiddenInput = element.nodeName === 'INPUT' && element.type !== 'hidden';
    if (['BUTTON', 'METER', 'OUTPUT', 'PROGRESS', 'SELECT', 'TEXTAREA'].includes(element.nodeName) || isNonHiddenInput) {
      const labels = element.labels;
      if (labels)
        return [...labels].map(label => elementText(label));
    }
    return [];
  }

  // ----------------------------------------------------------------- roles

  function hasExplicitAccessibleName(e) {
    return e.hasAttribute('aria-label') || e.hasAttribute('aria-labelledby');
  }

  const kAncestorPreventingLandmark = 'article:not([role]), aside:not([role]), main:not([role]), nav:not([role]), section:not([role]), [role=article], [role=complementary], [role=main], [role=navigation], [role=region]';

  const kGlobalAriaAttributes = [
    ['aria-atomic', undefined],
    ['aria-busy', undefined],
    ['aria-controls', undefined],
    ['aria-current', undefined],
    ['aria-describedby', undefined],
    ['aria-details', undefined],
    ['aria-dropeffect', undefined],
    ['aria-flowto', undefined],
    ['aria-grabbed', undefined],
    ['aria-hidden', undefined],
    ['aria-keyshortcuts', undefined],
    ['aria-label', ['caption', 'code', 'deletion', 'emphasis', 'generic', 'insertion', 'paragraph', 'presentation', 'strong', 'subscript', 'superscript']],
    ['aria-labelledby', ['caption', 'code', 'deletion', 'emphasis', 'generic', 'insertion', 'paragraph', 'presentation', 'strong', 'subscript', 'superscript']],
    ['aria-live', undefined],
    ['aria-owns', undefined],
    ['aria-relevant', undefined],
    ['aria-roledescription', ['generic']],
  ];

  function hasGlobalAriaAttribute(element, forRole) {
    return kGlobalAriaAttributes.some(([attr, prohibited]) => {
      return !(prohibited && prohibited.includes(forRole || '')) && element.hasAttribute(attr);
    });
  }

  function hasTabIndex(element) {
    return !Number.isNaN(Number(String(element.getAttribute('tabindex'))));
  }

  function isFocusable(element) {
    return !isNativelyDisabled(element) && (isNativelyFocusable(element) || hasTabIndex(element));
  }

  function isNativelyFocusable(element) {
    const tagName = elementSafeTagName(element);
    if (['BUTTON', 'DETAILS', 'SELECT', 'TEXTAREA'].includes(tagName))
      return true;
    if (tagName === 'A' || tagName === 'AREA')
      return element.hasAttribute('href');
    if (tagName === 'INPUT')
      return !element.hidden;
    return false;
  }

  const inputTypeToRole = {
    'button': 'button',
    'checkbox': 'checkbox',
    'image': 'button',
    'number': 'spinbutton',
    'radio': 'radio',
    'range': 'slider',
    'reset': 'button',
    'submit': 'button',
  };

  const kImplicitRoleByTagName = {
    'A': e => e.hasAttribute('href') ? 'link' : null,
    'AREA': e => e.hasAttribute('href') ? 'link' : null,
    'ARTICLE': () => 'article',
    'ASIDE': () => 'complementary',
    'BLOCKQUOTE': () => 'blockquote',
    'BUTTON': () => 'button',
    'CAPTION': () => 'caption',
    'CODE': () => 'code',
    'DATALIST': () => 'listbox',
    'DD': () => 'definition',
    'DEL': () => 'deletion',
    'DETAILS': () => 'group',
    'DFN': () => 'term',
    'DIALOG': () => 'dialog',
    'DT': () => 'term',
    'EM': () => 'emphasis',
    'FIELDSET': () => 'group',
    'FIGURE': () => 'figure',
    'FOOTER': e => closestCrossShadow(e, kAncestorPreventingLandmark) ? null : 'contentinfo',
    'FORM': e => hasExplicitAccessibleName(e) ? 'form' : null,
    'H1': () => 'heading',
    'H2': () => 'heading',
    'H3': () => 'heading',
    'H4': () => 'heading',
    'H5': () => 'heading',
    'H6': () => 'heading',
    'HEADER': e => closestCrossShadow(e, kAncestorPreventingLandmark) ? null : 'banner',
    'HR': () => 'separator',
    'HTML': () => 'document',
    'IMG': e => (e.getAttribute('alt') === '') && !e.getAttribute('title') && !hasGlobalAriaAttribute(e) && !hasTabIndex(e) ? 'presentation' : 'img',
    'INPUT': e => {
      const type = e.type.toLowerCase();
      if (['email', 'search', 'tel', 'text', 'url', ''].includes(type)) {
        const list = getIdRefs(e, e.getAttribute('list'))[0];
        if (list && elementSafeTagName(list) === 'DATALIST')
          return 'combobox';
        return type === 'search' ? 'searchbox' : 'textbox';
      }
      if (type === 'hidden')
        return null;
      if (type === 'file')
        return 'button';
      return inputTypeToRole[type] || 'textbox';
    },
    'INS': () => 'insertion',
    'LI': () => 'listitem',
    'MAIN': () => 'main',
    'MARK': () => 'mark',
    'MATH': () => 'math',
    'MENU': () => 'list',
    'METER': () => 'meter',
    'NAV': () => 'navigation',
    'OL': () => 'list',
    'OPTGROUP': () => 'group',
    'OPTION': () => 'option',
    'OUTPUT': () => 'status',
    'P': () => 'paragraph',
    'PROGRESS': () => 'progressbar',
    'SEARCH': () => 'search',
    'SECTION': e => hasExplicitAccessibleName(e) ? 'region' : null,
    'SELECT': e => e.hasAttribute('multiple') || e.size > 1 ? 'listbox' : 'combobox',
    'STRONG': () => 'strong',
    'SUB': () => 'subscript',
    'SUP': () => 'superscript',
    'SVG': () => 'img',
    'TABLE': () => 'table',
    'TBODY': () => 'rowgroup',
    'TD': e => {
      const table = closestCrossShadow(e, 'table');
      const role = table ? getExplicitAriaRole(table) : '';
      return (role === 'grid' || role === 'treegrid') ? 'gridcell' : 'cell';
    },
    'TEXTAREA': () => 'textbox',
    'TFOOT': () => 'rowgroup',
    'TH': e => {
      const scope = e.getAttribute('scope');
      if (scope === 'col' || scope === 'colgroup')
        return 'columnheader';
      if (scope === 'row' || scope === 'rowgroup')
        return 'rowheader';
      const nextSibling = e.nextElementSibling;
      const prevSibling = e.previousElementSibling;
      const row = !!e.parentElement && elementSafeTagName(e.parentElement) === 'TR' ? e.parentElement : undefined;
      if (!nextSibling && !prevSibling) {
        if (row) {
          const table = closestCrossShadow(row, 'table');
          if (table && table.rows.length <= 1)
            return null;
        }
        return 'columnheader';
      }
      if (isHeaderCell(nextSibling) && isHeaderCell(prevSibling))
        return 'columnheader';
      if (isNonEmptyDataCell(nextSibling) || isNonEmptyDataCell(prevSibling))
        return 'rowheader';
      return 'columnheader';
    },
    'THEAD': () => 'rowgroup',
    'TIME': () => 'time',
    'TR': () => 'row',
    'UL': () => 'list',
  };

  function isHeaderCell(element) {
    return !!element && elementSafeTagName(element) === 'TH';
  }

  function isNonEmptyDataCell(element) {
    if (!element || elementSafeTagName(element) !== 'TD')
      return false;
    return !!((element.textContent && element.textContent.trim()) || element.children.length > 0);
  }

  const kPresentationInheritanceParents = {
    'DD': ['DL', 'DIV'],
    'DIV': ['DL'],
    'DT': ['DL', 'DIV'],
    'LI': ['OL', 'UL'],
    'TBODY': ['TABLE'],
    'TD': ['TR'],
    'TFOOT': ['TABLE'],
    'TH': ['TR'],
    'THEAD': ['TABLE'],
    'TR': ['THEAD', 'TBODY', 'TFOOT', 'TABLE'],
  };

  function getImplicitAriaRole(element) {
    const compute = kImplicitRoleByTagName[elementSafeTagName(element)];
    const implicitRole = (compute && compute(element)) || '';
    if (!implicitRole)
      return null;
    let ancestor = element;
    while (ancestor) {
      const parent = parentElementOrShadowHost(ancestor);
      const parents = kPresentationInheritanceParents[elementSafeTagName(ancestor)];
      if (!parents || !parent || !parents.includes(elementSafeTagName(parent)))
        break;
      const parentExplicitRole = getExplicitAriaRole(parent);
      if ((parentExplicitRole === 'none' || parentExplicitRole === 'presentation') && !hasPresentationConflictResolution(parent, parentExplicitRole))
        return parentExplicitRole;
      ancestor = parent;
    }
    return implicitRole;
  }

  const validRoles = ['alert', 'alertdialog', 'application', 'article', 'banner', 'blockquote', 'button', 'caption', 'cell', 'checkbox', 'code', 'columnheader', 'combobox',
    'complementary', 'contentinfo', 'definition', 'deletion', 'dialog', 'directory', 'document', 'emphasis', 'feed', 'figure', 'form', 'generic', 'grid',
    'gridcell', 'group', 'heading', 'img', 'insertion', 'link', 'list', 'listbox', 'listitem', 'log', 'main', 'mark', 'marquee', 'math', 'meter', 'menu',
    'menubar', 'menuitem', 'menuitemcheckbox', 'menuitemradio', 'navigation', 'none', 'note', 'option', 'paragraph', 'presentation', 'progressbar', 'radio', 'radiogroup',
    'region', 'row', 'rowgroup', 'rowheader', 'scrollbar', 'search', 'searchbox', 'separator', 'slider',
    'spinbutton', 'status', 'strong', 'subscript', 'superscript', 'switch', 'tab', 'table', 'tablist', 'tabpanel', 'term', 'textbox', 'time', 'timer',
    'toolbar', 'tooltip', 'tree', 'treegrid', 'treeitem'];

  function getExplicitAriaRole(element) {
    const roles = (element.getAttribute('role') || '').split(' ').map(role => role.trim());
    return roles.find(role => validRoles.includes(role)) || null;
  }

  function hasPresentationConflictResolution(element, role) {
    return hasGlobalAriaAttribute(element, role) || isFocusable(element);
  }

  function ariaRole(element) {
    const cached = cache.ariaRole.get(element);
    if (cached !== undefined)
      return cached;
    const role = computeAriaRole(element);
    cache.ariaRole.set(element, role);
    return role;
  }

  function computeAriaRole(element) {
    const explicitRole = getExplicitAriaRole(element);
    if (!explicitRole)
      return getImplicitAriaRole(element);
    if (explicitRole === 'none' || explicitRole === 'presentation') {
      const implicitRole = getImplicitAriaRole(element);
      if (hasPresentationConflictResolution(element, implicitRole))
        return implicitRole;
    }
    return explicitRole;
  }

  function getAriaBoolean(attr) {
    return attr === null ? undefined : attr.toLowerCase() === 'true';
  }

  function isElementIgnoredForAria(element) {
    return ['STYLE', 'SCRIPT', 'NOSCRIPT', 'TEMPLATE'].includes(elementSafeTagName(element));
  }

  function ariaHidden(element) {
    if (isElementIgnoredForAria(element))
      return true;
    const style = getElementComputedStyle(element);
    const isSlot = element.nodeName === 'SLOT';
    if (style && style.display === 'contents' && !isSlot) {
      for (let child = element.firstChild; child; child = child.nextSibling) {
        if (child.nodeType === ELEMENT_NODE && !ariaHidden(child))
          return false;
        if (child.nodeType === TEXT_NODE && isVisibleTextNode(child))
          return false;
      }
      return true;
    }
    const isOptionInsideSelect = element.nodeName === 'OPTION' && !!element.closest('select');
    if (!isOptionInsideSelect && !isSlot && !isElementStyleVisibilityVisible(element, style))
      return true;
    return belongsToDisplayNoneOrAriaHiddenOrNonSlotted(element);
  }

  function belongsToDisplayNoneOrAriaHiddenOrNonSlotted(element) {
    let hidden = cache.isHidden.get(element);
    if (hidden === undefined) {
      hidden = false;
      if (element.parentElement && element.parentElement.shadowRoot && !element.assignedSlot)
        hidden = true;
      if (!hidden) {
        const style = getElementComputedStyle(element);
        hidden = !style || style.display === 'none' || getAriaBoolean(element.getAttribute('aria-hidden')) === true;
      }
      if (!hidden) {
        const parent = parentElementOrShadowHost(element);
        if (parent)
          hidden = belongsToDisplayNoneOrAriaHiddenOrNonSlotted(parent);
      }
      cache.isHidden.set(element, hidden);
    }
    return hidden;
  }

  function getIdRefs(element, ref) {
    if (!ref)
      return [];
    const root = enclosingShadowRootOrDocument(element);
    if (!root)
      return [];
    try {
      const ids = ref.split(' ').filter(id => !!id);
      const result = [];
      for (const id of ids) {
        const firstElement = root.querySelector('#' + CSS.escape(id));
        if (firstElement && !result.includes(firstElement))
          result.push(firstElement);
      }
      return result;
    } catch (e) {
      return [];
    }
  }

  function queryInAriaOwned(element, selector) {
    const result = [...element.querySelectorAll(selector)];
    for (const owned of getIdRefs(element, element.getAttribute('aria-owns'))) {
      if (owned.matches(selector))
        result.push(owned);
      result.push(...owned.querySelectorAll(selector));
    }
    return result;
  }

  function parseCSSContentPropertyAsString(element, content, isPseudo) {
    if (!content || content === 'none' || content === 'normal')
      return undefined;
    const tokens = [];
    const re = /"((?:[^"\\]|\\.)*)"|'((?:[^'\\]|\\.)*)'|attr\(\s*([\w-]+)\s*\)|(\/)|(\S+)/g;
    let match;
    while ((match = re.exec(content)) !== null) {
      if (match[1] !== undefined)
        tokens.push({ kind: 'string', value: match[1].replace(/\\(.)/g, '$1') });
      else if (match[2] !== undefined)
        tokens.push({ kind: 'string', value: match[2].replace(/\\(.)/g, '$1') });
      else if (match[3] !== undefined)
        tokens.push({ kind: 'attr', value: element.getAttribute(match[3]) || '' });
      else if (match[4] !== undefined)
        tokens.push({ kind: 'delim' });
      else
        tokens.push({ kind: 'other' });
    }
    let list = tokens;
    const delimIndex = tokens.findIndex(token => token.kind === 'delim');
    if (delimIndex !== -1)
      list = tokens.slice(delimIndex + 1);
    else if (!isPseudo)
      return undefined;
    if (list.some(token => token.kind === 'other'))
      return undefined;
    return list.map(token => token.value).join('');
  }

  function getCSSContent(element, pseudo) {
    const map = pseudo === '::before' ? cache.pseudoContentBefore : (pseudo === '::after' ? cache.pseudoContentAfter : cache.pseudoContent);
    if (map.has(element))
      return map.get(element);
    const style = getElementComputedStyle(element, pseudo);
    let content;
    if (style) {
      const contentValue = style.content;
      if (contentValue && contentValue !== 'none' && contentValue !== 'normal') {
        if (style.display !== 'none' && style.visibility !== 'hidden')
          content = parseCSSContentPropertyAsString(element, contentValue, !!pseudo);
      }
    }
    if (pseudo && content !== undefined) {
      const display = (style && style.display) || 'inline';
      if (display !== 'inline')
        content = ' ' + content + ' ';
    }
    map.set(element, content);
    return content;
  }

  function getAriaLabelledByElements(element) {
    const ref = element.getAttribute('aria-labelledby');
    if (ref === null)
      return null;
    const refs = getIdRefs(element, ref);
    return refs.length ? refs : null;
  }

  function allowsNameFromContent(role, targetDescendant) {
    const alwaysAllowsNameFromContent = ['button', 'cell', 'checkbox', 'columnheader', 'gridcell', 'heading', 'link', 'menuitem', 'menuitemcheckbox', 'menuitemradio', 'option', 'radio', 'row', 'rowheader', 'switch', 'tab', 'tooltip', 'treeitem'].includes(role);
    const descendantAllowsNameFromContent = targetDescendant && ['', 'caption', 'code', 'contentinfo', 'definition', 'deletion', 'emphasis', 'insertion', 'list', 'listitem', 'mark', 'none', 'paragraph', 'presentation', 'region', 'row', 'rowgroup', 'section', 'strong', 'subscript', 'superscript', 'table', 'term', 'time'].includes(role);
    return alwaysAllowsNameFromContent || descendantAllowsNameFromContent;
  }

  function accessibleName(element, includeHidden) {
    const map = includeHidden ? cache.accessibleNameHidden : cache.accessibleName;
    let accessibleName = map.get(element);
    if (accessibleName === undefined) {
      accessibleName = '';
      const elementProhibitsNaming = ['caption', 'code', 'definition', 'deletion', 'emphasis', 'generic', 'insertion', 'mark', 'paragraph', 'presentation', 'strong', 'subscript', 'suggestion', 'superscript', 'term', 'time'].includes(ariaRole(element) || '');
      if (!elementProhibitsNaming) {
        accessibleName = asFlatString(textAlternative(element, {
          includeHidden,
          visitedElements: new Set(),
          embeddedInTargetElement: 'self',
        }));
      }
      map.set(element, accessibleName);
    }
    return accessibleName;
  }

  function getElementAccessibleDescription(element, includeHidden) {
    if (element.hasAttribute('aria-describedby')) {
      const describedBy = getIdRefs(element, element.getAttribute('aria-describedby'));
      return asFlatString(describedBy.map(ref => textAlternative(ref, {
        includeHidden,
        visitedElements: new Set(),
        embeddedInDescribedBy: { element: ref, hidden: ariaHidden(ref) },
      })).join(' '));
    }
    if (element.hasAttribute('aria-description'))
      return asFlatString(element.getAttribute('aria-description') || '');
    return asFlatString(element.getAttribute('title') || '');
  }

  function textAlternative(element, options) {
    if (options.visitedElements.has(element))
      return '';
    const childOptions = Object.assign({}, options, {
      embeddedInTargetElement: options.embeddedInTargetElement === 'self' ? 'descendant' : options.embeddedInTargetElement,
    });

    if (!options.includeHidden) {
      const isEmbeddedInHiddenReferenceTraversal =
        !!(options.embeddedInLabelledBy && options.embeddedInLabelledBy.hidden) ||
        !!(options.embeddedInDescribedBy && options.embeddedInDescribedBy.hidden) ||
        !!(options.embeddedInNativeTextAlternative && options.embeddedInNativeTextAlternative.hidden) ||
        !!(options.embeddedInLabel && options.embeddedInLabel.hidden);
      if (isElementIgnoredForAria(element) || (!isEmbeddedInHiddenReferenceTraversal && ariaHidden(element))) {
        options.visitedElements.add(element);
        return '';
      }
    }

    const labelledBy = getAriaLabelledByElements(element);

    if (!options.embeddedInLabelledBy) {
      const accessibleName = (labelledBy || []).map(ref => textAlternative(ref, Object.assign({}, options, {
        embeddedInLabelledBy: { element: ref, hidden: ariaHidden(ref) },
        embeddedInDescribedBy: undefined,
        embeddedInTargetElement: undefined,
        embeddedInLabel: undefined,
        embeddedInNativeTextAlternative: undefined,
      }))).join(' ');
      if (accessibleName)
        return accessibleName;
    }

    const role = ariaRole(element) || '';
    const tagName = elementSafeTagName(element);

    if (!!options.embeddedInLabel || !!options.embeddedInLabelledBy || options.embeddedInTargetElement === 'descendant') {
      const isOwnLabel = [...(element.labels || [])].includes(element);
      const isOwnLabelledBy = (labelledBy || []).includes(element);
      if (!isOwnLabel && !isOwnLabelledBy) {
        if (role === 'textbox' || role === 'searchbox') {
          options.visitedElements.add(element);
          if (tagName === 'INPUT' || tagName === 'TEXTAREA')
            return element.value;
          return element.textContent || '';
        }
        if (['combobox', 'listbox'].includes(role)) {
          options.visitedElements.add(element);
          let selectedOptions;
          if (tagName === 'SELECT') {
            selectedOptions = [...element.selectedOptions];
            if (!selectedOptions.length && element.options.length)
              selectedOptions.push(element.options[0]);
          } else {
            const listbox = role === 'combobox' ? queryInAriaOwned(element, '*').find(e => ariaRole(e) === 'listbox') : element;
            selectedOptions = listbox ? queryInAriaOwned(listbox, '[aria-selected="true"]').filter(e => ariaRole(e) === 'option') : [];
          }
          if (!selectedOptions.length && tagName === 'INPUT')
            return element.value;
          return selectedOptions.map(option => textAlternative(option, childOptions)).join(' ');
        }
        if (['progressbar', 'scrollbar', 'slider', 'spinbutton', 'meter'].includes(role)) {
          options.visitedElements.add(element);
          if (element.hasAttribute('aria-valuetext'))
            return element.getAttribute('aria-valuetext') || '';
          if (element.hasAttribute('aria-valuenow'))
            return element.getAttribute('aria-valuenow') || '';
          return element.getAttribute('value') || '';
        }
        if (['menu'].includes(role)) {
          options.visitedElements.add(element);
          return '';
        }
      }
    }

    const ariaLabel = element.getAttribute('aria-label') || '';
    if (trimFlatString(ariaLabel)) {
      options.visitedElements.add(element);
      return ariaLabel;
    }

    if (!['presentation', 'none'].includes(role)) {
      if (tagName === 'INPUT' && ['button', 'submit', 'reset'].includes(element.type)) {
        options.visitedElements.add(element);
        const value = element.value || '';
        if (trimFlatString(value))
          return value;
        if (element.type === 'submit')
          return 'Submit';
        if (element.type === 'reset')
          return 'Reset';
        return element.getAttribute('title') || '';
      }
      if (tagName === 'INPUT' && element.type === 'file') {
        options.visitedElements.add(element);
        const labels = element.labels || [];
        if (labels.length && !options.embeddedInLabelledBy)
          return getAccessibleNameFromAssociatedLabels(labels, options);
        return 'Choose File';
      }
      if (tagName === 'INPUT' && element.type === 'image') {
        options.visitedElements.add(element);
        const labels = element.labels || [];
        if (labels.length && !options.embeddedInLabelledBy)
          return getAccessibleNameFromAssociatedLabels(labels, options);
        const alt = element.getAttribute('alt') || '';
        if (trimFlatString(alt))
          return alt;
        const title = element.getAttribute('title') || '';
        if (trimFlatString(title))
          return title;
        return 'Submit';
      }
      if (!labelledBy && tagName === 'BUTTON') {
        options.visitedElements.add(element);
        const labels = element.labels || [];
        if (labels.length)
          return getAccessibleNameFromAssociatedLabels(labels, options);
      }
      if (!labelledBy && tagName === 'OUTPUT') {
        options.visitedElements.add(element);
        const labels = element.labels || [];
        if (labels.length)
          return getAccessibleNameFromAssociatedLabels(labels, options);
        return element.getAttribute('title') || '';
      }
      if (!labelledBy && (tagName === 'TEXTAREA' || tagName === 'SELECT' || tagName === 'INPUT' || tagName === 'METER' || tagName === 'PROGRESS')) {
        options.visitedElements.add(element);
        const labels = element.labels || [];
        if (labels.length)
          return getAccessibleNameFromAssociatedLabels(labels, options);
        const usePlaceholder = (tagName === 'INPUT' && ['text', 'password', 'number', 'search', 'tel', 'email', 'url'].includes(element.type)) || tagName === 'TEXTAREA';
        const placeholder = element.getAttribute('placeholder') || '';
        const title = element.getAttribute('title') || '';
        if (!usePlaceholder || title)
          return title;
        return placeholder;
      }
      if (!labelledBy && tagName === 'FIELDSET') {
        options.visitedElements.add(element);
        for (let child = element.firstElementChild; child; child = child.nextElementSibling) {
          if (elementSafeTagName(child) === 'LEGEND') {
            return textAlternative(child, Object.assign({}, childOptions, {
              embeddedInNativeTextAlternative: { element: child, hidden: ariaHidden(child) },
            }));
          }
        }
        return element.getAttribute('title') || '';
      }
      if (!labelledBy && tagName === 'FIGURE') {
        options.visitedElements.add(element);
        for (let child = element.firstElementChild; child; child = child.nextElementSibling) {
          if (elementSafeTagName(child) === 'FIGCAPTION') {
            return textAlternative(child, Object.assign({}, childOptions, {
              embeddedInNativeTextAlternative: { element: child, hidden: ariaHidden(child) },
            }));
          }
        }
        return element.getAttribute('title') || '';
      }
      if (tagName === 'IMG') {
        options.visitedElements.add(element);
        const alt = element.getAttribute('alt') || '';
        if (trimFlatString(alt))
          return alt;
        return element.getAttribute('title') || '';
      }
      if (tagName === 'TABLE') {
        options.visitedElements.add(element);
        for (let child = element.firstElementChild; child; child = child.nextElementSibling) {
          if (elementSafeTagName(child) === 'CAPTION') {
            return textAlternative(child, Object.assign({}, childOptions, {
              embeddedInNativeTextAlternative: { element: child, hidden: ariaHidden(child) },
            }));
          }
        }
        const summary = element.getAttribute('summary') || '';
        if (summary)
          return summary;
      }
      if (tagName === 'AREA') {
        options.visitedElements.add(element);
        const alt = element.getAttribute('alt') || '';
        if (trimFlatString(alt))
          return alt;
        return element.getAttribute('title') || '';
      }
      if (tagName === 'SVG' || element.ownerSVGElement) {
        options.visitedElements.add(element);
        for (let child = element.firstElementChild; child; child = child.nextElementSibling) {
          if (elementSafeTagName(child) === 'TITLE' && child.ownerSVGElement) {
            return textAlternative(child, Object.assign({}, childOptions, {
              embeddedInLabelledBy: { element: child, hidden: ariaHidden(child) },
            }));
          }
        }
      }
      if (element.ownerSVGElement && tagName === 'A') {
        const title = element.getAttribute('xlink:title') || '';
        if (trimFlatString(title)) {
          options.visitedElements.add(element);
          return title;
        }
      }
    }

    const shouldNameFromContentForSummary = tagName === 'SUMMARY' && !['presentation', 'none'].includes(role);

    if (allowsNameFromContent(role, options.embeddedInTargetElement === 'descendant') ||
        shouldNameFromContentForSummary ||
        !!options.embeddedInLabelledBy || !!options.embeddedInDescribedBy ||
        !!options.embeddedInLabel || !!options.embeddedInNativeTextAlternative) {
      options.visitedElements.add(element);
      const accessibleName = accumulatedText(element, childOptions);
      const maybeTrimmedAccessibleName = options.embeddedInTargetElement === 'self' ? trimFlatString(accessibleName) : accessibleName;
      if (maybeTrimmedAccessibleName)
        return accessibleName;
    }

    if (!['presentation', 'none'].includes(role) || tagName === 'IFRAME' || tagName === 'FRAME') {
      options.visitedElements.add(element);
      const title = element.getAttribute('title') || '';
      if (trimFlatString(title))
        return title;
    }

    options.visitedElements.add(element);
    return '';
  }

  function accumulatedText(element, options) {
    const tokens = [];
    const visit = (node, skipSlotted) => {
      if (skipSlotted && node.assignedSlot)
        return;
      if (node.nodeType === ELEMENT_NODE) {
        const style = getElementComputedStyle(node);
        const display = (style && style.display) || 'inline';
        let token = textAlternative(node, options);
        if (display !== 'inline' || node.nodeName === 'BR')
          token = ' ' + token + ' ';
        tokens.push(token);
      } else if (node.nodeType === TEXT_NODE) {
        tokens.push(node.textContent || '');
      }
    };
    tokens.push(getCSSContent(element, '::before') || '');
    const content = getCSSContent(element);
    if (content !== undefined) {
      tokens.push(content);
    } else {
      const assignedNodes = element.nodeName === 'SLOT' ? element.assignedNodes() : [];
      if (assignedNodes.length) {
        for (const child of assignedNodes)
          visit(child, false);
      } else {
        for (let child = element.firstChild; child; child = child.nextSibling)
          visit(child, true);
        if (element.shadowRoot) {
          for (let child = element.shadowRoot.firstChild; child; child = child.nextSibling)
            visit(child, true);
        }
        for (const owned of getIdRefs(element, element.getAttribute('aria-owns')))
          visit(owned, true);
      }
    }
    tokens.push(getCSSContent(element, '::after') || '');
    return tokens.join('');
  }

  function getAccessibleNameFromAssociatedLabels(labels, options) {
    return [...labels].map(label => textAlternative(label, Object.assign({}, options, {
      embeddedInLabel: { element: label, hidden: ariaHidden(label) },
      embeddedInNativeTextAlternative: undefined,
      embeddedInLabelledBy: undefined,
      embeddedInDescribedBy: undefined,
      embeddedInTargetElement: undefined,
    }))).filter(accessibleName => !!accessibleName).join(' ');
  }

  const kAriaSelectedRoles = ['gridcell', 'option', 'row', 'tab', 'rowheader', 'columnheader', 'treeitem'];
  function getAriaSelected(element) {
    if (elementSafeTagName(element) === 'OPTION')
      return element.selected;
    if (kAriaSelectedRoles.includes(ariaRole(element) || ''))
      return getAriaBoolean(element.getAttribute('aria-selected')) === true;
    return false;
  }

  const kAriaCheckedRoles = ['checkbox', 'menuitemcheckbox', 'option', 'radio', 'switch', 'menuitemradio', 'treeitem'];
  function getAriaChecked(element) {
    const result = getChecked(element, true);
    return result === 'error' ? false : result;
  }

  function getChecked(element, allowMixed) {
    const tagName = elementSafeTagName(element);
    if (allowMixed && tagName === 'INPUT' && element.indeterminate)
      return 'mixed';
    if (tagName === 'INPUT' && ['checkbox', 'radio'].includes(element.type))
      return element.checked;
    if (kAriaCheckedRoles.includes(ariaRole(element) || '')) {
      const checked = element.getAttribute('aria-checked');
      if (checked === 'true')
        return true;
      if (allowMixed && checked === 'mixed')
        return 'mixed';
      return false;
    }
    return 'error';
  }

  const kAriaReadonlyRoles = ['checkbox', 'combobox', 'grid', 'gridcell', 'listbox', 'radiogroup', 'slider', 'spinbutton', 'textbox', 'columnheader', 'rowheader', 'searchbox', 'switch', 'treegrid'];
  function getReadonly(element) {
    const tagName = elementSafeTagName(element);
    if (['INPUT', 'TEXTAREA', 'SELECT'].includes(tagName))
      return element.hasAttribute('readonly');
    if (kAriaReadonlyRoles.includes(ariaRole(element) || ''))
      return element.getAttribute('aria-readonly') === 'true';
    if (element.isContentEditable)
      return false;
    return 'error';
  }

  const kAriaPressedRoles = ['button'];
  function getAriaPressed(element) {
    if (kAriaPressedRoles.includes(ariaRole(element) || '')) {
      const pressed = element.getAttribute('aria-pressed');
      if (pressed === 'true')
        return true;
      if (pressed === 'mixed')
        return 'mixed';
    }
    return false;
  }

  const kAriaExpandedRoles = ['application', 'button', 'checkbox', 'combobox', 'gridcell', 'link', 'listbox', 'menuitem', 'row', 'rowheader', 'tab', 'treeitem', 'columnheader', 'menuitemcheckbox', 'menuitemradio', 'rowheader', 'switch'];
  function getAriaExpanded(element) {
    if (elementSafeTagName(element) === 'DETAILS')
      return element.open;
    if (kAriaExpandedRoles.includes(ariaRole(element) || '')) {
      const expanded = element.getAttribute('aria-expanded');
      if (expanded === null)
        return undefined;
      return expanded === 'true';
    }
    return undefined;
  }

  const kAriaLevelRoles = ['heading', 'listitem', 'row', 'treeitem'];
  function getAriaLevel(element) {
    const native = { 'H1': 1, 'H2': 2, 'H3': 3, 'H4': 4, 'H5': 5, 'H6': 6 }[elementSafeTagName(element)];
    if (native)
      return native;
    if (kAriaLevelRoles.includes(ariaRole(element) || '')) {
      const attr = element.getAttribute('aria-level');
      const value = attr === null ? Number.NaN : Number(attr);
      if (Number.isInteger(value) && value >= 1)
        return value;
    }
    return 0;
  }

  const kAriaDisabledRoles = ['application', 'button', 'composite', 'gridcell', 'group', 'input', 'link', 'menuitem', 'scrollbar', 'separator', 'tab', 'checkbox', 'columnheader', 'combobox', 'grid', 'listbox', 'menu', 'menubar', 'menuitemcheckbox', 'menuitemradio', 'option', 'radio', 'radiogroup', 'row', 'rowheader', 'searchbox', 'select', 'slider', 'spinbutton', 'switch', 'tablist', 'textbox', 'toolbar', 'tree', 'treegrid', 'treeitem'];
  function getAriaDisabled(element) {
    return isNativelyDisabled(element) || hasExplicitAriaDisabled(element);
  }

  function isNativelyDisabled(element) {
    const isNativeFormControl = ['BUTTON', 'INPUT', 'SELECT', 'TEXTAREA', 'OPTION', 'OPTGROUP'].includes(elementSafeTagName(element));
    return isNativeFormControl && (element.hasAttribute('disabled') || belongsToDisabledOptGroup(element) || belongsToDisabledFieldSet(element));
  }

  function belongsToDisabledOptGroup(element) {
    return elementSafeTagName(element) === 'OPTION' && !!element.closest('OPTGROUP[DISABLED]');
  }

  function belongsToDisabledFieldSet(element) {
    const fieldSetElement = element.closest('FIELDSET[DISABLED]');
    if (!fieldSetElement)
      return false;
    const legendElement = fieldSetElement.querySelector(':scope > LEGEND');
    return !legendElement || !legendElement.contains(element);
  }

  function hasExplicitAriaDisabled(element) {
    if (!kAriaDisabledRoles.includes(ariaRole(element) || ''))
      return false;
    return hasAriaDisabledInChain(element);
  }

  function hasAriaDisabledInChain(element) {
    let result = cache.ariaDisabled.get(element);
    if (result === undefined) {
      const attribute = (element.getAttribute('aria-disabled') || '').toLowerCase();
      if (attribute === 'true') {
        result = true;
      } else if (attribute === 'false') {
        result = false;
      } else {
        const parent = parentElementOrShadowHost(element);
        result = parent ? hasAriaDisabledInChain(parent) : false;
      }
      cache.ariaDisabled.set(element, result);
    }
    return result;
  }

  // ---------------------------------------------------------- role engine

  function roleOptions(attrs, role) {
    const options = { role };
    const validateSupportedRole = (attr, roles) => {
      if (!roles.includes(role))
        throw new Error('"' + attr + '" attribute is only supported for roles: ' + roles.slice().sort().map(r => '"' + r + '"').join(', '));
    };
    const validateSupportedValues = (attr, values) => {
      if (attr.op !== '<truthy>' && !values.includes(attr.value))
        throw new Error('"' + attr.name + '" must be one of ' + values.map(v => JSON.stringify(v)).join(', '));
    };
    const validateSupportedOp = (attr, ops) => {
      if (!ops.includes(attr.op))
        throw new Error('"' + attr.name + '" does not support "' + attr.op + '" matcher');
    };
    for (const attr of attrs) {
      switch (attr.name) {
        case 'checked':
          validateSupportedRole(attr.name, kAriaCheckedRoles);
          validateSupportedValues(attr, [true, false, 'mixed']);
          validateSupportedOp(attr, ['<truthy>', '=']);
          options.checked = attr.op === '<truthy>' ? true : attr.value;
          break;
        case 'pressed':
          validateSupportedRole(attr.name, kAriaPressedRoles);
          validateSupportedValues(attr, [true, false, 'mixed']);
          validateSupportedOp(attr, ['<truthy>', '=']);
          options.pressed = attr.op === '<truthy>' ? true : attr.value;
          break;
        case 'selected':
          validateSupportedRole(attr.name, kAriaSelectedRoles);
          validateSupportedValues(attr, [true, false]);
          validateSupportedOp(attr, ['<truthy>', '=']);
          options.selected = attr.op === '<truthy>' ? true : attr.value;
          break;
        case 'expanded':
          validateSupportedRole(attr.name, kAriaExpandedRoles);
          validateSupportedValues(attr, [true, false]);
          validateSupportedOp(attr, ['<truthy>', '=']);
          options.expanded = attr.op === '<truthy>' ? true : attr.value;
          break;
        case 'level':
          validateSupportedRole(attr.name, kAriaLevelRoles);
          if (typeof attr.value === 'string')
            attr.value = +attr.value;
          if (attr.op !== '=' || typeof attr.value !== 'number' || Number.isNaN(attr.value))
            throw new Error('"level" attribute must be compared to a number');
          options.level = attr.value;
          break;
        case 'disabled':
          validateSupportedValues(attr, [true, false]);
          validateSupportedOp(attr, ['<truthy>', '=']);
          options.disabled = attr.op === '<truthy>' ? true : attr.value;
          break;
        case 'name':
          if (attr.op === '<truthy>')
            throw new Error('"name" attribute must have a value');
          if (typeof attr.value !== 'string' && !(attr.value instanceof RegExp))
            throw new Error('"name" attribute must be a string or a regular expression');
          options.name = attr.value;
          options.nameOp = attr.op;
          options.nameExact = attr.caseSensitive;
          break;
        case 'description':
          if (attr.op === '<truthy>')
            throw new Error('"description" attribute must have a value');
          if (typeof attr.value !== 'string' && !(attr.value instanceof RegExp))
            throw new Error('"description" attribute must be a string or a regular expression');
          options.description = attr.value;
          options.descriptionOp = attr.op;
          options.descriptionExact = attr.caseSensitive;
          break;
        case 'include-hidden':
          validateSupportedValues(attr, [true, false]);
          validateSupportedOp(attr, ['<truthy>', '=']);
          options.includeHidden = attr.op === '<truthy>' ? true : attr.value;
          break;
        default:
          throw new Error('Unknown attribute "' + attr.name + '", must be one of "checked", "description", "disabled", "expanded", "include-hidden", "level", "name", "pressed", "selected".');
      }
    }
    return options;
  }

  function roleQuery(scope, options, internal) {
    const result = [];
    const match = element => {
      if (ariaRole(element) !== options.role)
        return;
      if (options.selected !== undefined && getAriaSelected(element) !== options.selected)
        return;
      if (options.checked !== undefined && getAriaChecked(element) !== options.checked)
        return;
      if (options.pressed !== undefined && getAriaPressed(element) !== options.pressed)
        return;
      if (options.expanded !== undefined && getAriaExpanded(element) !== options.expanded)
        return;
      if (options.level !== undefined && getAriaLevel(element) !== options.level)
        return;
      if (options.disabled !== undefined && getAriaDisabled(element) !== options.disabled)
        return;
      if (!options.includeHidden && ariaHidden(element))
        return;
      if (options.name !== undefined) {
        const computedName = normalizeWhiteSpace(accessibleName(element, !!options.includeHidden));
        if (typeof options.name === 'string')
          options.name = normalizeWhiteSpace(options.name);
        if (internal && !options.nameExact && options.nameOp === '=')
          options.nameOp = '*=';
        if (!matchesAttributePart(computedName, { name: '', jsonPath: [], op: options.nameOp || '=', value: options.name, caseSensitive: !!options.nameExact }))
          return;
      }
      if (options.description !== undefined) {
        const accessibleDescription = normalizeWhiteSpace(getElementAccessibleDescription(element, !!options.includeHidden));
        if (typeof options.description === 'string')
          options.description = normalizeWhiteSpace(options.description);
        if (internal && !options.descriptionExact && options.descriptionOp === '=')
          options.descriptionOp = '*=';
        if (!matchesAttributePart(accessibleDescription, { name: '', jsonPath: [], op: options.descriptionOp || '=', value: options.description, caseSensitive: !!options.descriptionExact }))
          return;
      }
      result.push(element);
    };
    const query = root => {
      const shadows = [];
      if (root.shadowRoot)
        shadows.push(root.shadowRoot);
      for (const element of root.querySelectorAll('*')) {
        match(element);
        if (element.shadowRoot)
          shadows.push(element.shadowRoot);
      }
      shadows.forEach(query);
    };
    query(scope);
    return result;
  }

  function roleEngine(internal) {
    return {
      queryAll: (scope, selector) => {
        const parsed = parseAttributeSelector(selector, true);
        const role = parsed.name.toLowerCase();
        if (!role)
          throw new Error('Role must not be empty');
        const options = roleOptions(parsed.attributes, role);
        return roleQuery(scope, options, internal);
      },
    };
  }

  // ---------------------------------------------------------- engines

  function queryCSS(root, css, pierceShadow) {
    const result = [...root.querySelectorAll(css)];
    if (!pierceShadow)
      return result;
    const shadows = [];
    if (root.shadowRoot)
      shadows.push(root.shadowRoot);
    for (const element of root.querySelectorAll('*')) {
      if (element.shadowRoot)
        shadows.push(element.shadowRoot);
    }
    for (const shadow of shadows)
      result.push(...queryCSS(shadow, css, true));
    return result;
  }

  const XPathEngine = {
    queryAll(root, selector) {
      if (selector.startsWith('/') && root.nodeType !== DOCUMENT_NODE)
        selector = '.' + selector;
      const result = [];
      const document = root.ownerDocument || root;
      if (!document)
        return result;
      const it = document.evaluate(selector, root, null, XPathResult.ORDERED_NODE_ITERATOR_TYPE);
      for (let node = it.iterateNext(); node; node = it.iterateNext()) {
        if (node.nodeType === ELEMENT_NODE)
          result.push(node);
      }
      return result;
    },
  };

  function textEngine(shadow, internal) {
    const queryAll = (root, selector) => {
      const { matcher, kind } = textMatcher(selector, internal);
      const result = [];
      let lastDidNotMatchSelf = null;
      const appendElement = element => {
        if (kind === 'lax' && lastDidNotMatchSelf && lastDidNotMatchSelf.contains(element))
          return false;
        const matches = textMatch(element, matcher);
        if (matches === 'none')
          lastDidNotMatchSelf = element;
        if (matches === 'self' || (matches === 'selfAndChildren' && kind === 'strict' && !internal))
          result.push(element);
        return true;
      };
      if (root.nodeType === ELEMENT_NODE)
        appendElement(root);
      const elements = queryCSS(root, '*', shadow);
      for (const element of elements)
        appendElement(element);
      return result;
    };
    return { queryAll };
  }

  function attributeEngine(attribute, shadow) {
    return {
      queryAll: (root, selector) => queryCSS(root, '[' + attribute + '=' + JSON.stringify(selector) + ']', shadow),
    };
  }

  function namedAttributeEngine() {
    return {
      queryAll: (root, selector) => {
        const parsed = parseAttributeSelector(selector, true);
        if (parsed.name || parsed.attributes.length !== 1)
          throw new Error('Malformed attribute selector: ' + selector);
        const { name } = parsed.attributes[0];
        const matcher = createAttributeMatcher(parsed.attributes[0]);
        return queryCSS(root, '[' + name + ']', true).filter(e => matcher(e.getAttribute(name)));
      },
    };
  }

  function testIdEngine() {
    return {
      queryAll: (root, selector) => {
        const parsed = parseAttributeSelector(selector, true);
        if (parsed.name || parsed.attributes.length !== 1)
          throw new Error('Malformed test id selector: ' + selector);
        const names = parsed.attributes[0].name.split('/').map(n => n.trim()).filter(Boolean);
        const matcher = createAttributeMatcher(parsed.attributes[0]);
        const cssQuery = names.map(n => '[' + n + ']').join(',');
        return queryCSS(root, cssQuery, true).filter(e => names.some(n => {
          const actual = e.getAttribute(n);
          return actual !== null && matcher(actual);
        }));
      },
    };
  }

  function labelEngine() {
    return {
      queryAll: (root, selector) => {
        const { matcher } = textMatcher(selector, true);
        return queryCSS(root, '*', true).filter(element => getElementLabels(element).some(label => matcher(label)));
      },
    };
  }

  function hasTextEngine(negate) {
    return {
      queryAll: (root, selector) => {
        if (root.nodeType !== ELEMENT_NODE)
          return [];
        const text = elementText(root);
        const { matcher } = textMatcher(selector, true);
        const matches = matcher(text);
        return (negate ? !matches : matches) ? [root] : [];
      },
    };
  }

  function visibleEngine() {
    return {
      queryAll: (root, body) => {
        if (root.nodeType !== ELEMENT_NODE)
          return [];
        const visible = body === 'true';
        return isElementVisible(root) === visible ? [root] : [];
      },
    };
  }

  function controlEngine() {
    return {
      queryAll: (root, body) => {
        if (body === 'enter-frame' || body === 'any-frame' || body === 'return-empty')
          return [];
        throw new Error('Internal error, unknown internal:control selector ' + body);
      },
    };
  }

  const engines = new Map();
  engines.set('xpath', XPathEngine);
  engines.set('xpath:light', XPathEngine);
  engines.set('role', roleEngine(false));
  engines.set('text', textEngine(true, false));
  engines.set('text:light', textEngine(false, false));
  engines.set('id', attributeEngine('id', true));
  engines.set('id:light', attributeEngine('id', false));
  engines.set('data-testid', attributeEngine('data-testid', true));
  engines.set('data-testid:light', attributeEngine('data-testid', false));
  engines.set('data-test-id', attributeEngine('data-test-id', true));
  engines.set('data-test-id:light', attributeEngine('data-test-id', false));
  engines.set('data-test', attributeEngine('data-test', true));
  engines.set('data-test:light', attributeEngine('data-test', false));
  engines.set('css', { queryAll: (root, body) => queryCSS(root, body, true) });
  engines.set('nth', { queryAll: () => [] });
  engines.set('visible', visibleEngine());
  engines.set('internal:control', controlEngine());
  engines.set('internal:has', { queryAll: (root, body) => root.nodeType === ELEMENT_NODE && querySelectorAll(body.parsed, root).length ? [root] : [] });
  engines.set('internal:has-not', { queryAll: (root, body) => root.nodeType === ELEMENT_NODE && !querySelectorAll(body.parsed, root).length ? [root] : [] });
  engines.set('internal:and', { queryAll: () => [] });
  engines.set('internal:or', { queryAll: () => [] });
  engines.set('internal:chain', { queryAll: (root, body) => querySelectorAll(body.parsed, root) });
  engines.set('internal:label', labelEngine());
  engines.set('internal:text', textEngine(true, true));
  engines.set('internal:has-text', hasTextEngine(false));
  engines.set('internal:has-not-text', hasTextEngine(true));
  engines.set('internal:attr', namedAttributeEngine());
  engines.set('internal:testid', testIdEngine());
  engines.set('internal:role', roleEngine(true));
  engines.set('internal:describe', { queryAll: root => root.nodeType === ELEMENT_NODE ? [root] : [] });

  function queryNth(elements, part) {
    const list = [...elements];
    let nth = +part.body;
    if (nth === -1)
      nth = list.length - 1;
    return new Set(list.slice(nth, nth + 1));
  }

  function querySelectorAll(selector, root) {
    if (selector.capture !== undefined) {
      if (selector.parts.some(part => part.name === 'nth'))
        throw new Error("Can't query n-th element in a request with the capture.");
      const withHas = { parts: selector.parts.slice(0, selector.capture + 1) };
      if (selector.capture < selector.parts.length - 1) {
        const parsed = { parts: selector.parts.slice(selector.capture + 1) };
        withHas.parts.push({ name: 'internal:has', body: { parsed }, source: '' });
      }
      return querySelectorAll(withHas, root);
    }
    if (!root['querySelectorAll'])
      throw new Error('Node is not queryable.');
    if (root.nodeType === FRAGMENT_NODE && selector.parts.length === 1 && selector.parts[0].name === 'css' && selector.parts[0].source === ':scope')
      return [root];

    let roots = new Set([root]);
    for (const part of selector.parts) {
      if (part.name === 'nth') {
        roots = queryNth(roots, part);
      } else if (part.name === 'internal:and') {
        const andElements = querySelectorAll(part.body.parsed, root);
        roots = new Set(andElements.filter(e => roots.has(e)));
      } else if (part.name === 'internal:or') {
        const orElements = querySelectorAll(part.body.parsed, root);
        roots = new Set(sortInDOMOrder(new Set([...roots, ...orElements])));
      } else {
        const next = new Set();
        for (const r of roots) {
          const engine = engines.get(part.name);
          if (!engine)
            throw new Error('Unknown engine "' + part.name + '" while parsing selector');
          for (const one of engine.queryAll(r, part.body))
            next.add(one);
        }
        roots = next;
      }
    }
    return [...roots];
  }

  function describeNode(node) {
    if (node.nodeType === TEXT_NODE)
      return '#text=' + (node.nodeValue || '').substring(0, 50);
    if (node.nodeType !== ELEMENT_NODE)
      return node.nodeName.toLowerCase();
    const element = node;
    const attrs = [];
    for (let i = 0; i < element.attributes.length; i++) {
      const { name, value } = element.attributes[i];
      if (name === 'style')
        continue;
      if (!value && (name === 'class' || name === 'id'))
        continue;
      attrs.push(value ? name + '="' + value + '"' : name);
    }
    const attrText = attrs.length ? ' ' + attrs.join(' ') : '';
    const tag = element.nodeName.toLowerCase();
    if (!element.childNodes.length && !element.shadowRoot)
      return '<' + tag + attrText + '/>';
    const text = (element.textContent || '').replace(/\s+/g, ' ').trim();
    const preview = text.length > 50 ? text.substring(0, 49) + '…' : text;
    return '<' + tag + attrText + '>' + preview + '</' + tag + '>';
  }

  function ambiguousMatch(selector, matches) {
    const infos = matches.slice(0, 10).map(m => ({ preview: describeNode(m) }));
    const lines = infos.map((info, i) => '\n    ' + (i + 1) + ') ' + info.preview);
    if (infos.length < matches.length)
      lines.push('\n    ...');
    return new Error('strict mode violation: ' + selector + ' resolved to ' + matches.length + ' elements:' + lines.join('') + '\n');
  }

  function querySelector(selectorString, root, strict) {
    const parsed = parseSelector(selectorString);
    const result = querySelectorAll(parsed, root);
    if (strict && result.length > 1)
      throw ambiguousMatch(selectorString, result);
    return result[0];
  }

  // -------------------------------------------------------- element states

  function resolveTarget(node, behavior) {
    let element = node.nodeType === ELEMENT_NODE ? node : node.parentElement;
    if (!element)
      return null;
    if (behavior === 'none')
      return element;
    if (!element.matches('input, textarea, select') && !element.isContentEditable) {
      if (behavior === 'button-link')
        element = element.closest('button, [role=button], a, [role=link]') || element;
      else
        element = element.closest('button, [role=button], [role=checkbox], [role=radio]') || element;
    }
    if (behavior === 'follow-label') {
      if (!element.matches('a, input, textarea, button, select, [role=link], [role=button], [role=checkbox], [role=radio]') && !element.isContentEditable) {
        const enclosingLabel = element.closest('label');
        if (enclosingLabel && enclosingLabel.control)
          element = enclosingLabel.control;
      }
    }
    return element;
  }

  function elementState(node, state) {
    const element = resolveTarget(node, ['visible', 'hidden'].includes(state) ? 'none' : 'follow-label');
    if (!element || !element.isConnected) {
      if (state === 'hidden')
        return { matches: true, received: 'hidden' };
      return { matches: false, received: 'error:notconnected' };
    }
    if (state === 'visible' || state === 'hidden') {
      const visible = isElementVisible(element);
      return { matches: state === 'visible' ? visible : !visible, received: visible ? 'visible' : 'hidden' };
    }
    if (state === 'disabled' || state === 'enabled') {
      const disabled = getAriaDisabled(element);
      return { matches: state === 'disabled' ? disabled : !disabled, received: disabled ? 'disabled' : 'enabled' };
    }
    if (state === 'editable') {
      const disabled = getAriaDisabled(element);
      const readonly = getReadonly(element);
      if (readonly === 'error')
        throw new Error('Element is not an <input>, <textarea>, <select> or [contenteditable] and does not have a role allowing [aria-readonly]');
      return { matches: !disabled && !readonly, received: disabled ? 'disabled' : readonly ? 'readOnly' : 'editable' };
    }
    if (state === 'checked' || state === 'unchecked') {
      const need = state === 'checked';
      const checked = getChecked(element, false);
      if (checked === 'error')
        throw new Error('Not a checkbox or radio button');
      return { matches: need === checked, received: checked ? 'checked' : 'unchecked' };
    }
    if (state === 'indeterminate') {
      const checked = getChecked(element, true);
      if (checked === 'error')
        throw new Error('Not a checkbox or radio button');
      return { matches: checked === 'mixed', received: checked === true ? 'checked' : checked === false ? 'unchecked' : 'mixed' };
    }
    throw new Error('Unexpected element state "' + state + '"');
  }

  function settle(node) {
    let lastRect;
    let stableRafCounter = 0;
    let lastTime = 0;
    const stableRafCount = 2;
    // Hidden documents (a background tab after window.open) never run
    // requestAnimationFrame, so fall back to a timer there.
    const schedule = callback => {
      if (document.visibilityState === 'visible')
        requestAnimationFrame(callback);
      else
        setTimeout(callback, 16);
    };
    return new Promise((fulfill, reject) => {
      const raf = () => {
        try {
          const element = resolveTarget(node, 'no-follow-label');
          if (!element) {
            fulfill('error:notconnected');
            return;
          }
          const time = performance.now();
          if (stableRafCount > 1 && time - lastTime < 15) {
            schedule(raf);
            return;
          }
          lastTime = time;
          const clientRect = element.getBoundingClientRect();
          const rect = { x: clientRect.top, y: clientRect.left, width: clientRect.width, height: clientRect.height };
          if (lastRect) {
            const samePosition = rect.x === lastRect.x && rect.y === lastRect.y && rect.width === lastRect.width && rect.height === lastRect.height;
            if (!samePosition) {
              fulfill(false);
              return;
            }
            if (++stableRafCounter >= stableRafCount) {
              fulfill(true);
              return;
            }
          }
          lastRect = rect;
          schedule(raf);
        } catch (e) {
          reject(e);
        }
      };
      schedule(raf);
    });
  }

  async function checkStates(node, states) {
    if (states.includes('stable')) {
      const stableResult = await settle(node);
      if (stableResult === false)
        return { missingState: 'stable' };
      if (stableResult === 'error:notconnected')
        return 'error:notconnected';
    }
    for (const state of states) {
      if (state !== 'stable') {
        const result = elementState(node, state);
        if (result.received === 'error:notconnected')
          return 'error:notconnected';
        if (!result.matches)
          return { missingState: state };
      }
    }
    return undefined;
  }

  function hitCheck(hitPoint, targetElement) {
    const roots = [];
    let parentElement = targetElement;
    while (parentElement) {
      const root = enclosingShadowRootOrDocument(parentElement);
      if (!root)
        break;
      roots.push(root);
      if (root.nodeType === DOCUMENT_NODE)
        break;
      parentElement = root.host;
    }
    let hitElement;
    for (let index = roots.length - 1; index >= 0; index--) {
      const root = roots[index];
      const elements = root.elementsFromPoint(hitPoint.x, hitPoint.y);
      const singleElement = root.elementFromPoint(hitPoint.x, hitPoint.y);
      if (singleElement && elements[0] && parentElementOrShadowHost(singleElement) === elements[0]) {
        const style = getElementComputedStyle(singleElement);
        if (style && style.display === 'contents')
          elements.unshift(singleElement);
      }
      if (elements[0] && elements[0].shadowRoot === root && elements[1] === singleElement)
        elements.shift();
      const innerElement = elements[0];
      if (!innerElement)
        break;
      hitElement = innerElement;
      if (index && innerElement !== roots[index - 1].host)
        break;
    }
    const hitParents = [];
    while (hitElement && hitElement !== targetElement) {
      hitParents.push(hitElement);
      hitElement = hitElement.assignedSlot || parentElementOrShadowHost(hitElement);
    }
    if (hitElement === targetElement)
      return 'done';
    const hitTargetDescription = describeNode(hitParents[0] || targetElement.ownerDocument.documentElement);
    let rootHitTargetDescription;
    let element = targetElement;
    while (element) {
      const index = hitParents.indexOf(element);
      if (index !== -1) {
        if (index > 1)
          rootHitTargetDescription = describeNode(hitParents[index - 1]);
        break;
      }
      element = parentElementOrShadowHost(element);
    }
    if (rootHitTargetDescription)
      return { hitTargetDescription: hitTargetDescription + ' from ' + rootHitTargetDescription + ' subtree' };
    return { hitTargetDescription };
  }

  // -------------------------------------------------------------- actions

  function pickOptions(node, optionsToSelect) {
    const element = resolveTarget(node, 'follow-label');
    if (!element)
      return 'error:notconnected';
    if (element.nodeName.toLowerCase() !== 'select')
      throw new Error('Element is not a <select> element');
    const select = element;
    const options = [...select.options];
    const selectedOptions = [];
    let remainingOptionsToSelect = optionsToSelect.slice();
    for (let index = 0; index < options.length; index++) {
      const option = options[index];
      const normalizedOptionLabel = normalizeWhiteSpace(option.label);
      const filter = optionToSelect => {
        if (optionToSelect instanceof Node)
          return option === optionToSelect;
        const matchesLabel = label => label === option.label || normalizeWhiteSpace(label) === normalizedOptionLabel;
        let matches = true;
        if (optionToSelect.valueOrLabel !== undefined)
          matches = matches && (optionToSelect.valueOrLabel === option.value || matchesLabel(optionToSelect.valueOrLabel));
        if (optionToSelect.value !== undefined)
          matches = matches && optionToSelect.value === option.value;
        if (optionToSelect.label !== undefined)
          matches = matches && matchesLabel(optionToSelect.label);
        if (optionToSelect.index !== undefined)
          matches = matches && optionToSelect.index === index;
        return matches;
      };
      if (!remainingOptionsToSelect.some(filter))
        continue;
      if (!elementState(option, 'enabled').matches)
        return 'error:optionnotenabled';
      selectedOptions.push(option);
      if (select.multiple) {
        remainingOptionsToSelect = remainingOptionsToSelect.filter(o => !filter(o));
      } else {
        remainingOptionsToSelect = [];
        break;
      }
    }
    if (remainingOptionsToSelect.length)
      return 'error:optionsnotfound';
    select.value = undefined;
    selectedOptions.forEach(option => option.selected = true);
    select.dispatchEvent(new Event('input', { bubbles: true, composed: true }));
    select.dispatchEvent(new Event('change', { bubbles: true }));
    return selectedOptions.map(option => option.value);
  }

  function fillValue(node, value) {
    const element = resolveTarget(node, 'follow-label');
    if (!element)
      return 'error:notconnected';
    if (element.nodeName.toLowerCase() === 'input') {
      const input = element;
      const type = input.type.toLowerCase();
      const kInputTypesToSetValue = new Set(['color', 'date', 'time', 'datetime-local', 'month', 'range', 'week']);
      const kInputTypesToTypeInto = new Set(['', 'email', 'number', 'password', 'search', 'tel', 'text', 'url']);
      if (!kInputTypesToTypeInto.has(type) && !kInputTypesToSetValue.has(type))
        throw new Error('Input of type "' + type + '" cannot be filled');
      if (type === 'number') {
        value = value.trim();
        if (isNaN(Number(value)))
          throw new Error('Cannot type text into input[type=number]');
      }
      if (type === 'color')
        value = value.toLowerCase();
      if (kInputTypesToSetValue.has(type)) {
        value = value.trim();
        input.focus();
        input.value = value;
        if (input.value !== value)
          throw new Error('Malformed value');
        element.dispatchEvent(new Event('input', { bubbles: true, composed: true }));
        element.dispatchEvent(new Event('change', { bubbles: true }));
        return 'done';
      }
    } else if (element.nodeName.toLowerCase() === 'textarea') {
      // Nothing to check here.
    } else if (!element.isContentEditable) {
      throw new Error('Element is not an <input>, <textarea> or [contenteditable] element');
    }
    selectContents(element);
    return 'needsinput';
  }

  function selectContents(node) {
    const element = resolveTarget(node, 'follow-label');
    if (!element)
      return 'error:notconnected';
    if (element.nodeName.toLowerCase() === 'input') {
      element.select();
      element.focus();
      return 'done';
    }
    if (element.nodeName.toLowerCase() === 'textarea') {
      element.selectionStart = 0;
      element.selectionEnd = element.value.length;
      element.focus();
      return 'done';
    }
    element.focus();
    const range = element.ownerDocument.createRange();
    range.selectNodeContents(element);
    const selection = element.ownerDocument.defaultView.getSelection();
    if (selection) {
      selection.removeAllRanges();
      selection.addRange(range);
    }
    return 'done';
  }

  function focusElement(node, resetSelectionIfNotFocused) {
    if (!node.isConnected)
      return 'error:notconnected';
    if (node.nodeType !== ELEMENT_NODE)
      throw new Error('Node is not an element');
    const activeElement = node.getRootNode().activeElement;
    const wasFocused = activeElement === node && !!node.ownerDocument && node.ownerDocument.hasFocus();
    if (node.isContentEditable && !wasFocused && activeElement && activeElement.blur)
      activeElement.blur();
    node.focus();
    if (resetSelectionIfNotFocused && !wasFocused && node.nodeName.toLowerCase() === 'input') {
      try {
        node.setSelectionRange(0, 0);
      } catch (e) {
        // Some inputs do not allow selection.
      }
    }
    return 'done';
  }

  function inputValue(node) {
    const element = resolveTarget(node, 'follow-label');
    if (!element || (element.nodeName !== 'INPUT' && element.nodeName !== 'TEXTAREA' && element.nodeName !== 'SELECT'))
      throw new Error('Node is not an <input>, <textarea> or <select> element');
    return element.value;
  }

  function dispatchEvent(node, type, eventInit) {
    let event;
    eventInit = Object.assign({ bubbles: true, cancelable: true, composed: true }, eventInit || {});
    const kEventTypes = {
      'auxclick': 'MouseEvent', 'click': 'MouseEvent', 'dblclick': 'MouseEvent', 'mousedown': 'MouseEvent', 'mouseup': 'MouseEvent',
      'mousemove': 'MouseEvent', 'mouseover': 'MouseEvent', 'mouseout': 'MouseEvent', 'mouseenter': 'MouseEvent', 'mouseleave': 'MouseEvent',
      'keydown': 'KeyboardEvent', 'keyup': 'KeyboardEvent', 'keypress': 'KeyboardEvent',
      'focus': 'FocusEvent', 'blur': 'FocusEvent', 'focusin': 'FocusEvent', 'focusout': 'FocusEvent',
      'input': 'InputEvent', 'beforeinput': 'InputEvent',
      'drag': 'DragEvent', 'dragstart': 'DragEvent', 'dragend': 'DragEvent', 'dragover': 'DragEvent', 'dragenter': 'DragEvent', 'dragleave': 'DragEvent', 'drop': 'DragEvent',
      'touchstart': 'TouchEvent', 'touchend': 'TouchEvent', 'touchmove': 'TouchEvent', 'touchcancel': 'TouchEvent',
      'pointerdown': 'PointerEvent', 'pointerup': 'PointerEvent', 'pointermove': 'PointerEvent', 'pointerover': 'PointerEvent', 'pointerout': 'PointerEvent', 'pointerenter': 'PointerEvent', 'pointerleave': 'PointerEvent', 'pointercancel': 'PointerEvent',
      'wheel': 'WheelEvent', 'deviceorientation': 'DeviceOrientationEvent', 'devicemotion': 'DeviceMotionEvent',
    };
    const ctor = window[kEventTypes[type] || 'Event'];
    try {
      event = new ctor(type, eventInit);
    } catch (e) {
      event = new Event(type, eventInit);
    }
    node.dispatchEvent(event);
  }

  // ------------------------------------------------------------ combined actions

  function elementRect(element) {
    const r = element.getBoundingClientRect();
    return { x: r.x, y: r.y, width: r.width, height: r.height };
  }

  function fullyInViewport(rect) {
    return rect.x >= 0 && rect.y >= 0 && rect.x + rect.width <= window.innerWidth && rect.y + rect.height <= window.innerHeight;
  }

  function insideSpan(low, high) {
    return low + (high - low) * (0.3 + Math.random() * 0.4);
  }

  async function prepareForAction(node, options) {
    const element = resolveTarget(node, 'none');
    if (!element || !element.isConnected)
      return { status: 'notconnected' };
    if (!options.force) {
      const missing = await checkStates(node, options.states);
      if (missing === 'error:notconnected')
        return { status: 'notconnected' };
      if (missing)
        return { status: 'missing', state: missing.missingState };
    }
    let rect = elementRect(element);
    if (options.scroll !== 'none' && !fullyInViewport(rect)) {
      element.scrollIntoView({ block: 'center', inline: 'center', behavior: 'instant' });
      rect = elementRect(element);
    }
    let offsetX;
    let offsetY;
    if (options.position) {
      offsetX = options.position.x;
      offsetY = options.position.y;
    } else {
      const left = Math.max(rect.x, 0);
      const top = Math.max(rect.y, 0);
      const right = Math.min(rect.x + rect.width, window.innerWidth);
      const bottom = Math.min(rect.y + rect.height, window.innerHeight);
      if (right <= left || bottom <= top)
        return { status: 'notinviewport' };
      offsetX = insideSpan(left, right) - rect.x;
      offsetY = insideSpan(top, bottom) - rect.y;
    }
    const point = { x: rect.x + offsetX, y: rect.y + offsetY };
    if (!options.force) {
      const hit = hitCheck(point, element);
      if (hit !== 'done')
        return { status: 'intercepted', description: hit.hitTargetDescription };
    }
    return { status: 'done', x: point.x, y: point.y, offsetX, offsetY };
  }

  async function fillChecked(node, value, force) {
    if (!force) {
      const missing = await checkStates(node, ['visible', 'enabled', 'editable']);
      if (missing === 'error:notconnected')
        return 'error:notconnected';
      if (missing)
        return { missingState: missing.missingState };
    }
    return fillValue(node, value);
  }

  async function selectChecked(node, optionsToSelect, force) {
    if (!force) {
      const missing = await checkStates(node, ['visible', 'enabled']);
      if (missing === 'error:notconnected')
        return 'error:notconnected';
      if (missing)
        return { missingState: missing.missingState };
    }
    return pickOptions(node, optionsToSelect);
  }

  async function scrollWhenNeeded(node) {
    const missing = await checkStates(node, ['stable']);
    if (missing === 'error:notconnected')
      return 'error:notconnected';
    if (missing)
      return { missingState: missing.missingState };
    const element = resolveTarget(node, 'none');
    if (!fullyInViewport(elementRect(element)))
      element.scrollIntoView({ block: 'center', inline: 'center', behavior: 'instant' });
    return 'done';
  }

  function documentRect(node) {
    const element = resolveTarget(node, 'none');
    const r = element.getBoundingClientRect();
    return { x: r.x + window.scrollX, y: r.y + window.scrollY, width: r.width, height: r.height };
  }

  function clearCaches() {
    for (const map of Object.values(cache))
      map.clear();
  }

  function fresh(fn) {
    return function(...args) {
      clearCaches();
      return fn.apply(this, args);
    };
  }

  const api = {
    parseSelector,
    querySelector,
    querySelectorAll: (selectorString, root) => querySelectorAll(parseSelector(selectorString), root),
    elementState,
    checkStates,
    hitCheck,
    prepareForAction,
    fillChecked,
    selectChecked,
    scrollWhenNeeded,
    documentRect,
    isElementVisible,
    ariaRole,
    accessibleName,
    fill: fillValue,
    pickOptions,
    selectContents,
    focusElement,
    inputValue,
    dispatchEvent,
    describeNode,
    elementText: element => elementText(element).full,
    resolveTarget,
  };
  for (const key of Object.keys(api))
    api[key] = fresh(api[key]);
  return api;
})()
