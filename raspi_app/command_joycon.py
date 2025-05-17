#import sys
#import os
import time

def command_joycon(msg_receive):

    if msg_receive == "command_hazard":
        canorcanfd = "canfd"
        can_id = 91
        can_data = [00, 00, 0x40, 00, 00, 00, 00, 00]
        return canorcanfd, can_id, can_data
        
    if msg_receive == "command_failhazard":
        canorcanfd = "canfd"
        can_id = 91
        can_data = [00, 00, 0x40, 00, 00, 00, 00, 00]
        return canorcanfd, can_id, can_data
        
    elif msg_receive == "command_horn":
        canorcanfd = "canfd"
        can_id = 91
        can_data = [192, 00, 00, 00, 00, 00, 00, 00]
        return canorcanfd, can_id, can_data
        
    elif msg_receive == "command_lamp":
        canorcanfd = "canfd"
        can_id = 91
        can_data = [32, 00, 00, 00, 00, 00, 00, 00]
        return canorcanfd, can_id, can_data
    
    elif msg_receive == "command_turnleft":
        canorcanfd = "canfd"
        can_id = 91
        can_data = [00, 00, 32, 00, 00, 00, 00, 00]
        return canorcanfd, can_id, can_data
        
        
    elif msg_receive == "command_turnright":
        canorcanfd = "canfd"
        can_id = 91
        can_data = [00, 00, 16, 00, 00, 00, 00, 00]
        return canorcanfd, can_id, can_data

    elif msg_receive == "command_openwindow":
        canorcanfd = "subcan"
        can_id = "750#40"
        can_data = "062F2842030180"
        return canorcanfd, can_id, can_data

    else:
        print('存在しないコマンドです')
        canorcanfd = None
        can_id = None
        can_data = None
        return canorcanfd, can_id, can_data


if __name__ == '__main__':
    #test=LOG(logname='logname1',logmessage="logmessage1")
    canorcanfd, can_id, can_data = command_joycon("command_hazard")
    print(canorcanfd)
    print(can_id)
    print(can_data)
    time.sleep(1)
    canorcanfd, can_id, can_data = command_joycon("ddd")
    print(canorcanfd)
    print(can_id)
    print(can_data)
