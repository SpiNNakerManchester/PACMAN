# pacman imports
from pacman.model.constraints.partitioner_constraints\
    import MaxVertexAtomsConstraint
from pacman.model.graphs.common import Slice
from pacman.model.graphs.machine import SimpleMachineVertex

# unit tests imports
from uinit_test_objects.test_vertex import TestVertex

# general imports
import unittest


class TestApplicationGraphModel(unittest.TestCase):
    """
    tests which test the application graph object
    """
    def test_create_new_vertex(self):
        """
        test initisation of a vertex
        """
        vert = TestVertex(10, "New AbstractConstrainedVertex", 256)
        self.assertEqual(vert.n_atoms, 10)
        self.assertEqual(vert.label, "New AbstractConstrainedVertex")

    def test_create_new_vertex_without_label(self):
        """
        test initisation of a vertex without a label
        """
        vert = TestVertex(10, "Population", 256)
        self.assertEqual(vert.n_atoms, 10)
        pieces = vert.label.split(" ")
        self.assertIn(pieces[0], "Population n")

    def test_create_new_vertex_with_constraint_list(self):
        """
        test initisation of a vertex with a max size constraint
        """
        constraint = MaxVertexAtomsConstraint(2)
        vert = TestVertex(10, "New AbstractConstrainedVertex", 256)
        vert.add_constraint(constraint)
        self.assertEqual(vert.n_atoms, 10)
        self.assertEqual(vert.label, "New AbstractConstrainedVertex")
        assert constraint in vert.constraints

    def test_create_new_vertex_add_constraint(self):
        """
        test creating a vertex and then adding constraints indivusally
        """
        constraint1 = MaxVertexAtomsConstraint(2)
        constraint2 = MaxVertexAtomsConstraint(3)
        constr = list()
        constr.append(constraint1)
        constr.append(constraint2)
        vert = TestVertex(10, "New AbstractConstrainedVertex", 256)
        vert.add_constraint(constraint2)
        vert.add_constraint(constraint1)
        self.assertEqual(vert.n_atoms, 10)
        self.assertEqual(len(vert.constraints), 3)
        self.assertEqual(vert.label, "New AbstractConstrainedVertex")
        for constraint in constr:
            if constraint not in vert.constraints:
                raise Exception("dont exist where should")

    def test_create_new_vertex_add_constraints(self):
        """
        test that  creating a vertex and then adding constraints in a list
        """
        constraint1 = MaxVertexAtomsConstraint(2)
        constraint2 = MaxVertexAtomsConstraint(3)
        constr = list()
        constr.append(constraint1)
        constr.append(constraint2)
        vert = TestVertex(10, "New AbstractConstrainedVertex", 256)
        vert.add_constraints(constr)
        self.assertEqual(vert.n_atoms, 10)
        self.assertEqual(vert.label, "New AbstractConstrainedVertex")
        self.assertEqual(len(vert.constraints), 3)
        for constraint in constr:
            self.assertIn(constraint, vert.constraints)

    def test_create_vertex_from_vertex_with_previous_constraints(self):
        """
        test the create vertex command given by the
        vertex actually works and generates a vertex
        with the same constraints mapped over
        """
        constraint1 = MaxVertexAtomsConstraint(2)
        vert = TestVertex(10, "New AbstractConstrainedVertex", 256)
        subv_from_vert = vert.create_machine_vertex(
            Slice(0, 9),
            vert.get_resources_used_by_atoms(Slice(0, 9)))
        self.assertNotIn(constraint1, subv_from_vert.constraints)

    def test_new_create_vertex_from_vertex_no_constraints(self):
        """
        test the creating of a vertex by the
        create vertex method will actually create a vertex of the
        vertex type.
        """
        vert = TestVertex(10, "New AbstractConstrainedVertex", 256)
        vertex = vert.create_machine_vertex(
            Slice(0, 9),
            vert.get_resources_used_by_atoms(Slice(0, 9)))
        self.assertIsInstance(vertex, SimpleMachineVertex)

    def test_new_create_vertex_from_vertex_check_resources(self):
        """ check that the creation of a vertex means that the reosurces
        calcualted by the vertex is the same as what the
        vertex says (given same sizes)

        """
        vert = TestVertex(10, "New AbstractConstrainedVertex", 256)
        resources = vert.get_resources_used_by_atoms(Slice(0, 9))
        subv_from_vert = vert.create_machine_vertex(Slice(0, 9), resources, "")
        self.assertEqual(subv_from_vert.resources_required, resources)

    @unittest.skip("demonstrating skipping")
    def test_create_new_vertex_from_vertex_with_additional_constraints(
            self):
        """
        test that a vertex created from a vertex with
        constraints can have more constraints added to it.
        """
        constraint1 = MaxVertexAtomsConstraint(2)
        constraint2 = MaxVertexAtomsConstraint(3)
        vert = TestVertex(10, "New AbstractConstrainedVertex", 256)
        vert.add_constraint([constraint1])
        subv_from_vert = vert.create_machine_vertex(
            Slice(0, 9),
            vert.get_resources_used_by_atoms(Slice(0, 9)), "",
            [constraint2])
        subv_from_vert.add_constraint(constraint1)
        self.assertEqual(len(subv_from_vert.constraints), 2)
        self.assertEqual(subv_from_vert.constraints[1], constraint1)
        self.assertEqual(subv_from_vert.constraints[0], constraint2)
