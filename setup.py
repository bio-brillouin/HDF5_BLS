from setuptools import setup, find_packages

setup(
    name="HDF5_BLS",                 # Package name on PyPI
    version="0.1.001",
    author="Your Name",
    author_email="your.email@example.com",
    description="A library for creating Brillouin Light Scattering HDF5 files",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/PierreBouvet/HDF5_BLS", 
    packages=find_packages(),         # Automatically find packages in the directory
    install_requires=[
        "numpy",
        "h5py",
        "matplotlib",
        "pillow"                     # Required for .TIFF files
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)