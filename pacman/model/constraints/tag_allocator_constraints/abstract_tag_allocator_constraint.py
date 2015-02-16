from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass


from pacman.model.constraints.abstract_constraints.abstract_placer_constraint \
    import AbstractPlacerConstraint


@add_metaclass(ABCMeta)
class AbstractTagAllocatorConstraint(AbstractPlacerConstraint):

    def __init__(self):
        AbstractPlacerConstraint.__init__(
            self, "tag allocator constraint")

    def is_placer_constraint(self):
        return True

    @abstractmethod
    def is_tag_allocator_constraint(self):
        """
        helper method for is_instance
        :return:
        """
