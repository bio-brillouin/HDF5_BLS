#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python3 setup.py sdist bdist_wheel
pip install dist/HDF5_BLS-0.1.0-py3-none-any.whl -force-reinstall
python3 HDF5_BLS_GUI/main.py