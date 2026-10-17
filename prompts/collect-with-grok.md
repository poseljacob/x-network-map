# Collection prompt for a Grok agent (or any agent with X access)

Copy everything below the line into a chat with an agent that can read X: a Grok bot, or a Claude or Codex agent with X API tools. Replace `YOUR_HANDLE` with the account you want at the center of the map, and `OUTPUT_FOLDER` with where the files should land (a local folder, a shared drive, or an HQ vault path).

The prompt asks for public data only, writes five files in a fixed shape, and tells the agent to prefer free calls and report before spending money. The full file shape is in `docs/data-contract.md`; the prompt repeats the parts the agent needs.

---

I'm building a map of my X network. Please collect the data for it and write the files described below into `OUTPUT_FOLDER`. My handle is `YOUR_HANDLE`.

Use only public data: public posts, public replies, public profile fields, public counts. Do not invent or infer any value. When something is unavailable (private account, suspended, rate-limited), write `null` and say so in the report.

Work in this order. Each step builds on the one before. If you run out of free calls, stop at a clean point, save what you have, tell me what remains, and continue when the limit resets. Make every step resumable so nothing is pulled twice.

## Step 1: my own activity

Pull my last 300 posts, or everything from the last 90 days, whichever is more. Include my replies, quotes and reposts. For each post record who I interacted with:

- a reply to someone's post → `reply` from me to them
- a quote of someone's post → `quote` from me to them
- a repost of someone's post → `repost` from me to them
- anyone I mentioned in a post that is not a reply to them and not a quote of them → `mention` from me to them

Then search for posts by other people that mention me, reply to me, quote me or repost me in the same window, and record those the same way in the other direction (from them, to me).

## Step 2: pick the seeds

Rank everyone from step 1 by how much we interacted (replies and quotes count 3, mentions 2, reposts 1, in either direction). Take the top 40 as "seeds". Write their handles to `seeds.json`. If I named a target person in this conversation, add them as a seed even if we never interacted.

## Step 3: the seeds' activity

For each seed, pull their last 100 posts including replies, and record their interactions with anyone the same way as step 1. Also pull up to 25 recent posts by other people that mention or reply to the seed, and record those.

This is what tells the map who talks to whom beyond me. Keep every interaction, even with accounts that never appear again; the pipeline decides who stays on the map.

## Step 4: profiles

For every account that appears in any interaction from steps 1 to 3, collect: display name, bio, current follower count, and profile image URL. Change `_normal` in the image URL to `_200x200`. One lookup can usually cover 100 handles at a time; batch them.

## Step 5: 30-day views (optional, do last)

For me and for the 200 accounts with the most interactions in the data, sum the impression counts of their original posts and replies (not reposts) from the last 30 days. Cap at 100 posts per account; if an account posted more than 100 times in the window, extrapolate from the 100 and mark `estimated: true`. This step is the most expensive. If it needs paid calls, stop and tell me the estimated cost before pulling anything.

## Files to write

Write all handles without the `@`, in the capitalization X shows. No self-interactions. No duplicate rows.

`config.json`

```json
{"handle": "YOUR_HANDLE", "title": "My X network", "collected": "YYYY-MM-DD"}
```

`interactions.json`: a list of rows, one per (from, to, type), with `count` = how many times and `last` = ISO date of the most recent.

```json
[{"from": "YOUR_HANDLE", "to": "someone", "type": "reply", "count": 3, "last": "2026-10-15T12:58:15Z"}]
```

`profiles.json`: one entry per account seen in the interactions.

```json
{"someone": {"name": "Some One", "bio": "What their bio says", "followers": 12345, "img": "https://pbs.twimg.com/profile_images/.../x_200x200.jpg"}}
```

`seeds.json`: the handles from step 2.

```json
["seed_one", "seed_two"]
```

`impressions_30d.json` (only if step 5 ran): a `_meta` object with the window, the generation time, how many accounts are done out of how many, and a note on the method; then one entry per account.

```json
{"_meta": {"window": ["2026-09-17T00:00:00Z", "2026-10-17T23:59:59Z"], "generated": "2026-10-17T13:50:28Z", "done": 201, "total": 201, "note": "original posts + replies, no reposts; capped at 100 posts per account"},
 "someone": {"impressions_30d": 125300, "posts_30d": 41, "estimated": false}}
```

## Rules

- Prefer free calls. Before any paid call, tell me the estimated cost and wait for my yes.
- Never guess a number. Unknown is `null`.
- Keep the raw API responses you fetched in a `cache/` folder next to the output, so the pull can be refreshed without re-fetching everything.
- When you finish, or when you stop for a limit, send me a short report: posts read, accounts seen, interactions recorded, seeds chosen, which steps are complete, and what it would cost to finish the rest.

## Report format

```
Pull for @YOUR_HANDLE, DATE
- Step 1: N of my posts, M posts mentioning me
- Step 2: 40 seeds (list the top 10)
- Step 3: K seeds done of 40; P posts read
- Step 4: profiles for A of B accounts
- Step 5: views for C accounts (or: not started; estimated cost $X)
Files written: config.json, interactions.json (R rows), profiles.json, seeds.json[, impressions_30d.json]
Remaining: ...
```
