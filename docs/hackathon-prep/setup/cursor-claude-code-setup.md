# Cursor + Claude Code Setup — For the AI-Curious

> Audience: smart engineer / quant who has NOT shipped AI-generated apps before. You can write Python. You haven't lived in Flask or Leaflet. By the end of this doc you'll be productive with AI tooling in 30 minutes.
>
> The single biggest mental shift: **your job is to be the judgment, not the typist.** AI types fast. You decide what gets typed, what gets shipped, what gets thrown out.

---

## 0. Tool install (5 minutes)

**Option A: Cursor (recommended for this hackathon).** Visual editor with built-in AI. Best for someone new to AI coding.
- Download: https://cursor.com → install
- Sign in with email
- Pick model: Claude 4.7 Sonnet (default) — leave it alone

**Option B: Claude Code (CLI).** If you live in the terminal already. Slightly faster for some operations, no editor window.
- Install: `npm install -g @anthropic-ai/claude-code`
- Run from your project folder: `claude`

Use **one** consistently. Switching mid-hackathon is a tax.

---

## 1. Open the project (2 minutes)

```bash
# Clone the team repo Ongun set up
git clone https://github.com/[org]/sorted
cd sorted
cursor .     # or: claude
```

Cursor will index the codebase. Wait 30 seconds. Now the AI knows what's in the repo.

---

## 2. Mental model — what AI is GOOD at vs BAD at

| The AI is GOOD at | The AI is BAD at |
|-------------------|-------------------|
| Generating well-trod boilerplate (Flask routes, SQLite schemas, Leaflet maps) | Guessing what *you* actually want without specific direction |
| Translating "here's roughly what I want" into 100 working lines | Knowing the latest library version's syntax (sometimes it's wrong) |
| Running a fix-it loop when you paste in an error message | Telling you the *real* root cause of a bug — it'll often paper over symptoms |
| Stylistic consistency across files | Knowing what *not* to build (it loves over-engineering) |
| Refactoring with you watching | Refactoring while you go get coffee |
| Writing tests that mirror your code | Knowing what edge cases actually matter |

**Implication for the weekend:** treat AI as a senior intern. Brilliant, fast, eager to help. Will absolutely build the wrong thing if you don't tell it specifically what right looks like.

---

## 3. The anatomy of a good prompt

For this hackathon, every prompt to Cursor should have these four parts:

```
[GOAL] What you want the result to do, in one sentence.

[CONSTRAINTS] What it must use / not use. Specific library names. File paths.

[ACCEPTANCE] How you'll know it worked. Specific command or behaviour.

[CONTEXT] Anything from the codebase the AI should look at.
```

Example — bad prompt:

> *"add a map to the dashboard"*

The AI now invents a map. Maybe with React. Maybe with Mapbox (which needs API keys). Maybe in a separate file. Maybe with 200 lines.

Example — good prompt:

> *"GOAL: Add a Leaflet map to dashboard/index.html that plots every report from the /api/reports endpoint as a circle marker.*
>
> *CONSTRAINTS: Use Leaflet 1.9 from CDN, no npm. Map element should be #map, height 480px. Marker colour green if status='fixed', red if 'open'. No build step.*
>
> *ACCEPTANCE: `python dashboard/app.py` runs on :5050 and visiting / shows 100+ dots on a London-centred map.*
>
> *CONTEXT: Look at dashboard/app.py for the /api/reports JSON shape. Look at dashboard/static/style.css for the existing colour palette — use the same green and red."*

The AI now produces working code on the first or second try.

**Internalise the four parts.** You'll write 20-30 prompts on Saturday. Each one shaped like this saves you a re-prompt.

---

## 4. The Cursor flow that works on Saturday

1. **Open the file you want to edit** (or where you want the AI to write new code).
2. **Cmd+L** to open the chat. Paste your 4-part prompt.
3. AI proposes a diff. **Read it.** Don't skim. (~30 seconds of reading saves 20 minutes of debugging.)
4. If 80% right: accept, then write a follow-up prompt with what to fix. If 50% right: reject, refine the prompt, try again. **Don't iterate on a mediocre diff with vague follow-ups** — that's the rabbit-hole.
5. Run the smoke test for that component. If it fails, paste the full error message into chat and say *"this is the error after applying your change."* The AI is excellent at this loop.
6. Commit. Move on.

---

## 5. Hackathon-specific prompt patterns

When you sit down for your assigned task, the file `docs/hackathon-prep/prompts/build-prompt-*.md` will have a ready-made starter prompt for it. Paste that into Cursor's chat as your first message. Don't try to write your own prompt cold.

After the starter:
- *"Now add error handling for [specific case]"*
- *"Refactor [function name] to be 20 lines shorter"*
- *"Write a tiny smoke test in `tests/test_X.py`"*
- *"This is broken: [paste error]. Fix the cause, not the symptom."*

---

## 6. Anti-patterns — DO NOT do these

- ❌ **"Make it production-ready."** Means nothing. Decision-free. Use "make it pass `python smoke.py` without errors."
- ❌ **"Add tests."** Same problem. Use "write one test that calls `/api/reports` and asserts status 200."
- ❌ **"Refactor for clean architecture."** We do not have time. We have 14.5 hours.
- ❌ **Multi-turn "and also..."** — five things in one message. The AI does three and forgets two. One prompt, one outcome.
- ❌ **Asking for libraries we said no to** (React, Postgres, Docker). Re-read `docs/hackathon-prep/decisions-locked.md`. The stack is fixed.
- ❌ **Trusting AI on dates / counts / measurements.** It will say "this dataset has 50,000 rows" without checking. Verify any number with `wc -l` or `sqlite> SELECT COUNT(*)`.
- ❌ **Accepting a 200-line file when you asked for 50.** Reject. Re-prompt: "compress to under 60 lines."

---

## 7. Your most useful 3-line Cursor habit

Every hour, do this:

1. `git diff --stat` — what files did I touch?
2. `python smoke.py` for whatever you've been working on — does it still work?
3. Commit. *"intake: vision classifier returns category on real photo"*

If you can't run the smoke test, you don't know if you're moving forward or backward. **Run it. Commit small. Push often.**

---

## 8. When to stop talking to the AI and ask a human

- Stuck for 15 minutes → post `#sorted` Discord.
- Architecture / "should we even do X?" question → ask Ongun directly, NOT the AI.
- "Why is this slow?" — humans first. AI will guess.
- "Is this approach right?" — humans first. AI will agree with whatever you proposed.

The AI is great at *implementation*. Humans decide *direction*.

---

## You're ready

If you can paste the example prompt from Section 3 into Cursor's chat right now without re-reading this doc, you're ready for Saturday. If not, do that practice run before bed.
