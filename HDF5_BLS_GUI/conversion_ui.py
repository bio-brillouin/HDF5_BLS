from PySide6 import QtCore as qtc
from PySide6 import QtWidgets as qtw
from PySide6 import QtGui as qtg
import h5py

import numpy as np
from scipy.optimize import minimize

from ComboboxChoose.main import ComboboxChoose
from ParameterCurve.main import ar_BLS_VIPA_parameters
from AnalyzeWindow.main import AnalyzeWindow_VIPA

from HDF5_BLS import wrapper

def conversion_ar_BLS_VIPA(parent, wrp, path):
    def get_structure_wrapper(l, elt):
        for e in elt.data.keys():
            if isinstance(elt.data[e], wrapper.Wrapper):
                name = elt.data[e].attributes["FILEPROP.Name"]
                l[name] = {}
                get_structure_wrapper(l[name],elt.data[e])
        return l
    
    def list_from_structure(structure, ls=[], code = [], l=0, code_up = "Data", ls_up = ""):
        for i, e in enumerate(structure.keys()):
            if ls_up: ls.append("  |- " + ls_up + "/" + e)
            else: ls.append(e)
            code.append(code_up+"/Data_"+str(i))
            if structure[e] is not None: 
                ls, code = list_from_structure(structure[e], ls, code, l+1, code[-1], ls[-1])
        return ls, code

    def get_extent_radius(shape, c_x, c_y):
        s_x, s_y = shape
        if s_y > 2*c_y:
            R_max_curv = np.sqrt((s_x-c_x)**2 + (s_y-c_y)**2) - np.sqrt((c_x)**2 + (s_y-c_y)**2)
        else:
            R_max_curv = np.sqrt((s_x-c_x)**2 + (c_y)**2) - np.sqrt((c_x)**2 + (c_y)**2)
        return R_max_curv

    def change_names_of_all_arrays(wrp, name):
        for e in wrp.data.keys():
            if type(wrp.data[e]) == np.ndarray:
                if e in wrp.data_attributes.keys():
                    wrp.data_attributes[e]["Name"] = name
                else:
                    wrp.data_attributes[e] = {"Name": name}
            else:
                change_names_of_all_arrays(wrp.data[e], name)

    # Verify that the FSR can be found in the arguments
    if not "SPECTROMETER.VIPA_FSR_(GHz)" in wrp.get_attributes(path).keys():
        qtw.QMessageBox.warning(parent, "Warning", "PSD cannot be constructed because the FSR of the VIPA is not defined.")
        return

    # Create the combobox GUI to select the calibration data
    structure = get_structure_wrapper({}, wrp) # Extracts the structure of the wrapper
    l, code = list_from_structure(structure) # Transforms the structure into a list of strings and a list of codes
    text = "Select the calibration curves from the list below. You can either choose single datasets or groups of datasets."
    dialog = ComboboxChoose(text, l, parent)
    if dialog.exec_() == qtw.QDialog.Accepted:
        selected_structure = dialog.get_selected_structure()
        dialog.close()
    else:
        dialog.close()
        return
    
    # Opens the GUI to extract the center of the curvatures that the user has indicated
    code = code[l.index(selected_structure)]
    wrp_ref = wrp
    for e in code.split("/")[1:]: wrp_ref = wrp_ref.data[e]
    dialog = ar_BLS_VIPA_parameters(parent=parent, wrapper=wrp_ref)
    if dialog.exec_() == qtw.QDialog.Accepted:
        result = dialog.get_results()
        dialog.close()
    else:
        dialog.close()
        return

    # Combute the error on the centers of the fitted circles
    centers = np.array([[c for c in result["center"][e]] for e in result["center"].keys()])

    try:
        centers = np.array(centers)
    except:
        qtw.QMessageBox.warning(parent, "Warning", "PSD cannot be constructed because the number of elastic lines selected for each calibration curve is not the same.")
        return

    c_x = np.average(centers[:,:,0])
    c_y = np.average(centers[:,:,1])
    std_x = np.std(centers[:,:,0])
    std_y = np.std(centers[:,:,1])

    if result["data shape"][1] > 2*c_y:
        extent = abs(get_extent_radius(result["data shape"], c_x+std_x, c_y+std_y) - get_extent_radius(result["data shape"], c_x-std_x, c_y-std_y))
    else:
        extent = abs(get_extent_radius(result["data shape"], c_x+std_x, c_y-std_y) - get_extent_radius(result["data shape"], c_x-std_x, c_y+std_y))


    # Create the frequency array by first computing the distance to the average center of the point of the fringes located at the same y
    F = []

    for i, crv in enumerate(centers):
        y = np.arange(result["data shape"][1])
        d1 = np.array([np.sqrt(crv[0, 2]**2 - (y - crv[0, 1])**2) + crv[0, 0], y]).T
        d2 = np.array([np.sqrt(crv[1, 2]**2 - (y - crv[1, 1])**2) + crv[1, 0], y]).T
        d3 = np.array([np.sqrt(crv[2, 2]**2 - (y - crv[2, 1])**2) + crv[2, 0], y]).T

        # Combine data and targets
        X = np.vstack((d1, d2, d3))
        Y = np.hstack((np.ones(len(d1)), 2*np.ones(len(d2)), 3*np.ones(len(d3))))  # Target values

        # Construct the design matrix A: [x^2, y^2, xy, x, y, 1]
        A = np.column_stack([X[:, 0]**2, X[:, 1]**2, X[:, 0] * X[:, 1], X[:, 0], X[:, 1], np.ones(X.shape[0])])

        # Solve the least squares problem A * Θ = Y
        theta, _, _, _ = np.linalg.lstsq(A, Y, rcond=None)

        # Visualization
        X_grid, Y_grid = np.meshgrid(np.arange(result["data shape"][0]), np.arange(result["data shape"][1]))
        f = lambda X, Y: theta[0] * X**2 + theta[1] * Y**2 + theta[2] * X * Y + theta[3] * X + theta[4] * Y + theta[5]
        F.append(f(X_grid, Y_grid) * float(wrp.get_attributes(path)["SPECTROMETER.VIPA_FSR_(GHz)"]))
   
    F = np.array(F)
    freq = np.average(F, axis=0)

    # Store the treated data in the wrapper
    wrp.data["Frequency"] = freq
    wrp.data_attributes["Frequency"] = {"Name": "Frequency"}
    wrp.attributes["TREATMENT.Center"] = f"{c_x}, {c_y}"
    wrp.attributes["TREATMENT.PSD_algorithm"] = result["treatment"]
    wrp.attributes["TREATMENT.PSD_error_radius"] = extent

    # Change the names of the raw data to "Power Spectral Density"
    for e in wrp.data.keys():
        if type(wrp.data[e]) == wrapper.Wrapper:
            change_names_of_all_arrays(wrp.data[e], "Power Spectral Density")

