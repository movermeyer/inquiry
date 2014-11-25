import os
from .figure import Figure
from .navigator import Navigator

try:
    from psycopg2.extensions import adapt
except ImportError:
    def adapt(value):
        raise EnvironmentError("No adapting method found.")


class Inquiry(object):
    def __init__(self, figures=None, debug=None):
        """Debug will sort the sql statement for testing accuracy
        """
        self.debug = (os.getenv("DEBUG")=="TRUE" or os.getenv('CI')) if debug is None else debug
        self.figures = dict([(name, Figure(name, json)) for name, json in figures.items()]) if figures else {}
        self.build()

    def adapt(self, value, *extra_data):
        """Return the value adapted for sql
        """
        return adapt(value)

    def query(self, query):
        """Return the results of this query
        """
        pass

    def build(self):
        """Get all the figures
        """
        pass

    def format(self, key, value, *_):
        """Format the returned results as they are yielded
        """
        return value

    def adapter(self, *extra_data):
        """Return value to be passed when adapting with valideer
        ie. `valideer.parse(schema).validate(user_args, adapt=__this__)`
        """
        return True

    def add_figure(self, name, json):
        self.figures[name] = Figure(name, json)

    def new(self, *args):
        """:args and :kwargs are passed through the figure
        """
        return Navigator(self, args)

    def make(self, *args, **kwargs):
        return Navigator(self)(*args, **kwargs)

    def get(self, index):
        index = index.lower()
        if index in self.figures:
            return self.figures.get(index)
        elif (index+"s") in self.figures:
            return self.figures.get(index+"s")
        for key in self.figures:
            if index in self.figures[key].alias or index+"s" in self.figures[key].alias:
                return self.figures[key]

        raise LookupError('No figure found for `'+index+'`')
