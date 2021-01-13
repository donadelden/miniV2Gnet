import socket
# import threading

# def receive_thread():
#     receive_thread = threading.Thread(target=netcat, name="Receive")
#     receive_thread.start()

def netcat(hostname='0.0.0.0', port=20002):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((hostname, port))
    print('binding to %s:%s' % (hostname, port))

    print('waiting for connection')
    s.listen(2)
    while True:
        conn, addr = s.accept() # waits for connection

        print('waiting for reception')
        data = conn.recv(1024)
        print(data)
        if not data:
            break
    conn.close()
    s.close()

if __name__ == "__main__":
    netcat()