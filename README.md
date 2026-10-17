# X network map

A map of your X network built from public interactions, with you in the middle. Distance between two people tracks how strongly they are tied; color shows what each person talks about; size switches between followers and last-30-day views. Click any segment to see who carries you into it, which of your contacts can introduce you, and who the hubs are. Search for anyone to see your shortest path to them.

The output is one HTML file. Open it locally or put it on any static host.

## How it works

1. An agent with X access (a Grok bot, or any agent with X API tools) collects your public interactions, your top contacts' interactions, and everyone's profile. `prompts/collect-with-grok.md` is the prompt to give it. The files it writes are described in `docs/data-contract.md`.
2. `run.sh` turns those files into the map:
   - `prepare.py` decides who is on the map (everyone with a profile and at least one interaction).
   - `edges.py` turns directed, typed interactions into one tie strength per pair.
   - `analyze.py` labels topics from bios, counts steps from you over real ties, and ranks bridges, doors and hubs per segment.
   - `layout.py` places people so screen distance approximates network distance (stress layout, no clusters imposed).
   - `build.py` writes `site/index.html` from `site/template.html`.

## Quick start

```bash
git clone https://github.com/poseljacob/x-network-map.git
cd x-network-map
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
# put config.json, interactions.json, profiles.json, seeds.json (and optionally impressions_30d.json) in data/
PYTHON=.venv/bin/python ./run.sh
open site/index.html
```

The layout step takes about 10 seconds for 600 people and about a minute for 1,500.

## Getting the data

Copy `prompts/collect-with-grok.md` into a chat with an agent that can read X, replace `YOUR_HANDLE` and `OUTPUT_FOLDER`, and let it run. It pulls:

- your last 300 posts (or 90 days) and everything that mentions, replies to, quotes or reposts you
- your top 40 contacts' last 100 posts and 25 recent mentions of each
- display name, bio, follower count and photo for everyone seen
- optionally, 30-day views for the 200 most active accounts

Everything is public data. The prompt tells the agent to prefer free calls and to stop and report before any paid call.

You can also write the files yourself from the X API or an export. Only the file shapes matter.

## What the numbers mean

A tie between two people is the sum over every interaction of `type weight × (1 + ln(count)) × audience penalty`:

- replies count 3, quotes 2, mentions 1.5, reposts 1
- the audience penalty is `min(1, (followers_from + 1000) / (followers_to + 1000))`, so a reply from a 30K account to a 1M account counts about 3% of a reply between peers, and anything a larger account sends a smaller one counts in full
- replies that go both ways add an unpenalized bonus

A tie of 1.0 or more is a real connection. Steps from you are counted over real ties only, so a one-way mention of a celebrity is not a path. The "find a path" search allows weak ties but shows them dashed in red.

Topics come from bio keywords (DTC, AI, VC, Marketing by default; edit `data/topics.json` to change them) and spread along ties for people whose bio says nothing.

## Privacy

`data/` and `site/index.html` are ignored by git. The repo ships the tool, not anyone's network. The page you build embeds names, bios, follower counts and photo URLs of the people on it, all from public profiles; treat the built page the way you would treat any public list of your contacts.

## License

MIT.
