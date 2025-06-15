"""
Shadow DOM Example - Secure Shadow DOM Automation with pydoll

This example demonstrates how to securely interact with Shadow DOM elements
using pydoll's enhanced Shadow DOM support. It covers best practices for
security, error handling, and real-world usage patterns.

Security Features Demonstrated:
- Safe shadow root access with validation
- Selector sanitization and injection prevention
- Proper error handling for security edge cases
- Respecting shadow DOM boundaries and encapsulation
"""

import asyncio
import logging

from pydoll.browser.chromium import Chrome
from pydoll.exceptions import (
    ElementNotFound,
    InvalidShadowRoot,
    NoShadowRootAttached,
    ShadowRootAccessDenied,
)

# Configure logging for security and debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_basic_shadow_dom_access():
    """
    Basic Shadow DOM access demonstration.

    Shows the fundamental pattern for securely accessing shadow DOM content.
    """
    print('Basic Shadow DOM Access Demo')
    print('=' * 40)

    async with Chrome() as browser:
        tab = await browser.start()

        # Navigate to a page with Shadow DOM (example: a page with custom elements)
        await tab.go_to(
            'data:text/html,<html><body>'
            '<my-component id="host"></my-component>'
            '<script>'
            'class MyComponent extends HTMLElement {'
            '  connectedCallback() {'
            '    const shadow = this.attachShadow({mode: "open"});'
            '    shadow.innerHTML = "<button class=\\"shadow-btn\\">Shadow Button</button>";'
            '  }'
            '}'
            'customElements.define("my-component", MyComponent);'
            '</script></body></html>'
        )

        try:
            # Find the shadow host element
            host_element = await tab.find(id='host')
            logger.info('Found shadow host element')

            # Securely access the shadow root
            shadow_root = await host_element.get_shadow_root()
            logger.info(f'Accessed shadow root (mode: {shadow_root.mode})')

            # Find elements within the shadow DOM
            shadow_button = await shadow_root.find_element_in_shadow('button.shadow-btn')
            logger.info('Found button within shadow DOM')

            # Interact with shadow DOM elements safely
            await shadow_button.click()
            logger.info('Successfully clicked shadow DOM button')

        except NoShadowRootAttached:
            logger.error('Element does not have a shadow root attached')
        except InvalidShadowRoot as e:
            logger.error(f'Invalid shadow root: {e}')
        except ElementNotFound as e:
            logger.error(f'Element not found in shadow DOM: {e}')


async def demo_closed_shadow_dom():
    """
    Demonstration of closed shadow DOM handling.

    Shows how pydoll handles closed shadow roots and security boundaries.
    """
    print('\nClosed Shadow DOM Demo')
    print('=' * 25)

    async with Chrome() as browser:
        tab = await browser.start()

        # Create page with closed shadow DOM
        await tab.go_to(
            'data:text/html,<html><body>'
            '<closed-component id="closed-host"></closed-component>'
            '<script>'
            'class ClosedComponent extends HTMLElement {'
            '  connectedCallback() {'
            '    const shadow = this.attachShadow({mode: "closed"});'
            '    shadow.innerHTML = "<div class=\\"secret\\">Secret Content</div>";'
            '  }'
            '}'
            'customElements.define("closed-component", ClosedComponent);'
            '</script></body></html>'
        )

        try:
            host_element = await tab.find(id='closed-host')
            shadow_root = await host_element.get_shadow_root()
            logger.info(f'Accessed closed shadow root (mode: {shadow_root.mode})')

            # Even for closed shadow roots, if we have access, we can find elements
            secret_div = await shadow_root.find_element_in_shadow('.secret')
            content = await secret_div.text
            logger.info(f'Accessed closed shadow content: {content}')

        except ShadowRootAccessDenied:
            logger.warning('Access to closed shadow root was denied (expected)')
        except Exception as e:
            logger.error(f'Unexpected error: {e}')


