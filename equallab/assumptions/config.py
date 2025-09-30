from __future__ import annotations

from typing import Dict, Iterable, Tuple

import json
import sympy as sp


AllowedAssumption = str  # 'real' | 'positive' | 'integer'


def parse_assumptions_json(s: str | None) -> Dict:
    if not s:
        return {}
    try:
        data = json.loads(s)
        if not isinstance(data, dict):
            return {}
        return data
    except Exception:
        return {}


def _symbol_with( name: str, kind: AllowedAssumption | None ) -> sp.Symbol:
    if kind == 'real':
        return sp.Symbol(name, real=True)
    if kind == 'positive':
        return sp.Symbol(name, positive=True)
    if kind == 'integer':
        return sp.Symbol(name, integer=True)
    return sp.Symbol(name)


def build_symbol_mapping(symbols: Iterable[sp.Symbol], assumptions: Dict | None) -> Dict[sp.Symbol, sp.Symbol]:
    """
    根据 assumptions 生成符号替换映射。
    约定 assumptions 结构：
    {
      "all": "real" | "positive" | "integer",   # 可选，应用于所有未单独指定的符号
      "vars": { "x": "positive", "n": "integer" }  # 可选
    }
    """
    assumptions = assumptions or {}
    all_kind: AllowedAssumption | None = assumptions.get('all')
    var_kinds: Dict[str, AllowedAssumption] = assumptions.get('vars', {}) if isinstance(assumptions.get('vars', {}), dict) else {}

    mapping: Dict[sp.Symbol, sp.Symbol] = {}
    for s in symbols:
        specific = var_kinds.get(s.name)
        kind = specific or all_kind
        mapping[s] = _symbol_with(s.name, kind)
    return mapping


def apply_assumptions(expr: sp.Expr, assumptions: Dict | None) -> sp.Expr:
    mapping = build_symbol_mapping(expr.free_symbols, assumptions)
    if not mapping:
        return expr
    return expr.xreplace(mapping)


