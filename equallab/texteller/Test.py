# client_demo.py

import requests

server_url = "http://47.116.161.224:8501/predict"
# server_url = "http://127.0.0.1:8502/predict"

img_path = "/Users/pizhai/Downloads/x2y.png"
# img_path = "/mnt2/resource/AiPaperZSGC/x2y.png"
with open(img_path, 'rb') as img:
    files = {'img': img}
    response = requests.post(server_url, files=files)

print(response.text)