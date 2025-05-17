from tcpclass import TCPconnect
import socket
import time
import sys
import os

def ReadConfigFile_func(x):
    i = 0
    y = []
    try:
        with open(x,'r') as ConfigFile:
            while True:
                y.append(ConfigFile.readline().replace('\n',''))
                if len(y[i]) == 0:

                    y[i] = 'End'
                    break

                if y[i] == '':

                    y[i] = 'End'
                    break

                if y[i][0] == ',':

                    y[i] = 'End'
                    break

                i = i + 1

        return y

    except:

        print('Unable to read config file [' + x + ']')
        print('Exit')
        sys.exit()

ConfigFile_list = ReadConfigFile_func('config.csv')
Temp_list = ConfigFile_list[1].split(',')
ip = Temp_list[0]
port = Temp_list[1]
timeout = Temp_list[2]
#print("ip =",ip)
#print("port =",port)

test=TCPconnect(ip=ip,port=port,timeout=timeout)

while True:
    x = input('Input 1→Client or　2→Server and Enter : ')
    if x == "1":
        print("you are Client")
        while True:
            msg_send = test.Client()
            print("send message = ",msg_send)
    elif x == "2":
        print("you are Server")
        while True:
            msg_rec = test.Server()
            print("receive message = ",msg_rec)
    else:
        print("please input('Input 1→Client　2→Server')")
