# 已移除本地 texteller 模型调用示例，改为参考 HTTP OCR 用法。
# 请使用 equallab.api.image_latex_similarity 并设置环境变量 TEXTELLER_SERVER_URL 指向 OCR 服务。
# 示例：requests.get(os.getenv("TEXTELLER_SERVER_URL"), params={"path": "/abs/path/to/img.png"})
