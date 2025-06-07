from enum import Enum


class BrowserMethod(str, Enum):
    ADD_PRIVACY_SANDBOX_COORDINATOR_KEY_CONFIG = 'Browser.addPrivacySandboxCoordinatorKeyConfig'
    ADD_PRIVACY_SANDBOX_ENROLLMENT_OVERRIDE = 'Browser.addPrivacySandboxEnrollmentOverride'
    CLOSE = 'Browser.close'
    GET_VERSION = 'Browser.getVersion'
    RESET_PERMISSIONS = 'Browser.resetPermissions'
    CANCEL_DOWNLOAD = 'Browser.cancelDownload'
    CRASH = 'Browser.crash'
    CRASH_GPU_PROCESS = 'Browser.crashGpuProcess'
    EXECUTE_BROWSER_COMMAND = 'Browser.executeBrowserCommand'
    GET_BROWSER_COMMAND_LINE = 'Browser.getBrowserCommandLine'
    GET_HISTOGRAM = 'Browser.getHistogram'
    GET_HISTOGRAMS = 'Browser.getHistograms'
    GET_WINDOW_BOUNDS = 'Browser.getWindowBounds'
    GET_WINDOW_FOR_TARGET = 'Browser.getWindowForTarget'
    GRANT_PERMISSIONS = 'Browser.grantPermissions'
    SET_DOCK_TILE = 'Browser.setDockTile'
    SET_DOWNLOAD_BEHAVIOR = 'Browser.setDownloadBehavior'
    SET_PERMISSION = 'Browser.setPermission'
    SET_WINDOW_BOUNDS = 'Browser.setWindowBounds'
