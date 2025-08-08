import socket 

class CryptoSocketServer:
    def __init__(self, address= '0.0.0.0', port=14021):
        self.address= address
        self.port= port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.address, self.port))
        self.sock.listen(5)
        print(f"Python Socket Server started at {self.address}:{self.port}")

    def start(self):
        while True:

            conn, addr = self.sock.accept()
            print("Connected by {addr}")
            try:
                data=conn.recv(10000)
                if not data:
                    print("No data received")
                    continue
                decoded = data.decode('utf-8').strip()
                self.handle_data(decoded)

                conn.send(b"RECEIVES")
            except Exception as e:
                print(f"Error: {e}")
            finally:
                conn.close()
    def handle_data(self, msg):
        try:
            symbol , prices_tr = msg.split('|', 1)
            prices= [float(p) for p in prices_tr.strip().split()]
            print(f"Data received for {symbol}: {len(prices)} prices")
        except Exception as e:
            print(f"Failed to parse message: {msg}\nError: {e}")

if __name__== '__main__':
    server = CryptoSocketServer()
    server.start()