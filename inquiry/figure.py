from copy import deepcopy

from .helpers import *
from .garden import Garden
from .results import Results


class Figure(object):
    __slots__ = ("id", "title", "help", "outline", "alias", "seed")

    def __init__(self, id, figure):
        self.id = id
        figure = deepcopy(figure)
        self.title = figure.pop('title') if 'title' in figure else None
        self.help = figure.pop('help') if 'help' in figure else None
        self.outline = figure.pop('outline')
        self.alias = array(figure.pop('alias')) if 'alias' in figure else []
        self.seed = figure

    def _process(self, navigator, paths, userkwargs):
        # filter out empty paths and generate a garden
        garden = Garden(self, navigator, [p for p in paths if p])
        # water down the garden with user arguments
        query, period = garden.harvest(userkwargs)
        # return a Resultss
        return Results(navigator, query, period)
