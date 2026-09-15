.. _programmatic_attributes:

The ``HDF5_BLS`` package provides a centralized way to manage standardized metadata through the ``NormalizedAttributes`` class. This ensures that the attributes added to your HDF5 files follow the BioBrillouin community guidelines.

Using NormalizedAttributes
^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``NormalizedAttributes`` class allows you to retrieve standardized groups and attribute names. This is particularly useful when you want to ensure that your scripts use the correct nomenclature.

.. code-block:: python

    from HDF5_BLS import NormalizedAttributes

    # Get all available groups
    groups = NormalizedAttributes.get_groups()
    # Returns: ['FILEPROP', 'MEASURE', 'SPECTROMETER']

    # Get all attributes for a specific group
    attrs = NormalizedAttributes.get_attributes_by_group("SPECTROMETER")
    
    for attr in attrs:
        print(f"Name: {attr.full_name}")
        print(f"Description: {attr.description}")
        print(f"Recommended values: {attr.recommended_values}")

Adding Attributes to a Wrapper
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once you have identified the standardized name and value you want to use, you can add it to your HDF5 file using the ``add_attributes`` method of the ``Wrapper`` object.

.. code-block:: python

    from HDF5_BLS import Wrapper, NormalizedAttributes

    wrp = Wrapper("experiment_data.h5")

    # Define the attributes to add
    # We use the full_name property to ensure the correct prefix (e.g., 'SPECTROMETER.Type')
    new_attributes = {
        "SPECTROMETER.Type": "TFP",
        "MEASURE.Sample": "Cornea",
        "MEASURE.Temperature_(C)": 37
    }

    # Add attributes to a specific group in the HDF5 file
    wrp.add_attributes(attributes=new_attributes, parent_group="Brillouin/Measure")

Validation and Recommended Values
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Many standardized attributes come with recommended values. While the library does not strictly enforce these values in all cases, using them ensures maximum compatibility with other tools in the ecosystem.

.. code-block:: python

    # Find recommended values for the spectrometer type
    spec_type_attr = next(a for a in NormalizedAttributes.get_all() if a.full_name == "SPECTROMETER.Type")
    print(spec_type_attr.recommended_values)
    # Returns: ['1 stage VIPA', '2 stage VIPA', 'Angle-resolved VIPA', 'TFP', 'TR-TFP', 'TR-1VIPA']

Exporting the Nomenclature
^^^^^^^^^^^^^^^^^^^^^^^^^^

If you need to share the list of allowed attributes or prepare them in a spreadsheet, you can use the export methods:

.. code-block:: python

    # Export to Excel (includes dropdown validation for recommended values)
    NormalizedAttributes.to_excel("biobrillouin_nomenclature.xlsx")

    # Export to CSV
    NormalizedAttributes.to_csv("biobrillouin_nomenclature.csv")

Bulk Import of Attributes
^^^^^^^^^^^^^^^^^^^^^^^^^

A powerful feature for streamlining metadata entry is the bulk import of attributes from Excel or CSV files. This is particularly useful for experiments that share a similar setup (e.g., same spectrometer) with only minor changes to the sample or measurement parameters (e.g. sample, exposure time, objective).

1.  **Export Your Configuration**: Start by exporting the attributes of a reference experiment to an Excel file using the GUI (**Tools** > **Export Normalized Attributes**) or the API (``NormalizedAttributes.to_excel()``).
2.  **Edit the File**: Open the file and update any non-standard values or specific parameters for your new experiment.
3.  **Import to New File**: Use the ``import_properties_data`` method to fill the attributes of your new HDF5 file.

.. code-block:: python

    from HDF5_BLS import Wrapper

    wrp = Wrapper("new_experiment.h5")

    # Import attributes from the prepared Excel file
    # This will populate common fields like SPECTROMETER settings automatically
    wrp.import_properties_data(
        filepath="common_setup.xlsx",
        path="Brillouin/Measure",
        overwrite=True
    )

.. tip::
    Using bulk import minimizes manual entry errors, encourages the tagging of every experiment and essentially makes your data FAIR.
