from .figure import Figure
from .navigator import Navigator

FIGURES = {}

class Inquiry(object):
    def __init__(self):
        self.build()

    def adapt(self, value):
        """Return the value adapted for sql
        """
        pass

    def query(self, query):
        """Return the results of this query
        """
        pass

    def build(self):
        """Get all the figures
        """
        pass

    def format(self, results):
        """Format the returned results as they are yielded
        """
        return results

    def adapter(self, *extra_data):
        """Return value to be passed when adapting with valideer
        ie. `valideer.parse(schema).validate(user_args, adapt=__this__)`
        """
        return True

    def add_figure(self, name, json):
        global FIGURES
        FIGURES[name] = Figure(name, json)

    def new(self, *args):
        """:args and :kwargs are passed through the figure
        """
        return Navigator(self, args)

    def clear(self):
        global FIGURES
        FIGURES = {}

    def get(self, index):
        global FIGURES
        if not FIGURES:
            self.build()
        
        index = index.lower()
        if index in FIGURES:
            return FIGURES.get(index)
        elif (index+"s") in FIGURES:
            return FIGURES.get(index+"s")
        for key in FIGURES:
            if index in FIGURES[key].alias or index+"s" in FIGURES[key].alias:
                return FIGURES[key]

        raise LookupError('No figure found for `'+index+'`')
