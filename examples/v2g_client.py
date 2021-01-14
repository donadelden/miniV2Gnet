import socket
from time import sleep

class Client:
    '''
    TCP Client which can send a messsage and get the response if available.
    '''
    def __init__(self, addrinfo, name = "client"):
        # Connect to the server
        self.name = name
        (family, socktype, proto, canonname, sockaddr) = addrinfo[0]
        self.sockaddr = sockaddr
        self.s = socket.socket(family, socktype, proto)
        # self.s.bind(('', src_port))
        
    def connect(self):
        self.s.connect(self.sockaddr)
        print('Connected to', self.sockaddr)

    def send(self, message=b'Hello, world'):
        # Send the data and wait for response
        print('%s -> %s : %s' % (self.name, self.sockaddr[0], message))
        len_sent = self.s.send(message)

    def get_response(self):
        # Receive a response
        response = self.s.recv(1024)
        print('%s <- %s : %s' % (self.name, self.sockaddr[0], response))
        return response

    def __exit__(self):
        # Clean up
        self.s.close()


if __name__ == "__main__":
    # ev1 ipv6
    addrinfo = socket.getaddrinfo('fe80::543f:85ff:fe63:91a7%s' % ('%se1-eth0'), 20000, socket.AF_INET6, socket.SOCK_STREAM)
    client = Client(addrinfo)
    client.send()
    print(client.get_response())