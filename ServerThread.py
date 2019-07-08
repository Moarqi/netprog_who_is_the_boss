import socket
import os
from time import get_clock_info
import arrow as arr
from threading import Thread, Event
from select import select
import errno
import psutil
import subprocess


class ServerThread(Thread):
    """class for an independent serverthread which listens on the given port
    and accepts connections on every configured port"""
    def __init__(
        self,
        server_socket,
        port,
        score,
        ips = ['localhost'],
        port_range = range(1000, 2000)
    ):
        """
        Extends Thread. closes all sockets when calling join()

        Keyword arguments:
        server_socket -- server socket to accept connections
        port -- port the socket does listen on
        score -- initial score
        ips -- ips of all possible servers (default = ['localhost'])
        port_range -- port range for every server (default = range(1000, 2000)
        """
        self.port = port
        self.ips = ips
        self.port_range = port_range
        self.score = score
        self.base_score = score
        self.time_started = arr.now().timestamp

        self.server_socket = server_socket
        self.inputs = [self.server_socket]
        self.outputs = []
        self.running_servers = {}

        self.do_stop = Event()

        self.update_required = False
        self.master_script_running = False
        self.slave_script_running = False

        Thread.__init__(self)

    # overwrite join to set the event
    def join(self, timeout=None):
        self.do_stop.set()
        self.kill_all_child_processes()

        print("waiting for listener to stop..\n")
        Thread.join(self, timeout)


    def kill_all_child_processes(self):
        """
        kills all child processes of the current process.
        """
        children = psutil.Process().children(recursive=True)
        for child in children:  # this does assume, that the child we have is the correct one to terminate :)
            child.terminate()
            child.kill()


    def notify_running_servers(self):
        """
        notify all server in ip/port range. effectively scans the port range for
        every ip in the self.ips list
        """
        for ip in self.ips: # catch network unreachable
            for port in self.port_range:
                # WARNING:
                # this approach is actually not that nice. it could lead to an inf-loop if we would use the
                # network ip address of THIS computer. this is ignored for the size of the project.
                if port == self.port and (ip == 'localhost' or ip == '127.0.0.1'):
                    continue
                try:
                    _socket = socket.create_connection((ip, port))
                    _socket.setblocking(0)
                    _socket.send(bytes(f'[INFO] {self.port} {self.score}\n', 'utf-8'))
                    print(f'notify sent to {port}')
                    self.inputs.append(_socket)

                except socket.error as e:
                    if e.errno != errno.ECONNREFUSED:
                        if e.errno == errno.ENETUNREACH:
                            self.ips.remove(ip)
                            break
                        else:
                            raise


    def process_recieved_data(self, data, ip):
        """processes the recieved data and updates the running_servers dict."""
        info, port, score = data.split(' ')

        self.update_required = not port in (
            server.keys() for server in self.running_servers.values()
        ) if not self.update_required else True

        try:
            self.running_servers[ip][port] = {
                "score": float(score),
                "updated": True
            }
        except KeyError:
            self.running_servers[ip] = {
                f"{port}": {
                    "score": float(score),
                    "updated": True
                }
            }


    def handle_server_list(self):
        """
        checks if any change for master/slave is needed.
        when all scores in self.running_server are up to date, it compares the max score
        of the other servers with the current score.
        starts the appropriate script
        when the status changed.
        """
        if len(self.running_servers.keys()) and self.update_required and all(
            [
                server['updated']
                for server_for_ip in self.running_servers.values()
                for server in server_for_ip.values()
            ]
        ):
            self.update_required = False
            max_score = max([server['score'] for server_for_ip in self.running_servers.values() for server in server_for_ip.values()])
            self.score = self.base_score + (arr.now().timestamp - self.time_started)

            if self.score > max_score:
                if not self.master_script_running:
                    if self.slave_script_running:
                        self.slave_script_running = False
                        self.kill_all_child_processes()

                    self.master_script_running = True

                    subprocess.Popen(['./master.sh'])

            else:
                # TODO: i bet this is the most complicate way to do it but my brain just turned off.. needs rework
                server_list = [
                    (
                        max(
                            server_for_ip_value,
                            key=lambda s: server_for_ip_value[s]['score']
                        ),
                        server_for_ip_key,
                        server_for_ip_value[
                            max(
                                server_for_ip_value,
                                key=lambda s: server_for_ip_value[s]['score']
                            )
                        ]['score']
                    )
                    for server_for_ip_key, server_for_ip_value in self.running_servers.items()
                ]

                print(server_list)

                max_port, max_ip, _ = sorted(
                    server_list,
                    key=lambda x: x[2], reverse=True
                )[0]

                if not self.slave_script_running:
                    if self.master_script_running:
                        self.master_script_running = False
                        self.kill_all_child_processes()

                    self.slave_script_running = True

                    subprocess.Popen(['./slave.sh', f"{max_ip}:{max_port}"])
                else:
                    print(f"I KNOW THAT MY MASTER IS {max_ip}:{max_port} BUT MY SCRIPT IS RUNNING:)")



    def run(self):
        """
        main server method. handles all in/out sockets and calls functions to
        process data and determine master.
        """
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

                    for servers_for_ip in self.running_servers.values():
                        for server in servers_for_ip.values():
                            server['updated'] = False

                    if receive_socket not in self.outputs:
                        self.outputs.append(receive_socket)

                else:
                    recievedbytes = _socket.recv(1024)

                    if recievedbytes:
                        recieved_data = recievedbytes.decode('utf-8')
                        print(recieved_data)
                        remote_ip, _ = _socket.getpeername()

                        if '[INFO]' in recieved_data:
                            self.process_recieved_data(recieved_data, remote_ip)
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
                        self.update_required = True
                        self.outputs.extend(respond_to)

                        _socket.close()

            for _socket in writable_sockets:
                if _socket is not self.server_socket and _socket in respond_to:
                    self.score = self.base_score + (arr.now().timestamp - self.time_started)
                    _socket.send(bytes(f'[INFO] {self.port} {self.score}\n', 'utf-8'))
                    self.outputs.remove(_socket)

            for _socket in error_sockets:
                print('closing bc of error')
                self.inputs.remove(_socket)

                if _socket in self.outputs:
                    self.outputs.remove(_socket)

                _socket.close()

            self.handle_server_list()

        ### SHUTDOWN ###
        for _socket in self.inputs:
            _socket.close()

        for _socket in self.outputs:
            _socket.close()

        for _socket in respond_to:
            _socket.close()