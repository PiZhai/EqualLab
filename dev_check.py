import os
from equallab.api import similarity, normalize
from equallab.api import image_latex_similarity  # 新增 API 覆盖
from equallab.chem import (
    normalize_formula,
    formulas_equivalent,
    balance_reaction_info,
    reactions_equivalent,
)
from equallab.web import app

try:
    from fastapi.testclient import TestClient  # 轻量本地 HTTP 覆盖
except Exception:  # noqa: BLE001
    TestClient = None


def main():
    pairs = [
        (r"$x^2+2x+1$", r"$(x+1)^2$"),
        (r"$\frac{a}{b}$", r"a/b"),
        (r"$\sin(x)^2+\cos(x)^2$", r"1"),
        (r"$a\cdot b$", r"a*b"),
        (r"(x+y)^2", r"x^2+2xy+y^2"),
        # 对数/指数/根式
        (r"$\log(e^{x})$", r"x"),
        (r"$\sqrt{x^2}$", r"$\lvert x \rvert$"),
        # 积分/求和（简单可计算）
        (r"$\int_{0}^{1} 2x\,dx$", r"1"),
        (r"$\sum_{k=1}^{n} k$", r"n(n+1)/2"),
    ]
    for a, b in pairs:
        out = similarity(a, b)
        print("PAIR:", a, "::", b)
        print("equivalent:", out["equivalent"], "score:", out["score"])
        print("errors.a:", out["a"]["errors"])
        print("errors.b:", out["b"]["errors"])
        print("-" * 40)

    # 单例 normalize 检查
    for s in [r"$x^2+2x+1$", r"2x+3y", r"$\frac{1}{2}x + \frac{1}{2}x$"]:
        n = normalize(s)
        print("NORM:", s, "->", n["expr"], n["errors"])

    # 化学：公式与反应
    chem_samples = [
        "CuSO4·5H2O",
        "Na2CO3.10H2O",
        "2H2O",
        "Fe(s)",
        "SO4^{2-}",
        "Cl-",
    ]
    for s in chem_samples:
        print("CHEM.NORM:", s, "->", normalize_formula(s))
    print("CHEM.EQ H2O vs OH2:", formulas_equivalent("H2O", "OH2"))
    print("CHEM.BALANCE 0.5:", balance_reaction_info("H2 + 0.5 O2 -> H2O")[:3])
    print("CHEM.BALANCE 1/2:", balance_reaction_info("H2 + 1/2 O2 -> H2O")[:3])
    print("CHEM.EQRXN (same):", reactions_equivalent("H2 + 1/2 O2 -> H2O", "H2 + 1/2 O2 -> H2O"))

    # 图像识别 + 相似度：若示例图片存在且 texteller 可用
    img_path = "/Users/pizhai/PycharmProjects/EqualLab/equallab/texteller/x2y.png"
    if os.path.exists(img_path):
        try:
            r = image_latex_similarity(img_path, "$x$")
            print("IMG.SIM:", r["image_latex"], r["input_latex"], r["result"]["equivalent"], r["result"]["score"])
        except Exception as e:  # noqa: BLE001
            print("IMG.SIM.ERROR:", e)

    # Web 接口覆盖（本地 ASGI，不需启动服务）
    if TestClient is not None:
        client = TestClient(app)
        resp = client.post("/normalize", json={"input": "$x^2+2x+1$"})
        print("HTTP /normalize:", resp.status_code)
        resp = client.post("/similarity", json={"a": "$(x+1)^2$", "b": "$x^2+2x+1$"})
        print("HTTP /similarity:", resp.status_code)
        resp = client.post("/chem/formula/norm", json={"input": "K4[ON(SO3)2]2"})
        print("HTTP /chem/formula/norm:", resp.status_code)
        resp = client.post("/chem/formula/eq", json={"a": "H2O", "b": "OH2"})
        print("HTTP /chem/formula/eq:", resp.status_code)
        resp = client.post("/chem/reaction/balance", json={"reaction": "H2 + 1/2 O2 -> H2O"})
        print("HTTP /chem/reaction/balance:", resp.status_code)
        resp = client.post("/chem/reaction/eq", json={"a": "H2 + 1/2 O2 -> H2O", "b": "H2 + 1/2 O2 -> H2O"})
        print("HTTP /chem/reaction/eq:", resp.status_code)
        # 可选：图像接口（模型较大，若不可用则忽略错误）
        if os.path.exists(img_path):
            try:
                resp = client.post("/image/similarity", json={"image_path": img_path, "latex": "$x$", "use_onnx": False})
                print("HTTP /image/similarity:", resp.status_code)
            except Exception as e:  # noqa: BLE001
                print("HTTP /image/similarity ERROR:", e)


if __name__ == "__main__":
    main()


