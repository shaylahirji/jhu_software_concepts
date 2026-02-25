# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

import os
import sys

# Since this file is in 'module_4/docs/conf.py', we go up one level to 'module_4'
# and then into 'src' so Sphinx can find your python files directly.
sys.path.insert(0, os.path.abspath('../src'))

# -- Project information -----------------------------------------------------

project = 'Grad Cafe Application - Module 4'
copyright = '2026, Shayla Hirji'
author = 'Shayla Hirji'

# The full version, including alpha/beta/rc tags
release = '1.0'


# -- General configuration ---------------------------------------------------

# Extensions to enable automatic documentation from docstrings
extensions = [
    'sphinx.ext.autodoc',     # Generates documentation from docstrings
    'sphinx.ext.napoleon',    # Support for Google/NumPy style docstrings
    'sphinx.ext.viewcode',    # Adds links to highlighted source code
    'sphinx.ext.githubpages', # Prepares documentation for GitHub Pages
    'sphinx.ext.intersphinx'  # Links to other project documentation
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '.venv']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# -- Extension configuration -------------------------------------------------

# Autodoc settings
autodoc_member_order = 'bysource'
autoclass_content = 'both'  # Include both class and __init__ docstrings