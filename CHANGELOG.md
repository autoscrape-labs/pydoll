## 2.16.0 (2026-02-06)

### Feat

- add clear method for input and enhance page load state handling

### Fix

- **browser**: support secure websocket connections

## 2.15.1 (2026-01-04)

### Fix

- filter Symbol properties from element query results

## 2.15.0 (2025-12-24)

### Feat

- Implement incognito mode cookie retrieval for `tab.get_cookies()` and update related documentation

### Fix

- inconsistence in type checking
- Dispatch `KEY_DOWN` and `KEY_UP` events for character typing

## 2.14.0 (2025-12-10)

### Feat

- get_tab_by_target method added
- get_tab_by_target method added

### Fix

- adding type: ignore in JavascriptDialogOpeningEvent object
- adding type: ignore in JavascriptDialogOpeningEvent object

## 2.13.1 (2025-12-07)

### Fix

- add stuck scroll detection and minimum flick distance to humanized scroll, and correct scroll distance calculation.

## 2.13.0 (2025-12-07)

### Feat

- Implement humanized keyboard typing and physics-based scroll, and add iframe interaction support.

## 2.12.4 (2025-11-29)

### Fix

- optimize iframe resolution logic by adjusting backend node ID checks and enhancing child frame handling
- refine OOPIF resolution and frame attachment logic for improved handling of backend node IDs
- enhance OOPIF target attachment logic for improved session handling

## 2.12.3 (2025-11-27)

### Fix

- improve frame retrieval logic for better session handling

## 2.12.2 (2025-11-19)

### Fix

- adjust find_elements_mixin.py to refine return types and defaults

## 2.12.1 (2025-11-14)

### Fix

- continue cleanup process if temporary directory still exists
- adjust sleep duration for Windows and enhance temp dir cleanup
- enhance error handling for locked files on Windows systems
- remove unnecessary retry_times parameter in file processing
- ensure temp directory cleanup handles Chromium locked files
- enhance element selection and text extraction for better stability
- handle oopif targets
- change way to interact with iframes

### Refactor

- refactor iframe context handling in FindElementsMixin class

### Perf

- update Chrome options for better memory management and stability

## 2.12.0 (2025-11-04)

### Feat

- **execute_script**: validate element argument usage
- **tab,element,chrome**: revert arguments and add Chromium paths
- add a retry decorator for handling function execution failures

### Fix

- import TopLevelTargetRequired in test_browser_tab.py
- allow one additional retry attempt in the retry decorator

### Refactor

- **tab,element**: simplify execute_script parameters
- **element**: move and enhance execute_script from tab
- **tab**: separate execute_script concerns and enhance with comprehensive options

## 2.11.0 (2025-11-02)

### Feat

- add input handling functions and key constants for editing
- add KeyboardAPI for simulating keyboard input actions
- add KeyboardAPI integration for enhanced keyboard control

### Fix

- enhance text insertion and deprecate legacy key methods

## 2.10.0 (2025-11-01)

### Feat

- add ScrollAPI for enhanced page scrolling capabilities

## 2.9.3 (2025-10-30)

### Refactor

- keep take_screenshot consistent
- refactor type hints for better clarity and future compatibility

## 2.9.2 (2025-10-19)

### Fix

- update process creation to capture output and clean proxy format
- preserve query and fragment in WebSocket URL for tabs

### Refactor

- remove debug logging for request status and network events
- refactor logger messages to use consistent single quotes
- fix merge conflicts
- add logging for browser lifecycle and context management events
- refactor proxy parsing logic for improved clarity and efficiency

## 2.9.1 (2025-10-15)

### Fix

- change download event handling to use PageEvent instead of BrowserEvent

### Refactor

- use early return in setup proxy method

## 2.9.0 (2025-10-05)

### Feat

- add configurable page load state

## 2.8.2 (2025-10-03)

### Fix

- implement proxy authentication handling for browser tabs
- map exception when try to take screenshot of an iframe

## 2.8.1 (2025-09-27)

### Fix

