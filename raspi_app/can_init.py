import sys
import os
import can

def CAN_init():
    try:
        os.system('sudo ifconfig can0 down')
        os.system('sudo ifconfig can1 down')
        #os.system('sudo ip link set can0 type can bitrate 500000')#500kbpsトヨタ仕様
        #os.system('sudo ip link set can1 type can bitrate 500000')#500kbpsトヨタ仕様
        #os.system('sudo ip link set can0 type can bitrate 500000   dbitrate 8000000 restart-ms 1000 berr-reporting on fd on')
        os.system('sudo ip link set can0 up type can bitrate 500000 sample-point 0.8  dbitrate 2000000 dsample-point 0.7 restart-ms 1000 berr-reporting on fd on')
        os.system('sudo ip link set can1 up type can bitrate 500000 sample-point 0.8  dbitrate 2000000 dsample-point 0.7 restart-ms 1000 berr-reporting on fd on')
        #   dbitrate 8000000 restart-ms 1000 berr-reporting

        os.system('sudo ifconfig can0 up')
        os.system('sudo ifconfig can1 up')
        #os.system('sudo ifconfig can0 txqueuelen 1000000')
        os.system('sudo ifconfig can0 txqueuelen 65536')
        os.system('sudo ifconfig can1 txqueuelen 65536')

    except:
        print('【error】CAN initialize error')

def can_send(send_msg):
    cansendmessage = "cansend can1 "+ send_msg
    os.system(cansendmessage)


if __name__ == '__main__':
    #test=LOG(logname='logname1',logmessage="logmessage1")
    CAN_init()
    can_filters = [{"can_id":0x700,"can_mask":0x7F0}]
    can0 = can.interface.Bus(channel = 'can0', bustype='socketcan', bitrate=500000, canfilters=None)
    can1 = can.interface.Bus(channel = 'can1', bustype='socketcan', bitrate=500000, canfilters=None)
