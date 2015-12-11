from abc import ABCMeta
from six import add_metaclass


from pacman.model.abstract_classes.abstract_constrained_object import \
    AbstractConstrainedObject


@add_metaclass(ABCMeta)
class AbstractLabelledVertex(object):
    """ Represents a AbstractLabelledVertex of a partitionable_graph, \
        which contains a number of atoms, and\
        which can be partitioned into a number of subvertices, such that the\
        total number of atoms in the subvertices adds up to the number of\
        atoms in the vertex
    """

    def __init__(self, label):
        self._label = label

    @property
    def label(self):
        """ The label of the vertex

        :return: The label
        :rtype: str
        :raise None: Raises no known exceptions
        """
        return self._label

    @classmethod
    def __subclasshook__(cls, othercls):
        """ Checks if all the abstract methods are present on the subclass
        """
        for C in cls.__mro__:
            for key in C.__dict__:
                item = C.__dict__[key]
                if hasattr(item, "__isabstractmethod__"):
                    if not any(key in B.__dict__ for B in othercls.__mro__):
                        return NotImplemented
        return True
