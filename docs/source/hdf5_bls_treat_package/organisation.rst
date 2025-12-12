For the *HDF5_BLS_treat* module, a class storing the models that can be fitted is defined and called **Models**. This class is a standalone class that can be used to define new models or to use these models in custom codes. The class **Treat** is the main class of the module. This class is used to perform the treatment of the data. It inherits from **Treat_backend**. This class allows the user to fit the data to a model and to extract the results of the fit. Finally, the class **TreatmentError** is defined to allow the user to catch errors that might occur during the processing of PSD.


