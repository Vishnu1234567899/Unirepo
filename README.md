# Python 3.11 Dependency Compatibility Checker

This project checks pinned `requirements.txt` entries against the PyPI JSON API.

## What it reports

- Number of physical lines in the requirements file
- Package or pinned release not found on PyPI
- Existing releases incompatible with Python 3.11 according to `requires_python`
- Release with the highest minimum Python requirement

## Requirements

- Python 3.9+
- Internet access
- `packaging`

Install the dependency:

```bash
python -m pip install packaging
```

## Run

```bash
python check_python311.py
```

To check another file:

```bash
python check_python311.py path/to/requirements.txt
```

Do not install the packages listed in the test's requirements file. This program only queries PyPI metadata.

## GitHub submission

Create a **public** repository named `python311-dependency-checker`, then run these commands from this folder:

```bash
git init
git add .
git commit -m "Add Python 3.11 dependency checker"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/python311-dependency-checker.git
git push -u origin main
```

Replace `YOUR-USERNAME` with your GitHub username and submit the public repository URL on PANDA.
