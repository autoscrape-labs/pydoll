from typing import NotRequired, TypedDict


class DownloadPreferences(TypedDict, total=False):
    default_directory: str
    prompt_for_download: bool


class ProfilePreferences(TypedDict, total=False):
    password_manager_enabled: bool
    # maps content setting name -> int (e.g. popups: 0 or 1)
    default_content_setting_values: NotRequired[dict[str, int]]


class BrowserPreferences(TypedDict, total=False):
    download: DownloadPreferences
    profile: ProfilePreferences
    intl: NotRequired[dict[str, str]]
    plugins: NotRequired[dict[str, bool]]
    credentials_enable_service: bool


# Runtime schema used for validating preference paths and value types.
# Keys map to either a python type (str/bool/int/dict) or to a nested dict
# describing child keys and their expected types.
PREFERENCE_SCHEMA: dict = {
    'download': {
        'default_directory': str,
        'prompt_for_download': bool,
        'directory_upgrade': bool,
    },
    'profile': {
        'password_manager_enabled': bool,
        # default_content_setting_values is a mapping of content name -> int
        'default_content_setting_values': {
            'popups': int,
            'notifications': int,
            'automatic_downloads': int,
        },
    },
    'intl': {
        'accept_languages': str,
    },
    'plugins': {
        'always_open_pdf_externally': bool,
    },
    'credentials_enable_service': bool,
}
