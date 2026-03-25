# WebDriver BiDi Protocol Structure

## Transport Layer

**Protocol**: WebSocket (RFC 6455)
**Encoding**: JSON
**Message Types**: Commands (remote→local), Responses (local response), Events (remote→local)

### Message Format

```
Command (Remote End → Local End):
{
  "id": <js-uint>,
  "method": "<module>.<command>",
  "params": <params-object>
}

CommandResponse (Local End ← Remote End):
{
  "type": "success",
  "id": <js-uint>,
  "result": <result-object>
}

ErrorResponse:
{
  "type": "error",
  "id": <js-uint | null>,
  "error": <error-code>,
  "message": <string>,
  "stacktrace": <string> (optional)
}

Event (Local End ← Remote End):
{
  "type": "event",
  "method": "<module>.<event>",
  "params": <params-object>
}
```

**Numeric Ranges**:
- `js-int`: -9007199254740991 to 9007199254740991
- `js-uint`: 0 to 9007199254740991

---

## Modules Overview

### 1. **session Module**

#### Types
- `session.CapabilitiesRequest`
- `session.CapabilityRequest`
- `session.ProxyConfiguration`
- `session.UserPromptHandler`
- `session.UserPromptHandlerType`
- `session.Subscription`
- `session.SubscribeParameters`
- `session.UnsubscribeByIDRequest`
- `session.UnsubscribeByAttributesRequest`

#### Commands
1. **session.status** (static)
   - Params: `EmptyParams`
   - Result: implementation-defined status

2. **session.new**
   - Params: capabilities, proxy config, user prompt handlers
   - Result: sessionId, capabilities

3. **session.end**
   - Params: none
   - Result: empty

4. **session.subscribe**
   - Params: events, contexts, userContexts
   - Result: subscription id

5. **session.unsubscribe**
   - Params: subscription ids OR event/context attributes
   - Result: empty

---

### 2. **browser Module**

#### Types
- `browser.ClientWindow`
- `browser.ClientWindowInfo`
- `browser.UserContext`
- `browser.UserContextInfo`

#### Commands
1. **browser.close**
   - Params: none
   - Result: empty

2. **browser.createUserContext**
   - Params: none
   - Result: userContext id

3. **browser.getClientWindows**
   - Params: none
   - Result: list of ClientWindowInfo

4. **browser.getUserContexts**
   - Params: none
   - Result: list of UserContextInfo

5. **browser.removeUserContext**
   - Params: userContext id
   - Result: empty

6. **browser.setClientWindowState**
   - Params: handle, state (minimized/maximized/normal/fullscreen)
   - Result: empty

7. **browser.setDownloadBehavior**
   - Params: behaviors (prompt/accept/dismiss), contexts, userContexts
   - Result: empty

---

### 3. **browsingContext Module**

#### Types
- `browsingContext.BrowsingContext`
- `browsingContext.Info`
- `browsingContext.Locator`
- `browsingContext.Navigation`
- `browsingContext.NavigationInfo`
- `browsingContext.ReadinessState` (values: "none", "interactive", "complete")
- `browsingContext.UserPromptType` (values: "alert", "confirm", "prompt", "beforeunload")

#### Commands
1. **browsingContext.activate**
   - Params: context
   - Result: empty

2. **browsingContext.captureScreenshot**
   - Params: context, format, quality, origin, rect
   - Result: data (base64 string)

3. **browsingContext.close**
   - Params: context, promptHandler (optional)
   - Result: empty

4. **browsingContext.create**
   - Params: type (tab/window), referenceContext (optional), userContext (optional)
   - Result: context id

5. **browsingContext.getTree**
   - Params: root (optional), maxDepth (optional)
   - Result: tree structure of contexts

6. **browsingContext.handleUserPrompt**
   - Params: context, accept, userText (optional)
   - Result: empty

7. **browsingContext.locateNodes**
   - Params: context, locator (css selector, xpath, etc)
   - Result: list of nodes

8. **browsingContext.navigate**
   - Params: context, url, wait
   - Result: navigation id, url

9. **browsingContext.print**
   - Params: context, margins, orientation, page, scale, shrinkToFit
   - Result: data (base64 PDF)

10. **browsingContext.reload**
    - Params: context, ignoreCache, wait
    - Result: navigation id, url

11. **browsingContext.setBypassCSP**
    - Params: bypassCSP, contexts, userContexts
    - Result: empty

12. **browsingContext.setViewport**
    - Params: context, viewport (width, height)
    - Result: empty

