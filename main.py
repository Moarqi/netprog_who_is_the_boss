import socket
import errno
import signal
import sys
import os
import time
import threading

listen_socket = None
listen_thread = None

def find_listen_port():
    connected = False
    port = 1000

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


def notify_running_servers():
    for port in range(1000, 2000):
        try:
            server_socket = socket.create_connection(('localhost', port))
            server_socket.send(b'[REG_ME]')
            print(f'notify sent to {port}')
        except socket.error as e:
            if e.errno != errno.ECONNREFUSED:
                raise
            else:
                continue
        finally:
            if server_socket:
                server_socket.close()


def listener():
    while True:
        receive_socket, addr = listen_socket.accept() # this should wait for a connection
        print(addr)
        recievedbytes = receive_socket.recv(10)
        print(receive_socket.getpeername())
        if (len(recievedbytes) == 0):
            continue
        print(recievedbytes.decode('utf-8'),end='\n')



def signal_handler(signal, frame):
    global listen_socket
    global listen_thread
    if listen_socket:
        listen_socket.close()
    if listen_thread:
        listen_thread.join()
    sys.exit(0)

def exit_setup():
    signal.signal(signal.SIGINT, signal_handler)

exit_setup()
find_listen_port()
notify_running_servers()
listen_thread = threading.Thread(target=listener)
listen_thread.start()

while True:
    time.sleep(60*24)
