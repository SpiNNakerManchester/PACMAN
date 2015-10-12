"""
 creates constraitns file from the machine adn partitioend graph
"""
from pacman.model.abstract_classes.abstract_virtual_vertex import \
    AbstractVirtualVertex
from pacman.model.constraints.abstract_constraints.\
    abstract_key_allocator_constraint import \
    AbstractKeyAllocatorConstraint
from pacman.model.constraints.abstract_constraints.\
    abstract_placer_constraint import AbstractPlacerConstraint
from pacman.model.constraints.abstract_constraints.\
    abstract_tag_allocator_constraint import AbstractTagAllocatorConstraint
from pacman.model.constraints.key_allocator_constraints.\
    key_allocator_contiguous_range_constraint import \
    KeyAllocatorContiguousRangeContraint
from pacman.model.constraints.key_allocator_constraints.\
    key_allocator_fixed_key_and_mask_constraint import \
    KeyAllocatorFixedKeyAndMaskConstraint
from pacman.model.constraints.key_allocator_constraints.\
    key_allocator_fixed_mask_constraint import KeyAllocatorFixedMaskConstraint
from pacman.model.constraints.placer_constraints.\
    placer_chip_and_core_constraint import PlacerChipAndCoreConstraint
from pacman.model.constraints.tag_allocator_constraints.\
    tag_allocator_require_iptag_constraint import \
    TagAllocatorRequireIptagConstraint
from pacman.model.constraints.tag_allocator_constraints.\
    tag_allocator_require_reverse_iptag_constraint import \
    TagAllocatorRequireReverseIptagConstraint
from pacman import exceptions
from pacman.utilities import utility_calls
from pacman.utilities import constants
from pacman.utilities import file_format_schemas
from pacman.utilities.utility_objs.progress_bar import ProgressBar

import json
import os
import jsonschema


