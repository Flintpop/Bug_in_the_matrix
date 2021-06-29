from cryptography.fernet import Fernet


class Encrypt:
    def __init__(self):
        self.write_key()

        self.one = "".encode()
        self.two = "".encode()

        self.key = self.load_key()

        # initialize the Fernet class
        self.f = Fernet(self.key)
        self.encrypted = self.f.encrypt(self.one)
        self.encrypted_two = self.f.encrypt(self.two)

        self.write_data()

    def get_data_one(self):
        return str(self.f.decrypt(self.encrypted)).replace("b", " ").strip()

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
            file.write(self.f.encrypt(self.one))
            file.write("\n".encode())
            file.write(self.f.encrypt(self.two))
            file.write("\n".encode())


class GetData:
    @staticmethod
    def load_key():
        return open("key.key", "rb").read()

    @staticmethod
    def get_data(key):
        f = open("some_data.txt", "r")
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
