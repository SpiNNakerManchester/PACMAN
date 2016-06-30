from pacman.model.abstract_classes.abstract_has_label import AbstractHasLabel
from pacman.model.abstract_classes.overrides import overrides


class SimpleLabeledObject(AbstractHasLabel):
    """ Implementation of an item with a label
    """

    __slots__ = ("_label")

    def __init__(self, label):
        self._label = label

    @property
    @overrides(AbstractHasLabel)
    def label(self):
        return self._label
