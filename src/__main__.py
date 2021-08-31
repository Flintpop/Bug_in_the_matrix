from security import GetData


def os_path_fix(folder):
    import platform
    current_os = platform.system()
    if current_os == 'Windows':
        string = f"src/{folder}/"
    else:
        string = f"../{folder}/"

    return string


if __name__ == '__main__':
    # sec = Encrypt()
    # sec.encrypt_file("Data/test.py")
    # print("Welcome !")
    # print("Please enter the decryption key : ")

    obj = GetData()
    key = input()
    obj.decrypt_file("Data/test.py", key)
