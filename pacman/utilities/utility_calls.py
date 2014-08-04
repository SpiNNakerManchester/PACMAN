from pacman import exceptions
from pacman.model.constraints.abstract_placer_constraint import \
    AbstractPlacerConstraint


def locate_constraints_of_type(constraints, constraint_type):
    """locates all constraints of a given type out of a list

    :param constraints: a iterable of
     pacman.model.constraints.AbstractConstraint.AbstractConstraint
    :type constraints: a iterable object
    :param constraint_type: a impliemntation of a
    pacman.model.constraint.abstract_partitioner_constrant.AbstractpartitionConstraint
    :type constraint_type: a impliemntation of a
    pacman.model.constraint.abstract_partitioner_constrant.AbstractpartitionConstraint
    :return: a list containing only
    pacman.model.constraints.partitioner_maximum_size_constraint constraints
    or a empty list if none exist
    :rtype: iterable object
    :raises None: no known exceptions
    """
    passed_constraints = list()
    subclasses = constraint_type.__subclasses__()
    subclasses.append(constraint_type)
    for constrant in constraints:
        if type(constrant) in subclasses:
            passed_constraints.append(constrant)
    return passed_constraints


def check_algorithum_can_support_constraints(
        object_list, supported_constraints, constraint_check_level):
    for individual_object in object_list:
        for constraint in individual_object.constraints:
            if constraint in constraint_check_level.__subclasses__():
                located = False
                for supported_constraint in supported_constraints:
                    if type(constraint) == type(supported_constraint):
                        located = True
                if not located:
                    raise exceptions.PacmanPartitionException(
                        "the algorithum selected cannot support "
                        "the constraint '{}', which has been "
                        "placed on vertex labelled {}"
                        .format(constraint, individual_object.label))


def sort_objects_by_constraint_authority(objects):
        """helper method for all placers. \
        It takes the subverts of a subgraph and orders them into a list with a\
        order based off rank on the constraint \
        NOT TO BE CALLED OUTSIDE IMPLEMTATIONS OF THIS CLASS
        :param objects: The objects to be sorted. need to have a constraints
        :type objects: iterable of soem object with constraints
        :return: A list of ordered objects
        :rtype: list of objects
        :raise None: this method does not raise any known exceptions
        """
        rank_to_object_mapping = dict()
        for current_object in objects:
            if not hasattr(current_object, "constraints"):
                raise exceptions.PacmanConfigurationException(
                    "the object given to the "
                    "sort_objects_by_constraint_authority method does not "
                    "contain constraints")
            max_rank_so_far = 0
            for constraint in current_object.constraints:
                #only store ranks for placer contraints and ones that are better
                #than already seen
                if (isinstance(constraint, AbstractPlacerConstraint) and
                        constraint.rank >= max_rank_so_far):
                    max_rank_so_far = constraint.rank
            if not max_rank_so_far in rank_to_object_mapping.keys():
                rank_to_object_mapping[max_rank_so_far] = list()
            rank_to_object_mapping[max_rank_so_far].append(current_object)

        ordered_keys = \
            sorted(rank_to_object_mapping.keys(), key=int, reverse=True)
        ordered_objects = list()
        for ordered_key in ordered_keys:
            object_list = rank_to_object_mapping[ordered_key]
            for current_object in object_list:
                ordered_objects.append(current_object)
        return ordered_objects