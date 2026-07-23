"""Open a provider site in an isolated persistent browser profile for login."""

from __future__ import annotations

from pathlib import Path

PROFILE_MARKER = ".literature-review-profile"
SUPPORTED_BROWSER_CHANNELS = {"chromium", "chrome"}
SUPPORTED_NETWORK_MODES = {"direct", "system"}
COMPLETION_MODES = {"browser-close", "stdin", "none"}

DEFAULT_BROWSER_CHANNEL = "chromium"
DEFAULT_NETWORK_MODE = "direct"
DEFAULT_URL = "https://ieeexplore.ieee.org/"


def _start_playwright():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as error:
        raise RuntimeError(
            "Playwright is required; install it and its Chromium browser"
        ) from error
    return sync_playwright().start()


def _wait_for_completion(context, completion: str) -> None:
    if completion == "none":
        return
    if completion == "stdin":
        try:
            input("Complete login/CAPTCHA in the browser, then press Enter here to close: ")
        except EOFError as error:
            raise RuntimeError(
                "stdin is unavailable; use --completion browser-close and close the "
                "browser when login is complete"
            ) from error
        return
    # browser-close
    pages = context.pages
    if pages:
        pages[0].wait_for_event("close", timeout=0)


def _validate_dedicated_profile(profile: Path) -> None:
    resolved = profile.expanduser().resolve()
    if resolved == Path.home().resolve() or resolved == (Path.home() / ".config").resolve():
        raise ValueError("profile must be a dedicated automation profile")
    if resolved.exists() and any(resolved.iterdir()) and not (resolved / PROFILE_MARKER).exists():
        raise ValueError(
            "existing profile is not marked as a dedicated literature-review profile"
        )


def _launch_options(
    browser_channel: str,
    network_mode: str = DEFAULT_NETWORK_MODE,
) -> dict[str, object]:
    channel = browser_channel.strip().lower()
    if channel not in SUPPORTED_BROWSER_CHANNELS:
        raise ValueError(
            f"browser_channel must be one of: {', '.join(sorted(SUPPORTED_BROWSER_CHANNELS))}"
        )
    mode = network_mode.strip().lower()
    if mode not in SUPPORTED_NETWORK_MODES:
        raise ValueError(
            f"network_mode must be one of: {', '.join(sorted(SUPPORTED_NETWORK_MODES))}"
        )
    options: dict[str, object] = {"headless": False}
    if channel != "chromium":
        options["channel"] = channel
    if mode == "direct":
        options["args"] = ["--no-proxy-server"]
    return options


def open_login(
    profile: Path,
    url: str = DEFAULT_URL,
    browser_channel: str = DEFAULT_BROWSER_CHANNEL,
    completion: str = "browser-close",
    network_mode: str = DEFAULT_NETWORK_MODE,
) -> int:
    """Launch a persistent browser profile for manual login.

    The profile is marked with a sentinel file so subsequent operations can
    verify it is a dedicated automation profile.
    """
    if completion not in COMPLETION_MODES:
        raise ValueError(
            f"completion must be one of: {', '.join(sorted(COMPLETION_MODES))}"
        )

    profile = profile.expanduser().resolve()
    _validate_dedicated_profile(profile)
    profile.mkdir(parents=True, exist_ok=True)
    (profile / PROFILE_MARKER).touch(exist_ok=True)

    playwright = _start_playwright()
    context = None
    try:
        context = playwright.chromium.launch_persistent_context(
            str(profile),
            **_launch_options(browser_channel, network_mode=network_mode),
        )
        if context.pages:
            context.pages[0].goto(url)
        else:
            context.new_page().goto(url)
        _wait_for_completion(context, completion)
    finally:
        try:
            if context is not None:
                context.close()
        finally:
            playwright.stop()
    return 0
