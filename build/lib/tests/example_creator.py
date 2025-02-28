import numpy as np
import os
import h5py

def create_Ghost_abscissa_DAT():
    """Creates an abscissa for the example GHOST file.
    """
    abscissa = np.linspace(0,20.1257, 512)
    np.save("tests/test_data/example_abscissa_GHOST.npy",abscissa)
