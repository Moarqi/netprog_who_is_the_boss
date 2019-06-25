import socket
import os
from time import get_clock_info
import arrow as arr
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
        self.base_score = score
        self.time_started = arr.now().timestamp

        self.running_servers = {}
        self.new_server = False
        self.master_script_running = False
        self.slave_script_running = False
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
                print(_socket.getpeername())
                self.inputs.append(_socket)
            except socket.error as e:
                if e.errno != errno.ECONNREFUSED:
                    raise


    def process_recieved_data(self, data):
        self.score = self.base_score + (arr.now().timestamp - self.time_started)
        info, port, score = data.split(' ')

        self.new_server = not port in self.running_servers.keys()

        self.running_servers[port] = {
            "score": score,
            "updated": True
        }
        # new server, decide what to do

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

                    for server in self.running_servers.values():
                        server['updated'] = False

                    if receive_socket not in self.outputs:
                        self.outputs.append(receive_socket)
                    print(addr)

                else:
                    recievedbytes = _socket.recv(1024)

                    if recievedbytes:
                        recieved_data = recievedbytes.decode('utf-8')
                        print(recieved_data)

                        if '[INFO]' in recieved_data:
                            print(_socket)
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
                    self.score = self.base_score + (arr.now().timestamp - self.time_started)
                    _socket.send(bytes(f'[INFO] {self.port} {self.score}\n', 'utf-8'))
                    # respond_to.remove(_socket)
                    self.outputs.remove(_socket)

            for _socket in error_sockets:
                print('closing bc of error')
                self.inputs.remove(_socket)

                if _socket in self.outputs:
                    self.outputs.remove(_socket)

                _socket.close()

            print([self.running_servers[server] for server in self.running_servers])
            if self.new_server and not any([not server['updated'] for server in self.running_servers.values()]):
                self.new_server = False
                print([server['score'] for server in self.running_servers.values()])
                max_score = float(max([server['score'] for server in self.running_servers.values()]))

                if self.score > max_score:
                    if not self.master_script_running:
                        if self.slave_script_running:
                            pass  # end script here

                        self.master_script_running = True

                    print('I am the boss :)') # start master shell script here

                else:
                    if not self.slave_script_running:
                        if self.master_script_running:
                            pass  # end script here

                        self.slave_script_running = True

                    max_port = max(
                        self.running_servers,
                        key=lambda s: self.running_servers[s]['score']
                    )
                    print(f"{max_port} is the boss :(") # start slave shell script here


        ### SHUTDOWN ###
        for _socket in self.inputs:
            _socket.close()

        for _socket in self.outputs:
            _socket.close()

        for _socket in respond_to:
            _socket.close()




