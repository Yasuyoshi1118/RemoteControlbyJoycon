import time
import threading
from tcpclass import TCPconnect
import logmake
import can_init
import config
import PySimpleGUI as sg
import sys
import os
import can
import random
import pygame
from pygame.locals import *
import time
import socket
import command_joycon

#[setting variables]##########################
#mode, safety_mode, send_fd_file, send_fd_file, adjust_acc, adjust_blake, adjust_str, adjust_autoblake,control_time,joycon_acc,joycon_str,checkIP,checkPort =config.General_Setting_Read()

mode = "can"
safety_mode = "ON"
send_fd_file = "./fdsend_const.csv"
adjust_acc = 0.2
adjust_blake = 0.05
adjust_str = 10
adjust_accblake = 0.5
control_time = 100
joycon_acc = 1
joycon_str = -1
checkIP = "127.0.0.10"
checkPort = 8002

#[Global variables]##########################
version = "0.0.0.9"
#ver6
#緊急停止時のブレーキが聞かない問題の解消
#ステアリング上限値：マイナスに関しても対応
#Pを受信したらCANメッセージを送信しないようにする
#ver7
#車両速度をTCPで返信する＆ver7で修正（未定義で終了していた）
#TCP通信を毎回socketをcloseしないように変更
#CANFD通信モード追加
#ver8
#IFの整理（モニター上でCloseが途切れる）
#TCPでCommandを送信できるように追加
#ver9
#Rレンジ要求追加（走行OK＝Dレンジ要求＆走行開始フラグON）
#→でDレンジにしない

global_rec_msg = "default"
global_now_msg = "default"#現状の状況メッセージ
send_vehicledata = "Default2"
command_canorcanfd = "default"
command_can_id = 0
command_can_data = [00, 00, 00, 00, 00, 00, 00, 00]
command_send_flg = 0

msg_rec_flg = 0
calculate_flg = 0
end_flg = 0
go_flg = 1
can_msg_flg = 1
canfd_msg_flg = 0
safety_flg = 0
automoving_mode = 0
joycon_flg = 0
emergency_brake = -1

now_vel = 0
now_str = 0
tgt_acc = 0
tgt_str = 0
tgt_shift = 0

event = 0
values = 0

Maxvelocity = 2.0
Maxstearing = 440.0

count_e2e = 0
fd_data = [0,0,0,0,236,0,0,0,6,54,0,0,0,49,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]#e2eは除く data9(6)->shift要求なし 縦ID49
fd_data_def = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]#data9(6)->shift要求なし 縦ID49
crc_test = [0x01,0x00,0xec,0x78,0xff,0xe6,0x66,0x36,0xec,0x78,0x00,0x31,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00]#dde0

#[log filename]#############################
path = os.getcwd()
nowtime = time.ctime()
file_log_name = "log_"+nowtime.replace(" ","_")
file_log_name = path + "/log"+"/_" + file_log_name.replace(":","_")

#################################################################################################

def make_main():
    # ------------ メインウィンドウ作成 ------------
    main_layout = [[sg.B('ダイアグ通信モード')],
            [sg.B('CANFD通信モード')],
            [sg.Text(' ')],
            [sg.B('遠隔運転モード')],
            [sg.B('遠隔運転モード(JoyCon)')],
            [sg.B('遠隔運転モード(外部操作)')],
            [sg.Text(' ')],
            [sg.B('自動運転モード')],
            [sg.Text(' ')],
            [sg.Text('Version : '),sg.Text(version)],
            ]
    return sg.Window("TVECS created by Hatano", main_layout, finalize=True, size=(350, 250))

def make_gk():
    # ------------ GKウィンドウ作成 ------------
    gk_layout = [[sg.B('Close'),sg.B('マニュアル送信'),sg.B('CANモニタ')],
            [sg.Text(' ')],
            [sg.B("D席窓Close"),sg.B('拡張セッション移行'),sg.B('D席窓Open'),sg.B('ブレーキ工場モード解除')],
            [sg.Text(' ')],
            [sg.B("ダイアグ一括消去"),sg.B('RoB消去'),sg.B('RRCペアリング'),sg.B('Bluetooth遮断解除'),sg.B('Bluetooth遮断')],
            [sg.T('TVECS部品No.入力 '),sg.Input("156000",key='-IN_TVECS-', size=(10,1)),sg.B('コマンド送信')],
            [sg.Text('CAN_ログ'), sg.MLine(key='-LOG-'+sg.WRITE_ONLY_KEY, size=(50,15))],
            [sg.Text(' ')],
            [sg.Text('Version : '),sg.Text(version)],
            ]
    return sg.Window("GKⅢ", gk_layout, finalize=True)

def make_razicon():
    # ------------ 遠隔運転ウィンドウ作成 ------------
    gk_layout = [[sg.B('Close')],
            [sg.Text('      車速   '), sg.MLine(key='-ML_vel-'+sg.WRITE_ONLY_KEY, size=(10,1)),sg.Text('     舵角   '), sg.MLine(key='-ML_str-'+sg.WRITE_ONLY_KEY, size=(10,1))],
            [sg.Text(' ')],
            [sg.Text('*****************************************************************')],
            [sg.B('走行OK'),sg.B('自走モードON'),sg.B('EPB解除'),sg.B('ハザード要求'),sg.B('Pレンジ要求')],
            [sg.Text(' ')],
            [sg.Text('要求加速度'), sg.MLine(key='-ML_acc-'+sg.WRITE_ONLY_KEY, size=(10,1)),sg.Text('要求舵角'), sg.MLine(key='-ML_ang-'+sg.WRITE_ONLY_KEY, size=(10,1))],
            [sg.Text(' ')],
            [sg.Text('                  '),sg.B(" ← ", font=('Arial',15)),sg.B(' ↑ ', font=('Arial',15)),sg.B(' → ', font=('Arial',15))],
            [sg.Text('                  '),sg.B(" R ", font=('Arial',17)),sg.B(' ↓ ', font=('Arial',15)),sg.B(" C ", font=('Arial',17)),sg.B('緊急停止', font=('Arial',15))],
            [sg.Text(' ')],
            [sg.Text('状況'), sg.MLine(key='-ML_msg-'+sg.WRITE_ONLY_KEY, size=(40,2))],
            [sg.Text('Version : '),sg.Text(version)],
            ]
    return sg.Window("Telemotion(遠隔運転モード)", gk_layout, finalize=True)

def make_joycon():
    # ------------ 遠隔運転ウィンドウ作成 ------------
    gk_layout = [[sg.B('Close')],
            [sg.Text('      車速   '), sg.MLine(key='-ML_vel-'+sg.WRITE_ONLY_KEY, size=(10,1)),sg.Text('     舵角   '), sg.MLine(key='-ML_str-'+sg.WRITE_ONLY_KEY, size=(10,1))],
            [sg.T('  最大車速　'),sg.Input("3.0",key='-Maxvelocity-', size=(10,1)),sg.T('  最大舵角　'),sg.Input("440.0",key='-Maxstearing-', size=(10,1)),sg.B('MAX更新')],
            [sg.Text('*****************************************************************')],
            [sg.B('走行OK'),sg.B('自走モードON'),sg.B('EPB解除'),sg.B('ハザード要求'),sg.B('Pレンジ要求')],
            [sg.Text(' ')],
            [sg.Text('要求加速度'), sg.MLine(key='-ML_acc-'+sg.WRITE_ONLY_KEY, size=(10,1)),sg.Text('要求舵角'), sg.MLine(key='-ML_ang-'+sg.WRITE_ONLY_KEY, size=(10,1))],
            [sg.Text(' ')],
            [sg.Text('                  '),sg.B(" ← ", font=('Arial',15)),sg.B(' ↑ ', font=('Arial',15)),sg.B(' → ', font=('Arial',15))],
            [sg.Text('                  '),sg.B(" R ", font=('Arial',17)),sg.B(' ↓ ', font=('Arial',15)),sg.B(" C ", font=('Arial',17)),sg.B('緊急停止', font=('Arial',15))],
            [sg.Text(' ')],
            [sg.Text('状況'), sg.MLine(key='-ML_msg-'+sg.WRITE_ONLY_KEY, size=(40,2))],
            [sg.Text('Version : '),sg.Text(version)],
            ]
    return sg.Window("Telemotion(遠隔運転モード(joycon))", gk_layout, finalize=True)

