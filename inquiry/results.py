import valideer
from time import time
from json import dumps
from decimal import Decimal
from datetime import datetime


def json_defaults(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, datetime):
        return str(obj)
    elif hasattr(obj, 'json'):
        return obj.json()
    else:
        return str(obj)


class Results(object):
    __slots__ = ("navigator", "_query", "period", "_results", "_speed")

    def __init__(self, navigator, query, period):
        self.navigator = navigator
        self._query = query
        self.period = period
        self._results = False
        self._speed = None

    @property
    def results(self):
        if self._results is False:
            start = time()
            self._results = self.navigator.query(self._query.replace('__into__', ''))
            self._speed = (time() - start) * 1000
        return self._results

    def refresh(self):
        self._results = False
        self.results
        return self

    def json(self, debug=False):
        results = self.results
        result = dict(results=results,
                      meta={"status": 200,
                            "total": len(results),
                            "speed": "%.fms" % self._speed})

        if self.period:
            result["meta"]["time"] = {"start": str(self.period.start), 
                                      "end": str(self.period.end)}

        if debug:
            result['meta']['query'] = self.pg()

        return dumps(result, default=json_defaults)

    @valideer.accepts(into=valideer.Nullable(valideer.Pattern(r"^[a-zA-Z\_]{1,25}$")))
    def pg(self, into=None):
        return self._query.replace("__into__", (" INTO "+(into or '')) if into else '')

    @property
    def value(self):
        results = self.results
        if results and len(results)==1:
            return list(self)[0]
        else:
            return results

    def __str__(self):
        return str(self.value)

    def __nonzero__(self):
        return bool(self.results)

    @valideer.accepts(index="integer")
    def __getitem__(self, index):
        return self.results[index]

    def __getattr__(self, index):
        if len(self.results) == 1:
            return self.navigator.format(index, self.results[0][index])
        else:
            raise ValueError("Cannot get attr from list")
    
    def __iter__(self):
        """Returns the results with python objects inserted
        """
        results = self.results
        if results:
            for row in iter(results):
                yield dict([(key, self.navigator.format(key, value)) for key, value in row.iteritems()])

    def __len__(self):
        results = self.results
        return len(results) if results else 0

    def __cmp__(self, other):
        results = self.results
        if len(results)==1:
            x = results[0][results[0].keys()[0]]
            return 0 if other == x else -1 if other > x else 1
        else:
            return False
