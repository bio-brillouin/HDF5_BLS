def check_conversion_ar_BLS_VIPA(wrapper, path):
    attributes = wrapper.get_attributes_path(path)
    if "TREAT.Center" in attributes.keys():
        return True
    else:
        return False
    
    
    

