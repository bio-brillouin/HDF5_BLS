def brillouin_type_update(name, obj):
    """
    Updates the Brillouin_type attribute of an object to comply with the new version.
    """
    changes = [["_std","_err"]]
    if "Brillouin_type" in obj.attrs:
        tpe = obj.attrs["Brillouin_type"]
        for elt in changes:
            o,n = elt
            if o in tpe:
                obj.attrs.modify("Brillouin_type", tpe.replace(o,n))