13. **browsingContext.traverseHistory**
    - Params: context, delta
    - Result: empty

#### Events
1. **browsingContext.contextCreated**
   - Params: context, parent (optional), userContext

2. **browsingContext.contextDestroyed**
   - Params: context

3. **browsingContext.navigationStarted**
   - Params: context, navigation id, timestamp, url

4. **browsingContext.fragmentNavigated**
   - Params: context, url, timestamp

5. **browsingContext.historyUpdated**
   - Params: context, url, timestamp

6. **browsingContext.domContentLoaded**
   - Params: context, timestamp, url, navigation id

7. **browsingContext.load**
   - Params: context, timestamp, url, navigation id

8. **browsingContext.downloadWillBegin**
   - Params: context, navigation id, timestamp, url

9. **browsingContext.downloadEnd**
   - Params: context, navigation id, timestamp, url

10. **browsingContext.navigationAborted**
    - Params: context, navigation id, timestamp, url

11. **browsingContext.navigationCommitted**
    - Params: context, navigation id, timestamp, url

12. **browsingContext.navigationFailed**
    - Params: context, navigation id, timestamp, url, errorText

13. **browsingContext.userPromptClosed**
    - Params: context, accepted, userText (optional)

14. **browsingContext.userPromptOpened**
    - Params: context, type, message

---

### 4. **emulation Module**

#### Commands
1. **emulation.setForcedColorsModeThemeOverride**
   - Params: forced colors (active/none), contexts, userContexts
   - Result: empty

2. **emulation.setGeolocationOverride**
   - Params: latitude, longitude, accuracy, contexts, userContexts
   - Result: empty

3. **emulation.setLocaleOverride**
   - Params: locales, contexts, userContexts
   - Result: empty

4. **emulation.setNetworkConditions**
   - Params: offline, downloadThroughput, uploadThroughput, roundTripTime, contexts, userContexts
   - Result: empty

5. **emulation.setScreenSettingsOverride**
   - Params: colorDepth, pixelDepth, window dimensions, contexts, userContexts
   - Result: empty

6. **emulation.setScreenOrientationOverride**
   - Params: type (portrait/landscape), angle, contexts, userContexts
   - Result: empty

7. **emulation.setUserAgentOverride**
   - Params: userAgent, platform, architecture, mobile, contexts, userContexts
   - Result: empty

8. **emulation.setScriptingEnabled**
   - Params: value (boolean), contexts, userContexts
   - Result: empty

9. **emulation.setScrollbarTypeOverride**
   - Params: type (auto/thin), contexts, userContexts
   - Result: empty

10. **emulation.setTimezoneOverride**
    - Params: timezone, contexts, userContexts
    - Result: empty

11. **emulation.setTouchOverride**
    - Params: enabled, contexts, userContexts
    - Result: empty

---

### 5. **network Module**

#### Types
- `network.AuthChallenge`
- `network.AuthCredentials` (username, password)
- `network.BaseParameters`
- `network.BytesValue`
- `network.Collector`
- `network.CollectorType`
- `network.Cookie`
- `network.CookieHeader`
- `network.DataType`
- `network.FetchTimingInfo`
- `network.Header`
- `network.Initiator`
- `network.Intercept`
- `network.Request`
- `network.RequestData`
- `network.ResponseContent`
- `network.ResponseData`
- `network.SetCookieHeader`
- `network.UrlPattern`

#### Commands
1. **network.addDataCollector**
   - Params: dataTypes, contexts, userContexts
   - Result: collector id

2. **network.addIntercept**
   - Params: phases, urlPatterns, contexts, userContexts
   - Result: intercept id

3. **network.continueRequest**
   - Params: request id, url (optional), headers (optional)
   - Result: empty

4. **network.continueResponse**
   - Params: request id, statusCode (optional), reasonPhrase (optional), headers (optional), body (optional)
   - Result: empty

5. **network.continueWithAuth**
   - Params: request id, action (provide/cancel), credentials (optional)
   - Result: empty

6. **network.disownData**
   - Params: data id
   - Result: empty

7. **network.failRequest**
   - Params: request id
   - Result: empty

8. **network.getData**
   - Params: data id
   - Result: bytes data

9. **network.provideResponse**
   - Params: request id, statusCode, reasonPhrase, headers, body
   - Result: empty

10. **network.removeDataCollector**
    - Params: collector id
    - Result: empty

11. **network.removeIntercept**
    - Params: intercept id
    - Result: empty

12. **network.setCacheBehavior**
    - Params: cacheBehavior (all/none/default), contexts, userContexts
    - Result: empty

