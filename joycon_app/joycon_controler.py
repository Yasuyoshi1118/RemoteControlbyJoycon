import time
import threading
import sys
import socket
import pygame
from pygame.locals import *
import math

# ジョイコンの操作を処理する関数
def joycon_control():
    
    global send_message, receive_message, end_flg, comm_flg
    # 初期値セット
    device_mode = "joycon" # joycon：ジョイコン その他：キーボード
    adjust_accel = 0.1  # 押下時の加速
    adjust_brake = 0.5
    adjust_brake_pmode = 0.1
    # deceleration_rate_accel = 0.001  # 自然減速の調整値 最小が0.001だから
    max_accel = 0.2  # 最大加速度 10が限界かも？らしい
    min_accel = -0.5
    
    adjust_steering = 0.8  #度 押下時の舵角増加 max-2.3度 (60度/100msec = x * 3.14/180 * 1000 * 1.5)
    deceleration_rate_steering = 0.8  # 自然ハンドル戻しの調整値
    max_steering = 360  # 最大舵角 2回転分（720度）

    sleep_time = 0.1

    # try:
    pygame.init()  # Pygameの初期化
    
    if device_mode == "joycon":
        pygame.joystick.init()  # ジョイパッドの初期化
        joystick = pygame.joystick.Joystick(0)  # 最初のジョイパッドを取得
        joystick.init()  # ジョイパッドを初期化
    
    screen = pygame.display.set_mode((300, 300))  # ウィンドウを作成
    tgt_accel = 0  # 目標加速度
    tgt_str = 0  # 目標舵角
    
    button_sequence = [9, 10, 9, 10] # ボタンの押下順を管理するリスト
    game_end_count = 0 #5になったらゲーム終了する
    
    #初期値セット
    finish_button = False
    p_mode_button = False
    
    right_button = False
    left_botton = False
    accel_button = False
    brake_button = False
    sl_button = False
    sr_button = False
    
    car_speed = 0
    car_range = "I don't know"
    
    #入力情報確認フロー
    while True:
        time.sleep(sleep_time)  # 次までの送信間隔 100 msec
        eventlist = pygame.event.get() # イベントリストを取得
        
        # イベント処理
        for e in eventlist:
            if device_mode == "joycon":
                if e.type == pygame.locals.JOYBUTTONDOWN: # 終了イベント
                    if int(e.button) == 5: # homeボタン
                        finish_button = True
                    
                    if int(e.button) == 6: # セレクトボタン
                        p_mode_button = True 
            
            else:
                if e.type == KEYDOWN:
                    if e.key == K_f:
                        finish_button = True
                    
                    if e.key == K_p:
                        p_mode_button = True
                    
                
        # 現在のキーの状態を取得
        keys = pygame.key.get_pressed()
        
        # ジョイコンのボタン状態を取得
        if device_mode == "joycon":
            x_angle = joystick.get_axis(0)  # スティックのX軸
            if x_angle > 0.3:
                right_button = True
            else:
                right_button = False
            if x_angle < -0.3:
                left_button = True
            else:
                left_button = False
            
            accel_button = joystick.get_button(0)  # 丸4つの内 右
            brake_button = joystick.get_button(1)  # 丸4つの内 下
            sl_button = joystick.get_button(9)  # Lボタン
            sr_button = joystick.get_button(10)  # Rボタン
            
        else:
            right_button = keys[K_RIGHT]# 右矢印ボタン
            left_button = keys[K_LEFT]# 左矢印ボタン
                
            accel_button = keys[K_UP]  # 上矢印ボタン
            brake_button = keys[K_DOWN]  # 下矢印ボタン
            sl_button = keys[K_l]  # キーボード L
            sr_button = keys[K_r]  # キーボード R
            
            
        # ボタンの押下順をチェック
        if game_end_count < len(button_sequence):
            if button_sequence[game_end_count] == 9 and sl_button == True:
                game_end_count += 1
            elif button_sequence[game_end_count] == 10 and sr_button == True:
                game_end_count += 1
            elif button_sequence[game_end_count] == 9 and sl_button == True:
                game_end_count += 1
            elif button_sequence[game_end_count] == 10 and sr_button == True:
                game_end_count += 1
                
            # 順番が正しく押された場合
            if game_end_count == len(button_sequence):
                finish_button = True
    
            
        # 加速・減速処理
        if accel_button == True:  # 加速ボタンが押されている
            print('accel_button pressed --> speed up')
            will_message = tgt_accel + adjust_accel
            if will_message <= max_accel:  # 最大加速度以下か判定
                tgt_accel = will_message
            # print("tgt_accel = ", tgt_accel)
            
        elif brake_button == True:  # 減速ボタンが押されている
            print('brake_button pressed --> speed down')
            if tgt_accel > 0:
                tgt_accel = 0
            will_message = tgt_accel - adjust_brake
            if will_message >= min_accel:  # 最小加速度以上か判定
                tgt_accel = will_message
            # print("tgt_accel = ", tgt_accel)
            
        # else:  # 加速も減速も押されていない場合
        #     tgt_accel = -deceleration_rate_accel
        #     # print("tgt_accel (decelerating) = ", tgt_accel)
            
            
        # 舵角処理
        if right_button == True:  # スティックのXベクトルが0以上
            print('right_button pressed --> steering right')
            will_message = tgt_str - adjust_steering
            if abs(will_message) <= max_steering:  # 最大舵角を設定
                tgt_str = will_message
            # print("tgt_str = ", tgt_str)
            
        elif left_button == True:  # スティックのXベクトルが0以下
            print('left_button pressed --> steering left')
            will_message = tgt_str + adjust_steering
            if abs(will_message) <= max_steering:  # 最小舵角を設定
                tgt_str = will_message
            # print("tgt_str = ", tgt_str)
            
        if right_button == False and left_button == False:  # スティックのXベクトルが0の場合
            if tgt_str > 0:
                will_message = tgt_str - deceleration_rate_steering  # 緩やかに中央に向かう
                if will_message > 0:
                    tgt_str = will_message
                else:
                    tgt_str = 0
            elif tgt_str < 0:
                will_message = tgt_str + deceleration_rate_steering  # 緩やかに中央に向かう
                if will_message < 0:
                    tgt_str = will_message
                else:
                    tgt_str = 0
            elif tgt_str == 0:
                None
            # print("tgt_str (centering) = ", tgt_str)
            

        if finish_button == True:
            print('press finish_button --> speed down & change P & progrum finish')
            pygame.quit()
            tgt_accel = - adjust_brake_pmode
            send_message = change_int2hexMSG(tgt_accel, tgt_str)
            receive_message = str(receive_message[12:20], 'utf-8')
            car_speed = int(receive_message[0:4], 16)
            print("car_speed :",car_speed)
            # car_range = receive_message[8:9]
            if car_speed == 0:
                send_message = "p"
                time.sleep(3) #トライ用
                car_range = "p"#トライ用
            if car_range == "p":
                end_flg = 1
            return
            
        if p_mode_button == True:                
            print('press p_mode_button --> speed down & change P')
            tgt_accel = - adjust_brake_pmode
            send_message = change_int2hexMSG(tgt_accel, tgt_str)
            receive_message = str(receive_message[12:20], 'utf-8')
            car_speed = int(receive_message[0:4], 16)
            print("car_speed :",car_speed)
            # car_range = receive_message[8:9]
            if car_speed == 0:
                send_message = "p"
                time.sleep(3) #トライ用
                car_range = "p"#トライ用
            if car_range == "p":
                p_mode_button = False

                
        # メッセージを変換
        # send_message = change_int2hexMSG(tgt_accel, tgt_str)
        send_message = change_int2hexMSG(round(tgt_accel,2), round(tgt_str,2))
        print("send_message_joycon = ", send_message)
        
        comm_flg = comm_flg + 1
        while comm_flg == 3:
            None
        
        
    # except Exception as e:
    #     print(f"An error occurred: {e}")
        