- store the opened tab in the _tabs_opened dictionary
- **elements**: correctly detect parenthesized XPath expressions

### Refactor

- simplify FindElementsMixin._get_expression_type startswith checks into single tuple

## 2.8.0 (2025-08-28)

### Feat

- adding get_siblings_elements method
- adding get_children_elements method
- refactor Tab class to support optional WebSocket address handling
- add WebSocket connection support for existing browser instances
- add optional WebSocket address support in connection handler

### Fix

- add get siblings and get childen methods a raise_exc option
- improving children and parent retrive docstring and creating a private generic method for then
- using new execute_script public method
- solving conflicts
- rename pages fixtures files and adding a error test

### Refactor

- refactor Tab class to improve initialization and error handling
- refactor Browser class to manage opened tabs and WebSocket setup
- add new exception classes for connection and WebSocket errors

## 2.7.0 (2025-08-22)

### Feat

- refactor WebElement methods to use a unified naming convention
- add Response type and new bring_to_front method to Tab class
- improve element interactability scripts

### Fix

- **browser**: add google-chrome-stable path for Arch Linux AUR package
- run actions to fix badges
- enforce combined condition logic in wait_until
- **web_element**: raise WaitElementTimeout on wait_until timeout

### Refactor

- update command responses to use Response for empty responses
- **webelement**: simplify wait_until condition mapping

## 2.6.0 (2025-08-10)

### Feat

- add DownloadTimeout exception for file download timeouts
- add context manager for handling file downloads in Tab class

### Refactor

- add type checking for connection handler in mixin class
- add type overloads for event callback in Browser class

## 2.5.0 (2025-08-07)

### Feat

- add HTTP client functionality using the browser's fetch API
- add HTTP response object for browser-based fetch requests
- implement Request class for HTTP requests using fetch API
- add Request handling and improve network log retrieval methods

### Fix

- reject cookies with empty names during parsing in Request class
- refactor imports to include NotRequired and TypedDict from typing_extensions
- update imports to use typing_extensions for compatibility reasons
- check for None in events_enabled before updating params
- remove unused event type aliases and clean up imports

### Refactor

- depreciating headless argument in start method and adding it in to browser options properties
- add asynchronous function for makeRequest in JavaScript
- refactor imports for cleaner organization and improved clarity
- refactor type hints in FindElementsMixin for clarity and type safety
- refactor type hints and improve command method signatures
- refactor event handling to use specific event types for clarity
- refactor connection handler to use CDPEvent and typed commands
- refactor storage command methods to return specific command types
- refactor target command methods to use specific command types
- refactor command return types to specific command classes
- refactor page commands to use specific command types directly
- refactor network commands to use specific command types
- refactor input command methods to return specific command types
- refactor fetch_commands to use updated type definitions
- refactor enums to inherit from str for better compatibility
- refactor DOM command types for improved code clarity and structure
- refactor command and event parameter types for better typing
- refactor command responses to use EmptyResponse where applicable
- improve protocol types for target domain
- improve protocol types for storage domain
- refactor command response types for improved readability and consistency
- improve protocol types for page domain
- add IncludeWhitespace and RelationType enums to DOM types
- improve protocol types for input domain
- refactor AuthChallengeResponse and remove legacy definitions
- remove legacy WindowBoundsDict for cleaner type definitions
- add new TypedDicts and enums for runtime event parameters
- refactor DOM event types and methods for better clarity and structure
- refactor fetch command return types for better clarity and structure
- enhance browser command functionality with new methods and types
- add TypedDict and Enum definitions for emulation and debugging
- improve protocol types for network domain

## 2.4.0 (2025-08-01)

### Feat

- changing bool prefs to properties and adding support to user-data-dir preferences
- adding prefs options customization
- add overloads for find and query methods in FindElementsMixin
- add method to retrieve parent element and its attributes
- implements start_timeout option

### Fix

- adding typehint and fixing some codes
- removing options preferences private attributes
- set default URL to 'about:blank' in create_target method
- change navigation when creating a new tab
- add type hinting support and update project description

### Refactor

