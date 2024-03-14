import base64
import io

from celery import Celery, shared_task
import os
from middleware import dalayed_action

import smtplib
from email.message import EmailMessage
import sys
from configparser import ConfigParser
import magic



os.environ.setdefault('FORKED_BY_MULTIPROCESSING', '1')

app = Celery('tasks',
             broker='amqp://guest:guest@localhost:5672',
             backend='db+sqlite:///db.db')

@dalayed_action
@shared_task(name="send_email")
def send_email(par: dict, file_bytes=None, file_name: str = None):
    """
        par: {
                'content': 'This is a test',
                'subject': 'Test',
                'from': 'user@example.com',
                'to': ['someone_else@example.com'],
                'html': '<h1>Test</h1>',
                'files': [
                    {'file': fh, 'name': 'textfile.txt'},
                ],
            }

        return: True if success else False
    """


    base_path = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_path, "email.ini")
    if os.path.exists(config_path):
        cfg = ConfigParser()
        cfg.read(config_path)
    else:
        print("Config not found! Exiting!")
        sys.exit(1)

    EMAIL_HOST_USER = cfg.get('smtp', 'EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = cfg.get('smtp', 'EMAIL_HOST_PASSWORD')
    EMAIL_HOST = cfg.get('smtp', 'EMAIL_HOST')
    EMAIL_PORT = cfg.get('smtp', 'EMAIL_PORT')

    server = smtplib.SMTP_SSL(host=EMAIL_HOST, port=int(EMAIL_PORT))
    server.ehlo()
    server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)

    msg = EmailMessage()
    msg.set_content(par['content'])
    msg['Subject'] = par['subject']
    msg['From'] = par['from']
    msg['To'] = par['to']

    if 'html' in par:
        msg.add_alternative(par['html'], subtype='html')

    if 'files' in par:
        for file in par['files']:
            file1 = base64.b64decode(file['file'])
            mime = magic.Magic(mime=True)
            mime_type = mime.from_buffer(file1).split('/')
            msg.add_attachment(file1, maintype=mime_type[0], subtype=mime_type[1],
                               filename=file['name'])

    # err = ''
    # try:
    #     if file_bytes and file_name:
    #         path = os.path.join(base_path, file_name)
    #         # file = base64.b64encode(file_bytes)
    #         file = base64.b64decode(file_bytes)
    #         # with open(path, 'wb') as f:
    #         #     f.write(file)
    #         #
    #         # fh = io.BytesIO()
    #         # with open('textfile.txt', 'rb') as fp:
    #         #     fh.write(fp.read())
    #
    #         msg.add_attachment(file, maintype='application', subtype='octet-stream', filename=file_name)
    # except Exception as e:
    #     err = str(e)
    #     msg.set_content(err)


    server.send_message(msg)
    server.quit()
    return True



