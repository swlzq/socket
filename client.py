# @Author:langyi
# @Time  :2019/4/12


import socket
import os
import time
import json
import struct
import threading
import random

import argparse

# Super parameters
parser = argparse.ArgumentParser(description=" ")
parser.add_argument('--frame_num', default=16, type=int)
args = parser.parse_args()


# Connect server by TCP
def sock_connect(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    return s


# Send image thread
class SendThread(threading.Thread):
    def __init__(self, sock):
        threading.Thread.__init__(self)
        self.sock = sock

    def run(self):
        while True:
            # Image path
            dir_path = 'driver_p002_c7'
            n_frames = len(os.listdir(dir_path))
            # Choose sequence frame number randomly
            begin_idx = random.randint(0, n_frames - args.frame_num)
            frame_indices = list(range(begin_idx, begin_idx + args.frame_num))
            for i in frame_indices:
                image_path = os.path.join(dir_path, 'image_{:05d}.jpg'.format(i))
                if os.path.exists(image_path):
                    self.send_image(image_path)
                else:
                    raise ValueError('index error')

    # Send a piece of image by its path
    def send_image(self, image_path):
        timestamp = time.time()
        '''
            File head:
            Head size: '24si' (s means bytes in python or char[] in C,24s is 24 bytes;
                                i means int, 4 bytes;
                                total 28 bytes)
            Head content: timestamp, file size
        '''
        file_head = struct.pack('24si', bytes(str(timestamp), encoding='utf-8'), os.stat(image_path).st_size)
        self.sock.send(file_head)
        # Read image and send it
        with open(image_path, 'rb') as f:
            while True:
                data = f.read(1024)
                if not data:
                    # print('{} send over !'.format(image_path))
                    break
                self.sock.send(data)


# Receive result thread
class RecvThread(threading.Thread):
    def __init__(self, sock):
        threading.Thread.__init__(self)
        self.sock = sock

    def run(self):
        while True:
            result = self.sock.recv(1024).strip().decode('utf-8')
            if len(result) > 0:
                if is_json(result):
                    # If result is json type, loads it
                    result = json.loads(result)
                    print(result)
                else:
                    print(result)


# Judge received data is json format or not
def is_json(data):
    try:
        json.loads(data)
    except:
        return False
    return True


if __name__ == '__main__':
    HOST, PORT = 'localhost', 6666
    sk = sock_connect(HOST, PORT)
    send_thread = SendThread(sk)
    send_thread.start()
    recv_thread = RecvThread(sk)
    recv_thread.start()
