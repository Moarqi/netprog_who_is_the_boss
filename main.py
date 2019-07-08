import socket
import errno
import signal
import sys
import os
import time
from ServerThread import ServerThread

listen_socket = None
listen_thread = None
server_sockets = []
port = 1000

def find_listen_port():
    """
    find free port for server socket starting at 1000.
    adding 2 each iteration.
    """
    connected = False
    global port

    while not connected:
        try:
            global listen_socket
            listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
            listen_socket.bind(('localhost', port))
            listen_socket.listen(socket.SOMAXCONN)
            connected = True
            print(f"listening on port: {port}")
        except socket.error as e:
            if e.errno != errno.EADDRINUSE:
                raise
            else:
                port += 2


def signal_handler(signal, frame):
    """
    INTERRUPT HANDLER
    """
    global listen_socket
    global listen_thread
    global server_sockets
    if listen_thread:
        listen_thread.join()
    if listen_socket:
        listen_socket.close()
    for s in server_sockets:
        print(s)
        s.close()
    sys.exit(0)

def exit_setup():
    signal.signal(signal.SIGINT, signal_handler)

score = int(sys.argv[1]) if len(sys.argv) > 1 else 100
ips = ['localhost'] if len(sys.argv) < 3 else [arg for arg in sys.argv[2:]]

exit_setup()
find_listen_port()
listen_thread = ServerThread(listen_socket, port, score, ips)
listen_thread.start()

while True:
    time.sleep(60*24) # this prevents high cpu load
