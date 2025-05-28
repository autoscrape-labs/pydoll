from enum import Enum


class TargetMethod(str, Enum):
    ACTIVATE_TARGET = 'Target.activateTarget'
    ATTACH_TO_TARGET = 'Target.attachToTarget'
    CLOSE_TARGET = 'Target.closeTarget'
    CREATE_BROWSER_CONTEXT = 'Target.createBrowserContext'
    CREATE_TARGET = 'Target.createTarget'
    DETACH_FROM_TARGET = 'Target.detachFromTarget'
    DISPOSE_BROWSER_CONTEXT = 'Target.disposeBrowserContext'
    GET_BROWSER_CONTEXTS = 'Target.getBrowserContexts'
    GET_TARGETS = 'Target.getTargets'
    SET_AUTO_ATTACH = 'Target.setAutoAttach'
    SET_DISCOVER_TARGETS = 'Target.setDiscoverTargets'
    # Métodos experimentais
    ATTACH_TO_BROWSER_TARGET = 'Target.attachToBrowserTarget'
    AUTO_ATTACH_RELATED = 'Target.autoAttachRelated'
    EXPOSE_DEV_TOOLS_PROTOCOL = 'Target.exposeDevToolsProtocol'
    GET_TARGET_INFO = 'Target.getTargetInfo'
    SET_REMOTE_LOCATIONS = 'Target.setRemoteLocations'
