#import sys
#import os

def Log_init(logname):
    try:
        print("logname = ",logname)
        f = open(logname, "x")#r:読み取り、w:上書き、a:追記
        f.close()
    except:
        print('Log create error (同じファイル名が存在)')
def Log_make(logname,logmessage):
    try:
        f = open(logname, "a")#r:読み取り、w:上書き、a:追記
        f.write(str(logmessage))
        #f.write(text)
        f.write("\n")
        f.close()

    except:
        print('Log make error')

if __name__ == '__main__':
    #test=LOG(logname='logname1',logmessage="logmessage1")
    Log_init("logname2")
    Log_make("logname2","logmessage2")
