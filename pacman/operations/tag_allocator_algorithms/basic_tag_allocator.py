from pacman import exceptions
from pacman.model.constraints.tag_allocator_constraints.\
    abstract_tag_allocator_constraint import AbstractTagAllocatorConstraint
from pacman.model.constraints.tag_allocator_constraints.\
    tag_allocator_require_iptag_constraint import \
    TagAllocatorRequireIptagConstraint
from pacman.model.constraints.tag_allocator_constraints.\
    tag_allocator_require_reverse_iptag_constraint import \
    TagAllocatorRequireReverseIptagConstraint
from pacman.model.tag_infos.tag_infos import TagInfos
from pacman.operations.abstract_algorithms.\
    abstract_tag_allocator_algorithm import AbstractTagAllocatorAlgorithm
from pacman.utilities import utility_calls


class BasicTagAllocator(AbstractTagAllocatorAlgorithm):
    """ the basic tag allocator that goes though the boards avilable and applies
    the iptags and reverse iptags as needed.

    """

    def __init__(self, machine):
        AbstractTagAllocatorAlgorithm.__init__(self, machine)
        self._tag_infos = TagInfos()
        self._avilable_tag_ids = \
            self._locate_all_seperate_ethernet_connections()
        self._supported_constraints.append(TagAllocatorRequireIptagConstraint)
        self._supported_constraints.append(
            TagAllocatorRequireReverseIptagConstraint)

    def allocate(self, placements):
        """ entering method when using the tag allocator in situ.
         It calls methods which use the placements to check for taggable
         constraints and first time deals with tags with tag ids and the
         second for tags without tag ids
        :param placements: the placements object from the front end
        :type placements: pacman.model.placements.placements.Placements
        :return: A taginfo object which contains all the iptags and
        reverseiptags used by the spinnaker machine
        :rtype: pacman.model.tag_info.tag_infos.TagInfos
        :raises None: this method does not raise any known exceptions
        """
        self._check_algorithum_supported_constraints(placements)
        self._deal_with_placements(placements, True)
        self._deal_with_placements(placements, False)
        return self._tag_infos

    def allocate_for_constraint(self, taggable_constraint,
                                partitioned_vertex_label):
        """opening method for a placer algorithum to allocate a taggable vertex
        based off its constraint in a one by one mode.

        :param taggable_constraint:the constraint to be considered
        :type taggable_constraint: instance of
        "pacman.model.constraints.abstract_constraints.abstract_taggable_constraint.AbstractTaggableConstraint"
        :param partitioned_vertex_label: the label of the partitioned_vertex to
        which this constraint is associated with.
        :type partitioned_vertex_label: str
        :return None: this method does not return any thing
        :raises None: this method does not raise any known exceptions
        """
        self._handle_tag_constraint(
            taggable_constraint, True, partitioned_vertex_label)
        self._handle_tag_constraint(
            taggable_constraint, False, partitioned_vertex_label)

    def _deal_with_placements(self, placements, for_tags_with_tags):
        """ method that checks though the placements object and locates any
         which contain taggable constraints, if so its then sent to other
         emthods that generate the tag as required. Note that if ignores
         taggable constraints which do not have tag_ids if the
         for_tags_with_tags is set to False and ignores ones with tags when
         for_tags_with_tags is set to True.

        :param placements: the placements object from the front end
        :type placements: pacman.model.placements.placements.Placements
        :param for_tags_with_tags: bool which tells the handle tag constraint
        method to search for a tag if this constraint contains a tag_id or not.
        :type for_tags_with_tags: bool
        :return None: this method does not return anything
        :raises None: this method does not raise any known exceptions
        """
        # iterate though the placements and set tags which have tag ids set
        for placement in placements:
            tag_allocator_constraints = \
                utility_calls.locate_constraints_of_type(
                    placement.subvertex.constraints,
                    AbstractTagAllocatorConstraint)

            # if theres constraints, determine the tag and board address
            if len(tag_allocator_constraints) > 0:
                for tag_allocator_constraint in tag_allocator_constraints:
                    self._handle_tag_constraint(tag_allocator_constraint,
                                                for_tags_with_tags,
                                                placement.subvertex.label)

    def _handle_tag_constraint(self, tag_allocator_constraint,
                               for_tags_with_tags, partitioned_vertex_label):
        """ deals with a specific constraint and builds/locates its tag.
         This method can do nothing if the constraint being considered does not
         contain a tagid and the for_tags_with_tags is set to False.

        :param tag_allocator_constraint: the constraint to be considered
        :param for_tags_with_tags: bool which says if it should be
        considering constraints which have a tag_id or not
        :param partitioned_vertex_label: the label of the partitioned vertex to
        which this constraint is associated
        :type tag_allocator_constraint: instance of
        "pacman.model.constraints.abstract_constraints.abstract_taggable_constraint.AbstractTaggableConstraint"
        :type for_tags_with_tags: bool
        :type partitioned_vertex_label: str
        :return None: this method does not return anything
        :raises PacmanConfigurationException: because two identical reverse
        iptags have been decuded to be needed, yet this cannot be due a
         reversie iptag pointing at one core
        """
        #if dealing with tag this time around, allcoate tag to
        #  constraint and built in iptag objects
        if ((for_tags_with_tags and tag_allocator_constraint.tag_id is not None)
                or (not for_tags_with_tags
                    and tag_allocator_constraint.tag_id is None)):

            # check that a tag has been created for the
            # destination already
            if (isinstance(tag_allocator_constraint,
                           TagAllocatorRequireIptagConstraint)
                    and self._tag_infos.contains_iptag_for(
                        tag_allocator_constraint.port,
                        tag_allocator_constraint.address)):
                self._check_if_iptag_allocated_already(tag_allocator_constraint,
                                                       partitioned_vertex_label)
            elif (isinstance(tag_allocator_constraint,
                             TagAllocatorRequireReverseIptagConstraint)
                    and self._tag_infos.contains_reverse_iptag_for(
                        tag_allocator_constraint.placement_x,
                        tag_allocator_constraint.placement_y,
                        tag_allocator_constraint.placement_p,
                        tag_allocator_constraint.port)):
                raise exceptions.PacmanConfigurationException(
                    "You cant have 2 vertices which have the same reverse "
                    "iptag mapping. This is likely due to a malgination on "
                    "the placement algorithum")
            else:
                tag_id, board_address = \
                    self._check_tag(tag_allocator_constraint.tag_id,
                                    tag_allocator_constraint.board_address)
                #update constraint data
                tag_allocator_constraint.tag_id = tag_id
                tag_allocator_constraint.board_address = board_address
                # sort out tag setting in tag info
                self._set_tag(tag_allocator_constraint, partitioned_vertex_label)

    def _check_if_iptag_allocated_already(
            self, tag_allocator_constraint, partitioned_vertex_label):
        """iterates through the current tags and sees if theres one which
        already meets the constraints requirements, if so then it will use
        that one, otherwise itll create a new one.

        :param tag_allocator_constraint: the constraint to be linked to a tag
        :type tag_allocator_constraint: instance of
        "pacman.model.constraints.abstract_constraints.abstract_taggable_constraint.AbstractTaggableConstraint"
        :param partitioned_vertex_label:
        the label of the partitioned vertex to be linked to this tag
        :type partitioned_vertex_label: str
        :return None: this method does not return anything
        """
        # uses a iptag that already exists for a collection of boards
        iptags = self._tag_infos.get_iptag_for(
            tag_allocator_constraint.port, tag_allocator_constraint.address)

        located_tag_for_board = False
        for iptag in iptags:
            board_address = self._tag_infos.get_board_address_from_tag(iptag)
            if board_address == tag_allocator_constraint.board_address:
                tag_allocator_constraint.board_address = board_address
                tag_allocator_constraint.tag_id = iptag.tag
                located_tag_for_board = True
                #update constraint data
                tag_allocator_constraint.tag_id = iptag.tag
        if not located_tag_for_board:
            tag_id, board_address =\
                self._check_tag(tag_allocator_constraint.tag_id,
                                tag_allocator_constraint.board_address)
            #update constraint data
            tag_allocator_constraint.tag_id = tag_id
            tag_allocator_constraint.board_address = board_address
            # sort out tag setting in tag info
            self._set_tag(tag_allocator_constraint, partitioned_vertex_label)

    def _set_tag(self, constraint, partitioned_vertex_label):
        """ Private method that creates determines what type of tag to create
         based off the type of constraint parameter

        :param constraint: the constraint in question to create a tag from
        :type constraint: a instance of:
        "pacman.model.constraints.abstract_constraints.abstract_taggable_constraint.AbstractTaggableConstraint"
        :return None: this method does not return any thing
        :raises None: this method does not raise an exception
        """
        if isinstance(constraint, TagAllocatorRequireIptagConstraint):
            self._tag_infos.add_iptag(
                port=constraint.port, address=constraint.address,
                tag=constraint.tag_id, board_address=constraint.board_address,
                strip_sdp=constraint.strip_sdp,
                partitioned_vertex_label=partitioned_vertex_label)
        elif isinstance(constraint, TagAllocatorRequireReverseIptagConstraint):
            self._tag_infos.add_reverse_ip_tag(
                port=constraint.port, tag=constraint.tag_id,
                x=constraint.placement_x, y=constraint.placement_y,
                p=constraint.placement_p,
                board_address=constraint.board_address,
                port_num=constraint.port_num,
                partitioned_vertex=partitioned_vertex_label)

    def locate_board_for(self, taggable_constraint, placement_tracker):
        """ overrided method from abstract_taggable_algorithm
        method that a placer can call to deduce the board address of a
         taggablely constraitned partitioned vertex.

        :param taggable_constraint: the taggable constraint
        :type taggable_constraint: instance of:
        "pacman.model.constraints.abstract_constraints.abstract_taggable_constraint.AbstractTaggableConstraint"
        :param placement_tracker: the placement tracker used by the placer
        :type placement_tracker: instance of:
        "pacman.utilities.placement_tracker.PlacementTracker"
        :return: a board address which this constraint can satisfy
        """
        if taggable_constraint.board_address is not None:

            # check that the area code works for the tag allcoation
            if placement_tracker.\
                    ethernet_area_code_has_avilable_cores_left(
                    taggable_constraint.board_address):

                tag, board = \
                    self._check_tag(taggable_constraint.tag_id,
                                    taggable_constraint.board_address,
                                    True, False)
                return board
            else:
                raise exceptions.PacmanPlaceException(
                    "There are no more avilable cores in this ethernet area "
                    "code, therefore this constraint cannot be satisifed :{}:"
                    .format(taggable_constraint))
        else:
            # search though all area codes looking for one which will work

            area_codes = placement_tracker.ethernet_area_codes
            found = False
            board_address = None
            index = 0
            while index < len(area_codes) and not found:
                if placement_tracker.\
                        ethernet_area_code_has_avilable_cores_left(
                        area_codes.keys()[index]):
                    tag, board_address = self._check_tag(
                        taggable_constraint.tag_id,
                        taggable_constraint.board_address, False)

                    # if these are none, then there tag and board didnt
                    # work on this ethernet area code
                    if tag is not None and board_address is not None:
                        found = True
            return board_address

    def _check_tag(self, tag_id, board_address, raise_exceptions=True,
                   remove_tag_id_from_set=True):
        """
        HORRIBLE PIECE OF CODE. This bit does all the comparisions of all the
        boards and locates the tag and board address to allocate to a
        constraint. It can raise errors if the raise_exceptions parameter is set
        to true, and not allocate the tag and board_address (not removed from
        the data structures that track the avilable tags) if the
        remove_tag_id_from_set is set to true.

        NOTE: Attempts to clean this bit of code are damn welcome!!!!

        :param tag_id: the tag id to be used
        :type tag_id: int or None
        :param board_address: the board address to use
        :type board_address: str, or None
        :param raise_exceptions: a bool to state if this methof should raise
        exceptions or not. If its asked not to, and results in a position where
        it shoudl raise an exception, it returns None, None under the
        assumption that higher level calls will understand this.
        :type raise_exceptions: bool
        :param remove_tag_id_from_set: a bool which detemrines if the code
        should allocate a tag and board address or if it should peek under the
        assumption that later it will be asked to allocate it.
        :type remove_tag_id_from_set: bool
        :return: the tag and board_address, or None, None if not possible with
        the parameters
        :raises PacmanConfigurationException: when the raise _exceptions
        param is set to true and either if:
           1. the board address isnt avialble
           2. the tag id for the board you've speifcied is already in use
           3. there was no board address to which this tag id was free
           4. the board has no free tags
           5. the code has got into a strange state!
        """
        #check that board address is a connected ethernet
        if (board_address is not None
                and board_address not in self._avilable_tag_ids.keys()):
            if raise_exceptions:
                raise exceptions.PacmanConfigurationException(
                    "This board address is not one of the listed connected"
                    "ethernets, please fix this and try again")
            else:
                return None, None

        # fixed in both board and tag
        if tag_id is not None and board_address is not None:
            if tag_id in self._avilable_tag_ids[board_address]:
                if remove_tag_id_from_set:
                    self._avilable_tag_ids[board_address].remove(tag_id)
                return tag_id, board_address
            else:
                # if your expected to raise exceptions do so, otherwise
                # return None None.
                if raise_exceptions:
                    raise exceptions.PacmanConfigurationException(
                        "This tag has already been used by some other iptag, "
                        "please correct this and try again")
                else:
                    return None, None

        # fixed in tag id but not in board ( not sure if this is needed )
        elif tag_id is not None and board_address is None:
            key_index = 0
            while key_index < len(self._avilable_tag_ids.keys()):
                board_address = self._avilable_tag_ids.keys()[key_index]
                if tag_id in self._avilable_tag_ids[board_address]:
                    if remove_tag_id_from_set:
                        self._avilable_tag_ids[board_address].remove(tag_id)
                    return tag_id, board_address
                key_index += 1
            if raise_exceptions:
                raise exceptions.PacmanConfigurationException(
                    "Could not locate any connection which has this tag free, "
                    "please rectify and try again")
            else:
                return None, None

        # none fixed tag id and fixed board
        elif tag_id is None and board_address is not None:
            if len(self._avilable_tag_ids[board_address]) == 0:
                if raise_exceptions:
                    raise exceptions.PacmanConfigurationException(
                        "This board no longer has any tags left, "
                        "please rectify and try again")
                else:
                    return None, None
            else:
                tag_id = self._avilable_tag_ids[board_address].pop()
                if not remove_tag_id_from_set:
                    self._avilable_tag_ids[board_address].add(tag_id)
                return tag_id, board_address

        # no fixed tag nor fixed board (easiest)
        elif tag_id is None and board_address is None:
            key_index = 0
            while key_index < len(self._avilable_tag_ids.keys()):
                board_address = self._avilable_tag_ids.keys()[key_index]
                if len(self._avilable_tag_ids[board_address]) != 0:
                    tag_id = self._avilable_tag_ids[board_address].pop()
                    if not remove_tag_id_from_set:
                        self._avilable_tag_ids[board_address].add(tag_id)
                    return tag_id, board_address
                key_index += 1
            if raise_exceptions:
                raise exceptions.PacmanConfigurationException(
                    "There is no more tags avilable, therefore cannot allocate"
                    " a tag, please rectify and try again")
            else:
                return None, None
        else:
            if raise_exceptions:
                raise exceptions.PacmanConfigurationException(
                    "dont know how i got here. But theres some form of tag "
                    "configuration that i dont recongise. Please rectify and "
                    "try again.")
            else:
                return None, None

    def is_tag_allocator(self):
        """ helper method for is_instance
        :return:
        """
        return True