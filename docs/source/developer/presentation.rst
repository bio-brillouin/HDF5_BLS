Presentation of the project for developers
==========================================

Structure of the GitHub repository
----------------------------------

The project is composed of three blocks containing the three independent Python libraries:

- **HDF5\_BLS**: The library used to interface an HDF5 file to comply with the BLS standard we are developing.
- **HDF5\_BLS\_analyse**: The library performing the conversion of data obtained by a spectrometer to a Power spectrum.
- **HDF5\_BLS\_treat**: The library performing the treatment of the data (fitting, normalization, etc.).

The project has additionally, a graphical user interface (GUI) to facilitate the use of the library:

 - **HDF5\_BLS\_GUI**: The GUI used to interact with the library.

And the basis for a web viewer currently under development:

 - **HDF5\_BLS\_webview**: The web viewer used to interact with the library.

All these modules are independent but at the same time part of the same main goal: to unify and standardize the storage of BLS data in a HDF5 file, and to develop unified tools to process these data.

As such, the project is structured as a "monorepo" structure:

.. code-block:: bash

    .
    ├── data <- static data used in the project (algorithms, images, spreadsheets, etc.)
    ├── docs <- documentation of the project
    ├── packages <- the repository where all the Python scripts are stored
    │   ├── HDF5_BLS 
    │   ├── HDF5_BLS_analyse 
    │   ├── HDF5_BLS_treat
    │   └── HDF5_BLS_GUI
    ├── HDF5_BLS_webview
    ├── tests <- tests of the project
    └── ... <- other files like the README, LICENSE, etc.

We have also adopted the setuptools src-layout to organize the Python packages:

.. code-block:: bash

    .
    └── HDF5_BLS
        ├── src
        │   └── _HDF5_BLS
        │       ├── __init__.py
        │       ├── file.py
        │       └── ...
        ├── tests
        ├── pyproject.toml
        └── README.md

Documentation
-------------

The documentation is written in reStructuredText and is built using Sphinx. The documentation is hosted on `Read the Docs <https://hdf5-bls.readthedocs.io/en/latest/>`__. To compile the documentation locally, you need to install both Sphinx and the Read the Docs theme:

.. code-block:: bash

    pip install sphinx sphinx-rtd-theme

Then, you can compile the documentation by running the following command in the ``docs`` directory:

.. code-block:: bash

    make html

The documentation will be generated in the ``docs/build/html`` directory.

You can also compile the documentation as a latex file to get a pdf version:

.. code-block:: bash

    make latex

.. important::
    Part of the documentation is automatically generated from the docstrings of the code. The docstrings are written in the numpydoc format. The documentation is built using Sphinx.


Docstrings
----------

Docstrings are used to automatically generate the documentation of the code. They are written in the `numpydoc format <https://numpydoc.readthedocs.io/en/latest/format.html>`__ and are placed in the docstring of the functions. The docstrings are automatically extracted and used to generate the documentation.


    