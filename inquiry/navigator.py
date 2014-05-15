import re


class Navigator(object):
    __slots__ = ("inquiry", "paths", "figure")
    path = re.compile(r"([a-z]{3,25}|\d+|\+)")

    def __init__(self, inquiry, exta_data):
        self.inquiry = inquiry
        self.exta_data = exta_data
        self.figure = None
        self.paths = []

    def __getitem__(self, path):
        self.append(path)
        return self

    def __getattr__(self, path):
        self.append(path)
        return self

    def __call__(self, *paths, **kwargs):
        """Calls only the index path
        Returns a container for the results
        """
        if paths: [self.append(path) for path in paths if path]
        return self.figure._process(self, self.paths, kwargs)

    def adapt(self, value):
        return self.inquiry.adapt(value, *self.extra_data)

    def query(self, query):
        return self.inquiry.query(query, *self.extra_data)

    def format(self, value):
        return self.inquiry.format(value, *self.extra_data)
