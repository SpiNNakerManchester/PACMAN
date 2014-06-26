__author__ = 'daviess'

from pacman.structures.constraints.abstract_constraint import AbstractConstraint


class AbstractRouterConstraint(AbstractConstraint):
    """
    Object which is inherited by every constraint class\
    related to the router algorithm
    """
    
    def __init__(self):
        """
        
        :return: the router constraint object just created
        :rtype: pacman.constraints.abstract_router_constraint.AbstractRouterConstraint
        :raise None: Raises no known exceptions
        """
        pass
