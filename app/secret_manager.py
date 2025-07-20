import sqlite3
from cryptography.fernet import Fernet
import os # Added for path handling

class SecretManagerDB:
 
    def __init__(self, db_file='secrets.db', key_file='secret.key'):
        base_dir = os.path.abspath(os.path.dirname(__file__)) # This line
        self.db_file = os.path.join(base_dir, db_file) # This line
        self.key_file = os.path.join(base_dir, key_file) # This line

        self.key = self.load_key()
       #this s the old sqlite3 connection
       # self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
       #self.create_table()
    def load_key(self):
        try:
            with open(self.key_file, 'rb') as f:
                key = f.read()
                return key
        except FileNotFoundError:
            key = Fernet.generate_key()
            try:
                os.makedirs(os.path.dirname(self.key_file), exist_ok=True)
                with open(self.key_file, 'wb') as f:
                    f.write(key)
                os.chmod(self.key_file, 0o664) # Set permissions after creation
                return key
            except Exception as e:
                import logging
                logging.basicConfig(level=logging.ERROR)
                logging.error(f"Error generating/saving key to {self.key_file}: {e}")
                raise
    def encrypt(self, data):
        f = Fernet(self.key)
        encrypted = f.encrypt(data.encode())
        return encrypted.decode()

    def decrypt(self, token):
        f = Fernet(self.key)
        decrypted = f.decrypt(token.encode())
        return decrypted.decode()

    def save_secret(self, name, secret_value):
        encrypted_value = self.encrypt(secret_value)
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO secrets (name, encrypted_value)
            VALUES (?, ?)
            ON CONFLICT(name) DO UPDATE SET encrypted_value=excluded.encrypted_value
        ''', (name, encrypted_value))
        self.conn.commit()

    def get_all_secrets(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT name, encrypted_value FROM secrets')
        rows = cursor.fetchall()
        return [(name, self.decrypt(enc_val)) for name, enc_val in rows]

    def delete_secret(self, name):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM secrets WHERE name = ?', (name,))
        self.conn.commit()

if __name__ == "__main__":
    sm = SecretManagerDB()
    sm.save_secret('db_password', 'mySuperSecret123!')
    print("Decrypted secret:", sm.get_all_secrets())
