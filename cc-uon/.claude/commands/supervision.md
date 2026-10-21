---
name: supervision
description: Finalise a student's pending PGR supervision-record forms as supervisor on UoN Campus.
disable-model-invocation: true
argument-hint: "<student name> [<student name> ...]"
---

# Supervision records

Conventions and browser pitfalls live in `AGENTS.md`. Students: `$ARGUMENTS` (ask if empty).

In Nottingham Campus → PGR supervision records → **Finalise pending forms**, for each student:

1. Search Student Name (or use a Saved Search); process forms by Meeting date, earliest first.
   A student with only one pending form opens straight into it, with no list.
2. Set "Did you identify any cause for concern that could prevent progression?" to **No**.
3. Write a comment on about 40% of each student's forms (rounded: 3 → 1, 14 → 6), spread
   across the dates. Base it on the student's "Progress made since last meeting" and "Agreed
   actions": one short English sentence affirming progress and naming the next focus. Leave
   the rest blank.
4. Click **Submit form** directly.
5. If submission errors on a student-owned required field (e.g. "Reason for no meeting
   in-person is required"), do not invent content: skip the form, note its Form ID and reason.
6. Report per student: submitted Form IDs, which got comments, which were skipped and why.

## Page hooks

- Concern dropdown: `G3CFG_COLUMN_G3CODE_DROP01$19`, value `N` = No; set via JS, fire `change`.
- Student text: textareas `G3CFG_COLUMN_G3LONGRTXT_HTML01$15` (Progress), `$17` (Actions).
- Comment box: the last `.ql-editor` on the page; focus it, then type.
- Form ID links in the list: `G3KEYVAL_5_BTN$0`, `$1`, ...
- Success shows "has been submitted"; return via the left-hand "Finalise pending forms".
