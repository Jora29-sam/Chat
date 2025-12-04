import socket
import threading
import time
import db_handlerF as db_handlerF

HOST = '0.0.0.0'
PORT = 5001
clients = {}

def save_message(username, message):
    conn = db_handlerF.get_connection()
    if not conn:
        print("[DB ERROR] No se pudo conectar para guardar mensaje")
        return
    try:
        cursor = conn.cursor()
        query = "INSERT INTO messages (username, message, timestamp) VALUES (%s, %s, NOW())"
        cursor.execute(query, (username, message))
        conn.commit()
    except Exception as e:
        print(f"[DB ERROR] Guardar mensaje: {e}")
    finally:
        cursor.close()
        conn.close()

def broadcast(message, sender_socket=None):
    for client in list(clients):
        if client != sender_socket:
            try:
                client.sendall(message.encode())
            except:
                client.close()
                del clients[client]

def handle_client(client_socket, address):
    print(f"[+] Conectado desde {address} (servidor espejo)")
    try:
        client_socket.sendall("¿Deseas (1) Registrarte o (2) Iniciar sesión?: ".encode())
        opcion = client_socket.recv(1024).decode().strip()

        if opcion == "1":
            client_socket.sendall("Nuevo usuario: ".encode())
            new_user = client_socket.recv(1024).decode().strip()

            client_socket.sendall("Nueva contraseña: ".encode())
            new_pass = client_socket.recv(1024).decode().strip()

            client_socket.sendall("Rol (client/moderator): ".encode())
            new_role = client_socket.recv(1024).decode().strip()

            if db_handlerF.register_user(new_user, new_pass, new_role):
                client_socket.sendall(" Registro exitoso. Ahora inicia sesión.\nUsuario: ".encode())
            else:
                client_socket.sendall(" Error: Usuario ya existe. Intenta con otro.\nUsuario: ".encode())

        username = client_socket.recv(1024).decode().strip()
        client_socket.sendall("Contraseña: ".encode())
        password = client_socket.recv(1024).decode().strip()

        if not db_handlerF.authenticate_user(username, password):
            client_socket.sendall("ERROR: Usuario o contraseña incorrectos.".encode())
            client_socket.close()
            return

        role = db_handlerF.get_user_role(username)
        client_socket.sendall(f"Bienvenido {username} ({role})".encode())
        clients[client_socket] = username

        while True:
            data = client_socket.recv(1024).decode().strip()
            if not data:
                break

            if data.startswith("/changepass"):
                parts = data.split(" ", 1)
                if len(parts) != 2:
                    client_socket.sendall("Uso: /changepass nueva_contraseña".encode())
                    continue
                new_pass = parts[1]
                if db_handlerF.update_password(username, new_pass):
                    client_socket.sendall(" Contraseña actualizada.".encode())
                else:
                    client_socket.sendall(" Error actualizando contraseña.".encode())
                continue

            if data.startswith("/"):
                if role != "moderator":
                    client_socket.sendall(" No tienes permisos para usar comandos especiales.".encode())
                    continue

                if data.startswith("/kick"):
                    try:
                        _, target_user = data.split(" ", 1)
                    except:
                        client_socket.sendall(" Uso incorrecto. Usa: /kick nombre_usuario".encode())
                        continue

                    kicked = False
                    for c, u in list(clients.items()):
                        if u == target_user:
                            c.sendall(" Has sido expulsado por un moderador.".encode())
                            c.close()
                            del clients[c]
                            kicked = True
                            break
                    if kicked:
                        client_socket.sendall(f" Usuario {target_user} expulsado.".encode())
                    else:
                        client_socket.sendall(f" Usuario {target_user} no encontrado.".encode())
                    continue

                client_socket.sendall(" Comando no reconocido.".encode())
                continue

            timestamp = time.strftime("%H:%M:%S")
            message = f"[{timestamp}] {username}: {data}"
            print(message)
            save_message(username, data)
            broadcast(message, sender_socket=client_socket)
            client_socket.sendall("ACK".encode())

    except Exception as e:
        print(f"[ERROR] con {address} (backup): {e}")
    finally:
        print(f"[-] Desconectado {address} (backup)")
        if client_socket in clients:
            del clients[client_socket]
        client_socket.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[🟠] Servidor espejo escuchando en {HOST}:{PORT}")

    try:
        while True:
            client_socket, address = server.accept()
            thread = threading.Thread(target=handle_client, args=(client_socket, address))
            thread.start()
    except KeyboardInterrupt:
        print("\n[!] Servidor espejo detenido manualmente.")
    finally:
        server.close()

if __name__ == "__main__":
    main()
