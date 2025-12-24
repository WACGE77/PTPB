def validate_exclusive_params(*args):
    tmp = [i for i in args if i is not None and i != ""]
    if len(tmp) == 0 or len(tmp) > 1:
        raise ValueError()
    return tmp
