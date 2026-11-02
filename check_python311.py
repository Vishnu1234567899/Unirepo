#!/usr/bin/env python3
"""Check whether pinned requirements are available and compatible with Python 3.11."""

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from packaging.specifiers import SpecifierSet
from packaging.version import Version

PYPI = "https://pypi.org/pypi"
PYTHON_VERSION = Version("3.11")
USER_AGENT = "python311-requirement-checker/1.0"


def fetch_json(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise


def parse_requirement(line, line_number):
    """Parse the simple package==version format used in the test."""
    cleaned = line.strip()
    if not cleaned or cleaned.startswith("#"):
        return None

    # Ignore inline comments.
    cleaned = cleaned.split(" #", 1)[0].strip()
    if "==" not in cleaned:
        raise ValueError(
            "Line {} is not pinned with package==version: {}".format(
                line_number, line.rstrip()
            )
        )

    name, version = cleaned.split("==", 1)
    name, version = name.strip(), version.strip()
    if not name or not version:
        raise ValueError("Invalid requirement on line {}".format(line_number))
    return name, version


def quote(value):
    return urllib.parse.quote(value, safe="")


def minimum_python_version(requires_python):
    """Extract the strongest explicit lower bound from a requires_python string.

    The assignment asks for the highest minimum Python version. In typical
    PyPI metadata this is expressed with >= or >.
    """
    if not requires_python:
        return None

    candidates = []
    for operator, version_text in re.findall(r"(>=|>)\s*([0-9]+(?:\.[0-9]+)*)", requires_python):
        try:
            version = Version(version_text)
        except Exception:
            continue
        candidates.append((version, operator, version_text))

    if not candidates:
        return None

    # Use the strongest lower bound in the requirement expression.
    version, operator, text = max(candidates, key=lambda item: item[0])
    return version, operator, text


def main():
    parser = argparse.ArgumentParser(
        description="Check requirements.txt against PyPI for Python 3.11."
    )
    parser.add_argument(
        "file",
        nargs="?",
        default="requirements.txt",
        help="Requirements file (default: requirements.txt)",
    )
    args = parser.parse_args()

    path = Path(args.file)
    if not path.is_file():
        print("Error: requirements file not found: {}".format(path), file=sys.stderr)
        return 1

    lines = path.read_text(encoding="utf-8").splitlines()
    not_found = []
    incompatible = []
    lower_bounds = []

    for line_number, line in enumerate(lines, start=1):
        parsed = parse_requirement(line, line_number)
        if parsed is None:
            continue

        name, version = parsed
        package_json = fetch_json("{}/{}/json".format(PYPI, quote(name)))

        if package_json is None:
            not_found.append("{}=={}".format(name, version))
            continue

        release_json = fetch_json(
            "{}/{}/{}/json".format(PYPI, quote(name), quote(version))
        )
        if release_json is None:
            not_found.append("{}=={}".format(name, version))
            continue

        requires_python = (release_json.get("info") or {}).get("requires_python")

        # A missing/empty requires_python field is treated as compatible,
        # as specified in the task.
        if requires_python:
            try:
                compatible = SpecifierSet(requires_python).contains(
                    str(PYTHON_VERSION), prereleases=True
                )
            except Exception:
                # If PyPI contains an invalid specifier, don't silently call
                # the release compatible.
                compatible = False

            if not compatible:
                incompatible.append("{}=={}".format(name, version))

            lower_bound = minimum_python_version(requires_python)
            if lower_bound:
                lower_bounds.append((lower_bound[0], name, version, lower_bound[1], lower_bound[2]))

    highest = max(lower_bounds, key=lambda item: item[0]) if lower_bounds else None

    print("Dependencies checked: {}".format(len(lines)))
    print("Not found on PyPI: {}".format(len(not_found)))
    if not_found:
        print("  " + ", ".join(not_found))

    print("Incompatible with Python 3.11: {}".format(len(incompatible)))
    if incompatible:
        print("  " + ", ".join(incompatible))

    if highest:
        _, name, version, operator, minimum = highest
        # The assignment's sample output displays the minimum as >=3.x.
        print("Highest requirement: {}=={} ({}{})".format(
            name, version, operator, minimum
        ))
    else:
        print("Highest requirement: None")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, urllib.error.URLError, json.JSONDecodeError, ValueError) as error:
        print("Error: {}".format(error), file=sys.stderr)
        raise SystemExit(1)
