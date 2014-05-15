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

    def add_figure(self, name, json):
        global FIGURES
        FIGURES[name] = json

    def new(self, *args):
        """:args and :kwargs are passed through the figure
        """
        return Navigator(self, args)

    def clear(self):
        global FIGURES
        FIGURES = {}
