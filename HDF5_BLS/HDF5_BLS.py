import h5py
import numpy as np
import csv
import os
from PIL import Image

BLS_HDF5_Version = "0.1"

class HDF5_BLS:
    def __init__(self):
        self.filepath = None
        self.attributes = {}
        self.abscissa = None
        self.raw_data = None
        self.calibration_curve = None
        self.impulse_response = None
        self.loader = Load_Data()

    def define_abscissa(self, min_val, max_val, nb_samples):
        """Defines a new abscissa axis based on min, max values, and number of samples."""
        self.abscissa = np.linspace(min_val, max_val, nb_samples)
        return self.abscissa

    def export_properties_data(self, filepath_csv):
        """Exports properties to a CSV file."""
        with open(filepath_csv, mode='w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            for key, value in self.attributes.items():
                csv_writer.writerow([key, value])
        return filepath_csv

    def import_abscissa(self, filepath):
        """Imports abscissa points from a file and returns the associated array."""
        self.abscissa = np.loadtxt(filepath)
        return self.abscissa

    def import_properties_data(self, filepath_csv):
        """Imports properties from a CSV file into a dictionary."""
        with open(filepath_csv, mode='r') as csv_file:
            csv_reader = csv.reader(csv_file)
            for row in csv_reader:
                key, value = row
                self.attributes[key] = value
        return self.attributes

    def open_calibration(self, filepath):
        """Opens a calibration curve file and returns the calibration curve."""
        self.calibration_curve = np.loadtxt(filepath)
        return self.calibration_curve

    def open_hdf5_files(self, filepath):
        self.attributes = {}

        with h5py.File(filepath, 'r') as hdf5_file:
            print(hdf5_file.items())

            self.data = hdf5_file["Raw_Data"][:]
            
            for key in hdf5_file.attrs.keys():
                self.attributes[key] = hdf5_file.attrs[key]
            
        return self.data, self.attributes

    def open_data(self, filepath):
        """Opens a raw data file based on its file extension and stores the filepath."""
        self.filepath = filepath
        _, file_extension = os.path.splitext(filepath)
        
        
        if file_extension.lower() == ".dat":
            # Load .DAT file format data
            self.raw_data, self.attributes = self.loader.load_dat_file(filepath)
        elif file_extension.lower() == ".tif":
            # Load .TIFF file format data
            self.raw_data, self.attributes = self.loader.load_tiff_file(filepath)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
        
        return self.filepath

    def open_IR(self, filepath):
        """Opens an impulse response file and returns the curve."""
        self.impulse_response = np.loadtxt(filepath)
        return self.impulse_response

    def properties_data(self, **kwargs):
        """Creates a dictionary with the given properties."""
        self.attributes = kwargs
        return self.attributes

    def save_hdf5_as(self, save_filepath):
        """Saves the data and attributes to an HDF5 file."""
        with h5py.File(save_filepath, 'w') as hdf5_file:
            # Save attributes
            for key, value in self.attributes.items():
                hdf5_file.attrs[key] = value
            
            # Save datasets if they exist
            if self.raw_data is not None:
                hdf5_file.create_dataset('Raw_Data', data=self.raw_data)
                print("added Raw data")
            if self.abscissa is not None:
                hdf5_file.create_dataset('Abscissa', data=self.abscissa)
            if self.calibration_curve is not None:
                hdf5_file.create_dataset('Calibration_Curve', data=self.calibration_curve)
            if self.impulse_response is not None:
                hdf5_file.create_dataset('Impulse_Response', data=self.impulse_response)

class Load_Data():
    def __init__(self):
        pass

    def load_dat_file(self, filepath):
        metadata = {}
        data = []
        name, _ = os.path.splitext(filepath)
        attributes = {}
        
        with open(filepath, 'r') as file:
            lines = file.readlines()
            # Extract metadata
            for line in lines:
                if line.strip() == '':
                    continue  # Skip empty lines
                if any(char.isdigit() for char in line.split()[0]):
                    break  # Stop at the first number
                else:
                    # Split metadata into key-value pairs
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip()
            # Extract numerical data
            for line in lines:
                if line.strip().isdigit():
                    data.append(int(line.strip()))
        data = np.array(data)
        attributes['FILEPROP.BLS_HDF5_Version'] = BLS_HDF5_Version
        attributes['FILEPROP.Name'] = name
        attributes['MEASURE.Sample'] = metadata["Sample"]
        attributes['SPECTROMETER.Scanning_Strategy'] = "point_scanning"
        attributes['SPECTROMETER.Type'] = "TFP"
        attributes['SPECTROMETER.Illumination_Type'] = "CW"
        attributes['SPECTROMETER.Detector_Type'] = "Photon Counter"
        attributes['SPECTROMETER.Filtering_Module'] = "None"
        attributes['SPECTROMETER.Wavelength_nm'] = metadata["Wavelength"]
        attributes['SPECTROMETER.Scan_Amplitude'] = metadata["Scan amplitude"]
        spectral_resolution = float(float(metadata["Scan amplitude"])/data.shape[-1])
        attributes['SPECTROMETER.Spectral_Resolution'] = str(spectral_resolution)
        return data, attributes

    def load_tiff_file(self,filepath):
        data = []
        name, _ = os.path.splitext(filepath)
        attributes = {}

        im = Image.open(filepath)
        data = np.array(im)

        attributes['FILEPROP.BLS_HDF5_Version'] = BLS_HDF5_Version
        attributes['FILEPROP.Name'] = name

        return data, attributes
