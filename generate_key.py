from cryptography.fernet import Fernet

# Generar y guardar la clave secreta
def generate_secret_key():
    key = Fernet.generate_key()
    with open("secret.key", "wb") as key_file:
        key_file.write(key)

if __name__ == "__main__":
    generate_secret_key()
    print("Clave secreta generada y guardada en 'secret.key'")
