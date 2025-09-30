import json
import typer
from rich import print

from .api import normalize, similarity
from .assumptions.config import parse_assumptions_json
from .chem import (
    parse_formula,
    normalize_formula,
    formulas_equivalent,
    parse_reaction,
    balance_reaction,
    balance_reaction_info,
    reactions_equivalent,
)


app = typer.Typer(add_completion=False)


@app.command()
def norm(expr: str):
    """规范化并输出 SymPy 表达式与中间结果"""
    out = normalize(expr)
    print(json.dumps({
        "text_norm": out["text_norm"],
        "latex_norm": out["latex_norm"],
        "expr": str(out["expr"]),
        "errors": out["errors"],
    }, ensure_ascii=False, indent=2))


@app.command()
def sim(a: str, b: str, assumptions: str = typer.Option(None, help="JSON 假设，如 '{\"all\":\"real\",\"vars\":{\"x\":\"positive\"}}'")):
    """比较两个表达式的等价性与相似度"""
    out = similarity(a, b, assumptions=parse_assumptions_json(assumptions))
    print(json.dumps({
        "equivalent": out["equivalent"],
        "score": out["score"],
        "detail": out["detail"],
    }, ensure_ascii=False, indent=2))


chem = typer.Typer(help="化学公式/反应相关命令")
app.add_typer(chem, name="chem")


@chem.command("norm")
def chem_norm(formula: str):
    print(json.dumps(normalize_formula(formula), ensure_ascii=False, indent=2))


@chem.command("eq")
def chem_eq(a: str, b: str):
    print(json.dumps({"equivalent": formulas_equivalent(a, b)}, ensure_ascii=False, indent=2))


@chem.command("balance")
def chem_balance(reaction: str):
    rc, pc, reag, prod, method = balance_reaction_info(reaction)
    print(json.dumps({
        "reactants": [{"coef": c, "species": s} for c, s in zip(rc, reag)],
        "products": [{"coef": c, "species": s} for c, s in zip(pc, prod)],
        "method": method,
    }, ensure_ascii=False, indent=2))


@chem.command("eqrxn")
def chem_eqrxn(a: str, b: str):
    print(json.dumps({"equivalent": reactions_equivalent(a, b)}, ensure_ascii=False, indent=2))


def main():
    app()


if __name__ == "__main__":
    main()


