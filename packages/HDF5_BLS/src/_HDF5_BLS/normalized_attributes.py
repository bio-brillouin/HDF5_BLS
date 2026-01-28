from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import pandas as pd
import os

@dataclass
class Attribute:
    """
    Metadata for a standardized HDF5 attribute.
    """
    group: str
    name: str
    units: Optional[str] = None
    description: Optional[str] = None
    example: Any = None
    recommended_values: List[Any] = field(default_factory=list)

    @property
    def full_name(self) -> str:
        return f"{self.group}.{self.name}"

class NormalizedAttributes:
    """
    Centralized list of normalized attributes for HDF5_BLS.
    """
    
    ATTRIBUTES = [
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

    @classmethod
    def get_all(cls) -> List[Attribute]:
        """Returns the list of all normalized attributes."""
        return cls.ATTRIBUTES

    @classmethod
    def get_groups(cls) -> List[str]:
        """Returns the list of all standardized groups."""
        return sorted(list(set(attr.group for attr in cls.ATTRIBUTES)))

    @classmethod
    def get_attributes_by_group(cls, group: str) -> List[Attribute]:
        """Returns the list of attributes belonging to a specific group."""
        return [attr for attr in cls.ATTRIBUTES if attr.group == group]

    @classmethod
    def to_pandas(cls) -> pd.DataFrame:
        """
        Returns a pandas DataFrame representation of the normalized attributes.
        """
        data = []
        current_group = None
        for attr in cls.ATTRIBUTES:
            if attr.group != current_group:
                data.append({
                    "Attribute": attr.group,
                    "Value": None,
                    "Units": None,
                    "Norm or precisions on parameter": None,
                    "Example": None,
                    "Recommended Values": None
                })
                current_group = attr.group
            
            data.append({
                "Attribute": attr.full_name,
                "Value": None,
                "Units": attr.units,
                "Norm or precisions on parameter": attr.description,
                "Example": attr.example,
                "Recommended Values": ", ".join(map(str, attr.recommended_values)) if attr.recommended_values else None
            })
            
        return pd.DataFrame(data)

    @classmethod
    def to_excel(cls, path: str):
        """Generates an Excel spreadsheet of the normalized attributes with dropdowns."""
        from openpyxl.worksheet.datavalidation import DataValidation
        from openpyxl.utils import get_column_letter

        df = cls.to_pandas()
        
        with pd.ExcelWriter(path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Attributes')
            workbook = writer.book
            worksheet = writer.sheets['Attributes']

            # Find columns
            attribute_col = 1 # A
            value_col = 2     # B
            
            # Add data validation for attributes with recommended values
            # Rows are 2-indexed (1 is header)
            row_idx = 2
            current_group = None
            for attr in cls.ATTRIBUTES:
                if attr.group != current_group:
                    row_idx += 1 # Skip group header row
                    current_group = attr.group
                
                if attr.recommended_values:
                    dv = DataValidation(
                        type="list", 
                        formula1=f'"{",".join(map(str, attr.recommended_values))}"',
                        allow_blank=True
                    )
                    dv.add(f"{get_column_letter(value_col)}{row_idx}")
                    worksheet.add_data_validation(dv)
                
                row_idx += 1

    @classmethod
    def to_csv(cls, path: str):
        """Generates a CSV file of the normalized attributes."""
        df = cls.to_pandas()
        df.to_csv(path, index=False)

if __name__ == "__main__":
    NormalizedAttributes.to_excel("/Users/pierrebouvet/Desktop/normalized_attributes.xlsx")