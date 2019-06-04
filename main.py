from socket import socket, SOMAXCONN
import signal
import sys
import time
import threading

s = None

def find_listen_port():
    connected = False
    port = 1000

    while not connected:
        try:
            global s
            s = socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
            s.bind(('localhost', 1000))
            s.listen(SOMAXCONN)
            connected = True
            print(f"listening on port: {port}")
        except BaseException as e:
            print(e)
            port += 2

def signal_handler(signal, frame):
    global s
    if s:
        s.close()
    sys.exit(0)

def exit_setup():
    signal.signal(signal.SIGINT, signal_handler)

exit_setup()
find_listen_port()

while True:
    pass
