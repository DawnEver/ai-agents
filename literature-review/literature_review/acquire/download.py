"""PDF acquisition — browser login + download for approved candidates."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Playwright setup (inlined from deleted browser/login.py)
# ---------------------------------------------------------------------------

DEFAULT_BROWSER_CHANNEL = "chromium"
DEFAULT_NETWORK_MODE = "direct"
SUPPORTED_BROWSER_CHANNELS = {"chromium", "chrome"}
SUPPORTED_NETWORK_MODES = {"direct", "system"}
COMPLETION_MODES = {"browser-close", "stdin", "none"}
PROFILE_MARKER = ".lit-review-profile"
IEEE_HOME = "https://ieeexplore.ieee.org/"


def _start_playwright():
    from playwright.sync_api import sync_playwright
    return sync_playwright().start()


def _launch_options(channel: str = "chromium", network_mode: str = "direct"):
    opts: dict[str, Any] = {"headless": False}
    if channel == "chrome":
        opts["channel"] = "chrome"
    if network_mode == "direct":
        opts["args"] = ["--no-proxy-server"]
    return opts


def _validate_dedicated_profile(profile: Path) -> None:
    marker = profile / PROFILE_MARKER
    if not marker.is_file() and any(profile.iterdir()):
        raise ValueError(f"profile exists but is not a recognized browser profile: {profile}")


def open_login(profile: Path, url: str = IEEE_HOME, browser_channel: str = "chromium",
               completion: str = "browser-close", network_mode: str = "direct") -> int:
    profile.mkdir(parents=True, exist_ok=True)
    _validate_dedicated_profile(profile)
    (profile / PROFILE_MARKER).touch()
    pw = _start_playwright()
    try:
        browser = pw.chromium.launch_persistent_context(
            user_data_dir=str(profile), **_launch_options(browser_channel, network_mode),
        )
        page = browser.new_page()
        page.goto(url)
        if completion == "stdin":
            input("Press Enter after login...")
        elif completion == "browser-close":
            print("Close the browser window when done.")
            page.wait_for_event("close", timeout=0)
        browser.close()
    finally:
        pw.stop()
    print(f"logged-in: {profile}")
    return 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")[:120]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_pdf(path: Path) -> None:
    if not path.is_file():
        raise ValueError(f"PDF does not exist: {path}")
    with path.open("rb") as f:
        if f.read(5) != b"%PDF-":
            raise ValueError(f"invalid PDF signature: {path}")

DEFAULT_LIMIT = 10
HARD_LIMIT = 20
LOG_FIELDS = [
    "candidate_id", "status", "pdf_path", "sha256",
    "source_url", "timestamp", "error",
]


class AccessBlockedError(RuntimeError):
    """Raised when authentication, CAPTCHA, throttling, or access denial is observed."""


def _verified_download_ids(log_path: Path) -> set[str]:
    """Return IDs whose logged downloads still validate on disk."""
    if not log_path.exists():
        return set()
    verified: set[str] = set()
    with log_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            cid = str(row.get("candidate_id") or "")
            pdf_path = str(row.get("pdf_path") or "")
            expected_hash = str(row.get("sha256") or "").lower()
            if row.get("status") != "downloaded" or not cid or not pdf_path or not expected_hash:
                continue
            try:
                validate_pdf(Path(pdf_path))
                if sha256_file(Path(pdf_path)).lower() == expected_hash:
                    verified.add(cid)
            except (OSError, ValueError):
                continue
    return verified


def _select_approved(
    items: list[dict[str, Any]],
    limit: int = DEFAULT_LIMIT,
    completed_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    if limit < 1:
        raise ValueError("limit must be positive")
    if limit > HARD_LIMIT:
        raise ValueError(f"limit exceeds hard limit of {HARD_LIMIT}")
    completed_ids = completed_ids or set()
    return [
        item for item in items
        if item.get("approved") is True
        and str(item.get("candidate_id") or "") not in completed_ids
    ][:limit]


def _append_log(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=LOG_FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerow({key: row.get(key, "") for key in LOG_FIELDS})


def _download_with_page(page: Any, url: str, target: Path) -> str:
    """Attempt to download a PDF via the Playwright page; return source URL."""
    downloads: list[Any] = []

    def on_download(download: Any) -> None:
        downloads.append(download)

    page.on("download", on_download)
    navigation_error: Exception | None = None
    try:
        try:
            response = page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        except Exception as error:
            navigation_error = error

        if downloads:
            downloads[0].save_as(target)
            return downloads[0].url or url

        if navigation_error is not None:
            raise navigation_error

        if response and response.status in {401, 403, 418, 429}:
            raise AccessBlockedError(f"access stopped with HTTP {response.status}")

        # Direct PDF response
        content_type = (response.headers.get("content-type", "") if response else "").lower()
        raw = response.body() if response and "application/pdf" in content_type else b""
        if raw.lstrip().startswith(b"%PDF-"):
            target.write_bytes(raw)
            return response.url or url

        # Try IEEE-style iframe-based PDF delivery
        iframe_src = None
        try:
            iframe_src = page.locator(
                'iframe[src*="stampPDF/getPDF.jsp"]'
            ).first.get_attribute("src", timeout=10_000)
        except Exception:
            pass

        if iframe_src:
            from urllib.parse import urljoin
            pdf_url = urljoin(response.url if response else url, iframe_src)
            api_response = None
            try:
                api_response = page.context.request.get(pdf_url, timeout=60_000)
            except AttributeError:
                pass
            if api_response is not None:
                if api_response.status in {401, 403, 418, 429}:
                    raise AccessBlockedError(f"access stopped with HTTP {api_response.status}")
                raw = api_response.body()
                if raw.lstrip().startswith(b"%PDF-"):
                    target.write_bytes(raw)
                    return api_response.url or pdf_url
                lower = raw[:4096].lower()
                if any(t in lower for t in (
                    b"captcha", b"access denied", b"sign in",
                    b"verify you are human", b"unusual traffic detected",
                )):
                    raise AccessBlockedError("login, CAPTCHA, or access restriction detected")

            # Navigate to the iframe PDF URL as fallback
            navigation_error = None
            try:
                response = page.goto(pdf_url, wait_until="domcontentloaded", timeout=60_000)
            except Exception as error:
                navigation_error = error
            if downloads:
                downloads[0].save_as(target)
                return downloads[0].url or pdf_url
            if navigation_error is not None:
                raise navigation_error
            if response and response.status in {401, 403, 418, 429}:
                raise AccessBlockedError(f"access stopped with HTTP {response.status}")
            content_type = (response.headers.get("content-type", "") if response else "").lower()
            raw = response.body() if response and "application/pdf" in content_type else b""
            if raw.lstrip().startswith(b"%PDF-"):
                target.write_bytes(raw)
                return response.url or pdf_url

        # Check for access-block signals in page body
        body = page.content().lower()
        if any(t in body for t in (
            "captcha", "access denied", "sign in",
            "verify you are human", "unusual traffic detected",
        )):
            raise AccessBlockedError("login, CAPTCHA, or access restriction detected")

        raise ValueError("response did not produce a PDF download")
    finally:
        page.remove_listener("download", on_download)


def _playwright_downloader(
    profile: Path,
    browser_channel: str = DEFAULT_BROWSER_CHANNEL,
    network_mode: str = DEFAULT_NETWORK_MODE,
) -> tuple[Callable[[dict[str, Any], Path], str], Callable[[], None]]:
    """Create a download function backed by a persistent browser context."""
    _validate_dedicated_profile(profile)
    if not (profile / PROFILE_MARKER).exists():
        raise ValueError("run browser-login first to create the dedicated profile")

    playwright = _start_playwright()
    try:
        context = playwright.chromium.launch_persistent_context(
            str(profile.resolve()),
            **_launch_options(browser_channel, network_mode=network_mode),
        )
    except Exception:
        playwright.stop()
        raise

    page = context.pages[0] if context.pages else context.new_page()

    def download(item: dict[str, Any], target: Path) -> str:
        url = str(item.get("pdf_url") or item.get("html_url") or "")
        if not url:
            raise ValueError("queue item has no PDF or HTML URL")
        return _download_with_page(page, url, target)

    def close() -> None:
        try:
            context.close()
        finally:
            playwright.stop()

    return download, close


def acquire_headed(
    papers: list[dict[str, str]],
    pdf_dir: Path,
    *,
    browser_channel: str = "chrome",
    timeout_per_paper: int = 60,
) -> list[dict[str, Any]]:
    """Download PDFs via headed (visible) real Chrome with auto-click.

    Opens the user's REAL Chrome with existing sessions/cookies — no CAPTCHA.
    For each paper: navigates to URL, auto-clicks PDF download button,
    saves to *pdf_dir*.

    Args:
        papers: List of {"label": "name", "url": "https://..."} dicts
        pdf_dir: Where to save PDFs
        browser_channel: "chrome" (real Chrome) or "chromium" (Playwright)
        timeout_per_paper: Seconds to wait for download click per paper

    Returns:
        List of {"label": ..., "url": ..., "status": "ok|failed", "path": ...}
    """
    import time as _time
    from playwright.sync_api import sync_playwright

    pdf_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir="",
            headless=False,
            channel=browser_channel,
            accept_downloads=True,
            args=["--no-first-run", "--no-default-browser-check"],
        )

        for paper in papers:
            label = str(paper.get("label", "paper"))
            url = str(paper.get("url", ""))
            print(f"\n  {label}")
            print(f"    {url[:120]}")

            page = ctx.new_page()
            download_occurred: list[str] = []

            def on_download(download):
                path = str(pdf_dir / f"{label}.pdf")
                download.save_as(path)
                download_occurred.append(path)

            page.on("download", on_download)

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(3000)
                print(f"    Page: {page.title()[:80]}")

                # Find PDF link href on the page
                pdf_href = None
                for sel in [
                    "a:has-text('PDF')",
                    "a:has-text('View PDF')",
                    "a[href*='.pdf']",
                    ".pdf-link",
                    "a.int-view:has-text('PDF')",
                    "a[href*='stampPDF']",
                    "a[href*='/pdf/']",
                ]:
                    try:
                        el = page.query_selector(sel)
                        if el and el.is_visible():
                            pdf_href = el.get_attribute("href") or ""
                            print(f"    Link: {sel} -> {pdf_href[:120]}")
                            break
                    except Exception:
                        continue

                # Fetch PDF binary via browser's authenticated session
                if pdf_href:
                    from urllib.parse import urljoin
                    full_url = urljoin(page.url, pdf_href)
                    print(f"    GET {full_url[:120]}")
                    api_resp = page.context.request.get(full_url, timeout=60000)
                    body = api_resp.body()
                    if api_resp.status == 200 and body[:4] == b'%PDF':
                        path = str(pdf_dir / f"{label}.pdf")
                        with open(path, 'wb') as f:
                            f.write(body)
                        download_occurred.append(path)
                        print(f"    OK {len(body)/1024:.0f} KB")
                    else:
                        print(f"    HTTP {api_resp.status}, PDF={body[:4]==b'%PDF'}")
                else:
                    print(f"    No PDF link found on page")

            except Exception as e:
                print(f"    Error: {e}")
            finally:
                page.close()

            if download_occurred:
                size_kb = Path(download_occurred[0]).stat().st_size / 1024
                print(f"    -> {size_kb:.0f} KB")
                results.append({"label": label, "url": url, "status": "ok", "path": download_occurred[0]})
            else:
                results.append({"label": label, "url": url, "status": "failed", "path": ""})

        ctx.close()

    return results


def acquire_pdfs(
    queue_path: Path,
    run_dir: Path,
    limit: int = DEFAULT_LIMIT,
    profile: Path | None = None,
    browser_channel: str = DEFAULT_BROWSER_CHANNEL,
    network_mode: str = DEFAULT_NETWORK_MODE,
    downloader: Callable[[dict[str, Any], Path], str] | None = None,
) -> list[dict[str, Any]]:
    """Download approved PDFs from the queue using an authenticated browser."""
    artifact = json.loads(queue_path.read_text(encoding="utf-8"))
    pdf_dir = run_dir / "pdfs"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "download" / "download_log.csv"

    items = _select_approved(
        artifact.get("items", []),
        limit,
        completed_ids=_verified_download_ids(log_path),
    )

    close = lambda: None  # noqa: E731
    if downloader is None:
        if profile is None:
            raise ValueError("a dedicated --profile is required")
        downloader, close = _playwright_downloader(
            profile, browser_channel=browser_channel, network_mode=network_mode,
        )

    results: list[dict[str, Any]] = []
    try:
        for item in items:
            cid = safe_filename(str(item.get("candidate_id") or "paper"), 40)
            title = safe_filename(str(item.get("title") or "paper"), 80)
            target = pdf_dir / f"{cid}_{title}.pdf"
            timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
            try:
                source_url = downloader(item, target)
                validate_pdf(target)
                row = {
                    "candidate_id": item.get("candidate_id", ""),
                    "status": "downloaded",
                    "pdf_path": str(target.resolve()),
                    "sha256": sha256_file(target),
                    "source_url": source_url,
                    "timestamp": timestamp,
                    "error": "",
                }
                results.append(row)
                _append_log(log_path, row)
            except AccessBlockedError:
                target.unlink(missing_ok=True)
                _append_log(log_path, {
                    "candidate_id": item.get("candidate_id", ""),
                    "status": "stopped", "timestamp": timestamp,
                    "error": "access blocked — login, CAPTCHA, or throttling",
                })
                raise
            except Exception as error:
                target.unlink(missing_ok=True)
                _append_log(log_path, {
                    "candidate_id": item.get("candidate_id", ""),
                    "status": "failed", "timestamp": timestamp,
                    "error": str(error),
                })
    finally:
        close()
    return results
