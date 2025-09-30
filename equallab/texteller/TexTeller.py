from texteller import load_model, load_tokenizer, img2latex

# Load models
model = load_model(use_onnx=False)
tokenizer = load_tokenizer()

# Convert image to LaTeX
latex = img2latex(model, tokenizer, ["x2y.png"])[0]

# texteller inference "/Users/pizhai/PycharmProjects/EqualLab/x2y.png"
# 更多参数请查看 texteller inference --help

# texteller web
# 在浏览器中输入 http://localhost:8501 查看网页演示
