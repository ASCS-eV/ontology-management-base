import ast
import os
import re
import sys
import textwrap
import unicodedata
from io import StringIO
from pathlib import Path
from typing import Callable, List, Optional, Union

from rdflib import RDF, BNode, Graph, Namespace
from rdflib.collection import Collection
from rdflib.term import Node

from omb.core.result import Violation


def ensure_utf8_output() -> None:
    """Make ``stdout``/``stderr`` able to carry the emoji this package prints.

    Every OMB ``main()`` calls this first. Python picks the console's encoding for
    ``sys.stdout``, which on Windows is a legacy code page (cp1252) unless UTF-8 mode
    is on — and the first thing the validation suite prints is "🔍", so an installed
    ``onto-validate`` died there with ``UnicodeEncodeError`` before doing any work::

        UnicodeEncodeError: 'charmap' codec can't encode character '\\U0001f50d'

    The repository never saw this because its ``justfile`` exports ``PYTHONUTF8=1``,
    and the equivalent stream re-wrapping lived under ``if __name__ == "__main__"``,
    which the ``onto-validate`` console script and ``python -m omb`` both bypass.

    Safe to call repeatedly, and on streams that cannot be reconfigured (a pipe
    replaced by a test harness, a ``StringIO``): those are left untouched.
    """
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="backslashreplace")
        except (ValueError, OSError):
            # Detached or already-closed stream: printing is the caller's problem now.
            continue


def normalize_text(text: str) -> str:
    """Standardizes text by scrubbing variable blank node IDs for test comparison."""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _clean(text)
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)
    pattern = r"(={10,}\n(?:\s*=.*\n)+={10,}\n(?:\s*=.*\n)+={10,})"
    match = re.search(pattern, text)
    return match.group(0).strip() if match else ""


def normalize_path_for_display(path: Union[str, Path], root_dir: Path) -> str:
    """
    Convert any path to a portable, relative string for console output.

    Prevents leaking user/machine folder information (e.g. /home/user/... or a uv
    cache directory) in console output, and keeps report snapshots stable across
    machines and CI. Always uses forward slashes for cross-platform consistency.

    Resolution order:
      1. If ``path`` is inside ``root_dir`` (OMB's own built-in data), render it
         relative to ``root_dir`` (e.g. "artifacts/scenario/scenario.owl.ttl").
      2. Otherwise ``path`` is an external/consumer input (e.g. ``--data-paths`` or
         ``--artifacts``). ``root_dir`` MUST NOT be the display base here: when OMB
         runs from an installed wheel it is a machine-specific location (a uv/pip
         cache), so a ``root_dir``-relative ``../`` traversal would embed that path
         and differ on every machine. Render relative to the current working
         directory, which is stable in the consumer's checkout and CI, instead.
      3. If ``path`` is under neither ``root_dir`` nor the working directory, fall
         back to a deterministic traversal from the working directory (same drive) or
         the bare filename — never an absolute or user-specific path.

    Args:
        path: Path to normalize (string or Path object)
        root_dir: OMB's built-in data root (used only for case 1)

    Returns:
        Portable relative path string with forward slashes.
    """
    if isinstance(path, str):
        path = Path(path)

    # Resolve to absolute for comparison
    try:
        path = path.resolve()
    except (OSError, ValueError):
        return str(path).replace("\\", "/")

    root_dir = root_dir.resolve()

    # 1) OMB's own built-in data: render relative to root_dir.
    try:
        return path.relative_to(root_dir).as_posix()
    except ValueError:
        pass

    # 2) External/consumer path: render relative to the working directory (stable in
    #    the consumer's repo and CI), NOT relative to root_dir, which may be a
    #    machine-specific wheel/cache location.
    try:
        cwd = Path.cwd().resolve()
    except (OSError, ValueError):
        return path.name
    try:
        return path.relative_to(cwd).as_posix()
    except ValueError:
        pass

    # 3) Under neither root_dir nor cwd: deterministic traversal from cwd on the same
    #    drive, else the bare filename. Never leak an absolute/user-specific path.
    try:
        if path.anchor != cwd.anchor:
            return path.name
        return Path(os.path.relpath(path, cwd)).as_posix()
    except (ValueError, OSError):
        return path.name


#: pySHACL's generic sh:in message ends with the Python repr of the allowed values.
_SH_IN_MESSAGE = re.compile(r"(?<=not in list )(\[.*\])$", re.DOTALL)


