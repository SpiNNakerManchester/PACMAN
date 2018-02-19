import os
import tempfile
import unittest
from pacman.executor import PACMANAlgorithmExecutor
from pacman.executor.algorithm_decorators import algorithm
from pacman.executor.algorithm_decorators.token import Token


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


@algorithm({"param": "TestType1", "param_2": "TestType2"}, ["TestType2"])
class TestRecursiveOptionalAlgorithm(object):

    called = False

    def __call__(self, param, param_2=None):
        if param != "TestType1":
            raise Exception("Unexpected Param")
        if param_2 is not None and param_2 != "TestType2":
            raise Exception("Unexpected Optional Param")
        TestRecursiveOptionalAlgorithm.called = True
        return "TestType2"


@algorithm({"param": "TestType2"}, ["TestType3"])
class TestAlgorithm3(object):

    called = False

    def __call__(self, param):
        if param != "TestType2":
            raise Exception("Unexpected Param")
        TestAlgorithm3.called = True
        return "TestType3"


@algorithm({}, [], generated_output_tokens=[Token("Test", "Part1")])
class TestPartTokenOutput1(object):

    called = False

    def __call__(self):
        TestPartTokenOutput1.called = True


@algorithm({}, [], generated_output_tokens=[Token("Test", "Part2")])
class TestPartTokenOutput2(object):

    called = False

    def __call__(self):
        TestPartTokenOutput2.called = True


@algorithm({}, [], required_input_tokens=[Token("Test")])
class TestWholeTokenRequired(object):

    called = False

    def __call__(self):
        TestWholeTokenRequired.called = True


@algorithm({}, [], optional_input_tokens=[Token("Test")])
class TestWholeTokenOptional(object):

    called = False

    def __call__(self):
        TestWholeTokenOptional.called = True


class SpecificException(Exception):
    """ Just for test purposes.
    """


@algorithm({}, [], optional_input_tokens=[Token("Test")])
class TestExceptionWhenCalled(object):
    def __call__(self):
        raise SpecificException("boom")