# TCP送信を行うスレッド関数
def tcp_send():
    global send_message, receive_message, end_flg, comm_flg
    ConfigFile_list = ReadConfigFile_func('config.csv')  # 設定ファイルを読み込む
    ip = ConfigFile_list[0]
    port = int(ConfigFile_list[1])
    timeout = float(ConfigFile_list[2])
    
    # 終了フラグが立つまで繰り返す
    while end_flg == 0:
        try:
            socket_info = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP/IPソケットを作成
            socket_info.settimeout(timeout)  # タイムアウト設定
            socket_info.connect((ip, port))  # サーバーに接続
            while end_flg == 0:
                try:
                    time.sleep(0.01)
                    socket_info.sendall(bytes(send_message, 'utf-8'))  # メッセージを送信
                    receive_message = socket_info.recv(1024)  # サーバーからの応答を受信
                    print("send_message_tcp: ", send_message)
                    print('receive_message : ', receive_message)
                    comm_flg = 0
                except:
                    socket_info.close()  # ソケットを閉じる
                    break

        except:
            print('Server connection error / send message = ', send_message)
            
    print("tcp_send finish")

                    
# 加速度と舵角を16進数のメッセージに変換する関数
def change_int2hexMSG(tgt_accel, tgt_str):
    # 加速度の調整
    # print("tgt_accel : ",tgt_accel)
    # print("tgt_str   : ",tgt_str)
    
    if tgt_accel>= 0:
        tgt_acc_adj = (tgt_accel * 1000)
    else:
        tgt_acc_adj = (tgt_accel* 1000) + (2**16)
    # print("tgt_acc_adj   : ",tgt_acc_adj)
    tgt_acc_hex = format(int(tgt_acc_adj), '04X')  # 16進数に変換

    # 舵角の調整
    if tgt_str >= 0:
        tgt_str_adj = (tgt_str * math.pi / 180 * 1000)
    else:
        tgt_str_adj = (tgt_str * math.pi / 180 * 1000) + (2**16)
    # print("tgt_str_adj   : ",tgt_str_adj)
    tgt_str_hex = format(int(tgt_str_adj), '04X')  # 16進数に変換
    
    return_message = tgt_acc_hex + tgt_str_hex  # メッセージを結合
    return return_message

        
# 設定ファイルを読み込む関数
def ReadConfigFile_func(x):
    i = 0
    y = []
    try:
        with open(x,'r') as ConfigFile:
            while True:
                y.append(ConfigFile.readline().replace('\n',''))  # 行を読み込んで改行を削除
                if len(y[i]) == 0 or y[i] == '' or y[i][0] == ',':  # 空行やカンマで始まる行を処理
                    y[i] = 'End'
                    break
                i += 1  # インデックスを増加
            y = y[1].split(',') # データ部(2行目)をスプリットして返す
        return y
    
    except:
        print('Unable to read config file [' + x + ']')
        print('Exit')
        sys.exit()            

    

# メインプログラム
if __name__ == '__main__':
    print('start_program')

    # 初期値ｾｯﾄ
    send_message = "00000000"
    receive_message = ""
    end_flg = 0

    thread1 = threading.Thread(target=tcp_send)  # TCP送信スレッド 
    thread2 = threading.Thread(target=joycon_control)  # ジョイコン制御スレッド
    thread1.start()  # スレッドを開始
    thread2.start()  # スレッドを開始
    thread2.join()  # thread2が終わったら次に進む
    thread1.join()  # thread1が終わるのを待つ
    
    print('end_program')  # プログラム終了メッセージ