def _sort_sh_in_values(message: str) -> str:
    """Render the allowed values of an sh:in message in sorted order.

    pySHACL collects them in a set, so their order follows string hashing and
    changes from one process to the next; a report snapshot must not.
    A custom ``sh:message`` that merely contains the phrase is left as it is.
    """
    match = _SH_IN_MESSAGE.search(message)
    if not match:
        return message
    try:
        values = ast.literal_eval(match.group(1))
    except (ValueError, SyntaxError):
        return message
    if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
        return message
    return message[: match.start(1)] + repr(sorted(values))


#: pySHACL renders a blank node in a message to a fixed depth, marks where it stopped
#: with this IRI, and caches the rendering under the node alone. Which path reaches a
#: shared node first decides where it is cut off, and that follows string hashing.
_RECURSION_MARKER = "<http://recursion.too.deep>"
_TRUNCATED_NODE = "[ ... ]"


def _matching_bracket(text: str, start: int) -> int | None:
    """Index of the ``]`` closing the ``[`` at ``start``, skipping quoted literals."""
    depth, quoted, i = 0, False, start
    while i < len(text):
        char = text[i]
        if quoted:
            if char == "\\":
                i += 1
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return None


def _collapse_truncated_nodes(message: str) -> str:
    """Replace each blank-node rendering pySHACL cut off with a fixed placeholder.

    A rendering that was not cut off is complete and sorted, so it is kept.
    """
    if _RECURSION_MARKER not in message:
        return message
    parts, i = [], 0
    while i < len(message):
        end = _matching_bracket(message, i) if message.startswith("[ ", i) else None
        if end is None:
            parts.append(message[i])
            i += 1
            continue
        span = message[i : end + 1]
        parts.append(_TRUNCATED_NODE if _RECURSION_MARKER in span else span)
        i = end + 1
    return "".join(parts)


def _clean(val) -> str:
    """Helper to apply path and bnode normalization to a single string value."""
    if val is None:
        return ""
    v = str(val)
    v = re.sub(r"N[a-f0-9]{32}", "[BNODE]", v)
    return v


def _get_visual_width(text: str) -> int:
    """Calculate visual width, counting wide emoji characters as 2 cells."""
    wide_chars = ["🔹", "❌", "✅", "⚠️", "🔍", "📌"]
    return len(text) + sum(text.count(c) for c in wide_chars)


def _print_boxed_line(text: str, width: int, file=None):
    """Prints a line framed by '= ... =' with visual width compensation."""
    inner_width = width - 4
    padding = inner_width - _get_visual_width(text)
    print(f"= {text}{' ' * max(0, padding)} =", file=file)


#: Severities that do not make a graph non-conformant when warnings are allowed.
ADVISORY_SEVERITIES = ("Warning", "Info")


def _severity_name(severity) -> str:
    """Local name of a ``sh:resultSeverity``; absent severity means Violation."""
    return str(severity).split("#")[-1] if severity else "Violation"


def _extract_and_sort_errors(report_graph: Graph, advisory: bool = False):
    """Extracts and sorts results deterministically using normalized content.

    Args:
        report_graph: SHACL validation report graph.
        advisory: If False (default), return only results that make the graph
            non-conformant. If True, return only ``sh:Warning``/``sh:Info``
            results. Splitting them keeps advisory results out of the recorded
            ``.expected`` snapshots, so adding a warning-severity constraint
            cannot churn 40-odd unrelated negative-test snapshots.
    """
    SH = Namespace("http://www.w3.org/ns/shacl#")
    results = list(report_graph.subjects(RDF.type, SH.ValidationResult))
    error_rows = []
    seen = set()

    for result in results:
        severity = report_graph.value(result, SH.resultSeverity)
        is_advisory = _severity_name(severity) in ADVISORY_SEVERITIES
        if is_advisory != advisory:
            continue
        data = {
            "focus_node": report_graph.value(result, SH.focusNode),
            "result_path": report_graph.value(result, SH.resultPath),
            "result_message": report_graph.value(result, SH.resultMessage),
            "severity": severity,
        }
        sig = (
            str(data["focus_node"]),
            str(data["result_path"]),
            str(data["result_message"]),
        )
        if sig in seen:
            continue
        seen.add(sig)
        error_rows.append(data)

    # Sort by normalized path, then message, then node ID (normalized)
    # REMOVED: str(x["focus_node"]) to prevent sorting by random BNode IDs
    error_rows.sort(
        key=lambda x: (
            _clean(x["result_path"]),
            _clean(x["result_message"]),
            _clean(x["focus_node"]),
        )
    )
    return error_rows


