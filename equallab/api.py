from typing import Dict, Any

from .normalization.preprocess import preprocess_text
from .normalization.latex_clean import clean_latex
from .normalization.to_sympy import parse_to_sympy
from .similarity.scorer import similarity as _similarity
from .chem import normalize_formula, formulas_equivalent, balance_reaction_info, reactions_equivalent

import os
import requests


def normalize(input_text: str, is_latex: bool | None = None) -> Dict[str, Any]:
    """
    基础规范化入口：
    - 预处理文本（Unicode NFKC、空白规范、常见替换）
    - 若判断为 LaTeX 或显式声明 is_latex=True，则进行 LaTeX 清洗
    - 解析为 SymPy 表达式
    返回：{"input": 原始字符串, "text_norm": 规范化文本, "latex_norm": 规范化后可能的 LaTeX,
          "expr": sympy.Expr 或 None, "errors": list[str]}
    """
    raw = input_text
    errors: list[str] = []

    text_norm = preprocess_text(raw)

    # 粗略判断是否为 LaTeX
    if is_latex is None:
        # 粗略判定：包含反斜杠命令或外层数学模式
        looks_latex = any(sym in text_norm for sym in ("\\", "^{", "_{", "\\frac", "\\sqrt", "\\sum", "\\int", "$", "\\(", "\\["))
    else:
        looks_latex = bool(is_latex)

    latex_norm = None
    to_parse = text_norm
    if looks_latex:
        latex_norm = clean_latex(text_norm)
        to_parse = latex_norm

    expr, parse_err = parse_to_sympy(to_parse, assume_latex=looks_latex)
    if parse_err:
        errors.append(parse_err)

    return {
        "input": raw,
        "text_norm": text_norm,
        "latex_norm": latex_norm,
        "expr": expr,
        "errors": errors,
    }


