from ..config import VersionConfig, GroupType, DatasetType, Attribute

ATTRIBUTES_1_0 = [
        # MEASURE group
        Attribute("MEASURE", "Sample", example="Water"),
        Attribute("MEASURE", "Date_of_measure", description="ISO 8601", example="2024-11-18T14:17:55.294821"),
        Attribute("MEASURE", "Exposure_(s)", units="s", example=0.1),
        
        # SPECTROMETER group
        Attribute(
            "SPECTROMETER", "Type", 
            example="Tandem Fabry-Perot",
            recommended_values=["1 stage VIPA", "2 stage VIPA", "Angle-resolved VIPA", "TFP", "TR-TFP", "TR-1VIPA"]
        ),
        Attribute("SPECTROMETER", "Model", description="Manufacturer-Model", example="JRS-TFP2"),
        Attribute("SPECTROMETER", "Wavelength_(nm)", units="nm", example=532),
        Attribute("SPECTROMETER", "Confocal_Pinhole_Diameter_(AU)", units="AU", example=1),
        Attribute("SPECTROMETER", "Detection_Lens_NA", example=0.45),
        Attribute("SPECTROMETER", "Detector_Model", description="Manufacturer-Model", example="Hamamatsu-Orca C11440"),
        Attribute("SPECTROMETER", "Detector_Type", example="CMOS"),
        Attribute("SPECTROMETER", "Filtering_Type", example="Gas cell"),
        Attribute("SPECTROMETER", "Filtering_Module", description="Manufacturer-Model", example="Thorlabs-GC19100-I"),
        Attribute("SPECTROMETER", "Illumination_Lens_NA", description="Taking into account beam size before lens or objective", example=0.2),
        Attribute("SPECTROMETER", "Illumination_Power_(mW)", units="mW", description="Measured at the sample", example=15),
        Attribute("SPECTROMETER", "Illumination_Type", example="CW Laser", recommended_values=["CW Laser", "Pulsed Laser"]),
        Attribute("SPECTROMETER", "Laser_Model", description="Manufacturer-Model", example="Cobolt-Samba"),
        Attribute("SPECTROMETER", "Laser_Drift_(MHz/h)", units="MHz/h", description="Measured independently of spectrometer drifts", example=700),
        Attribute("SPECTROMETER", "Phonons_Measured", description="Longitudinal, Transverse or both", example="Longitudinal & Transverse", recommended_values=["Longitudinal", "Transverse", "Longitudinal & Transverse"]),
        Attribute("SPECTROMETER", "Polarization_probed-analyzed", description="Probed-Analyzed", example="Vertical-Horizontal", recommended_values=["Vertical-Horizontal", "Horizontal-Vertical", "Vertical-Vertical", "Horizontal-Horizontal"]),
        Attribute("SPECTROMETER", "Scan_Amplitude_(GHz)", units="GHz", description="Only for scanning spectrometers", example=20),
        Attribute("SPECTROMETER", "Scanning_Strategy", example="Raster scan", recommended_values=["Raster scan", "Line scan", "Point scan"]),
        Attribute("SPECTROMETER", "Scattering_Angle_(deg)", units="degrees", description="The angle between the illumination and the detection", example=180),
        Attribute("SPECTROMETER", "Spectral_Resolution_(MHz)", units="MHz", description="Largest measured value", example=150),
        Attribute("SPECTROMETER", "VIPA_FSR_(GHz)", units="GHz", description="The Free Spectral Range of the VIPA used in 1-VIPA spectrometers", example=30),
        Attribute("SPECTROMETER", "x-Mechanical_Resolution_(um)", units="um", description="Estimated (phonon lifetime)", example=0.5),
        Attribute("SPECTROMETER", "x-Optical_Resolution_(um)", units="um", description="Measured", example=5),
        Attribute("SPECTROMETER", "y-Mechanical_Resolution_(um)", units="um", description="Estimated (phonon lifetime)", example=0.5),
        Attribute("SPECTROMETER", "y-Optical_Resolution_(um)", units="um", description="Measured", example=5),
        Attribute("SPECTROMETER", "z-Mechanical_Resolution_(um)", units="um", description="Estimated (phonon lifetime)", example=0.5),
        Attribute("SPECTROMETER", "z-Optical_Resolution_(um)", units="um", description="Measured", example=50),
        
        # FILEPROP group
        Attribute("FILEPROP", "BLS_HDF5_Version", description="Version of the spreadsheet - Don't change", example="0.1"),
        Attribute("FILEPROP", "Filepath", description="Global name of the h5 file", example=r"\Users\library\documents\BLS.h5"),
        Attribute("FILEPROP", "Name", example="Water spectrum"),
    ]


