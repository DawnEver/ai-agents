"""Literature source provider adapters.

Provider classes are imported lazily (PEP 562) so that importing this package
does not pull in every provider's HTTP/browser dependencies.
"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Callable

from literature_review.providers.base import BaseProvider, ProbeResult, ProviderError, SearchResult

if TYPE_CHECKING:
    from literature_review.providers.arxiv import ArxivProvider
    from literature_review.providers.dblp import DblpProvider
    from literature_review.providers.ieee import IeeeXploreProvider
    from literature_review.providers.semantic_scholar import SemanticScholarProvider

_CLASS_MODULES = {
    "IeeeXploreProvider": "literature_review.providers.ieee",
    "SemanticScholarProvider": "literature_review.providers.semantic_scholar",
    "ArxivProvider": "literature_review.providers.arxiv",
    "DblpProvider": "literature_review.providers.dblp",
}


def _lazy(class_name: str) -> Callable[[], BaseProvider]:
    def factory() -> BaseProvider:
        module = import_module(_CLASS_MODULES[class_name])
        return getattr(module, class_name)()
    return factory


# Single source of truth: alias -> factory. Tests may monkeypatch entries.
PROVIDER_FACTORIES: dict[str, Callable[[], BaseProvider]] = {
    "ieee": _lazy("IeeeXploreProvider"),
    "ieee_xplore": _lazy("IeeeXploreProvider"),
    "s2": _lazy("SemanticScholarProvider"),
    "semantic_scholar": _lazy("SemanticScholarProvider"),
    "arxiv": _lazy("ArxivProvider"),
    "dblp": _lazy("DblpProvider"),
}


def get_provider(name: str) -> BaseProvider:
    """Return a literature-source provider instance by name or alias."""
    factory = PROVIDER_FACTORIES.get(name)
    if factory is None:
        known = ", ".join(sorted(PROVIDER_FACTORIES))
        raise ValueError(f"unknown provider: {name} (known: {known})")
    return factory()


def __getattr__(name: str):
    if name in _CLASS_MODULES:
        return getattr(import_module(_CLASS_MODULES[name]), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "BaseProvider",
    "SearchResult",
    "ProbeResult",
    "ProviderError",
    "PROVIDER_FACTORIES",
    "get_provider",
    "IeeeXploreProvider",
    "SemanticScholarProvider",
    "ArxivProvider",
    "DblpProvider",
]
