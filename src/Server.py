import socket
import sys
import random
from threading import *

myport=50001
DATA_SIZE=978
PACKET_SIZE=1024
myip=socket.gethostbyaddr(socket.gethostname())[2][0]
clientip=''
clientport=0
ack_recv=0
ACK_TIMEOUT=5 # second
SEND_TRY=10000  #while 1
END_OF_BUFFER=0
RECV_TIMEOUT=10
PERCENT=0
g_buf=''

def Recieve(conn, size):
    s=0
    global g_buf
    while len(g_buf) < size:
        d = conn.recv(PACKET_SIZE)
        if len(d)==0:
            break
        s+=len(d)
        g_buf += d
    buf = g_buf[:s]
    g_buf=g_buf[s:]
    return buf

def Send(data, conn):
    count=0
    while count<len(data):
        count+=conn.send(data[count:])
    return count

def AdjustIp(s):
    s=s.split('.')
    i=0;n=''
    for tk in s:
        n += (3-len(tk))*'0' + tk + '.'
    n = n[:-1]
    return n

def makePacket(data, seq_num, sender, reciever, last):
    lng=`len(data)` #+PACKET_SIZE-DATA_SIZE`
    lng=(4-len(lng))*'0'+lng
    packet=lng+data
    packet+=`seq_num`
    sip=AdjustIp(sender[0])
    sport = `sender[1]`
    sport = (5-len(sport))*'0'+sport
    rip=AdjustIp(reciever[0])
    rport = `reciever[1]`
    rport = (5-len(rport))*'0'+rport
    packet += sip + sport+rip+rport
    packet += last
    return packet

def extractPacket(data, flag):
    pack=[]
    l=int(data[:4])
    pack.append(`l`)
    data=data[4:]
    pack.append(data[:l])
    data=data[l:]
    pack.append(int(data[0]))
    data=data[1:]
    
    pack.append(data[:15])
    data=data[15:]
    pack.append(int(data[:5]))
    data=data[5:]
    
    pack.append(data[:15])
    data=data[15:]
    pack.append(int(data[:5]))
    data=data[5:]
    pack.append(data[0])
    np=[]
    if flag:
        np = [pack[0], pack[1], pack[2], (pack[5], pack[6]), (pack[3], pack[4]), pack[7]]
    else:
        np = [pack[0], pack[1], pack[2], (pack[3], pack[4]), (pack[5], pack[6]), pack[7]]
    return np

def EndOfBuffer():
    return END_OF_BUFFER

def ReadData(file):
    d=''
    d=file.read(DATA_SIZE)
    last='0'
    if len(d) < DATA_SIZE:
        END_OF_BUFFER=1
        last='1'
    return d, last
    
def SendBuffer(file, socket_obj):
    seq_num = 0
    data=''
    go_on = 1
    global ack_recv
    socket_obj.settimeout(ACK_TIMEOUT)
    while not EndOfBuffer():
        data, last=ReadData(file)
        if len(data)==0:
            break
        pack=makePacket(data, go_on%2, (myip, myport), (clientip, clientport), last)
        go_on+=1
        count = 0
        while count < SEND_TRY:
            ack_recv=0
            Send(pack, socket_obj)
            try:
                AckListener(socket_obj, pack)
            except socket.timeout:
                ack_recv=0
                print 'ack time out'
            count += 1
            if ack_recv:
                break
        else:
            print 'Ack not recieved'
            print 'Exit'
            sys.exit(0)
    socket_obj.close()

def AckListener(conn, pack):
    global ack_recv
    data = Recieve(conn, PACKET_SIZE)
    if not data:
        ack_recv=0
        return
    rpack = extractPacket(data, 1)
    pack = extractPacket(pack, 0)
    if pack == rpack:
##        print 'Ack recieved'
        ack_recv = 1
    else:
        ack_recv = 0

def WaitForAck(sock, pack):
    t=Thread(target=AckListener, args=(sock, pack))
    t.start()
    return t

def Reciever(recv_sock, of):
    all=''
    cnt=0
    prvPacket=[]
    recv_sock.listen(1)
    conn, addr = recv_sock.accept()
    last = '0'
    conn.settimeout(RECV_TIMEOUT)
    while last == '0':
        data = Recieve(conn, PACKET_SIZE)
        if data:
            packet=extractPacket(data, 0)
            spacket=extractPacket(data, 1)
            if random.randint(0,100)>PERCENT:
                SendAck(conn, spacket)
            if packet!=prvPacket:
                print 'got packet', last
                of.write(packet[1])
                cnt+=len(packet[1])
                print cnt
            last = packet[5]
            prvPacket=packet
        else:
            print 'Connection abort'
            break
        if last == '1':
            print 'Last'
    conn.close()



def SendAck(conn, spack):
    data=makePacket(spack[1], spack[2], spack[3], spack[4], spack[5])
    Send(data, conn)
    
if __name__=='__main__':
    snd=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lst=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if sys.argv[1] == 'send':
        buf_file=open(sys.argv[4], 'rb')
        snd.connect((sys.argv[2], int(sys.argv[3])))
        clientip=sys.argv[2]; clientport=int(sys.argv[3])
        print 'Sending file:', sys.argv[4], '...'
        SendBuffer(buf_file, snd)
    else:
        lst.bind(('', myport))
        out_file=open(sys.argv[2],'wb')
        PERCENT=int(sys.argv[3])%100
        Reciever(lst, out_file)
        out_file.close()