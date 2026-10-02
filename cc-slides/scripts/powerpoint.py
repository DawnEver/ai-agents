"""Drive Microsoft PowerPoint to export a deck as PDF (the renderer of record).

macOS: AppleScript. PowerPoint is sandboxed — it cannot read /tmp or most paths without a user
prompt, and scripted `open` fails with -9074 — so the deck is staged inside PowerPoint's own
container, opened with `open -a`, saved as PDF via an HFS path, copied back, and the staging
directory removed. AppleScript "save as PNG" silently writes nothing, hence PDF + Ghostscript.
Windows: COM (pywin32). Elsewhere: LibreOffice `soffice` as a best-effort fallback.
"""
import os
import platform
import shutil
import subprocess
import time
import uuid
from pathlib import Path

MAC_STAGING = Path.home() / "Library/Containers/com.microsoft.Powerpoint/Data/tmp/cc-slides"
OPEN_TIMEOUT = 90
SAVE_TIMEOUT = 180


class PowerPointError(RuntimeError):
    pass


def _osa(script, timeout=SAVE_TIMEOUT):
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=timeout)
    if r.returncode:
        raise PowerPointError(r.stderr.strip() or "osascript failed")
    return r.stdout.strip()


def _as_str(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _wait_for(predicate, timeout, what):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return
        time.sleep(0.5)
    raise PowerPointError(f"timed out waiting for {what}")


def _stable_file(path):
    if not path.exists() or path.stat().st_size == 0:
        return False
    size = path.stat().st_size
    time.sleep(0.5)
    return path.stat().st_size == size


def _export_pdf_mac(deck, pdf):
    token = uuid.uuid4().hex[:8]
    staged = None
    stage = MAC_STAGING / token
    stage.mkdir(parents=True, exist_ok=True)
    try:
        # unique file name: PowerPoint identifies open presentations by name only
        staged = stage / f"{deck.stem}-{token}{deck.suffix}"
        staged_pdf = stage / (deck.stem + ".pdf")
        shutil.copy2(deck, staged)
        subprocess.run(["open", "-g", "-a", "Microsoft PowerPoint", str(staged)], check=True)
        name = _as_str(staged.name)
        _wait_for(lambda: staged.name in _osa(
            'tell application "Microsoft PowerPoint" to get name of presentations', 30),
            OPEN_TIMEOUT, f"PowerPoint to open {staged.name}")
        _osa(f'''tell application "Microsoft PowerPoint"
    set p to missing value
    repeat with i from 1 to count of presentations
        if name of presentation i is {name} then set p to presentation i
    end repeat
    if p is missing value then error "presentation not open: " & {name}
    save p in ((POSIX file {_as_str(staged_pdf)}) as text) as save as PDF
    close p saving no
end tell''')
        _wait_for(lambda: _stable_file(staged_pdf), SAVE_TIMEOUT, "the PDF to be written")
        shutil.copy2(staged_pdf, pdf)
    finally:
        if staged is not None:  # never leave PowerPoint holding a file we are about to delete
            try:
                _osa(f'''tell application "Microsoft PowerPoint"
    repeat with i from (count of presentations) to 1 by -1
        if name of presentation i is {_as_str(staged.name)} then close presentation i saving no
    end repeat
end tell''', 30)
            except (PowerPointError, subprocess.SubprocessError):
                pass
        shutil.rmtree(stage, ignore_errors=True)


def _export_pdf_windows(deck, pdf):
    try:
        import win32com.client  # type: ignore
    except ImportError as e:  # pragma: no cover
        raise PowerPointError("pywin32 is required on Windows: pip install pywin32") from e
    app = win32com.client.Dispatch("PowerPoint.Application")
    pres = app.Presentations.Open(str(deck), ReadOnly=True, Untitled=False, WithWindow=False)
    try:
        pres.SaveAs(str(pdf), 32)  # ppSaveAsPDF
    finally:
        pres.Close()


def _export_pdf_soffice(deck, pdf):
    exe = shutil.which("soffice") or shutil.which("libreoffice")
    if not exe:
        raise PowerPointError("no renderer: install Microsoft PowerPoint (macOS/Windows) or LibreOffice")
    subprocess.run([exe, "--headless", "--convert-to", "pdf", "--outdir", str(pdf.parent), str(deck)],
                   check=True, capture_output=True, timeout=SAVE_TIMEOUT)
    produced = pdf.parent / (deck.stem + ".pdf")
    if produced != pdf:
        os.replace(produced, pdf)


def export_pdf(deck, pdf=None):
    """Export `deck` to `pdf` (default: beside the deck). Returns the PDF path."""
    deck = Path(deck).resolve()
    pdf = Path(pdf).resolve() if pdf else deck.with_suffix(".pdf")
    pdf.parent.mkdir(parents=True, exist_ok=True)
    system = platform.system()
    if system == "Darwin" and Path("/Applications/Microsoft PowerPoint.app").exists():
        _export_pdf_mac(deck, pdf)
    elif system == "Windows":
        _export_pdf_windows(deck, pdf)
    else:
        _export_pdf_soffice(deck, pdf)
    if not pdf.exists():
        raise PowerPointError(f"export produced no file: {pdf}")
    return pdf
