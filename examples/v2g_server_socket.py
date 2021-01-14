import socket
from v2g_client import Client

if __name__ == "__main__":

    # HOW RiseV2G works
    
    # step 1) get udp messages

    # UDP: ev1       -> se1:15118
    # UDP: se1:15118 -> ev1
    # UDP socket listening to 15118

    se_port = 15118
    with socket.socket(socket.AF_INET6, socket.SOCK_DGRAM) as s:
        # se_port + 1 because otherwise mininet won't allow another person listening on the same port  
        print('listening on port %d' % (se_port + 1))
        s.bind(('',se_port + 1))
        while True:
            data, addr = s.recvfrom(72) # len = 10, 72
            addr_ip = addr[0] # ip of source
            addr_port = addr[0] # UDP port of ev1
            print("%s:%s (len=%d) : %s" % (addr_ip, addr_port, len(data), data))
            # send udp packet to the real destination
            with socket.socket(socket.AF_INET6, socket.SOCK_DGRAM) as s2:
                se_addrinfo = socket.getaddrinfo('fe80::61:94ff:fe32:a53a%s' % ('%mim-eth0'), se_port, socket.AF_INET6, socket.SOCK_DGRAM)
                (family, socktype, proto, canonname, se_sockaddr) = se_addrinfo[0]
                s2.sendto(data, se_sockaddr)

    # TCP messages which can be
    # ev1 -> se1
    # se1 -> ev1

    # se1 ipv6
    # addrinfo = socket.getaddrinfo('fe80::61:94ff:fe32:a53a%s' % ('%mim-eth0'), 20, socket.AF_INET6, socket.SOCK_STREAM)
    # (family, socktype, proto, canonname, sockaddr) = addrinfo[0]
    # se1 = Client(addrinfo)
    # connected = False
    # while not connected:
    #     try:
    #         se1.connect() # connect mim to se1
    #         connected = True
    #     except:
    #         pass

    # with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as s:  
    #     port = 202
    #     print('listening on port %d' % port)
    #     s.bind(('',port))
    #     s.listen(2)
    #     conn, addr = s.accept()
    #     with conn:
    #         print(addr, "has connected")
    #         while True:    
    #             recv = conn.recv(1024)
    #             se1.send(recv)
    #             resp = se1.get_response()
    