async def demo_nested_shadow_dom():
    """
    Demonstration of nested shadow DOM access.

    Shows how to navigate through multiple levels of shadow DOM safely.
    """
    print('\nNested Shadow DOM Demo')
    print('=' * 23)

    async with Chrome() as browser:
        tab = await browser.start()

        # Create page with nested shadow DOM
        await tab.go_to(
            'data:text/html,<html><body>'
            '<outer-component id="outer"></outer-component>'
            '<script>'
            'class OuterComponent extends HTMLElement {'
            '  connectedCallback() {'
            '    const shadow = this.attachShadow({mode: "open"});'
            '    shadow.innerHTML = "<inner-component class=\\"inner\\"></inner-component>";'
            '  }'
            '}'
            'class InnerComponent extends HTMLElement {'
            '  connectedCallback() {'
            '    const shadow = this.attachShadow({mode: "open"});'
            '    shadow.innerHTML = "<button class=\\"deep-btn\\">Deep Button</button>";'
            '  }'
            '}'
            'customElements.define("outer-component", OuterComponent);'
            'customElements.define("inner-component", InnerComponent);'
            '</script></body></html>'
        )

        try:
            # Access outer shadow DOM
            outer_host = await tab.find(id='outer')
            outer_shadow = await outer_host.get_shadow_root()
            logger.info('Accessed outer shadow root')

            # Find inner component within outer shadow
            inner_component = await outer_shadow.find_element_in_shadow('.inner')
            logger.info('Found inner component')

            # Access inner shadow DOM
            inner_shadow = await inner_component.get_shadow_root()
            logger.info('Accessed inner shadow root')

            # Find deeply nested button
            deep_button = await inner_shadow.find_element_in_shadow('.deep-btn')
            await deep_button.click()
            logger.info('Successfully clicked deeply nested shadow button')

        except Exception as e:
            logger.error(f'Error in nested shadow access: {e}')


async def demo_security_features():
    """
    Demonstration of security features and injection prevention.

    Shows how pydoll prevents various types of security vulnerabilities.
    """
    print('\nSecurity Features Demo')
    print('=' * 26)

    async with Chrome() as browser:
        tab = await browser.start()

        # Create a simple shadow DOM for testing
        await tab.go_to(
            'data:text/html,<html><body>'
            '<test-component id="test"></test-component>'
            '<script>'
            'class TestComponent extends HTMLElement {'
            '  connectedCallback() {'
            '    const shadow = this.attachShadow({mode: "open"});'
            '    shadow.innerHTML = "<div class=\\"content\\">Safe Content</div>";'
            '  }'
            '}'
            'customElements.define("test-component", TestComponent);'
            '</script></body></html>'
        )

        host_element = await tab.find(id='test')
        shadow_root = await host_element.get_shadow_root()

        # Test 1: Valid selector (should work)
        try:
            await shadow_root.find_element_in_shadow('.content')
            logger.info('Valid selector works correctly')
        except Exception as e:
            logger.error(f'Valid selector failed: {e}')

        # Test 2: Dangerous shadow-piercing selectors (should be blocked)
        dangerous_selectors = [
            'div ::shadow button',  # Deprecated shadow piercing
            'div /deep/ button',  # Deprecated deep combinator
            'div >>> button',  # Deep combinator
        ]

        for selector in dangerous_selectors:
            try:
                await shadow_root.find_element_in_shadow(selector)
                logger.error(f'Dangerous selector was allowed: {selector}')
            except ValueError:
                logger.info(f'Blocked dangerous selector: {selector}')


async def demo_error_handling():
    """
    Demonstration of comprehensive error handling.

    Shows proper error handling patterns for shadow DOM automation.
    """
    print('\nError Handling Demo')
    print('=' * 20)

    async with Chrome() as browser:
        tab = await browser.start()

        # Test 1: Element without shadow root
        await tab.go_to(
            'data:text/html,<html><body><div id="no-shadow">Regular div</div></body></html>'
        )

        try:
            regular_div = await tab.find(id='no-shadow')
            await regular_div.get_shadow_root()
            logger.error('Should have thrown NoShadowRootAttached')
        except NoShadowRootAttached:
            logger.info('Correctly detected element without shadow root')

        # Test 2: Shadow root invalidation
        await tab.go_to(
            'data:text/html,<html><body>'
            '<shadow-element id="shadow-host"></shadow-element>'
            '<script>'
            'class ShadowElement extends HTMLElement {'
            '  connectedCallback() {'
            '    const shadow = this.attachShadow({mode: "open"});'
            '    shadow.innerHTML = "<p>Content</p>";'
            '  }'
            '}'
            'customElements.define("shadow-element", ShadowElement);'
            '</script></body></html>'
        )

        try:
            shadow_host = await tab.find(id='shadow-host')
            shadow_root = await shadow_host.get_shadow_root()

            # Manually invalidate the shadow root
            shadow_root.invalidate()

            # Try to use invalidated shadow root
            await shadow_root.find_element_in_shadow('p')
            logger.error('Should have thrown InvalidShadowRoot')
        except InvalidShadowRoot:
            logger.info('Correctly detected invalidated shadow root')


