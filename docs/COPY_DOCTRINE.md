# Dilly Medical — Copy Doctrine

These rules are load-bearing. They are enforced in code where possible
(`api/llm.py` NO_FABRICATION_RULES, tests in `tests/`), but every human and
agent writing copy follows them too.

## Hard rules (never violate)

1. **No fabrication, ever.** Every generated claim traces to a numbered
   profile fact [F#] or hours-log entry [H#]. AMCAS falsification ends
   careers; our no-fabrication rule is a selling point, not a constraint.
   Where evidence is thin, Craft writes `[you need a real moment here]`.
2. **Never a numeric admission chance.** No percentages, no scores, no
   "78% match." Bands only: getting_started / building / on_track / strong;
   verdicts only: likely / target / reach / far_reach / incomplete.
3. **Undergraduate applicants only.** The user is an undergrad (or fresh
   grad in a gap year) applying to MD/DO programs. No MBA/PhD/postdoc copy.
4. **Never recommend Caribbean medical schools.** They are not in the
   dataset and must not be suggested. DO schools are first-class citizens.
5. **Dilly's voice uses no markdown emphasis.** No bold, italics, or
   headers in chat/read copy. Plain sentences.
6. **Every read ends in one concrete move** the student can take this week.
   Not three. One.

## Tone rules

- **Honest, never cruel.** "You would not get in today" always lands as
  "here's the gap, and here's the move." The read is a coach's film review,
  not a rejection letter.
- **Empty states INVITE.** "Let's build your record" — never "0 hours logged."
- **The student wields the process; the process doesn't happen to them.**
  Timing intelligence (submit windows, secondary turnarounds) is framed as
  their edge, not another anxiety.
- **Speak to them directly.** "Your GPA is doing its job" not "the user's
  GPA is sufficient."
- **The hours-log promise is sacred copy:** logging is always free, forever.
  Say it at the paywall, in onboarding, on the Hours tab.

## Data honesty

- School medians and national benchmarks are approximate public aggregates.
  Every payload that uses them carries a `data_note` telling students to
  verify in MSAR. Never present seed data as authoritative.
- Timing guidance ("submit early June") is presented as rolling-admissions
  strategy, not a guarantee.
