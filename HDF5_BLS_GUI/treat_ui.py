from PySide6 import QtWidgets as qtw

from ParameterCurve.main import ar_BLS_VIPA_treat, TFP_treat
from HDF5_BLS import wrapper
import numpy as np

def treat_ar_BLS_VIPA(parent, wrp, path):
    """
    Extracts the PSD from data obtained with an angle-resolved VIPA spectrometer.

    Parameters
    ----------
    parent : application window
        The parent GUI window
    wrp : wrapper.Wrapper
        The wrapper associated to the main h5 file
    path : str
        The path to the data we want to treat in the form "Data/Data/..."
    """
    def count_PSD(wrp, n=0):
        for e in wrp.data.keys():
            if isinstance(wrp.data[e], np.ndarray) and wrp.data_attributes[e]["Name"] == "Power Spectral Density": 
                n += 1
            else:
                n = count_PSD(wrp.data[e], n)
        return n

    # Get the selected data wrapper
    wrp_temp = wrp
    path = path.split("/")[1:]
    for e in path: 
        if isinstance(wrp_temp.data[e], wrapper.Wrapper): 
            wrp_temp = wrp_temp.data[e]

    # Go through the wrapper and count the PSD then ask the user if he wants to treat all of them with the same parameters or each one individually
    n = count_PSD(wrp_temp)
    if n == 0: 
        qtw.QMessageBox.warning(parent, "Warning", "No PSD found")
        return
    
    # Display a dialog box to ask the user if he wants to treat all of them with the same parameters or each one individually
    msgBox = qtw.QMessageBox()
    msgBox.setText(f"There are {n} PSD in the selected data. Do you want to treat all of them at once?")
    msgBox.setInformativeText("Treat all PSD at once?")
    msgBox.setStandardButtons(qtw.QMessageBox.Yes | qtw.QMessageBox.No | qtw.QMessageBox.Cancel)
    msgBox.setDefaultButton(qtw.QMessageBox.Yes)
    ret = msgBox.exec()
    if ret == qtw.QMessageBox.Yes: 
        dialog = ar_BLS_VIPA_treat(parent = parent, wrapper = wrp_temp, frequency = wrp.data["Frequency"])
        if dialog.exec_() == qtw.QDialog.Accepted:
            print("Treating all PSD at once")

def treat_TFP(parent, wrp, path):
    """
    Extracts the PSD from data obtained with an angle-resolved VIPA spectrometer.

    Parameters
    ----------
    parent : application window
        The parent GUI window
    wrp : wrapper.Wrapper
        The wrapper associated to the main h5 file
    path : str
        The path to the data we want to treat in the form "Data/Data/..."
    """
    def get_paths_childs(wrp, path = "", frequency = None):
        child, freq = [], []
        if "Frequency" in wrp.data.keys():
            if path: frequency = path+"/Frequency"
            else: frequency = "Frequency"
        for e in wrp.data.keys():
            if isinstance(wrp.data[e], wrapper.Wrapper):
                if path: ce, fe = get_paths_childs(wrp.data[e], path+"/"+e, frequency=frequency)
                else: ce, fe = get_paths_childs(wrp.data[e], path=e, frequency=frequency)
                child += ce
                freq += fe
            else:
                if e == "Power Spectral Density":
                    freq.append(frequency)
                    if path: child.append(path+"/"+e)
                    else: child.append(e)
        return child, freq
            
    # Get the selected data wrapper and frequency array
    wrp_temp = wrp
    path_loc = path.split("/")[1:]
    path_temp = "Data/"
    if "Frequency" in wrp.data.keys(): frequency = path_temp+"/Frequency"
    else: frequency = None
    for e in path_loc: 
        path_temp+"/"+e
        if "Frequency" in wrp_temp.data[e].data.keys(): 
            frequency = path_temp+"/Frequency"
        if isinstance(wrp_temp.data[e], wrapper.Wrapper): 
            wrp_temp = wrp_temp.data[e]

    childs, frequency = get_paths_childs(wrp_temp)
    
    # Display a dialog box to ask the user if he wants to treat all of them with the same parameters or each one individually
    msgBox = qtw.QMessageBox()
    msgBox.setText(f"There are {len(childs)} PSD in the selected data. Do you want to treat all of them at once?")
    msgBox.setStandardButtons(qtw.QMessageBox.Yes | qtw.QMessageBox.No | qtw.QMessageBox.Cancel)
    msgBox.setDefaultButton(qtw.QMessageBox.Yes)
    ret = msgBox.exec()

    # If the user chooses to treat all the spectra at once, open directly 
    if ret == qtw.QMessageBox.Yes: 
        dialog = TFP_treat(parent = parent, wrp_base = wrp, path_base = path, path_curves = childs, path_frequency = frequency)
        if dialog.exec_() == qtw.QDialog.Accepted:
            result = dialog.get_results()
            func = result["Function"]
            parameters = result["Parameters"]
            dialog.close()
        for c,f in zip(childs, frequency):
            frequency = wrp.get_child(path+"/"+f)[:]
            data = wrp.get_child(path+"/"+c)[:]
            try:
                popt, std, steps = func(n_frequency = frequency, 
                                        n_data = data, 
                                        **parameters)
                path_group = path+"/"+"/".join(c.split("/")[:-1])
                wrp_loc = wrp.get_child(path_group)
                i = 0
                for e in wrp_loc.data.keys():
                    if "Treat" in e: i+=1
                wrp_loc.data[f"Treat_{i}"] = wrapper.Wrapper(data = {"Shift" : np.array(popt[-2]),
                                                                     "Linewidth" : np.array(popt[-1]),
                                                                     "Shift_std" : np.array(std[-2]),
                                                                     "Linewidth_std" : np.array(std[-1])},
                                                             data_attributes = {},
                                                             attributes = {"FILEPROP.Name": f"Treat_{i}",
                                                                           "TREAT.Process": steps})
                parent.textBrowser_Log.append(f"Treatment of {path}/{c} with {func.__name__} succesful, returning the following parameters:\n Shift = {popt[-2]:.2f}±{std[-2]:.2f} GHz\n Linewidth = {popt[-1]:.3f}±{std[-1]:.3f} GHz")
            except Exception as e:
                parent.textBrowser_Log.append(f"Treatment of {path}/{c} with {func.__name__} unsuccesful: {e}")
        
    # If not, go through each spectrum and ask the user to give the treatment parameters
    elif ret == qtw.QMessageBox.No:
        for c,f in zip(childs, frequency):
            dialog = TFP_treat(parent = parent, wrp_base = wrp, path_base = path+"/"+c, frequency = path+"/"+f)
            if dialog.exec_() == qtw.QDialog.Accepted:
                result = dialog.get_results()
                dialog.close()
            frequency = wrp.get_child(path+"/"+f)[:]
            data = wrp.get_child(path+"/"+c)[:]
            try:
                popt, std, steps = func(n_frequency = frequency, 
                                        n_data = data, 
                                        **parameters)
                parent.textBrowser_Log.append(f"Treatment of {path}/{c} with {func.__name__} succesful, returning the following parameters:\n Shift = {popt[-2]}\n Linewidth = {popt[-1]}")
            except Exception as e:
                parent.textBrowser_Log.append(f"Treatment of {path}/{c} with {func.__name__} unsuccesful: {e}")