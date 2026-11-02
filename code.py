import sys
import json
import urllib.error
import urllib.request
import packaging.specifiers
import packaging.version

PYTHON_TARGET = packaging.version.Version("3.11")


SAMPLE_DEPS = [

    "requests==2.31.0",
    "django==6.0",
    "numpy==1.21.6",
    "flask==3.0.0",
    "langchain-pdf-agent==0.1.0",
]


TEST_DEPS = [
    "django==4.2",
    "numpy==2.3.0",
    "scipy==1.7.0",
    "scikit-learn==1.4.0",
    "fastapi-agent-router==0.3.1",
    "matplotlib==3.99.0",
    "six==1.16.0",
    "requests==2.32.0",
]


def parse_dep(dep):
    name, version = dep.split("==", 1)
    return name.strip(), version.strip()


def get_release(name, version):
    """Release JSON for exactly name==version, or None if it doesn't exist."""
    url = f"https://pypi.org/pypi/{name}/{version}/json"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None  # package or version does not exist
        raise


def min_python(spec):
    """Lowest Python version a SpecifierSet requires, or None."""
    lows = [
        packaging.version.Version(s.version.replace(".*", ""))
        for s in spec
        if s.operator in (">=", ">", "==", "~=")
    ]
    return max(lows) if lows else None


def main():
    deps = SAMPLE_DEPS if "sample" in sys.argv[1:] else TEST_DEPS

    not_found = []
    incompatible = []
    checked = 0
    highest = (None, None)  # (dep, min python Version)

    for dep in deps:
        checked += 1  # count every dependency, found or not
        name, version = parse_dep(dep)
        data = get_release(name, version)
        if data is None:
            not_found.append(dep)
            continue

        req_py = data["info"].get("requires_python")
        if not req_py:
            continue  # no requires_python: counts as compatible

        spec = packaging.specifiers.SpecifierSet(req_py)
        if not spec.contains(PYTHON_TARGET):
            incompatible.append(dep)

        low = min_python(spec)
        if low is not None and (highest[1] is None or low > highest[1]):
            highest = (dep, low)

    print(f"Dependencies checked: {checked}")
    print(f"Not found on PyPI: {len(not_found)}")
    print(f"Incompatible with Python 3.11: {len(incompatible)}")
    if highest[0]:
        print(f"Highest requirement: {highest[0]} (>={highest[1]})")
    else:
        print("Highest requirement: None")


if __name__ == "__main__":
    main()