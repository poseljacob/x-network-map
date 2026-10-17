"""Assemble the self-contained map page.

Reads everything in data/ plus site/template.html. Writes site/index.html.

Usage: python3 pipeline/build.py data site
"""
import json, os, sys

data, site = sys.argv[1], sys.argv[2]
P = lambda name: os.path.join(data, name)
cfg = json.load(open(P("config.json")))
nodes_list = json.load(open(P("nodes.json")))
T_ = json.load(open(P("ties.json")))
pos = json.load(open(P("positions.json")))
an = json.load(open(P("analysis.json")))
inter = json.load(open(P("interactions.json")))
seeds = json.load(open(P("seeds.json"))) if os.path.exists(P("seeds.json")) else []
impr = json.load(open(P("impressions_30d.json"))) if os.path.exists(P("impressions_30d.json")) else {}
impr_meta = impr.pop("_meta", {})
impr = {k.lower(): v for k, v in impr.items()}

ext = max(max(abs(x), abs(y)) for x, y in pos.values()) or 1
SCALE = 1900 / ext

nodes = []
for n in nodes_list:
    nid = n["id"]
    im = impr.get(nid.lower()) or {}
    x, y = pos[nid]
    nodes.append({
        "id": nid, "name": n["name"], "img": n["img"], "followers": n["followers"],
        "impressions": im.get("impressions_30d"), "posts": im.get("posts_30d"), "estimated": bool(im.get("estimated")),
        "bio": n["bio"], "seed": n["seed"],
        "x": round(x * SCALE, 1), "y": round(y * SCALE, 1),
        "topic": an["topic_of"][nid], "scores": an["score"][nid],
        "hops": an["hops"].get(nid, 9), "via": an["via"].get(nid, []),
        "degree": an["degree"][nid],
        "seg": {t: an["seg"][t][nid] for t in an["topics"]},
        "dir": an["direction"][nid],
    })

payload = {
    "me": an["me"],
    "title": cfg.get("title") or f"@{an['me']}'s X network",
    "collected": cfg.get("collected", ""),
    "topics": an["topics"], "topicNames": an["topicNames"], "topicColors": an["topicColors"],
    "nodes": nodes,
    "edges": T_["edges"], "threshold": T_["threshold"],
    "summary": an["summary"],
    "interactions": sum(int(r.get("count", 1)) for r in inter),
    "seeds": len(seeds),
    "imprDone": impr_meta.get("done", len(impr)),
}
html = open(os.path.join(site, "template.html")).read().replace("/*__DATA__*/null", json.dumps(payload, separators=(",", ":")))
out = os.path.join(site, "index.html")
open(out, "w").write(html)
print(f"wrote {out}: {len(nodes)} people, {len(payload['edges'])} ties")
