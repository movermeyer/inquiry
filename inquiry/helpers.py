from copy import deepcopy

def unique(lst):
    """Unique with keeping sort/order 
        ["a", "c", "b", "c", "c", ["d", "e"]]
    
    Results in 
        ["a", "c", "b", "d", "e"]
    """
    nl = []
    [(nl.append(e) if type(e) is not list else nl.extend(e)) \
     for e in lst if e not in nl]
    return nl

def _merge_fix(d):
    """Fixes keys that start with "&" and "-"
        d = {
          "&steve": 10,
          "-gary": 4
        }
        result = {
          "steve": 10,
          "gary": 4
        }
    """
    if type(d) is dict:
        for key in d.keys():
            if key[0] in ('&', '-'):
                d[key[1:]] = _merge_fix(d.pop(key))
    return d

def merge(d1, d2):
    """This method does cool stuff like append and replace for dicts
        d1 = {
          "steve": 10,
          "gary": 4
        }
        d2 = {
          "&steve": 11,
          "-gary": null
        }
        result = {
          "steve": [10, 11]
        }
    """
    d1, d2 = deepcopy(d1), deepcopy(d2)
    if d1 == {} or type(d1) is not dict:
        return _merge_fix(d2)

    for key in d2.keys():
        # "&:arg" join method
        if key[0] == '&':
            data = d2[key]
            key = key[1:]
            if key in d1:
                if type(d1[key]) is dict and type(data) is dict:
                    d1[key] = merge(d1[key], data)
                elif type(d1[key]) is list:
                    d1[key].append(data)
                else:
                    d1[key] = [d1[key], data]
            else:
                # not found, just add it
                d1[key] = data

        # "-:arg" reduce method
        elif key[0] == '-':
            data = d2[key]
            key = key[1:]
            if key in d1:
                # simply remove the key
                if data is None:
                    d1.pop(key)
                elif type(d1[key]) is list and data in d1[key]:
                    d1[key].remove(data)

        # standard replace method
        else:
            d1[key] = _merge_fix(d2[key])

    return d1

def get(dict, key, _else=None, pop=False):
    options = (key, ((key[:-1]) if key.endswith('s') else key+'s'), key+'[]')
    for option in options:
        if option in dict:
            if pop:
                return dict.pop(option)
            return dict[option]
    return _else

def array(value):
    """Always return a list
    """
    if type(value) in (list, tuple):
        return value
    else:
        return [value]
