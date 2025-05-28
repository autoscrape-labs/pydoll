from enum import Enum


class BrowserEvent(str, Enum):
    """
    Events from the Browser domain of the Chrome DevTools Protocol.

    This enumeration contains the names of browser-related events that can be
    received from the Chrome DevTools Protocol. These events provide information
    about browser activities and state changes.
    """

    DOWNLOAD_PROGRESS = 'Browser.downloadProgress'
    """
    Fired when download makes progress. The last call has |done| == true.

    Args:
        guid (str): Global unique identifier of the download.
        totalBytes (int): Total expected bytes to download.
        receivedBytes (int): Total bytes received.
        state (str): Download status.
            Allowed values: 'inProgress', 'completed', 'canceled'
    """

    DOWNLOAD_WILL_BEGIN = 'Browser.downloadWillBegin'
    """
    Fired when page is about to start a download.

    Args:
        frameId (str): Id of the frame that caused the download to begin.
        guid (str): Global unique identifier of the download.
        url (str): URL of the resource being downloaded.
        suggestedFilename (str): Suggested file name of the resource
            (the actual name of the file saved on disk may differ).
    """
