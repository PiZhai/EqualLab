# EqualLab

[![CI](https://github.com/OWNER/EqualLab/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/EqualLab/actions)
[![PyPI](https://img.shields.io/pypi/v/equallab.svg)](https://pypi.org/project/equallab/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)

Normalize and compare mathematical expressions (LaTeX/Unicode/plain text) using SymPy, with chemistry formula/reaction equivalence and balancing. Exposes a REST API via FastAPI and a convenient CLI. Optional image-to-LaTeX recognition powered by TexTeller.

> Tech: Python 3.12, FastAPI, SymPy, TexTeller

[中文文档 | Chinese Guide](./README.zh-CN.md)

## Table of Contents
- [Features](#features)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
  - [Run with Docker](#run-with-docker)
  - [Run locally (Python)](#run-locally-python)
- [Usage by Role](#usage-by-role)
  - [For API Consumers](#for-api-consumers)
  - [For CLI Users](#for-cli-users)
  - [For Operators (Ops/Prod)](#for-operators-opsprod)
  - [For Developers](#for-developers)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Limitations](#limitations)
- [Acknowledgements](#acknowledgements)

## Features
- Math normalization: Clean and parse LaTeX/Unicode to SymPy expressions.
- Equivalence & similarity: Symbolic + numeric checks with a composite score.
- Chemistry utilities: Formula normalization/equivalence; reaction balancing/equivalence.
- Image-to-LaTeX (optional): Compare recognized LaTeX with user input via TexTeller.
- Robust API: FastAPI app with logging and error handling.

## Project Structure
```
equallab/
  api.py              # Public API (normalize/similarity/image_latex_similarity)
  web.py              # FastAPI app (uvicorn entry)
  cli.py              # Typer-based CLI
  normalization/      # Preprocess / LaTeX clean / parse to SymPy
  similarity/         # Equivalence / structure / scoring
  assumptions/        # Assumption config parsing
  chem/               # Chemical formula/reaction tools
```

## Quick Start

### Run with Docker
```bash
docker build -t equallab:latest .
docker run -d --name equallab -p 10086:10086 --restart unless-stopped equallab:latest
# Visit: http://127.0.0.1:10086
```

### Run locally (Python)
```bash
python -m venv .venv && source .venv/bin/activate
pip install --upgrade --force-reinstall -r requirements.txt
uvicorn equallab.web:app --host 0.0.0.0 --port 10086 --log-level info
```

## Usage by Role

### For API Consumers
Base URL (default): `http://127.0.0.1:10086`

Endpoints:

1) Normalize: `POST /normalize`
```bash
curl -s http://127.0.0.1:10086/normalize \
  -H 'Content-Type: application/json' \
  -d '{"input":"$x^2+2x+1$"}'
```

2) Similarity (with optional assumptions): `POST /similarity`
```bash
curl -s http://127.0.0.1:10086/similarity \
  -H 'Content-Type: application/json' \
  -d '{"a":"$(x+1)^2$","b":"$x^2+2x+1$","assumptions":{"vars":{"x":"positive"}}}'
```

3) Chemistry:
```bash
# Formula normalization
curl -s http://127.0.0.1:10086/chem/formula/norm \
  -H 'Content-Type: application/json' \
  -d '{"input":"K4[ON(SO3)2]2"}'

# Formula equivalence
curl -s http://127.0.0.1:10086/chem/formula/eq \
  -H 'Content-Type: application/json' \
  -d '{"a":"H2O","b":"OH2"}'

# Reaction balancing
curl -s http://127.0.0.1:10086/chem/reaction/balance \
  -H 'Content-Type: application/json' \
  -d '{"reaction":"H2 + 0.5 O2 -> H2O"}'

# Reaction equivalence
curl -s http://127.0.0.1:10086/chem/reaction/eq \
  -H 'Content-Type: application/json' \
  -d '{"a":"2H2 + O2 -> 2H2O","b":"H2 + 0.5 O2 -> H2O"}'
```

4) Image + Similarity (optional, TexTeller required): `POST /image/similarity`
```bash
curl -s http://127.0.0.1:10086/image/similarity \
  -H 'Content-Type: application/json' \
  -d '{"image_path":"/abs/path/to/image.png","latex":"$x$","use_onnx":false}'
```

### For CLI Users
```bash
python -m equallab.cli norm '$x^2+2x+1$'
python -m equallab.cli sim '$(x+1)^2$' '$x^2+2x+1$'
python -m equallab.cli sim '$\frac{a}{b}$' 'a/b'
python -m equallab.cli sim '$\sin(x)^2+\cos(x)^2$' '1'
python -m equallab.cli sim '$\int_{0}^{1} 2x\\,dx$' '1'
python -m equallab.cli sim '$\sum_{k=1}^{n} k$' 'n(n+1)/2'

# Chemistry
python -m equallab.cli chem norm 'K4[ON(SO3)2]2'
python -m equallab.cli chem eq 'H2O' 'OH2'
python -m equallab.cli chem balance 'H2 + 0.5 O2 -> H2O'
python -m equallab.cli chem eqrxn '2H2 + O2 -> 2H2O' 'H2 + 0.5 O2 -> H2O'
```

### For Operators (Ops/Prod)
- Container listens on port `10086` (`uvicorn equallab.web:app --host 0.0.0.0 --port 10086`).
- Mount host directories for image input if using `/image/similarity` (e.g., `-v /data/images:/data:Z` on SELinux systems).
- Use `--restart unless-stopped` for resilience; consider reverse proxy/HTTPS in production.

### For Developers
```bash
python -m venv .venv && source .venv/bin/activate
pip install --upgrade --force-reinstall -r requirements.txt

# Smoke checks
python -c "from sympy.parsing.latex import parse_latex; print('parse_latex_ok')"
python dev_check.py
```

Programmatic API:
```python
from equallab.api import normalize, similarity, image_latex_similarity

normalize('$x^2+2x+1$')
similarity('$(x+1)^2$', '$x^2+2x+1$')
similarity('$\\sqrt{x^2}$', '$\\lvert x \\rvert$', assumptions={"vars":{"x":"positive"}})

image_latex_similarity('/abs/path/to/image.png', '$x$')  # requires TexTeller
```

## Configuration
Assumptions JSON (optional):
```json
{
  "all": "real | positive | integer",
  "vars": { "x": "positive", "n": "integer" }
}
```

## Troubleshooting
- LaTeX parsing errors: ensure proper escaping and math-mode wrappers like `$...$` or `\(...\)`.
- CLI argument issues: `click==8.1.7` is pinned; reinstall dependencies if needed.
- Chemistry fractional coefficients: prefer decimals like `0.5 O2`; if `chempy` fails, it falls back to `sympy` method.

## Limitations
- Extremely complex LaTeX macros/custom commands are not comprehensively covered yet.
- Chemistry grammar currently omits charge, phase, electrons, and half-reactions.

## Acknowledgements
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

---

If you find this project useful, consider starring it and opening issues/PRs for enhancements.


