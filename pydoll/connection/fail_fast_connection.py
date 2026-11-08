from __future__ import annotations

from websockets.asyncio.client import ClientConnection


class FailFastConnection(ClientConnection):
    """WebSocket client connection that ends at once when it fails the connection itself.

    When a received frame breaks the protocol, most often a CDP message larger
    than ``max_message_size``, websockets sends the close frame and then waits
    for the browser to close the TCP connection, as RFC 6455 asks of a client.
    Nothing bounds that wait while no frame is being sent, and Chrome can take
    seconds to close (or never close, if it stopped reading), so the receive
    loop and every pending command would wait with it. Closing the transport
    right away still flushes the close frame, then ends the connection.
    """

    def data_received(self, data: bytes) -> None:
        super().data_received(data)
        if self.protocol.parser_exc is not None:
            self.transport.close()
