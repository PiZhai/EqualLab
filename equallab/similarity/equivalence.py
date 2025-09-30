from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

import random
import sympy as sp

from equallab.assumptions.config import apply_assumptions

@dataclass
class EquivalenceResult:
    is_equivalent: bool
    method: str
    samples_total: int
    samples_success: int
    message: str | None = None


def _symbol_list(expr: sp.Expr) -> List[sp.Symbol]:
    return sorted(list(expr.free_symbols), key=lambda s: s.name)


def _generate_samples(symbols: Iterable[sp.Symbol], n: int = 8) -> List[Dict[sp.Symbol, int]]:
    # 生成整型样本，避免 0 带来的分母问题；可根据需要延展为有理/浮点
    domain = [-3, -2, -1, 1, 2, 3]
    sym_list = list(symbols)
    rng = random.Random(42)
    samples = []
    for _ in range(n * 3):  # 生成多一些，过滤无效后取前 n 个
        sub = {s: rng.choice(domain) for s in sym_list}
        samples.append(sub)
    return samples


def _safe_eval(expr: sp.Expr, subs: Dict[sp.Symbol, int]) -> Tuple[sp.Expr | None, str | None]:
    try:
        v = sp.N(expr.subs(subs))
        if v.has(sp.zoo, sp.oo, sp.nan):
            return None, "non-finite"
        return v, None
    except Exception as e:  # noqa: BLE001
        return None, str(e)


def are_equivalent(expr1: sp.Expr, expr2: sp.Expr, samples: int = 8, tol: float = 1e-8, assumptions: Dict | None = None) -> EquivalenceResult:
    # 预处理：将自由符号统一设为实数，并将 sqrt(z**2) -> Abs(z)
    def _assume_real(e: sp.Expr) -> sp.Expr:
        symbols = {s for s in e.free_symbols}
        mapping = {s: sp.Symbol(s.name, real=True) for s in symbols}
        return e.xreplace(mapping)

    def _sqrt_to_abs(e: sp.Expr) -> sp.Expr:
        z = sp.Wild('z')
        pattern1 = sp.sqrt(z**2)
        pattern2 = (z**2) ** sp.Rational(1, 2)
        e = e.replace(pattern1, sp.Abs(z))
        e = e.replace(pattern2, sp.Abs(z))
        return e

    def _log_E_pow(e: sp.Expr) -> sp.Expr:
        z = sp.Wild('z')
        pattern = sp.log(sp.E**z)
        return e.replace(pattern, z)

    # 应用外部假设
    if assumptions:
        expr1 = apply_assumptions(expr1, assumptions)
        expr2 = apply_assumptions(expr2, assumptions)
    else:
        expr1 = _assume_real(expr1)
        expr2 = _assume_real(expr2)
    expr1 = _sqrt_to_abs(expr1)
    expr2 = _sqrt_to_abs(expr2)

    # 1) 符号化简判定
    try:
        # 先执行显式计算（积分/求和/极限等），再做常见三角代数简化
        e1 = sp.simplify(sp.trigsimp(expr1.doit(deep=True), deep=True))
        e2 = sp.simplify(sp.trigsimp(expr2.doit(deep=True), deep=True))
        # 显式归一化
        e1 = _log_E_pow(_sqrt_to_abs(e1))
        e2 = _log_E_pow(_sqrt_to_abs(e2))
        # 日志/指数：展开与合并
        e1 = sp.simplify(sp.logcombine(sp.expand_log(e1, force=True), force=True))
        e2 = sp.simplify(sp.logcombine(sp.expand_log(e2, force=True), force=True))
        diff = sp.simplify(sp.together(e1 - e2))
        if diff == 0 or getattr(diff, "is_zero", False) or diff.equals(0):
            return EquivalenceResult(True, "symbolic", 0, 0, None)
        # 某些表达式 simplify 后仍可进一步判断
        if sp.simplify(diff) == 0 or sp.simplify(diff).equals(0):
            return EquivalenceResult(True, "symbolic", 0, 0, None)
    except Exception:
        diff = expr1 - expr2

    # 2) 数值采样
    symbols = set(expr1.free_symbols) | set(expr2.free_symbols)
    # 常量表达式：直接比较
    if not symbols:
        try:
            val = sp.N(diff)
            if sp.Abs(val) < tol:
                return EquivalenceResult(True, "numeric-const", 0, 0, None)
            return EquivalenceResult(False, "numeric-const", 0, 0, None)
        except Exception as e:  # noqa: BLE001
            return EquivalenceResult(False, "numeric-const", 0, 0, str(e))

    # 分母为 0 的过滤依据
    denom = sp.denom(sp.together(diff))

    successes = 0
    tried = 0
    for sub in _generate_samples(symbols, n=samples):
        if tried >= samples:
            break
        # 过滤分母为 0 的样本
        try:
            dval = sp.N(denom.subs(sub))
            if dval == 0 or dval.has(sp.zoo, sp.oo, sp.nan):
                continue
        except Exception:
            continue

        val, err = _safe_eval(diff, sub)
        if err is not None:
            continue
        tried += 1
        if sp.Abs(val) < tol:
            successes += 1

    if tried == 0:
        return EquivalenceResult(False, "numeric-none", 0, 0, "no valid samples")

    return EquivalenceResult(successes == tried, "numeric", tried, successes, None)


