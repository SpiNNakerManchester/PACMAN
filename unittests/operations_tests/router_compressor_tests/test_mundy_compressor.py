from pacman.model.routing_tables.multicast_routing_tables import \
    MulticastRoutingTables
from pacman.operations.router_compressors.mundys_router_compressor.\
    routing_table_condenser import MundyRouterCompressor
from pacman.model.routing_tables.multicast_routing_table \
    import MulticastRoutingTable
from spinn_machine.multicast_routing_entry import MulticastRoutingEntry
import unittest


class MyTestCase(unittest.TestCase):

    def test(self):
        """Test minimising a table of the form:

            0000 -> N NE
            0001 -> E
            0101 -> SW
            1000 -> N NE
            1001 -> E
            1110 -> SW
            1100 -> N NE
            0X00 -> S SW

        The result (worked out by hand) should be:

            0000 -> N NE
            0X00 -> S SW
            1X00 -> N NE
            X001 -> E
            X1XX -> SW
        """

        original_tables = MulticastRoutingTables()
        original_table = MulticastRoutingTable(x=0, y=0)
        original_table.add_multicast_routing_entry(
            MulticastRoutingEntry(0b0000, 0b1111, [1, 2], [], False))
        original_table.add_multicast_routing_entry(
            MulticastRoutingEntry(0b0001, 0b1111, [0], [], False))
        original_table.add_multicast_routing_entry(
            MulticastRoutingEntry(0b0101, 0b1111, [4], [], False))
        original_table.add_multicast_routing_entry(
            MulticastRoutingEntry(0b1000, 0b1111, [1, 2], [], False))
        original_table.add_multicast_routing_entry(
            MulticastRoutingEntry(0b1001, 0b1111, [0], [], False))
        original_table.add_multicast_routing_entry(
            MulticastRoutingEntry(0b1110, 0b1111, [4], [], False))
        original_table.add_multicast_routing_entry(
            MulticastRoutingEntry(0b1100, 0b1111, [1, 2], [], False))
        original_table.add_multicast_routing_entry(
            MulticastRoutingEntry(0b0000, 0b1011, [4, 5], [], False))
        original_tables.add_routing_table(original_table)

        mundy_compressor = MundyRouterCompressor()
        compressed_tables = mundy_compressor(original_tables)
        compressed_table = compressed_tables.get_routing_table_for_chip(0, 0)

        # TODO: FIX THIS SO THAT WE TEST THAT THE RESULT IS VALID
        # result_table_expected = MulticastRoutingTable(x=0, y=0)
        # result_table_expected.add_multicast_routing_entry(
        #     MulticastRoutingEntry(0b0000, 0b1111, [1, 2], [], False))
        # result_table_expected.add_multicast_routing_entry(
        #     MulticastRoutingEntry(0b0000, 0b1011, [4, 5], [], False))
        # result_table_expected.add_multicast_routing_entry(
        #     MulticastRoutingEntry(0b1000, 0b1011, [1, 2], [], False))
        # result_table_expected.add_multicast_routing_entry(
        #     MulticastRoutingEntry(0b0001, 0b0111, [0], [], False))
        # result_table_expected.add_multicast_routing_entry(
        #     MulticastRoutingEntry(0b0100, 0b0100, [4], [], False))

        # Minimise as far as possible
        assert compressed_table.number_of_entries == 5
        # assert compressed_table == result_table_expected


if __name__ == '__main__':
    unittest.main()
