import socketserver
import socket
import threading
from time import sleep
from v2g_client import *
import sys, getopt

class EchoRequestHandler(socketserver.BaseRequestHandler):
    '''
    TCP server, which acts as a man in the middle
    It waits for a message from source and sends it to the target
    It waits for a message from target and sends it to the source
    It needs to know the ip and port of target and source
    '''

    # def __init__(self, request, client_address, server, source, target):
    #     super().__init__(request, client_address, server)

    def setup(self):
        self.target = self.server.target
        self.source = self.server.source
        # self.target_client = Client(self.target, 20000) # tcp stream to send/receive to target
        # self.source_client = Client(self.source, 20000) # tcp stream to send/receive to source
        
    # 1 and 3 have to be known/detected by mim
    # example: source:1 -> mim:20000 -> target:3
    # example: target:3 -> mim:20000 -> source:1
    def handle(self):
        client_ip, client_port = self.client_address
        # dynamically assign ports based on incoming messages from v2g
        # does not work
        # if not hasattr(self, 'source_port') and client_ip == self.source:
        #     self.source_port = client_port
        # elif not hasattr(self, 'target_port') and client_ip == self.target:
        #     self.target_port = client_port

        print("t", self.target, "s", self.source)
        print('Client connected', self.client_address)
        data = self.request.recv(1024) # self.request is a socket
        print("Data from %s:%s : %s" % (client_ip, client_port, data))

        # if messsage from source, send data to target
        # wait for response to send back to source
        if client_ip == self.source:
            server_out_port = 10001 # has to be changed by switch to target port
            self.target_client = Client(self.target, client_port, server_out_port) # tcp stream to send/receive to target
            self.target_client.send(data) # TODO: alter data before sending
            target_response = self.target_client.get_response()
            # target_response = b'test'
            self.request.send(target_response) # send to the source the target response
        elif client_ip == self.target:
            server_out_port = 10002 # has to be changed by switch to source port
            self.source_client = Client(self.source, client_port, server_out_port) # tcp stream to send/receive to source
            self.source_client.send(data)
            source_response = self.source_client.get_response()
            self.request.send(source_response)

        return

    # def finish():
    #     pass

class TCPRequestHandler(socketserver.TCPServer):
    def __init__(self, server_address, RequestHandlerClass, source, target):
        self.source = source
        self.target = target
        socketserver.TCPServer.__init__(self, server_address, RequestHandlerClass)

def parse_args(argv):
    source = None
    target = None
    try:
        opts, args = getopt.getopt(argv,"hs:t:",["source=","target="])
    except getopt.GetoptError:
        print('test.py -s <source> -t <target>')
        sys.exit(2)
        
    for opt, arg in opts:
        if opt == '-h':
            print('v2g_server.py -s <source> -t <target>')
            sys.exit()
        elif opt in ("-s", "--source"):
            source = arg
        elif opt in ("-t", "--target"):
            target = arg
    print("%s %s" % (source, target))
    return source, target

if __name__ == '__main__':

    source = None
    target = None
    source, target = parse_args(sys.argv[1:])

    server_in_port = 20000 # fixed incoming messages for server

    address = ('0.0.0.0', server_in_port)
    print("Listening on port %i" % server_in_port)
    custom_server = TCPRequestHandler(address, EchoRequestHandler, source, target)
    custom_server.handle_request()
    # server = socketserver.TCPServer(address, EchoRequestHandler)
    # server.target = target
    # server.source = source
    # ip, port = server.server_address # find out what port we were given

    # t = threading.Thread(target=server.serve_forever)
    # t.setDaemon(True) # don't hang on exit
    # t.start()

    # # client sends
    # sleep(20)

    # server.socket.close()