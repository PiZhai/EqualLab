# EqualLab（中文指南）

[![CI](https://github.com/OWNER/EqualLab/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/EqualLab/actions)
[![PyPI](https://img.shields.io/pypi/v/equallab.svg)](https://pypi.org/project/equallab/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)

EqualLab 提供对数学表达式（LaTeX/Unicode/纯文本）的规范化与等价/相似度判断，并提供化学式与反应的等价与配平能力。支持 REST API（FastAPI）与命令行（Typer），可选集成 TexTeller 以实现图片转 LaTeX。

> 技术栈：Python 3.12、FastAPI、SymPy、TexTeller

## 快速开始

### 使用 Docker
```bash
docker build -t equallab:latest .
docker run -d --name equallab -p 10086:10086 --restart unless-stopped equallab:latest
# 打开：http://127.0.0.1:10086
```

### 本地运行（Python）
```bash
python -m venv .venv && source .venv/bin/activate
pip install --upgrade --force-reinstall -r requirements.txt
uvicorn equallab.web:app --host 0.0.0.0 --port 10086 --log-level info
```

## API 示例
基础地址：`http://127.0.0.1:10086`
```bash
# 规范化
curl -s http://127.0.0.1:10086/normalize \
  -H 'Content-Type: application/json' \
  -d '{"input":"$x^2+2x+1$"}'

# 相似度（带假设）
curl -s http://127.0.0.1:10086/similarity \
  -H 'Content-Type: application/json' \
  -d '{"a":"$(x+1)^2$","b":"$x^2+2x+1$","assumptions":{"vars":{"x":"positive"}}}'

# 化学式/反应
curl -s http://127.0.0.1:10086/chem/formula/norm -H 'Content-Type: application/json' -d '{"input":"K4[ON(SO3)2]2"}'
curl -s http://127.0.0.1:10086/chem/formula/eq -H 'Content-Type: application/json' -d '{"a":"H2O","b":"OH2"}'
curl -s http://127.0.0.1:10086/chem/reaction/balance -H 'Content-Type: application/json' -d '{"reaction":"H2 + 0.5 O2 -> H2O"}'
curl -s http://127.0.0.1:10086/chem/reaction/eq -H 'Content-Type: application/json' -d '{"a":"2H2 + O2 -> 2H2O","b":"H2 + 0.5 O2 -> H2O"}'

# 图片 + 相似度（需要 TexTeller）
curl -s http://127.0.0.1:10086/image/similarity \
  -H 'Content-Type: application/json' \
  -d '{"image_path":"/abs/path/to/image.png","latex":"$x$","use_onnx":false}'
```

## CLI 示例
```bash
python -m equallab.cli norm '$x^2+2x+1$'
python -m equallab.cli sim '$(x+1)^2$' '$x^2+2x+1$'
python -m equallab.cli sim '$\frac{a}{b}$' 'a/b'
python -m equallab.cli sim '$\sin(x)^2+\cos(x)^2$' '1'
python -m equallab.cli sim '$\int_{0}^{1} 2x\\,dx$' '1'
python -m equallab.cli sim '$\sum_{k=1}^{n} k$' 'n(n+1)/2'

# 化学
python -m equallab.cli chem norm 'K4[ON(SO3)2]2'
python -m equallab.cli chem eq 'H2O' 'OH2'
python -m equallab.cli chem balance 'H2 + 0.5 O2 -> H2O'
python -m equallab.cli chem eqrxn '2H2 + O2 -> 2H2O' 'H2 + 0.5 O2 -> H2O'
```

## 部署要点
- 容器默认监听 `10086`；生产环境建议加反向代理/HTTPS。
- 使用 `/image/similarity` 时，可通过 `-v /data/images:/data:Z` 挂载图片目录（SELinux 建议 `:Z`）。
- 当 `chempy` 配平失败时，会自动回退到内置 `sympy` 方法。

## 致谢（References）
- TexTeller: https://github.com/OleehyO/TexTeller
- SymPy: https://github.com/sympy/sympy
- FastAPI: https://github.com/fastapi/fastapi
- Uvicorn: https://github.com/encode/uvicorn
- Typer: https://github.com/tiangolo/typer
- NetworkX: https://github.com/networkx/networkx
- SciPy: https://github.com/scipy/scipy
- NumPy: https://github.com/numpy/numpy
- Chempy: https://github.com/bjodah/chempy
- ANTLR4 Python runtime: https://github.com/antlr/antlr4/tree/master/runtime/Python3

## 限制
- 未全面覆盖极端 LaTeX 宏/自定义命令。
- 化学语法暂未支持电荷、相态、电子与半反应等高级特性。

---

如对你有帮助，欢迎 Star、提 Issue 或提交 PR。
