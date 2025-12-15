import h5py
import numpy as np
from collections import defaultdict

TREATMENT_LEVEL = ['Shift', 'Shift_std', 'Linewidth', 'Linewidth_std', 'Amplitude', 
                   'Amplitude_std', 'BLT', 'BLT_std']
BT_TO_ATTR = { # Brillouin_type to brimfile attribute pair types, Pierre: Carlo,
    'Shift': 'shift_as',
    'Shift_std': 'shift_std_as',
    'Linewidth': 'width_as',
    'Linewidth_std': 'width_std_as',
    'Amplitude': 'amplitude_as',
    'Amplitude_std': 'amplitude_std_as',
    'BLT': 'blt_as',
    'BLT_std': 'blt_std_as',
}
# TODO: AS vs S nuance not captured with Pierre's yet! hardcoding everything to AS above but Carlo's will pass both
# TODO: Pierre's BLT and _std values not captured. Carlo's Offset, R2, RMSE, Cov_matrix are leaked (and AS vs S)

class HDF5Flattener:
    """
    class that wraps the flatten() function to prepare brimX files for conversion to brimfile :)
        __________
        Returns:
            a dictionary of brim-ready arrays containing the Brillouin data, invoked by .flatten() in driver
        TODO: currently leaks Impulse response and Calibration data sets
    """
    def __init__(self):
        self.acq_path_to_index = {}
        self.acq_path_to_metadata_index = {}
        self.flat_shape = {}
        self.data_index = 0
        self.data_metadata_index = 0

        self.frequency = {}
        self.PSD = {}
        self.x = {}
        self.y = {}
        self.z = {}
        self.dx = {}
        self.dy = {}
        self.dz = {}
        self.shift_as = {}
        self.shift_std_as = {}
        self.width_as = {}
        self.width_std_as = {}
        self.amplitude_as = {}
        self.amplitude_std_as = {}
        self.blt_as = {}
        self.blt_std_as = {}

        self.metadata = {}
        self.dataset_queue = []  # store all datasets for ordered processing

        # Store paths of groups that are of Brillouin_type == "Measure"
        self.measure_paths = set()

    def collect_measure_groups(self, name, obj):
        """Pre-scan to find all group paths that are 'Measure' acquisition groups"""
        if isinstance(obj, h5py.Group):
            #rint(f"\nVisited group: {name}")
            #for attr_key in obj.attrs:
                #if not attr_key.startswith("Process"):
                    #print(f"  ↳ Attribute: {attr_key} = {obj.attrs[attr_key]}")      

            attr_type = obj.attrs.get("Brillouin_type", None)
            if attr_type == "Measure": # should I make one for Impulse_response and Calibration_spectrum as well?
                self.measure_paths.add(name)
                #print(f"Found 'Measure' group: {name}")  # highlight matched groups

    def collect_metadata(self, name, obj):
        base_acq = self.get_base_acquisition_path(name)
        if base_acq is None:
            return
        
        # Get or assign index
        if base_acq not in self.acq_path_to_metadata_index:
            self.acq_path_to_metadata_index[base_acq] = self.data_metadata_index
            self.data_metadata_index += 1

        jdx = self.acq_path_to_metadata_index[base_acq]

        # Initialize dictionary for this idx
        if jdx not in self.metadata:
            self.metadata[jdx] = {}

        # Filter and collect metadata
        for attr_key in obj.attrs:
            if attr_key.startswith(("FILEPROP", "MEASURE", "SPECTROMETER")): # Pierre's end
                self.metadata[jdx][attr_key] = obj.attrs[attr_key] 

    def get_base_acquisition_path(self, name):
        """Returns acquisition path if it is a child of a 'Measure' group"""
        parts = name.split('/')
        for i in range(len(parts), 0, -1):
            candidate = '/'.join(parts[:i])
            if candidate in self.measure_paths:
                return candidate
        return None   

    def copy_dataset(self, name, obj):
        """
        visit directories that have been identified as containing Brillouin datasets, then based on 
        what is found, scrape the data, reshape it if necessary (e.g. PSD), then store locally for
        output in flatten() and then the pass to brimfile in brim_converter.py
        """
        if not isinstance(obj, h5py.Dataset):
            return     

        # identify path to high level base paths that containing low level Brillouin datasets
        base_acq = self.get_base_acquisition_path(name)
        if base_acq is None:
            return

        if base_acq not in self.acq_path_to_index:
            self.acq_path_to_index[base_acq] = self.data_index
            self.flat_shape = {}
            self.data_index += 1

        idx = self.acq_path_to_index[base_acq]

        # The key-word on Pierre's end is datasets with Brillouin_type attributes
        bt = obj.attrs.get("Brillouin_type")

        # prepare for possibility that PSD could be representative of 1D-to-4D Brillouin data
        if bt == "PSD" and not self.flat_shape:
            if len(obj.shape) == 1:
                self.flat_shape = 1
                #xdim, ydim, zdim = 1, 1, 1 # pierre
                zdim, ydim, xdim = 1, 1, 1 # carlo
            elif len(obj.shape) == 2:
                self.flat_shape = obj.shape[0]
                #xdim, ydim, zdim = obj.shape[0], 1, 1 # pierre
                zdim, ydim, xdim = 1, 1, obj.shape[0] # carlo
            elif len(obj.shape) == 3:
                self.flat_shape = obj.shape[0] * obj.shape[1]
                #xdim, ydim, zdim = obj.shape[0], obj.shape[1], 1 # pierre
                zdim, ydim, xdim = 1, obj.shape[0], obj.shape[1] # carlo
            elif len(obj.shape) == 4:
                self.flat_shape = obj.shape[0] * obj.shape[1] * obj.shape[2]
                #xdim, ydim, zdim = obj.shape[0], obj.shape[1], obj.shape[2] # pierre
                zdim, ydim, xdim = obj.shape[0], obj.shape[1], obj.shape[2] # carlo

        # if a dataset is found, store it locally for future pass to brim
        if bt == "Frequency":
            self.frequency[idx] = obj[()]
        elif bt == "PSD":
            self.PSD[idx] = np.reshape(obj, (zdim, ydim, xdim, obj.shape[-1])) # this needs to be as is
        #elif obj.attrs["Brillouin_data"] == "Raw_data": # should I just pass this through un-reshaped?
         #   self.Raw_data[idx] = np.reshape(obj, (d)) # TODO: raw data?
        elif bt == "Abscissa_0_1": # TODO: correctly scrape this from brim
            self.x[idx] = obj[()] # what about for 2D case?
        elif bt == "Abscissa_1_2":
            self.y[idx] = obj[()]
        elif bt == "Abscissa_2_3":
            self.z[idx] = obj[()]
        elif bt in TREATMENT_LEVEL: # making sure to add dummy dimensions correctly as/if needed
            self_tmp = getattr(self, BT_TO_ATTR[bt])
            if len(obj.shape) == 1: # 1D input dataset
                self_tmp[idx] = (obj[()])[None, None, ...]
            elif len(obj.shape) == 2: # 2D input dataset
                self_tmp[idx] = (obj[()])[None, ...]
            elif len(obj.shape) == 3: # 3D input dataset
                self_tmp[idx] = obj[()]
            else:
                raise ValueError(f"{bt} of shape {obj.shape} is not supported")            
        
    # sees the outside world
    def flatten(self, src_path):
        """
        __________
        Input: 
            brimX input file name/path
        Returns:
            a dictionary containing the reshaped Brillouin data that brim_converter unpackages and passes to brim        
        """

        # heavy lifting
        with h5py.File(src_path, 'r') as f_src:
            f_src.visititems(self.collect_measure_groups)  # find Measure groups
            f_src.visititems(self.collect_metadata)    # collect metadata
            f_src.visititems(self.copy_dataset) # do heavy lifting for extracting/reshaping

        # final checks for PSD existence and shape checks
        if not self.PSD:
            raise Exception(f"No PSD Brillouin_type attribute found in {src_path}. PSD is required to convert to brimfile.") 
        for k in self.PSD:
            if k in self.shift_as:
                if self.PSD[k].shape[:len(self.PSD[k].shape)-1] != self.shift_as[k].shape[:len(self.shift_as[k].shape)]:
                    raise ValueError(f"Shape mismatch for index {k}: the non-spectral dimensions of PSD {self.PSD[k].shape[:len(self.PSD[k].shape)-1]} do not match the dimensions of your shift! {self.shift_as[k].shape[:len(self.shift_as[k].shape)]}")
        
        # safely deactivate dx, dy, or dz if they don't exist, because they're still needed in brimfile
        for j in range(self.data_index):
            self.dx[j] = np.mean(np.diff(self.x[j])) if self.x else 1 # needs to be None instead?
            self.dy[j] = np.mean(np.diff(self.y[j])) if self.y else 1
            self.dz[j] = np.mean(np.diff(self.z[j])) if self.z else 1

        return {
            "frequency": self.frequency,
            "PSD": self.PSD,
            "z": self.z,
            "y": self.y,
            "x": self.x,
            "dz": self.dz,
            "dy": self.dy,
            "dx": self.dx,
            "shift_as": self.shift_as,
            "shift_std_as": self.shift_std_as,
            "width_as": self.width_as,
            "width_std_as": self.width_std_as,
            "amplitude_as": self.amplitude_as,
            "amplitude_std_as": self.amplitude_std_as,
            "blt_as": self.blt_as, # prob needs as vs _s as well, same with _std below
            "blt_std_as": self.blt_std_as,
            "metadata": self.metadata
            # TODO: AS vs S not captured correctly!
        }
