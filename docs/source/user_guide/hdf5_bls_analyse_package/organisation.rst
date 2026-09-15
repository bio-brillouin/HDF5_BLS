For the *HDF5_BLS_analyse* module, a general class performing general operations on the data is defined. This class is called **Analyse_general** and inherits from **Analyse_backend**. This class is used to perform operations on the data that are not specific to a particular type of spectrometer. For example, the function to add a remarkable point to the data. 
Functions specific to a particular spectrometers are defined in classes that inherit from **Analyse_general**, and are dedicated to the analysis of data obtained with that spectrometer.

Here are a few examples of such classes:
- **Analyse_VIPA**: for the analysis of data obtained with VIPA spectrometers.
- **Analyse_TFP**: for the analysis of data obtained with tandem Fabry-Pérot interferometers. (*Not yet implemented*)
- **Analyse_TD**: for the analysis of data obtained with time-domain spectrometers.(*Not yet implemented*)
- **Analyse_SBS**: for the analysis of data obtained with echelle spectrometers(*Not yet implemented*)

.. admonition:: Note for developpers

    It is possible to develop new spectrometer classes based on spectrometer classes if the new spectrometers are based on a specific type of existing instrument. For example, the Ultrafast Stimulation-Synchronized Brillouin spectrometer (USS-BM spectrometr) being based on a VIPA spectrometer, it would be possible to create a class **Analyse_USS_BM** inheriting from **Analyse_VIPA**. This would allow to reuse the functions already defined for VIPA spectrometers, and to add functions specific to the USS-BM spectrometer. 


For now, only the **Analyse_VIPA** class is stable. It inherits from **Analyse_general**, and is defined for the analysis of data obtained with VIPA spectrometers.
