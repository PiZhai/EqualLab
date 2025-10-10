from __future__ import annotations

from typing import Any, Dict

import logging
import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .api import normalize as _normalize, similarity as _similarity, image_latex_similarity as _image_latex_similarity
from .api import chem_image_similarity as _chem_image_similarity
from .assumptions.config import parse_assumptions_json
from .chem import (
    normalize_formula,
    formulas_equivalent,
    balance_reaction_info,
    reactions_equivalent,
)


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("equallab.web")

app = FastAPI(title="EqualLab API", version="0.1.0")


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start = time.time()
    try:
        response = await call_next(request)
        duration_ms = int((time.time() - start) * 1000)
        logger.info("%s %s -> %s in %dms", request.method, request.url.path, getattr(response, "status_code", "-"), duration_ms)
        return response
    except Exception as e:  # noqa: BLE001
        duration_ms = int((time.time() - start) * 1000)
        logger.exception("Unhandled error for %s %s after %dms", request.method, request.url.path, duration_ms)
        return JSONResponse(status_code=500, content={"detail": str(e)})


class NormalizeReq(BaseModel):
    input: str
    is_latex: bool | None = None


class SimilarityReq(BaseModel):
    a: str
    b: str
    assumptions: Dict[str, Any] | None = None


class ChemEqReq(BaseModel):
    a: str
    b: str


class ChemBalanceReq(BaseModel):
    reaction: str

class ImageSimReq(BaseModel):
    image_path: str
    latex: str
    assumptions: Dict[str, Any] | None = None
    use_onnx: bool = False

class ChemImageSimReq(BaseModel):
    image_path: str
    text: str
    type: str  # "formula" | "reaction"


@app.post("/normalize")
def normalize(req: NormalizeReq):
    out = _normalize(req.input, is_latex=req.is_latex)
    if out.get("expr") is not None:
        out = dict(out)
        out["expr"] = str(out["expr"])  # ensure JSON-serializable
    return out


@app.post("/similarity")
def similarity(req: SimilarityReq):
    out = _similarity(req.a, req.b, assumptions=req.assumptions)
    # make nested expr JSON-serializable
    a = dict(out.get("a", {}))
    b = dict(out.get("b", {}))
    if a.get("expr") is not None:
        a["expr"] = str(a["expr"]) 
    if b.get("expr") is not None:
        b["expr"] = str(b["expr"]) 
    out = dict(out)
    out["a"] = a
    out["b"] = b
    return out


@app.post("/chem/formula/norm")
def chem_norm(req: NormalizeReq):
    return {"composition": normalize_formula(req.input)}


@app.post("/chem/formula/eq")
def chem_eq(req: ChemEqReq):
    return {"equivalent": formulas_equivalent(req.a, req.b)}


@app.post("/chem/reaction/balance")
def chem_balance(req: ChemBalanceReq):
    rc, pc, reag, prod, method = balance_reaction_info(req.reaction)
    return {
        "reactants": [{"coef": c, "species": s} for c, s in zip(rc, reag)],
        "products": [{"coef": c, "species": s} for c, s in zip(pc, prod)],
        "method": method,
    }


@app.post("/chem/reaction/eq")
def chem_eqrxn(req: ChemEqReq):
    return {"equivalent": reactions_equivalent(req.a, req.b)}


@app.post("/image/similarity")
def image_similarity(req: ImageSimReq):
    out = _image_latex_similarity(req.image_path, req.latex, assumptions=req.assumptions, use_onnx=req.use_onnx)
    # 使内部 result 的 expr 可序列化
    res = dict(out["result"]) if isinstance(out.get("result"), dict) else out["result"]
    a = dict(res.get("a", {})) if isinstance(res.get("a", {}), dict) else {}
    b = dict(res.get("b", {})) if isinstance(res.get("b", {}), dict) else {}
    if a.get("expr") is not None:
        a["expr"] = str(a["expr"]) 
    if b.get("expr") is not None:
        b["expr"] = str(b["expr"]) 
    res["a"] = a
    res["b"] = b
    return {"image_latex": out["image_latex"], "input_latex": out["input_latex"], "result": res}


@app.post("/chem/image/similarity")
def chem_image_similarity_endpoint(req: ChemImageSimReq):
    """化学：一步到位的图片识别 + 等价判断。"""
    out = _chem_image_similarity(req.image_path, req.text, req.type)
    # 直接返回业务结果结构：{"image_text","input_text","type","result":{...}}
    return out

