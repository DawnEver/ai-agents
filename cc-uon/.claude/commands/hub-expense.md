---
name: hub-expense
description: Fill a PGR student exceptional expense claim on NottinghamHub (Campus Solutions eForm) from receipts and a budget-holder pre-approval.
disable-model-invocation: true
---

# PGR exceptional expense claim (NottinghamHub)

Conventions (layout, authorization, browser pitfalls) live in `AGENTS.md`; recorded codes in
`profile.md`. This file is the sequence only. Entry: NottinghamHub > Expenses tile
(`scname=G_NCOL_UN_EXPENSE`) > "Submit an expense or advance".

1. **Gate** — the claim needs, before any browser work:
   - a budget-holder pre-approval naming the project or purpose code, exported to PDF;
   - the cost centre and that code. `profile.md` only RECORDS codes from earlier claims: ask the
     user to confirm each one for this claim; never default to a recorded code.
   - the user's bank account and "direct deposit" set up in NottinghamHub.
2. **Collect** — `ongoing/<YYYY-MM-DD>-<slug>/receipts/`: copy receipts and the pre-approval PDF.
   Re-read every receipt; a handoff's amounts are claims to verify, not facts (Ryanair shows the
   fare in EUR and the card charge in GBP on separate lines — claim the "card holders currency"
   line). Do not attach a pro-forma invoice next to its paid receipt.
3. **Plan lines** — `lines.md`, one row per expense:
   `| # | Date | Reason | Currency | Amount | Rate | GBP | Receipt | Status |`.
   Date = order/payment date. Foreign currency: GBP actually charged if the statement shows it,
   otherwise the user chooses the payment-date rate (ECB via frankfurter.app; the form's OANDA
   link ignores a date). Show the table and wait for corrections.
4. **Header** — Type `Expense`; Reason; Term (academic year); Cost centre (5 digits); Purpose
   code (6) OR Project code (7, starts `P`) — never both.
5. **Other expenses** grid, one row per expense: Date (DD/MM/YYYY), Reason, Currency
   (`GBP` with rate `1` for sterling), Currency amount, Exchange rate. Add rows with the row's
   `+` (`G3CFG_LVL2GR_VW$new$<n-1>$$3`). Check "Total GBP to Reimburse" against `lines.md`.
6. **Comments** — if travel was booked outside Key Travel, explain in the user's own words:
   booked yourself because PGRs have no Key Travel account, not aware dispensation was needed,
   budget holder approved, will contact the school office / travel@nottingham.ac.uk next time.
   Without it the claim is Recycled (the Travel Team gives no retrospective dispensation).
   State any exchange-rate basis here too.
7. **Attachments** — row 1 is type Pre-approval; create one `Receipt` row per remaining file
   (`G3ATT_WRK_ADD_PB`, type select `G3UNIQUE_KEY$<n>`), then **Save**. The user uploads the
   files (see AGENTS.md) — give them the row-to-file table.
8. **Submit** — the user ticks the certification and submits. Verify read-only under
   "Submitted forms": status `Pending`, total, attachment count. Record the form ID in
   `lines.md`, move the folder to `archived/<YYYY>/<form-id>/`.

Approval: payment within 10 working days; queries to bb-fm-transactional@exmail.nottingham.ac.uk
quoting the form ID.
