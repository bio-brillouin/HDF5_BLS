from ..config import VersionConfig, GroupType, DatasetType

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
    }
)
