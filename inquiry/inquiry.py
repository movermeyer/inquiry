import re


class Inquiry(object):
    __slots__ = ("paths", "_figure")
    path = re.compile(r"([a-z]{3,25}|\d+|\+)")
    figures = {}
    defaults = {}

    def __init__(self):
        self._figure = None
        self.paths = []

    def __getitem__(self, path):
        self.append(path)
        return self

    def __getattr__(self, path):
        self.append(path)
        return self

    def append(self, path):
        if path is None:
            return
        elif not self.path.match(str(path)):
            raise LookupError("Data not found for path `%s`" % str(path))
        elif not self._figure:
            self._figure = self.figures.get(path)
        else:
            self.paths.append(str(path))

    def __contains__(self, path):
        return True

    def __call__(self, *paths, **kwargs):
        """Calls only the index path
        Returns a container for the results
        """
        if paths:
            [self.append(path) for path in paths if path]
        return self._figure._process(self, self.paths, kwargs)

    def adapt(self, value):
        """Return the value adapted for sql
        """
        pass

    def query(self, query):
        """Return the results of this query
        """
        pass

    def get(self, index):
        """Return the <inquiry.Figure> at provided index
        """
        pass

    def format(self, results):
        """Format the returned results as they are yielded
        """
        return results
