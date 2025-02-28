from PySide6 import QtWidgets as qtw

from ParameterCurve.main import ar_BLS_VIPA_treat
from HDF5_BLS import wrapper
import numpy as np

def treat_ar_BLS_VIPA(parent, wrp, path):
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
        if isinstance(wrp_temp.data[e], wrapper.Wrapper): wrp_temp = wrp_temp.data[e]

    # Go through the wrapper and count the PSD then ask the user if he wants to treat all of them with the same parameters or each one individually
    n = count_PSD(wrp_temp)
    treat_all = True
    if n == 0: 
        qtw.QMessageBox.warning(parent, "Warning", "No PSD found")
        return
    
    msgBox = qtw.QMessageBox()
    msgBox.setText(f"There are {n} PSD in the selected data. Do you want to treat all of them at once?")
    msgBox.setInformativeText("Treat all PSD at once?")
    msgBox.setStandardButtons(qtw.QMessageBox.Yes | qtw.QMessageBox.No | qtw.QMessageBox.Cancel)
    msgBox.setDefaultButton(qtw.QMessageBox.Yes)
    ret = msgBox.exec()
    if ret == qtw.QMessageBox.Cancel: return
    elif ret == qtw.QMessageBox.No: treat_all = False

    # If treating all PSD at once, open a Parameter Curve GUI with all the PSD
    if treat_all:
         dialog = ar_BLS_VIPA_treat(parent = parent, wrapper = wrp_temp, frequency = wrp.data["Frequency"])
         if dialog.exec_() == qtw.QDialog.Accepted:
             print("Treating all PSD at once")
    