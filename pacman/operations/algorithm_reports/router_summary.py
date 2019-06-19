

class RouterSummary(object):

    __slots__ = [
        "_total_entries",
        "_max_per_chip",
        "_max_defaultable",
        "_max_link",
        "_unqiue_routes",
    ]

    def __init__(self, total_entries, max_per_chip, max_defaultable, max_link,
                 unqiue_routes):

        self._total_entries = total_entries
        self._max_per_chip = max_per_chip
        self._max_defaultable = max_defaultable
        self._max_link = max_link
        self._unqiue_routes = unqiue_routes

    @property
    def total_entries(self):
        return self._total_entries

    @property
    def max_per_chip(self):
        return self._max_per_chip

    @property
    def max_defaultable(self):
        return self._max_defaultable

    @property
    def max_link(self):
        return self._max_link

    @property
    def unqiue_routes(self):
        return self._unqiue_routes