_SH = Namespace("http://www.w3.org/ns/shacl#")

#: Unary SHACL path operators and their notation in :attr:`Violation.path`.
_UNARY_PATHS = (
    (_SH.inversePath, "^{}"),
    (_SH.zeroOrMorePath, "{}*"),
    (_SH.oneOrMorePath, "{}+"),
    (_SH.zeroOrOnePath, "{}?"),
)

#: A node rendering in a violation message longer than this is shortened to
#: ``[ ... ]``. pySHACL renders a blank node with everything reachable from it, so an
#: ``sh:or`` or ``sh:closed`` message about a document's nested content runs to tens
#: of thousands of characters; the violation's other fields locate the node instead.
_MAX_NODE_RENDERING = 120


def _local_name(term) -> str:
    """Final path or fragment segment of an IRI -- the property or component name."""
    return str(term).rsplit("/", 1)[-1].rsplit("#", 1)[-1]


def _term_text(term) -> str:
    """An IRI or literal verbatim, a blank node as ``[BNODE]``, no term as ``""``."""
    if term is None:
        return ""
    if isinstance(term, BNode):
        return "[BNODE]"
    return str(term)


def _is_sequence_path(report_graph: Graph, path) -> bool:
    return isinstance(path, BNode) and report_graph.value(path, RDF.first) is not None


def _render_path(report_graph: Graph, path) -> str:
    """A SHACL property path in compact notation, one local name per IRI.

    A sequence reads ``a/b``, an alternative ``(a|b)``, an inverse ``^p`` and the
    repetitions ``p*``, ``p+`` and ``p?``. A blank node identifier never appears: a
    path of any other shape renders as ``[ ... ]``.
    """
    if not isinstance(path, BNode):
        return _local_name(path)
    if _is_sequence_path(report_graph, path):
        steps = Collection(report_graph, path)
        return "/".join(_render_path(report_graph, step) for step in steps)
    alternatives = report_graph.value(path, _SH.alternativePath)
    if alternatives is not None:
        steps = Collection(report_graph, alternatives)
        return "({})".format("|".join(_render_path(report_graph, s) for s in steps))
    for operator, notation in _UNARY_PATHS:
        operand = report_graph.value(path, operator)
        if operand is not None:
            text = _render_path(report_graph, operand)
            if _is_sequence_path(report_graph, operand):
                text = f"({text})"
            return notation.format(text)
    return _TRUNCATED_NODE


def _violation_message(message) -> str:
    """A result message in the stable, compact form :attr:`Violation.message` holds.

    Blank node identifiers are scrubbed, pySHACL's hash-dependent message parts
    (``sh:in`` value order, cut-off node renderings) put in a fixed form, and long
    node renderings shortened.
    """
    text = _sort_sh_in_values(_collapse_truncated_nodes(_clean(message)))
    return _shorten_node_renderings(text.strip())


def _shorten_node_renderings(message: str) -> str:
    """Replace each node rendering longer than ``_MAX_NODE_RENDERING`` with ``[ ... ]``."""
    parts, i = [], 0
    while i < len(message):
        end = _matching_bracket(message, i) if message.startswith("[ ", i) else None
        if end is None:
            parts.append(message[i])
            i += 1
            continue
        span = message[i : end + 1]
        parts.append(_TRUNCATED_NODE if len(span) > _MAX_NODE_RENDERING else span)
        i = end + 1
    return "".join(parts)


def _iter_violation_leaves(report_graph: Graph, node, path: tuple):
    """Yields ``(path, result)`` for every leaf result reachable from ``node``.

    ``path`` accumulates the ``sh:resultPath`` of each hop traversed, so a leaf
    carries the full location of the value that actually failed.
    """
    segment = report_graph.value(node, _SH.resultPath)
    if segment is not None:
        path = path + (_render_path(report_graph, segment),)
    details = list(report_graph.objects(node, _SH.detail))
    if not details:
        yield path, node
        return
    for detail in details:
        yield from _iter_violation_leaves(report_graph, detail, path)


