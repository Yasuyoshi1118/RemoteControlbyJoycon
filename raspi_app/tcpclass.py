import socket
import time
import sys
import os

class TCPconnect():
    def __init__(self, ip, port,timeout):
        self.ip = ip
        self.port = int(port)
        self.timeout = int(timeout)
        print("ip = ",self.ip)
        print("port = ",self.port)
        print("timeout = ",self.timeout)

    def Client(self):
        print('')
        x = input('Input message and press enter: ')

        try:
            Socket1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  #// AF_INET=IPv4, SOCK_STREAM=TCP/IP
            Socket1.settimeout(5)
            Socket1.connect((self.ip, self.port))
            Socket1.sendall(bytes(x,'utf-8'))
            Receive1 = Socket1.recv(1024)
            print('Received from server: ' ,Receive1 )
            Socket1.close()
            return Receive1

        except:
            print('Server connection error')

    def Server(self):
        try:
            print('')
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as Socket0:
                Socket0.bind(("", self.port))
                Socket0.listen()
                print('Waiting for data from client...')
                print(self.port)
                Socket0.settimeout(self.timeout)
                try:
                    conn, addr = Socket0.accept()
                    with conn:
                        Receive0 = conn.recv(1024)
                        #print('Received from client: ' , Receive0 )
                        Send0 = b'I received [' + Receive0 + b'] from client'
                        #print('Reply to client: ' , Send0 )
                        conn.sendall(Send0)
                        Socket0.close()
                        time.sleep(.1)
                        return Receive0
                except:
                    print("TCP通信のコネクト失敗（タイムアウト）")
        except KeyboardInterrupt:
            print("プログラムが強制終了されました。")



if __name__ == '__main__':
    test=TCPconnect(ip='127.0.0.1',port=9000,timeout=60)
    test.Server()
