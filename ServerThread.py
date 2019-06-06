import socket
from time import get_clock_info
from threading import Thread, Event
from select import select
import errno

class ServerThread(Thread):
    def __init__(self, server_socket, port, score):
        self.server_socket = server_socket
        self.port = port
        self.inputs = [self.server_socket]
        self.outputs = []
        self.do_stop = Event()
        self.score = score
        self.running_servers = {}
        self.waiting = []
        Thread.__init__(self)

    # overwrite join to set the event
    def join(self, timeout=None):
        self.do_stop.set()
        print("waiting for listener to stop..\n")
        Thread.join(self, timeout)


    def notify_running_servers(self):
        for port in range(1000, 2000):
            if port == self.port:
                continue
            try:
                _socket = socket.create_connection(('localhost', port))
                _socket.send(bytes(f'[INFO] {self.port} {self.score}\n', 'utf-8'))
                print(f'notify sent to {port}')
                self.inputs.append(_socket) # this line is critical!
            except socket.error as e:
                if e.errno != errno.ECONNREFUSED:
                    raise


    def process_recieved_data(self, data):
        info, port, score = data.split(' ')
        self.running_servers[port] = score
        print(self.running_servers)


    def run(self):
        self.notify_running_servers()
        while not self.do_stop.isSet():
            readable_sockets, writable_sockets, error_sockets = (
                select(self.inputs, self.outputs, self.waiting, 0.5)
            )
            for _socket in readable_sockets:
                # the server itself is the one that can accept new connections
                if _socket is self.server_socket:
                    print('accepting')
                    receive_socket, addr = _socket.accept()
                    receive_socket.setblocking(0)
                    self.inputs.append(receive_socket)

                else:
                    recievedbytes = _socket.recv(1024)
                    if recievedbytes:
                        recieved_data = recievedbytes.decode('utf-8')
                        print(recieved_data)
                        if '[INFO]' in recieved_data:
                            self.process_recieved_data(recieved_data)
                        if _socket not in self.outputs:
                            self.outputs.append(_socket)
                    else:
                        self.inputs.remove(_socket)
                        print('closing')
                        if _socket in self.outputs:
                            self.outputs.remove(_socket)
                        _socket.close()

            for _socket in writable_sockets:
                self.score += get_clock_info('process_time').resolution
                _socket.send(bytes(f'[INFO] {self.port} {self.score}\n', 'utf-8'))
                self.outputs.remove(_socket)
                self.inputs.remove(_socket)
                self.waiting.append(_socket)

            for _socket in error_sockets:
                print('closing')
                self.inputs.remove(_socket)
                if _socket in self.outputs:
                    self.outputs.remove(_socket)
                _socket.close()




