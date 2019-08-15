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
try:
    from collections.abc import OrderedDict
except ImportError:
    from collections import OrderedDict
import json
import gzip
from pacman.model.constraints.key_allocator_constraints import (
    ContiguousKeyRangeContraint,
    FixedKeyAndMaskConstraint, FixedMaskConstraint,
    ShareKeyConstraint)
from pacman.model.constraints.placer_constraints import (
    BoardConstraint, ChipAndCoreConstraint, RadialPlacementFromChipConstraint,
    SameChipAsConstraint)
from pacman.model.constraints.partitioner_constraints import (
    MaxVertexAtomsConstraint, SameAtomsAsVertexConstraint,
    FixedVertexAtomsConstraint)
from pacman.model.resources import (
    CPUCyclesPerTickResource, DTCMResource, IPtagResource, ResourceContainer,
    VariableSDRAM)
from pacman.model.routing_info import BaseKeyAndMask
from pacman.model.graphs.machine import SimpleMachineVertex


def json_to_object(json_object):
    if isinstance(json_object, str):
        if json_object.endswith(".gz"):
            with gzip.open(json_object) as j_file:
                return json.load(j_file)
        else:
            with open(json_object) as j_file:
                return json.load(j_file)
    return json_object

# TODO ShareKeyConstraint
def constraint_to_json(constraint):
    json_dict = OrderedDict()
    try:
        json_dict["class"] = constraint.__class__.__name__
        if isinstance(constraint, BoardConstraint):
            json_dict["board_address"] = constraint.board_address
        elif isinstance(constraint, (
                ChipAndCoreConstraint, RadialPlacementFromChipConstraint)):
            json_dict["x"] = constraint.x
            json_dict["y"] = constraint.y
            if isinstance(constraint, ChipAndCoreConstraint):
                if constraint.p is not None:
                    json_dict["p"] = constraint.p
        elif isinstance(constraint,
                        (SameChipAsConstraint, SameAtomsAsVertexConstraint)):
            json_dict["vertex"] = constraint.vertex.label
        elif isinstance(constraint,
                        (FixedVertexAtomsConstraint, MaxVertexAtomsConstraint)):
            json_dict["size"] = constraint.size
        elif isinstance(constraint, FixedKeyAndMaskConstraint):
            json_dict["keys_and_masks"] = key_masks_to_json(
                constraint.keys_and_masks)
            if constraint.key_list_function:
                json_dict["key_list_function"] = str(
                    constraint.key_list_function)
        elif isinstance(constraint, FixedMaskConstraint):
            json_dict["mask"] = constraint.mask
        elif isinstance(constraint, "ContiguousKeyRangeContraint"):
             # No extra parameters
            pass
        else:
            # Oops an unexpected class
            # Classes Not covered include
            # FixedKeyFieldConstraint
            # FlexiKeyFieldConstraint
            json_dict["str"] = str(constraint)
            json_dict["repr"] = repr(constraint)
    except Exception as ex:
        json_dict["exception"] = str(ex)
    return json_dict


def constraint_from_json(json_dict):
    if json_dict["class"] == "BoardConstraint":
        return BoardConstraint(json_dict["board_address"])
    if json_dict["class"] == "ChipAndCoreConstraint":
        if "p" in json_dict:
            p = json_dict["p"]
        else:
            p = None
        return ChipAndCoreConstraint(json_dict["x"], json_dict["y"], p)
    if json_dict["class"] == "ContiguousKeyRangeContraint":
        return ContiguousKeyRangeContraint()
    if json_dict["class"] == "FixedKeyAndMaskConstraint":
        if "key_list_function" in json_dict:
            raise NotImplementedError(
                "key_list_function {}".format(json_dict["key_list_function"]))
        return FixedKeyAndMaskConstraint(
            key_masks_from_json(json_dict["keys_and_masks"]))
    if json_dict["class"] == "FixedMaskConstraint":
        return FixedMaskConstraint(json_dict["mask"])
    if json_dict["class"] == "FixedVertexAtomsConstraint":
        return FixedVertexAtomsConstraint(json_dict["size"])
    if json_dict["class"] == "MaxVertexAtomsConstraint":
        return MaxVertexAtomsConstraint(json_dict["size"])
    if json_dict["class"] == "RadialPlacementFromChipConstraint":
        return RadialPlacementFromChipConstraint(
            json_dict["x"], json_dict["y"])
    if json_dict["class"] == "SameChipAsConstraint":
        return SameChipAsConstraint(vertex_lookup(json_dict["vertex"]))
    if json_dict["class"] == "SameAtomsAsVertexConstraint":
        return SameAtomsAsVertexConstraint(
            vertex_lookup(json_dict["vertex"]))
    raise NotImplementedError("contraint {}".format(json_dict["class"]))


