import asyncio
import json
import subprocess
import signal

import websockets

from pydoll.protocol.bidi.session.methods import (
    SessionMethod,
    NewParameters,
    StatusCommand,
    NewCommand,
    EndCommand,
    SubscribeCommand,
)
from pydoll.protocol.bidi.session.types import (
    CapabilitiesRequest,
    SubscribeParameters,
)


FIREFOX_PATH = '/Applications/Firefox.app/Contents/MacOS/firefox'
WS_PORT = 9222
cmd_counter = 0


def build_status_command() -> StatusCommand:
    global cmd_counter
    cmd_counter += 1
    return {'id': cmd_counter, 'method': SessionMethod.STATUS, 'params': {}}


def build_new_command() -> NewCommand:
    global cmd_counter
    cmd_counter += 1
    params: NewParameters = {'capabilities': CapabilitiesRequest()}
    return {'id': cmd_counter, 'method': SessionMethod.NEW, 'params': params}


def build_subscribe_command(events: list[str]) -> SubscribeCommand:
    global cmd_counter
    cmd_counter += 1
    params: SubscribeParameters = {'events': events}
    return {'id': cmd_counter, 'method': SessionMethod.SUBSCRIBE, 'params': params}


def build_end_command() -> EndCommand:
    global cmd_counter
    cmd_counter += 1
    return {'id': cmd_counter, 'method': SessionMethod.END, 'params': {}}


async def send(ws, command):
    print(f'\n>>> {json.dumps(command, indent=2)}')
    await ws.send(json.dumps(command))
    response = await ws.recv()
    parsed = json.loads(response)
    print(f'<<< {json.dumps(parsed, indent=2)}')
    return parsed


async def main():
    process = subprocess.Popen(
        [
            FIREFOX_PATH,
            '--remote-debugging-port', str(WS_PORT),
            '--new-instance',
            '--profile', '/tmp/firefox_bidi_debug',
            'about:blank',
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    print(f'Firefox PID {process.pid}')
    await asyncio.sleep(3)

    ws_url = f'ws://localhost:{WS_PORT}/session'
    print(f'Connecting to {ws_url}...')

    try:
        async with websockets.connect(ws_url) as ws:
            print('Connected!\n')

            await send(ws, build_status_command())
            await send(ws, build_new_command())
            await send(ws, build_subscribe_command([
                'browsingContext.contextCreated',
                'browsingContext.load',
            ]))
            await send(ws, build_end_command())

    except Exception as e:
        print(f'Error: {e}')
    finally:
        process.send_signal(signal.SIGTERM)
        process.wait(timeout=5)
        print('\nFirefox terminated.')


if __name__ == '__main__':
    asyncio.run(main())
