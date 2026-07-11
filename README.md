# Dilly Medical

The Dilly concept, pointed at med school: an honest, personal read on where an
undergraduate pre-med actually stands — and what to do about it. Not a school
ranker, not an essay mill. It knows the student (their real hours, moments, and
facts) and uses that to read them against real matriculant numbers, scout
specific schools, and turn their own lived moments into application prose.

**The wedge:** the hours ledger. Every pre-med tracks clinical / shadowing /
research / service hours in a miserable spreadsheet, then two years later
scrapes their memory for essay anecdotes. Dilly Medical captures both in one
15-second log after each shift ("anything stick with you today?"). Logging is
permanently free — it is the data moat. By application season the student has a
verified hours ledger AND a dated bank of real moments no ChatGPT essay can fake.

## The mental model (inherited from career Dilly)

AI actions are **Moves** from one shared counter:

| Plan | Moves | Bucket |
|---|---|---|
| Starter (free) | 5 / week | account-anchored weekly |
| Dilly | 120 / month | account-anchored 30-day |
| Pro | unlimited | — |

Moves: **Readiness Read** (where you stand, five dimensions), **School Scout**
(how you fit one school), **Craft** (W&A descriptions + personal statement
skeletons from your real material). Out of Moves → HTTP 402 → the mobile
paywall opens automatically. The hours ledger, opportunities feed, weekly
brief, facts, and plan are never metered.

Hard product rules (see `docs/COPY_DOCTRINE.md`): undergraduate-only, zero
fabrication (every generated claim cites a `[F#]` fact or `[H#]` log entry),
never a numeric admission chance, never Caribbean schools, no markdown emphasis
in Dilly's voice.

## v0.2 — what's new

- **60+ med schools** (`med_schools.json` + `med_schools_extended.json`) with mission tags, IS/OOS logic, School Scout
- **Secondary essay Craft** — generic + per-school prompts; drafts from real facts only (`/secondaries/craft`)
- **MMI interview practice** — 8 station bank, voice or typed answers, AI feedback (`/interview/*`)
- **Voice reflection capture** — `expo-speech-recognition` on Hours tab; stored as `voice_transcript`
- **Live opportunity crawler** — NSF REU, USAJobs health trainees, ScribeAmerica, Idealist → `live_opportunities` table; daily GitHub Action
- **Postgres on Railway** — set `DATABASE_URL`; SQLite remains the local default
- **TestFlight** — `mobile/build1001.sh` (after `npx expo prebuild --platform ios`)

## Deploy to Railway

Run each command on its own line (do not paste `#` comment lines into the terminal).

```bash
cd dilly-medical
railway login                    # re-auth if token expired
railway init                     # new project, or: railway link
railway add --database postgres  # Railway v5 CLI (not --plugin)
railway variables set ANTHROPIC_API_KEY=sk-... CRON_SECRET=your-secret DILLY_MED_DEV=0
railway up
railway domain                   # optional: generate public URL
```

Railway reads `railway.json` + `Dockerfile`; health check at `/health`.
Point mobile: `EXPO_PUBLIC_MED_API_BASE=https://<your-railway-domain>`.

## Standalone GitHub repo

```bash
bash dilly-medical/scripts/create-github-repo.sh
```

Uses HTTPS (not SSH). Creates or updates `github.com/Dilan1234321/dilly-medical` via `git subtree split`.

## TestFlight (iOS)

```bash
cd dilly-medical/mobile
npm install
npx expo install expo-speech-recognition expo-dev-client
npx expo prebuild --platform ios
chmod +x build1001.sh
# Founder runs when ready:
ASC_API_KEY=... ASC_ISSUER=... ./build1001.sh
```

Native rebuild required for voice (`expo-speech-recognition`). Simulator can type reflections until then.

## Repo layout

```
dilly-medical/
├── api/                  # FastAPI backend (SQLite; Postgres-ready schema)
│   ├── main.py           # app + router mounts + startup migrations
│   ├── moves.py          # Moves metering (402 contract)
│   ├── billing_period.py # account-anchored buckets (career-Dilly semantics)
│   ├── readiness.py      # Readiness Read engine (rule-based, LLM-warmed)
│   ├── school_fit.py     # School Scout engine
│   ├── amcas_calendar.py # cycle phase engine (timing intelligence)
│   ├── benchmarks.py     # AAMC-approximate benchmark bands
│   ├── data/             # schools (60+), secondaries, MMI stations, opportunities
│   ├── crawler/          # live opportunity ingest
│   └── routers/          # auth, hours, readiness, schools, secondaries, interview, cron, …
├── mobile/               # Expo / React Native app (expo-router, SDK 55)
│   ├── app/              # onboarding + (app)/ tabs: Home, Hours, Schools, You
│   ├── components/       # UI primitives (chunky buttons, DillyFace), paywall
│   ├── hooks/usePaywall  # global paywall pub/sub
│   └── lib/api.ts        # client with 402 paywall interception
├── tests/                # pytest (20 tests: metering, readiness, scout, craft)
└── docs/                 # PRODUCT.md, COPY_DOCTRINE.md
```

## Run it

Backend (Python 3.11+):

```bash
cd dilly-medical
pip install -r api/requirements.txt
uvicorn api.main:app --reload --port 8100
# docs at http://localhost:8100/docs
```

Dev mode is on by default (`DILLY_MED_DEV=1`): `/auth/send-code` returns the
code in the response. Set `ANTHROPIC_API_KEY` to enable LLM-warmed narratives;
everything works without it (deterministic fallbacks).

Mobile:

```bash
cd dilly-medical/mobile
npm install
EXPO_PUBLIC_MED_API_BASE=http://<your-ip>:8100 npx expo start
```

Tests:

```bash
cd dilly-medical && python3 -m pytest tests/ -q
```

## Verifying changes (same habits as career Dilly)

- Backend: `python3 -m pytest tests/` — pure logic has real tests.
- Mobile: `npx tsc --noEmit` plus the per-file Babel transpile sweep before
  any build (`node -e 'require("@babel/core").transformFileSync(...)'`).

## Splitting into its own repository

This directory is fully self-contained (no imports from `projects/dilly`).
To extract it with history into a new repo:

```bash
git subtree split --prefix=dilly-medical -b dilly-medical-standalone
mkdir ../dilly-medical && cd ../dilly-medical && git init
git pull ../dilly-workspace dilly-medical-standalone
git remote add origin git@github.com:<you>/dilly-medical.git && git push -u origin main
```

## What's deliberately NOT here yet (next phases)

- **Voice capture** for reflections (mic-first logging — the data model and
  prompts are already shaped for it; expo-av/expo-speech next).
- **Stripe Payment Links** (`mobile/lib/pricing.ts` has the slots; the dev
  plan-switch endpoint exercises the full paywall loop until then).
- **Live opportunity crawler** (scribe companies, hospital volunteer portals,
  REU/SURP deadlines) replacing the structural catalog — same architecture as
  career Dilly's jobs crawler.
- **MMI / interview practice** via voice chat (career Dilly's AI overlay is the
  blueprint).
- **MSAR-licensed school data** — the bundled dataset is approximate public
  aggregates with an explicit data note; a licensed feed upgrades it.
- **Push notifications** (submit-window timing nudges are the killer use).
