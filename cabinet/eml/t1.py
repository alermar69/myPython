import base64

import magic

def get_mime_type(file_path):
    mime = magic.Magic(mime=True)
    return mime.from_file(file_path)

content_type =  get_mime_type('t1.py')
print(content_type)

with open('t1.py', 'rb') as fp:
    # par['files'] = [{'file': xmlrpc.client.Binary(fp.read()), 'name': 'textfile.txt'}]
    file = base64.b64encode(fp.read())
file = file.decode('utf-8')

mime = magic.Magic(mime=True)
print(mime.from_buffer(base64.b64decode(file)))
print(mime.from_buffer(file))

