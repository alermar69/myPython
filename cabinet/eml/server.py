from xmlrpc.server import SimpleXMLRPCServer
from eml_utils import send_email

server = SimpleXMLRPCServer(("localhost", 6000))
print("Listening on port 6000...")

server.register_function(send_email, "send_email")
server.serve_forever()