def make_sub():
    # ------------ サブウィンドウ作成 ------------
    sub_layout = [[sg.T('CANコード入力 '),sg.Input("7d2#0322106000000000",key='-IN-', size=(30,1)),sg.B('送信'),sg.Checkbox("一括",key='checkbox')],
          [sg.Text('CAN受信データ'), sg.MLine(key='-ML1-'+sg.WRITE_ONLY_KEY, size=(50,2))],
          [sg.T('       　　　　　　　　タイマ'),sg.Input("0.5",key='-Timer1-', size=(10,1))],
          [sg.T('CANコード入力 '),sg.Input("750#40062F2841030180",key='-IN2-', size=(30,1)),sg.B('送信2'),sg.Checkbox("一括",key='checkbox2')],
          [sg.Text('CAN受信データ'), sg.MLine(key='-ML2-'+sg.WRITE_ONLY_KEY, size=(50,2))],
          [sg.T('       　　　　　　　　タイマ'),sg.Input("0.5",key='-Timer2-', size=(10,1))],
          [sg.T('CANコード入力 '),sg.Input("750#4002100300000000",key='-IN3-', size=(30,1)),sg.B('送信3'),sg.Checkbox("一括",key='checkbox3')],
          [sg.Text('CAN受信データ'), sg.MLine(key='-ML3-'+sg.WRITE_ONLY_KEY, size=(50,2))],
          [sg.T('       　　　　　　　　タイマ'),sg.Input("0.5",key='-Timer3-', size=(10,1))],
          [sg.T('CANコード入力 '),sg.Input("750#40062F2842030180",key='-IN4-', size=(30,1)),sg.B('送信4'),sg.Checkbox("一括",key='checkbox4')],
          [sg.Text('CAN受信データ'), sg.MLine(key='-ML4-'+sg.WRITE_ONLY_KEY, size=(50,2))],
          [sg.T('       　　　　　　　　タイマ'),sg.Input("0.5",key='-Timer4-', size=(10,1))],
          [sg.T('CANコード入力 '),sg.Input("77f#fe0414ffffff0000",key='-IN5-', size=(30,1)),sg.B('送信5'),sg.Checkbox("一括",key='checkbox5')],
          [sg.Text('CAN受信データ'), sg.MLine(key='-ML5-'+sg.WRITE_ONLY_KEY, size=(50,2))],
          [sg.B('一括送信'),sg.Text(' '),sg.B('Close')],
          [sg.Text(' ')],
          [sg.Text('Version : '),sg.Text(version)],
          ]
    return sg.Window("マニュアル送信", sub_layout, finalize=True)

def make_canfd():
    # ------------ サブウィンドウ作成 ------------
    canfd_layout = [[sg.B('CANFD更新'),sg.Text(' '),sg.B('Close'),sg.B('CAN停止'),sg.B('CAN送信')],
          [sg.Text(' ')],
          [sg.T('CANFD_ID '),sg.Input("91",key='-canfd_id-', size=(7,1))],
          [
          sg.T('data#01~10'),sg.Input("00",key='-canfd_data01-', size=(3,1)),
          sg.Input("00",key='-canfd_data02-', size=(3,1)),
          sg.Input("00",key='-canfd_data03-', size=(3,1)),
          sg.Input("64",key='-canfd_data04-', size=(3,1)),
          sg.Input("00",key='-canfd_data05-', size=(3,1)),
          sg.Input("00",key='-canfd_data06-', size=(3,1)),
          sg.Input("00",key='-canfd_data07-', size=(3,1)),
          sg.Input("00",key='-canfd_data08-', size=(3,1)),
          sg.Input("00",key='-canfd_data09-', size=(3,1)),
          sg.Input("00",key='-canfd_data10-', size=(3,1)),
          ],
          [
          sg.T('data#11~20'),sg.Input("00",key='-canfd_data11-', size=(3,1)),
          sg.Input("00",key='-canfd_data12-', size=(3,1)),
          sg.Input("00",key='-canfd_data13-', size=(3,1)),
          sg.Input("00",key='-canfd_data14-', size=(3,1)),
          sg.Input("00",key='-canfd_data15-', size=(3,1)),
          sg.Input("00",key='-canfd_data16-', size=(3,1)),
          sg.Input("00",key='-canfd_data17-', size=(3,1)),
          sg.Input("00",key='-canfd_data18-', size=(3,1)),
          sg.Input("00",key='-canfd_data19-', size=(3,1)),
          sg.Input("00",key='-canfd_data20-', size=(3,1)),
          ],
          [
          sg.T('data#21~30'),sg.Input("00",key='-canfd_data21-', size=(3,1)),
          sg.Input("00",key='-canfd_data22-', size=(3,1)),
          sg.Input("00",key='-canfd_data23-', size=(3,1)),
          sg.Input("00",key='-canfd_data24-', size=(3,1)),
          sg.Input("00",key='-canfd_data25-', size=(3,1)),
          sg.Input("00",key='-canfd_data26-', size=(3,1)),
          sg.Input("00",key='-canfd_data27-', size=(3,1)),
          sg.Input("00",key='-canfd_data28-', size=(3,1)),
          sg.Input("00",key='-canfd_data29-', size=(3,1)),
          sg.Input("00",key='-canfd_data30-', size=(3,1)),
          ],
          [
          sg.T('data#31~32'),sg.Input("00",key='-canfd_data31-', size=(3,1)),
          sg.Input("00",key='-canfd_data32-', size=(3,1)),
          ],
          [sg.Text(' ')],
          [sg.Text('Version : '),sg.Text(version)],
          ]
    return sg.Window("CANFD通信モード", canfd_layout, finalize=True)


def make_pw():
    # ------------ メインウィンドウ作成 ------------
    main_layout = [
            [sg.T('PW入力 '),sg.Input("",key='-PW-', size=(30,1)),sg.B('OK')],
            [sg.Text(' ')],
            [sg.Text(' ')],
            [sg.Text('Version : '),sg.Text(version)],
            ]
    return sg.Window("パスワード", main_layout, finalize=True, size=(350, 250))

def make_log():
    # ------------ CANモニタウィンドウ作成 ------------
    main_layout = [[sg.B('Close'),sg.B('開始'),sg.B('停止'),sg.Checkbox("フィルタ",key='filter')],
            [sg.Text('CAN_ログ'), sg.MLine(key='-Monitor-'+sg.WRITE_ONLY_KEY, size=(50,20))]
            ]
    return sg.Window("CANmonitor", main_layout, finalize=True)

def can_send(send_msg):
    cansendmessage = "cansend can1 "+ send_msg
    os.system(cansendmessage)
    nowtime = time.ctime()
    log_message = "S"+"," + nowtime + ","+ send_msg
    logmake.Log_make(file_log_name,log_message)