def extract_violations(
    report_graph: Graph,
    advisory: bool = False,
    file_of: Optional[Callable[[Node], str]] = None,
) -> List[Violation]:
    """Returns one :class:`Violation` per distinct constraint violation, sorted.

    pySHACL reports a failure inside a nested shape as a chain of results: each hop
    carries only "Value does not conform to Shape X. See details for more
    information.", and the constraint that actually failed hangs off ``sh:detail``.
    Only the ends of these chains are returned, each located by the
    ``sh:resultPath`` of every hop traversed to reach it, so a violation inside a
    nested object reads ``road_network/overhead_structure/tunnel_phase``.

    Severity comes from the top-level result, because only top-level results decide
    conformance; a nested result carries the severity of its own shape. A
    Warning-severity shape that reaches a constraint through ``sh:node`` is advisory
    even though the nested result says Violation, and the reverse holds too.

    The same violation surfaces once per shape that reaches it: pySHACL validates a
    nested shape that has a target on its own, as well as through each parent. Ends
    of chains are de-duplicated on the RDF terms identifying the violation (focus
    node, value, constraint component, source shape and message), so two distinct
    blank nodes failing the same way remain two violations. Each is reported at its
    longest path, the one rooted at the validated document; among equally long
    paths the lowest-sorting violation wins.

    Args:
        report_graph: SHACL validation report graph.
        advisory: If False (default), return only violations that make the graph
            non-conformant. If True, return only ``sh:Warning``/``sh:Info`` ones.
            Mirrors :func:`_extract_and_sort_errors`.
        file_of: Maps a top-level focus node to the input file holding it, for
            :attr:`Violation.file`. Without it the file is left empty.

    Returns:
        Sorted violations. Blank node identifiers are scrubbed and hash-dependent
        message parts normalized, so the result is stable across runs.
    """
    nested = set(report_graph.objects(None, _SH.detail))
    best = {}
    for root in report_graph.subjects(RDF.type, _SH.ValidationResult):
        if root in nested:
            continue
        severity = _severity_name(report_graph.value(root, _SH.resultSeverity))
        if (severity in ADVISORY_SEVERITIES) != advisory:
            continue
        root_focus = report_graph.value(root, _SH.focusNode)
        file = file_of(root_focus) if file_of and root_focus is not None else ""
        for path, leaf in _iter_violation_leaves(report_graph, root, ()):
            identity = tuple(
                report_graph.value(leaf, predicate)
                for predicate in (
                    _SH.focusNode,
                    _SH.value,
                    _SH.sourceConstraintComponent,
                    _SH.sourceShape,
                    _SH.resultMessage,
                )
            )
            _, value, component, shape, message = identity
            component_name = "" if component is None else _local_name(component)
            text = _violation_message(message)
            candidate = (
                -len(path),
                Violation(
                    file=file,
                    path="/".join(path),
                    message=text or component_name,
                    component=component_name,
                    focus_node=_term_text(root_focus),
                    value=_term_text(value),
                    source_shape="" if isinstance(shape, BNode) else _term_text(shape),
                    severity=severity,
                ),
            )
            if identity not in best or candidate < best[identity]:
                best[identity] = candidate

    return sorted(violation for _, violation in best.values())


def format_artifact_coherence_result(
    ontology_file, num_onto, num_shacl, matches, missing, extra
):
    """Formats validation summary using consistent boxed alignment."""
    width, buf = 150, StringIO()
    border = "=" * width
    print(f"\n{border}", file=buf)
    _print_boxed_line("VALIDATION SUMMARY".center(width - 4), width, buf)
    print(border, file=buf)
    _print_boxed_line(f"Ontology File: {_clean(ontology_file)}", width, buf)
    _print_boxed_line(f"🔹 Ontology Classes: {num_onto}", width, buf)
    _print_boxed_line(f"🔹 SHACL Target Classes: {num_shacl}", width, buf)
    _print_boxed_line(f"✅ Matched Classes: {len(matches)}", width, buf)
    _print_boxed_line(f"❌ Missing Classes: {len(missing)}", width, buf)
    _print_boxed_line(f"⚠️  Extra Classes: {len(extra)}", width + 2, buf)
    if missing:
        print(border, file=buf)
        _print_boxed_line(f"❌ Missing SHACL Classes: {len(missing)}", width, buf)
        for cls in sorted(missing):
            _print_boxed_line(f"   ❌ {cls}", width, buf)
    print(border, file=buf)
    status = "❌ Validation failed!" if missing else "✅ Validation successful!"
    _print_boxed_line(status.center(width - 5), width, buf)
    print(border, file=buf)
    return buf.getvalue().strip()


