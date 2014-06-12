import valideer
from time import time
from json import dumps
from decimal import Decimal
from datetime import datetime
from xml.dom.minidom import Document


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

    def json(self):
        results = self.results
        result = dict(results=results,
                      meta={"status": 200,
                            "total": len(results),
                            "speed": "%.fms" % self._speed})
        if self.period:
            result["time"] = {"start": str(self.period.start), 
                              "end": str(self.period.end)}

        return dumps(result, default=json_defaults)
    
    def xml(self):
        speed = time()
        results = self.results
        if results:
            doc = Document()
            # <figure></figure>
            base = doc.createElement('figure')
            doc.appendChild(base)
            
            # <figure><meta></meta></figure>
            meta = doc.createElement('meta')
            base.appendChild(meta)
            for key, value in (("status", 200), ("rows", len(results)), ("title", self.title), ('time', self.period), ("speed", "%.fms" % ((time() - speed)*1000))):
                # <figure><meta><:key>:value</:key></meta></figure>
                _meta, meta_value = doc.createElement(key), doc.createTextNode(str(value))
                meta.appendChild(_meta)
                meta.appendChild(meta_value)

            # <figure><rows></rows></figure>
            rows = doc.createElement('rows')
            base.appendChild(rows)
            for row in results:
                # <figure><rows><row></row></rows></figure>
                _row = doc.createElement('row')
                rows.appendChild(_row)
                for key in row:
                    k, v = doc.createElement(key), doc.createTextNode(str(row[key]) if row[key] is not None else '')
                    _row.appendChild(k)
                    k.appendChild(v)

            return doc.toxml()

    def csv(self):
        results = self.results
        if results:
            keys = self.results[0].keys()
            string = ",".join(keys)
            for row in self.results:
                string = "\n" + ",".join(map(lambda k: '"%s"'%str(row[k]), keys))
            return string

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
