"""Topic labels, steps from the center, and segment metrics.

Topics start from bio keywords (data/topics.json, or four defaults), then
spread along ties for people whose bio says nothing. Steps from the center
handle are counted over real ties only (strength >= threshold), so a one-way
mention of a celebrity is not a path.

Per segment, each person gets: ties into the segment, an influence rank
(people with at least two real ties in the segment, ranked by ties and
audience), and, for the center's direct ties, a bridge score.

Reads data/config.json, data/nodes.json, data/ties.json. Writes data/analysis.json.

Usage: python3 pipeline/analyze.py data
"""
import json, math, os, re, sys
from collections import defaultdict, deque

data = sys.argv[1]
cfg = json.load(open(os.path.join(data, "config.json")))
nodes_list = json.load(open(os.path.join(data, "nodes.json")))
T_ = json.load(open(os.path.join(data, "ties.json")))
topics_path = os.path.join(data, "topics.json")

DEFAULT_TOPICS = [
    {"key": "DTC", "name": "DTC & ecommerce", "color": "#e0874f",
     "regex": r"\b(dtc|d2c|ecom\w*|e-commerce|ecommerce|shopify|retention|cpg|brands?|store|amazon|tiktok shop|subscription|klaviyo|3pl|merch|consumer)\b"},
    {"key": "AI", "name": "AI & builders", "color": "#4f8fd6",
     "regex": r"\b(ai|agents?|agentic|llms?|claude|gpt|openai|anthropic|ml|machine learning|codex|cursor|vibe|coding|developer|engineer(ing)?|software|dev tools?|replit|open ?source)\b"},
    {"key": "VC", "name": "VC & investors", "color": "#4fae86",
     "regex": r"\b(vc|investor|investing|invest|venture|partner @|fund|a16z|yc|y ?combinator|angel|seed|portfolio|capital)\b"},
    {"key": "Marketing", "name": "Marketing & creators", "color": "#b07cc6",
     "regex": r"\b(marketing|marketer|creators?|newsletter|content|growth|ads?|advertis\w*|copywrit\w*|media|podcast|host|audience)\b"},
]
TOPICS = json.load(open(topics_path)) if os.path.exists(topics_path) else DEFAULT_TOPICS
T = [t["key"] for t in TOPICS]
RX = {t["key"]: re.compile(t["regex"], re.I) for t in TOPICS}

nodes = {n["id"]: n for n in nodes_list}
canon = {h.lower(): h for h in nodes}
ME = canon[cfg["handle"].lower()]
THR = T_["threshold"]
adj = defaultdict(dict); strong = defaultdict(dict)
for a, b, w in T_["edges"]:
    adj[a][b] = w; adj[b][a] = w
    if w >= THR:
        strong[a][b] = w; strong[b][a] = w

# --- topic scores: bio seeds + propagation over ties ---
bio_score = {}
for nid, n in nodes.items():
    hits = {t: len(RX[t].findall(n["bio"] or "")) for t in T}
    s = sum(hits.values())
    bio_score[nid] = {t: hits[t] / s for t in T} if s else None
score = {nid: (dict(bs) if bs else {t: 0.0 for t in T}) for nid, bs in bio_score.items()}
for _ in range(12):
    nxt = {}
    for nid in nodes:
        nb = adj[nid]; tot = sum(nb.values())
        avg = {t: (sum(w * score[o][t] for o, w in nb.items()) / tot if tot else 0.0) for t in T}
        nxt[nid] = {t: 0.6 * bio_score[nid][t] + 0.4 * avg[t] for t in T} if bio_score[nid] else avg
    score = nxt
def primary(nid):
    s = score[nid]; best = max(T, key=lambda t: s[t])
    return best if s[best] > 0.15 else "Other"
topic_of = {nid: primary(nid) for nid in nodes}

# --- steps from the center over real ties; connectors for people two steps out ---
hops = {ME: 0}; via = defaultdict(set); q = deque([ME])
while q:
    cur = q.popleft()
    for nb in strong[cur]:
        if nb not in hops:
            hops[nb] = hops[cur] + 1; q.append(nb)
        if hops[nb] == 2 and hops[cur] == 1:
            via[nb].add(cur)

followers = {nid: (n["followers"] or 0) for nid, n in nodes.items()}

def pct_rank(values):
    order = sorted(values.items(), key=lambda kv: kv[1]); r = {}
    for i, (k, _) in enumerate(order):
        r[k] = i / max(1, len(order) - 1)
    return r

members = {t: [nid for nid in nodes if topic_of[nid] == t or score[nid][t] >= 0.35] for t in T}
seg = {t: {} for t in T}
for t in T:
    mset = set(members[t])
    ties = {nid: sum(w for o, w in adj[nid].items() if o in mset) for nid in nodes}
    deg_in = {nid: sum(1 for o in strong[nid] if o in mset) for nid in nodes}
    hub_pool = [k for k in mset if deg_in[k] >= 2 and k != ME]
    deg_rank = pct_rank({k: deg_in[k] + 0.1 * ties[k] for k in hub_pool})
    reach_rank = pct_rank({k: math.log10(followers[k] + 10) for k in hub_pool})
    for nid in nodes:
        rec = {"ties": round(ties[nid], 1), "deg": deg_in[nid]}
        if nid in hub_pool:
            rec["influence"] = round(math.sqrt(deg_rank[nid] * reach_rank[nid]), 3)
        if hops.get(nid) == 1:
            rec["bridge"] = round(math.log1p(deg_in[nid]) * math.log10(followers[nid] + 10), 3)
        seg[t][nid] = rec

me_weight = defaultdict(float)
for o, w in strong[ME].items():
    me_weight[topic_of[o]] += w
tot_w = sum(me_weight.values())

summary = {}
for t in T:
    mset = set(members[t])
    direct = [o for o in strong[ME] if o in mset]
    two = [nid for nid in mset if hops.get(nid) == 2]
    summary[t] = {
        "members": len(mset), "direct": len(direct), "two_hop": len(two),
        "share_of_my_weight": round(me_weight[t] / tot_w, 3) if tot_w else 0,
        "hubs": sorted([nid for nid in mset if "influence" in seg[t][nid]], key=lambda n: -seg[t][n]["influence"])[:12],
        "bridges": sorted([nid for nid in strong[ME] if seg[t][nid]["deg"] > 0], key=lambda n: -seg[t][n]["bridge"])[:10],
        "doors": sorted(two, key=lambda n: -(math.log10(followers[n] + 10) * math.log1p(seg[t][n]["deg"])))[:10],
    }

out = {
    "me": ME,
    "topics": T,
    "topicNames": {t["key"]: t["name"] for t in TOPICS},
    "topicColors": {t["key"]: t["color"] for t in TOPICS},
    "topic_of": topic_of,
    "score": {nid: {t: round(v, 3) for t, v in s.items()} for nid, s in score.items()},
    "hops": hops,
    "via": {k: sorted(v, key=lambda c: -strong[ME][c])[:3] for k, v in via.items()},
    "degree": {nid: len(strong[nid]) for nid in nodes},
    "seg": seg, "summary": summary, "direction": T_["direction"], "threshold": THR,
}
json.dump(out, open(os.path.join(data, "analysis.json"), "w"))
print("steps:", {h: sum(1 for v in hops.values() if v == h) for h in range(0, 8)}, "no close path:", sum(1 for nid in nodes if nid not in hops))
print({t: (len(members[t]), summary[t]["direct"], summary[t]["two_hop"], summary[t]["share_of_my_weight"]) for t in T})
