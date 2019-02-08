from .abstract_key_allocator_constraint import AbstractKeyAllocatorConstraint


class ShareKeyConstraint(AbstractKeyAllocatorConstraint):
    """ Constraint to allow the same keys to be allocated to multiple edges\
        via partitions.
    """

    __slots__ = [
        # The set of outgoing partitions to vertices which all share the same\
        # key
        "_other_partitions"
    ]

    def __init__(self, other_partitions):
        """
        :param other_partitions: the other edges which keys are shared with.
        """
        self._other_partitions = other_partitions

    @property
    def other_partitions(self):
        return self._other_partitions
