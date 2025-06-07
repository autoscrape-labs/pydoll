# global imports
from pydoll.commands.browser_commands import BrowserCommands
from pydoll.commands.dom_commands import DomCommands
from pydoll.commands.fetch_commands import FetchCommands
from pydoll.commands.input_commands import InputCommands
from pydoll.commands.network_commands import NetworkCommands
from pydoll.commands.page_commands import PageCommands
from pydoll.commands.runtime_commands import RuntimeCommands
from pydoll.commands.storage_commands import StorageCommands
from pydoll.commands.target_commands import TargetCommands

__all__ = [
    'DomCommands',
    'FetchCommands',
    'InputCommands',
    'NetworkCommands',
    'PageCommands',
    'RuntimeCommands',
    'StorageCommands',
    'BrowserCommands',
    'TargetCommands',
]