def format_data_conformance_result(
    success, onto_files=None, v_text="", report_graph=None, exit_code=None, file=None
):
    width, file = 150, file or sys.stdout
    border, inner_width = "=" * width, 146
    print(border, file=file)
    header = (
        "✅ SHACL validation passed for:"
        if success
        else "❌ SHACL validation failed for:"
    )
    _print_boxed_line(header.center(inner_width - 1), width, file=file)
    if onto_files:
        _print_boxed_line(" ", width, file=file)
        formatted_files = f"[{', '.join(f"'{_clean(f)}'" for f in onto_files)}]"
        for line in textwrap.wrap(formatted_files, width=inner_width):
            _print_boxed_line(line.center(inner_width), width, file=file)
        _print_boxed_line(" ", width, file=file)
        print(border, file=file)
    if not success and report_graph:
        _print_boxed_line(" ", width, file=file)
        _print_boxed_line(
            "Structured Validation Errors:".center(inner_width), width, file=file
        )
        _print_boxed_line("-" * inner_width, width, file=file)
        _print_result_rows(
            _extract_and_sort_errors(report_graph), width, inner_width, file
        )
        print(border, file=file)
    if exit_code is not None:
        sys.exit(exit_code)


def _print_result_rows(rows, width, inner_width, file):
    """Renders SHACL result rows as boxed, wrapped node/property/message blocks."""
    for i, row in enumerate(rows):
        sev = _severity_name(row["severity"])
        labels = [f"🔹 [{sev}] Node: ", "   Property: ", "   Error:    "]
        max_label_w = max(_get_visual_width(ll) for ll in labels)

        def pad(ll):
            return ll + (" " * (max_label_w - _get_visual_width(ll)))

        # Print Node
        node_val = _clean(row["focus_node"])
        wrapped_node = textwrap.wrap(node_val, width=inner_width - max_label_w)
        _print_boxed_line(f"{pad(labels[0])}{wrapped_node[0]}", width, file=file)
        for line in wrapped_node[1:]:
            _print_boxed_line(" " * max_label_w + line, width, file=file)

        # Print Property
        if row["result_path"]:
            prop_val = _clean(row["result_path"])
            wrapped_prop = textwrap.wrap(prop_val, width=inner_width - max_label_w)
            _print_boxed_line(f"{pad(labels[1])}{wrapped_prop[0]}", width, file=file)
            for line in wrapped_prop[1:]:
                _print_boxed_line(" " * max_label_w + line, width, file=file)

        # Print Error Message
        if row["result_message"]:
            msg_val = _clean(row["result_message"])
            wrapped_msg = textwrap.wrap(msg_val, width=inner_width - max_label_w)
            _print_boxed_line(f"{pad(labels[2])}{wrapped_msg[0]}", width, file=file)
            for line in wrapped_msg[1:]:
                _print_boxed_line(" " * max_label_w + line, width, file=file)

        if i < len(rows) - 1:
            _print_boxed_line("-" * inner_width, width, file=file)


def format_advisory_results(report_graph, files=None) -> str:
    """Render ``sh:Warning``/``sh:Info`` results as a separate, non-failing section.

    Returns an empty string when there are none. Deliberately *not* part of
    ``format_data_conformance_result``: advisory results must be visible in the
    console without entering the ``.expected`` snapshots that
    ``check-failing-tests`` compares byte for byte.
    """
    if report_graph is None:
        return ""
    rows = _extract_and_sort_errors(report_graph, advisory=True)
    if not rows:
        return ""

    width, inner_width = 150, 146
    border, buf = "=" * width, StringIO()
    print(border, file=buf)
    _print_boxed_line(
        "⚠️  Advisory results (do not fail validation):".center(inner_width - 1),
        width,
        file=buf,
    )
    if files:
        _print_boxed_line(" ", width, file=buf)
        formatted = f"[{', '.join(f"'{_clean(f)}'" for f in files)}]"
        for line in textwrap.wrap(formatted, width=inner_width):
            _print_boxed_line(line.center(inner_width), width, file=buf)
    _print_boxed_line("-" * inner_width, width, file=buf)
    _print_result_rows(rows, width, inner_width, buf)
    print(border, file=buf)
    return buf.getvalue()


def format_shacl_validation_result(
    success, onto_files=None, v_text="", report_graph=None, exit_code=None, file=None
):
    """Alias for format_data_conformance_result() for backwards compatibility."""
    format_data_conformance_result(
        success, onto_files, v_text, report_graph, exit_code, file
    )
