import json
import pytest
from six import iterkeys
from spinn_machine import virtual_machine
from pacman.model.placements import Placement, Placements
from pacman.model.graphs.machine import (
    MachineGraph, MachineEdge, SimpleMachineVertex, MachineSpiNNakerLinkVertex)
from pacman.model.resources import (
    ResourceContainer, IPtagResource, ReverseIPtagResource)
from pacman.model.constraints.placer_constraints import ChipAndCoreConstraint
from pacman.utilities.file_format_converters import (
    ConvertToFileMachineGraphPureMulticast, ConvertToFilePlacement,
    ConvertToFileMachine, ConvertToFileMachineGraph,
    ConvertToFileCoreAllocations, ConvertToMemoryMultiCastRoutes,
    ConvertToMemoryPlacements, CreateConstraintsToFile)
from pacman.utilities.utility_calls import md5, ident
from pacman.operations.chip_id_allocator_algorithms \
    import MallocBasedChipIdAllocator


def test_convert_to_file_core_allocations(tmpdir):
    algo = ConvertToFileCoreAllocations()
    fn = tmpdir.join("foo.json")
    algo([], str(fn))
    assert fn.read() == '{"type": "cores"}'

    v = SimpleMachineVertex(ResourceContainer())
    pl = Placement(v, 1, 2, 3)
    filename, _ = algo([pl], str(fn))
    assert filename == str(fn)
    assert fn.read() == '{"type": "cores", "%s": [3, 4]}' % ident(v)