@algorithm({}, [], optional_input_tokens=[Token("Test")])
def exception_when_called():
    raise SpecificException("boom")


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
            optional_algorithms=[], inputs=inputs, required_outputs=[],
            tokens=[], required_output_tokens=[])
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
            required_outputs=["TestType3"],
            tokens=[], required_output_tokens=[])
        executor.execute_mapping()
        self.assertTrue(TestAlgorithm.called)
        self.assertFalse(TestNoChangesAlgorithm.called)
        self.assertTrue(TestAlgorithm3.called)
        self.assertEqual(executor.get_item("TestType3"), "TestType3")

    def test_token_workflow(self):
        """ Tests that a workflow with tokens works
        """
        TestPartTokenOutput1.called = False
        TestPartTokenOutput2.called = False
        TestWholeTokenRequired.called = False
        executor = PACMANAlgorithmExecutor(
            algorithms=[
                "TestWholeTokenRequired",
                "TestPartTokenOutput2", "TestPartTokenOutput1"],
            optional_algorithms=[], inputs={}, required_outputs=[],
            tokens=[], required_output_tokens=[])
        executor.execute_mapping()
        self.assertTrue(TestPartTokenOutput1.called)
        self.assertTrue(TestPartTokenOutput2.called)
        self.assertTrue(TestWholeTokenRequired.called)

    def test_optional_algorithm_token_workflow(self):
        """ Tests that a workflow with tokens works with optional algorithms
        """
        TestPartTokenOutput1.called = False
        TestPartTokenOutput2.called = False
        TestWholeTokenRequired.called = False
        executor = PACMANAlgorithmExecutor(
            algorithms=[],
            optional_algorithms=[
                "TestPartTokenOutput2", "TestPartTokenOutput1"],
            inputs={}, required_outputs=[],
            tokens=[], required_output_tokens=["Test"])
        executor.execute_mapping()
        self.assertTrue(TestPartTokenOutput1.called)
        self.assertTrue(TestPartTokenOutput2.called)

    def test_optional_token_workflow_not_needed(self):
        """ Tests that a workflow with tokens works with optional algorithms\
            that are not needed
        """
        TestPartTokenOutput1.called = False
        TestPartTokenOutput2.called = False
        TestWholeTokenRequired.called = False
        executor = PACMANAlgorithmExecutor(
            algorithms=["TestWholeTokenRequired"],
            optional_algorithms=[
                "TestPartTokenOutput2", "TestPartTokenOutput1"],
            inputs={}, required_outputs=[],
            tokens=["Test"], required_output_tokens=[])
        executor.execute_mapping()
        self.assertFalse(TestPartTokenOutput1.called)
        self.assertFalse(TestPartTokenOutput2.called)
        self.assertTrue(TestWholeTokenRequired.called)

    def test_optional_token_workflow(self):
        """ Tests that a workflow with tokens works with optional tokens
        """
        TestPartTokenOutput1.called = False
        TestPartTokenOutput2.called = False
        TestWholeTokenOptional.called = False
        executor = PACMANAlgorithmExecutor(
            algorithms=["TestWholeTokenOptional"],
            optional_algorithms=[
                "TestPartTokenOutput2", "TestPartTokenOutput1"],
            inputs={}, required_outputs=[],
            tokens=[], required_output_tokens=[])
        executor.execute_mapping()
        self.assertTrue(TestPartTokenOutput1.called)
        self.assertTrue(TestPartTokenOutput2.called)
        self.assertTrue(TestWholeTokenOptional.called)

    def test_recursive_optional_workflow(self):
        """ Test the basic operation of the executor
        """
        TestRecursiveOptionalAlgorithm.called = False
        TestAlgorithm3.called = False
        inputs = {"TestType1": "TestType1"}
        executor = PACMANAlgorithmExecutor(
            algorithms=[
                "TestRecursiveOptionalAlgorithm", "TestAlgorithm3"],
            optional_algorithms=[], inputs=inputs, required_outputs=[],
            tokens=[], required_output_tokens=[])
        executor.execute_mapping()
        self.assertTrue(TestRecursiveOptionalAlgorithm.called)
        self.assertTrue(TestAlgorithm3.called)
        self.assertEqual(
            [algorithm.algorithm_id for algorithm in executor._algorithms],
            ["TestRecursiveOptionalAlgorithm", "TestAlgorithm3"])

    def test_failing_class_workflow(self):
        inputs = {}
        executor = PACMANAlgorithmExecutor(
            algorithms=["TestExceptionWhenCalled"],
            optional_algorithms=[], inputs=inputs, required_outputs=[],
            tokens=[], required_output_tokens=[])
        with self.assertRaises(SpecificException):
            executor.execute_mapping()

    def test_failing_function_workflow(self):
        inputs = {}
        executor = PACMANAlgorithmExecutor(
            algorithms=["exception_when_called"],
            optional_algorithms=[], inputs=inputs, required_outputs=[],
            tokens=[], required_output_tokens=[])
        with self.assertRaises(SpecificException):
            executor.execute_mapping()

    def test_external_algorithm(self):
        if not os.access("/bin/sh", os.X_OK):
            raise self.skipTest("need Bourne shell to run this test")
        fd, name = tempfile.mkstemp()
        inputs = {"ExampleFilePath": name}
        xmlfile = os.path.join(os.path.dirname(__file__), "test_algos.xml")
        executor = PACMANAlgorithmExecutor(
            algorithms=["SimpleExternal"], xml_paths=[xmlfile],
            optional_algorithms=[], inputs=inputs, required_outputs=[],
            tokens=[], required_output_tokens=[])
        executor.execute_mapping()
        self.assertEqual(executor.get_item("Foo"), name)
        with os.fdopen(fd) as f:
            self.assertEqual(f.read(), "foo\n")


if __name__ == "__main__":
    unittest.main()
