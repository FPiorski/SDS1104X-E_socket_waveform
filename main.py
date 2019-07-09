#!/usr/bin/python
#-*- coding:utf-8 –*-

# FPiorski 2019 - based on both python examples from https://www.siglenteu.com/wp-content/uploads/dlm_uploads/2017/10/ProgrammingGuide_PG01-E02B.pdf
# Keep in mind that I don't know Python at all, so blame Siglent for all of the more 'conceptual' Python mistakes

import socket
import sys
import time
import pylab as pl

remote_ip = "192.168.0.150"  # change it to match you scope's IP
port = 5025                  # this scope is running two simmilar interfaces on ports 5024 and 5025, the former is for human use, the latter for scripts and such

def SocketConnect():
    try:
        # create a TCP socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        print('Failed to create socket')
        sys.exit();
    try:
        # connect to the oscilloscope
        s.connect((remote_ip , port))
    except socket.error:
        print('Failed to connect to ip ' + remote_ip)
    return s

# SocketQuery() is used when a response is expected, otherwise SocketWrite() is used 

def SocketQuery(Sock, cmd):
    try : # to send the command
        Sock.sendall(cmd)
        time.sleep(0.1)
    except socket.error:
        print('Failed to send the command ' + cmd)
        sys.exit()
    reply = Sock.recv(4096)
    return reply

def SocketWrite(Sock, cmd):
    try : # to send the command
        Sock.sendall(cmd)
        time.sleep(0.1)
    except socket.error:
        print('Failed to send the command ' + cmd)
        sys.exit()

def SocketClose(Sock):
    Sock.close()
    time.sleep(0.3)

def main():
    global remote_ip
    global port
    global count

    s = SocketConnect()

    idn = SocketQuery(s, '*IDN?\n')
    print(idn) 
    
    #wfsu = SocketQuery(s, 'wfsu?\n')
    #print(str(wfsu))

    SocketWrite(s, 'chdr off\n')

    #chdr = SocketQuery(s, 'chdr?\n')
    #print(str(chdr))
    
    vdiv = SocketQuery(s, 'c1:vdiv?\n')
    #print(str(vdiv)) 
    ofst = SocketQuery(s, 'c1:ofst?\n')
    #print(str(ofst)) 
    tdiv = SocketQuery(s, 'tdiv?\n')
    #print(str(tdiv)) 
    sara = SocketQuery(s, 'sara?\n')
    #print(str(sara)) 
    
    sara = float(sara)
    #print(sara)

    # here's where all the magic happens

    # as far as I can tell, data2 block is constructed as follows:
    # <16 bytes of header>
    #   - <7 byte string> "DAT2,#9"
    #   - <9 byte number> length of the waveform data that follows
    # <block of waveform data of length defined in the header>
    #   samples are one byte each, as this oscilloscope has an 8-bit ADC
    # <2 bytes with values of 0x0A (signifying the end of frame)>

    # get channel two waveform data
    s.sendall('c1:wf? dat2\n')
    time.sleep(0.1)
    header = s.recv(16)
    datalen = int(header[7:])

    # because we are dealing with TCP we cannot just recv all the data at once (trust me, I've tried, for my particular setup the most I could get was ~130kpoints at once)
    # so this code reads the response in chunks until the expected length is read

    data = b''
    while 1:
        part = s.recv(4096)
        data += part
        if len(data) >= datalen+2:
            break
    
    data = map(lambda x:ord(x), data) # change chars to their ascii codes
    data = list(data)
    data.pop()
    data.pop()

    # now this part of code is lifted straight from the siglent pdf I linked up at the top of this file
    # well, almost, as I fixed it in one place
    # scratch  that ^, now I think it was broken in two places

    volt_value = []
    for t in data:
        if t > 127:
# here, assuming the transmited data is expressed in two's complement, one shoud
# subtract 256, not 255
            t = t - 256 #255
        else:
            pass
        volt_value.append(t)
    time_value = []
    for idx in range(0,len(volt_value)):
#                         \/ they forgot to convert it to float here
        volt_value[idx] = float(volt_value[idx])/25*float(vdiv)-float(ofst)
        time_data = -(float(tdiv)*14/2)+idx*(1/sara)
        time_value.append(time_data)

    pl.figure(figsize=(7,5))
    pl.ticklabel_format(style='sci', axis='x', scilimits=(0,0))
    pl.plot(time_value, volt_value, markersize=2, label=u"Y1(T)")
    pl.legend()
    pl.grid()
    pl.show()

    SocketClose(s)

if __name__=='__main__':
    main()