- remove redundant asterisk from find method overloads and reorganize query method overloads
- refine type hint for response parameter and improve key check

## 2.3.1 (2025-07-12)

### Fix

- refactor click_option_tag to use direct script reference
- update script to use closest for more reliable DOM selection
- improve selection script for higher accuracy
- use correct class name and id selector in query()
- add fetch command methods to handle request processing

### Refactor

- change body type from dict to string in fetch command parameters
- refactor continue_request and fulfill_request to use options
- enhance continue_request and fulfill_request with new options

## 2.3.0 (2025-06-25)

### Feat

- **connection**: Upgrade adapt websockets version to 14.0

### Fix

- refine selector condition to include attributes check

## 2.2.3 (2025-06-20)

### Fix

- fix contextmanager for file upload

## 2.2.2 (2025-06-18)

### Fix

- fix call_function_on parameters order

### Refactor

- replace BeautifulSoup with custom HTML text extractor

## 2.2.1 (2025-06-16)

### Fix

- fix call parameters order in call_function_on method

## 2.2.0 (2025-06-15)

### Feat

- add method to retrieve non-extension opened tabs as Tab instances

### Refactor

- refactor attribute assignments to include type annotations
- implement singleton pattern for Tab instances by target_id

## 2.1.0 (2025-06-14)

### Feat

- add new script-related exception classes for better handling
- add functions to clean scripts and check return statements
- add methods to retrieve network response body and logs

### Fix

- click in the input before typing and fix documentation

### Refactor

- add overloads for execute_script to improve type safety

## 2.0.1 (2025-06-08)

### Fix

- fix private proxy configuration

## 2.0.0 (2025-06-08)

### BREAKING CHANGE

- pydoll v2 finished

### Feat

- intuitive way to interact with iframes
- refactor Keys class to Key and add utility methods for enums
- add Event TypedDict for standardized event structure
- add TargetEvent enum for Chrome DevTools Protocol events
- add StorageEvent enumeration for Chrome DevTools Protocol events
- add RuntimeEvent enumeration for Chrome DevTools Protocol events
- add PageEvent enumeration for Chrome DevTools Protocol events
- add NetworkEvent enumeration for Chrome DevTools Protocol events
- add InputEvent enum for Chrome DevTools input events
- add FetchEvent enumeration for Chrome DevTools Protocol events
- add DomEvent enumeration for Chrome DevTools Protocol events
- add BrowserEvent enum for Chrome DevTools protocol events
- add methods to enable and disable the runtime domain commands
- add new enums for whitespace, axes, pseudo types, and modes
- add DOM response types and corresponding response classes
- add DOM command types and parameter definitions for pydoll
- add enums for key, mouse, touch, and drag event types
- add input command types for touch, mouse, and keyboard events
- enhance TargetCommands class with new methods for targets management
- add TypedDicts for target response types and browser contexts
- add TypedDict definitions for target command parameters
- add storage-related enumerations for bucket durability and types
- enhance StorageCommands with new methods for data management
- add storage response types and related classes for handling data
- add storage command types using TypedDict for structured params
- add new enumeration classes for serialization and object types
- add runtime response types for handling various object previews
- add initial runtime command types for protocol handling
- add constants for various encoding, formats, and policies
- add TypedDict definitions for page response types and results
- add typed dictionaries for various page command parameters
- add new command parameter classes for network resource handling
- add TypedDict definitions for network response types
- organize command types into structured imports and exports
- add network command types and parameters for cookie management
- add enums for cookie priorities, connection types, and encodings
- add response classes for browser window target retrieval
- setup mkdocs and install related packages
- add async text property for retrieving element text

### Fix

- remove target directory from .gitignore file
- fix typo in USB_UNRESTRICTED constant for consistency
- add new network command parameters and methods for cookies
- change postData type from dict to string in ContinueRequestParams

### Refactor

