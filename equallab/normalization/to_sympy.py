from __future__ import annotations

from typing import Tuple, Optional
import re

import sympy as sp
from sympy.parsing.latex import parse_latex
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)


def parse_to_sympy(text: str, assume_latex: bool = False) -> Tuple[Optional[sp.Expr], Optional[str]]:
    """
    将文本解析为 SymPy 表达式。
    - 优先：当 assume_latex=True 时，尝试 parse_latex
    - 回退：尝试 sympify（支持简易纯文本表达式）
    返回 (expr, error_message)
    """
    if not text:
        return None, "empty input"

    if assume_latex:
        try:
            # 将自由符号 e 预替换为 E，使 e^x 解析为 E**x
            # 注意：仅在明显的幂或函数上下文中替换，避免误伤变量名
            patched = text.replace('e^', 'E^')

            # 专门处理绝对值：若整体是一个绝对值，递归解析内部后构造 Abs()
            abs_full = re.fullmatch(r"\s*(?:\\left\|\s*(?P<inner1>.+?)\s*\\right\||\\lvert\s*(?P<inner2>.+?)\s*\\rvert)\s*", patched, flags=re.DOTALL)
            if abs_full:
                inner = abs_full.group('inner1') or abs_full.group('inner2')
                inner_expr, inner_err = parse_to_sympy(inner, assume_latex=True)
                if inner_err is None and inner_expr is not None:
                    expr = sp.Abs(inner_expr)
                    return sp.simplify(expr), None

            expr = parse_latex(patched)
            if isinstance(expr, sp.Equality):
                expr = expr.lhs - expr.rhs
            return sp.simplify(expr), None
        except Exception as e:  # noqa: BLE001
            # 对于明确是 LaTeX 的输入，直接返回解析错误，不回退到纯文本解析，避免误判
            return None, f"latex_parse_error: {e}"

    try:
        transformations = (
            *standard_transformations,
            convert_xor,
            implicit_multiplication_application,
        )
        expr = parse_expr(text, transformations=transformations, evaluate=True)
        return sp.simplify(expr), None
    except Exception as e:  # noqa: BLE001
        return None, str(e)


