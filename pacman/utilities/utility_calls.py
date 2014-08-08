from pacman import exceptions
from pacman.model.constraints.abstract_placer_constraint import \
    AbstractPlacerConstraint
import inspect


def locate_constraints_of_type(constraints, constraint_type):
    """locates all constraints of a given type out of a list

    :param constraints: a iterable of
     pacman.model.constraints.AbstractConstraint.AbstractConstraint
    :type constraints: a iterable object
    :param constraint_type: a implementation of a
    pacman.model.constraint.abstract_partitioner_constraint.AbstractPartitionConstraint
    :type constraint_type: a impliemntation of a
    pacman.model.constraint.abstract_partitioner_constraint.AbstractPartitionConstraint
    :return: a list containing only
    pacman.model.constraints.partitioner_maximum_size_constraint constraints
    or a empty list if none exist
    :rtype: iterable object
    :raises None: no known exceptions
    """
    passed_constraints = list()
    subclasses = constraint_type.__subclasses__()
    subclasses.append(constraint_type)
    for constraint in constraints:
        if type(constraint) in subclasses:
            passed_constraints.append(constraint)
    return passed_constraints


def check_algorithm_can_support_constraints(
        object_list, supported_constraints, constraint_check_level):
    """helper method to find out if an algorithum can support all the\
     constraints given the objects its expected to work on

    :param object_list: the lsit of objects the algorithum is expected to work\
    on
    :param supported_constraints: the list of constraints that the algortihum \
    can support
    :param constraint_check_level: where to check from
    :type object_list: iterable of a object
    :type supported_constraints: iterable implimentations of \
    pacamn.model.constraints.abstractconstraint.AbstractConstraint
    :type constraint_check_level: implimentation of \
    pacamn.model.constraints.abstractconstraint.AbstractConstraint
    :return: None
    :rtype: None
    :raise PacmanException: when the algorithum cannot support the constraints \
    demanded of it
    """
    for individual_object in object_list:
        for constraint in individual_object.constraints:
            if constraint in constraint_check_level.__subclasses__():
                located = False
                for supported_constraint in supported_constraints:
                    if type(constraint) == type(supported_constraint):
                        located = True
                if not located:
                    raise exceptions.PacmanException(
                        "the algorithm selected cannot support "
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
                    "contain constraints. Every object must have at least a "
                    "max atoms per core constraint")
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

        #collected them all
        ordered_keys = \
            sorted(rank_to_object_mapping.keys(), key=int, reverse=True)
        ordered_objects = list()
        for ordered_key in ordered_keys:
            object_list = rank_to_object_mapping[ordered_key]
            for current_object in object_list:
                ordered_objects.append(current_object)
        return ordered_objects


def locate_all_subclasses_of(class_to_find_subclasses_of):
    """helper method to locate all the subclasses of an object. Mainly due to \
    interferance of abc meta and the hirarcy structure of python

    :param class_to_find_subclasses_of: the class to find subclasses of
    :type class_to_find_subclasses_of: class
    :return: iterable of its subclasses
    :rtype: iterable of classes
    :raise None: does not raise any known exceptions
    """
    #find all constraints!
    subclass_list = list()
    current_subclass_list = class_to_find_subclasses_of.__subclasses__()
    while len(current_subclass_list) != 0:
        current_class = current_subclass_list[0]
        #todo make this work so it doesnt just return false all the bloody time!!!!
        if not inspect.isabstract(current_class):
            subclass_list.append(current_class)
        current_subclass_list.remove(current_class)
        for new_found_class in current_class.__subclasses__():
            current_subclass_list.append(new_found_class)
    return subclass_list