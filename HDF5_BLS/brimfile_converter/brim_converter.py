from brimfile import File, StoreType, Data
import numpy as np
import h5py

LABELS = ['Shift', 'Width', 'Amplitude', 'Offset', 'R2', 'RMSE', 'Cov_matrix'] # list all Carlo's dataset types
BRILLOUIN_TYPE_MAPPING = { # mapping initial collection of dataset names from Carlo: Pierre,
    'Shift': 'Shift',
    'Width': 'Linewidth',
    'Amplitude': 'Amplitude',
    # TODO: Pierre's BLT and _std values not captured.
}

class BrimConverter:
    """ 
    As described on the tin. Converts between brim file format (and nominally brimX).
    """
    def __init__(self, path_from: str, path_to: str, mode: str = 'brim2brimX', stop_at: int = None, map_to: str ='cartesian'):
        """Initializes the conveter

        Parameters
        ----------
        filename_from : str
            The path to the initial file. 
        filename_to : str
            The path to the created file
        mode : str, optional
            The mode of conversion. Modes can be either "brim2brimX" or "brimX2brim", by default 'brim2brimX'
        stop_at : int, optional
            For big files, option to only convert part of the dataset, more for testing/debugging, by default None
        map_to : str, optional
            For brim to brimX, allows brimX to be stored in cartesian shapes or flat, by default 'cartesian'

        Raises
        ------
        ValueError
            If the mode is not "brim2brimX" or "brimX2brim"
        """
        if mode not in ['brim2brimX', 'brimX2brim']:
            raise ValueError(f"Unsupported mode: {mode}. Use 'brim2brimX' or 'brimX2brim'.")

        self.filename_from = path_from # strings
        self.filename_to = path_to
        self.mode = mode # conversion type
        self.stop_at = stop_at # for big files, option to only convert part of the dataset, more for testing/debugging
        self.map_to = map_to # for brim to brimX, allows brimX to be stored in cartesian shapes or flat

    def convert(self):
        # toggle between the two conversion modes
        if self.mode == 'brim2brimX':
            self.f_from = File(self.filename_from)
            self._convert_brim_to_brimX()
        elif self.mode == 'brimX2brim':
            self.f_from = h5py.File(self.filename_from, 'r')
            self._convert_brimX_to_brim()

        self.f_from.close()
        self.f_to.close()

    def _convert_brim_to_brimX(self):
        print('Converting from brim to brimX...') # could pass file names and extensions as well...
        self.data_groups = self.f_from.list_data_groups(retrieve_custom_name=True)
        if self.stop_at:
            num_iters = self.stop_at
        else:
            num_iters = len(self.data_groups)
        for idx in range(num_iters): 
            self._process_data_group_brim2brimX(idx)

    def _convert_brimX_to_brim(self):
        print('Converting from brimX to brim...') # could pass file names and extensions as well...
        self._process_data_group_brimX2brim()

    def _process_data_group_brim2brimX(self, index):
        """ 
        Function to do the heavy lifting for loading a brim file (arbitrary file extension), 
        extracting the relevant quantities, reformatting, and then passing back through brim with
        HDF5 file extension as output. HDF5 could be hardcoded but is currently still input by user
        in driver script (*.brim.h5). 
        __________
        Input: 
            self and the index of the current data group (e.g. an experimental dataset with 
            8 Brillouin scans will have 8 data groups to iterate through).
        Returns:
            nothing, it saves the new file to the filepath specified by the user on input
        Note:
            if a brim Data group contains multiple Analysis_m sub-groups, currently this won't be dealt with properly
            should be relatively easy to deal with if needed though
        """

        # use brimfile library to load dataset
        d = self.f_from.get_data(index) # just for one datagroup (same with ar and md below)
        ar = d.get_analysis_results()
        md = d.get_metadata()
        all_metadata = md.all_to_dict() # TODO: not used yet

        # scrape spatial information and store locally
        cv, px_size = d._load_spatial_mapping() # extract z, y, x pixel sizes
        dz, dy, dx = px_size[0].value, px_size[1].value, px_size[2].value # store them
        Nz, Ny, Nx = cv.shape # store data shape for z, y, x
        z, y, x = np.arange(Nz)*dz, np.arange(Ny)*dy, np.arange(Nx)*dx # TODO: SAL, FOR WRITING TO ABSCISSA IN FUTURE

        # collect PSD and reshape depending on state of map_to
        # is get_PSD() going to be stable longterm?
        PSD, freq, PSD_units, freq_units = d.get_PSD()
        PSD_save = PSD if self.map_to == 'flat' else np.reshape(PSD, (Nz, Ny, Nx, -1))

        # create/append the brimX file and populate the correct datasets
        self.f_to = h5py.File(self.filename_to, 'a')
        group = self.f_to.require_group(f"/Brillouin/Data_{index}")
        group.attrs["Brillouin_type"] = "Measure"
        dg = group.create_dataset("PSD", data=PSD_save)
        dg.attrs["Brillouin_type"] = "PSD"
        dg = group.create_dataset("Frequency", data=freq)
        dg.attrs["Brillouin_type"] = "Frequency"

        # Now going to extract name, value pairs from _get_quantity. Try everything and walk away 
        # with whatever's there in two dictionaries, one for AS and one for S
        treatment_group = None
        for name in LABELS:
            for peak_type in ['AntiStokes', 'Stokes']:
                try:
                    dataset_name = f"{name}_{'S' if peak_type == 'Stokes' else 'AS'}"
                    quantity_now = getattr(Data.AnalysisResults.Quantity, name)
                    peak_type_now = getattr(Data.AnalysisResults.PeakType, peak_type)                  
                    data, _ = ar.get_image(quantity_now, peak_type_now)
                    data = data if not self.map_to == 'flat' else data.flatten() 
                    if treatment_group is None:
                        treatment_group = group.require_group("Treatment")
                        treatment_group.attrs["Brillouin_type"] = "Treatment"
                    ds = treatment_group.create_dataset(dataset_name, data=data)
                    if name in BRILLOUIN_TYPE_MAPPING:
                        ds.attrs["Brillouin_type"] = BRILLOUIN_TYPE_MAPPING[name]
                    else:
                        ds.attrs["Brillouin_type"] = "Other"

                    # Sal, leaving out units for now, should append to brillouin_type as _(unit) instead?
                    #units = ar.get_units(quantity)
                    #ds.attrs["units"] = units
                except Exception as e:
                    print(f"Exception for {dataset_name} ({peak_type}): {e}")

                # Sal, previous way of parsing units that was more consistent with brim way, yet will clutter brimx file
                """try:
                    datasets_S[f"{name.lower()}_units"] = ar.get_units(quantity_S)
                    treatment_group.create_dataset(f"/Brillouin/Data_{index}/Treatment/{name}_S_units", data=datasets_S[f"{name.lower()}_units"])  
                    print(datasets_S[f"{name.lower()}_units"])
                except Exception:
                    pass"""

        # TODO: Sal, properly deal with metadata!

    def _process_data_group_brimX2brim(self):
        """ 
        Function to do the heavy lifting for loading a brimX file (h5 from HDF5_BLS), scraping the
        relevant quantities from the brimX format (HDF5Flattener class), reshaping as necessary, 
        and then passing to brim with a file extension dictated by the user input (zarr, zip).
        __________
        Input: 
            self (nominally the input file name/path)
        Returns:
            nothing, it saves the new file to the filepath specified by the user on input
        """        
        from .hdf5_flattener import HDF5Flattener 
        flattener = HDF5Flattener()
        
        # load file_from and enforce flattened dataset shapes for the brimfile pass, then create new brim file
        data_from_brimX = flattener.flatten(self.filename_from) 
        self.f_to = File.create(self.filename_to, store_type=StoreType.AUTO)

        # assignments to local variables + hardcode as only AS curently, future: potentially add extra dimension if _S exists
        print(data_from_brimX)
        for i in range(len(data_from_brimX["PSD"])):
            PSD = data_from_brimX["PSD"][i]
            freq = data_from_brimX["frequency"][i]
            shift = data_from_brimX.get("shift_as", {}).get(i)
            width = data_from_brimX.get("width_as", {}).get(i)
            amplitude = data_from_brimX.get("amplitude_as", {}).get(i)
            dz = data_from_brimX.get("dz", {}).get(i, 1)
            dy = data_from_brimX.get("dy", {}).get(i, 1)
            dx = data_from_brimX.get("dx", {}).get(i, 1)

            # create data group in brim file, populate with PSD, freq, and spatial info
            d = self.f_to.create_data_group(PSD, freq, (dz, dy, dx), name=f"Group_{i}")

            analysis_dict = {}

            if shift is not None:
                analysis_dict["shift"] = shift
                analysis_dict["shift_units"] = "GHz"  # TODO: scrape units from input brimx file
            if width is not None:
                analysis_dict["width"] = width
                analysis_dict["width_units"] = "GHz"  # TODO: scrape units from input brimx file
            if amplitude is not None:
                analysis_dict["amplitude"] = amplitude

            # Then create Analysis sub-group with shift, linewidth, etc
            if analysis_dict:
                d.create_analysis_results_group((analysis_dict,), name=f"Group_{i}_analysis")

            # TODO: port metadata_all[i] into .create_metadata_group or similar

    # TODO: below
    def _write_metadata(self, data_group, metadata_dict):
        pass