- refactor screenshot path handling and enhance error checking
- refactor type hints from List to built-in list for consistency
- refine XPath condition handling and ensure integer coordinates
- refactor condition checks to ensure against None values
- refactor exception handling and add browser path validation function
- rename BrowserOptionsManager to ChromiumOptionsManager
- refactor Edge class to use ChromiumOptionsManager and simplify path validation
- refactor Chrome class to use Chromium-specific options manager
- refactor Browser class to use options manager and improve methods
- refactor Options class to ChromiumOptions and use type hints
- refactor to create ChromiumOptionsManager for better clarity
- add abstract base classes for browser options management
- use `message.get('id')` for safer ID checks in response
- refactor message handling to support multiple message types
- refactor element finding methods for enhanced flexibility and clarity
- rename method for better clarity in captcha element handling
- refactor type hints for event callback parameters and options
- simplify ping call by inlining WebSocketClientProtocol cast
- refactor EventsManager to use typed Event objects consistently
- add runtime events management to the Tab class functionality
- update event callback signatures for better type handling
- remove unused import of Response in runtime_commands.py
- add Response import to page_commands for improved functionality
- refactor response classes to use TypedDict for better typing
- refactor WebElement class to organize exception imports clearly
- refactor exception handling in FindElementsMixin class
- refactor exception handling to use custom timeout and connection errors
- remove unused import statements in events_manager.py
- refactor error handling to use specific exceptions for clarity
- refactor error handling to use custom exception for arguments
- fix PermissionError raising in TempDirectoryManager class
- refactor error handling to use specific exceptions for clarity
- handle unsupported OS with a custom exception in Edge class
- raise UnsupportedOS exception for unsupported operating systems
- refactor browser error handling and improve method return types
- refactor exception classes to improve organization and clarity
- refactor element finding methods to use updated command structure
- refactor WebElement class for improved structure and clarity
- refactor import statements and clean up code formatting
- refactor command imports and enhance download behavior method
- refactor Tab import and update FetchCommands method calls
- refactor ConnectionHandler docstrings for clarity and conciseness
- refactor command and event managers for improved type safety
- refactor ConnectionHandler to improve WebSocket management and clarity
- add Tab class for managing browser tabs via CDP integration
- enhance TempDirectoryManager with detailed docstrings and type hints
- refactor ProxyManager to enhance proxy credential handling
- refactor Browser class to enhance automation capabilities and structure
- move commands to a different module
- define base structures for commands and responses in protocol
- import Rect from dom_commands_types for response handling
- refactor cookie-related types for improved clarity and consistency
- remove unnecessary whitespace in docstring of InputCommands class
- refactor DOM commands to improve structure and add functionality
- refactor InputCommands to enhance user input simulation methods
- add CookieParam TypedDict to define cookie attributes
- add new runtime command methods for JavaScript bindings and promises
- remove unused method to clear accepted encodings in network commands
- update ResetPermissionsParams to use NotRequired for context ID
- refactor PageCommands to improve structure and add type hints
- simplify import statements by using wildcard imports for responses
- add new response types and update existing response classes
- consolidate command imports using wildcard imports for clarity
- correct post_data type from dict to str in FetchCommands class
- refactor NetworkCommands to use structured command parameters
- refactor fetch command methods to use static methods directly
- refactor BrowserCommands to use static methods and improve clarity
- refactor response imports and update __all__ definitions
- refactor import statements for better readability and structure
- refactor import statements for consistency in response types
- refactor import and rename EnableParams to FetchEnableParams
- refactor import statement for CommandParams module path
- refactor fetch command templates to use Command class
- add enums for window states, download behaviors, and permissions
- remove unused enum imports and rename base_types module
- refactor command structures for better organization and clarity
- rename command and response modules for better clarity
- refactor imports for better organization and readability
- add browser command methods for version, permissions, and downloads
- add command and response types for protocol implementation
- refactor execute_command to use type annotations for clarity
- refactor command methods to specify response types in BrowserCommands
- refactor command structures and introduce base CommandParams class
- refactor browser command constants to use Command class type
- refactor connection imports and rename manager files for clarity
- refactor BrowserType import to a common constants module
- refactor browser modules to use the new chromium structure
- refactor element imports and remove deprecated element file
- refactor import paths to use the protocol submodule structure
- move command files to the protocol directory for better structure
- rename insert_text to paste_text and remove unused files
- refactor the `InputCommands` class to enhance clarity and simplicity in its operations
- add deprecation warning to get_element_text()

