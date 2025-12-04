import socket
import threading
import json
from datetime import datetime
from mysql.connector import Error
import mysql.connector

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Satoru2412*',
    'database': 'chat_system'
}

def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"[DB ERROR] {e}")
        return None

def register_user(username, password, role):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return False  # Usuario ya existe
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
            (username, password, role)
        )
        conn.commit()
        return True
    except Error as e:
        print(f"[DB ERROR] {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def authenticate_user(username, password):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()
        return result and result[0] == password
    except Error as e:
        print(f"[DB ERROR] {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_user_role(username):
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Error as e:
        print(f"[DB ERROR] {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def update_password(username, new_password):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password = %s WHERE username = %s", (new_password, username))
        conn.commit()
        return True
    except Error as e:
        print(f"[DB ERROR] update_password: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def save_message_to_db(username, msg_text):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (username, message) VALUES (%s, %s)",
            (username, msg_text)
        )
        conn.commit()
        return True
    except Error as e:
        print(f"[DB ERROR] save_message_to_db: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_last_messages(limit=50):
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT username, message, timestamp FROM messages ORDER BY timestamp DESC LIMIT %s",
            (limit,)
        )
        rows = cursor.fetchall()
        return rows[::-1]  # ordenar ascendente por timestamp
    except Error as e:
        print(f"[DB ERROR] get_last_messages: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

clients = []  # lista global de clientes conectados

class ClientThread(threading.Thread):
    def __init__(self, client_socket, addr):
        threading.Thread.__init__(self)
        self.client_socket = client_socket
        self.addr = addr
        self.username = None
        self.role = None
        self.connected = True

    def send(self, msg):
        try:
            self.client_socket.sendall(msg.encode())
        except:
            self.connected = False

    def receive(self):
        try:
            data = self.client_socket.recv(2048).decode()
            return data.strip()
        except:
            self.connected = False
            return ""

    def kick_user(self, target_username):
        for client in clients:
            if client.username == target_username and client.connected:
                client.send("Has sido expulsado del servidor por un moderador.\n")
                client.connected = False
                client.client_socket.close()
                broadcast(f"*** {target_username} ha sido expulsado por un moderador ***", "Server")
                return True
        return False

    def run(self):
        try:
            # Login or Register
            self.send("¿Quieres registrarte (1) o iniciar sesión (2)? ")
            option = self.receive()
            if option == "1":
                self.send("Nombre de usuario para registro: ")
                new_user = self.receive()
                self.send("Contraseña: ")
                new_pass = self.receive()
                self.send("Rol (client/moderator): ")
                new_role = self.receive()
                while new_role not in ("client", "moderator"):
                    self.send("Rol inválido. Escribe 'client' o 'moderator': ")
                    new_role = self.receive()
                if register_user(new_user, new_pass, new_role):
                    self.send("Registro exitoso. Ahora inicia sesión.\n")
                else:
                    self.send("Error: usuario ya existe o problema con DB. Cerrando conexión.\n")
                    self.client_socket.close()
                    return

            self.send("Nombre de usuario: ")
            username = self.receive()
            self.send("Contraseña: ")
            password = self.receive()

            if not authenticate_user(username, password):
                self.send("ERROR: Usuario o contraseña incorrectos.\n")
                self.client_socket.close()
                return

            self.username = username
            self.role = get_user_role(username)
            self.send(f"Bienvenido {self.username} ({self.role})\n")
            broadcast(f"*** {self.username} se ha unido al chat ***", "Server")

            while self.connected:
                data = self.receive()
                if not data:
                    break

                # Comandos especiales
                if data.startswith("/"):
                    if data.startswith("/kick "):
                        if self.role != "moderator":
                            self.send("No tienes permiso para usar este comando.\n")
                            continue
                        target_user = data[6:].strip()
                        if target_user == self.username:
                            self.send("No puedes expulsarte a ti mismo.\n")
                            continue
                        if self.kick_user(target_user):
                            self.send(f"Usuario {target_user} expulsado.\n")
                        else:
                            self.send(f"Usuario {target_user} no encontrado o no está conectado.\n")
                        continue

                    elif data.startswith("/changepass "):
                        new_pass = data[11:].strip()
                        if not new_pass:
                            self.send("Debes especificar una nueva contraseña.\n")
                            continue
                        if update_password(self.username, new_pass):
                            self.send("Contraseña cambiada exitosamente.\n")
                        else:
                            self.send("Error cambiando la contraseña.\n")
                        continue

                    elif data == "/quit":
                        self.send("Desconectando...\n")
                        break

                    elif data == "/history":
                        messages = get_last_messages()
                        if messages:
                            history = "\n".join([f"[{msg[2]}] {msg[0]}: {msg[1]}" for msg in messages])
                        else:
                            history = "No hay mensajes previos."
                        self.send(history + "\n")
                        continue
                    else:
                        self.send("Comando desconocido.\n")
                        continue

                # Mensaje normal: guardarlo y enviarlo
                if save_message_to_db(self.username, data):
                    broadcast(f"{self.username}: {data}", self.username)
                else:
                    self.send("Error guardando mensaje en la base de datos.\n")

        except Exception as e:
            print(f"Error en hilo cliente {self.addr}: {e}")
        finally:
            broadcast(f"*** {self.username} ha salido del chat ***", "Server")
            self.client_socket.close()
            self.connected = False
            clients.remove(self)

def broadcast(message, sender):
    for client in clients:
        if client.connected and client.username != sender:
            try:
                client.send(message + "\n")
            except:
                client.connected = False

def main():
    global clients
    clients = []

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 5000))  # Cambia a 5001 para servidor de respaldo
    server.listen(5)
    print("Servidor principal escuchando en puerto 5000...")

    while True:
        client_socket, addr = server.accept()
        print(f"Conexión de {addr}")
        new_client = ClientThread(client_socket, addr)
        new_client.start()
        clients.append(new_client)

if __name__ == "__main__":
    main()
