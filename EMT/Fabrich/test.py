import os
from sys import argv

script, arg1, arg2 = argv

namedir = arg1 + arg2

os.makedirs(f'c:/{namedir}')