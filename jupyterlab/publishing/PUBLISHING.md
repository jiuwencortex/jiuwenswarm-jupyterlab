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

### Python package only (cell magics and notebook tools)

```bash
pip install -e ".[dev]"
%load_ext jiuwenswarm_jupyter   # in a notebook
```

### Full JupyterLab extension (includes sidebar panel)

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

# 2. Build Python wheel (bundles frontend + chat.html)
cd ../..
python -m build --wheel

# Output: dist/jiuwenswarm_jupyter-X.Y.Z-py3-none-any.whl
```

> `packages/shared-webview/chat.html` is automatically included in the wheel at
> `jiuwenswarm_jupyter/static/chat.html` via the `force-include` entry in
> `pyproject.toml`. No manual copy step is needed.

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

| Environment | Python | Status |
|---|---|---|
| JupyterLab 4.x | 3.10–3.12 | Full support — cell magics, sidebar panel, swarm map |
| JupyterLab 3.x | 3.10–3.12 | Not tested — sidebar panel may work with minor changes |
| classic Notebook | 3.10–3.12 | Cell magics and notebook tools work; sidebar panel does not |
| Google Colab | 3.10–3.12 | Cell magics, notebook tools, and `%jiuwen_chat` work |
| VS Code Notebooks | 3.10–3.12 | Cell magics and notebook tools work; sidebar panel does not |
| Kaggle Notebooks | 3.10–3.12 | Cell magics, notebook tools, and `%jiuwen_chat` work |
