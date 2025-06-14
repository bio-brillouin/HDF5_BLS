def check_conversion_ar_BLS_VIPA(wrapper, path):
    """This function checks if without any additional information, the data can be converted to a PSD. For an ar-BLS VIPA spectrometer, this can be the case if the center of center of the beam is known and a frequency array exists on the parent of the data.

    Parameters
    ----------
    wrapper : wrapper.Wrapper
        The wrapper object leading to the data to be converted.
    path : str
        The path to the data to be converted.

    Returns
    -------
    bool
        True if the data can be converted to a PSD, False otherwise.
    """
    attributes = wrapper.get_attributes_path(path)
    if "TREAT.Center" in attributes.keys():
        return True
    else:
        return False
    
def check_conversion_VIPA(wrapper, path):
    """This function checks if without any additional information, the data can be converted to a PSD. For a VIPA spectrometer, this is never the case so the function returns False.

    Parameters
    ----------
    wrapper : wrapper.Wrapper
        The wrapper object leading to the data to be converted.
    path : str
        The path to the data to be converted.

    Returns
    -------
    bool
        False, as the user needs to enter additional information to convert the data.
    """
    return False

def check_conversion_Streak_VIPA(wrapper, path):
    """This function checks if without any additional information, the data can be converted to a PSD. For a VIPA spectrometer (even one using a Streak camera), this is never the case so the function returns False.

    Parameters
    ----------
    wrapper : wrapper.Wrapper
        The wrapper object leading to the data to be converted.
    path : str
        The path to the data to be converted.

    Returns
    -------
    bool
        False, as the user needs to enter additional information to convert the data.
    """
    return False

    
    
    

