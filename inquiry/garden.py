import re
import valideer
from copy import deepcopy

from .helpers import *
from .query import Query


class Garden(object):
    """A garden is the container and controller for Figures
    the objective is to create a query from user arguments
    through generating seeds that will flower into the query.
    """
    _seed_titles = ("inherit", "inherits", 
                    "with", "with[]",
                    "select", "select[]",
                    "table", "table[]",
                    "tables", "tables[]",
                    "where", "where[]", 
                    "arguments")

    COLUMN_RE = re.compile(r"^[a-zA-Z]{3,25}$")
    __slots__ = ("navigator", "network_kwargs", "seeds", "arguments")

    def __init__(self, figure, navigator, paths):
        self.navigator = navigator
        # args found in network
        self.network_kwargs = {}
        self.seeds = []
        # updated by each seed when planted/cleaned
        self.arguments = {}
        self.plant(figure.seed)

        # go though the figure outline
        # plant the seeds along the way
        if len(paths) == 0:
            # using the index
            if figure.outline.get('index'):
                self.plant(figure.outline['index'])
        else:
            # start on the figure outline
            lvl = figure.outline
            # go through each provided path
            # navigating the figure outline
            while paths:
                path = paths[0]
                found = None
                for pattern in lvl:
                    # check the path regexp
                    results = re.match("^"+pattern+"$", "/"+path)
                    if results:
                        # this is a valid path
                        # change the lvl
                        lvl = lvl[pattern]
                        # plant the lvl & apply the network seed found
                        self.plant(lvl, **results.groupdict())

                        found = paths.pop(0)
                        # pop this path, we found it!
                        break

                if found is None:
                    # no path found
                    # lets look for any pattern matching "^/$"
                    # this will match r"^/a?$" because of regexp (just a reminder)
                    found = None
                    for pattern in lvl:
                        results = re.match("^"+pattern+"$", "/")
                        if results:
                            # navigate into that lvl
                            lvl = lvl[pattern]
                            # copy the seeds, pass any args back
                            self.plant(lvl, **results.groupdict())
                            found = True
                            break

                    if found is None:
                        # no paths ar all found, so serve up an error
                        paths.insert(0, figure.id)
                        raise LookupError("Figure does not exist at %s" % "/".join(paths))

            if 'index' in lvl:
                self.plant(lvl['index'])

    def plant(self, *seeds, **arguments):
        """Applys seeds and arguments
        to the garden for use during the harvest
        """
        map(self._clean, seeds)
        self.network_kwargs.update(arguments)

    def harvest(self, userkwargs):
        operators, validated = self._harvest_validate(userkwargs)
        period = deepcopy(validated.get('time'))
        query = self._harvest_query(operators, validated)
        return query, period

    def _harvest_validate(self, userkwargs):
        """Validate and Plant user provided arguments
        - Go through and plants the seedlings
          for any user arguments provided.
        - Validate the arguments, cleaning and adapting (valideer wise)
        - Extract negatives "!" arguments
        """
        # the valideer to parse the 
        # user arguemnts when watering
        parser = {}

        userkwargs.update(self.network_kwargs)
        # a simple set of original provided argument keys (used in IGNORES)
        original_kwargs = set(map(lambda k: k.split('_')[1] if k.find('_')>-1 else k, userkwargs.keys()))
        # list of columns that are required from seeds
        requires = []

        # -------------
        # Clean up Aggs
        # -------------
        for key in userkwargs.keys():
            # agg example: "avg_total", "max_tax"
            if key.find('_') > 0:
                agg, base = tuple(key.split('_'))
                if base in userkwargs:
                    if type(userkwargs[base]) is not list:
                        userkwargs[base] = [(None, userkwargs[base])]
                    userkwargs[base].append( (agg, userkwargs.pop(key)) )
                else:
                    userkwargs[base] = [(agg, userkwargs.pop(key))]

        # -----------------
        # Process Arguments
        # -----------------
        for key, seed in self.arguments.iteritems():
            # --------------
            # Argument Alias
            # --------------
            if seed.get('alias') and key in userkwargs:
                # pop the value form the user kwargs (to change the key later)
                value = userkwargs.pop(key) if key in userkwargs else NotImplemented
                # for duplicate keys
                oldkey = key+""
                # change the key
                key = seed.get('alias')
                # change the seed
                seed = get(self.arguments, seed.get('alias'))
                # set the new key:value
                if value is not NotImplemented:
                    if key in userkwargs:
                        raise valideer.ValidationError("Argument alias already specified for `%s` via `%s`" % (oldkey, key), oldkey)
                    userkwargs[key] = value

            # can provide multiple arguments
            if key.endswith('[]'):
                multi = True
                key = key[:-2]
            else:
                multi = False

            # get value(s) from user
            if key in userkwargs:
                value = userkwargs.pop(key)
            elif seed.get('copy'):
                value = userkwargs.get(seed.get('copy'))
            else:
                value = seed.get('default')

            # no argument provided, lets continue)
            if value is None or value == []:
                if seed.get('required'):
                    raise valideer.ValidationError("missing required property: %s" % key, key)
                else:
                    continue

            # add requires
            requires.extend(array(get(seed, 'requires', [])))

            # -----------
            # Inheritance
            # -----------
            # not permited from arguements yet. would need to happen above the ""PROCESS ARGUMENT"" block
            # self._inherit(*array(get(seed, 'inherit', [])))

            if type(value) is list and type(value[0]) is tuple:
                # complex
                for v in value:
                    ud, pd = self._harvest_args(key, seed, v, multi)
                    userkwargs.update(ud)
                    parser.update(pd)
            else:
                ud, pd = self._harvest_args(key, seed, value, multi)
                userkwargs.update(ud)
                parser.update(pd)

        # ------------
        # Ignored Keys
        # ------------
        for seed in self.seeds:
            ignores = set(array(get(seed, 'ignore')))
            if ignores:
                if ignores & original_kwargs:
                    if not get(seed, 'silent'):
                        additionals = ignores & original_kwargs
                        raise valideer.ValidationError("additional properties: %s" % ",".join(additionals), additionals)
                [userkwargs.pop(key) for key in ignores if key in userkwargs]

        # -------------------------
        # Custom Operators (part 1)
        # -------------------------
        operators = {}
        for key, value in userkwargs.items():
            rk = key
            agg = None
            if key.find('_')>-1:
                agg, rk = tuple(key.split('_'))
            seed = self.arguments.get(rk, self.arguments.get(rk+'[]'))
            if seed:
                if type(value) is list:
                    operators[key] = []
                    # need to remove the operator for validating
                    new_values = []
                    for v in value:
                        operator, v = self._operator(v, *seed.get('column', "").rsplit("::", 1))
                        new_values.append(v)
                        operators[key].append((agg, operator) if agg else operator)
                    userkwargs[key] = new_values
                else:
                    operator, value = self._operator(value, *seed.get('column', "").rsplit("::", 1))
                    operators[key] = (agg, operator) if agg else operator
                    userkwargs[key] = value

        # -----------------
        # Plant Sort Method
        # -----------------
        if 'sortby' in userkwargs:
            seed = self.arguments.get(userkwargs['sortby'].lower(), self.arguments.get(userkwargs['sortby'].lower()+'[]'))
            if seed:
                seed['id'] = str(userkwargs['sortby'].lower())

        for r in set(requires):
            if userkwargs.get(r) is None:
                raise valideer.ValidationError("required property not set: %s" % r, r)

        # --------
        # Validate
        # --------
        parser = valideer.parse(parser, additional_properties=False)
        validated = parser.validate(userkwargs, adapt=self.navigator.adapter())
        validated.update(self.network_kwargs)
        #   operators                   validated
        # --------------------------- | --------------------------------
        # {                           {
        #   "type": ["!", "!"],         "type": ['a', 'b'],
        #   "total": "<",               "total": "50",
        #   "tax": ("avg, ">"),         "tax": "1",
        #   "time": None                "time": "2014"
        # }                           }
        return operators, validated

    def _harvest_args(self, key, seed, value, multi):
        agg = value[0] if type(value) is tuple else None
        value = value[1] if type(value) is tuple else value

        # adapt to proper variable types
        # if value and multi and type(value) not in (list, tuple):
        #     value = [str(value).lower()]
        # if type(value) in (int, long, float, bool):
        #     value = str(value).lower()
        if multi and type(value) not in (list, tuple):
            multi = False

        # plant this arguments seed
        key = key if not agg else ("%s_%s" % (agg, key))
        seed["id"] = key
        self.plant(seed)

        # set the value
        # userkwargs[key] = value

        # add to the parser
        # parse key "+" if required
        pkey = ("+"+key) if seed.get('required') else key

        # validation methods
        # 1) choose
        if 'options' in seed:
            replace_with = []
            if seed.get('*') and value in ('*', 'all'):
                map(self.plant, seed['options'].values())

            else:
                for _value in array(value):
                    found = False
                    for pattern, _seed in seed['options'].iteritems():
                        if re.match(pattern, _value):
                            found = True

                            # replace the value provided
                            replace_with.append(_seed.get('value', _value))

                            # add the seed
                            self.plant(_seed)

                            # add the parser, though we have already parsed properly
                            break

                    # no seed found: invalid
                    if not found: raise valideer.ValidationError("Invalid value", key)
            
            if type(value) in (list, tuple):
                value = replace_with
                validate = valideer.HomogeneousSequence(valideer.String())
            else:
                value = replace_with[0] if replace_with else ""
                validate = valideer.String()

        elif 'validator' in seed:
            validator = seed.get('validator')
            if validator == 'currency':
                # somehow change currency to respect stores... (future)
                validator = "float"
            validate = valideer.HomogeneousSequence(validator) if multi else validator

        else:
            raise EnvironmentError("Missing validation method for "+key)

        return {key: value}, {pkey: validate}
       
    def _harvest_query(self, operators, validated):
        # ------------------
        # Casting / Adapting
        # ------------------
        for key in validated:
            # yes, adapt me
            rk = key.split('_')[1] if key.find('_')>-1 else key
            seed = self.arguments.get(rk, self.arguments.get(rk+'[]'))
            if seed and seed.get('adapt', True):
                validated[key] = self.navigator.adapt(validated[key])

        # ----------------
        # Format Arguments
        # ----------------
        for key, value in validated.iteritems():
            rk = key.split('_')[1] if key.find('_')>-1 else key
            seed = self.arguments.get(rk, self.arguments.get(rk+'[]'))
            if seed and seed.get('format'):
                validated[key] = seed['format'] % value

        # --------------------
        # Build Query Elements
        # --------------------
        query = Query(debug=self.navigator.inquiry.debug)
        query.groupby(*array(validated.get('groupby', [])))
        query.sortby(*array(validated.get('sortby', [])))

        for seed in self.seeds:
            if seed.get('id') and seed['id'] not in validated:
                # seed should be ignored
                continue

            # change query formatter
            if seed.get('query'):
                query.query(seed.get('query'))

            [query.with_(with_) for with_ in array(get(seed, 'with', []))]
            for column in array(get(seed, 'select', [])):
                if type(column) is dict:
                    query.select(column['column'], column.get('agg'), column.get('as'), column.get('distinct'))
                else:
                    query.select(column)

            # --------------------------
            # Formulate SELECT and WHERE
            # --------------------------
            if 'column' in seed and seed['id'] in operators:
                # if "id" not in operators then it is is likely found 
                #   in the "WHERE" arguments as task only feature.
                # operators add the query on its own
                column, datatype = tuple(seed['column'].rsplit("::", 1))
                is_array = str(datatype).endswith('[]')
                if is_array:
                    datatype = datatype[:-2]
                ops = operators[seed['id']]

                if seed.get('agg'):
                    # this column is produced when aggregated
                    # need to add that to the query
                    query.agg(seed['id'])
                
                if type(ops) is list:
                    # ----------
                    # ["!", "!"]
                    # ----------
                    if len(set(ops)) == 1:
                        # multiple arguments provided 
                        w = ("%%(%(id)s)s::%(type)s[] %(operator)s array[%(column)s]" if not is_array \
                             else "%(column)s %(operator)s %%(%(id)s)s::%(type)s[]") %\
                                  dict(column=column,
                                       operator={"=":"@>","!":"@>"}.get(ops[0], ops[0]),
                                       id=seed['id'],
                                       type=datatype)
                        where = "not("+w+")" if ops[0]=='!' else w

                    # ----------
                    # ["!", "="]
                    # ----------
                    else:
                        raise NotImplementedError("Different ops not NotImplemented")

                # ------------
                # ("avg", "<")
                # ------------
                elif type(ops) is tuple:
                    # we have an aggregate method provided
                    # need to select that data for sorting/where
                    query.select(column, ops[0], seed['id'])
                    query.agg(seed['id'])
                    where = "%(id)s %(operator)s %%(%(id)s)s::%(type)s" % \
                            dict(operator={"~":"@@","!":"!="}.get(ops[1], ops[1]),
                                 id=seed['id'],
                                 type=datatype)
               
                # -----------
                # "=" (array)
                # -----------
                elif is_array:
                    """The column being compared to is an ARRAY of any type
                    """
                    w = "%(column)s %(operator)s array[%%(%(id)s)s::%(type)s]" %\
                                 dict(column=column,
                                      operator={"=":"@>","!":"@>"}.get(ops, ops),
                                      id=seed['id'],
                                      type=datatype)
                    where = "not("+w+")" if ops=='!' else w

                # -------
                # Boolean
                # -------
                elif datatype == 'boolean':
                    where = "%(column)s is %%(%(id)s)s" % dict(column=column, id=seed['id'])

                # ---
                # "="
                # ---
                else:
                    """The column is NOT an array
                    """
                    where = "%(column)s %(operator)s %%(%(id)s)s::%(type)s" % \
                            dict(column=column,
                                 operator={"~":"@@","!":"!="}.get(ops, ops),
                                 id=seed['id'],
                                 type=datatype)

                if seed.get('format-after'):
                    where = seed.get('format-after') % where

                if seed.get('where') is not False:
                    query.where(seed.get('id'), where, *array(seed.get('where')))

                if seed.get('id'):
                    validated["where_%s"%seed['id']] = where

            else:
                ops = operators.get(seed.get('id', None))
                if ops and (type(ops) is list and '!' in ops) or ops == '!':
                    query.where(seed['id'], *[("not(%s)" % w) for w in array(get(seed, 'where', []))])
                else:
                    query.where(seed.get('id'), *array(get(seed, 'where', [])))


            query.tables(*array(get(seed, 'table', [])))
            query.groupby(*array(get(seed, 'groupby', [])))
            query.sortby(*array(get(seed, 'sortby', [])))

        # / end foreach seed

        # used for insert queries
        if '%(columns)s' in query._query:
            filtered = filter(lambda k: not k.startswith('where_'), validated.keys())
            query._query = query._query.replace('%(columns)s', ', '.join(filtered))
            query._query = query._query.replace('%(values)s', ', '.join(map(lambda k: "%%(%s)s"%k, filtered)))
        elif '%(updates)s' in query._query:
            # used for update quries
            updates = []
            for key, value in validated.items():
                if key in self.arguments:
                    column, dt = tuple(self.arguments[key]['column'].rsplit("::", 1))
                    _column = "".join((column, '=%(', key, ')s::', dt))
                    # validated["_"+key] = value
                    if ("%%(%s)s" % key) in query._query:
                        query._query = query._query.replace(("%%(%s)s" % key), _column)
                        # validated[key] = _column
                    else:
                        updates.append(_column)
            query._query = query._query.replace('%(updates)s', ", ".join(updates))

        return query(validated)
    
    def _inherit(self, *paths):
        for path in paths:
            if path:
                outline = path.split('/')
                figure = self.navigator.inquiry.get(outline.pop(0))
                garden = Garden(figure, self.navigator, outline)
                # -----------------
                # Replace Base Soil
                # -----------------
                # Seeds
                self.seeds = garden.seeds

                # Arguments
                self.arguments.update(garden.arguments)

    def _operator(self, value, column=None, datatype=None):
        # http://www.postgresql.org/docs/9.3/static/datatype.html#DATATYPE-TABLE
        ops = {"text":('!', '~'),
               "numeric":('<', '<=', '>', '>=', '!'),
               "float8":('<', '<=', '>', '>=', '!'),
               "int":('<', '<=', '>', '>=', '!')}.get(datatype, ('!'))
        for o in ops:
            if str(value).startswith(o):
                return o, value[len(o):]
        return '=', value

    def _clean(self, seed):
        """Takes a seed and applies it to the garden
        """
        seed = deepcopy(seed)
        # inherit any other figures
        self._inherit(*array(get(seed, 'inherit', [])))
        # merge the seed arguments
        if '&arguments' in seed:
            self.arguments = merge(self.arguments, seed.pop('&arguments'))

        elif 'arguments' in seed:
            self.arguments = seed.pop('arguments')
        # append the seed
        self.seeds.append(seed)
