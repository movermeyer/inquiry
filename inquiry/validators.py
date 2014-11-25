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
    def validate(self, value, adapt=True):
        if value in (False, True):
            return value
        elif value.lower() in ('f', 'false', '0'):
            return False
        elif value.lower() in ('t', 'true', '1'):
            return True
        else:
            self.error("Bool is not a valid format")


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
