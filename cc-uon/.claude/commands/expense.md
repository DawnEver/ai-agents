---
name: expense
description: Fill a UoN Oracle expense claim from receipts the user provides, then submit.
disable-model-invocation: true
---

# Expense claim

Conventions (layout, authorization, browser pitfalls) live in `AGENTS.md`; values in
`profile.md`. This file is the sequence only.

1. **Collect** — create `ongoing/<YYYY-MM-DD>-<slug>/receipts/` and copy the receipts there.
   Read each PDF with `pdftotext -layout`; view images directly.
2. **Plan lines** — write `lines.md`, one row per line:
   `| # | Type | Date | Amount | Currency | Purpose | Description | Status |`.
   - Date and currency follow `profile.md` rules.
   - Purpose: travel code for transport/accommodation, conference code for registration.
   - Group receipts of the same Type into one item (e.g. outbound + return rail) and attach
     all of them to it — except **Meals** (one item per meal/receipt) and Airfare (one item
     per leg, forced by its one-way fields).
   - Oracle Type names: meals → `Meals`; visa → `Passport & Visa Fees`; list the full set with
     JS over the Type `<select>` when unsure.
   Show the table to the user and wait for corrections before touching the browser.
3. **Fill each line** in Oracle (re-screenshot before every click):
   1. Set Type, then **Date first** — changing the date re-renders the line and clears
      amount and description.
   2. Amount, currency, Purpose, Description (description via JS + input/change events).
   3. Item-level Purpose, Analysis, Taxable Expense from `profile.md`.
   4. Types with **Itemization** (e.g. Meals: Breakfast / Lunch / Dinner / Refreshments) need
      one row (a meal item has a single row); each row has its own Cost Centre (defaults 99999), Purpose,
      Analysis and Taxable — fill all from `profile.md`. Rows must sum to the item amount.
   5. Upload the item's receipts yourself: `find` the attachment `input[type=file]`, then
      `file_upload` with the paths under `receipts/`.
   - Business Entertainment has no itemization but extra required fields: Expense relate to,
     Purpose of expense, annual event? (No), held on UoN campus? (No), and an attendee table
     (the user is pre-listed as employee attendee; put the full amount there).
   - Airfare fields: Flight Type (International/Domestic), Flight Class (Coach), Ticket Number
     (booking ref), Departure/Arrival City, Agency (airline), Passenger Name (required).
   - Currency is sticky across Create Another. To change it, type the code into the Currency
     LOV, wait for the suggestion, and click it — Tab alone fails ("Autocompletion failed").
     Assert the currency before entering each amount.
   - Daily/policy-rate warnings are non-blocking but add a required Justification field.
   6. Selects ignore a JS `value` change: focus them via JS, then type the option text + Tab.
   7. **Create Another** for the next line — it resets Cost Centre to 99999; refill it.
   8. Mark the row `Saved` in `lines.md`.
4. **Submit** — after the last line, check the claim total against `lines.md`, record the claim
   number at the top of `lines.md`, then Submit.
5. **Archive** — move the folder to `archived/<YYYY>/<claim-no>/` and report claim number,
   line count, and total.
