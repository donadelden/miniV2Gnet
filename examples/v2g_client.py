import socket

class Client:
    '''
    TCP Client which can send a messsage and get the response if available.
    '''
    def __init__(self, hostname, src_port, port):
        # Connect to the server
        self.hostname = hostname
        self.port = port
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind(('', src_port)) # in_port
        self.s.connect((hostname, port)) # out_port

    def send(self, message=b'Hello, world'):
        # Send the data and wait for response
        print('Sending to %s:%s : "%s"' % (self.hostname, self.port, message))
        len_sent = self.s.send(message)

    def get_response(self):
        # Receive a response
        response = self.s.recv(1024)
        print('Received: from %s:%s : "%s"' % (self.hostname, self.port, response))
        return response

    def __exit__(self):
        # Clean up
        self.s.close()


if __name__ == "__main__":
    client = Client('10.0.0.2', 20002, 20000)
    client.send()
    print(client.get_response())