def constraints_to_json(constraints):
    json_list = []
    for constraint in constraints:
        json_list.append(constraint_to_json(constraint))
    return json_list


def constraints_from_json(json_list):
    constraints = []
    for sub in json_list:
        constraints.append(constraint_from_json(sub))
    return constraints


def key_mask_to_json(key_mask):
    try:
        json_object = OrderedDict()
        json_object["key"] = key_mask.key
        json_object["mask"] = key_mask.mask
    except Exception as ex:
        json_object["exception"] = str(ex)
    return json_object


def key_mask_from_json(json_dict):
    return BaseKeyAndMask(json_dict["key"], json_dict["mask"])


def key_masks_to_json(key_masks):
    json_list = []
    for key_mask in key_masks:
        json_list.append(key_mask_to_json(key_mask))
    return json_list


def key_masks_from_json(json_list):
    key_masks = []
    for sub in json_list:
        key_masks.append(key_mask_from_json(sub))
    return key_masks


def resource_container_to_json(container):
    json_dict = OrderedDict()
    try:
        json_dict["dtcm"] = container.dtcm.get_value()
        json_dict["cpu_cycles"] = container.cpu_cycles.get_value()
        json_dict["fixed_sdram"] = container.sdram.fixed
        json_dict["per_timestep_sdram"] = container.sdram.per_timestep
        json_dict["iptag"] = iptag_resources_to_json(container.iptags)
        json_dict["reverse_iptags"] = iptag_resources_to_json(
            container.reverse_iptags)
    except Exception as ex:
        json_dict["exception"] = str(ex)
    return json_dict


def resource_container_from_json(json_dict):
    dtcm = DTCMResource(json_dict["dtcm"])
    sdram = VariableSDRAM(
        json_dict["fixed_sdram"], json_dict["per_timestep_sdram"])
    cpu_cycles = CPUCyclesPerTickResource(json_dict["cpu_cycles"])
    iptags = iptag_resources_from_json(json_dict["iptag"])
    reverse_iptags = iptag_resources_from_json(json_dict["reverse_iptags"])
    return ResourceContainer(dtcm, sdram, cpu_cycles, iptags, reverse_iptags)


def iptag_resource_to_json(iptag):
    json_dict = OrderedDict()
    try:
        json_dict["ip_address"] = iptag.ip_address
        if iptag.port is not None:
            json_dict["port"] = iptag.port
        json_dict["strip_sdp"] = iptag.strip_sdp
        if iptag.tag is not None:
            json_dict["tag"] = iptag.tag
        json_dict["traffic_identifier"] = iptag.traffic_identifier
    except Exception as ex:
        json_dict["exception"] = str(ex)
    return json_dict


def iptag_resource_from_json(json_dict):
    if "port" in json_dict:
        port = json_dict["port"]
    else:
        port = None
    if "tag" in json_dict:
        tag = json_dict["tag"]
    else:
        tag = None
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


def vertex_to_json(vertex):
    json_dict = OrderedDict()
    try:
        json_dict["class"] = vertex.__class__.__name__
        json_dict["label"] = vertex.label
        json_dict["constraints"] = constraints_to_json(vertex.constraints)
        json_dict["resources"] = resource_container_to_json(
            vertex.resources_required)
    except Exception as ex:
            json_dict["exception"] = str(ex)
    return json_dict


def vertex_from_json(json_dict):
    constraints = constraints_from_json(json_dict["constraints"])
    resources = resource_container_from_json(
        json_dict["resources"])
    return SimpleMachineVertex(
        resources, label=json_dict["label"], constraints=constraints)


def bacon_to_json(bacon):
    json_dict = OrderedDict()
    try:
        alan_likes_eggs_too = 1/0
    except Exception as ex:
            json_dict["exception"] = str(ex)
    return json_dict


def vertex_lookup(label):
    return SimpleMachineVertex(None, label)
