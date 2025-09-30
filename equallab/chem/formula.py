from __future__ import annotations

import re
from collections import defaultdict
from typing import Dict, List


_TOKEN = re.compile(r"([A-Z][a-z]?)(\d*)|\(|\)|\[|\]|\{|\}")


def _merge_counts(a: Dict[str, int], b: Dict[str, int], k: int = 1) -> None:
    for el, c in b.items():
        a[el] += c * k


def _strip_trailing_annotations(s: str) -> str:
    """
    去除末尾相态与电荷标记：(s)/(l)/(g)/(aq)、^2-、^{2+}、+、- 等；同时移除空格。
    仅处理末尾，避免破坏像 (OH)2 的结构。
    """
    s = s.strip()
    s = re.sub(r"\s+", "", s)
    changed = True
    while changed and s:
        changed = False
        # 相态
        if re.search(r"(\(s\)|\(l\)|\(g\)|\(aq\))$", s):
            s = re.sub(r"(\(s\)|\(l\)|\(g\)|\(aq\))$", "", s)
            changed = True
        # 电荷 ^{...} 或 ^... 或 末尾 +/-
        if re.search(r"\^\{[^}]*\}$", s):
            s = re.sub(r"\^\{[^}]*\}$", "", s)
            changed = True
        if re.search(r"\^[+\-]?\d*$", s):
            s = re.sub(r"\^[+\-]?\d*$", "", s)
            changed = True
        if re.search(r"[+\-]+$", s):
            s = re.sub(r"[+\-]+$", "", s)
            changed = True
    return s


def _parse_core(formula: str) -> Dict[str, int]:
    tokens = list(_TOKEN.finditer(formula))
    i = 0

    def parse_group() -> Dict[str, int]:
        nonlocal i
        counts: Dict[str, int] = defaultdict(int)
        while i < len(tokens):
            t = tokens[i]
            text = t.group(0)
            i += 1
            if text in ("(", "[", "{"):
                inner = parse_group()
                if i < len(tokens) and tokens[i].group(0).isdigit():
                    mul = int(tokens[i].group(0))
                    i += 1
                else:
                    mul = 1
                _merge_counts(counts, inner, mul)
            elif text in (")", "]", "}"):
                break
            else:
                el = t.group(1)
                num = t.group(2)
                if not el:
                    raise ValueError(f"invalid token near: {text}")
                c = int(num) if num else 1
                counts[el] += c
        return counts

    out = parse_group()
    if i != len(tokens):
        raise ValueError("unparsed tokens remain")
    return dict(out)


def parse_formula(s: str) -> Dict[str, int]:
    """
    解析化学式为元素计数字典：
    - 支持括号与嵌套：Ca(OH)2、K4[ON(SO3)2]2
    - 支持水合点/配位点：CuSO4·5H2O、Na2CO3.10H2O（分隔符 '·'/'•'/'.'）
    - 支持前置整体系数：2H2O（等价于 (H2O)2）
    - 忽略末尾相态与电荷：Fe(s)、SO4^{2-}、Fe3+、Cl-
    """
    s = _strip_trailing_annotations(s)
    if not s:
        return {}

    parts: List[str] = re.split(r"[·•.]", s)
    parts = [p for p in parts if p]

    total: Dict[str, int] = defaultdict(int)
    for part in parts:
        part = _strip_trailing_annotations(part)
        m = re.match(r"^(\d+)\s*(.*)$", part)
        if m:
            mul = int(m.group(1))
            core = m.group(2)
        else:
            mul = 1
            core = part
        core = _strip_trailing_annotations(core)
        if not core:
            continue
        counts = _parse_core(core)
        _merge_counts(total, counts, mul)
    return dict(total)


def normalize_formula(s: str) -> Dict[str, int]:
    return parse_formula(s)


def formulas_equivalent(a: str, b: str) -> bool:
    return normalize_formula(a) == normalize_formula(b)