## 1.7.0 (2025-04-06)

### Feat

- refactor captcha handling with adjustable wait times and parameters

## 1.6.0 (2025-04-06)

### Feat

- add connect method to handle existing port scenarios
- create enable_auto_solve_cloudflare_captcha method
- add context manager to bypass Cloudflare Turnstile captcha

## 1.5.1 (2025-03-31)

### Fix

- handle headers input as list or dictionary in fetch command

## 1.5.0 (2025-03-26)

### Feat

- add flag to run browser on headless mode on start function

### Fix

- Wait for the file `CrashpadMetrics-active.pma` to be deoccupied and cleaned up
- Catch websockets.ConnectionClosed errors on duplicate close()
- move connection closed log inside if statement

## 1.4.0 (2025-03-23)

### Feat

- Update initialize_options method to allow optional browser_type parameter
- Refactor Edge browser options handling to use EdgeOptions class
- Supports initialization options based on browser type
- Edge browser constructors to support optional connection port parameters
- Add Microsoft Edge browser support
- 为 Edge 浏览器添加默认用户数据目录支持
- Add Microsoft Edge browser support

### Refactor

- Clean up imports and improve code formatting across browser modules
- Simplify user data directory setup and enhance Edge browser path handling

## 1.3.3 (2025-03-18)

### Fix

- solve browser invalid domain events issue
- improve process termination
- improve process management and deactivate websockets connection size limit

### Refactor

- import commands and evebts from __init__.py

## 1.3.2 (2025-03-13)

### Fix

- fixed the tests and used lint for the OS multi path support
- support multiple default Chrome paths on each OS

## 1.3.1 (2025-03-12)

### Fix

- remove unnecessary encoding from screenshot response data

## 1.3.0 (2025-03-12)

### Feat

- add method to retrieve screenshot as base64 encoded string

## 1.2.4 (2025-03-11)

### Fix

- refactor Chrome constructor to use Optional for parameters

## 1.2.3 (2025-03-11)

### Fix

- refactor proxy configuration retrieval for cleaner code flow

## 1.2.2 (2025-03-10)

### Fix

- Get file extension from file path and changes use of reserved word 'format' to 'fmt'

## 1.2.1 (2025-03-09)

### Fix

- resolve issue #29 where browser path was not found on macOS
- Quickstart code given in README is wrong

## 1.2.0 (2025-02-11)

### Feat

- add close method and command to Page class functionality

## 1.1.0 (2025-02-11)

### Feat

- add method to retrieve Page instance by its ID in Browser class

## 1.0.1 (2025-02-10)

### Fix

- add dialog property to ConnectionHandler and manage dialog state

## 1.0.0 (2025-02-05)

### BREAKING CHANGE

- now you'll have to use By.CSS_SELECTOR instead of By.CSS

### Feat

- refactor import and export statements for better readability
- update changelog for version 0.7.0 and fix dependency versions
- add ping method to ConnectionHandler for browser connectivity check
- add tests for BrowserCommands in test_browser_commands.py

### Fix

- add initial module files for commands, connection, events, and mixins
- add connection port parameter to Chrome browser initialization
- use deepcopy for templates to prevent mutation issues

### Refactor

- rename constant CSS to CSS_SELECTOR
- add command imports and remove obsolete connection handler code
- refactor methods to be static in ConnectionHandler class
- refactor proxy configuration and cleanup logic in Browser class
- refactor ConnectionHandler to improve WebSocket management logic
- refactor Browser class initialization for better clarity and structure
- refactor Browser initialization to enhance flexibility and defaults
- refactor import statement for ConnectionHandler module
- refactor import paths for ConnectionHandler in browser modules
- implement ConnectionHandler for WebSocket browser automation
- implement command and event management for asynchronous processing
- remove unnecessary logging for WebSocket address fetching
- refactor Chrome class to use BrowserOptionsManager for path validation
- implement proxy and browser management in the new managers module
- refactor Browser class to use manager classes for better structure
- refactor DOM command scripts for clarity and efficiency

