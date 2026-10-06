---
name: long-harvests-must-be-detached-from-the-session
description: A background shell reaped under memory pressure leaves its process running — the symptom reads as "it died", and relaunching then runs two writers over the same files
metadata:
  type: engineering
---

# Long harvests must be detached from the session's process tree

`created: 2026-10-06, accessed: 2026-10-06`

Confirms and extends `2026-10-05/bibliometric-sources-and-data-permissions`, which
already recorded that background shells are reaped under memory pressure and that
two crawlers sharing a cache file overwrite each other. This adds the symptom
that makes the mistake easy to make, and the remedy.

## The failure shape

A multi-hour crawl launched with a background shell appeared to die: its log
held the header line and nothing more. `tasklist` filtered on `python.exe`
reported no such process. Both readings were wrong — the shell was reaped, the
process was **not**, and the interpreter is `python3.13.exe`, so the filter could
never have matched it.

Acting on that reading launched a second run. Two writers then shared
`api_done.txt` and the profile cache for about twenty minutes. Nothing was
corrupted, because two properties happened to hold, and both are worth keeping
on purpose:

- each result line is self-contained, and the reader takes the last line per key;
- the cache is keyed by the thing fetched, so a clobber costs a re-fetch, never a
  wrong value.

What it did cost was a **notification that lied**: the completion watcher counted
*lines*, and duplicated lines crossed the threshold early, so it reported the run
finished while it was 40% done.

## Before concluding a background job died

- Match the real interpreter name (`python3.13.exe`, not `python.exe`) — or list
  every `python*` and read the command lines. `Get-CimInstance Win32_Process`
  gives the full command line; `tasklist` gives only a truncated image name.
- Sample the output file twice, a minute apart. A log that stopped growing while
  the process is alive means a stall or a reaped shell, not a dead process.
- Never count raw lines in a file two writers append to. Count distinct keys.

## The remedy

`Start-Process` (via the PowerShell tool) detaches the job from the session's
process tree, which is what `run_in_background` does not do here:

```powershell
Start-Process -FilePath "python" -ArgumentList 'script.py','--flag' `
  -WindowStyle Hidden -RedirectStandardOutput "out.log" -RedirectStandardError "err.log"
```

Bash's `nohup ... &` inside the session is still the same tree and does not help.

## Make the job survivable regardless

Detaching is not a substitute for resumability, because the same memory pressure
kills detached processes too. A crawl should skip work already recorded (a
done-list of keys), cache each fetched unit under its own key, and append results
one self-contained line at a time. Then a restart costs only the work in flight,
and an interrupted run is indistinguishable from a slow one.

Progress must also be reported from a value that cannot be double-counted — the
job's own counter, not the length of a shared file.
