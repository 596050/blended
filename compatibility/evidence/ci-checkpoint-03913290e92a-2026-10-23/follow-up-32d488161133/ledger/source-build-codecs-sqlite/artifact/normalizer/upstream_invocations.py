"""Authenticate declarations against complete checksum-bound upstream CMake.

The catalog retains every declaration, including conditional and generated
ones. It is a source inventory, never a configured CTest denominator. Manifest
authors cannot create authority by editing both argv and registration text.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re
import shlex

CATALOG_PATH = Path(__file__).with_name("upstream_invocations_5_2.json")
CATALOG_SHA256 = "c326f9a99e665b15901dda134afd0c074c5c150441ed2971d977ce134a1fe7f2"
CATALOG_BYTES = 140627


def cmake_commands(text):
    """Read balanced command spans; retain conditions instead of evaluating them."""
    position = 0
    expression = re.compile(r"(?m)^[ \t]*([A-Za-z_][A-Za-z_0-9]*)[ \t\r\n]*\(")
    while match := expression.search(text, position):
        cursor, depth, quoted = match.end(), 1, False
        while cursor < len(text) and depth:
            character = text[cursor]
            if character == "\\":
                cursor += 2
                continue
            if character == '"':
                quoted = not quoted
            elif not quoted:
                bracket = re.match(r"\[(=*)\[", text[cursor:]) if character == "[" else None
                if bracket:
                    end = text.find("]" + bracket.group(1) + "]", cursor + len(bracket.group()))
                    if end == -1:
                        raise ValueError("unterminated CMake bracket argument")
                    cursor = end + len(bracket.group())
                    continue
                if character == "#":
                    newline = text.find("\n", cursor)
                    cursor = len(text) if newline == -1 else newline + 1
                    continue
                if character == "(":
                    depth += 1
                elif character == ")":
                    depth -= 1
            cursor += 1
        if depth:
            raise ValueError("unterminated CMake command")
        yield {"name": match.group(1).lower(), "arguments": text[match.end():cursor - 1],
               "text": text[match.start():cursor].strip(), "line": text.count("\n", 0, match.start()) + 1}
        position = cursor


def registrations(text):
    stack = []
    for command in cmake_commands(text):
        name = command["name"]
        if name in {"endif", "endforeach", "endfunction", "endmacro", "endwhile"}:
            if not stack:
                raise ValueError("unbalanced CMake block")
            stack.pop()
        elif name in {"else", "elseif"}:
            if not stack:
                raise ValueError("unbalanced CMake conditional")
            stack[-1]["branch"] = command["text"]
        elif name in {"if", "foreach", "function", "macro", "while"}:
            stack.append({"opener": command["text"], "line": command["line"]})
        elif name.startswith("add_blender_test"):
            yield {**command, "context": copy.deepcopy(stack)}
    if stack:
        raise ValueError("unclosed CMake block")


def load_catalog():
    raw = CATALOG_PATH.read_bytes()
    if len(raw) != CATALOG_BYTES or hashlib.sha256(raw).hexdigest() != CATALOG_SHA256:
        raise ValueError("pinned CMake declaration catalog bytes changed")
    catalog = json.loads(raw)
    for source in catalog["sources"]:
        data = source["text"].encode("utf-8")
        if len(data) != source["bytes"] or hashlib.sha256(data).hexdigest() != source["sha256"]:
            raise ValueError("pinned CMake declaration source bytes changed")
    source = next(row for row in catalog["sources"] if row["upstream_path"] == "tests/python/CMakeLists.txt")
    reconstructed = [{"source_declaration_index": index, "source_path": source["upstream_path"], **row}
                     for index, row in enumerate(registrations(source["text"]))]
    if len(reconstructed) != 132 or reconstructed != catalog["declarations"]:
        raise ValueError("pinned CMake declaration catalog does not reproduce the complete source")
    return catalog


def validate_original_invocation(name, text, cmake_sources):
    catalog = load_catalog()
    identities = [{key: source[key] for key in ("upstream_path", "bytes", "sha256")} for source in catalog["sources"]]
    matches = [row for row in catalog["declarations"] if row["text"] == text]
    if (cmake_sources != identities or len(matches) != 1 or matches[0]["context"] or
            matches[0]["name"] != "add_blender_test" or shlex.split(matches[0]["arguments"], comments=True)[0] != name):
        raise ValueError("registration differs from the independently pinned CMake declaration")
    return matches[0]


def validate_declaration(value):
    """Validate one authentic row; a subset is allowed but is not a full plan."""
    rows = load_catalog()["declarations"]
    index = value.get("source_declaration_index")
    if type(index) is not int or not 0 <= index < len(rows):
        raise ValueError("source row has no valid pinned CMake declaration index")
    expected = rows[index]
    if any(value.get(key) != expected[other] for key, other in
           (("line", "line"), ("registration", "text"), ("context", "context"))):
        raise ValueError("source row differs from the independently pinned CMake declaration")
    tokens = shlex.split(expected["arguments"], comments=True)
    if value.get("ctest_name") is not None and (not tokens or value["ctest_name"] != tokens[0]):
        raise ValueError("source name differs from the independently pinned CMake declaration")
    if value.get("upstream_path") is not None:
        match = re.fullmatch(r"\$\{(?:CMAKE_CURRENT_LIST_DIR|TEST_PYTHON_DIR)\}/([A-Za-z0-9_./-]+\.py)", tokens[2]) if len(tokens) >= 3 and tokens[1] == "--python" else None
        if match is None or value["upstream_path"] != "tests/python/" + match.group(1):
            raise ValueError("source path differs from the independently pinned CMake declaration")
    return expected
