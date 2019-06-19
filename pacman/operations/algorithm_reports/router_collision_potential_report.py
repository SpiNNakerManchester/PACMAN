import os
from collections import defaultdict
from spinn_machine.router import Router


class RouterCollisionPotentialReport(object):

    def __call__(
            self, router_tables_by_partition, n_keys_map,
            default_report_folder, machine):
        file_name = os.path.join(
            default_report_folder, "routing_collision_protential_report.rpt")

        with open(file_name, "w") as writer:
            collision_counts = self._generate_data(
                router_tables_by_partition, n_keys_map, machine)
            self._write_report(collision_counts, writer)

    @staticmethod
    def _write_report(collision_counts, writer):
        for (x, y) in collision_counts:
            for link_id in collision_counts[(x, y)]:
                writer.write(
                    "router {}:{} link {} has potential {} collisions "
                    "\n".format(
                        x, y, link_id, collision_counts[(x, y)][link_id]))

    def _generate_data(
            self, router_tables_by_partition, n_keys_map, machine):
        collisions = defaultdict(lambda: defaultdict(int))

        for (x, y) in router_tables_by_partition.get_routers():
            for partition in \
                    router_tables_by_partition.get_entries_for_router(x, y):
                entry = router_tables_by_partition.get_entry_on_coords_for_edge(
                    partition, x, y)
                for link in entry.link_ids:
                    if collisions[(x, y)][link] == 0:
                        chip = machine.get_chip_at(x, y)
                        other_chip_x = chip.router.get_link(link).destination_x
                        other_chip_y = chip.router.get_link(link).destination_y
                        collision_route = Router.opposite(link)

                        collision_potential = \
                            self._get_collisions_with_other_router(
                                other_chip_x, other_chip_y, collision_route,
                                router_tables_by_partition, n_keys_map)

                        collisions[(x, y)][link] = collision_potential

                    n_packets = n_keys_map.n_keys_for_partition(partition)
                    collisions[(x, y)][link] += n_packets
        return collisions

    @staticmethod
    def _get_collisions_with_other_router(
            x, y, collision_route, router_tables_by_partition, n_key_map):
        total= 0
        for partition in \
                router_tables_by_partition.get_entries_for_router(x, y):
            entry = router_tables_by_partition.get_entry_on_coords_for_edge(
                partition, x, y)
            if collision_route in entry.link_ids:
                total += n_key_map.n_keys_for_partition(partition)
        return total






