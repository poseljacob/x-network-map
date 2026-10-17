"""Stress-based layout: screen distance tracks network distance.

Edge length = 1/sqrt(tie strength), so strong ties sit closer. Kamada-Kawai
places every pair of people at a distance that approximates their shortest
weighted path. The center handle is translated to the origin afterwards;
nothing else is pinned or grouped.

Reads data/config.json, data/nodes.json, data/ties.json. Writes data/positions.json.
Needs networkx and scipy (see requirements.txt).

Usage: python3 pipeline/layout.py data
"""
import json, math, os, sys, time
import networkx as nx

data = sys.argv[1]
cfg = json.load(open(os.path.join(data, "config.json")))
nodes = json.load(open(os.path.join(data, "nodes.json")))
T_ = json.load(open(os.path.join(data, "ties.json")))
me = {n["id"].lower(): n["id"] for n in nodes}[cfg["handle"].lower()]

G = nx.Graph()
for n in nodes:
    G.add_node(n["id"])
for a, b, w in T_["edges"]:
    G.add_edge(a, b, w=w, len=1.0 / math.sqrt(w))

t0 = time.time()
pos = {}
# lay out each connected component separately; isolated pieces get placed around the main one
components = sorted(nx.connected_components(G), key=len, reverse=True)
for i, comp in enumerate(components):
    H = G.subgraph(comp)
    if len(comp) == 1:
        p = {next(iter(comp)): (0.0, 0.0)}
    else:
        init = nx.spring_layout(H, weight="w", seed=7, iterations=80)
        p = nx.kamada_kawai_layout(H, weight="len", pos=init, scale=1.0)
    if i == 0:
        pos.update({k: (float(v[0]), float(v[1])) for k, v in p.items()})
    else:
        ang = 2 * math.pi * i / max(1, len(components) - 1)
        pos.update({k: (float(v[0]) * 0.3 + 1.6 * math.cos(ang), float(v[1]) * 0.3 + 1.6 * math.sin(ang)) for k, v in p.items()})
print(f"layout done in {time.time() - t0:.0f}s, {len(components)} component(s)", file=sys.stderr)

mx, my = pos[me]
out = {k: [v[0] - mx, v[1] - my] for k, v in pos.items()}
json.dump(out, open(os.path.join(data, "positions.json"), "w"))
print(f"positions for {len(out)} people")