def conversion_VIPA(parent, wrp, path):
    """This function allows the user to convert a raw spectrum  from aVIPA spectrometer to a PSD. It opens a dedicated GUI to perform the conversion

    Parameters
    ----------
    parent : QtWidgets.QWidget
        The parent widget of the function.
    wrp : wrapper.Wrapper
        The wrapper object leading to the data to be converted.
    path : str
        The path to the data to be converted.

    Returns
    -------
    None
    """
    if type(path) == list:
        all_paths = path
        path = path[0]
    else: 
        all_paths = None

    # Verify that the FSR can be found in the arguments. If not, the frequency axis cannot be created
    if not "SPECTROMETER.VIPA_FSR_(GHz)" in wrp.get_attributes(path).keys():
        qtw.QMessageBox.warning(parent, "Warning", "PSD cannot be constructed because the FSR of the VIPA is not defined.")
        return

    # If the user has chosen a single dataset, select the parent group
    if all_paths is None:   
        if not wrp.get_type(path = path) == h5py._hl.group.Group:
            path = "/".join(path.split("/")[:-1])  
    # If the user has chosen multiple elements, make sure they are all groups
    else:
        for p in all_paths:
            if not wrp.get_type(path = p) == h5py._hl.group.Group:
                qtw.QMessageBox.information(parent, "Information", "All selected elements must be groups.")
                return

    # Check if the chosen gorup is a measure group
    if all_paths is None:   
        if not wrp.get_type(path = path, return_Brillouin_type = True) == "Measure":
            qtw.QMessageBox.information(parent, "Information", "Only measure groups can be analyzed for now.")
            return
    else:
        for p in all_paths:
            if not wrp.get_type(path = p, return_Brillouin_type = True) == "Measure":
                qtw.QMessageBox.information(parent, "Information", "All selected groups must be measure groups.")
                return
    
    # Extract the raw data and the PSD from the wrapper corresponding to the selected curve in the combobox
    raw_data, PSD = False, False
    if all_paths is None: 
        e = ''
        for child in wrp.get_children_elements(path = path):
            if wrp.get_type(path = f"{path}/{child}", return_Brillouin_type = True) == "Raw_data":
                y_rd = wrp[f"{path}/{child}"]
                str_algorithm_rd = None
                raw_data = True
                e = child
            elif wrp.get_type(path = f"{path}/{child}", return_Brillouin_type = True) == "PSD":
                y_psd = wrp[f"{path}/{child}"]
                str_algorithm_psd = wrp.get_attributes(path = f"{path}/{child}")["Process_PSD"]
                PSD = True
                e = child
    else:
        y_rd = None
        str_algorithm_rd = None
        for p in all_paths:
            for child in wrp.get_children_elements(path = p):
                if wrp.get_type(path = f"{p}/{child}", return_Brillouin_type = True) in ["Raw_data", "PSD"]:
                    temp_y_rd = wrp[f"{p}/{child}"]
                    temp_y_rd = np.array(temp_y_rd).reshape((-1, temp_y_rd.shape[-1]))
                    raw_data = True
                    if y_rd is None:
                        y_rd = temp_y_rd
                    else:
                        y_rd = np.concatenate((y_rd, temp_y_rd), axis = 0)

    if raw_data and not PSD:
        dialog = AnalyzeWindow_VIPA(parent, x = np.arange(y_rd.shape[-1]), y = y_rd)
    elif PSD and not raw_data:
        dialog = AnalyzeWindow_VIPA(parent, x = np.arange(y_psd.shape[-1]), y = y_psd, str_algorithm = str_algorithm_psd)
    else:
        response = qtw.QMessageBox.question(parent, "Warning", "Do you want to open the previous analysis (Yes) or create a new one (No)?", qtw.QMessageBox.Yes | qtw.QMessageBox.No | qtw.QMessageBox.Cancel)
        if response == qtw.QMessageBox.No:
            dialog = AnalyzeWindow_VIPA(parent, x = np.arange(y_psd.shape[-1]), y = y_psd, str_algorithm = str_algorithm_psd)
        elif response == qtw.QMessageBox.Yes:
            dialog = AnalyzeWindow_VIPA(parent, x = np.arange(y_rd.shape[-1]), y = y_rd)
        else:
            return
        
    dialog.exec_()
    if dialog.result() == qtw.QDialog.Accepted:
        process, frequency = dialog.get_results()
        dialog.close()
    else: 
        dialog.close()
        return

    dic = {"Frequency": {"Name": "Frequency",
                            "Data": frequency},
            "Attributes": {"Process_PSD": process}}
    
    if all_paths is None:  
        if "Frequency" in wrp.get_children_elements(path):
            wrp.delete_element(f"{path}/Frequency")
        # wrp.add_frequency(data = frequency, parent_group = path, overwrite = True)
        wrp.add_dictionary(dic = dic,
                            parent_group = path,
                            overwrite = True)
        wrp.change_brillouin_type(path = f"{path}/{e}", brillouin_type = "PSD")
    else:
        for p in all_paths:
            if "Frequency" in wrp.get_children_elements(path = p):
                wrp.delete_element(f"{p}/Frequency")
            wrp.add_dictionnary(dic = dic,
                        parent_group = p,
                        name_group = p,
                        overwrite = True)
            for child in wrp.get_children_elements(path = p):
                if wrp.get_type(path = f"{p}/{child}", return_Brillouin_type = True) == "Raw_data":
                    wrp.change_brillouin_type(path = f"{p}/{child}", brillouin_type = "PSD")
    parent.update_treeview()

def conversion_Streak_VIPA(parent, wrp, path):
    """This function allows the user to convert a raw spectrum  from a Streak VIPA spectrometer to a PSD. It applies the same algorithm as the one used for the VIPA spectrometer.

    Parameters
    ----------
    parent : QtWidgets.QWidget
        The parent widget of the function.
    wrp : wrapper.Wrapper
        The wrapper object leading to the data to be converted.
    path : str
        The path to the data to be converted.

    Returns
    -------
    None
    """
    conversion_VIPA(parent, wrp, path)

    

    
