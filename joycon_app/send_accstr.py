#from tcpclass import TCPconnect
import socket
import time
import sys
import os
import PySimpleGUI as sg

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
port = int(Temp_list[1])
timeout = Temp_list[2]
send_message = "00000000"

layout = [
    [sg.Text("port No"),sg.InputText("9000",key="port")],
    [sg.Button("ポート更新",key='change',size=(15,2),button_color = ('#ffffff','#000000'))],
    [sg.Text("Send DATA"),sg.InputText("00000000",key="message")],#ba52130000000000663600000031000000000000000000000000000000000000
    #[sg.Text("Send DATA"),sg.InputText("ba5213000#000000663600000031000000000000000000000000000000000000",key="message")],#ba52130000000000663600000031000000000000000000000000000000000000
    [sg.Button("メッセージ更新",key='out',size=(15,2),button_color = ('#ffffff','#000000'))],
    [sg.Button("一時停止",key='stop',size=(15,2),button_color = ('#ffffff','#000000'))]
]

window = sg.Window("CANデバイスへメッセージ送信",layout)


while True:
    event,values = window.read(1000)
    if event =="out":
        b = values["message"]
        send_message = values["message"]
    elif event =="stop":
        send_message = "00000000"
    elif event =="change":
        Socket1.close()
        port = values["port"]
        port = int(port)
    print(send_message + "  port:" + str(port))

    try:
        Socket1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  #// AF_INET=IPv4, SOCK_STREAM=TCP/IP
        Socket1.settimeout(5)
        Socket1.connect((ip,port))
        Socket1.sendall(bytes(send_message,'utf-8'))
        Receive1 = Socket1.recv(1024)
        print('Received from server: ' ,Receive1 )
        Socket1.close()

    except:
        print('Server connection error')
