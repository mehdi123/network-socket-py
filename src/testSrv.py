import socket
HOST = ''                 # Symbolic name meaning the local host
PORT = 50007              # Arbitrary non-privileged port
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
##raw_input()
while 1:
    s.setblocking(0)
    
    while s.listen(1):
        pass
    conn, addr = s.accept()
    print 'Connected by', addr
    while 1:
        data = conn.recv(1024)
        if not data: break
        conn.send(data)
    conn.close()
##    s.close()
##    s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
##    s.bind((HOST, PORT))
