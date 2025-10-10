# client_demo.py

import requests

server_url = "http://47.116.161.224:8501/predict"
# server_url = "http://127.0.0.1:8502/predict"

# 要上传图片的路径
# img_path = "/Users/pizhai/Downloads/x2y.png"
# 远程服务器上面的图片路径
img_path = "/mnt2/resource/AiPaperZSGC/x2y.png"
# 使用上传图片方式识别
# with open(img_path, 'rb') as img:
#     files = {'img': img}
#     response = requests.post(server_url, files=files)
#
# print(response.text)

# 识别远程服务器上面的图片
# get请求
response = requests.get(server_url, params={'path': img_path})
print(response.text)