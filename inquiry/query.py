import re
import valideer
import itertools
from copy import deepcopy

from .helpers import unique


class Query(object):
    __slots__ = ("debug", "_with", "_selects", "_where", "_tables", "_groupby", "_sortby", "_aggs", "_into")
    escape = re.compile(r'\%(?!\()')

    def __init__(self, debug=False):
        self.debug = debug
        self._with = []
        self._selects = {}
        self._where = {}
        self._tables = []
        self._groupby = []
        self._sortby = []
        self._aggs = []
        self._into = True

    def with_(self, _with, as_=None):
        if as_:
            _with = "%s as (%s)" % (as_, _with)
        if _with is False:
            self._with = []
        elif _with not in self._with:
            self._with.append(_with)

    def agg(self, column):
        if column is False:
            self._aggs = []
        elif column not in self._aggs:
            self._aggs.append(column)

    def select(self, column, agg=None, _as=None, distinct=False):
        """
        What columnns to select in query.
        :column should be a column name or equation to produce column **not** aggregated
        :agg should be a valid aggregate method used to producte the figure
        :_as should be a string used to represent the column. Required when agg present
        """
        if agg and not _as:
            raise ValueError("Aggregate colunns require `_as` to be specified")
        if column is False:
            self._selects = {}
        else:
            if agg:
                self._aggs.append(_as or column)
            self._selects.setdefault((_as or column), (column, agg, _as, distinct))

    def tables(self, *tables):
        # first table is always a From
        for table in tables:
            if table is False:
                self._tables = []
            else:
                self._tables.append(table)

    def into(self, bool):
        self._into = bool

    def where(self, column, *where):
        self._where.setdefault(column, []).extend(list(where))

    def groupby(self, *groupby):
        for g in groupby:
            if g is False:
                self._groupby = []
            elif g not in self._groupby:
                self._groupby.append(g)

    def sortby(self, *sorts):
        for sort in sorts:
            if sort is False:
                self._sortby = []
            elif sort not in self._sortby:
                self._sortby.append(sort)

    def __call__(self, validated):

        # Selects
        # -------

        # need to add all the groupbys
        for g in self._groupby:
            found = False
            for s in self._selects:
                #                         |v|       | v         |
                # matches "extract(..) as day" and "gph.productid as product"
                if s.startswith(g) or s.endswith(g):
                    found = True
                    break
            if not found:
                self._selects[g] = (g, None, None, None)

        if self._aggs and set(self._aggs) & set(self._where.keys()) and self._groupby:

            # --------------
            # New Main Query
            # --------------
            With = Query()

            # select all the columns (by as)
            [With.select(col) for col in self._selects.keys()]
            With.into(True)
            With.tables("from _data")
            [With.where(col, *self._where.pop(col)) for col in self._aggs if col in self._where]

            # ~~groupby~~ no need
            if self._sortby:
                With.sortby(*self._sortby)
                # need to select sorts in next query
                for sort in self._sortby:
                    if sort not in self._selects.keys():
                        self._selects[sort] = (sort, None, None, None)
                self._sortby = []
            # only need to pop these when sorting methods present
            limit = validated.pop('limit') if 'limit' in validated else None
            offset = validated.pop('offset') if 'offset' in validated else None

            # ----------------------
            # Change Self Properties
            # ----------------------
            With._with = self._with
            self._with = []

            self.into(False)
            # remove sorting from **this** query

            # ---------
            # With Self
            # ---------
            self._aggs = []
            With.with_(self(validated), as_="_data")

            validated['limit'] = limit
            validated['offset'] = offset
            return With(validated)

        elif str(validated.get('limit', '')).endswith('%'):
            """
            ### Making the with query below

            ```psql
            with _limited as (select total from orders where total > 10) 
            select total from _limited order by total asc limit (select round(count(*)*.1) from _limited)
            ```
            """
            _limited = Query()
            _limited._selects = deepcopy(self._selects)
            self._selects = dict(zip(self._selects.keys(), map(lambda a: (a, None, None, None), self._selects.keys())))
            _limited.into(False)
            _limited.tables("from _limited")

            if self._sortby:
                _limited.sortby(*self._sortby)
                # need to select sorts in next query
                for sort in self._sortby:
                    if sort not in self._selects.keys():
                        self._selects[sort] = sort
                self._sortby = []

            _limited._with = self._with
            self._with = []

            [_limited.agg(a) for a in self._aggs]
            self._aggs = []

            self.into(False)

            limit = validated.pop('limit')
            _limited.with_(self(validated), as_="_limited")

            validated['limit'] = "(select round(count(*)*%s) from _limited)" % (float(limit[:-1])/100)
            return _limited(validated)
        else:

            query = "%(with)sselect %(select)s%(into)s %(tables)s%(where)s%(groupby)s%(sortby)s%(limit)s%(offset)s"

            elements = {}

            # With
            # ----
            elements['with'] = ("with %s "%', '.join(self._with)) if self._with else ""

            # Select
            # ---------------
            # add sortby to select (only needed for DISTINCT)
            if self._sortby:
                for sort in self._sortby:
                    if sort not in self._selects.keys():
                        self._selects[sort] = (sort, None, None, None)

            elements["select"] = ', '.join(map(self._column, sorted(self._selects.values(), key=lambda a: a[3])))

            # Into
            # ----
            elements['into'] = "__into__" if self._into else ""

            # Tables
            # ------
            _from = None
            for table in self._tables:
                if table.startswith('from'):
                    _from = table
            if _from is None:
                raise valideer.ValidationError("Not enough arguments supplied to formulate a tables for query")

            newtables = self._tables[self._tables.index(_from):]
            oldtables = self._tables[:self._tables.index(_from)]
            newtables.extend([t for t in oldtables if not t.startswith('from')])
            self._tables = unique(newtables)
            elements["tables"] = " ".join(self._tables)

            # Where
            # -----
            # custom ?where=this|that
            if validated.get('where'):

                # valideer produces the tuple below
                keys, string = validated.pop("where")
                try:
                    self._where.setdefault('_', []).append(string % self._algebra(self._where))
                except KeyError as e:
                    raise valideer.ValidationError("Missing argument `%s` needed in provided where clause" % str(e)[1:-1],
                                                   str(e)[1:-1])
                [self._where.pop(key) for key in keys if key in self._where]

            wheres = list(itertools.chain(*self._where.values()))
            if self.debug: wheres = sorted(wheres)
            elements['where'] = (" where " + ' and '.join(wheres)) if wheres else ""

            # Group By
            # --------
            elements['groupby'] = (" group by " + ','.join(map(lambda g: ('"%s"'%g) if g == 'group' else g,
                                                               self._groupby))) if self._groupby else ""

            # Sort By
            # -------
            # http://www.postgresql.org/docs/8.1/static/queries-order.html
            #   Each column specification may be followed by an optional ASC or DESC to set the sort direction to ascending or descending. 
            #   ASC order is the default
            elements['sortby'] = (" order by %s %s" % (",".join(self._sortby), validated.get('dir', 'asc'))) if self._sortby else ""

            # Limit
            # -----
            limit = validated.get('limit')
            

            elements['limit'] = (" limit %s" % validated['limit']) if limit else ""

            # Offset
            # ------
            elements['offset'] = (" offset %s" % validated['offset']) if validated.get('offset') else ""

            # ----------
            # Format SQL
            # ----------
            try:
                return (query % elements) % validated
            except ValueError:
                return (self.escape.sub('%%', query) % elements) % validated

    def _column(self, peices):
        col, agg, _as, distinct = peices
        return "".join(["distinct " if distinct else "",
                        agg or "", "(" if agg else "", (('"%s"'%col) if col == 'group' else col), ")" if agg else "",
                        " as " if _as else "", _as or ""])
                       # lambda g: ("".join([])'"%s"'%g) if g == 'group' else g

    def _algebra(self, dct):
        return dict([(key, (("(%s)" % " and ".join(value)) if len(value) > 1 else value[0])) for key, value in dct.items() if value])
