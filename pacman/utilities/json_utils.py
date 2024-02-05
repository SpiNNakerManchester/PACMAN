# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Miscellaneous minor functions for converting between JSON and Python objects.
"""

import json
import gzip
from typing import cast, List, Optional, Union

from spinn_utilities.typing.json import JsonArray, JsonObject

from pacman.data import PacmanDataView
from pacman.model.graphs.application import (
    ApplicationGraph, ApplicationVertex)
from pacman.model.graphs.machine import MachineVertex, SimpleMachineVertex
from pacman.model.placements.placement import Placement
from pacman.model.resources import (
    IPtagResource, ReverseIPtagResource, VariableSDRAM)
from pacman.model.routing_info import BaseKeyAndMask


def json_to_object(json_object: Union[str, JsonObject]) -> JsonObject:
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


def key_mask_to_json(key_mask: BaseKeyAndMask) -> JsonObject:
    """
    Converts a BaseKeyAndMask into json

    :param BaseKeyAndMask key_mask:
    :rtype: dict(str, object)
    """
    try:
        json_object: JsonObject = dict()
        json_object["key"] = key_mask.key
        json_object["mask"] = key_mask.mask
    except Exception as ex:  # pylint: disable=broad-except
        json_object["exception"] = str(ex)
    return json_object


def iptag_resource_to_json(iptag: IPtagResource) -> JsonObject:
    """
    Converts an iptag to json

    :param IPtagResource iptag:
    :rtype: dict(str, object)
    """
    json_dict: JsonObject = dict()
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


def iptag_resource_from_json(json_dict: JsonObject) -> IPtagResource:
    """
    Creates an iptag from json

    :param dict(str, object) json_dict:
    :rtype: IPtagResource
    """
    return IPtagResource(
        cast(str, json_dict["ip_address"]), cast(int, json_dict.get("port")),
        cast(bool, json_dict["strip_sdp"]), cast(int, json_dict.get("tag")),
        cast(str, json_dict["traffic_identifier"]))


def iptag_resources_to_json(iptags: List[IPtagResource]) -> JsonArray:
    """
    Converts a list of iptags to json.

    :param list(IPtagResource) iptags:
    :rtype: list
    """
    json_list: JsonArray = []
    for iptag in iptags:
        json_list.append(iptag_resource_to_json(iptag))
    return json_list


def iptag_resources_from_json(
        json_list: List[JsonObject]) -> List[IPtagResource]:
    """
    Creates a list of iptags from json.

    :param list(dict(str, object)) json_list:
    :rtype: list(IPtagResource)
    """
    iptags = []
    for json_dict in json_list:
        iptags.append(iptag_resource_from_json(json_dict))
    return iptags


def reverse_iptag_to_json(iptag: ReverseIPtagResource) -> JsonObject:
    """
    Converts a reverse iptag to json

    :param ReverseIPtagResource iptag:
    :rtype: dict(object)
    """
    json_dict: JsonObject = dict()
    try:
        if iptag.port is not None:
            json_dict["port"] = iptag.port
        json_dict["sdp_port"] = iptag.sdp_port
        if iptag.tag is not None:
            json_dict["tag"] = iptag.tag
    except Exception as ex:  # pylint: disable=broad-except
        json_dict["exception"] = str(ex)
    return json_dict


def reverse_iptag_from_json(json_dict: JsonObject) -> ReverseIPtagResource:
    """
    Creates a ReverseIPtagResource based on json

    :param dict(str, object) json_dict:
    :rtype: ReverseIPtagResource
    """
    port = cast(int, json_dict.get("port"))
    sdp_port = cast(int, json_dict["sdp_port"])
    tag = cast(int, json_dict.get("tag"))
    return ReverseIPtagResource(port, sdp_port, tag)


def reverse_iptags_to_json(iptags: List[ReverseIPtagResource]) -> JsonArray:
    """
    Converts a list of reverse iptags to json

    :param list(ReverseIPtagResource) iptags:
    :rtype: list
    """
    json_list: JsonArray = []
    for iptag in iptags:
        json_list.append(reverse_iptag_to_json(iptag))
    return json_list


def reverse_iptags_from_json(
        json_list: List[JsonObject]) -> List[ReverseIPtagResource]:
    """
    Creates a list of ReverseIPtagResource from json

    :param list json_list:
    :type: list(ReverseIPtagResource)
    """
    iptags = []
    for json_dict in json_list:
        iptags.append(reverse_iptag_from_json(json_dict))
    return iptags


def vertex_to_json(vertex: MachineVertex) -> JsonObject:
    """
    Converts a Machine Vertex to json.

    :param MachineVertex vertex:
    :rtype: dict(str, object)
    """
    json_dict: JsonObject = dict()
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


def vertex_from_json(json_dict: JsonObject) -> SimpleMachineVertex:
    """
    Creates a simple Vertex based on the json

    :param dict(str, object) json_dict:
    :rtype:  SimpleMachineVertex
    """
    sdram = VariableSDRAM(
        cast(int, json_dict["fixed_sdram"]),
        cast(float, json_dict["per_timestep_sdram"]))
    iptags = iptag_resources_from_json(json_dict["iptags"])
    reverse_iptags = reverse_iptags_from_json(json_dict["reverse_iptags"])
    return SimpleMachineVertex(
        sdram=sdram, label=json_dict["label"], iptags=iptags,
        reverse_iptags=reverse_iptags)


def placement_to_json(placement: Placement) -> JsonObject:
    """
    Converts a Placement to json

    :param Placement placement:
    :rtype: dict(str, object)
    """
    json_dict: JsonObject = dict()
    try:
        json_dict["vertex_label"] = placement.vertex.label
        json_dict["x"] = placement.x
        json_dict["y"] = placement.y
        json_dict["p"] = placement.p
    except Exception as ex:  # pylint: disable=broad-except
        json_dict["exception"] = str(ex)
    return json_dict


def placements_to_json() -> JsonArray:
    """
    Gets a json description of the placements (held in DataView)
    """
    json_list: JsonArray = []
    for placement in PacmanDataView.iterate_placemements():
        json_list.append(placement_to_json(placement))
    return json_list


def placement_from_json(json_dict: JsonObject) -> Placement:
    """
    Gets a Placement based on the json.

    :param dict(str, object) json_dict:
    :param graph: Application Graph (if used)
    :type graph:  ApplicationGraph or None
    :rtype: Placement
    """
    vertex = SimpleMachineVertex(None, cast(str, json_dict["vertex_label"]))
    return Placement(
        vertex, int(json_dict["x"]), int(json_dict["y"]), int(json_dict["p"]))
