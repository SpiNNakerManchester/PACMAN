import unittest
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.model.constraints.partitioner_constraints import \
    MaxVertexAtomsConstraint, SameAtomsAsVertexConstraint,\
    FixedVertexAtomsConstraint


class TestPartitionConstraints(unittest.TestCase):
    """ Tester for pacman.model.constraints.partitioner_constraints
    """

    def test_max_vertex_atoms_constraint(self):
        c1 = MaxVertexAtomsConstraint(5)
        self.assertEqual(c1.size, 5)
        self.assertEqual(c1, MaxVertexAtomsConstraint(5))
        self.assertEqual(str(c1), 'MaxVertexAtomsConstraint(size=5)')
        c2 = MaxVertexAtomsConstraint(7)
        self.assertNotEqual(c1, c2)
        self.assertNotEqual(c1, "1.2.3.4")
        d = {}
        d[c1] = 1
        d[c2] = 2
        self.assertEqual(len(d), 2)

    def test_fixed_vertex_atoms_constraint(self):
        c1 = FixedVertexAtomsConstraint(5)
        self.assertEqual(c1.size, 5)
        self.assertEqual(c1, FixedVertexAtomsConstraint(5))
        self.assertEqual(str(c1), 'FixedVertexAtomsConstraint(size=5)')
        c2 = FixedVertexAtomsConstraint(7)
        self.assertNotEqual(c1, c2)
        self.assertNotEqual(c1, "1.2.3.4")
        d = {}
        d[c1] = 1
        d[c2] = 2
        self.assertEqual(len(d), 2)

    def test_same_atoms_as_vertex_constraint(self):
        v1 = SimpleMachineVertex(None, "v1")
        v2 = SimpleMachineVertex(None, "v2")
        c1 = SameAtomsAsVertexConstraint(v1)
        self.assertEqual(c1.vertex, v1)
        self.assertEqual(c1, SameAtomsAsVertexConstraint(v1))
        self.assertEqual(str(c1), 'SameAtomsAsVertexConstraint(vertex=v1)')
        c2 = SameAtomsAsVertexConstraint(v2)
        self.assertNotEqual(c1, c2)
        self.assertNotEqual(c1, "1.2.3.4")
        d = {}
        d[c1] = 1
        d[c2] = 2
        self.assertEqual(len(d), 2)
