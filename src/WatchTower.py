import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from time import sleep


def send_email(word):
    port = 587  # For starttls
    smtp_server = "smtp.gmail.com"
    sender_email = 'bestfriendnotifier@gmail.com'
    receiver_email = 'darwho06@gmail.com'
    password = 'azprhcdunwpdtwkz'
    subject = "Update in your project"
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
    msg['To'] = ','.join(receiver_email)
    part = MIMEText(html, 'html')

    msg.attach(part)
    context = ssl.create_default_context()

    with smtplib.SMTP(smtp_server, port) as server:
        server.ehlo()  # Can be omitted
        server.starttls(context=context)
        server.ehlo()  # Can be omitted
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())


if __name__ == '__main__':
    wait = 600
    print("WatchTowerLaunched !")
    stopped = False
    f = open("Output/debug_file.txt", "r")
    last_content = f.read()
    f.close()
    sleep(wait)
    while not stopped:
        file = open("Output/debug_file.txt", "r")
        content = file.read()
        if content == last_content:
            print("\n Bot stopped !")
            stopped = True
            send_email("Bot stopped !")
        else:
            last_content = content
            file.close()
            sleep(wait)
