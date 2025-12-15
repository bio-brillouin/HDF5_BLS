from setuptools import setup, find_packages
from os import path
working_directory = path.abspath(path.dirname(__file__))
print(working_directory)

with open(path.join(working_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Helper function to read requirements.txt
def parse_requirements(filename):
    """Load requirements from a pip requirements file."""
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Read the requirements from requirements.txt
requirements = parse_requirements('/Users/pierrebouvet/Documents/Code/HDF5_BLS/requirements_library.txt')

setup(
    name='HDF5_BLS_GUI', # name of pack which will be package dir below project
    version='0.0.1', 
    url='https://github.com/bio-brillouin/HDF5_BLS_GUI',
    author='Pierre Bouvet',
    author_email='pierre.bouvet@meduniwien.ac.at',
    description='A package to interface the HDF5_BLS library with a GUI',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(), 
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
) 