13. **network.setExtraHeaders**
    - Params: headers, contexts, userContexts
    - Result: empty

#### Events
1. **network.authRequired**
   - Params: request, authChallenge

2. **network.beforeRequestSent**
   - Params: request, initiator, timingInfo

3. **network.fetchError**
   - Params: request, errorText, timestamp, isBlocked

4. **network.responseCompleted**
   - Params: request, response, timestamp

5. **network.responseStarted**
   - Params: request, response, timestamp

---

### 6. **script Module**

#### Types
- `script.Channel`
- `script.ChannelValue`
- `script.EvaluateResult`
- `script.ExceptionDetails`
- `script.Handle`
- `script.InternalId`
- `script.LocalValue`
- `script.PreloadScript`
- `script.Realm`
- `script.PrimitiveProtocolValue`
- `script.RealmInfo`
- `script.RealmType` (values: "window", "worker", "service_worker", "shared_worker", "paint_worker", "audit_worker", "worklet")
- `script.RemoteReference`
- `script.RemoteValue`
- `script.ResultOwnership` (values: "root", "none")
- `script.SerializationOptions`
- `script.SharedId`
- `script.StackFrame`
- `script.StackTrace`
- `script.Source`
- `script.Target`

#### Commands
1. **script.addPreloadScript**
   - Params: functionDeclaration, arguments (optional), contexts, userContexts
   - Result: scriptId

2. **script.disown**
   - Params: handles, realm
   - Result: empty

3. **script.callFunction**
   - Params: functionDeclaration, arguments (optional), target, resultOwnership (optional), awaitPromise, serializationOptions (optional)
   - Result: EvaluateResult

4. **script.evaluate**
   - Params: expression, target, resultOwnership (optional), awaitPromise, serializationOptions (optional)
   - Result: EvaluateResult

5. **script.getRealms**
   - Params: context (optional), type (optional)
   - Result: list of RealmInfo

6. **script.removePreloadScript**
   - Params: scriptId
   - Result: empty

#### Events
1. **script.message**
   - Params: source, data, replies

2. **script.realmCreated**
   - Params: realm, context (optional), type, origin

3. **script.realmDestroyed**
   - Params: realm

---

### 7. **storage Module**

#### Types
- `storage.PartitionKey`

#### Commands
1. **storage.getCookies**
   - Params: filter (optional), partition (optional)
   - Result: cookies list

2. **storage.setCookie**
   - Params: cookie object (name, value, domain, path, secure, httpOnly, sameSite, expiry), partition (optional)
   - Result: empty

3. **storage.deleteCookies**
   - Params: filter (optional), partition (optional)
   - Result: empty

---

### 8. **log Module**

#### Types
- `log.LogEntry` (level, source, text, timestamp, args, stackTrace)

#### Events
1. **log.entryAdded**
   - Params: logEntry

---

### 9. **input Module**

#### Types
- `input.ElementOrigin`

#### Commands
1. **input.performActions**
   - Params: context, actions (array of action objects)
   - Result: empty

2. **input.releaseActions**
   - Params: context
   - Result: empty

3. **input.setFiles**
   - Params: context, element, files
   - Result: empty

#### Events
1. **input.fileDialogOpened**
   - Params: context

---

### 10. **webExtension Module**

#### Types
- `webExtension.Extension`

#### Commands
1. **webExtension.install**
   - Params: extension, contexts, userContexts
   - Result: extension id

2. **webExtension.uninstall**
   - Params: extension id, contexts, userContexts
   - Result: empty

---

## Error Codes

```
"invalid argument"
"invalid selector"
"invalid session id"
"invalid web extension"
"move target out of bounds"
"no such alert"
"no such network collector"
"no such element"
"no such frame"
"no such handle"
"no such history entry"
"no such intercept"
"no such network data"
"no such node"
"no such request"
"no such script"
"no such storage partition"
"no such user context"
"no such web extension"
"session not created"
"unable to capture screen"
"unable to close browser"
"unable to set cookie"
"unable to set file input"
"unavailable network data"
"underspecified storage partition"
"unknown command"
"unknown error"
"unsupported operation"
```

---

## Key Concepts

- **BiDi Flag**: Sessions track whether they support bidirectional communication
- **Subscriptions**: Targeted event filtering via subscription ids with support for specific contexts/user contexts
- **Static Commands**: Commands executable without active session (e.g., session.status)
- **User Contexts**: Isolated data partitions within browser instances
- **Sandboxed Execution**: Separate ECMAScript realms with controlled DOM access
