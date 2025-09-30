from __future__ import annotations

from typing import Dict, Tuple

import sympy as sp
import networkx as nx


def _expr_to_graph(expr: sp.Expr) -> nx.DiGraph:
    g = nx.DiGraph()

    def add_node(e: sp.Expr) -> int:
        idx = id(e)
        if idx in g:
            return idx
        label = type(e).__name__
        if isinstance(e, sp.Symbol):
            label = f"Sym:{e.name}"
        elif isinstance(e, sp.Integer):
            label = f"Int:{int(e)}"
        elif isinstance(e, sp.Rational):
            label = f"Rat:{e.p}/{e.q}"
        elif isinstance(e, sp.Float):
            label = "Float"
        g.add_node(idx, label=label)
        for arg in e.args:
            child_idx = add_node(arg)
            g.add_edge(idx, child_idx)
        return idx

    add_node(expr)
    return g


def structure_similarity(expr1: sp.Expr, expr2: sp.Expr) -> float:
    """
    结构相似度（0-1）：
    - 将表达式树转为有向图
    - 使用节点标签与边的 Jaccard 相似度的简单组合
    """
    g1 = _expr_to_graph(expr1)
    g2 = _expr_to_graph(expr2)

    nodes1 = {g1.nodes[n]["label"] for n in g1.nodes}
    nodes2 = {g2.nodes[n]["label"] for n in g2.nodes}
    edges1 = {(g1.nodes[u]["label"], g1.nodes[v]["label"]) for u, v in g1.edges}
    edges2 = {(g2.nodes[u]["label"], g2.nodes[v]["label"]) for u, v in g2.edges}

    def jaccard(a: set, b: set) -> float:
        if not a and not b:
            return 1.0
        inter = len(a & b)
        union = len(a | b)
        return inter / union if union else 0.0

    node_sim = jaccard(nodes1, nodes2)
    edge_sim = jaccard(edges1, edges2)
    return 0.5 * node_sim + 0.5 * edge_sim


