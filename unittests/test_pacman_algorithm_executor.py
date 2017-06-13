import unittest
from pacman.executor.pacman_algorithm_executor import PACMANAlgorithmExecutor
from pacman.executor.algorithm_decorators.algorithm_decorator import algorithm


@algorithm({"param": "TestType1"}, ["TestType2"])
class TestAlgorithm(object):

    called = False

    def __call__(self, param):
        if param != "TestType1":
            raise Exception("Unexpected Param")
        TestAlgorithm.called = True
        return "TestType2"


@algorithm({"param": "TestType2"}, ["TestType2"])
class TestNoChangesAlgorithm(object):

    called = False

    def __call__(self, param):
        if param != "TestType2":
            raise Exception("Unexpected Param")
        TestNoChangesAlgorithm.called = True
        return param


@algorithm({"param": "TestType2"}, ["TestType3"])
class TestAlgorithm3(object):

    called = False

    def __call__(self, param):
        if param != "TestType2":
            raise Exception("Unexpected Param")
        TestAlgorithm3.called = True
        return "TestType3"


class Test(unittest.TestCase):

    def test_basic_workflow(self):
        """ Test the basic operation of the executor
        """
        TestAlgorithm.called = False
        TestNoChangesAlgorithm.called = False
        TestAlgorithm3.called = False
        inputs = {"TestType1": "TestType1"}
        executor = PACMANAlgorithmExecutor(
            algorithms=[
                "TestAlgorithm3", "TestAlgorithm", "TestNoChangesAlgorithm"],
            optional_algorithms=[], inputs=inputs, required_outputs=[])
        executor.execute_mapping()
        self.assertTrue(TestAlgorithm.called)
        self.assertTrue(TestNoChangesAlgorithm.called)
        self.assertTrue(TestAlgorithm3.called)

    def test_optional_workflow(self):
        """ Tests that an optional algorithm that doesn't do anything doesn't
            get called
        """
        TestAlgorithm.called = False
        TestNoChangesAlgorithm.called = False
        TestAlgorithm3.called = False
        inputs = {"TestType1": "TestType1"}
        executor = PACMANAlgorithmExecutor(
            algorithms=["TestAlgorithm"],
            optional_algorithms=["TestNoChangesAlgorithm", "TestAlgorithm3"],
            inputs=inputs,
            required_outputs=["TestType3"])
        executor.execute_mapping()
        self.assertTrue(TestAlgorithm.called)
        self.assertFalse(TestNoChangesAlgorithm.called)
        self.assertTrue(TestAlgorithm3.called)
        self.assertEqual(executor.get_item("TestType3"), "TestType3")


if __name__ == "__main__":
    unittest.main()