## 0.7.0 (2024-12-09)

### Feat

- autoremove dialog from connection_handler when closed
- add handle_dialog method to PageCommands class
- add dialog handling methods to Page class
- add support for handling JavaScript dialog opening events
- refactor network response handling for base64 encoding support
- add clipping option for screenshots and implement element capture

### Fix

- index error on method get_dialog_message
- update screenshot format from 'jpg' to 'jpeg' for consistency
- handle potential IndexError when retrieving valid page targetId
- filter valid pages using URL condition instead of title check

### Refactor

- run ruff formatter to ensure code consistency
- run ruff formatter to ensure code consistency
- change screenshot format from PNG to JPG in commands and element

## 0.6.0 (2024-11-18)

### Feat

- add callback ID handling for page load events in Page class
- update event registration to return callback IDs and add removal
- refactor DOM commands to use object_id instead of node_id

### Fix

- refactor page navigation and loading logic for efficiency
- add page reload after navigating to a new URL in Page class
- refactor URL navigation to use evaluate_script for efficiency
- implement page refresh on URL unchanged and add navigation event
- update object ID reference in Page class for clarity
- refactor element search logic to simplify error handling
- DomCommands using `object_id` instead of `node_id` to prevent bugs
- handle OSError when cleaning up temporary directories in Browser

### Refactor

- change error log to warning for missing callback ID
- refactor DOM command scripts for improved readability and reuse
- rename methods for clarity and consistency in WebElement class
- refactor parameter names for consistency in target methods
- normalize variable naming for consistency in fetch commands

## 0.5.1 (2024-11-12)

### Fix

- simplify outer HTML retrieval for consistent object handling
- refactor click method to check option tag earlier in flow
- refactor bounding box retrieval to access nested response value
- handle KeyError instead of IndexError for element bounds retrieval
- enhance DOM command methods and rename for clarity and consistency
- add JavaScript bounding box retrieval for web elements
- remove redundant top-checks for element clicks in WebElement

## 0.5.0 (2024-11-11)

### Feat

- add method to generate command for calling a function on an object
- implement script execution and visibility checks in click method
- add JavaScript functions for element visibility and interaction

### Refactor

- enhance exception classes with descriptive error messages
- simplify command creation by using RuntimeCommands.evaluate_script
- refactor JavaScript execution and introduce runtime commands

## 0.4.4 (2024-11-11)

### Fix

- remove redundant DOM content loaded event handling logic

## 0.4.3 (2024-11-11)

### Fix

- rename event variables for clarity and improve timeout handling

### Refactor

- remove debug print statement from connection event handling

## 0.4.2 (2024-11-11)

### Fix

- update event handling to use DOM_CONTENT_LOADED for page load
- convert Browser context management to async methods

### Refactor

- fix string formatting in logger info message for clarity

## 0.4.1 (2024-11-08)

### Fix

- fixes workflow removing unnecessary hifen
- reduce sleep duration in key press handling for improved speed

## 0.4.0 (2024-11-08)

### Feat

- add type_keys method for realistic key input simulation

## 0.3.1 (2024-11-08)

### Fix

- addning new package version
- removing encode utf8 in get_pdf_base64

## 0.3.0 (2024-11-08)

### Feat

- set_download_path added in browser class methods

## 0.2.0 (2024-11-08)

### Feat

- dynamic lib version using pyproject

## 0.1.1 (2024-11-07)

### Fix

- ensure browser process terminates after executing close command

## 0.1.0 (2024-11-07)

### Feat