gu16_table = [
  0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50A5, 0x60C6, 0x70E7,
  0x8108, 0x9129, 0xA14A, 0xB16B, 0xC18C, 0xD1AD, 0xE1CE, 0xF1EF,
  0x1231, 0x0210, 0x3273, 0x2252, 0x52B5, 0x4294, 0x72F7, 0x62D6,
  0x9339, 0x8318, 0xB37B, 0xA35A, 0xD3BD, 0xC39C, 0xF3FF, 0xE3DE,
  0x2462, 0x3443, 0x0420, 0x1401, 0x64E6, 0x74C7, 0x44A4, 0x5485,
  0xA56A, 0xB54B, 0x8528, 0x9509, 0xE5EE, 0xF5CF, 0xC5AC, 0xD58D,
  0x3653, 0x2672, 0x1611, 0x0630, 0x76D7, 0x66F6, 0x5695, 0x46B4,
  0xB75B, 0xA77A, 0x9719, 0x8738, 0xF7DF, 0xE7FE, 0xD79D, 0xC7BC,
  0x48C4, 0x58E5, 0x6886, 0x78A7, 0x0840, 0x1861, 0x2802, 0x3823,
  0xC9CC, 0xD9ED, 0xE98E, 0xF9AF, 0x8948, 0x9969, 0xA90A, 0xB92B,
  0x5AF5, 0x4AD4, 0x7AB7, 0x6A96, 0x1A71, 0x0A50, 0x3A33, 0x2A12,
  0xDBFD, 0xCBDC, 0xFBBF, 0xEB9E, 0x9B79, 0x8B58, 0xBB3B, 0xAB1A,
  0x6CA6, 0x7C87, 0x4CE4, 0x5CC5, 0x2C22, 0x3C03, 0x0C60, 0x1C41,
  0xEDAE, 0xFD8F, 0xCDEC, 0xDDCD, 0xAD2A, 0xBD0B, 0x8D68, 0x9D49,
  0x7E97, 0x6EB6, 0x5ED5, 0x4EF4, 0x3E13, 0x2E32, 0x1E51, 0x0E70,
  0xFF9F, 0xEFBE, 0xDFDD, 0xCFFC, 0xBF1B, 0xAF3A, 0x9F59, 0x8F78,
  0x9188, 0x81A9, 0xB1CA, 0xA1EB, 0xD10C, 0xC12D, 0xF14E, 0xE16F,
  0x1080, 0x00A1, 0x30C2, 0x20E3, 0x5004, 0x4025, 0x7046, 0x6067,
  0x83B9, 0x9398, 0xA3FB, 0xB3DA, 0xC33D, 0xD31C, 0xE37F, 0xF35E,
  0x02B1, 0x1290, 0x22F3, 0x32D2, 0x4235, 0x5214, 0x6277, 0x7256,
  0xB5EA, 0xA5CB, 0x95A8, 0x8589, 0xF56E, 0xE54F, 0xD52C, 0xC50D,
  0x34E2, 0x24C3, 0x14A0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
  0xA7DB, 0xB7FA, 0x8799, 0x97B8, 0xE75F, 0xF77E, 0xC71D, 0xD73C,
  0x26D3, 0x36F2, 0x0691, 0x16B0, 0x6657, 0x7676, 0x4615, 0x5634,
  0xD94C, 0xC96D, 0xF90E, 0xE92F, 0x99C8, 0x89E9, 0xB98A, 0xA9AB,
  0x5844, 0x4865, 0x7806, 0x6827, 0x18C0, 0x08E1, 0x3882, 0x28A3,
  0xCB7D, 0xDB5C, 0xEB3F, 0xFB1E, 0x8BF9, 0x9BD8, 0xABBB, 0xBB9A,
  0x4A75, 0x5A54, 0x6A37, 0x7A16, 0x0AF1, 0x1AD0, 0x2AB3, 0x3A92,
  0xFD2E, 0xED0F, 0xDD6C, 0xCD4D, 0xBDAA, 0xAD8B, 0x9DE8, 0x8DC9,
  0x7C26, 0x6C07, 0x5C64, 0x4C45, 0x3CA2, 0x2C83, 0x1CE0, 0x0CC1,
  0xEF1F, 0xFF3E, 0xCF5D, 0xDF7C, 0xAF9B, 0xBFBA, 0x8FD9, 0x9FF8,
  0x6E17, 0x7E36, 0x4E55, 0x5E74, 0x2E93, 0x3EB2, 0x0ED1, 0x1EF0
]

def e2e_calc(fddata,i32_size,canid_h,canid_l):
    u16_crc = 0xffff

    for i32_count in range(i32_size):
        u16_crc_bef = gu16_table[((u16_crc>>8)^fddata[i32_count])&0xff]
        u16_crc=u16_crc_bef ^((u16_crc<<8)&0xffff)

    u16_crc ^= 0x0000
    u16_crc = gu16_table[(u16_crc>>8)^canid_l]^((u16_crc<<8)&0xffff)
    u16_crc ^= 0x0000
    u16_crc = gu16_table[(u16_crc>>8)^canid_h]^((u16_crc<<8)&0xffff)
    u16_crc ^= 0x0000
    return u16_crc

