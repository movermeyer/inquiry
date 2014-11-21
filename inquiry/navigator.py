import re


class Navigator(object):
    __slots__ = ("inquiry", "paths", "figure", "extra_data")
    path = re.compile(r"([a-z]{1,25}|\d+|\+)")

    def __init__(self, inquiry, extra_data=None):
        self.inquiry = inquiry
        self.extra_data = extra_data or []
        self.figure = None
        self.paths = []

    def __getitem__(self, path):
        self._append(path)
        return self

    def __getattr__(self, path):
        self._append(path)
        return self

    def _append(self, path):
        if path is None:
            return
        elif not self.path.match(str(path)):
            raise LookupError("Data not found for path `%s`" % str(path))
        elif not self.figure:
            self.figure = self.inquiry.get(path)
        else:
            self.paths.append(str(path))

    def __call__(self, *paths, **kwargs):
        """Calls only the index path
        Returns a container for the results
        """
        if paths: [self._append(path) for path in paths if path]
        return self.figure._process(self, self.paths, kwargs)

    def adapt(self, value):
        return self.inquiry.adapt(value, *self.extra_data)

    def query(self, query):
        return self.inquiry.query(query, *self.extra_data)

    def format(self, key, value):
        return self.inquiry.format(key, value, *self.extra_data)

    def adapter(self):
        return self.inquiry.adapter(*self.extra_data)