class CreateConstraintsToFile(object):
    """
     creates constraitns file from the machine adn partitioend graph
    """

    def __call__(self, partitioned_graph, machine, file_path):
        """
        tqakes a partitioned graph, machine and file path and creates a
        constraints.json file
        :param partitioned_graph: the partitioned graph
        :param machine: the machine
        :return:
        """

        progress_bar = ProgressBar(
            (len(partitioned_graph.subvertices) +
             len(partitioned_graph.subedges)) + 2,
            "creating json constraints")

        json_constraints_dictory_rep = list()
        self._add_monitor_core_reserve(json_constraints_dictory_rep)
        progress_bar.update()
        self._add_extra_monitor_cores(json_constraints_dictory_rep, machine)
        progress_bar.update()
        self._search_graph_for_placement_constraints(
            json_constraints_dictory_rep, partitioned_graph, machine,
            progress_bar)

        file_to_write = open(file_path, "w")
        json.dump(json_constraints_dictory_rep, file_to_write)
        file_to_write.close()

        # validate the schema
        partitioned_graph_schema_file_path = os.path.join(
            os.path.dirname(file_format_schemas.__file__), "constraints.json"
        )

        # for debug purposes, read schema and validate
        file_to_read = open(partitioned_graph_schema_file_path, "r")
        partitioned_graph_schema = json.load(file_to_read)
        jsonschema.validate(
            json_constraints_dictory_rep, partitioned_graph_schema)

        # complete progress bar
        progress_bar.end()

        return {'constraints': file_path}

    def _search_graph_for_placement_constraints(
            self, json_constraints_dictory_rep, partitioned_graph, machine,
            progress_bar):
        for vertex in partitioned_graph.subvertices:
            for constraint in vertex.constraints:
                self._handle_vertex_constraint(
                    constraint, json_constraints_dictory_rep, vertex)
                progress_bar.update()
            if isinstance(vertex, AbstractVirtualVertex):
                self._handle_virtual_vertex(
                    vertex, json_constraints_dictory_rep, machine)

        for edge in partitioned_graph.subedges:
            for constraint in edge.constraints:
                progress_bar.update()
                #self._handle_edge_constraint(
                #    constraint, json_constraints_dictory_rep, edge

    def _handle_virtual_vertex(self, vertex, json_constraints_dictory_rep,
                               machine):
        route_end_point_constraint = dict()
        virtual_chip_location_constraint = dict()
        json_constraints_dictory_rep.append(route_end_point_constraint)
        json_constraints_dictory_rep.append(virtual_chip_location_constraint)

        (real_chip_id, direction_id) = \
            self._locate_connected_chip_data(vertex, machine)
        route_end_point_constraint['type'] = "route_endpoint"
        route_end_point_constraint['vertex'] = vertex.label
        route_end_point_constraint['direction'] = constants.EDGES(direction_id)

        virtual_chip_location_constraint["type"] = "location"
        virtual_chip_location_constraint["vertex"] = vertex.label
        virtual_chip_location_constraint["location"] = real_chip_id

    @staticmethod
    def _locate_connected_chip_data(vertex, machine):
        """
        searches and fnds the connected virutal chip
        :param vertex:
        :param machine:
        :return:
        """
        # locate the chip from the placement constraint
        placement_constraint = utility_calls.locate_constraints_of_type(
            vertex.constraints, PlacerChipAndCoreConstraint)
        router = machine.get_chip_at(
            placement_constraint.x, placement_constraint.y).router
        found_link = False
        link_id = 0
        while not found_link or link_id < 5:
            if router.is_link(link_id):
                found_link = True
            else:
                link_id += 1
        if not found_link:
            raise exceptions.PacmanConfigurationException(
                "Cant find the real chip this virutal chip is connected to."
                "Please fix and try again.")
        else:
            return ("[{}, {}]".format(router.get_link(link_id).destination_x,
                                      router.get_link(link_id).destination_y),
                    router.get_link(link_id).multicast_default_from)

    @staticmethod
    def _handle_vertex_constraint(
            constraint, json_constraints_dictory_rep, vertex):
        if not isinstance(vertex, AbstractVirtualVertex):
            if (isinstance(constraint, AbstractPlacerConstraint)
                    and not isinstance(constraint,
                                       AbstractTagAllocatorConstraint)):
                chip_loc_constraint = dict()
                chip_loc_constraint['type'] = "location"
                chip_loc_constraint['vertex'] = str(id(vertex))
                chip_loc_constraint['location'] = [constraint.x, constraint.y]
                json_constraints_dictory_rep.append(chip_loc_constraint)
            if (isinstance(constraint, PlacerChipAndCoreConstraint)
                    and constraint.p is not None):
                chip_loc_constraint = dict()
                chip_loc_constraint['type'] = "resource"
                chip_loc_constraint['vertex'] = str(id(vertex))
                chip_loc_constraint['resource'] = "cores"
                chip_loc_constraint['range'] = \
                    "[{}, {}]".format(constraint.p, constraint.p + 1)
                json_constraints_dictory_rep.append(chip_loc_constraint)
        if isinstance(constraint, AbstractTagAllocatorConstraint):
            tag_constraint = dict()
            tag_constraint['type'] = "resource"
            tag_constraint['vertex'] = str(id(vertex))
            if isinstance(constraint,
                          TagAllocatorRequireIptagConstraint):
                tag_constraint['resource'] = "iptag"
                tag_constraint['range'] = [0, 1]
            elif isinstance(constraint,
                            TagAllocatorRequireReverseIptagConstraint):
                tag_constraint['resource'] = "reverse_iptag"
                tag_constraint['range'] = [0, 1]
            else:
                raise exceptions.PacmanConfigurationException(
                    "Converter does not regonsise this tag constraint."
                    "Please update this algorithum and try again.")
            json_constraints_dictory_rep.append(tag_constraint)
                    
    @staticmethod
    def _handle_edge_constraint(
            constraint, json_constraints_dictory_rep, edge):
        if isinstance(constraint, AbstractKeyAllocatorConstraint):
            if isinstance(constraint,
                          KeyAllocatorContiguousRangeContraint):
                key_constraint = dict()
                key_constraint['type'] = "reserve_resource"
                key_constraint['edge'] = str(id(edge))
                key_constraint['resource'] = "keys"
                key_constraint['restriction'] = "continious_range"
                json_constraints_dictory_rep.append(key_constraint)
            if isinstance(constraint,
                          KeyAllocatorFixedKeyAndMaskConstraint):
                key_constraint = dict()
                key_constraint['type'] = "reserve_resource"
                key_constraint['edge'] = str(id(edge))
                key_constraint['resource'] = "keys"
                key_constraint['restriction'] = "[key, mask]"
                constraint_string = "["
                for key_and_mask in constraint.keys_and_masks:
                    constraint_string += "[{}, {}]"\
                        .format(key_and_mask.key, key_and_mask.mask)
                constraint_string += "]"
                key_constraint['key'] = constraint_string
                json_constraints_dictory_rep.append(key_constraint)
            if isinstance(constraint,
                          KeyAllocatorFixedMaskConstraint):
                key_constraint = dict()
                key_constraint['type'] = "reserve_resource"
                key_constraint['edge'] = str(id(edge))
                key_constraint['resource'] = "keys"
                key_constraint['restriction'] = "[mask]"
                key_constraint['mask'] = constraint.mask
                json_constraints_dictory_rep.append(key_constraint)

    @staticmethod
    def _add_extra_monitor_cores(json_constraints_dictory_rep, machine):
        for chip in machine.chips:
            for processor in chip.processors:
                if processor.processor_id != 0 and processor.is_monitor:
                    reserve_monitor = dict()
                    reserve_monitor['type'] = "reserve_resource"
                    reserve_monitor['resource'] = "cores"
                    reserve_monitor['reservation'] = \
                        [processor.processor_id, processor.processor_id + 1]
                    reserve_monitor['location'] = [chip.x, chip.y]
                    json_constraints_dictory_rep.append(reserve_monitor)

    @staticmethod
    def _add_monitor_core_reserve(json_constraints_dictory_rep):
        reserve_monitor = dict()
        reserve_monitor['type'] = "reserve_resource"
        reserve_monitor['resource'] = "cores"
        reserve_monitor['reservation'] = [0, 1]
        reserve_monitor['location'] = None
        json_constraints_dictory_rep.append(reserve_monitor)