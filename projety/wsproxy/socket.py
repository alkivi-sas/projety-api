"""Socket that will proxy request to a local port."""
from __future__ import absolute_import

import logging
import select
import sys
import errno

import socket as _socket

from base64 import b64encode
from hashlib import sha1

logger = logging.getLogger(__name__)


class ProxySocket(object):
    """An Websockify proxy socket."""

    upgrade_protocols = ['websocket']

    GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    buffer_size = 65536

    class CClose(Exception):
        """An exception while the WebSocket client was connected."""

        pass

    def __init__(self, server, sid):
        """Init."""
        self.server = server
        self.sid = sid

        # To have the state of our socket
        self.connected = False
        self.upgraded = False
        self.closed = False

        # Not sure we need this
        self.base64 = False

        # Init to none
        self.proxy_port = None
        self.proxy_socket = None

    def setup_proxy(self, port):
        """Create the proxy socket."""
        self.proxy_port = port

        # Create proxy_socket and connect to it
        host = '127.0.0.1'
        port = self.proxy_port
        flags = 0

        # Create socket magic
        addrs = _socket.getaddrinfo(host, port, 0, _socket.SOCK_STREAM,
                                    _socket.IPPROTO_TCP, flags)

        if not addrs:
            raise Exception("Could not resolve host '%s'" % host)

        addrs.sort(key=lambda x: x[0])
        self.proxy_socket = _socket.socket(addrs[0][0], addrs[0][1])
        self.proxy_socket.connect(addrs[0][4])

        self.proxy_socket.setsockopt(_socket.SOL_SOCKET,
                                     _socket.SO_KEEPALIVE, 1)
        return True

    def do_proxy(self, environ, start_response):
        """Start a thread to proxy request to a specific port."""
        # Select the right websocket class
        if self.server.async['websocket'] is None or \
                self.server.async['websocket_class'] is None:
            # the selected async mode does not support websocket
            raise Exception('Unable to websocket')
        websocket_class = getattr(self.server.async['websocket'],
                                  self.server.async['websocket_class'])

        # Now handle the websocket
        ws = websocket_class(self._websocket_handler)
        return ws(environ, start_response)

    def do_websocket_handshake(self, environ, start_response):
        """Perform the websocket handshake."""
        if 'HTTP_SEC_WEBSOCKET_PROTOCOL' in environ:
            protocols = environ['HTTP_SEC_WEBSOCKET_PROTOCOL'].split(',')
        else:
            protocols = ['binary']
        version = environ['HTTP_SEC_WEBSOCKET_VERSION']

        if version:
            # HyBi/IETF version of the protocol

            # HyBi-07 report version 7
            # HyBi-08 - HyBi-12 report version 8
            # HyBi-13 reports version 13
            if version in ['7', '8', '13']:
                self.version = "hybi-%02d" % int(version)
            else:
                return False

            key = environ['HTTP_SEC_WEBSOCKET_KEY']

            # Choose binary if client supports it
            if 'binary' in protocols:
                self.base64 = False
            elif 'base64' in protocols:
                self.base64 = True
            else:
                raise Exception('TODO')

            # Generate the hash value for the accept header
            accept = b64encode(sha1(key + self.GUID).digest())

            # Generate the upgrade packet for websocket
            status = '101 Switching Protocols'
            headers = [
                ("Upgrade", "websocket"),
                ("Connection", "Upgrade"),
                ("Sec-WebSocket-Accept", accept)]

            if self.base64:
                headers.append(("Sec-WebSocket-Protocol", "base64"))
            else:
                headers.append(("Sec-WebSocket-Protocol", "binary"))

            if self.server.cookie:
                cookie = self.server.cookie + '=' + self.sid
                headers.append(("Set-Cookie", cookie))

            cors_headers = self.server._cors_headers(environ)
            start_response(status, headers + cors_headers)

            self.connected = True
            return True

        else:
            return False

    def close(self, wait=True, abort=False):
        """Close the socket connection."""
        if self.proxy_socket:
            self.proxy_socket.shutdown(_socket.SHUT_RDWR)
            self.proxy_socket.close()
        self.closed = True

    def make_websocket(self, environ, start_response):
        """Todo correcly."""
        if self.server.async['websocket'] is None or \
                self.server.async['websocket_class'] is None:
                # the selected async mode does not support websocket
                return self.server._bad_request()
        websocket_class = getattr(self.server.async['websocket'],
                                  self.server.async['websocket_class'])
        ws = websocket_class(self._websocket_handler)
        return ws(environ, start_response)

    def _websocket_handler(self, ws):
        """Create the handler for websocket transport."""
        cqueue = []
        c_pend = 0
        tqueue = []
        rlist = [ws.socket, self.proxy_socket]

        while True:
            wlist = []

            if tqueue:
                wlist.append(self.proxy_socket)

            if cqueue or c_pend:
                wlist.append(ws.socket)

            try:
                ins, outs, excepts = select.select(rlist, wlist, [], 1)
            except (select.error, OSError):
                exc = sys.exc_info()[1]
                if hasattr(exc, 'errno'):
                    err = exc.errno
                else:
                    err = exc[0]

                if err != errno.EINTR:
                    raise
                else:
                    continue

            if excepts:
                logger.warning("Socket exception")
                break

            if ws.socket in outs:
                # Send vnc packet to the websocket
                for pkt in cqueue:
                    ws.send(pkt)
                cqueue = []

            if ws.socket in ins:
                # Receive websocket packet
                # Queue them for vnc
                try:
                    p = ws.wait()
                except:
                    logger.warning('websocket: wait exception')
                    break
                if p is None:
                    # connection closed by client
                    break
                tqueue.extend(p)

            if self.proxy_socket in outs:
                # Send queued websocket packet to vnc
                dat = tqueue.pop(0)
                sent = self.proxy_socket.send(dat)

                if sent == len(dat):
                    pass
                else:
                    # requeue the remaining data
                    tqueue.insert(0, dat[sent:])

            if self.proxy_socket in ins:
                # Receive vnc packet
                # Queue them for websocket
                buf = self.proxy_socket.recv(self.buffer_size)
                if len(buf) == 0:
                    logger.warning('Target closed connection')
                    break

                cqueue.append(buf)

        self.close(wait=True, abort=True)

        return []
