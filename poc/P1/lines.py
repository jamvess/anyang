"""Line scorer for PoC P1: is a transcribed line the same as the label line?

A line counts as read correctly when it is mathematically equal to the label line
(specs/poc/README.md P1), without evaluating what the student did not write: a derivative,
limit or integral is compared as written, never computed. PoC-only code; the real SymPy
service is apps/api/app/math (Junior, S3).

Needs `antlr4-python3-runtime==4.11` (`uv run --with ...`). The `lark` backend of SymPy is
not used: it silently misparses lines such as `2x\\sin(x)+x^{2}\\cos(x)`.
"""

import re
import sys
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "apps" / "api"))

import sympy  # noqa: E402
from sympy.parsing.latex import parse_latex  # noqa: E402

from app.settings import get_settings  # noqa: E402

# config/learning.yaml -> checker.sympy_timeout_seconds
TIMEOUT_S = get_settings().learning.checker.sympy_timeout_seconds

_SPACING = re.compile(r"\\left|\\right|\\[,;:! ]|\s+|\$")
_OPEN, _CLOSE = "({[", ")}]"
_UNEVALUATED = (sympy.Derivative, sympy.Limit, sympy.Integral)
_pool = ThreadPoolExecutor(max_workers=1)


def normalize(latex: str) -> str:
    return _SPACING.sub("", latex).lstrip("=")


def split_top_level(latex: str) -> list[str]:
    """Split on commas that are not inside (), {} or []."""
    parts, depth, start = [], 0, 0
    for i, ch in enumerate(latex):
        if ch in _OPEN:
            depth += 1
        elif ch in _CLOSE:
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append(latex[start:i])
            start = i + 1
    parts.append(latex[start:])
    return [p.strip() for p in parts if p.strip()]


@lru_cache(maxsize=4096)
def _parse(latex: str):
    return parse_latex(latex, backend="antlr")


def to_sympy(latex: str) -> list | None:
    """SymPy objects of one line, one per top-level comma part; None if any part fails."""
    text = latex.strip().lstrip("=").strip()
    if not text:
        return None
    try:
        return [_parse(part) for part in split_top_level(text)]
    except Exception:
        return None


def _opaque(exprs: list) -> list:
    """Replace derivatives, limits and integrals by symbols, so simplify cannot compute them.
    The same operation written the same way (after simplifying inside) gets the same symbol."""
    table: dict[str, sympy.Symbol] = {}

    def key(node) -> str:
        inner = [sympy.simplify(a) if isinstance(a, sympy.Expr) else a for a in node.args]
        return f"{type(node).__name__}{sympy.srepr(tuple(inner))}"

    def replace(expr):
        nodes = [n for n in sympy.preorder_traversal(expr) if isinstance(n, _UNEVALUATED)]
        mapping = {}
        for node in nodes:
            k = key(node)
            table.setdefault(k, sympy.Symbol(f"_op{len(table)}"))
            mapping[node] = table[k]
        return expr.xreplace(mapping)

    return [replace(e) for e in exprs]


def _zero(expr) -> bool:
    return sympy.simplify(expr) == 0


def _equivalent(a, b) -> bool:
    a, b = _opaque([a, b])
    if isinstance(a, sympy.Equality) and isinstance(b, sympy.Equality):
        da, db = a.lhs - a.rhs, b.lhs - b.rhs
        return _zero(da - db) or _zero(da + db)
    if isinstance(a, sympy.Equality) or isinstance(b, sympy.Equality):
        return False
    if isinstance(a, sympy.Basic) and isinstance(b, sympy.Basic) and a.is_Relational:
        return sympy.srepr(a) == sympy.srepr(b)
    return _zero(a - b)


def equivalent(a, b, timeout_s: float = TIMEOUT_S) -> bool:
    """SymPy equality with a time limit (simplify can hang). A timeout counts as different.
    PoC: the thread is not killed on timeout; the real service uses a subprocess."""
    try:
        return _pool.submit(_equivalent, a, b).result(timeout=timeout_s)
    except FutureTimeout:
        return False
    except Exception:
        return False


def same_line(predicted: str, label: str) -> bool:
    if normalize(predicted) == normalize(label):
        return True
    p, t = to_sympy(predicted), to_sympy(label)
    if p is None or t is None or len(p) != len(t):
        return False
    unmatched = list(t)
    for part in p:  # multi-part answers ("x=0, x=\ln(2)") may come in any order
        hit = next((u for u in unmatched if equivalent(part, u)), None)
        if hit is None:
            return False
        unmatched.remove(hit)
    return True


@dataclass
class Alignment:
    correct: int
    pairs: list[tuple[int, int]] = field(default_factory=list)
    predicted_wrong: list[int] = field(default_factory=list)
    label_missed: list[int] = field(default_factory=list)


def align(
    predicted: list[str], label: list[str], same: Callable[[str, str], bool] = same_line
) -> Alignment:
    """Longest in-order matching of predicted lines to label lines (LCS)."""
    n, m = len(predicted), len(label)
    match = [[same(predicted[i], label[j]) for j in range(m)] for i in range(n)]
    best = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            best[i][j] = max(
                best[i + 1][j], best[i][j + 1], best[i + 1][j + 1] + 1 if match[i][j] else 0
            )
    pairs, i, j = [], 0, 0
    while i < n and j < m:
        if match[i][j] and best[i][j] == best[i + 1][j + 1] + 1:
            pairs.append((i, j))
            i, j = i + 1, j + 1
        elif best[i + 1][j] >= best[i][j + 1]:
            i += 1
        else:
            j += 1
    matched_p = {p for p, _ in pairs}
    matched_l = {lab for _, lab in pairs}
    return Alignment(
        correct=len(pairs),
        pairs=pairs,
        predicted_wrong=[k for k in range(n) if k not in matched_p],
        label_missed=[k for k in range(m) if k not in matched_l],
    )
