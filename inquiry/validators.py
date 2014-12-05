import re
from valideer import *


class where(Pattern):
    name = "where"
    regexp = re.compile(r"[\w&<>|*/\+\-\(\)]+")
    rp = re.compile(r"(\w+)")
    def validate(self, value, adapt=True):
        super(where, self).validate(value)
        keys = self.rp.findall(value)
        value = self.rp.sub(r'%(\1)s', value)
        value = value.replace(' ', ' and ')
        value = value.replace('|', ' or ')
        value = value.replace('&', ' and ')
        return keys, '('+value+')'


class boolean(Validator):
    name = "bool"
    true = ("y", "yes", "1", "t", "true", "on")
    false = ("n", "no", "0", "f", "false", "off")
    def validate(self, value, adapt=True):
        if type(value) is bool:
            return value
        _value = str(value).lower()
        if _value in self.true:
            return True if adapt else value
        elif _value in self.false:
            return False if adapt else value
        else:
            self.error("bool is not valid")


# class figure(Validator):
#     name = "figure"
#     tables = HomogeneousSequence(Pattern(r"(from|(inner|outer|full|right) join) .*"))
#     seed = None # todod
#     arguments = Mapping(Pattern(r"(\&\-)\w+(\[\])?", seed))
#     validate = Object(required=dict(tables=tables,
#                                     arguments=arguments,
#                                     outline=Mapping("string", Type(dict))),
#                       optional=dict(help="string"),
#                       additional=False)