async def demo_practical_example():
    """
    Practical example: Automating a custom web component.

    Real-world scenario demonstrating shadow DOM automation.
    """
    print('\nPractical Example: Custom Form Component')
    print('=' * 40)

    async with Chrome() as browser:
        tab = await browser.start()

        # Create a realistic custom form component
        form_html = """
        <html>
        <head>
            <style>
                custom-form { display: block; margin: 20px; }
            </style>
        </head>
        <body>
            <custom-form id="registration-form"></custom-form>
            <script>
                class CustomForm extends HTMLElement {
                    connectedCallback() {
                        const shadow = this.attachShadow({mode: 'open'});
                        shadow.innerHTML = `
                            <style>
                                .form-container {
                                    border: 1px solid #ccc;
                                    padding: 20px;
                                    border-radius: 8px;
                                }
                                .form-group { margin-bottom: 15px; }
                                label { display: block; margin-bottom: 5px; }
                                input { width: 100%; padding: 8px; }
                                .submit-btn {
                                    background: #007bff;
                                    color: white;
                                    padding: 10px 20px;
                                    border: none;
                                    border-radius: 4px;
                                    cursor: pointer;
                                }
                                .error { color: red; display: none; }
                            </style>
                            <div class="form-container">
                                <h3>Registration Form</h3>
                                <div class="form-group">
                                    <label for="username">Username:</label>
                                    <input type="text" id="username" class="username-input" />
                                </div>
                                <div class="form-group">
                                    <label for="email">Email:</label>
                                    <input type="email" id="email" class="email-input" />
                                </div>
                                <div class="form-group">
                                    <label for="password">Password:</label>
                                    <input type="password" id="password" class="password-input" />
                                </div>
                                <button class="submit-btn" type="button">Register</button>
                                <div class="error" id="error-message">Please fill all fields</div>
                            </div>
                        `;

                        // Add form functionality
                        const submitBtn = shadow.querySelector('.submit-btn');
                        const errorMsg = shadow.querySelector('.error');

                        submitBtn.addEventListener('click', () => {
                            const username = shadow.querySelector('.username-input').value;
                            const email = shadow.querySelector('.email-input').value;
                            const password = shadow.querySelector('.password-input').value;

                            if (!username || !email || !password) {
                                errorMsg.style.display = 'block';
                            } else {
                                errorMsg.style.display = 'none';
                                alert('Registration successful!');
                            }
                        });
                    }
                }
                customElements.define('custom-form', CustomForm);
            </script>
        </body>
        </html>
        """

        await tab.go_to(f'data:text/html,{form_html}')

        try:
            # Access the custom form component
            form_component = await tab.find(id='registration-form')
            form_shadow = await form_component.get_shadow_root()
            logger.info('Accessed custom form shadow root')

            # Fill out the form within shadow DOM
            username_input = await form_shadow.find_element_in_shadow('.username-input')
            await username_input.type_text('john_doe')

            email_input = await form_shadow.find_element_in_shadow('.email-input')
            await email_input.type_text('john@example.com')

            password_input = await form_shadow.find_element_in_shadow('.password-input')
            await password_input.type_text('securepassword123')

            logger.info('Filled form fields in shadow DOM')

            # Submit the form
            submit_button = await form_shadow.find_element_in_shadow('.submit-btn')
            await submit_button.click()

            logger.info('Successfully automated custom form component')

            # Wait a moment for any JavaScript to execute
            await asyncio.sleep(1)

        except Exception as e:
            logger.error(f'Error in practical example: {e}')


async def main():
    """
    Main function demonstrating all Shadow DOM features.
    """
    print('Pydoll Shadow DOM Security Demo')
    print('=' * 32)
    print('This demo showcases secure Shadow DOM automation with pydoll')
    print('including security features, error handling, and best practices.\n')

    try:
        await demo_basic_shadow_dom_access()
        await demo_closed_shadow_dom()
        await demo_nested_shadow_dom()
        await demo_security_features()
        await demo_error_handling()
        await demo_practical_example()

        print('\nAll Shadow DOM demos completed successfully!')
        print('\nKey Security Features Demonstrated:')
        print('• Safe shadow root access with validation')
        print('• Selector injection prevention')
        print('• Proper error handling and boundaries')
        print('• Support for open and closed shadow roots')
        print('• Nested shadow DOM navigation')
        print('• Real-world component automation')

    except Exception as e:
        logger.error(f'Demo failed with error: {e}')
        raise


if __name__ == '__main__':
    asyncio.run(main())
