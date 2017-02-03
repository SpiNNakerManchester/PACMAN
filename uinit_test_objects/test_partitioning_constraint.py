"""
test constraint
"""
from pacman.model.constraints.partitioner_constraints\
    .abstract_partitioner_constraint import AbstractPartitionerConstraint


class NewPartitionerConstraint(AbstractPartitionerConstraint):
    """
    a partitioning constraint that shouldn't be recognised by any algorithm
    """

    def __init__(self, label):
        AbstractPartitionerConstraint.__init__(self, label)

    def is_constraint(self):
        """
        helper method for is_instance

        :return:
        """
        return True

    def is_partitioner_constraint(self):
        """ Determine if this is a partitioner constraint
        """
        return True
