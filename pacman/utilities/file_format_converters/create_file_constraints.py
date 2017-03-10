from pacman.model.graphs.abstract_virtual_vertex import AbstractVirtualVertex
from pacman.model.constraints.placer_constraints\
    import PlacerChipAndCoreConstraint, AbstractPlacerConstraint
from pacman import exceptions
from pacman.utilities import utility_calls
from pacman.utilities import constants
from pacman.utilities import file_format_schemas

from spinn_machine.utilities.progress_bar import ProgressBar

import json
import os
import jsonschema


class CreateConstraintsToFile(object):
    """ Creates constraints file from the machine and machine graph
    """

    __slots__ = []

    def __call__(self, machine_graph, machine, file_path):
        """
        :param machine_graph: the machine graph
        :param machine: the machine
        :return:
        """

        progress_bar = ProgressBar(
            machine_graph.n_vertices + 2, "creating json constraints")

        json_constraints_directory_rep = list()
        self._add_monitor_core_reserve(json_constraints_directory_rep)
        progress_bar.update()
        self._add_extra_monitor_cores(json_constraints_directory_rep, machine)
        progress_bar.update()
        vertex_by_id = self._search_graph_for_placement_constraints(
            json_constraints_directory_rep, machine_graph, machine,
            progress_bar)

        file_to_write = open(file_path, "w")
        json.dump(json_constraints_directory_rep, file_to_write)
        file_to_write.close()

        # validate the schema
        constraints_schema_file_path = os.path.join(
            os.path.dirname(file_format_schemas.__file__), "constraints.json"
        )

        # for debug purposes, read schema and validate
        file_to_read = open(constraints_schema_file_path, "r")
        constraints_schema = json.load(file_to_read)
        jsonschema.validate(
            json_constraints_directory_rep, constraints_schema)

        # complete progress bar
        progress_bar.end()

        return file_path, vertex_by_id

    def _search_graph_for_placement_constraints(
            self, json_constraints_dictionary_rep, machine_graph, machine,
            progress_bar):
        vertex_by_id = dict()
        for vertex in machine_graph.vertices:
            vertex_id = str(id(vertex))
            vertex_by_id[vertex_id] = vertex
            for constraint in vertex.constraints:
                self._handle_vertex_constraint(
                    constraint, json_constraints_dictionary_rep, vertex,
                    vertex_id)
                progress_bar.update()
            self._handle_vertex_resources(
                vertex.resources_required, json_constraints_dictionary_rep,
                vertex_id)
            if isinstance(vertex, AbstractVirtualVertex):
                self._handle_virtual_vertex(
                    vertex, vertex_id, json_constraints_dictionary_rep,
                    machine)
        return vertex_by_id

    def _handle_virtual_vertex(
            self, vertex, vertex_id, json_constraints_dictionary_rep, machine):
        route_end_point_constraint = dict()
        virtual_chip_location_constraint = dict()
        json_constraints_dictionary_rep.append(route_end_point_constraint)
        json_constraints_dictionary_rep.append(
            virtual_chip_location_constraint)

        (real_chip_id, direction_id) = \
            self._locate_connected_chip_data(vertex, machine)
        route_end_point_constraint['type'] = "route_endpoint"
        route_end_point_constraint['vertex'] = vertex_id
        route_end_point_constraint['direction'] = constants.EDGES(direction_id)

        virtual_chip_location_constraint["type"] = "location"
        virtual_chip_location_constraint["vertex"] = vertex_id
        virtual_chip_location_constraint["location"] = real_chip_id

    @staticmethod
    def _locate_connected_chip_data(vertex, machine):
        """ Finds the connected virtual chip

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
                "Can't find the real chip this virtual chip is connected to."
                "Please fix and try again.")
        else:
            return ("[{}, {}]".format(router.get_link(link_id).destination_x,
                                      router.get_link(link_id).destination_y),
                    router.get_link(link_id).multicast_default_from)

    @staticmethod
    def _handle_vertex_constraint(
            constraint, json_constraints_dictionary_rep, vertex, vertex_id):
        if not isinstance(vertex, AbstractVirtualVertex):
            if isinstance(constraint, AbstractPlacerConstraint):
                if isinstance(constraint, PlacerChipAndCoreConstraint):
                    chip_loc_constraint = dict()
                    chip_loc_constraint['type'] = "location"
                    chip_loc_constraint['vertex'] = vertex_id
                    chip_loc_constraint['location'] = [
                        constraint.x, constraint.y]
                    json_constraints_dictionary_rep.append(chip_loc_constraint)
                    if constraint.p is not None:
                        chip_loc_constraint = dict()
                        chip_loc_constraint['type'] = "resource"
                        chip_loc_constraint['vertex'] = vertex_id
                        chip_loc_constraint['resource'] = "cores"
                        chip_loc_constraint['range'] = \
                            "[{}, {}]".format(constraint.p, constraint.p + 1)
                        json_constraints_dictionary_rep.append(
                            chip_loc_constraint)
                else:
                    raise exceptions.PacmanConfigurationException(
                        "Converter does not recognise placer constraint {}"
                        .format(constraint))

    @staticmethod
    def _handle_vertex_resources(
            resources_required, json_constraints_dictionary_rep, vertex_id):
        for _ in resources_required.iptags:
            tag_constraint = dict()
            tag_constraint['type'] = "resource"
            tag_constraint['vertex'] = vertex_id
            tag_constraint['resource'] = "iptag"
            tag_constraint['range'] = [0, 1]
            json_constraints_dictionary_rep.append(tag_constraint)
        for _ in resources_required.reverse_iptags:
            tag_constraint = dict()
            tag_constraint['type'] = "resource"
            tag_constraint['vertex'] = vertex_id
            tag_constraint['resource'] = "reverse_iptag"
            tag_constraint['range'] = [0, 1]
            json_constraints_dictionary_rep.append(tag_constraint)

    @staticmethod
    def _add_extra_monitor_cores(json_constraints_dictionary_rep, machine):
        for chip in machine.chips:
            for processor in chip.processors:
                if processor.processor_id != 0 and processor.is_monitor:
                    reserve_monitor = dict()
                    reserve_monitor['type'] = "reserve_resource"
                    reserve_monitor['resource'] = "cores"
                    reserve_monitor['reservation'] = \
                        [processor.processor_id, processor.processor_id + 1]
                    reserve_monitor['location'] = [chip.x, chip.y]
                    json_constraints_dictionary_rep.append(reserve_monitor)

    @staticmethod
    def _add_monitor_core_reserve(json_constraints_dictionary_rep):
        reserve_monitor = dict()
        reserve_monitor['type'] = "reserve_resource"
        reserve_monitor['resource'] = "cores"
        reserve_monitor['reservation'] = [0, 1]
        reserve_monitor['location'] = None
        json_constraints_dictionary_rep.append(reserve_monitor)