VERSION_1_0 = VersionConfig(
    version="1.0",
    default_group_type="Root",
    default_dataset_type="Other",
    groups={
        "Root": GroupType(
            name="Root",
            description="Hierarchy-oriented group type used to organize the overall file.",
            allowed_child_groups=["Measure", "Calibration_spectrum", "Impulse_response", "Root", "Treatment"]
        ),
        "Measure": GroupType(
            name="Measure",
            description="The main group storing the datasets resulting from an acquisition and the results derived from them.",
            allowed_child_groups=["Treatment"]
        ),
        "Calibration_spectrum": GroupType(
            name="Calibration_spectrum",
            description="Calibration spectra acquired to characterize spectrometer dispersion and instrument response.",
            allowed_child_groups=["Treatment"]
        ),
        "Impulse_response": GroupType(
            name="Impulse_response",
            description="Instrument impulse response function (IRF) measurements.",
            allowed_child_groups=["Treatment"]
        ),
        "Treatment": GroupType(
            name="Treatment",
            description="Processed results, peak-fitting outputs (shift, linewidth), and derived physical parameters.",
            allowed_child_groups=["Treatment"]
        ),
    },
    datasets={
        "Raw_data": DatasetType(
            name="Raw_data",
            description="Any signal collected that contains information from which the Brillouin scattered light power spectrum can be derived.",
            allowed_parent_groups=["Measure", "Calibration_spectrum", "Impulse_response"]
        ),
        "PSD": DatasetType(
            name="PSD",
            description="Power spectrum of the detected signal.",
            allowed_parent_groups=["Measure", "Calibration_spectrum", "Impulse_response"],
            default_unit="AU"
        ),
        "Frequency": DatasetType(
            name="Frequency",
            description="Spectral frequency axis corresponding to the PSD.",
            allowed_parent_groups=["Measure", "Calibration_spectrum", "Impulse_response"],
            default_unit="GHz",
        ),
        "Abscissa": DatasetType(
            name="Abscissa",
            description="Coordinate axis for scans.",
            allowed_parent_groups=["Measure"]
        ),
        "Shift": DatasetType(
            name="Shift",
            description="Extracted Brillouin frequency shift peak position.",
            allowed_parent_groups=["Treatment"],
            default_unit="GHz"
        ),
        "Shift_err": DatasetType(
            name="Shift_err",
            description="Uncertainty / standard error of the extracted Brillouin frequency shift.",
            allowed_parent_groups=["Treatment"],
            default_unit="GHz"
        ),
        "Linewidth": DatasetType(
            name="Linewidth",
            description="Extracted Brillouin peak Full Width at Half Maximum (FWHM).",
            allowed_parent_groups=["Treatment"],
            default_unit="GHz"
        ),
        "Linewidth_err": DatasetType(
            name="Linewidth_err",
            description="Uncertainty / standard error of the extracted Brillouin linewidth.",
            allowed_parent_groups=["Treatment"],
            default_unit="GHz"
        ),
        "Amplitude": DatasetType(
            name="Amplitude",
            description="Extracted Brillouin peak amplitude.",
            allowed_parent_groups=["Treatment"],
            default_unit="AU"
        ),
        "Amplitude_err": DatasetType(
            name="Amplitude_err",
            description="Uncertainty of the extracted peak amplitude.",
            allowed_parent_groups=["Treatment"],
            default_unit="AU"
        ),
        "BLT": DatasetType(
            name="BLT",
            description="Brillouin Loss Tangent (ratio of linewidth to frequency shift).",
            allowed_parent_groups=["Treatment"],
            default_unit="AU"
        ),
        "BLT_err": DatasetType(
            name="BLT_err",
            description="Uncertainty of the Brillouin Loss Tangent.",
            allowed_parent_groups=["Treatment"],
            default_unit="AU"
        ),
        "Other": DatasetType(
            name="Other",
            description="Supplementary datasets (e.g., other modalities, fit statistics, chi-square, baseline offset, slope, etc.)",
            allowed_parent_groups=["Measure", "Treatment", "Root", "Calibration_spectrum", "Impulse_response"]
        ),
    },
    type_renames={
        "Shift_std": "Shift_err",
        "Linewidth_std": "Linewidth_err",
        "Amplitude_std": "Amplitude_err",
        "BLT_std": "BLT_err",
    },
    attributes={attr.full_name: attr for attr in ATTRIBUTES_1_0},
)
