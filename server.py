# coding = utf-8
# @Author:langyi
# @Time  :2019/4/12


import socketserver
import threading
import json
import struct
from io import BytesIO
from PIL import Image


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    def setup(self):
        print('Accept connection from {}'.format(self.client_address))
        self.imgs = []  # Keep image and timestamp message
        self.frames = 16  # Output 16 frames

    def handle(self):
        while True:
            # Head size ('24si' = 28 bytes)
            file_head_size = struct.calcsize('24si')
            # Receive file head
            buf = self.request.recv(file_head_size)
            if buf:
                # Unpack head and get timestamp and file size
                timestamp, file_size = struct.unpack('24si', buf)
                timestamp = timestamp.decode('utf-8').strip('\x00')
                received_size = 0  # Already received file size
                data = b''
                '''
                    If file size minus received size greater than 1024,
                        receive 1024 bytes once time,
                    else:
                        receive file size minus received size.
                        (Attention: receive 1024 will stick package.)
                '''
                while not received_size == file_size:
                    if file_size - received_size > 1024:
                        data += self.request.recv(1024)
                        received_size += 1024
                    else:
                        data += self.request.recv(file_size - received_size)
                        received_size = file_size
                # BytesIO: Read bytes data from memory
                # Then open it with PIL
                data = BytesIO(data)
                with Image.open(data) as f:
                    frame = f.convert('RGB')
                img = {}
                img['timestamp'] = timestamp
                img['frame'] = frame
                self.imgs.append(img)

                # When images number equals given frame number in memory,
                # calculate result by model and send it
                if len(self.imgs) == self.frames:
                    # PIL list
                    image_array = []
                    for image in self.imgs:
                        image_array.append(image['frame'])

                    result = {
                        'timestamp': self.imgs[len(self.imgs) - 1]['timestamp'],
                        'category': 0,
                        'description': 'Normal'
                    }
                    # Clear images in memory
                    self.imgs = []
                    self.request.send(bytes(json.dumps(result), encoding='utf-8'))


if __name__ == "__main__":
    # Port 0 means to select an arbitrary unused port
    HOST, PORT = 'localhost', 6666
    socketserver.TCPServer.allow_reuse_address = True

    server = socketserver.ThreadingTCPServer((HOST, PORT), ThreadedTCPRequestHandler)

    # Start a thread with the server -- that thread will then start one
    # more thread for each request
    server_thread = threading.Thread(target=server.serve_forever)

    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()
    print("Server loop running in thread:", server_thread.name)
    print("Waiting for connection.... ")

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
