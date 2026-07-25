"""PDF acquisition — browser login + download for approved candidates."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from literature_review.acquire import http_fetch, oa_resolve, researchgate

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
    args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-features=IsolateOrigins,site-per-process",
    ]
    if network_mode == "direct":
        args.append("--no-proxy-server")
    opts["args"] = args
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

def safe_filename(value: str, max_length: int = 120) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value or "paper")
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ._") or "paper"
    return cleaned[:max_length].rstrip(" .")


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


def candidate_urls(item: dict[str, Any], resolve: bool = True) -> list[str]:
    """Build the ordered list of URLs to try for one queue item.

    Screening often records only a publisher landing page (or worse, a search
    URL), which Cloudflare will reject. Resolving the DOI against the OA
    aggregators surfaces repository and preprint mirrors that download cleanly,
    so those are merged in and everything is ranked by source reliability.
    """
    urls: list[str] = []
    for key in ("pdf_url", "oa_url", "html_url", "url"):
        value = str(item.get(key) or "").strip()
        if value:
            urls.append(value)

    doi = str(item.get("doi") or "").strip()
    if doi:
        if resolve:
            urls.extend(oa_resolve.resolve_oa_urls(doi, title=str(item.get("title") or "") or None))
        normalized = doi.removeprefix("https://doi.org/").removeprefix("doi:")
        urls.append(f"https://doi.org/{normalized}")

    # ResearchGate as a systematic last resort: it carries author-uploaded
    # copies of papers no repository or aggregator knows about. Ranked last,
    # so it is only reached once every cheaper source has failed.
    query = researchgate.query_from_item(item)
    if query:
        urls.append(researchgate.search_url(query))

    return oa_resolve.rank_urls(urls)


def _append_log(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=LOG_FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerow({key: row.get(key, "") for key in LOG_FIELDS})


CLEARANCE_WAIT_MS = 6_000


def _request_pdf_bytes(page: Any, url: str, referer: str) -> bytes | None:
    """GET *url* through the browser context; return PDF bytes or None."""
    try:
        response = page.context.request.get(url, timeout=60_000, headers={"Referer": referer})
        if response.status != 200:
            return None
        body = response.body()
    except Exception:  # noqa: BLE001
        return None
    return body if body and body.lstrip().startswith(b"%PDF-") else None


def _fetch_linked_pdf(page: Any, target: Path, base_url: str) -> str | None:
    """Find PDF links in the loaded page and fetch them via the browser context."""
    try:
        html = page.content()
        base = page.url or base_url
    except Exception:  # noqa: BLE001
        return None

    for link in http_fetch.extract_pdf_links(html, base)[:http_fetch.MAX_LINKS_PER_PAGE]:
        body = _request_pdf_bytes(page, link, base)
        if body is None:
            # Cloudflare-guarded file endpoint: a context request alone gets a
            # 403 because it runs no JS. Navigating the page to the URL lets
            # Chrome solve the challenge, which banks a clearance cookie in the
            # context — the identical request then succeeds.
            try:
                page.goto(link, wait_until="domcontentloaded", timeout=60_000)
            except Exception:  # noqa: BLE001 - a download/abort here is fine
                pass
            page.wait_for_timeout(CLEARANCE_WAIT_MS)
            body = _request_pdf_bytes(page, link, base)
        if body is not None:
            target.write_bytes(body)
            return link
    return None


def _download_with_page(page: Any, url: str, target: Path) -> str:
    """Attempt to download a PDF via the Playwright page; return source URL."""
    # Fast path: direct PDF URL → use HTTP request, no navigation needed
    if url.lower().endswith(".pdf") or "/bitstream/" in url or "/portalfiles/" in url or "/content/pdf/" in url or "/stampPDF/" in url:
        try:
            resp = page.context.request.get(url, timeout=60_000)
            # A 401/403/429 here is not final: the same URL often succeeds once
            # loaded in the browser, which carries the session cookies.
            if resp.status not in {401, 403, 429}:
                body = resp.body()
                if body and body.lstrip().startswith(b"%PDF-"):
                    target.write_bytes(body)
                    return resp.url or url
        except Exception:
            pass  # Fall through to browser navigation

    downloads: list[Any] = []

    def on_download(download: Any) -> None:
        downloads.append(download)

    page.on("download", on_download)
    navigation_error: Exception | None = None
    response: Any = None
    body = ""
    try:
        try:
            response = page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            try:
                page.wait_for_load_state("networkidle", timeout=15_000)
            except Exception:
                pass
        except Exception as error:
            navigation_error = error
            # Direct PDF navigation triggers "Download is starting" — wait for it
            if "download" in str(error).lower():
                import time as _time
                for _ in range(10):  # Wait up to 5s for download event
                    if downloads:
                        break
                    _time.sleep(0.5)

        if downloads:
            downloads[0].save_as(target)
            return downloads[0].url or url

        # Auto-click PDF download buttons on publisher pages (before checking errors)
        if not downloads:
            pdf_selectors = [
                # IEEE-specific
                'a[href*="/stampPDF/"]',
                'xpl-download-pdf a',
                'a[xpl-download-pdf]',
                '.document-pdf-link a',
                'a:has-text("PDF")',
                'button:has-text("PDF")',
                'a:has-text("Download PDF")',
                'a:has-text("View PDF")',
                # Generic
                'a[href*="pdf"]',
                '.pdf-btn',
                '[data-artifact="pdf"]',
                'a[aria-label*="PDF"]',
                'a[title*="PDF"]',
                # Springer
                '.c-pdf-download__link',
                'a[href*="/content/pdf/"]',
            ]
            for sel in pdf_selectors:
                try:
                    btn = page.locator(sel).first
                    if btn and btn.is_visible():
                        btn.click(timeout=3_000)
                        import time as _time2
                        for _ in range(6):
                            if downloads:
                                break
                            _time2.sleep(0.5)
                        if downloads:
                            break
                except Exception:
                    continue

        if downloads:
            downloads[0].save_as(target)
            return downloads[0].url or url

        # Parse the loaded HTML for PDF links and request them through the
        # browser context, which carries the Cloudflare clearance cookie the
        # page just earned. More reliable than matching a visible button.
        linked = _fetch_linked_pdf(page, target, url)
        if linked:
            return linked

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
                    b"challenge-platform",
                    b"cf-challenge",
                    b"turnstile",
                    b"verify you are human",
                    b"unusual traffic detected",
                    b"please sign in to continue",
                    b"purchase this document",
                    b"you are not authorized",
                )):
                    matched = [t for t in (b"challenge-platform", b"cf-challenge", b"turnstile", b"verify you are human", b"unusual traffic detected", b"please sign in to continue", b"purchase this document", b"you are not authorized") if t in lower]
                    raise AccessBlockedError(f"iframe API blocked — matched: {matched}")

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

        # Dismiss cookie consent banners that block page interaction
        try:
            # Osano (IEEE) cookie consent
            osano_btn = page.locator('.osano-cm-button--type_accept, .osano-cm-button--type_accept-all').first
            if osano_btn:
                osano_btn.click(timeout=5_000)
                page.wait_for_timeout(1_000)
        except Exception:
            pass  # No cookie banner, continue

        # Check for Cloudflare challenge (specific markers, not generic words)
        for attempt in range(3):
            body = page.content().lower()
            cf_markers = ["challenge-platform", "cf-challenge", "turnstile", "verify you are human", "unusual traffic detected"]
            if any(m in body for m in cf_markers):
                if attempt < 2:
                    time.sleep(5)
                    try:
                        page.wait_for_load_state("networkidle", timeout=15_000)
                    except Exception:
                        pass
                    continue
                else:
                    # Keep debug dumps out of the PDF directory — anything left
                    # beside the PDFs gets mistaken for a downloaded paper.
                    debug_dir = target.parent / "_debug"
                    debug_dir.mkdir(parents=True, exist_ok=True)
                    try:
                        page.screenshot(path=str(debug_dir / f"_debug_{target.stem}.png"))
                    except Exception:
                        pass
                    (debug_dir / f"_debug_{target.stem}.html").write_text(page.content(), encoding="utf-8")
                    raise AccessBlockedError(f"Cloudflare challenge did not resolve after retries (debug saved for {target.stem})")
            break

        access_blocks = [
            "access to ieee explore requires",
            "you are not authorized",
            "please sign in to continue",
            "purchase this document",
            "challenge-platform",
            "cf-challenge",
            "turnstile",
            "verify you are human",
            "unusual traffic detected",
        ]
        if any(t in body for t in access_blocks):
            matched = [t for t in access_blocks if t in body]
            raise AccessBlockedError(f"page body blocked — matched: {matched}")

        raise ValueError("response did not produce a PDF download")
    finally:
        page.remove_listener("download", on_download)


# Hosts that answer plain HTTP with a challenge page — only a real browser
# session (with its cookies) gets through, so skip the HTTP attempt entirely.
_BROWSER_ONLY_HOSTS = (
    "ieeexplore.ieee.org", "researchgate.net", "sciencedirect.com",
    "onlinelibrary.wiley.com", "academia.edu", "dl.acm.org",
)


def _needs_browser(url: str) -> bool:
    from urllib.parse import urlparse
    host = (urlparse(url.lower()).hostname or "")
    return any(blocked in host for blocked in _BROWSER_ONLY_HOSTS)


_PROFILE_LOCK_MARKERS = (
    "existing browser", "profile appears to be in use",
    "singletonlock", "failed to create a profilesyncdatatypecontroller",
)


def _is_profile_lock_error(error: Exception) -> bool:
    message = str(error).lower()
    return any(marker in message for marker in _PROFILE_LOCK_MARKERS)


def _kill_stale_chrome() -> bool:
    """Force-close Chrome so a locked profile can be reopened. Returns success."""
    import platform
    import subprocess

    command = (
        ["taskkill", "/F", "/IM", "chrome.exe"]
        if platform.system() == "Windows"
        else ["pkill", "-f", "chrome"]
    )
    try:
        subprocess.run(command, capture_output=True, timeout=10, check=False)
    except (OSError, subprocess.SubprocessError):
        return False
    time.sleep(2)
    return True


def _playwright_downloader(
    profile: Path | None = None,
    browser_channel: str = DEFAULT_BROWSER_CHANNEL,
    network_mode: str = DEFAULT_NETWORK_MODE,
) -> tuple[Callable[[dict[str, Any], Path, str], str], Callable[[], None]]:
    """Create a download function. Uses persistent profile if given, else a plain headed browser (campus IP)."""
    playwright = _start_playwright()
    _browser = None
    if profile is not None:
        _validate_dedicated_profile(profile)
        if not (profile / PROFILE_MARKER).exists():
            raise ValueError("run browser-login first to create the dedicated profile")
        try:
            context = playwright.chromium.launch_persistent_context(
                str(profile.resolve()),
                **_launch_options(browser_channel, network_mode=network_mode),
            )
        except Exception as error:
            # A stale process still holds the profile lock. Only then is killing
            # Chrome justified — doing it unconditionally would close the
            # browser windows the user is actually working in.
            if not _is_profile_lock_error(error) or not _kill_stale_chrome():
                playwright.stop()
                raise
            try:
                context = playwright.chromium.launch_persistent_context(
                    str(profile.resolve()),
                    **_launch_options(browser_channel, network_mode=network_mode),
                )
            except Exception:
                playwright.stop()
                raise
    else:
        _browser = playwright.chromium.launch(
            headless=False, channel=browser_channel if browser_channel != "chromium" else None,
        )
        context = _browser.new_context()

    page = context.pages[0] if context.pages else context.new_page()
    # Hide automation signals from Cloudflare
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
    """)

    def download(item: dict[str, Any], target: Path, url: str) -> str:
        if not url:
            raise ValueError("queue item has no PDF or HTML URL")
        # ResearchGate needs search → publication → download, not a URL fetch.
        if researchgate.is_researchgate_url(url):
            query = researchgate.query_from_item(item) or researchgate.query_from_item({"html_url": url})
            source = researchgate.fetch(page, query, target)
            if source:
                return source
            raise ValueError("ResearchGate has no downloadable full text")
        # Repositories and preprint servers need no browser at all; try the
        # cheap, selector-free HTTP path before spending a page navigation.
        if not _needs_browser(url):
            source = http_fetch.fetch_pdf(url, target)
            if source:
                return source
        return _download_with_page(page, url, target)

    def close() -> None:
        try:
            context.close()
            if _browser is not None:
                _browser.close()
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

            # Intercept PDF responses — some publishers (PMC, IEEE) render
            # PDFs via Chrome extension instead of triggering downloads.
            pdf_body: list[bytes] = []

            def on_response(resp):
                ct = (resp.headers.get("content-type", "") or "").lower()
                if resp.status == 200 and "application/pdf" in ct:
                    try:
                        pdf_body.append(resp.body())
                    except Exception:
                        pass

            page.on("response", on_response)

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(3000)
                print(f"    Page: {page.title()[:80]}")

                # Find PDF link on the page
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

                # Dismiss cookie/privacy banners that block clicks (Springer, Elsevier)
                for banner_sel in [
                    "button:has-text('Accept')", "button:has-text('Accept all')",
                    "button:has-text('I accept')", "button:has-text('OK')",
                    ".cc-banner button:has-text('Accept')",
                ]:
                    try:
                        btn = page.query_selector(banner_sel)
                        if btn and btn.is_visible():
                            btn.click()
                            page.wait_for_timeout(500)
                            break
                    except Exception:
                        continue
                try:
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(300)
                except Exception:
                    pass

                # Try clicking PDF link first (some sites trigger download via JS)
                if pdf_href:
                    for sel in [
                        "a:has-text('PDF')", "a:has-text('Download')",
                        "a[href*='.pdf']", "a:has-text('View PDF')",
                    ]:
                        try:
                            el = page.query_selector(sel)
                            if el and el.is_visible():
                                el.click(force=True)  # bypass banner interception
                                page.wait_for_timeout(3000)
                                break
                        except Exception:
                            continue

                if pdf_href:
                    from urllib.parse import urljoin
                    full_url = urljoin(page.url, pdf_href)
                    print(f"    Goto: {full_url[:120]}")
                    # Navigate to PDF — browser JS renders it, we intercept via on_response
                    page.goto(full_url, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(3000)

                # Check interceptor for valid PDF body
                for body in pdf_body:
                    if body[:4] == b'%PDF':
                        path = str(pdf_dir / f"{label}.pdf")
                        with open(path, 'wb') as f:
                            f.write(body)
                        download_occurred.append(path)
                        print(f"    Intercepted {len(body)/1024:.0f} KB")
                        break
                else:
                    # Fallback: direct API request
                    if pdf_href and not download_occurred:
                        full_url = urljoin(page.url, pdf_href)
                        api_resp = page.context.request.get(full_url, timeout=60000)
                        body = api_resp.body()
                        if body[:4] == b'%PDF':
                            path = str(pdf_dir / f"{label}.pdf")
                            with open(path, 'wb') as f:
                                f.write(body)
                            download_occurred.append(path)
                            print(f"    Direct {len(body)/1024:.0f} KB")

            except Exception as e:
                print(f"    Error: {e}")
            finally:
                page.close()

            if download_occurred:
                size_kb = Path(download_occurred[0]).stat().st_size / 1024
                results.append({"label": label, "url": url, "status": "ok", "path": download_occurred[0]})
                print(f"    -> {size_kb:.0f} KB")
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
    downloader: Callable[[dict[str, Any], Path, str], str] | None = None,
    resolve_oa: bool = True,
) -> list[dict[str, Any]]:
    """Download approved PDFs from the queue using an authenticated browser.

    Each item is tried against every known source in reliability order
    (repository → preprint → aggregator → publisher) and only gives up once all
    of them fail; the per-URL failures are kept so the log says *why*.
    """
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
        downloader, close = _playwright_downloader(
            profile=profile,
            browser_channel=browser_channel,
            network_mode=network_mode,
        )

    results: list[dict[str, Any]] = []
    try:
        for item in items:
            cid = safe_filename(str(item.get("candidate_id") or "paper"), 40)
            title = safe_filename(str(item.get("title") or "paper"), 80)
            target = pdf_dir / f"{cid}_{title}.pdf"
            timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
            urls = candidate_urls(item, resolve=resolve_oa)

            if not urls:
                _append_log(log_path, {
                    "candidate_id": item.get("candidate_id", ""),
                    "status": "failed", "timestamp": timestamp,
                    "error": "no candidate URL — item has no pdf_url, html_url, or doi",
                })
                continue

            row = None
            attempts: list[str] = []
            blocked = False
            for url in urls:
                try:
                    source_url = downloader(item, target, url)
                    validate_pdf(target)
                except researchgate.AccessDeniedError as error:
                    # IP-level ban: every remaining ResearchGate URL in this run
                    # would fail the same way, so record it and move on.
                    blocked = True
                    attempts.append(f"{url} -> {error}")
                except AccessBlockedError as error:
                    blocked = True
                    attempts.append(f"{url} -> blocked: {error}")
                except Exception as error:  # noqa: BLE001 - try the next source
                    attempts.append(f"{url} -> {error}")
                else:
                    row = {
                        "candidate_id": item.get("candidate_id", ""),
                        "status": "downloaded",
                        "pdf_path": str(target.resolve()),
                        "sha256": sha256_file(target),
                        "source_url": source_url or url,
                        "timestamp": timestamp,
                        "error": "",
                    }
                    break
                target.unlink(missing_ok=True)

            if row is not None:
                results.append(row)
                _append_log(log_path, row)
            else:
                _append_log(log_path, {
                    "candidate_id": item.get("candidate_id", ""),
                    # "stopped" signals a human-solvable block; "failed" is technical.
                    "status": "stopped" if blocked else "failed",
                    "timestamp": timestamp,
                    "error": f"all {len(urls)} source(s) failed: " + " | ".join(attempts),
                })
    finally:
        close()
    return results
