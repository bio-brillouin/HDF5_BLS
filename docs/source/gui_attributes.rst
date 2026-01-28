.. _gui_attributes:

Managing Attributes with the GUI
================================

The HDF5_BLS GUI provides built-in tools to easily manage standardized attributes within your HDF5 files, ensuring they remain compliant with the BioBrillouin normalization rules.

Adding Attributes
-----------------

To add an attribute to a specific group or dataset:

1.  Select the desired element in the **Architecture Tree** (right panel).
2.  Click the **"Add Attribute"** button located below the Properties tab widget.
3.  In the **Add Attribute** window:
    -   **Group Selection**: Choose a standardized group from the dropdown (e.g., `MEASURE`, `SPECTROMETER`).
    -   **Attribute Name**: Select an existing name from the dropdown or click **"new name"** to enter a custom one. A grey italicized placeholder will guide your custom entry.
    -   **Value**: If the selected attribute has recommended values, choose one from the dropdown. Otherwise, click **"custom"** to enter a manual value.
4.  Click **OK** to save the attribute to the HDF5 file. The Properties view will refresh automatically.

Removing Attributes
-------------------

To remove an attribute:

1.  Select the element in the treeview.
2.  Click the **"Remove Attribute"** button (Currently a placeholder, implementation coming soon).

Exporting the Standardized List
-------------------------------

The full list of standardized attributes can be exported to an Excel file for reference or manual data entry:

1.  Navigate to **Tools** > **Export Normalized Attributes** in the menu bar.
2.  Choose a destination path and save the file.
3.  The resulting Excel file will include **dropdown menus** in the "Value" column for all attributes that have recommended standardized values.

.. tip::
    Exporting to Excel is highly recommended for preparing large batches of metadata or for sharing the attribute nomenclature with collaborators.