def test_convert_to_file_machine_graph_pure_multicast(tmpdir):
    # Construct the sample graph
    graph = MachineGraph("foo")
    v0 = SimpleMachineVertex(ResourceContainer())
    graph.add_vertex(v0)
    tag = IPtagResource("1.2.3.4", 5, False, tag="footag")
    v1 = SimpleMachineVertex(ResourceContainer(iptags=[tag]))
    graph.add_vertex(v1)
    t1id = md5("%s_tag" % ident(v1))
    tag = ReverseIPtagResource(tag="bartag")
    v2 = SimpleMachineVertex(ResourceContainer(reverse_iptags=[tag]))
    graph.add_vertex(v2)
    t2id = md5("%s_tag" % ident(v2))
    graph.add_edge(MachineEdge(v1, v0), "part1")
    p1 = graph.get_outgoing_edge_partition_starting_at_vertex(v1, "part1")
    graph.add_edge(MachineEdge(v0, v2, label="foobar"), "part2")
    p2 = graph.get_outgoing_edge_partition_starting_at_vertex(v0, "part2")

    # Convert it to JSON
    algo = ConvertToFileMachineGraphPureMulticast()
    fn = tmpdir.join("foo.json")
    filename, _vertex_by_id, _partition_by_id = algo(
        graph, plan_n_timesteps=None, file_path=str(fn))
    assert filename == str(fn)

    # Rebuild and compare; simplest way of checking given that order is not
    # preserved in the underlying string and altering that is hard
    obj = json.loads(fn.read())
    baseline = {
        "vertices_resources": {
            ident(v0): {"cores": 1, "sdram": 0},
            ident(v1): {"cores": 1, "sdram": 0},
            t1id:      {"cores": 0, "sdram": 0},
            ident(v2): {"cores": 1, "sdram": 0},
            t2id:      {"cores": 0, "sdram": 0}},
        "edges": {
            ident(p1): {
                "source": ident(v1), "sinks": [ident(v0)],
                "type": "multicast", "weight": 1},
            ident(p2): {
                "source": ident(v0), "sinks": [ident(v2)],
                "type": "multicast", "weight": 1},
            t1id: {
                "source": ident(v1), "sinks": [t1id],
                "weight": 1.0, "type": "FAKE_TAG_EDGE"},
            t2id: {
                "source": ident(v2), "sinks": [t2id],
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
    t1id = md5("%s_tag" % ident(v1))
    tag = ReverseIPtagResource(tag="bartag")
    v2 = SimpleMachineVertex(ResourceContainer(reverse_iptags=[tag]))
    graph.add_vertex(v2)
    t2id = md5("%s_tag" % ident(v2))
    graph.add_edge(MachineEdge(v1, v0), "part1")
    p1 = graph.get_outgoing_edge_partition_starting_at_vertex(v1, "part1")
    graph.add_edge(MachineEdge(v0, v2, label="foobar"), "part2")
    p2 = graph.get_outgoing_edge_partition_starting_at_vertex(v0, "part2")

    # Convert it to JSON
    algo = ConvertToFileMachineGraph()
    fn = tmpdir.join("foo.json")
    filename, _vertex_by_id, _partition_by_id = algo(
        graph, plan_n_timesteps=None, file_path=str(fn))
    assert filename == str(fn)

    # Rebuild and compare; simplest way of checking given that order is not
    # preserved in the underlying string and altering that is hard
    obj = json.loads(fn.read())
    baseline = {
        "vertices_resources": {
            ident(v0): {"cores": 1, "sdram": 0},
            ident(v1): {"cores": 1, "sdram": 0},
            t1id:      {"cores": 0, "sdram": 0},
            ident(v2): {"cores": 1, "sdram": 0},
            t2id:      {"cores": 0, "sdram": 0}},
        "edges": {
            ident(p1): {
                "source": ident(v1), "sinks": [ident(v0)],
                "type": "multicast", "weight": 1},
            ident(p2): {
                "source": ident(v0), "sinks": [ident(v2)],
                "type": "multicast", "weight": 1},
            t1id: {
                "source": ident(v1), "sinks": [t1id],
                "weight": 1.0, "type": "FAKE_TAG_EDGE"},
            t2id: {
                "source": ident(v2), "sinks": [t2id],
                "weight": 1.0, "type": "FAKE_TAG_EDGE"}}}
    assert obj == baseline

def test_convert_to_file_machine(tmpdir):
    # Construct the sample machine
    machine = virtual_machine(version=3)

    # Convert it to JSON
    algo = ConvertToFileMachine()
    fn = tmpdir.join("foo.json")
    filename = algo(machine, str(fn))
    assert filename == str(fn)

    def fix_cre(obj):
        obj = dict(obj)
        if "chip_resource_exceptions" in obj:
            cre = list(obj["chip_resource_exceptions"])
            cre.sort(key=lambda e: (e[0], e[1]))
            obj["chip_resource_exceptions"] = cre
        return obj

    # Rebuild and compare; simplest way of checking given that order is not
    # preserved in the underlying string and altering that is hard
    obj = json.loads(fn.read())
    baseline = {
         "chip_resource_exceptions": [
             [0, 1, {"cores": 17}], [1, 0, {"cores": 17}],
             [0, 0, {"cores": 17, "tags": 7}], [1, 1, {"cores": 17}]],
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
    assert fix_cre(obj) == fix_cre(baseline)

def test_convert_to_file_placement(tmpdir):
    v = SimpleMachineVertex(ResourceContainer())
    pl = Placement(v, 1, 2, 3)
    placements = Placements([pl])
    algo = ConvertToFilePlacement()
    fn = tmpdir.join("foo.json")
    filename, _vertex_by_id = algo(placements, str(fn))
    assert filename == str(fn)
    obj = json.loads(fn.read())
    baseline = {
        ident(v): [1, 2]}
    assert obj == baseline

def test_create_constraints_to_file(tmpdir):
    # Construct the sample machine and graph
    machine = virtual_machine(version=3)
    # TODO: define some extra monitor cores (how?)
    graph = MachineGraph("foo")
    tag1 = IPtagResource("1.2.3.4", 5, False, tag="footag")
    tag2 = ReverseIPtagResource(tag="bartag")
    v0 = SimpleMachineVertex(ResourceContainer(
        iptags=[tag1], reverse_iptags=[tag2]), constraints=[
        ChipAndCoreConstraint(1, 1, 3)])
    graph.add_vertex(v0)
    v0_id = ident(v0)
    v1 = MachineSpiNNakerLinkVertex(0)
    v1.set_virtual_chip_coordinates(0, 2)
    graph.add_vertex(v1)
    v1_id = ident(v1)

    machine = MallocBasedChipIdAllocator()(machine, graph)
    algo = CreateConstraintsToFile()
    fn = tmpdir.join("foo.json")
    filename, mapping = algo(graph, machine, str(fn))
    assert filename == str(fn)
    for vid in mapping:
        assert vid in [v0_id, v1_id]
        assert vid == ident(mapping[vid])
    obj = json.loads(fn.read())
    baseline = [
        {
            "type": "reserve_resource",
            "location": None, "reservation": [0, 1], "resource": "cores"},
        {
            "type": "location",
            "location": [1, 1], "vertex": v0_id},
        {
            "type": "resource",
            "resource": "cores", "range": [3, 4], "vertex": v0_id},
        {
            "type": "resource",
            "resource": "iptag", "range": [0, 1], "vertex": v0_id},
        {
            "type": "resource",
            "resource": "reverse_iptag", "range": [0, 1], "vertex": v0_id},
        {
            "type": "route_endpoint",
            "direction": "west", "vertex": v1_id},
        {
            "type": "location",
            "location": [0, 0], "vertex": v1_id}]
    assert obj == baseline


def test_convert_to_memory_multi_cast_routes(tmpdir):
    algo = ConvertToMemoryMultiCastRoutes()
    fn = tmpdir.join("foo.json")
    # TODO: A more useful input document
    baseline = {
        "a": None,
        "b": {
            "chip": [0, 0],
            "children": [
                {"route": "core_0", "next_hop": None}]}}
    # TODO: Use some real partitions!
    partitions = {
        "a": None,
        "b": 123}
    fn.write(json.dumps(baseline))
    mrtp = algo(str(fn), partitions)
    assert list(mrtp.get_routers()) == [(0, 0)]
    assert list(iterkeys(mrtp.get_entries_for_router(0, 0))) == [123]


@pytest.mark.skip("not yet finished")
def test_convert_to_memory_placements(tmpdir):
    # FIXME: use better inputs
    machine = None
    placements = {}
    allocations = {}
    constraints = {}
    vertex_by_id = None

    p_f = tmpdir.join("placements.json")
    p_f.write(json.dumps(placements))
    a_f = tmpdir.join("allocations.json")
    a_f.write(json.dumps(allocations))
    c_f = tmpdir.join("constraints.json")
    c_f.write(json.dumps(constraints))

    algo = ConvertToMemoryPlacements()
    placements = algo(
        machine, str(p_f), str(a_f), str(c_f), vertex_by_id)
    assert placements is not None
    assert placements == []  # FIXME: compare to real result
