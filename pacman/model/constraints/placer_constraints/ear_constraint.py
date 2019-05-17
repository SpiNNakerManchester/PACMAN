from .abstract_placer_constraint import AbstractPlacerConstraint


class EarConstraint(AbstractPlacerConstraint):
    """ A constraint to place a vertex on a specific chip and, optionally, a\
        specific core on that chip.
    """

    __slots__ = [
        "label"
    ]

    def __init__(self):
        self.label = "Spinnak-Ear"