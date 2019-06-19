import unittest
from pacman.executor.algorithm_classes import PythonFunctionAlgorithm


class TestPythonFunctionAlgorithm(unittest.TestCase):
    """
    tests which test the application graph object
    """

    def test_python_module(self):
        python_module = "Foo"
        alg = PythonFunctionAlgorithm("algorithm_id", [], [], [],
                                      python_module, "python_function")
        self.assertEqual(python_module, alg._python_module)
