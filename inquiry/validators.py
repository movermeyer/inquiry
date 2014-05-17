import re
import valideer


class where(valideer.Pattern):
    name = "where"
    regexp = re.compile(r"[\w&<>|*/+\-\(\)]+")
    rp = re.compile(r"(\w+)")
    def validate(self, value, adapt=True):
        super(where, self).validate(value)
        keys = self.rp.findall(value)
        value = self.rp.sub(r'%(\1)s', value)
        value = value.replace('|', ' or ')
        value = value.replace('&', ' and ')
        return keys, '('+value+')'


class boolean(valideer.Validator):
    name = "bool"
    def validate(self, value, adapt=True):
        if value in (False, True):
            return value
        elif value.lower() in ('f', 'false', '0'):
            return False
        elif value.lower() in ('t', 'true', '1'):
            return True
        else:
            raise valideer.ValidationError("Bool is not a valid format")
