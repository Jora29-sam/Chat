import mysql.connector
from mysql.connector import Error

# Configura según tus datos
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
        print(f"[DB ERROR] {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_last_messages(limit=20):
    """
    Recupera los últimos `limit` mensajes del chat ordenados por fecha ascendente.
    """
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT username, message, timestamp FROM messages ORDER BY timestamp ASC LIMIT %s",
            (limit,)
        )
        return cursor.fetchall()
    except Error as e:
        print(f"[DB ERROR] get_last_messages: {e}")
        return []
    finally:
        cursor.close()
        conn.close()
