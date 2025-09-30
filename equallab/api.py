from typing import Dict, Any, Tuple

from .normalization.preprocess import preprocess_text
from .normalization.latex_clean import clean_latex
from .normalization.to_sympy import parse_to_sympy
from .similarity.scorer import similarity as _similarity

# 懒加载 texteller 以避免每次导入均加载模型
_TT_MODEL = None
_TT_TOKENIZER = None


def _ensure_texteller_loaded(use_onnx: bool = False) -> Tuple[Any, Any]:
    global _TT_MODEL, _TT_TOKENIZER  # noqa: PLW0603
    if _TT_MODEL is not None and _TT_TOKENIZER is not None:
        return _TT_MODEL, _TT_TOKENIZER
    try:
        from texteller import load_model, load_tokenizer  # type: ignore
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"texteller import failed: {e}")
    _TT_MODEL = load_model(use_onnx=use_onnx)
    _TT_TOKENIZER = load_tokenizer()
    return _TT_MODEL, _TT_TOKENIZER


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
    返回：{"image_latex": str, "input_latex": str, "result": similarity(...) }
    """
    try:
        from texteller import img2latex  # type: ignore
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"texteller import failed: {e}")

    model, tokenizer = _ensure_texteller_loaded(use_onnx=use_onnx)
    outs = img2latex(model, tokenizer, [image_path])
    if not outs:
        raise RuntimeError("img2latex returned empty result")
    img_latex_raw = outs[0] or ""

    # 包裹检测与剥壳（仅用于展示），计算时保留/补齐包裹
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


