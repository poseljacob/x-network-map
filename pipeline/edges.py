"""Tie strength from directed, typed interactions.

For each pair of map accounts, every directed interaction adds
    type_weight × (1 + ln(count)) × penalty
where penalty discounts a one-way interaction aimed at a much larger audience:
    penalty = min(1, (followers_from + 1000) / (followers_to + 1000))
A reply from a 30K account to a 1M account counts about 3% of a reply between
peers; anything a larger account sends a smaller one counts in full. Replies
that go both ways add an unpenalized bonus, because a conversation is the
strongest sign two people can reach each other.

Also records, per account, how many different people they replied to in the
posts that were sampled, so the page can show who answers people.

Reads data/nodes.json and data/interactions.json. Writes data/ties.json.

Usage: python3 pipeline/edges.py data
"""
import json, math, os, sys
from collections import defaultdict

data = sys.argv[1]
nodes = json.load(open(os.path.join(data, "nodes.json")))
inter = json.load(open(os.path.join(data, "interactions.json")))

TYPE_W = {"reply": 3.0, "quote": 2.0, "mention": 1.5, "repost": 1.0}
THRESHOLD = 1.0   # a tie at or above this counts as a real connection for "steps"
FLOOR = 0.05      # weakest tie kept, so a mentioned celebrity still has a place on the map

canon = {n["id"].lower(): n["id"] for n in nodes}
followers = {n["id"]: n["followers"] for n in nodes}

def penalty(a, b):
    # unknown follower count on either side: no discount, rather than treating it as zero
    if followers[a] is None or followers[b] is None:
        return 1.0
    return min(1.0, (followers[a] + 1000) / (followers[b] + 1000))

pair_w = defaultdict(float)
replies = defaultdict(int)
out_targets, out_replies, in_sources, posted = defaultdict(set), defaultdict(int), defaultdict(set), set()
for r in inter:
    a, b = canon.get(r["from"].lower()), canon.get(r["to"].lower())
    t, c = r["type"], max(1, int(r["count"]))
    if a:
        posted.add(a)
        if t == "reply":
            out_targets[a].add(r["to"].lower()); out_replies[a] += c
    if b and t == "reply":
        in_sources[b].add(r["from"].lower())
    if not a or not b or a == b or t not in TYPE_W:
        continue
    key = tuple(sorted((a, b)))
    pair_w[key] += TYPE_W[t] * (1 + math.log(c)) * penalty(a, b)
    if t == "reply":
        replies[(a, b)] += c

for (a, b) in list(pair_w):
    both = min(replies.get((a, b), 0), replies.get((b, a), 0))
    if both:
        pair_w[(a, b)] += TYPE_W["reply"] * (1 + math.log(both))

edges = [[a, b, round(max(w, FLOOR), 3)] for (a, b), w in pair_w.items()]

reciprocal = defaultdict(int)
for (a, b) in replies:
    if replies.get((b, a)):
        reciprocal[a] += 1
direction = {n["id"]: {
    "known": n["id"] in posted,
    "out_targets": len(out_targets[n["id"]]),
    "out_replies": out_replies[n["id"]],
    "in_sources": len(in_sources[n["id"]]),
    "reciprocal": reciprocal[n["id"]],
} for n in nodes}

json.dump({"edges": edges, "threshold": THRESHOLD, "direction": direction}, open(os.path.join(data, "ties.json"), "w"))
strong = sum(1 for e in edges if e[2] >= THRESHOLD)
print(f"ties {len(edges)}; real (>= {THRESHOLD}) {strong}; accounts with reply-out data {sum(1 for d in direction.values() if d['known'])}")
