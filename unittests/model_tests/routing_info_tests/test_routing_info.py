import unittest
from pacman.model.resources import ResourceContainer
from pacman.exceptions import PacmanAlreadyExistsException
from pacman.model.routing_info \
    import RoutingInfo, BaseKeyAndMask, PartitionRoutingInfo
from pacman.model.graphs.machine \
    import MachineOutgoingEdgePartition, MachineEdge, SimpleMachineVertex


class TestRoutingInfo(unittest.TestCase):

    def test_routing_info(self):
        partition = MachineOutgoingEdgePartition("Test")
        pre_vertex = SimpleMachineVertex(resources=ResourceContainer())
        post_vertex = SimpleMachineVertex(resources=ResourceContainer())
        edge = MachineEdge(pre_vertex, post_vertex)
        key = 12345
        partition_info = PartitionRoutingInfo(
            [BaseKeyAndMask(key, 0xFFFFFFFF)], partition)
        partition.add_edge(edge)
        routing_info = RoutingInfo([partition_info])

        with self.assertRaises(PacmanAlreadyExistsException):
            routing_info.add_partition_info(partition_info)

        assert routing_info.get_first_key_from_partition(partition) == key
        assert routing_info.get_first_key_from_partition(None) is None

        assert routing_info.get_routing_info_from_partition(partition) == \
            partition_info
        assert routing_info.get_routing_info_from_partition(None) is None

        assert routing_info.get_routing_info_from_pre_vertex(
            pre_vertex, "Test") == partition_info
        assert routing_info.get_routing_info_from_pre_vertex(
            post_vertex, "Test") is None
        assert routing_info.get_routing_info_from_pre_vertex(
            pre_vertex, "None") is None

        assert routing_info.get_first_key_from_pre_vertex(
            pre_vertex, "Test") == key
        assert routing_info.get_first_key_from_pre_vertex(
            post_vertex, "Test") is None
        assert routing_info.get_first_key_from_pre_vertex(
            pre_vertex, "None") is None

        assert routing_info.get_routing_info_for_edge(edge) == partition_info
        assert routing_info.get_routing_info_for_edge(None) is None

        assert routing_info.get_first_key_for_edge(edge) == key
        assert routing_info.get_first_key_for_edge(None) is None

        assert next(iter(routing_info)) == partition_info


if __name__ == "__main__":
    unittest.main()
