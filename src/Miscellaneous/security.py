from cryptography.fernet import Fernet
from src.Miscellaneous.print_and_debug import os_path_fix


class Encrypt:
    def __init__(self):
        self.write_key()

        self.api_key = "".encode()
        self.secret_key = "".encode()

        self.key = self.load_key()

        # initialize the Fernet class
        self.f = Fernet(self.key)
        self.encrypted = self.f.encrypt(self.api_key)
        self.encrypted_two = self.f.encrypt(self.secret_key)

        self.write_data()

    def get_data_one(self):
        return str(self.f.decrypt(self.encrypted)).replace("b", " ").strip()

    def encrypt_file(self, file):
        f = open(file, "r")
        content = f.read()
        content = self.f.encrypt(content.encode())
        f.close()
        f = open(file, 'w')
        f.write(str(content))
        f.close()

    @staticmethod
    def write_key():
        key = Fernet.generate_key()
        with open("key.key", "wb") as key_file:
            key_file.write(key)

    @staticmethod
    def load_key():
        return open("key.key", "rb").read()

    def write_data(self):
        with open("some_data.txt", "wb") as file:
            file.write(self.f.encrypt(self.api_key))
            file.write("\n".encode())
            file.write(self.f.encrypt(self.secret_key))
            file.write("\n".encode())


class GetData:
    @staticmethod
    def load_key():
        return open("key.key", "rb").read()

    @staticmethod
    def get_data(key):
        path = os_path_fix() + "some_data.txt"
        f = open(path, "r")
        k = Fernet(key)
        infos = []
        decrypted = []
        for x in f:
            infos.append(x)
        for items in infos:
            temp = k.decrypt(bytes(items.encode())).decode()
            decrypted.append(temp)
        f.close()
        return decrypted

    @staticmethod
    def login():
        keys = GetData()
        password = GetData.get_password()
        key = keys.get_data(password)
        return key

    @staticmethod
    def get_password():
        import platform
        current_os = platform.system()

        if current_os == 'Windows':
            password = input("Please enter the password : ")
        elif current_os == 'Linux' or current_os == 'Darwin':
            from getpass import getpass
            password = getpass()
        else:
            raise print("CRITICAL ERROR: could not determine the os.")
        return password

    @staticmethod
    def decrypt_file(file, key):
        k = Fernet(key)
        f = open(file, "r")
        content = f.read()
        print(content)
        decrypted = k.decrypt(bytes(content.encode())).decode()
        f.close()
        with open("test3.py", "w+") as f:
            f.write(str(decrypted))
        f.close()


if __name__ == '__main__':
    Encrypt()
