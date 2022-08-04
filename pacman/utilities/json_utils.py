# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Miscellaneous minor functions for converting between JSON and Python objects.
"""

import json
import gzip
from pacman.data import PacmanDataView
from pacman.model.resources import (
    IPtagResource, ReverseIPtagResource, VariableSDRAM)
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.model.placements.placement import Placement


def json_to_object(json_object):
    """
    Makes sure this is a JSON object reading in a file if required

    :param json_object: Either a JSON Object or a string pointing to a file
    :type json_object: dict or list or str
    :return: a JSON object
    :rtype: dict or list
    """
    if isinstance(json_object, str):
        if json_object.endswith(".gz"):
            with gzip.open(json_object) as j_file:
                return json.load(j_file)
        else:
            with open(json_object, encoding="utf-8") as j_file:
                return json.load(j_file)
    return json_object


def key_mask_to_json(key_mask):
    try:
        json_object = dict()
        json_object["key"] = key_mask.key
        json_object["mask"] = key_mask.mask
    except Exception as ex:  # pylint: disable=broad-except
        json_object["exception"] = str(ex)
    return json_object


def iptag_resource_to_json(iptag):
    json_dict = dict()
    try:
        json_dict["ip_address"] = iptag.ip_address
        if iptag.port is not None:
            json_dict["port"] = iptag.port
        json_dict["strip_sdp"] = iptag.strip_sdp
        if iptag.tag is not None:
            json_dict["tag"] = iptag.tag
        json_dict["traffic_identifier"] = iptag.traffic_identifier
    except Exception as ex:  # pylint: disable=broad-except
        json_dict["exception"] = str(ex)
    return json_dict


def iptag_resource_from_json(json_dict):
    port = json_dict.get("port")
    tag = json_dict.get("tag")
    return IPtagResource(
        json_dict["ip_address"], port, json_dict["strip_sdp"], tag,
        json_dict["traffic_identifier"])


def iptag_resources_to_json(iptags):
    json_list = []
    for iptag in iptags:
        json_list.append(iptag_resource_to_json(iptag))
    return json_list


def iptag_resources_from_json(json_list):
    iptags = []
    for json_dict in json_list:
        iptags.append(iptag_resource_from_json(json_dict))
    return iptags


def reverse_iptag_to_json(iptag):
    json_dict = dict()
    try:
        if iptag.port is not None:
            json_dict["port"] = iptag.port
        json_dict["sdp_port"] = iptag.sdp_port
        if iptag.tag is not None:
            json_dict["tag"] = iptag.tag
    except Exception as ex:  # pylint: disable=broad-except
        json_dict["exception"] = str(ex)
    return json_dict


def reverse_iptag_from_json(json_dict):
    port = json_dict.get("port")
    sdp_port = json_dict["sdp_port"]
    tag = json_dict.get("tag")
    return ReverseIPtagResource(port, sdp_port, tag)


def reverse_iptags_to_json(iptags):
    json_list = []
    for iptag in iptags:
        json_list.append(reverse_iptag_to_json(iptag))
    return json_list


def reverse_iptags_from_json(json_list):
    iptags = []
    for json_dict in json_list:
        iptags.append(reverse_iptag_from_json(json_dict))
    return iptags


def vertex_to_json(vertex):
    json_dict = dict()
    try:
        json_dict["class"] = vertex.__class__.__name__
        json_dict["label"] = vertex.label
        json_dict["fixed_sdram"] = int(vertex.sdram_required.fixed)
        json_dict["per_timestep_sdram"] = int(
            vertex.sdram_required.per_timestep)
        json_dict["iptags"] = iptag_resources_to_json(vertex.iptags)
        json_dict["reverse_iptags"] = reverse_iptags_to_json(
            vertex.reverse_iptags)
    except Exception as ex:  # pylint: disable=broad-except
        json_dict["exception"] = str(ex)
    return json_dict


def vertex_from_json(json_dict):
    sdram = VariableSDRAM(
        json_dict["fixed_sdram"], json_dict["per_timestep_sdram"])
    iptags = iptag_resources_from_json(json_dict["iptags"])
    reverse_iptags = reverse_iptags_from_json(json_dict["reverse_iptags"])
    return SimpleMachineVertex(
        sdram=sdram, label=json_dict["label"], iptags=iptags,
        reverse_iptags=reverse_iptags)


def vertex_lookup(label, graph=None):
    if graph:
        return graph.vertex_by_label(label)
    return SimpleMachineVertex(None, label)


def placement_to_json(placement):
    json_dict = dict()
    try:
        json_dict["vertex_label"] = placement.vertex.label
        json_dict["x"] = placement.x
        json_dict["y"] = placement.y
        json_dict["p"] = placement.p
    except Exception as ex:  # pylint: disable=broad-except
        json_dict["exception"] = str(ex)
    return json_dict


def placements_to_json():
    json_list = []
    for placement in PacmanDataView.iterate_placemements():
        json_list.append(placement_to_json(placement))
    return json_list


def placement_from_json(json_dict, graph=None):
    vertex = vertex_lookup(json_dict["vertex_label"], graph)
    return Placement(
        vertex, int(json_dict["x"]), int(json_dict["y"]), int(json_dict["p"]))
