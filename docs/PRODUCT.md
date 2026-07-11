# Dilly Medical — Product Spec (v0.1)

## The promise

In an admissions process that rejects ~60% of all applicants with no
explanation, tell an undergraduate pre-med the honest truth about where they
stand and what to do about it — personally, for *this* student, four years
before a consultant would even take their money.

## Why this transfers from career Dilly

- Same soul: honest reads, real facts, one concrete move at a time.
- Better market: pain is acute (opacity + fear), the audience self-identifies
  freshman year (3-4 year LTV), and families already pay consultants
  $3,000-$10,000+ — $8.99/mo is an impulse purchase against that anchor.
- Stronger moat: the application literally IS a ledger of facts (AMCAS Work &
  Activities) plus essays grounded in lived moments. Whoever holds the
  longitudinal record wins, and nobody else is there from freshman year.

## Surfaces (v0.1, shipped)

1. **Home** — Moves counter, "where you stand" band teaser (from last read),
   cycle-aware weekly brief (AMCAS calendar engine), open-lane card into
   Opportunities, plan count.
2. **Hours (the wedge)** — 15-second shift logging with the reflection prompt
   ("anything stick with you today?"). Totals by category. Always free.
3. **Schools** — 29-school MD/DO dataset (approximate medians + mission tags +
   IS/OOS preference), save to list, **School Scout** (Move): verdict
   (likely/target/reach/far_reach — never a percentage), fact-cited why
   bullets, residency warnings, one move.
4. **You** — numbers (GPA/MCAT), story facts by category, the plan
   (check-off list fed by "Add to plan" everywhere), tools, sign out.
5. **Readiness Read** (Move) — five dimensions (Stats, Clinical, Shadowing,
   Research & Service, Story), each a band + evidence citing [F#]/[H#] + one
   move. History endpoint tracks band progression over time.
6. **Opportunities** — structural catalog (scribe, EMT, CNA, hospice, free
   clinics, REU/SURP, SHPEP, crisis lines...) ranked by THIS student's gaps,
   each with "why I picked this" chips.
7. **Craft** (Move) — W&A activity descriptions and personal statement
   skeletons built ONLY from logged reflections and facts. Where evidence is
   thin it says `[you need a real moment here]` instead of inventing one.

## Moves & pricing

One shared counter (`users.move_count` + account-anchored bucket key), exact
career-Dilly semantics. Starter 5/week; Dilly 120/month ($8.99, $5.99 .edu);
Pro unlimited ($14.99, $9.99 .edu). 402 → global paywall. Hours ledger, brief,
opportunities, facts, plan: never metered.

## The honesty line

"You would not get in today" must always land as "here's the gap and here's
the move." Bands, not verdicts; evidence, not judgment; one move, not a
lecture. Full rules in COPY_DOCTRINE.md.

## Roadmap (post v0.1)

- **Phase 1 — voice**: mic-first reflection capture; MMI practice prompts.
- **Phase 2 — live data**: opportunity crawler (scribe cos., hospital
  volunteer portals, REU deadlines); MSAR-licensed school data; secondaries
  prompt database.
- **Phase 3 — application year mode**: submit-window push nudges, secondary
  turnaround tracker, interview scheduler, update-letter drafting.
- **Phase 4 — the loop closes**: outcomes data (who got in where with what
  ledger) makes the Readiness Read self-calibrating — the thing no consultant
  can ever have.
