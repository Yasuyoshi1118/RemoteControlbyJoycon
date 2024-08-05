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

# layout = [
#     [sg.Text("port No"),sg.InputText("9000",key="port")],
#     [sg.Button("ポート更新",key='change',size=(15,2),button_color = ('#ffffff','#000000'))],
#     [sg.Text("Send DATA"),sg.InputText("00000000",key="message")],#ba52130000000000663600000031000000000000000000000000000000000000
#     #[sg.Text("Send DATA"),sg.InputText("ba5213000#000000663600000031000000000000000000000000000000000000",key="message")],#ba52130000000000663600000031000000000000000000000000000000000000
#     [sg.Button("メッセージ更新",key='out',size=(15,2),button_color = ('#ffffff','#000000'))],
#     [sg.Button("一時停止",key='stop',size=(15,2),button_color = ('#ffffff','#000000'))]
# ]
#
# window = sg.Window("CANデバイスへメッセージ送信",layout)


# ------------ 遠隔運転ウィンドウ作成 ------------
layout = [[sg.Text(' ')],
        [sg.Text('要求加速度'), sg.MLine(key='-ML_acc-'+sg.WRITE_ONLY_KEY, size=(10,1)),sg.Text('要求舵角'), sg.MLine(key='-ML_ang-'+sg.WRITE_ONLY_KEY, size=(10,1))],
        [sg.Text(' ')],
        [sg.Text('                  '),sg.B(" ← ", font=('Arial',15)),sg.B(' ↑ ', font=('Arial',15)),sg.B(' → ', font=('Arial',15))],
        [sg.Text('     '),sg.B(" P ", font=('Arial',17)),sg.B(" R ", font=('Arial',17)),sg.B(' ↓ ', font=('Arial',15)),sg.B('緊急停止', font=('Arial',15))],
        [sg.Text(' ')],
        [sg.Text("port No"),sg.InputText("9000",key="port")],
        [sg.Button("ポート更新",key='change',size=(15,2),button_color = ('#ffffff','#000000'))],
        [sg.Text("Send DATA"),sg.InputText("00000000",key="message")],#ba52130000000000663600000031000000000000000000000000000000000000
        #[sg.Text("Send DATA"),sg.InputText("ba5213000#000000663600000031000000000000000000000000000000000000",key="message")],#ba52130000000000663600000031000000000000000000000000000000000000
        [sg.Button("メッセージ更新",key='out',size=(15,2),button_color = ('#ffffff','#000000'))],
        [sg.Button("一時停止",key='stop',size=(15,2),button_color = ('#ffffff','#000000'))]
        ]
window = sg.Window("CANデバイスへメッセージ送信",layout)

tgt_acc = 0
tgt_str = 0

adjust_acc = 0.2
adjust_str = 1

nogoflg = 0


while True:
    event,values = window.read(10)
    if event == sg.WIN_CLOSED or event == "Exit":
        break

    elif event =="out":
        b = values["message"]
        send_message = values["message"]
    elif event =="stop":
        send_message = "00000000"
        tgt_acc = 0
        tgt_str = 0
    elif event =="change":
        Socket1.close()
        port = values["port"]
        port = int(port)

    elif event == ' ↑ ':
        tgt_acc = tgt_acc + (1 * adjust_acc)

    elif event == ' ↓ ':
        tgt_acc = tgt_acc - (1 * adjust_acc)

    elif event == ' ← ':
        tgt_str = tgt_str + (1 * adjust_str)

    elif event == ' → ':
        tgt_str = tgt_str - (1 * adjust_str)
    
    elif event == ' P ':
        tgt_str = 0
        tgt_acc = 0
        send_message = "p"
        nogoflg = 1

    if nogoflg == 0:

        if tgt_acc >= 0:
            tgt_acc_adj = (tgt_acc * 1000)
        elif tgt_acc < 0:
            tgt_acc_adj = (-tgt_acc * 1000)+(2**15)
        tgt_acc_hex = format(int(tgt_acc_adj), '04X')
        send_data1 = int(tgt_acc_hex[0:2],16)
        print("send_data1 : ",send_data1)
        send_data2 = int(tgt_acc_hex[2:4],16)

        if tgt_str >= 0:
            tgt_str_adj = (tgt_str * 1000 * 3.14 / 180)
        elif tgt_str < 0:
            tgt_str_adj = (tgt_str * 1000 * 3.14 / 180 ) + ( 2**16 )
        tgt_str_hex = format(int(tgt_str_adj), '04X')
        send_data3 = int(tgt_str_hex[0:2],16)
        send_data4 = int(tgt_str_hex[2:4],16)

        print("send_data1 : ",send_data1)
        #send_message = str(send_data1) + str(send_data2) + str(send_data3) + str(send_data4)
        send_message = tgt_acc_hex + tgt_str_hex
    print(send_message + "  port:" + str(port))
    window['-ML_acc-'+sg.WRITE_ONLY_KEY].update(tgt_acc)
    window['-ML_ang-'+sg.WRITE_ONLY_KEY].update(tgt_str)

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
