# Data contract

The pipeline reads five files from `data/`. Any collector that writes them in this shape works: the Grok agent prompt in `prompts/`, your own X API script, or a hand-made export.

Handles are written without the `@`, in the capitalization X shows. Matching is case-insensitive downstream, so `JacobPosel` and `jacobposel` are the same person.

## `data/config.json`

```json
{
  "handle": "jacob_posel",
  "title": "Jacob's X network",
  "collected": "2026-10-17"
}
```

`handle` is the account the map is centered on. `title` is the page heading. `collected` is the date of the pull, shown on the page.

## `data/interactions.json`

Every directed public interaction found in the pull, one row per (from, to, type).

```json
[
  {"from": "jacob_posel", "to": "codyplof", "type": "reply", "count": 12, "last": "2026-10-15T12:58:15Z"},
  {"from": "codyplof", "to": "jacob_posel", "type": "quote", "count": 1, "last": "2026-09-30T18:02:00Z"}
]
```

- `type` is one of `reply`, `quote`, `mention`, `repost`.
- `reply`: `from` replied to a post by `to`.
- `quote`: `from` quote-posted a post by `to`.
- `mention`: `from` mentioned `to` in a post that was not a reply to `to` and not a quote of `to`.
- `repost`: `from` reposted a post by `to`.
- `count` is how many times that happened in the pull. `last` is the ISO date of the most recent one.
- No self rows. No duplicate (from, to, type) rows.

## `data/profiles.json`

One entry per account that appears in `interactions.json` and should be on the map.

```json
{
  "codyplof": {
    "name": "Cody Plofker",
    "bio": "Dad of 2. Co-host of Marketing Operators.",
    "followers": 71848,
    "img": "https://pbs.twimg.com/profile_images/.../photo_200x200.jpg"
  }
}
```

- `img` is the profile image URL. Replace `_normal` in the URL X gives you with `_200x200`. Empty string if unknown.
- `followers` is the current follower count. Use `null` if unknown; never guess.
- Accounts that appear in `interactions.json` but not here are left off the map, and interactions with them are ignored. Collect a profile for everyone you want shown.

## `data/seeds.json`

The accounts whose own posts were pulled (beyond the center handle). The page uses the count to explain which ties are well covered.

```json
["codyplof", "VibeMarketer_", "AndrewCurran_"]
```

## `data/impressions_30d.json` (optional)

Views on each account's posts and replies over the last 30 days.

```json
{
  "_meta": {
    "window": ["2026-09-17T00:00:00Z", "2026-10-17T23:59:59Z"],
    "generated": "2026-10-17T13:50:28Z",
    "done": 207,
    "total": 1125,
    "note": "original posts + replies, no reposts; capped at 100 posts per account; estimated=true means extrapolated to the window"
  },
  "codyplof": {"impressions_30d": 1253000, "posts_30d": 41, "estimated": false},
  "someone_private": {"impressions_30d": null, "posts_30d": null, "estimated": false}
}
```

If the file is missing, the "Views, 30 days" toggle still appears and shows everyone as a small dot.

## `data/topics.json` (optional)

The segments people are colored and grouped by. Each has a key, a display name, a color, and a regular expression matched against bios (case-insensitive). People whose bio matches nothing take the topics of the people they interact with.

```json
[
  {"key": "DTC", "name": "DTC & ecommerce", "color": "#e0874f", "regex": "\\b(dtc|d2c|ecom\\w*|ecommerce|shopify|retention|cpg|brands?)\\b"},
  {"key": "AI", "name": "AI & builders", "color": "#4f8fd6", "regex": "\\b(ai|agents?|llms?|claude|gpt|openai|anthropic|coding|developer|software)\\b"}
]
```

Without this file the pipeline uses four defaults: DTC & ecommerce, AI & builders, VC & investors, Marketing & creators.

## What the pipeline produces

- `data/nodes.json`, `data/ties.json`, `data/positions.json`, `data/analysis.json`: intermediate files, safe to delete and regenerate.
- `site/index.html`: the finished map. One self-contained file; open it in a browser or put it on any static host.
