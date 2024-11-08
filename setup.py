from setuptools import setup, find_packages
from os import path
working_directory = path.abspath(path.dirname(__file__))

with open(path.join(working_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='HDF5_BLS', # name of pack which will be package dir below project
    version='0.0.5',
    url='https://github.com/PierreBouvet/HDF5_BLS',
    author='Pierre Bouvet',
    author_email='pierre.bouvet@meduniwien.ac.at',
    description='A package to convert Brillouin spectra to a HDF5 file and use them',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(), 
    install_requires=[
        "h5py >= 3",
        "pillow >= 11",
        "numpy >= 2"
        ],
) 