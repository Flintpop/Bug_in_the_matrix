import os.path

from cryptography.fernet import Fernet
from src.Miscellaneous.print_and_debug import os_path_fix


class Encrypt:
    def __init__(self):
        self.write_key()

        self.api_key = "".encode()
        self.secret_key = "".encode()

        self.key = GetData.load_key()

        # initialize the Fernet class
        self.f = Fernet(self.key)
        self.encrypted = self.f.encrypt(self.api_key)
        self.encrypted_two = self.f.encrypt(self.secret_key)

        self.write_data()

    def get_data_one(self):
        return str(self.f.decrypt(self.encrypted)).replace("b", " ").strip()

    @staticmethod
    def encrypt_file(file):
        f = open(os_path_fix() + file, "r")
        content = f.read()
        fernet = Fernet(GetData.get_password().encode())
        content = fernet.encrypt(content.encode()).decode()
        f.close()
        f = open(os_path_fix() + file.strip(".txt") + "_encrypted.txt", 'w')
        f.write(str(content))
        f.close()

    @staticmethod
    def write_key(key_input=""):
        if key_input == "":
            key = Fernet.generate_key()
        else:
            key = key_input
        with open(os_path_fix() + "key.key", "wb") as key_file:
            if type(key) == str:
                key_file.write(key.encode())
            else:
                key_file.write(key)

    def write_data(self):
        with open("some_data.txt", "wb") as file:
            file.write(self.f.encrypt(self.api_key))
            file.write("\n".encode())
            # file.write(self.f.encrypt(self.secret_key))
            # file.write("\n".encode())


class GetData:
    password: str

    @staticmethod
    def load_key():
        key = open(os_path_fix() + "key.key", "rb").read()
        print(type(key))

        return open(os_path_fix() + "key.key", "rb").read()

    @staticmethod
    def get_data(key, file: str):
        path = os_path_fix() + file
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
        if os.path.exists(os_path_fix() + "key.key"):
            password = keys.load_key()
        else:
            password = GetData.get_password()
            Encrypt.write_key(password)

        key = keys.get_data(password, "some_data.txt")
        return key

    @staticmethod
    def get_email_password():
        keys = GetData()
        if os.path.exists(os_path_fix() + "key.key"):
            password = keys.load_key()
        else:
            raise Exception("No file key.key found")
        key = keys.get_data(password, "password_email_encrypted.txt")
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
    def decrypt_file(file, key: bytes):
        print(key)
        k = Fernet(key)
        f = open(os_path_fix() + file, "r")
        content = f.read()
        print(content)
        decrypted = k.decrypt(bytes(content.encode())).decode()
        f.close()
        with open(os_path_fix() + file.strip(".txt") + "_decrypted", "w+") as f:
            f.write(str(decrypted))
        f.close()


if __name__ == '__main__':
    GetData()
