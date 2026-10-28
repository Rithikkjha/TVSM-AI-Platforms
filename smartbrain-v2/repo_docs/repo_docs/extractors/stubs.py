"""Planned stub extractors (``<stack>.planned``): ``extract`` raises NotImplementedError; files of
those stacks stay ``pending`` for phase 3 and the stack is listed in ``missing_extractors``."""
from __future__ import annotations

from .base import ExtractResult, Extractor

PLANNED_STACKS = ("android", "react-native", "vue", "python", "ios", "dart", "flutter", "php")


class PlannedExtractor(Extractor):
    status = "planned"
    extractor_version = "0.0.0"

    def extract(self, ctx, subproject) -> ExtractResult:
        raise NotImplementedError("planned")


def _make(stack: str) -> type[Extractor]:
    name = "".join(p.capitalize() for p in stack.replace("-", "_").split("_")) + "PlannedExtractor"
    return type(name, (PlannedExtractor,), {"id": f"{stack}.planned", "stacks": (stack,)})


STUBS: dict[str, type[Extractor]] = {f"{s}.planned": _make(s) for s in PLANNED_STACKS}
