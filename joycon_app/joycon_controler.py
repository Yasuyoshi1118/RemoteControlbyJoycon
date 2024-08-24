import time
import threading
import sys
import socket
import time
import pygame
from pygame.locals import *

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


def tcp_send():
    print('start_thre1')
    global send_message, end_flg
    ConfigFile_list = ReadConfigFile_func('config.csv')
    Temp_list = ConfigFile_list[1].split(',')
    ip = Temp_list[0]
    port = int(Temp_list[1])
    timeout = int(Temp_list[2])
    while end_flg == 0:
      try:
          Socket1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  #// AF_INET=IPv4, SOCK_STREAM=TCP/IP
          Socket1.settimeout(timeout)
          Socket1.connect((ip,port))
          Socket1.sendall(bytes(send_message,'utf-8'))
          Receive1 = Socket1.recv(1024)
          print('Received from server: ' ,Receive1 )
          Socket1.close()

      except:
          print('Server connection error / send message = ',send_message)

def message_change():
    print('start_thre2')
    global send_message, end_flg
    while True:
      send_message = input('send message を入力 --> ')
      if send_message == "finish":
          end_flg = 1

def joycon_control():
    try:
        joycon()
    except pygame.error:
        print ('joystickが見つかりませんでした。')

def joycon():
    pygame.joystick.init()
    joystick0 = pygame.joystick.Joystick(0)
    joystick0.init()
    print('joystick start')
    pygame.init()
    tgt_accel = 0
    tgt_str = 0
    while True:
         # コントローラーの操作を取得
        time.sleep(0.1)
        eventlist = pygame.event.get()
        # イベント処理
        for e in eventlist:
            if e.type == QUIT:
                return
            if e.type == pygame.locals.JOYBUTTONDOWN:
                print ('button:' + str(e.button))
                if int(e.button)==0:
                    print ('press up')
                    tgt_accel += 1
                    print("tgt_accel = ", tgt_accel)
                elif int(e.button)==3:
                    print ('press down')
                    tgt_accel -= 1
                    print("tgt_accel = ", tgt_accel)
                elif int(e.button)==1:
                    print ('press right')
                    tgt_str -= 1
                    print("tgt_str = ", tgt_str)
                elif int(e.button)==2:
                    print ('press left')
                    tgt_str += 1
                    print("tgt_str = ", tgt_str)
                elif int(e.button)==6:
                    print ('press +  -->  finish')
                    end_flg = 1
                    return

            elif e.type == pygame.locals.JOYAXISMOTION:
                hat_x, hat_y = joystick0.get_axis(0), joystick0.get_axis(1)
                if (abs(hat_x) > 0.3) or (abs(hat_y) > 0.3) :
                    print('hat x:' + str(hat_x) + ' hat y:' + str(hat_y))

if __name__ == '__main__':
    print('start_program')
    send_message = "00000000"
    end_flg = 0
    thread1 = threading.Thread(target=tcp_send)
    # thread2 = threading.Thread(target=message_change)
    thread2 = threading.Thread(target=joycon_control)
    thread1.start()
    thread2.start()
    thread2.join()#thread2が終わったら次に進む
    end_flg = 1
    thread1.join()
    print('end_program')
