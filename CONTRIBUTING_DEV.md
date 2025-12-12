Development notes — running the package in-place
===============================================

When developing locally you have two convenient options to run and test the
package without doing a full install every time.

1) Editable install (recommended)

   Create and activate a virtual environment, then install the project in
   editable mode. This keeps the package importable as `HDF5_BLS` and picks up
   code changes immediately:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .
   pip install -r requirements.txt  # optional: install development deps
   ```

2) In-place import using PYTHONPATH

   If you prefer not to install, set PYTHONPATH (or add the package root to
   sys.path) so Python will import the package from the repository root. From
   the repository root run tests or scripts like:

   ```bash
   PYTHONPATH=$(pwd) .venv/bin/python -m pytest HDF5_BLS/tests
   ```

Notes
- The project uses a `src/` layout; the top-level `HDF5_BLS/__init__.py` file
  re-exports the real implementation in `src/` so the package can be imported
  in-place (e.g. `from HDF5_BLS import wrapper`).
- Prefer editable install for development because IDEs, linters and test
  runners resolve imports more consistently.
