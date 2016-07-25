from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractProvidesIncomingPartitionConstraints(object):
    """ A vertex that can provide constraints for its incoming edge partitions
    """

    @abstractmethod
    def get_incoming_partition_constraints(self, partition):
        """ Get constraints to be added to the given partition

        :param partition: A partition that has an edge that ends at this vertex
        :type partition:\
            :py:class:`pacman.model.graph.abstract_outgoing_edge_partition.AbstractOutgoingEdgePartition`
        :return: A list of constraints
        :rtype: \
            list of\
            :py:class:`pacman.model.constraints.abstract_constraint.AbstractConstraint`
        """
