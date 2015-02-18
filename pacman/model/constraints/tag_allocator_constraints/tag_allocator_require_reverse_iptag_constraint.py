import sys
from pacman.model.constraints.tag_allocator_constraints.\
    abstract_tag_allocator_constraint import \
    AbstractTagAllocatorConstraint


class TagAllocatorRequireReverseIptagConstraint(AbstractTagAllocatorConstraint):

    def __init__(self, tag_id, board_address, port_num, port, placement_x=None,
                 placement_y=None, placement_p=None):
        AbstractTagAllocatorConstraint.__init__(self, board_address, port,
                                                tag_id)
        self._placement_x = placement_x
        self._placement_y = placement_y
        self._placement_p = placement_p
        self._port_num = port_num

    @property
    def port_num(self):
        return self._port_num

    @property
    def placement_x(self):
        return self._placement_x

    @property
    def placement_y(self):
        return self._placement_y

    @property
    def placement_p(self):
        return self._placement_p

    @placement_p.setter
    def placement_p(self, new_value):
        self._placement_p = new_value

    @placement_x.setter
    def placement_x(self, new_value):
        self._placement_x = new_value

    @placement_y.setter
    def placement_y(self, new_value):
        self._placement_y = new_value

    def is_placer_constraint(self):
        return True

    def is_tag_allocator_constraint(self):
        return True

    def rank(self):
        return sys.maxint - 4