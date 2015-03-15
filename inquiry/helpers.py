import re
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


TOKENIZER = re.compile(r'"|(/\*)|(\*/)|(//)|\n|\r')
END_SLASHES_RE = re.compile(r'(\\)*$')

def json_minify(string, strip_space=True): # pragma: no cover
    """Removes whitespace from json strings, returning the string
    """
    in_string = False
    in_multi = False
    in_single = False

    new_str = []
    index = 0

    for match in re.finditer(TOKENIZER, string):

        if not (in_multi or in_single):
            tmp = string[index:match.start()]
            if not in_string and strip_space:
                # replace white space as defined in standard
                tmp = re.sub('[ \t\n\r]+', '', tmp)
            new_str.append(tmp)

        index = match.end()
        val = match.group()

        if val == '"' and not (in_multi or in_single):
            escaped = END_SLASHES_RE.search(string, 0, match.start())

            # start of string or unescaped quote character to end string
            if not in_string or (escaped is None or len(escaped.group()) % 2 == 0):
                in_string = not in_string
            index -= 1 # include " character in next catch
        elif not (in_string or in_multi or in_single):
            if val == '/*':
                in_multi = True
            elif val == '//':
                in_single = True
        elif val == '*/' and in_multi and not (in_string or in_single):
            in_multi = False
        elif val in '\r\n' and not (in_multi or in_string) and in_single:
            in_single = False
        elif not ((in_multi or in_single) or (val in ' \r\n\t' and strip_space)):
            new_str.append(val)

    new_str.append(string[index:])
    return ''.join(new_str)