def gui_main():
    global global_rec_msg,nowtime,msg_rec_flg,mode,end_flg,go_flg,safety_flg,automoving_mode
    global now_vel,now_str,tgt_acc,tgt_str,event,values,global_now_msg,count_e2e,fd_data,joycon_flg
    global Maxvelocity,Maxstearing,can_msg_flg,canfd_msg_flg
    global command_canorcanfd,command_can_id,command_can_data,command_send_flg
    window = make_joycon()
    #########
    go_flg = 1
    safety_flg = 1
    automoving_mode = 1
    tgt_acc = 0
    tgt_str = 0
    # window = make_joycon()
    global_now_msg = "外部操作モード有の遠隔運転モードに切り替えました"
    #########
    count_run = 1
    if mode == "can":
        try:
            can1 = can.interface.Bus(channel = 'can1', bustype='socketcan', bitrate=500000, canfilters=None, fd=True)
        except:
            print("[error]can't initialize can")
    elif mode == "tcp":
        try:
            print("MODE : tcp reveive mode")
            # tcp_ip,tcp_port, tcp_timeout =config.TCP_Setting_Read()
            tcp_ip = "127.0.0.1"
            tcp_port = 9000
            tcp_timeout = 10
            #test=TCPconnect(ip=tcp_ip,port=tcp_port,timeout=tcp_timeout)
            #print("end_flg = ",end_flg)
            HOST = checkIP#"127.0.0.10"
            PORT = int(checkPort)
            client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except:

            print("[error]can't initialize tcp")

    while True:
        event, values = window.read(timeout=control_time,timeout_key='-timeout-')
        if event == sg.WIN_CLOSED or event == "Exit":
            go_flg = 0
            automoving_mode =0
            end_flg = 1
            canfd_msg_flg = 0
            break
        # Closeボタンが押された場合
        elif event == "Close":
            window.close()
            window = make_main()
            safety_flg = 0
            automoving_mode = 0
            joycon_flg = 0
            canfd_msg_flg = 0

        elif event == "OK":
            while True:
                event, values = window.read()
                if event == sg.WIN_CLOSED or event == "OK":
                    input_PW = values['-PW-']
                    if input_PW == "telemotion2022":
                        print("パスワードOK")
                        break
                    else:
                        print("パスワードが異なります")
                        time.sleep(1)
                        print("パスワードを入力してください")
            window.close()
            window = make_main()

        elif event == "ダイアグ通信モード":
            window.close()
            window = make_gk()

        elif event == "CANFD通信モード":
            window.close()
            window = make_canfd()
            canfd_msg_flg = 1
            canfd_id ="default"
            canfd_data = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]#32byte

        elif event == "マニュアル送信":
            window.close()
            window = make_sub()

        elif event == "遠隔運転モード":
            window.close()
            go_flg = 1
            safety_flg = 0
            automoving_mode = 1
            tgt_acc = 0
            tgt_str = 0
            window = make_razicon()
            global_now_msg = "遠隔運転モードに切り替えました"


        elif event == "遠隔運転モード(JoyCon)":
            window.close()
            go_flg = 1
            safety_flg = 0
            automoving_mode = 1
            joycon_flg = 1
            tgt_acc = 0
            tgt_str = 0
            window = make_joycon()
            global_now_msg = "JoyConモードの遠隔運転モードに切り替えました"

        elif event == "遠隔運転モード(外部操作)":
            window.close()
            go_flg = 1
            safety_flg = 1
            automoving_mode = 1
            tgt_acc = 0
            tgt_str = 0
            window = make_joycon()
            global_now_msg = "外部操作モード有の遠隔運転モードに切り替えました"

        elif event == "MAX更新":
            Maxvelocity = float(values['-Maxvelocity-'])
            Maxstearing = float(values['-Maxstearing-'])

        elif event == "CANモニタ":
            window.close()
            window = make_log()

        elif event == "CAN停止":
            can_msg_flg = 0

        elif event == "CAN送信":
            can_msg_flg = 1

        elif event == "CANFD更新":
            canfd_id = int(values['-canfd_id-'])
            canfd_data[0] = int(values['-canfd_data01-'])
            canfd_data[1] = int(values['-canfd_data02-'])
            canfd_data[2] = int(values['-canfd_data03-'])
            canfd_data[3] = int(values['-canfd_data04-'])
            canfd_data[4] = int(values['-canfd_data05-'])
            canfd_data[5] = int(values['-canfd_data06-'])
            canfd_data[6] = int(values['-canfd_data07-'])
            canfd_data[7] = int(values['-canfd_data08-'])
            canfd_data[8] = int(values['-canfd_data09-'])
            canfd_data[9] = int(values['-canfd_data10-'])
            canfd_data[10] = int(values['-canfd_data11-'])
            canfd_data[11] = int(values['-canfd_data12-'])
            canfd_data[12] = int(values['-canfd_data13-'])
            canfd_data[13] = int(values['-canfd_data14-'])
            canfd_data[14] = int(values['-canfd_data15-'])
            canfd_data[15] = int(values['-canfd_data16-'])
            canfd_data[16] = int(values['-canfd_data17-'])
            canfd_data[17] = int(values['-canfd_data18-'])
            canfd_data[18] = int(values['-canfd_data19-'])
            canfd_data[19] = int(values['-canfd_data20-'])
            canfd_data[20] = int(values['-canfd_data21-'])
            canfd_data[21] = int(values['-canfd_data22-'])
            canfd_data[22] = int(values['-canfd_data23-'])
            canfd_data[23] = int(values['-canfd_data24-'])
            canfd_data[24] = int(values['-canfd_data25-'])
            canfd_data[25] = int(values['-canfd_data26-'])
            canfd_data[26] = int(values['-canfd_data27-'])
            canfd_data[27] = int(values['-canfd_data28-'])
            canfd_data[28] = int(values['-canfd_data29-'])
            canfd_data[29] = int(values['-canfd_data30-'])
            canfd_data[30] = int(values['-canfd_data31-'])
            canfd_data[31] = int(values['-canfd_data32-'])


            #canfd_data = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]#32byte

        elif event == 'コマンド送信':
            if values['-IN_TVECS-']=="156000":
                window['-LOG-'+sg.WRITE_ONLY_KEY].print("S:156000を送信")
            else:
                window['-LOG-'+sg.WRITE_ONLY_KEY].print("*******部品が存在しません("+values['-IN_TVECS-']+")*******")
        elif event == '開始':
            print("CAN message rec start")
            while True:
                if msg_rec_flg == 1:
                    rec_msg = global_rec_msg
                    msg_str = str(rec_msg)
                    if mode == "can":
                        msg_str = msg_str[36:101]
                    window['-Monitor-'+sg.WRITE_ONLY_KEY].print(msg_str)
                    msg_rec_flg = 0
                event, values = window.read(0.05)
                if event == "停止":
                    print("CAN message rec stop")
                    break

        elif event == '拡張セッション移行':
            #Bluetooth遮断解除
            can_send("750#4002100300000000")
            window['-LOG-'+sg.WRITE_ONLY_KEY].print("750#4002100300000000 拡張セッション移行")
        elif event == 'D席窓Open':
            #Bluetooth遮断解除
            can_send("750#40062F2842030180")
            window['-LOG-'+sg.WRITE_ONLY_KEY].print("750#40062F2842030180 D席窓Open")
        elif event == 'D席窓Close':
            #Bluetooth遮断解除
            can_send("750#40062F2841030180")
            window['-LOG-'+sg.WRITE_ONLY_KEY].print("750#40062F2841030180 D席窓Close")

        elif event == 'ブレーキ工場モード解除':
            can_send("7b0#0210030000000000")
            window['-LOG-'+sg.WRITE_ONLY_KEY].print("7b0#0210030000000000 拡張セッション移行")
            time.sleep(0.2)
            can_send("7b0#032e020400000000")
            window['-LOG-'+sg.WRITE_ONLY_KEY].print("7b0#032e020400000000 ブレーキ工場モード解除")


        elif event == 'RRCペアリング':
            #Bluetooth遮断解除
            can_send("7d0#0531011119000000")
            window['-LOG-'+sg.WRITE_ONLY_KEY].print("7d0#0531011119000000 Bluetooth遮断解除")
            time.sleep(1)
            #MM接続履歴消去
            can_send("7d0#0631011108010000")
            window['-LOG-'+sg.WRITE_ONLY_KEY].print("7d0#0631011108010000 MM接続履歴消去")
            time.sleep(1)
            #ペアリング移行
            can_send("7d0#0531011107000000")
            window['-LOG-'+sg.WRITE_ONLY_KEY].print("7d0#0531011107000000 ペアリング移行")
            time.sleep(1)

        elif event == 'Bluetooth遮断解除':
            #Bluetooth遮断解除
            can_send("7d0#0531011119000000")
            window['-LOG-'+sg.WRITE_ONLY_KEY].print("7d0#0531011119000000 Bluetooth遮断解除")
        elif event == 'Bluetooth遮断':
            #Bluetooth遮断
            can_send("7d0#0531011118000000")
            window['-LOG-'+sg.WRITE_ONLY_KEY].print("7d0#0531011118000000 Bluetooth遮断")

        elif event == 'ダイアグ一括消去':
            #ダイアグ一括消去
            can_send("77f#fe0414ffffff0000")
            window['-LOG-'+sg.WRITE_ONLY_KEY].print("77f#fe0414ffffff0000 ダイアグ一括消去")

        elif event == ' ↑ ':
            can_msg_flg = 1
            if go_flg == 1:
                tgt_acc = tgt_acc + (1 * adjust_acc)
            else:
                global_now_msg = "【緊急停止】中です。走行OKボタンを押して再開してください"

        elif event == ' ↓ ':
            can_msg_flg = 1
            if go_flg == 1:
                tgt_acc = tgt_acc - (1 * adjust_blake)
            else:
                global_now_msg = "【緊急停止】中です。走行OKボタンを押して再開してください"

        elif event == ' ← ':
            can_msg_flg = 1
            if go_flg == 1:
                tgt_str = tgt_str + (1 * adjust_str)
            else:
                global_now_msg = "【緊急停止】中です。走行OKボタンを押して再開してください"

        elif event == ' → ':
            can_msg_flg = 1
            if go_flg == 1:
                tgt_str = tgt_str - (1 * adjust_str)
            else:
                global_now_msg = "【緊急停止】中です。走行OKボタンを押して再開してください"

        elif event == ' C ':
            tgt_str = 0
            tgt_acc = 0

        elif event == ' R ':
            if now_vel < 0.1:
                print("Rレンジ要求を実施")
                fd_data[9-1] = 0xa6
                global_now_msg = "【Rレンジ要求】ボタンが押されました。"
                tgt_acc = -0.1
                try:
                    msg = can.Message(arbitration_id=0x05a, data=fd_data, is_extended_id=False, is_fd=True)
                    can1.send(msg)
                except:
                    print("[error]can't send message to can device (l.575_Rレンジ要求)")
                time.sleep(0.1)

            else:
                print("NG)Rレンジ要求がされましたが車速が０でないためRにできません")
                global_now_msg = "【NG)Rレンジ要求】ボタンが押されましたが車速が0でないためRにできません"


        elif event == '自走モードON':
            can_send("750#5f03222002000000")
            time.sleep(0.2)
            can_send("750#5f02100300000000")
            time.sleep(0.2)
            can_send("750#5f052e2002808000")
            time.sleep(0.2)
            can_send("750#5f03222002000000")

        elif event =='ハザード要求':
            data = [00, 00, 0x40, 00, 00, 00, 00, 00]
            #data = [random.randint(0, 255) for _ in range(32)]
            ## Construct CAN message
            try:
                msg = can.Message(arbitration_id=0x05b, data=data, is_extended_id=False, is_fd=True)
                can1.send(msg)
            except:
                print("[error]can't send message to can device (l.351)")

        elif event =='Pレンジ要求':
            if now_vel < 0.1:
                print("Pレンジ要求を実施")
                tgt_acc = -0.1
                fd_data[9-1] = 0xc6
                global_now_msg = "【Pレンジ要求】ボタンが押されました。走行OKであれば走行OKボタンを押して再開できます"

                #data = [00, 00, 0x40, 00, 00, 00, 00, 00]
                #data = [random.randint(0, 255) for _ in range(32)]
                ## Construct CAN message
                try:
                    msg = can.Message(arbitration_id=0x05a, data=fd_data, is_extended_id=False, is_fd=True)
                    can1.send(msg)
                except:
                    print("[error]can't send message to can device (l.468_Pレンジ要求)")
                time.sleep(0.1)
                can_msg_flg = 0
            else:
                print("NG)Pレンジ要求がされましたが車速が０でないためPにできません")
                global_now_msg = "【NG)Pレンジ要求】ボタンが押されましたが車速が0でないためPにできません"


        elif event =='EPB解除':
            fd_data[9-1] = 0x0e
            print("！！！！EPB解除要求！！！！")
            global_now_msg = "【EPB解除要求】ボタンが押されました。"

        elif event =='緊急停止':
            tgt_acc = emergency_brake
            go_flg = 0
            print("！！！！緊急停止！！！！")
            global_now_msg = "【緊急停止】ボタンが押されました。走行OKであれば走行OKボタンを押して再開できます"
        elif event =='走行OK':
            fd_data[9-1] = 0x66
            global_now_msg = "走行を再開します"
            tgt_acc = 0
            go_flg = 1
            can_msg_flg = 1
            global_now_msg = "【走行OK】ボタンが押されました。再開できます"

        elif event =='定常走行':
            count_e2e = 0
            if go_flg == 0:
                global_now_msg = "走行停止指示あり(走行フラグ=0）のため、走行不可"
                window['-ML_msg-'+sg.WRITE_ONLY_KEY].update(global_now_msg)
            elif go_flg == 1:
                global_now_msg = "定常走行 " + str(send_fd_file) + " を開始します。 ※ループ中→緊停＆走OK＆Closeボタン以外無効"
                window['-ML_msg-'+sg.WRITE_ONLY_KEY].update(global_now_msg)
            data = []
            #with open("./fdsend_test3.csv") as f:#send_fd_file
            filepath = "./" + send_fd_file
            with open(filepath) as f:#send_fd_file
                for line in f:
                    data.append(line)

            count_i = 0
            count_j = 0
            send_data = []
            line = []
            loop_flg = 0
            for i in data:
                event, values = window.read(100)
                if event == sg.WIN_CLOSED or event == "Exit":
                    go_flg = 0
                    end_flg = 1
                    break
                elif event =='緊急停止':
                    go_flg = 0
                    print("！！！！緊急停止！！！！")
                    global_now_msg = "【緊急停止】ボタンが押されました。走行OKであれば走行OKボタンを押して再開できます"
                    window['-ML_msg-'+sg.WRITE_ONLY_KEY].update(global_now_msg)

                elif go_flg == 0:
                    while go_flg == 0:
                        print("！！！！走行停止指示あり！！！！（走行フラグ=0）")
                        #time.sleep(2)
                        #print("go_flg =" , go_flg)
                        event, values = window.read(2000)
                        if event == sg.WIN_CLOSED or event == "Exit":
                            go_flg = 0
                            end_flg = 1
                            break
                        elif event =='走行OK':
                            go_flg = 1
                        elif event =='Close':
                            loop_flg = 1
                            global_now_msg = "定常走行を中断します"
                            window['-ML_msg-'+sg.WRITE_ONLY_KEY].update(global_now_msg)
                            print("定常走行中断、走行停止中（走行フラグ=0）")
                            event, values = window.read(2)
                            break
                    if loop_flg == 1:
                        loop_flg = 0
                        break
                elif go_flg ==1:
                    count_j= 0
                    datalist = i.split(",")
                    #print("i = ,",datalist)
                    #print("i length = ,",len(datalist))
                    for j in range(len(datalist)):
                        str_datalist = str(datalist[count_j])
                        if j == (len(datalist)-1):
                            str_datalist= str_datalist[:-1]
                            #print('******str_datalist = ',str_datalist)
                        str_datalist=int(str_datalist,16)#16進数でインポートするなら必要
                        line.append(int(str_datalist))
                        count_j = count_j + 1
                        #print("j = ",j)
                    #print("send message = ",line)
                    if can_msg_flg == 1:
                        try:
                            msg = can.Message(arbitration_id=0x05a, data=line, is_extended_id=False, is_fd=True)
                            can1.send(msg)
                        except:
                            print("[error]can't send message to can device (l.442)")
                    line = []
                    #print("count:"+str(count_i)+"    line:"+str(line))
                    count_i = count_i + 1
                    window['-ML_vel-'+sg.WRITE_ONLY_KEY].update(now_vel)
                    window['-ML_str-'+sg.WRITE_ONLY_KEY].update(now_str)

                    if count_run % 10 ==0:
                        data = [00, 00, 0x40, 00, 00, 00, 00, 00]
                        #data = [random.randint(0, 255) for _ in range(32)]
                        ## Construct CAN message
                        try:
                            msg = can.Message(arbitration_id=0x05b, data=data, is_extended_id=False, is_fd=True)
                            can1.send(msg)
                        except:
                            print("[error]can't send message to can device (l.457)")

        elif event == '送信':
            input_data = values['-IN-']
            can_send(input_data)
            time.sleep(0.2)
            rec_msg = global_rec_msg
            msg_str = str(rec_msg)
            msg_str = msg_str[36:101]
            window['-ML1-'+sg.WRITE_ONLY_KEY].print(msg_str)
        elif event == '送信2':
            input_data = values['-IN2-']
            can_send(input_data)
            time.sleep(0.2)
            rec_msg = global_rec_msg
            msg_str = str(rec_msg)
            msg_str = msg_str[36:101]
            window['-ML2-'+sg.WRITE_ONLY_KEY].print("R",msg_str)
        elif event == '送信3':
            input_data = values['-IN3-']
            can_send(input_data)
            time.sleep(0.2)
            rec_msg = global_rec_msg
            msg_str = str(rec_msg)
            msg_str = msg_str[36:101]
            window['-ML3-'+sg.WRITE_ONLY_KEY].print("R",msg_str)
        elif event == '送信4':
            input_data = values['-IN4-']
            can_send(input_data)
            time.sleep(0.2)
            rec_msg = global_rec_msg
            msg_str = str(rec_msg)
            msg_str = msg_str[36:101]
            window['-ML4-'+sg.WRITE_ONLY_KEY].print("R",msg_str)
        elif event == '送信5':
            input_data = values['-IN5-']
            can_send(input_data)
            time.sleep(0.2)
            rec_msg = global_rec_msg
            msg_str = str(rec_msg)
            msg_str = msg_str[36:101]
            window['-ML5-'+sg.WRITE_ONLY_KEY].print("R",msg_str)
        elif event == '一括送信':
            if values['checkbox']:
                input_data = values['-IN-']
                can_send(input_data)
                time.sleep(0.2)
                rec_msg = global_rec_msg
                msg_str = str(rec_msg)
                msg_str = msg_str[36:101]
                window['-ML1-'+sg.WRITE_ONLY_KEY].print("R",msg_str)

                timer = values['-Timer1-']
                timer_float=float(timer)
                time.sleep(timer_float)

            if values['checkbox2']:
                input_data = values['-IN2-']
                can_send(input_data)
                time.sleep(0.2)
                rec_msg = global_rec_msg
                msg_str = str(rec_msg)
                msg_str = msg_str[36:101]
                window['-ML2-'+sg.WRITE_ONLY_KEY].print("R",msg_str)

                timer = values['-Timer2-']
                timer_float=float(timer)
                time.sleep(timer_float)

            if values['checkbox3']:
                input_data = values['-IN3-']
                can_send(input_data)
                time.sleep(0.2)
                rec_msg = global_rec_msg
                msg_str = str(rec_msg)
                msg_str = msg_str[36:101]
                window['-ML3-'+sg.WRITE_ONLY_KEY].print("R",msg_str)

                timer = values['-Timer3-']
                timer_float=float(timer)
                time.sleep(timer_float)

            if values['checkbox4']:
                input_data = values['-IN4-']
                can_send(input_data)
                time.sleep(0.2)
                rec_msg = global_rec_msg
                msg_str = str(rec_msg)
                msg_str = msg_str[36:101]
                window['-ML4-'+sg.WRITE_ONLY_KEY].print("R",msg_str)

                timer = values['-Timer4-']
                timer_float=float(timer)
                time.sleep(timer_float)

            if values['checkbox5']:
                input_data = values['-IN5-']
                can_send(input_data)
                time.sleep(0.2)
                rec_msg = global_rec_msg
                msg_str = str(rec_msg)
                msg_str = msg_str[36:101]
                window['-ML5-'+sg.WRITE_ONLY_KEY].print("R",msg_str)

        if automoving_mode == 1:
            window['-ML_vel-'+sg.WRITE_ONLY_KEY].update(now_vel)
            window['-ML_str-'+sg.WRITE_ONLY_KEY].update(now_str)
            window['-ML_acc-'+sg.WRITE_ONLY_KEY].update(tgt_acc)
            window['-ML_ang-'+sg.WRITE_ONLY_KEY].update(tgt_str)
            window['-ML_msg-'+sg.WRITE_ONLY_KEY].update(global_now_msg)

            fd_data[2] = count_e2e
            if count_e2e <= 254:
                count_e2e = count_e2e + 1
            else:
                count_e2e = 0

            #tgt_acc をローカルにして処理するように変更 241026
            #print("tgt_acc = ",tgt_acc)
            tgt_acc_local = tgt_acc
            
            if go_flg == 0:
                tgt_acc_local = emergency_brake
            if tgt_acc_local > 0:
                if now_vel > (Maxvelocity + 2):
                    tgt_acc_local = -0.3
                elif now_vel > Maxvelocity:
                    tgt_acc_local = -0.1
            if tgt_acc_local >= 0:
                tgt_acc_adj = (tgt_acc_local * 1000)
            elif tgt_acc_local < 0:
                tgt_acc_adj = (tgt_acc_local * 1000)+(2**16)
            #print("tgt_acc_adj = ",tgt_acc_adj)
            tgt_acc_hex = format(int(tgt_acc_adj), '04X')
            fd_data[5-1] = int(tgt_acc_hex[0:2],16)
            #print("tgt_hex:",tgt_acc_hex)
            fd_data[6-1] = int(tgt_acc_hex[2:4],16)
            fd_data[11-1] = int(tgt_acc_hex[0:2],16)
            fd_data[12-1] = int(tgt_acc_hex[2:4],16)

            tgt_str_local = tgt_str
            
            #print("tgt_str(deg) = ",tgt_str)
            if tgt_str_local > Maxstearing:
                tgt_str_local = Maxstearing
            if tgt_str_local < -1 * Maxstearing:
                tgt_str_local = -1 * Maxstearing
            if tgt_str_local >= 0:
                tgt_str_adj = (tgt_str_local * 1000 * 3.14 / 180)
            elif tgt_str_local < 0:
                tgt_str_adj = (tgt_str_local * 1000 * 3.14 / 180 ) + ( 2**16 )
            #print("tgt_str_adj = ",tgt_str_adj)
            tgt_str_hex = format(int(tgt_str_adj), '04X')
            fd_data[7-1] = int(tgt_str_hex[0:2],16)
            #print("tgt_hex:",tgt_str_hex)
            fd_data[8-1] = int(tgt_str_hex[2:4],16)



            #####CRCの計算#################3
            CRC = e2e_calc(fd_data[2:],30,0x00,0x5a)
            e2e_hex = format(int(CRC), '04X')
            #print("e2e == ",(e2e_hex))

            fd_data[1] = int(e2e_hex[0:2],16)
            fd_data[0] = int(e2e_hex[2:4],16)

            ###itizi#########################################################3print("fd_data == ",fd_data)
            #fd_data[:0] = int(e2e_hex[0:2],16)##左に追加
            #fd_data[:0] = int(e2e_hex[2:4],16)##左に追加
            if go_flg == 1:
                if mode == "can":
                    if can_msg_flg ==1:
                        try:
                            msg = can.Message(arbitration_id=0x05a, data=fd_data, is_extended_id=False, is_fd=True)
                            can1.send(msg)
                        except:
                            print("[error]can't send message to can device (l.618)")

                elif mode == "tcp":
                    try:

                        # 16進数に変換して文字列に結合
                        hex_string = ''.join(f'{x:02x}' for x in fd_data)

                        #print(hex_string)
                        print("to GameEngine : "+hex_string + "  port:" + str(PORT))

                        client.sendto(hex_string.encode('utf-8'),(HOST,PORT))
                        time.sleep(0.01)
                    except:
                        print("[error]can't send message to tcp device (l.668)")
                else:
                    print("[error] mode nothing")


            if tgt_acc >= 0.05:
                tgt_acc = tgt_acc - (0.01 * adjust_accblake)
            elif (tgt_acc > 0 ) and (tgt_acc < 0.05):
                #print('acc < 0.1')
                tgt_acc = 0
            #count_run = count_run + 1
            #if count_run % 10 ==0:
              #  data = [00, 00, 0x40, 00, 00, 00, 00, 00]
                #data = [random.randint(0, 255) for _ in range(32)]
                ## Construct CAN message
               # try:
               #     msg = can.Message(arbitration_id=0x05b, data=data, is_extended_id=False, is_fd=True)
               #     can1.send(msg)
               # except:
               #     print("cant send message to can device")
        elif canfd_msg_flg == 1:
            time.sleep(0.1)
            print("canfd_id = ",canfd_id)
            print("canfd_data = ",canfd_data)

            if mode == "can":
                if can_msg_flg == 1:
                    try:
                        msg = can.Message(arbitration_id=canfd_id, data=canfd_data, is_extended_id=False, is_fd=True)
                        can1.send(msg)
                    except:
                        print("[error]can't send message to can device (canfd_mode)")
                else:
                    print("can_msg_flgがOFFのため、CAN送信不可")
                    time.sleep(0.5)

        if command_send_flg == 1:
            command_send_flg = 0
            if command_canorcanfd == "canfd":
                try:
                    msg = can.Message(arbitration_id=command_can_id, data=command_can_data, is_extended_id=False, is_fd=True)
                    can1.send(msg)
                except:
                    print("[error]can't send canfd message to can device (command_joycon)")

            elif command_canorcanfd == "subcan":
                try:
                    message_subcan = command_can_id + "02100300000000"
                    can_send(message_subcan)
                    time.sleep(0.2)
                    message_subcan = command_can_id + command_can_data
                    can_send(message_subcan)

                except:
                    print("[error]can't send message to can device (command_joycon)")
            elif command_canorcanfd == "can":
                try:
                    message_can = command_can_id + "#" + command_can_data
                    can_send(message_can)

                except:
                    print("[error]can't send message to can device (command_joycon)")

    # ウィンドウを終了する
    window.close()
    print("GUI表示終了します")


