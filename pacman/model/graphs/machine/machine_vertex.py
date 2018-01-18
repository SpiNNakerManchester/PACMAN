from six import add_metaclass

from pacman.model.graphs import AbstractVertex
from pacman.model.graphs.common import ConstrainedObject
from pacman.model.decorators import overrides

from spinn_utilities.abstract_base import AbstractBase, abstractproperty


@add_metaclass(AbstractBase)
class MachineVertex(ConstrainedObject, AbstractVertex):
    """ A machine graph vertex
    """

    __slots__ = ["_label"]

    def __init__(self, label=None, constraints=None):
        """
        :param label: The optional name of the vertex
        :type label: str
        :param constraints: The optional initial constraints of the vertex
        :type constraints: \
            iterable of\
            :py:class:`pacman.model.constraints.AbstractConstraint`
        :raise pacman.exceptions.PacmanInvalidParameterException:
            * If one of the constraints is not valid
        """
        super(MachineVertex, self).__init__(constraints)
        self._label = label

    @property
    @overrides(AbstractVertex.label)
    def label(self):
        return self._label

    def __str__(self):
        _l = self.label
        return self.__repr__() if _l is None else _l

    def __repr__(self):
        return "MachineVertex(label={}, constraints={}".format(
            self.label, self.constraints)

    @abstractproperty
    def resources_required(self):
        """ The resources required by the vertex

        :rtype:\
            :py:class:`pacman.model.resources.ResourceContainer`
        """
