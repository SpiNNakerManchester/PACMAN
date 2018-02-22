from pacman.model.placements import Placement
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.model.resources import ResourceContainer
from pacman.model.graphs.machine.machine_graph import MachineGraph
from pacman.model.resources.iptag_resource import IPtagResource
from pacman.model.resources.reverse_iptag_resource import ReverseIPtagResource
from pacman.model.graphs.machine.machine_edge import MachineEdge
from spinn_machine.virtual_machine import VirtualMachine

from pacman.utilities.file_format_converters.\
    convert_to_file_machine_graph_pure_multicast import \
    ConvertToFileMachineGraphPureMulticast
from pacman.utilities.file_format_converters.convert_to_file_machine \
    import ConvertToFileMachine
from pacman.utilities.file_format_converters.convert_to_file_machine_graph \
    import ConvertToFileMachineGraph
from pacman.utilities.file_format_converters.convert_to_file_core_allocations \
    import ConvertToFileCoreAllocations

import hashlib
import json


def test_convert_to_file_core_allocations(tmpdir):
    algo = ConvertToFileCoreAllocations()
    fn = tmpdir.join("foo.json")
    algo([], str(fn))
    assert fn.read() == '{"type": "cores"}'

    v = SimpleMachineVertex(ResourceContainer())
    pl = Placement(v, 1, 2, 3)
    algo([pl], str(fn))
    assert fn.read() == '{"type": "cores", "%d": [3, 4]}' % id(v)


def test_ConvertToFileMachineGraphPureMulticast(tmpdir):
    # Construct the sample graph
    graph = MachineGraph("foo")
    v0 = SimpleMachineVertex(ResourceContainer())
    graph.add_vertex(v0)
    tag = IPtagResource("1.2.3.4", 5, False, tag="footag")
    v1 = SimpleMachineVertex(ResourceContainer(iptags=[tag]))
    graph.add_vertex(v1)
    t1id = hashlib.md5("%d_tag" % id(v1)).hexdigest()
    tag = ReverseIPtagResource(tag="bartag")
    v2 = SimpleMachineVertex(ResourceContainer(reverse_iptags=[tag]))
    graph.add_vertex(v2)
    t2id = hashlib.md5("%d_tag" % id(v2)).hexdigest()
    graph.add_edge(MachineEdge(v1, v0), "part1")
    p1 = graph.get_outgoing_edge_partition_starting_at_vertex(v1, "part1")
    graph.add_edge(MachineEdge(v0, v2, label="foobar"), "part2")
    p2 = graph.get_outgoing_edge_partition_starting_at_vertex(v0, "part2")

    # Convert it to JSON
    algo = ConvertToFileMachineGraphPureMulticast()
    fn = tmpdir.join("foo.json")
    algo(graph, str(fn))

    # Rebuild and compare; simplest way of checking given that order is not
    # preserved in the underlying string and altering that is hard
    obj = json.loads(fn.read())
    baseline = {
        "vertices_resources": {
            str(id(v0)): {"cores": 1, "sdram": 0},
            str(id(v1)): {"cores": 1, "sdram": 0},
            t1id:        {"cores": 0, "sdram": 0},
            str(id(v2)): {"cores": 1, "sdram": 0},
            t2id:        {"cores": 0, "sdram": 0}},
        "edges": {
            str(id(p1)): {
                "source": str(id(v1)), "sinks": [str(id(v0))],
                "type": "multicast", "weight": 1},
            str(id(p2)): {
                "source": str(id(v0)), "sinks": [str(id(v2))], 
                "type": "multicast", "weight": 1},
            t1id: {
                "source": str(id(v1)), "sinks": t1id,
                "weight": 1.0, "type": "FAKE_TAG_EDGE"},
            t2id: {
                "source": str(id(v2)), "sinks": t2id,
                "weight": 1.0, "type": "FAKE_TAG_EDGE"}}}
    assert obj == baseline


def test_convert_to_file_machine_graph(tmpdir):
    # Construct the sample graph
    graph = MachineGraph("foo")
    v0 = SimpleMachineVertex(ResourceContainer())
    graph.add_vertex(v0)
    tag = IPtagResource("1.2.3.4", 5, False, tag="footag")
    v1 = SimpleMachineVertex(ResourceContainer(iptags=[tag]))
    graph.add_vertex(v1)
    t1id = hashlib.md5("%d_tag" % id(v1)).hexdigest()
    tag = ReverseIPtagResource(tag="bartag")
    v2 = SimpleMachineVertex(ResourceContainer(reverse_iptags=[tag]))
    graph.add_vertex(v2)
    t2id = hashlib.md5("%d_tag" % id(v2)).hexdigest()
    graph.add_edge(MachineEdge(v1, v0), "part1")
    p1 = graph.get_outgoing_edge_partition_starting_at_vertex(v1, "part1")
    graph.add_edge(MachineEdge(v0, v2, label="foobar"), "part2")
    p2 = graph.get_outgoing_edge_partition_starting_at_vertex(v0, "part2")

    # Convert it to JSON
    algo = ConvertToFileMachineGraph()
    fn = tmpdir.join("foo.json")
    algo(graph, str(fn))

    # Rebuild and compare; simplest way of checking given that order is not
    # preserved in the underlying string and altering that is hard
    obj = json.loads(fn.read())
    baseline = {
        "vertices_resources": {
            str(id(v0)): {"cores": 1, "sdram": 0},
            str(id(v1)): {"cores": 1, "sdram": 0},
            t1id:        {"cores": 0, "sdram": 0},
            str(id(v2)): {"cores": 1, "sdram": 0},
            t2id:        {"cores": 0, "sdram": 0}},
        "edges": {
            str(id(p1)): {
                "source": str(id(v1)), "sinks": [str(id(v0))],
                "type": "multicast", "weight": 1},
            str(id(p2)): {
                "source": str(id(v0)), "sinks": [str(id(v2))], 
                "type": "multicast", "weight": 1},
            t1id: {
                "source": str(id(v1)), "sinks": t1id,
                "weight": 1.0, "type": "FAKE_TAG_EDGE"},
            t2id: {
                "source": str(id(v2)), "sinks": t2id,
                "weight": 1.0, "type": "FAKE_TAG_EDGE"}}}
    assert obj == baseline


def test_convert_to_file_machine(tmpdir):
    # Construct the sample machine
    machine = VirtualMachine(version=3, with_wrap_arounds=None)

    # Convert it to JSON
    algo = ConvertToFileMachine()
    fn = tmpdir.join("foo.json")
    algo(machine, str(fn))

    # Rebuild and compare; simplest way of checking given that order is not
    # preserved in the underlying string and altering that is hard
    obj = json.loads(fn.read())
    baseline = {
         "chip_resource_exceptions": [
             [0, 1, {"cores": 16}], [1, 0, {"cores": 16}],
             [0, 0, {"cores": 16, "tags": 7}], [1, 1, {"cores": 16}]],
         "chip_resources": {
             "cores": 18, "router_entries": 1024,
             "sdram": 119275520, "sram": 24320, "tags": 0},
         "dead_chips": [],
         "dead_links": [
             [0, 0, "west"], [0, 0, "south_west"],
             [0, 1, "west"], [0, 1, "south_west"],
             [1, 0, "east"], [1, 0, "north_east"],
             [1, 1, "east"], [1, 1, "north_east"]],
         "height": 2, "width": 2}
    assert obj == baseline