##*****************************************************************************************

def thread01():#Message receive
    print('thre1_start')
    global global_rec_msg
    global calculate_flg
    global nowtime
    global msg_rec_flg
    global end_flg
    global safety_flg,automoving_mode
    global now_vel,now_str,tgt_acc,tgt_str,event,values
    global send_vehicledata

    if mode == "can":
        print("MODE : can reveive mode")

        can_init.CAN_init()
        #os.system('sudo ifconfig can0 down')
        #os.system('sudo ip link set can0 type can bitrate 500000')#500kbpsトヨタ仕様
        #os.system('sudo ifconfig can0 up')
        #os.system('sudo ifconfig can0 txqueuelen 1000000')

        #try:
        can_filters = [{"can_id":0x700,"can_mask":0x7F0}]
    #can0 = can.interface.Bus(channel = 'can0', bustype='socketcan', bitrate=500000, canfilters=can_filters)
        can0 = can.interface.Bus(channel = 'can0', bustype='socketcan', bitrate=500000, canfilters=None, fd=True)

        msg_id = None;
        count_id4 = 0
        can_msg_vel = "0000"
        can_msg_str = "000"
        can_msg_sft = "000"

        while end_flg == 0:
            # print("thread11111111111111")
            msg = can0.recv(1.0)
            msg_str = str(msg)
            #print(msg_str)
            #msg_str = "Timestamp: 1652798453.126237        ID: 0750    S Rx                DL:  8    5f 05 2e 20 02 f9 00 00"
            #Timestamp: 1716461757.164243    ID:      081    S Rx     F BS       DL: 32    00 00 00 18 ff b9 bf 1(100)8 00 00 00 20 00 00 00 00 ff 8c ff b9 ff b9 ff b9 ff b9 00 00 63 c1 d9 69   (76) Channel: can0
            #Timestamp: 1716461757.161496    ID:      0d7    S Rx     F BS       DL: 32    00 00 00 00 00 00 00 df 02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 ea f1 6c eb    Channel: can0
            msg_id = msg_str[41:42]
            msg_idall = msg_str[41:44]
            msg_rt = msg_str[50:52]
            if(msg_id=="4"):
                count_id4 = count_id4 + 1

            elif(msg_idall=="0d7"):
                global_rec_msg = msg_str
                nowtime = time.ctime()
                can_msg_vel = msg_str[81:83]+msg_str[84:86]
                now_vel = int(can_msg_vel.lower(),16)*0.01
                log_msg = "Rx,"+ nowtime + " ,"+ global_rec_msg
                logmake.Log_make(file_log_name,log_msg)#logファイルの作成
                logmake.Log_make(file_log_name,'++++++++++++++++++++++++++++++++++++')#logファイルの作成
                count_id4 = 0
                msg_rec_flg = 1

            elif(msg_idall=="030"):
                global_rec_msg = msg_str
                nowtime = time.ctime()
                can_msg_str = msg_str[87:89]+msg_str[90:91]#5.4~12bit
                cal_str = int(can_msg_str.lower(),16)
                if cal_str > 2048:
                    cal_str = cal_str - 4096
                now_str = cal_str * 1.5
                log_msg = "Rx,"+ nowtime + " ,"+ global_rec_msg
                logmake.Log_make(file_log_name,log_msg)#logファイルの作成
                count_id4 = 0
                msg_rec_flg = 1

            elif(msg_idall=="1d5"):
                global_rec_msg = msg_str
                nowtime = time.ctime()
                print("msg_str==",msg_str)
                can_msg_sft = msg_str[78:80]
                cal_sft = bin(int(can_msg_sft.lower(),16))[-3:]
                print(cal_sft)
                log_msg = "Rx,"+ nowtime + " ,"+ global_rec_msg
                logmake.Log_make(file_log_name,log_msg)#logファイルの作成
                count_id4 = 0
                msg_rec_flg = 1

            elif(msg_rt=="Rx"):
                global_rec_msg = msg_str
                nowtime = time.ctime()

                log_msg = "Rx,"+ nowtime + " ,"+ global_rec_msg
                logmake.Log_make(file_log_name,log_msg)#logファイルの作成
                count_id4 = 0
                msg_rec_flg = 1

            elif(msg_rt=="Tx"):
                nowtime = time.ctime()
                log_msg = "Tx,"+ nowtime + " ,"+ msg_str
                logmake.Log_make(file_log_name,log_msg)#logファイルの作成

            send_vehicledata = can_msg_vel + can_msg_str + can_msg_sft
            print("send_vehicledata = ",send_vehicledata)


        #except:
         #   print("[error]can0 can't receive can_msg (l.728)")

    elif mode == "tcp":
        print("MODE : tcp reveive mode")
    #     tcp_ip,tcp_port, tcp_timeout =config.TCP_Setting_Read()
    #     test=TCPconnect(ip=tcp_ip,port=tcp_port,timeout=tcp_timeout)
    #     #print("end_flg = ",end_flg)
    #     HOST = "127.0.0.10"
    #     PORT = int(tcp_port)
    #     client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #
    #     shift_data = "01"
    #     accel_data = "00"
    #     speed_data = "0000"
    #     stearing_data = "0000"
    #     send_message = ""
    #     send_message = shift_data + accel_data + speed_data + stearing_data
        while end_flg == 0:
            try:
                send_vehicledata = str(tgt_acc) + str(tgt_str)
    #             shift_data = "01"
    #             print("tgt_acc = ",tgt_acc)
    #             print("tgt_str = ",tgt_str)

                # formatted_tgt_acc = "{:08.3f}".format(tgt_acc*1000)
                # accel_data = str(formatted_tgt_acc)
                # speed_data = "0000"
                # formatted_tgt_str = "{:08.3f}".format(tgt_str)

                # formatted_tgt_acc = "{:08}".format(int(tgt_acc*1000))
                # accel_data = str(formatted_tgt_acc)
                # speed_data = "0000"
                # formatted_tgt_str = "{:08}".format(int(tgt_str))


                # stearing_data = str(formatted_tgt_str)
                # print("acc_data = ",accel_data)
                # print("str_data = ",stearing_data)
                # send_message = shift_data + accel_data + speed_data + stearing_data
                # print("send_data = ",send_message)
                # print(send_message + "  port:" + str(PORT))
                #client.sendto(send_message.encode('utf-8'),(HOST,PORT))
                time.sleep(0.1)

            # except:
            #     if end_flg == 1:
            #         print('Connect TCP failed and end loop because endflg = 1')
            except KeyboardInterrupt:
                print(exit)

    else:
        print("[error] mode nothing")
    print('thre1_finish')

