# Publishing — jiuwenswarm-jupyterlab

## Package structure

This project publishes two artefacts:

| Artefact | Registry | Install command |
|---|---|---|
| `jiuwenswarm-jupyter` | PyPI | `pip install jiuwenswarm-jupyter` |
| `@jiuwenswarm/jupyterlab` | npm (not published separately) | bundled inside the Python wheel |

The TypeScript frontend is compiled with Webpack and its output is bundled into the Python wheel under `share/jupyter/labextensions/@jiuwenswarm/jupyterlab/`. JupyterLab discovers labextensions from that path automatically.

---

## Prerequisites

```bash
# Python tooling
pip install hatch build twine

# Node.js tooling (Node 18+)
npm install
```

---

## Local development setup

### Python package only (Phase 1)

```bash
pip install -e ".[dev]"
%load_ext jiuwenswarm_jupyter   # in a notebook
```

### Full JupyterLab extension (Phase 2)

```bash
# Build TypeScript
cd packages/frontend
npm install
npm run build:dev

# Install in development mode (labextension hot-reload)
pip install -e .
jupyter labextension develop --overwrite .
jupyter lab build

# Watch mode (rebuilds on TypeScript changes)
npm run watch   # in packages/frontend/
jupyter lab     # in a separate terminal
```

---

## Running tests

```bash
pytest tests/
```

---

## Building for release

```bash
# 1. Build TypeScript frontend
cd packages/frontend
npm run build   # production build → dist/

# 2. Build Python wheel (bundles frontend)
cd ../..
python -m build --wheel

# Output: dist/jiuwenswarm_jupyter-X.Y.Z-py3-none-any.whl
```

---

## Version bump

Version is set in two places:

| File | Field |
|---|---|
| `pyproject.toml` | `[project] version` |
| `jiuwenswarm_jupyter/__init__.py` | `__version__` |
| `packages/frontend/package.json` | `version` |

Update all three to the same version before releasing.

---

## Publishing to PyPI

```bash
# Test release
twine upload --repository testpypi dist/jiuwenswarm_jupyter-*.whl

# Verify install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ jiuwenswarm-jupyter

# Production release
twine upload dist/jiuwenswarm_jupyter-*.whl
```

Credentials: use an API token (`__token__` as username, token as password), or configure `~/.pypirc`.

---

## CI / release checklist

- [ ] All tests pass (`pytest tests/`)
- [ ] TypeScript builds clean (`npm run build` with no errors)
- [ ] Version bumped in all three files
- [ ] `CHANGELOG` updated (if maintained)
- [ ] Wheel built and tested locally in a clean venv
- [ ] Published to TestPyPI and smoke-tested
- [ ] Published to PyPI
- [ ] Git tag created: `git tag vX.Y.Z && git push origin vX.Y.Z`

---

## Compatibility matrix

| JupyterLab | Python | Status |
|---|---|---|
| 4.x | 3.10–3.12 | supported (Phase 2 target) |
| 3.x | 3.10–3.12 | not tested (Phase 2 may support with minor changes) |
| classic Notebook | 3.10–3.12 | Phase 1 only (cell magic works, sidebar panel does not) |
| Google Colab | 3.10–3.12 | Phase 1 only (standard pip + IPython magic) |
| VS Code Notebooks | 3.10–3.12 | Phase 1 only |
