# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import sys
import os

import HDF5_BLS
import HDF5_BLS_analyse
import HDF5_BLS_treat


sys.path.append("../")
sys.path.insert(0, os.path.abspath('..'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'HDF5_BLS'
copyright = '2025, Pierre Bouvet'
author = 'Pierre Bouvet'
release = 'v1.0.3'
html_favicon = '_static/myicon.png'
html_logo = "_static/myicon.png"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',      # For generating documentation from docstrings
    'sphinx.ext.napoleon',     # For Google-style and NumPy-style docstrings
    'sphinx.ext.viewcode',     # For adding links to the source code
    'sphinx.ext.autosummary',  # For generating summary tables
    'sphinx.ext.imgconverter',
]

# Add the directory containing your custom.css file
html_static_path = ['_static']

# Tell Sphinx to include your custom CSS file
html_css_files = [
    'custom.css',
]

autosummary_generate = True

autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
}

numfig = True
templates_path = ['_templates']
master_doc = 'index'
language = 'en'
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
