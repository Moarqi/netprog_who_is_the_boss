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
                _socket.setblocking(0)
                _socket.send(bytes(f'[INFO] {self.port} {self.score}\n', 'utf-8'))
                print(f'notify sent to {port}')
                self.inputs.append(_socket) # this line is critical!
            except socket.error as e:
                if e.errno != errno.ECONNREFUSED:
                    raise


    def process_recieved_data(self, data):
        self.score += get_clock_info('process_time').resolution
        info, port, score = data.split(' ')
        self.running_servers[port] = score
        max_score = float(max([server for server in self.running_servers.values()]))
        print(self.score, max_score)
        if self.score > max_score:
            print('I am the boss :)')
        else:
            max_port = max(
                self.running_servers,
                key=lambda s: self.running_servers[s]
            )
            print(f"{max_port} is the boss :(")
        print(self.running_servers)


    def run(self):
        self.notify_running_servers()
        respond_to = []

        while not self.do_stop.isSet():
            readable_sockets, writable_sockets, error_sockets = (
                select(self.inputs, self.outputs, self.inputs, 1)
            )

            for _socket in readable_sockets:
                # the server itself is the one that can accept new connections
                if _socket is self.server_socket:
                    print('accepting')
                    receive_socket, addr = _socket.accept()
                    receive_socket.setblocking(0)
                    self.inputs.append(receive_socket)
                    self.outputs.extend(respond_to)

                    if receive_socket not in self.outputs:
                        self.outputs.append(receive_socket)

                else:
                    recievedbytes = _socket.recv(1024)

                    if recievedbytes:
                        recieved_data = recievedbytes.decode('utf-8')
                        print(recieved_data)
                        # problem is, every time the other server sends an info, this server
                        # responds with an info -> inf loop!
                        if '[INFO]' in recieved_data:
                            self.process_recieved_data(recieved_data)
                        if _socket not in respond_to:
                            respond_to.append(_socket)

                    else:
                        self.inputs.remove(_socket)
                        print('closing')

                        if _socket in self.outputs:
                            self.outputs.remove(_socket)
                        if _socket in respond_to:
                            respond_to.remove(_socket)

                        self.running_servers.clear()
                        self.outputs.extend(respond_to)

                        _socket.close()

            for _socket in writable_sockets:
                if _socket is not self.server_socket and _socket in respond_to:
                    self.score += get_clock_info('process_time').resolution
                    _socket.send(bytes(f'[INFO] {self.port} {self.score}\n', 'utf-8'))
                    # respond_to.remove(_socket)
                    self.outputs.remove(_socket)

            for _socket in error_sockets:
                print('closing bc of error')
                self.inputs.remove(_socket)

                if _socket in self.outputs:
                    self.outputs.remove(_socket)

                _socket.close()

        ### SHUTDOWN ###
        for _socket in self.inputs:
            _socket.close()

        for _socket in self.outputs:
            _socket.close()

        for _socket in respond_to:
            _socket.close()




