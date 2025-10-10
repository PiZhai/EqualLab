import os
from equallab.api import similarity, normalize
from equallab.api import image_latex_similarity  # 新增 API 覆盖
from equallab.api import chem_image_similarity  # 化学图片+相似度（一步）
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
    # 数学基本功能
    print("SIM:", similarity("$(x+1)^2$", "$x^2+2x+1$"))
    print("NORM:", normalize("$x^2+2x+1$"))
    print("SIM with assumptions:", similarity("$\\sqrt{x^2}$", "$\\lvert x \\rvert$", assumptions={"vars": {"x": "positive"}}))

    # 化学基本功能
    print("CHEM.NORM:", normalize_formula("K4[ON(SO3)2]2"))
    print("CHEM.EQ:", formulas_equivalent("H2O", "OH2"))
    print("CHEM.BALANCE:", balance_reaction_info("H2 + 1/2 O2 -> H2O"))
    print("CHEM.EQRXN:", reactions_equivalent("2H2 + O2 -> 2H2O", "H2 + 0.5 O2 -> H2O"))
    print("CHEM.EQRXN (same):", reactions_equivalent("H2 + 1/2 O2 -> H2O", "H2 + 1/2 O2 -> H2O"))

    # 图像识别 + 相似度：若示例图片存在且 texteller 可用
    img_path = "/mnt2/resource/AiPaperZSGC/x2y.png"
    try:
        r = image_latex_similarity(img_path, "$x+2*y$")
        print("IMG.SIM:", r["image_latex"], r["input_latex"], r["result"]["equivalent"], r["result"]["score"])
    except Exception as e:  # noqa: BLE001
        print("IMG.SIM.ERROR:", e)

    # 化学：图片 + 相似度（业务函数直接调用）
    chem_img_path = "/mnt2/resource/AiPaperZSGC/chem.png"  # 如不存在会报错，捕获即可
    try:
        r = chem_image_similarity(chem_img_path, "H2O", "formula")
        print("CHEM.IMG.SIM.FORMULA:", r)
    except Exception as e:
        print("CHEM.IMG.SIM.FORMULA.ERROR:", e)
    try:
        r = chem_image_similarity(chem_img_path, "H2 + 0.5 O2 -> H2O", "reaction")
        print("CHEM.IMG.SIM.REACTION:", r)
    except Exception as e:
        print("CHEM.IMG.SIM.REACTION.ERROR:", e)

    # Web 接口覆盖（本地 ASGI，不需启动服务）
    img_path = "/Users/pizhai/PycharmProjects/EqualLab/equallab/texteller/x2y.png"
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
        # 新增：化学图片 + 相似度端点
        chem_img_path2 = "/Users/pizhai/PycharmProjects/EqualLab/equallab/texteller/chem.png"
        if os.path.exists(chem_img_path2):
            try:
                resp = client.post("/chem/image/similarity", json={"image_path": chem_img_path2, "text": "H2O", "type": "formula"})
                print("HTTP /chem/image/similarity (formula):", resp.status_code)
                resp = client.post("/chem/image/similarity", json={"image_path": chem_img_path2, "text": "H2 + 0.5 O2 -> H2O", "type": "reaction"})
                print("HTTP /chem/image/similarity (reaction):", resp.status_code)
            except Exception as e:
                print("HTTP /chem/image/similarity ERROR:", e)


if __name__ == "__main__":
    main()