def similarity(a: str, b: str, assumptions: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    计算两个输入表达式的等价性与相似度分数。
    返回：{"a": normalize(a), "b": normalize(b), "equivalent": bool, "score": float, "detail": {...}}
    """
    na = normalize(a)
    nb = normalize(b)
    if na["expr"] is None or nb["expr"] is None:
        return {
            "a": na,
            "b": nb,
            "equivalent": False,
            "score": 0.0,
            "detail": {"error": "failed to parse one of inputs"},
        }
    res = _similarity(na["expr"], nb["expr"], assumptions=assumptions)
    return {
        "a": na,
        "b": nb,
        "equivalent": res.equivalent,
        "score": res.score,
        "detail": res.detail,
    }


def image_latex_similarity(image_path: str, latex: str, assumptions: Dict[str, Any] | None = None, use_onnx: bool = False) -> Dict[str, Any]:
    """
    识别图片中的公式为 LaTeX，并与传入的 LaTeX 进行等价/相似度比对。
    通过 HTTP 请求远程 OCR 服务（如 TexTeller web），期望接口形如 GET {server_url}?path={image_path}。
    返回：{"image_latex": str, "input_latex": str, "result": similarity(...) }
    """
    # server_url = os.getenv("TEXTELLER_SERVER_URL")
    server_url = "http://47.116.161.224:8501/predict"
    if not server_url:
        raise RuntimeError(
            "TEXTELLER_SERVER_URL 未设置，请配置指向 OCR 服务的 HTTP 接口，例如 http://127.0.0.1:8502/predict"
        )

    try:
        resp = requests.get(server_url, params={"path": image_path}, timeout=15)
    except requests.RequestException as e:  # noqa: BLE001
        raise RuntimeError(f"HTTP 请求 OCR 服务失败: {e}")

    if resp.status_code != 200:
        trunc = (resp.text or "")[:200]
        raise RuntimeError(f"OCR 服务返回非 200 状态码: {resp.status_code}, 响应片段: {trunc}")

    img_latex_raw = ""
    # 尝试 JSON；否则退回纯文本
    try:
        if "application/json" in (resp.headers.get("Content-Type") or ""):
            data = resp.json()
            if isinstance(data, dict):
                cand = data.get("latex") or data.get("data") or data.get("result") or data.get("prediction")
                if isinstance(cand, list):
                    img_latex_raw = (cand[0] or "") if cand else ""
                elif isinstance(cand, dict) and "latex" in cand:
                    img_latex_raw = str(cand.get("latex") or "")
                elif isinstance(cand, str):
                    img_latex_raw = cand
            elif isinstance(data, list):
                if data and isinstance(data[0], str):
                    img_latex_raw = data[0]
                elif data and isinstance(data[0], dict) and "latex" in data[0]:
                    img_latex_raw = str(data[0].get("latex") or "")
        else:
            img_latex_raw = resp.text.strip()
    except Exception:
        img_latex_raw = resp.text.strip()

    if not img_latex_raw:
        raise RuntimeError("OCR 服务未返回可用的 LaTeX 字符串")

    import re as _re
    _wrapper_pat = _re.compile(r"^\s*(?:\$(?:[\s\S]+)\$|\\\((?:[\s\S]+)\\\)|\\\[(?:[\s\S]+)\\\])\s*$")

    def _strip_wrappers(s: str) -> str:
        m = _re.fullmatch(r"\s*\$(.*)\$\s*", s, flags=_re.DOTALL)
        if m:
            return m.group(1).strip()
        m = _re.fullmatch(r"\s*\\\((.*)\\\)\s*", s, flags=_re.DOTALL)
        if m:
            return m.group(1).strip()
        m = _re.fullmatch(r"\s*\\\[(.*)\\\]\s*", s, flags=_re.DOTALL)
        if m:
            return m.group(1).strip()
        return s.strip()

    # 展示用（去壳）
    image_latex_display = _strip_wrappers(img_latex_raw)

    # 计算用：确保有包裹
    def _wrap_if_needed(s: str) -> str:
        s = s.strip()
        if not s:
            return s
        if _wrapper_pat.fullmatch(s):
            return s
        return f"${s}$"

    a = _wrap_if_needed(img_latex_raw)
    b = _wrap_if_needed(latex)
    result = similarity(a, b, assumptions=assumptions)
    return {"image_latex": image_latex_display, "input_latex": _strip_wrappers(latex), "result": result}


# 化学：图片 + 等价/相似度（一步到位）

def chem_image_similarity(image_path: str, text: str, type_: str) -> Dict[str, Any]:
    """
    识别化学图片为文本，并与传入的化学文本进行等价/相似度比对。
    type_ ∈ {"formula", "reaction"}
    通过 HTTP 请求远程 OCR 服务（同上），期望接口形如 GET {server_url}?path={image_path}。
    返回：{"image_text": str, "input_text": str, "type": type_, "result": {"equivalent": bool, "detail": {...}} }
    """
    server_url = os.getenv("TEXTELLER_SERVER_URL")
    if not server_url:
        raise RuntimeError(
            "TEXTELLER_SERVER_URL 未设置，请配置指向 OCR 服务的 HTTP 接口，例如 http://127.0.0.1:8502/predict"
        )

    try:
        resp = requests.get(server_url, params={"path": image_path}, timeout=15)
    except requests.RequestException as e:  # noqa: BLE001
        raise RuntimeError(f"HTTP 请求 OCR 服务失败: {e}")

    if resp.status_code != 200:
        trunc = (resp.text or "")[:200]
        raise RuntimeError(f"OCR 服务返回非 200 状态码: {resp.status_code}, 响应片段: {trunc}")

    # 解析为纯文本优先；若为 JSON 则尝试常见字段
    ocr_text_raw = ""
    try:
        if "application/json" in (resp.headers.get("Content-Type") or ""):
            data = resp.json()
            if isinstance(data, dict):
                cand = data.get("text") or data.get("data") or data.get("result") or data.get("prediction") or data.get("latex")
                if isinstance(cand, list):
                    ocr_text_raw = (cand[0] or "") if cand else ""
                elif isinstance(cand, dict):
                    # 尝试常见键
                    for k in ("text", "latex"):
                        if k in cand:
                            ocr_text_raw = str(cand.get(k) or "")
                            break
                elif isinstance(cand, str):
                    ocr_text_raw = cand
            elif isinstance(data, list):
                if data and isinstance(data[0], str):
                    ocr_text_raw = data[0]
                elif data and isinstance(data[0], dict):
                    for k in ("text", "latex"):
                        if k in data[0]:
                            ocr_text_raw = str(data[0].get(k) or "")
                            break
        else:
            ocr_text_raw = resp.text.strip()
    except Exception:
        ocr_text_raw = resp.text.strip()

    if not ocr_text_raw:
        raise RuntimeError("OCR 服务未返回可用的化学文本")

    import re as _re

    def _strip_math_wrappers(s: str) -> str:
        m = _re.fullmatch(r"\s*\$(.*)\$\s*", s, flags=_re.DOTALL)
        if m:
            return m.group(1).strip()
        m = _re.fullmatch(r"\s*\\\((.*)\\\)\s*", s, flags=_re.DOTALL)
        if m:
            return m.group(1).strip()
        m = _re.fullmatch(r"\s*\\\[(.*)\\\]\s*", s, flags=_re.DOTALL)
        if m:
            return m.group(1).strip()
        return s.strip()

    def _strip_common_macros(s: str) -> str:
        # 移除简单 LaTeX 宏包装，如 \ce{...}, \mathrm{...}, \text{...}
        s = _re.sub(r"\\(?:ce|mathrm|text)\{([^}]*)\}", r"\1", s)
        # 移除多余空白
        return s.strip()

    image_text = _strip_common_macros(_strip_math_wrappers(ocr_text_raw))
    input_text = _strip_common_macros(_strip_math_wrappers(text))

    kind = (type_ or "").strip().lower()
    if kind not in {"formula", "reaction"}:
        raise RuntimeError("type 必须为 'formula' 或 'reaction'")

    if kind == "formula":
        equiv = formulas_equivalent(image_text, input_text)
        detail = {
            "normalized_a": normalize_formula(image_text),
            "normalized_b": normalize_formula(input_text),
        }
    else:  # reaction
        equiv = reactions_equivalent(image_text, input_text)
        # 可选：给出配平信息，便于排查
        try:
            ra = balance_reaction_info(image_text)
        except Exception:
            ra = None
        try:
            rb = balance_reaction_info(input_text)
        except Exception:
            rb = None
        detail = {
            "balance_a": ra,
            "balance_b": rb,
        }

    return {"image_text": image_text, "input_text": input_text, "type": kind, "result": {"equivalent": equiv, "detail": detail}}


