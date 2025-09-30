import re


_MATH_MODE = re.compile(r"\$(.*?)\$|\\\((.*?)\\\)|\\\[(.*?)\\\]", re.DOTALL)


def _strip_math_wrappers(s: str) -> str:
    # 若包含数学模式外壳，提取内部；若多段，仅保留原串（交给解析处理）
    m = _MATH_MODE.fullmatch(s)
    if m:
        inner = next((g for g in m.groups() if g is not None), s)
        return inner
    return s


def clean_latex(s: str) -> str:
    r"""
    轻量 LaTeX 清洗：
    - 去除 $...$ / \( ... \) / \[ ... \]
    - 常见空格与间距命令移除：\, \; \! ~ \quad \qquad
    - 常见等价宏替换：\dfrac/\tfrac -> \frac
    - 注意：不移除必要花括号，不将 \cdot 替换为 *（交由 parse_latex 处理）
    """
    s = _strip_math_wrappers(s)

    replacements = {
        r"\\dfrac": r"\\frac",
        r"\\tfrac": r"\\frac",
        r"\\ln": r"\\log",
        # 三角/双曲函数常见别名统一
        r"\\tg": r"\\tan",
        r"\\ctg": r"\\cot",
        r"\\arctg": r"\\arctan",
        r"\\arccotg": r"\\arccot",
        r"\\ch": r"\\cosh",
        r"\\sh": r"\\sinh",
        r"\\th": r"\\tanh",
        # 间距与不换行空格
        r"\\,": "",
        r"\\;": "",
        r"\\!": "",
        r"\\quad": " ",
        r"\\qquad": "  ",
        r"~": " ",
    }
    for pat, val in replacements.items():
        s = re.sub(pat, val, s)

    # 处理绝对值：双向归一化为 \left| x \right|
    s = re.sub(r"\\left\|\s*(.*?)\s*\\right\|", r"\\left| \1 \\right|", s, flags=re.DOTALL)
    s = re.sub(r"\\lvert\s*(.*?)\s*\\rvert", r"\\left| \1 \\right|", s, flags=re.DOTALL)
    # 支持 \abs{...} 与 \left\lvert ... \right\rvert
    s = re.sub(r"\\abs\s*\{\s*(.*?)\s*\}", r"\\left| \1 \\right|", s, flags=re.DOTALL)
    s = re.sub(r"\\left\\lvert\s*(.*?)\s*\\right\\rvert", r"\\left| \1 \\right|", s, flags=re.DOTALL)

    # 处理 ln/log(e^{x}) -> x, ln/log(e^x) -> x
    s = re.sub(r"\\(?:ln|log)\s*\(\s*e\s*\^\s*\{\s*([^}]+)\s*\}\s*\)", r"\1", s)
    s = re.sub(r"\\(?:ln|log)\s*\(\s*e\s*\^\s*([^\)]+)\)", r"\1", s)
    # 去壳 \mathrm{} 与 \operatorname{}
    s = re.sub(r"\\mathrm\s*\{\s*([^}]+)\s*\}", r"\1", s)
    s = re.sub(r"\\operatorname\s*\{\s*([^}]+)\s*\}", r"\1", s)

    # 压缩多空格
    s = re.sub(r"\s+", " ", s).strip()
    return s