def thread02():#GUI

    print('thre2_start')
    gui_main()
    print('thre2_finish')

def thread03():#RCD
    print('thre3_start')
    global global_rec_msg,nowtime,msg_rec_flg,mode,end_flg,go_flg,safety_flg,tgt_acc,tgt_str,joycon_flg,global_now_msg
    global send_vehicledata,can_msg_flg,command_canorcanfd,command_can_id,command_can_data,command_send_flg
    while end_flg == 0:
        time.sleep(1)
        if safety_flg == 1:
            # IPaddress, Port, Time_Out =config.Setting_File_Read()
            IPaddress = "127.0.0.1"
            Port = 9999
            Time_Out = 1
            print("MODE : safety mode start  Port:",Port)
            # test=TCPconnect(ip=IPaddress,port=Port,timeout=Time_Out)
            while end_flg == 0 and safety_flg == 1:
                try:
                    # msg_receive = test.Server()
                    # msg_receive = msg_receive.decode("utf-8")
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as Socket0:
                        Socket0.bind(("", int(Port)))
                        Socket0.listen()
                        print('Waiting for data from client...')
                        Socket0.settimeout(int(Time_Out))
                        #Socket0.settimeout(Time_Out) # 10秒のタイムアウトを設定
                        conn, addr = Socket0.accept()
                        with conn:
                            while end_flg == 0 and safety_flg == 1:
                                try:
                                    conn.settimeout(int(Time_Out))
                                    Receive0 = conn.recv(1024)
                                    # msg_receive = conn.recv(1024)
                                    msg_receive = Receive0
                                    print('Received from client: ' , Receive0 )
                                    # Send0 = b'I received [' + Receive0 + b'] from client'
                                    Send0 = b'I received [' + send_vehicledata.encode() + b'] from vehicle'
                                    #Send0 = b'binary'+ send_message + 'I received [' + Receive0 + b'] from client'
                                    print('Reply to client: ' , Send0 )
                                    conn.sendall(Send0)
                                    global_now_msg = "TCP通信中"
                                    print("TCP receive message = ",msg_receive)
                                    msg_receive = msg_receive.decode('utf-8')
                                    print("TCP receive message after decode = ",msg_receive)
                                    if msg_receive[0:7]=="command":
                                        command_canorcanfd, command_can_id, command_can_data = command_joycon.command_joycon(msg_receive)
                                        command_send_flg = 1

                                    elif msg_receive == None:
                                        go_flg = 0
                                        log_msg = "[Safety]TCP not receive,"+ nowtime
                                        logmake.Log_make(file_log_name,log_msg)#logファイルの作成

                                    elif msg_receive == "stop":
                                        go_flg = 0
                                        log_msg = "[Safety]TCP receive,"+ nowtime + " , receive Stop message "
                                        logmake.Log_make(file_log_name,log_msg)#logファイルの作成
                                        can_msg_flg = 0

                                    elif msg_receive == "p":
                                        if now_vel < 0.1:
                                            go_flg = 1
                                            log_msg = "[Safety]TCP receive,"+ nowtime + " , receive change_P message "
                                            logmake.Log_make(file_log_name,log_msg)#logファイルの作成
                                            ####### change P のプログラム作成

                                            fd_data[9-1] = 0xc6
                                            global_now_msg = "【Pレンジ要求】ボタンが押されました。走行OKであれば走行OKボタンを押して再開できます"

                                            #data = [00, 00, 0x40, 00, 00, 00, 00, 00]
                                            #data = [random.randint(0, 255) for _ in range(32)]
                                            ## Construct CAN message
                                            if can_msg_flg == 1:
                                                print("Pレンジ要求を実施")
                                                can_msg_flg = 0
                                                try:
                                                    msg = can.Message(arbitration_id=0x05a, data=fd_data, is_extended_id=False, is_fd=True)
                                                    can1.send(msg)
                                                except:
                                                    print("[error]can't send message to can device (l.468_Pレンジ要求)")
                                                time.sleep(1)
                                                can_msg_flg = 0

                                        else:
                                            print("NG)Pレンジ要求がされましたが車速が０でないためPにできません")
                                            global_now_msg = "【NG)Pレンジ要求】車速を０にしてください"

                                    elif msg_receive == "r":
                                        if now_vel < 0.1:
                                            go_flg = 1
                                            log_msg = "[Safety]TCP receive,"+ nowtime + " , receive change_R message "
                                            logmake.Log_make(file_log_name,log_msg)#logファイルの作成
                                            ####### change P のプログラム作成

                                            fd_data[9-1] = 0xa6
                                            global_now_msg = "【Rレンジ要求】ボタンが押されました。"

                                        else:
                                            print("NG)Rレンジ要求がされましたが車速が０でないためPにできません")
                                            global_now_msg = "【NG)Rレンジ要求】車速を０にしてください"

                                    elif msg_receive == "d":
                                        if now_vel < 0.1:
                                            go_flg = 1
                                            log_msg = "[Safety]TCP receive,"+ nowtime + " , receive change_R message "
                                            logmake.Log_make(file_log_name,log_msg)#logファイルの作成
                                            ####### change P のプログラム作成

                                            fd_data[9-1] = 0x66
                                            global_now_msg = "【Rレンジ要求】ボタンが押されました。"

                                        else:
                                            print("NG)Rレンジ要求がされましたが車速が０でないためPにできません")
                                            global_now_msg = "【NG)Rレンジ要求】車速を０にしてください"

                                    elif msg_receive == "finish":
                                        end_flg = 0
                                        log_msg = "[Safety]TCP receive,"+ nowtime + " , receive Finish message "
                                        logmake.Log_make(file_log_name,log_msg)#logファイルの作成
                                    else:
                                        can_msg_flg = 1
                                        log_msg = "[Safety]TCP receive,"+ nowtime + " ,"+ str(msg_receive)
                                        logmake.Log_make(file_log_name,log_msg)#logファイルの作成

                                        tcp_accel = msg_receive[0:4]
                                        print("tcp_accel",tcp_accel)
                                        tcp_accel = int(tcp_accel.lower(),16)
                                        if tcp_accel > 32768:
                                            tcp_accel = tcp_accel - 65536
                                        print("tcp_accel",tcp_accel)
                                        tcp_accel = tcp_accel / 1000
                                        print("tcp_accel",tcp_accel)
                                        tgt_acc = tcp_accel
                                        if tgt_acc > Maxvelocity:
                                            tgt_acc = Maxvelocity

                                        # message1 = "tgt_acc = "+tgt_acc + " / tcp_acc = "+tcp_accel
                                        # print(message1)

                                        tcp_str = msg_receive[4:8]
                                        tcp_str = int(tcp_str.lower(),16)
                                        if tcp_str > 32768:
                                            tcp_str = tcp_str - 65536
                                        tcp_str = tcp_str * 1.5
                                        tgt_str = tcp_str
                                        if tgt_str > Maxstearing:
                                            tgt_str = Maxstearing
                                        if tgt_str < -1 * Maxstearing:
                                            tgt_str = -1 * Maxstearing

                                except ConnectionResetError:
                                    break
                                except BrokenPipeError:
                                    break
                            global_now_msg = "TCP通信が途絶しました"
                            Socket0.close()
                            time.sleep(.01)

                        # message2 = "tgt_str = "+tgt_str + " / tcp_str = "+tcp_str
                        # print(message2)

                except:
                    print("[error]TCPconnect error")
                    #go_flg = 0
                    tgt_acc = -1.0
                    log_msg = "[Safety]TCP not receive,"+ nowtime
                    logmake.Log_make(file_log_name,log_msg)#logファイルの作成
                    global_now_msg = "TCP通信ができません"
                    # time.sleep(Time_Out)


        elif joycon_flg == 1:
            pygame.joystick.init()
            joystick0 = pygame.joystick.Joystick(0)
            joystick0.init()
            print('joystick start')
            pygame.init()
            x=0;
            y=0;
            while True:
                 # コントローラーの操作を取得
                eventlist = pygame.event.get()

                # イベント処理
                for e in eventlist:
                    if e.type == QUIT:
                        return

                    if e.type == pygame.locals.JOYAXISMOTION:
                        x, y = joystick0.get_axis(0), joystick0.get_axis(1)
                        print ('axis x:' + str(x) + ' axis y:' + str(y))
                    elif e.type == pygame.locals.JOYHATMOTION:
                        x, y = joystick0.get_hat(0)
                        print('hat x:' + str(x) + ' hat y:' + str(y))
                    # elif e.type == pygame.locals.JOYBUTTONDOWN:
                    #     print ('button:' + str(e.button))
                button_acc = joystick0.get_button(1)
                button_blake = joystick0.get_button(0)

                if button_acc == 1:
                    if tgt_acc <= 0:
                        tgt_acc = 0.1*joycon_acc
                    elif tgt_acc>0:
                        tgt_acc += 0.1*joycon_acc
                elif button_blake == 1:
                    tgt_acc = tgt_acc - (0.1 * joycon_acc)

                if (x>0.1 or x<-0.1):
                    tgt_str = tgt_str + (10 * x * joycon_str)
                # time.sleep(0.01)

    print('thre3_finish')

if __name__ == '__main__':
    print('main program start  ' + '  Version :' + version)
    logmake.Log_init(file_log_name)#logファイルの作成
    log_msg = "Create log file ( nowtime :"+ nowtime + " )"
    logmake.Log_make(file_log_name,log_msg)#logファイルの作成
    #mode = "tcp"#tcp or can
    thread1 = threading.Thread(target=thread01)#msg_receive
    thread2 = threading.Thread(target=thread02)#gui_main
    thread3 = threading.Thread(target=thread03)
    thread1.start()
    thread2.start()
    if safety_mode == "ON":
        thread3.start()
    thread2.join()#thread2が終わったら次に進む
    end_flg = 1;
    thread1.join()#thread2が終わったら次に進む

    if safety_mode == "ON":
        thread3.join()#thread2が終わったら次に進む
    print('main program finish')
