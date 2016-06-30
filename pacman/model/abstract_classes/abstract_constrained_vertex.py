from abc import ABCMeta
from six import add_metaclass


from pacman.model.abstract_classes.abstract_has_constraints import \
    AbstractHasConstraints
from pacman.model.abstract_classes.simple_labeled_object import \
    SimpleLabeledObject


@add_metaclass(ABCMeta)
class AbstractConstrainedVertex(AbstractHasConstraints,
                                SimpleLabeledObject):
    """ Represents a AbstractConstrainedVertex of a partitionable_graph, \
        which contains a number of atoms, and\
        which can be partitioned into a number of subvertices, such that the\
        total number of atoms in the subvertices adds up to the number of\
        atoms in the vertex
    """

    def __init__(self, label, constraints=None):

        """
        :param label: The name of the vertex
        :type label: str
        :param constraints: The constraints of the vertex
        :type constraints: iterable of\
                    :py:class:`pacman.model.constraints.abstract_constraint.AbstractConstraint`
        :raise pacman.exceptions.PacmanInvalidParameterException:
                    * If one of the constraints is not valid
                    * If the number of atoms is less than 1
        """
        AbstractHasConstraints.__init__(self, constraints)
        SimpleLabeledObject.__init__(self, label)
