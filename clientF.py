import socket
import threading
import time

SERVER_PRIMARY = ('172.20.10.4', 5000)
SERVER_BACKUP = ('172.20.10.11', 5001)
RECONNECT_DELAY = 5  # segundos entr2e intentos de reconexión

class ChatClient:
    def __init__(self):
        self.sock = None
        self.connected_server = None
        self.running = True

    def connect_to_server(self):
        for server in [SERVER_PRIMARY, SERVER_BACKUP]:
            try:
                print(f"Intentando conectar a {server[0]}:{server[1]}...")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect(server)
                print(f"Conectado a {server[0]}:{server[1]}")
                self.connected_server = server
                return sock
            except Exception as e:
                print(f"No se pudo conectar a {server[0]}:{server[1]} - {e}")
        return None

    def receive_messages(self):
        while self.running:
            try:
                data = self.sock.recv(2048).decode()
                if not data:
                    print("Conexión cerrada por el servidor.")
                    self.sock.close()
                    self.sock = None
                    break
                print(data)
            except Exception:
                print("Error al recibir datos del servidor.")
                if self.sock:
                    self.sock.close()
                    self.sock = None
                break

    def run(self):
        while self.running:
            if not self.sock:
                self.sock = self.connect_to_server()
                if not self.sock:
                    print(f"No se pudo conectar a ningún servidor, reintentando en {RECONNECT_DELAY} segundos...")
                    time.sleep(RECONNECT_DELAY)
                    continue
                threading.Thread(target=self.receive_messages, daemon=True).start()

            try:
                msg = input()
                if msg.lower() == "/quit":
                    self.sock.sendall(msg.encode())
                    print("Desconectando...")
                    self.running = False
                    break
                else:
                    self.sock.sendall(msg.encode())
            except Exception:
                print("Error enviando mensaje, intentando reconectar...")
                if self.sock:
                    self.sock.close()
                    self.sock = None

if __name__ == "__main__":
    client = ChatClient()
    client.run()
