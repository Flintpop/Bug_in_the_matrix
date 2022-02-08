import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from time import sleep
import datetime
from src.Miscellaneous.settings import Parameters


def send_email(word, subject="Update in your project"):
    port = 587  # For starttls
    smtp_server = "smtp.gmail.com"
    sender_email = 'bestfriendnotifier@gmail.com'
    receiver_email = 'bestfriendnotifier@gmail.com'
    password = 'lkkuxirbnhtpcavg'
    html = u"""\
    <html>
    <head>
    <meta charset="utf-8" />
    </head>
    <body>
    <div>
    {}
    </div>
    </body
    </html>
    """.format(word)
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver_email
    part = MIMEText(html, 'html')

    msg.attach(part)
    context = ssl.create_default_context()

    with smtplib.SMTP(smtp_server, port) as server:
        server.ehlo()  # Can be omitted
        server.starttls(context=context)
        server.ehlo()  # Can be omitted
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())


class Watch:
    def __init__(self):
        settings = Parameters()
        self.wait = int(settings.waiting_time * 1.3)
        print(f"WatchTowerLaunched ! It will check every {self.wait} seconds")
        self.file = open("Output/debug_file.txt", "r")
        self.watch_tower()

    def watch_tower(self):
        stopped = False
        last_content = self.file.read()
        self.file.close()
        sleep(self.wait)
        while not stopped:
            self.file = open("Output/debug_file.txt", "r")
            content = self.file.read()
            stopped = self.check_bot_response(content=content, last_content=last_content)
            last_content = content
            self.file.close()

    def check_bot_response(self, content, last_content):
        if content == last_content:
            print("Bot stopped !")
            stopped_and_detected = False
            try:
                collection = content.strip(" ")
                stopped_and_detected = "Code" in collection
            except Exception as e:
                send_email(f"Could not strip the content in debug_file.txt\nError message : \n\n{e}",
                           "Error in watch_tower.py")
            if not stopped_and_detected:
                send_email(f"The bot stopped at : {datetime.datetime.now()}", "Bot stopped !")
            return True
        else:
            sleep(self.wait)
            return False


if __name__ == '__main__':
    Watch()
