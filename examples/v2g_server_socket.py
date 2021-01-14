import socket
from v2g_client import Client

if __name__ == "__main__":

    # example: broken in a real network
    # se1 listens
    # create socket from mim to se1
    # ev1 connects to se1 (passing through mim): mim should wait for ev1
    # ev1 -> mim -> se1
    # se1 -> mim -> ev1

    # se1 ipv6
    addrinfo = socket.getaddrinfo('fe80::61:94ff:fe32:a53a%s' % ('%mim-eth0'), 20, socket.AF_INET6, socket.SOCK_STREAM)
    (family, socktype, proto, canonname, sockaddr) = addrinfo[0]
    se1 = Client(addrinfo)
    connected = False
    while not connected:
        try:
            se1.connect() # connect mim to se1
            connected = True
        except:
            pass

    with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as s:  
        port = 202
        print('listening on port %d' % port)
        s.bind(('',port))
        s.listen(2)
        conn, addr = s.accept()
        with conn:
            print(addr, "has connected")
            while True:    
                recv = conn.recv(1024)
                se1.send(recv)
                resp = se1.get_response()
    