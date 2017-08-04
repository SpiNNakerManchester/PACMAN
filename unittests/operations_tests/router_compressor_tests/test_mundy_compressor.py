from pacman.model.routing_tables \
    import MulticastRoutingTable, MulticastRoutingTables
from pacman.operations.router_compressors.mundys_router_compressor.\
    routing_table_condenser import MundyRouterCompressor
from spinn_machine import MulticastRoutingEntry
import unittest


class MyTestCase(unittest.TestCase):

    def value_checker(self, table, value):
        for route in table.multicast_routing_entries:
            # print route, type(route)
            check = value & route.mask
            if check == route.routing_entry_key:
                return route
        return None

    def table_compare(self, original, compressed, covers):
        for value in covers:
            route1 = self.value_checker(original, value)
            route2 = self.value_checker(compressed, value)
            if route1 is None:
                continue
            if route2 is None:
                msg = "Value {} was picked up by route: {} in the original " \
                      "but not in the compressed.".format(value, route1)
                raise AssertionError(msg)
            if (not route1.processor_ids == route2.processor_ids):
                msg = "Value {} was picked up by route: {} in the original " \
                      "and route: in the compressed.".format(value, route1)
                raise AssertionError(msg)

    def covers(self, route, length=4):
        """
        This method discovers all the routing keys covered by this route

        Starts of with the assumption thsat the key is always covered/

        Whenever a mask bit is zero the list of covered keys is doubled to
            include both the key with a aero and a one at that place

        :param route: single routing Entry
        :type route: :py:class:`spinn_machine.MulticastRoutingEntry`
        :param length: length in bits of the key and mask
        ;type length int
        :return: set of routing_keys covered by this route
        """
        mask = route.mask
        routing_entry_key = route.routing_entry_key
        covers = [routing_entry_key]
        # Check each bit in the mask
        for i in range(length):
            bit_value = 2**i
            # If the mask bit is zero then both zero and one acceptable
            if mask & bit_value == 0:
                # Safety key 1 with mask 0 is an error
                if routing_entry_key & bit_value == 1:
                    msg = "Bit {} on the mask:{} is 0 but 1 in the key:{}" \
                          "".format(i, bin(mask), bin(routing_entry_key))
                    raise AssertionError(msg)
                for j in range(len(covers)):
                    covers.append(covers[j] + bit_value)
        return covers

    def pattern(self, route, length=4):
        mask = route.mask
        routing_entry_key = route.routing_entry_key
        covers = ""
        # Check each bit in the mask
        for i in reversed(range(length)):
            bit_value = 2**i
            if mask & bit_value == 0:
                if routing_entry_key & bit_value == 0:
                    covers += "X"
                else:
                    # Safety key 1 with mask 0 is an error
                    msg = "Bit {} on the mask:{} is 0 but 1 in the key:{}" \
                          "".format(i, bin(mask), bin(routing_entry_key))
                    raise AssertionError(msg)
            else:
                if routing_entry_key & bit_value == 0:
                    covers += "0"
                else:
                    covers += "1"
        return covers

    def all_pattern(self, table, length=4):
        """
        This method discovers all the routing keys covered by this
            routing table

        :param table: Routing table
        :type table: MulticastRoutingTable
        :param length: length in bits of the key and mask
        ;type length int
        :return: set of routing_keys covered by this route
        """
        covers = set()
        for route in table.multicast_routing_entries:
            print route, "*", self.pattern(route)
            covers.add(self.pattern(route))
        return covers

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

        # Minimise as far as possible
        assert compressed_table.number_of_entries == 5
        patterns = self.all_pattern(original_table)
        #self.table_compare(original_table, compressed_table, covers)


if __name__ == '__main__':
    unittest.main()