- add method to delete all cookies from the browser session
- add is_enabled property to check element's enabled status
- add option to raise exception in wait_element method
- add method to set browser download path via command
- refactor text extraction using BeautifulSoup for accuracy
- add method to get properties and improve XPath handling
- refactor text retrieval methods and improve code readability
- add timeout parameter to page navigation and loading methods
- add cookie management and scroll into view functionality
- add method to retrieve page PDF data as base64 string
- add async property to retrieve inner HTML of the element
- add async page_source property to retrieve page source code
- add async property to retrieve the current page URL
- add method to find multiple DOM elements using selectors
- refactor WebElement to use FindElementsMixin for clarity
- add FindElementsMixin for asynchronous DOM element handling
- add methods to retrieve network response bodies from logs
- add method to retrieve matching network logs from the page
- add cookie management methods to the Browser class
- add ElementNotFound exception to handle missing elements
- add value property and handle option tag clicks in WebElement
- rename FIND_ELEMENT_XPATH_TEMPLATE to EVALUATE_TEMPLATE
- add exception handling for element not found in find_element method
- downgrade Python version requirement to 3.10 in pyproject.toml
- add async function to fetch browser WebSocket address
- simplify text input handling by using insert_text command
- add TargetCommands class for managing target operations
- add method to generate command for disabling the Page domain
- add method to generate text insertion commands for inputs
- add Page class to manage browser page interactions and events
- add page management methods to the Browser class
- add detailed logging for command responses and event handling
- add event classes for browser, DOM, fetch, and network actions
- add NetworkCommands class for managing network operations
- implement fetch command methods for handling requests and responses
- add method to enable DOM domain events in DomCommands class
- add proxy configuration and fetch event handling to Browser
- refactor connection errors to use custom exceptions for clarity
- add methods to clear callbacks and close WebSocket connection
- remove unnecessary newline at the end of PageEvents class file
- add context managers and async file handling for efficiency
- implement singleton pattern and prevent multiple initializations
- add dynamic connection port handling for browser instance
- add temporary directory management for browser session storage
- add logging for connection events and command executions
- add PageEvents class with PAGE_LOADED event constant
- add temporary callback option to event registration method
- add page event handling and improve loading timeout management
- add utility function to decode base64 images to bytes
- add WebElement class for handling browser elements asynchronously
- add enumeration for selector types in constants module
- add PageCommands class for browser page control functions
- add InputCommands class for handling mouse and keyboard events
- implement DOM commands for interacting with web elements
- refactor BrowserCommands to include new window management methods
- implement some basic methods to navigate and control the browser instance
- enhance ConnectionHandler with detailed docstrings for methods
- add .gitignore, .python-version, and poetry.lock files

### Fix

- browser context now uses the storage commands to get cookies, while the page context us cookies, while page context uses network
- update cookie retrieval to use NetworkCommands for consistency
- remove download path method from Browser and add to Page class
- add options to disable first-run and browser check flags
- handle KeyError when retrieving network response bodies
- use get() to safely retrieve attributes in WebElement class
- rename class attribute retrieval for clarity and consistency
- enhance get_properties and simplify text retrieval method
- enhance create_web_element call with additional value parameter
- fix incorrect key access in JavaScript evaluation result
- update cookie management to clear browser cookies correctly
- filter pages by title instead of URL in Browser class
- filter out non-page entries when fetching valid page IDs
- xpath element solved
- refactor event callback storage to use unique callback IDs
- add JavaScript execution method and enhance click offsets
- simplify response handling and improve event callback structure
- reorder page event enabling to ensure proper browser startup
- add JSON handling and improve WebSocket command execution

### Refactor

- improve WebElement representation and handle None for nodeValue
- add newline at end of file for ElementNotFound exception class
- remove unused aiohttp import and clean up whitespace
- remove unnecessary blank lines in storage.py for clarity
- fix missing newline at the end of the file in page.py
- remove unnecessary whitespace in InputCommands class methods
- refactor DOM command methods for improved clarity and usability
- refactor Page class to inherit from FindElementsMixin
- refactor code to remove duplicate import of StorageCommands
- clarify error messages for command and callback validation
- refactor ConnectionHandler to simplify initialization and connect logic
- remove unnecessary whitespace in element.py for cleaner code
- refactor WebElement to enhance attribute retrieval methods
- refactor connection handling and improve error messaging
- refactor Browser class to use abstract base class and commands
