from pacman.model.abstract_classes.abstract_has_label import AbstractHasLabel
from pacman.model.decorators.overrides import overrides


class SimpleLabeledObject(AbstractHasLabel):
    """ Implementation of an item with a label
    """

    __slots__ = [

        # The label of the object
        "_label"
    ]

    def __init__(self, label):
        """

        :param label: The label of the object
        """
        self._label = label

    @property
    @overrides(AbstractHasLabel.label)
    def label(self):
        return self._label
