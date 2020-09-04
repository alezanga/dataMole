import copy

import pytest

import dataMole.exceptions as exp
from dataMole.flow.dag import OperationDag, OperationNode
from .DummyOp import *


class DummyWithOptions(DummyOp):
    def __init__(self):
        super().__init__()
        self.options: bool = False

    def needsOptions(self) -> bool:
        return True

    def setOptions(self, hasOp: bool) -> None:
        self.options = hasOp

    def unsetOptions(self) -> None:
        pass

    def getOptions(self) -> Any:
        return (self.options,)

    def hasOptions(self) -> bool:
        return self.options


def test_add_remove_exc():
    n1 = OperationNode(InputDummy())
    n2 = OperationNode(DummyOp())
    dag = OperationDag()

    dag.addNode(n2)
    assert not dag.addConnection(n1.uid, n2.uid, 0)

    assert not dag.removeConnection(n1.uid, n2.uid)


def test_GraphAdd():
    d = {'col1': [1, 2, 0.5, 4, 10], 'col2': [3, 4, 5, 6, 0]}
    f = data.Frame(d)
    dag = OperationDag()

    op0 = InputDummy()
    op1 = DummyWithOptions()
    op2 = DummyOp()
    op3 = OutputDummy()

    node0 = OperationNode(op0)
    node1 = OperationNode(op1)
    node2 = OperationNode(op2)
    node3 = OperationNode(op3)

    dag.addNode(node0)
    dag.addNode(node1)
    dag.addNode(node2)
    dag.addNode(node3)

    # Node1 needs options otherwise outputShape is always None
    dag.updateNodeOptions(node1.uid, True)

    # DummyOptions -> Dummy
    assert dag.addConnection(node1.uid, node2.uid, 0) is True
    assert op2._shapes == [None]
    assert op1._shapes == [None]

    # Input -> DummyOptions
    assert dag.addConnection(node0.uid, node1.uid, 0) is True
    assert op0._shapes == []
    assert op1._shapes == [None]
    assert op2._shapes == [None]
    assert op3._shapes == [None]
    # Add options to node0
    assert set(dag.updateNodeOptions(node0.uid, f)) == {node0.uid, node1.uid, node2.uid}
    assert op0._shapes == []
    assert op1._shapes == [f.shape]
    assert op2._shapes == [f.shape]
    assert op3._shapes == [None]

    # Dummy -> OutputDummy
    assert dag.addConnection(node2.uid, node3.uid, 0) is True
    assert op3._shapes == [f.shape]
    # Dummy -> DummyOptions : cycle
    with pytest.raises(exp.DagException):
        assert dag.addConnection(node2.uid, node1.uid, 0) is False
    # DummyOptions -> OutputDummy : > 1 connection
    with pytest.raises(exp.DagException):
        assert dag.addConnection(node1.uid, node3.uid, 1) is False

    # Test if input shapes are removed
    dag.updateNodeOptions(node1.uid, False)
    assert op0._shapes == []
    assert op1._shapes == [f.shape]
    assert op2._shapes == [None]
    assert op3._shapes == [None]

    dag.updateNodeOptions(node1.uid, True)
    assert op0._shapes == []
    assert op1._shapes == [f.shape]
    assert op2._shapes == [f.shape]
    assert op3._shapes == [f.shape]

    output1: List[data.Frame] = [None]  # Allows to get output by reference
    assert node3.operation.getOutputShape() is None
    assert dag.updateNodeOptions(node3.uid, output1)
    assert [f.shape] == node3.operation._shapes


def test_removeNode():
    d = {'col1': [1, 2, 0.5, 4, 10], 'col2': [3, 4, 5, 6, 0]}
    f = data.Frame(d)
    dag = OperationDag()

    op0 = InputDummy()
    op1 = DummyOp()
    op2 = DummyWithOptions()
    op3 = OutputDummy()

    node0 = OperationNode(op0)
    node1 = OperationNode(op1)
    node2 = OperationNode(op2)
    node3 = OperationNode(op3)

    dag.addNode(node0)
    dag.addNode(node1)
    dag.addNode(node2)
    dag.addNode(node3)

    assert dag.addConnection(node1.uid, node2.uid, 0) is True
    assert dag.addConnection(node2.uid, node3.uid, 0) is True
    assert dag.addConnection(node0.uid, node1.uid, 0) is True
    output = [None]
    dag.updateNodeOptions(node3.uid, output)
    dag.updateNodeOptions(node2.uid, True)
    assert node3.operation.getOutputShape() is None
    assert node2.operation.getOutputShape() is None
    assert node3.operation.shapes[0] is None
    assert node2.operation.shapes[0] is None

    dag.updateNodeOptions(node0.uid, f)
    node3_is = copy.deepcopy(node3.operation._shapes)
    node2_is = copy.deepcopy(node2.operation._shapes)
    node1_is = copy.deepcopy(node1.operation._shapes)
    node0_is = copy.deepcopy(node0.operation._shapes)
    node0_os = node0.operation.getOutputShape().clone()
    node1_os = node1.operation.getOutputShape().clone()
    node2_os = node2.operation.getOutputShape().clone()
    node3_os = node3.operation.getOutputShape().clone()
    assert node3_os == node2_os == node0_os == node1_os == f.shape
    # Remove a node
    dag.removeNode(node1.uid)
    assert node3.operation.getOutputShape() is node2.operation.getOutputShape() is None
    assert node0.operation.getOutputShape() == f.shape

    # Reinsert the same node and its connections
    assert dag.addNode(node1) is True
    assert dag.addNode(node1) is False
    assert dag.addConnection(node0.uid, node1.uid, 0) is True
    assert dag.addConnection(node1.uid, node2.uid, 0) is True
    # Reconfigure
    # assert dag.updateNodeOptions(node3.uid, output)
    # assert dag.updateNodeOptions(node2.uid, 1)
    # See if everything is as before
    assert node0.operation._shapes == node0_is
    assert node1.operation._shapes == node1_is
    assert node2.operation._shapes == node2_is
    assert node3.operation._shapes == node3_is
    assert node0.operation.getOutputShape() == node0_os
    assert node1.operation.getOutputShape() == node1_os
    assert node2.operation.getOutputShape() == node2_os
    assert node3.operation.getOutputShape() == node3_os


def test_removeNode_unsetOptions():
    d = {'col1': [1, 2, 0.5, 4, 10], 'col2': [3, 4, 5, 6, 0]}
    f = data.Frame(d)
    dag = OperationDag()

    class DummySetOptions(DummyWithOptions):
        def unsetOptions(self) -> None:
            self.options = False

    op0 = InputDummy()
    op1 = DummyOp()
    op2 = DummySetOptions()
    op3 = OutputDummy()

    node0 = OperationNode(op0)
    node1 = OperationNode(op1)
    node2 = OperationNode(op2)
    node3 = OperationNode(op3)

    dag.addNode(node0)
    dag.addNode(node1)
    dag.addNode(node2)
    dag.addNode(node3)

    assert dag.addConnection(node1.uid, node2.uid, 0) is True
    assert dag.addConnection(node2.uid, node3.uid, 0) is True
    assert dag.addConnection(node0.uid, node1.uid, 0) is True
    output = [None]
    dag.updateNodeOptions(node3.uid, output)
    dag.updateNodeOptions(node2.uid, True)
    assert node3.operation.getOutputShape() is None
    assert node2.operation.getOutputShape() is None
    assert node3.operation.shapes[0] is None
    assert node2.operation.shapes[0] is None

    dag.updateNodeOptions(node0.uid, f)
    dag.updateNodeOptions(node2.uid, True)  # Must be reconfigured since it depends on shape
    node3_is = copy.deepcopy(node3.operation._shapes)
    node2_is = copy.deepcopy(node2.operation._shapes)
    node1_is = copy.deepcopy(node1.operation._shapes)
    node0_is = copy.deepcopy(node0.operation._shapes)
    node0_os = node0.operation.getOutputShape().clone()
    node1_os = node1.operation.getOutputShape().clone()
    node2_os = node2.operation.getOutputShape().clone()
    node3_os = node3.operation.getOutputShape().clone()
    assert node3_os == node2_os == node0_os == node1_os == f.shape
    # Remove a node
    dag.removeNode(node1.uid)
    assert node3.operation.getOutputShape() is node2.operation.getOutputShape() is None
    assert node0.operation.getOutputShape() == f.shape

    # Reinsert the same node and its connections
    assert dag.addNode(node1) is True
    assert dag.addNode(node1) is False
    assert dag.addConnection(node0.uid, node1.uid, 0) is True
    assert dag.addConnection(node1.uid, node2.uid, 0) is True
    # Reconfigure
    # assert dag.updateNodeOptions(node3.uid, output)

    # See if everything is as before
    assert node0.operation.getOutputShape() == f.shape
    assert node1.operation.getOutputShape() == f.shape
    assert node2.operation.getOutputShape() is None
    assert node3.operation.getOutputShape() is None
    assert dag.updateNodeOptions(node2.uid, True)

    assert node0.operation._shapes == node0_is
    assert node1.operation._shapes == node1_is
    assert node2.operation._shapes == node2_is
    assert node3.operation._shapes == node3_is
    assert node0.operation.getOutputShape() == node0_os == f.shape
    assert node1.operation.getOutputShape() == node1_os == f.shape
    assert node2.operation.getOutputShape() == node2_os == f.shape
    assert node3.operation.getOutputShape() == node3_os == f.shape


def test_KnownShape():
    d = {'col1': [1, 2, 0.5, 4, 10], 'col2': [3, 4, 5, 6, 0]}
    f = data.Frame(d)
    dag = OperationDag()

    class DummyNotKnownShape(DummyWithOptions):
        @staticmethod
        def isOutputShapeKnown() -> bool:
            return False

        def getOutputShape(self) -> Union[data.Shape, None]:
            super().getOutputShape()
            return None

        @staticmethod
        def needsInputShapeKnown() -> bool:
            return True

    class DummyNotNeedShape(DummyOp):
        @staticmethod
        def needsInputShapeKnown() -> bool:
            return False

    opi = InputDummy()
    op1 = DummyNotNeedShape()
    op2 = DummyOp()
    opo = OutputDummy()
    op3 = DummyNotKnownShape()
    op4 = DummyNotNeedShape()
    op5 = DummyNotNeedShape()

    nodei = OperationNode(opi)
    node1 = OperationNode(op1)
    node2 = OperationNode(op2)
    nodeo = OperationNode(opo)
    node3 = OperationNode(op3)
    node4 = OperationNode(op4)
    node5 = OperationNode(op5)

    dag.addNode(nodei)
    dag.addNode(node1)
    dag.addNode(node2)
    dag.addNode(node3)
    dag.addNode(node4)
    dag.addNode(node5)
    # assert dag.addConnection(node5.uid, nodeo.uid, 0) is False
    dag.addNode(nodeo)
    other = OperationNode(DummyOp())
    dag.addNode(other)
    assert dag.addConnection(node1.uid, node2.uid, 0) is True
    assert dag.addConnection(node2.uid, node3.uid, 0) is True
    with pytest.raises(exp.DagException):
        # Dummy needs input shape and node3 does not have it
        dag.addConnection(node3.uid, other.uid, 0)
    assert dag.addConnection(node3.uid, node4.uid, 0) is True
    assert dag.addConnection(node4.uid, node5.uid, 0) is True
    assert dag.addConnection(node5.uid, nodeo.uid, 0) is True
    dag.removeNode(other.uid)
    assert dag.addConnection(nodei.uid, node1.uid, 0) is True

    dag.updateNodeOptions(nodei.uid, f)
    os = op2.getOutputShape()
    a = opi.getOutputShape()
    b = op1.getOutputShape()
    c = op2.getOutputShape()
    d = op3.getOutputShape()  # this returns None as output shape
    e = op4.getOutputShape()
    ff = op5.getOutputShape()
    assert os == a == b == c != d is e is ff is None


def test_removeConnection():
    d = {'col1': [1, 2, 0.5, 4, 10], 'col2': [3, 4, 5, 6, 0]}
    f = data.Frame(d)
    dag = OperationDag()

    op0 = InputDummy()
    op1 = DummyOp()
    op2 = OutputDummy()

    node0 = OperationNode(op0)
    node1 = OperationNode(op1)
    node2 = OperationNode(op2)

    dag.addNode(node0)
    dag.addNode(node1)
    dag.addNode(node2)

    assert dag.addConnection(node0.uid, node1.uid, 0) is True
    assert dag.addConnection(node1.uid, node2.uid, 0) is True
    with pytest.raises(exp.DagException):
        # OutputDummy only wants 1 input
        dag.addConnection(node0.uid, node2.uid, 0)
    output = [None]
    dag.updateNodeOptions(node2.uid, output)
    assert node0.operation.getOutputShape() is None
    assert node1.operation.getOutputShape() is None
    assert node2.operation.shapes[0] is None

    dag.updateNodeOptions(node0.uid, f)
    assert node0.operation.getOutputShape() == f.shape
    assert node1.operation.getOutputShape() == f.shape
    assert node2.operation.getOutputShape() == f.shape
    assert node2.operation.shapes[0] == f.shape

    # REMOVE 1 -> 2
    dag.removeConnection(node1.uid, node2.uid)
    assert node0.operation.getOutputShape() == f.shape
    assert node1.operation.getOutputShape() == f.shape
    assert node2.operation.getOutputShape() is None
    assert node2.operation.shapes[0] is None

    # RE-INSERT
    dag.addConnection(node1.uid, node2.uid, 0)
    assert node0.operation.getOutputShape() == f.shape
    assert node1.operation.getOutputShape() == f.shape
    assert node2.operation.getOutputShape() == f.shape
    assert node2.operation.shapes[0] == f.shape

    # REMOVE 0 -> 1
    dag.removeConnection(node0.uid, node1.uid)
    assert node0.operation.getOutputShape() == f.shape
    assert node1.operation.getOutputShape() is None
    assert node2.operation.getOutputShape() is None
    assert node2.operation.shapes[0] is None

    # RE-INSERT
    dag.addConnection(node0.uid, node1.uid, 0)
    assert node0.operation.getOutputShape() == f.shape
    assert node1.operation.getOutputShape() == f.shape
    assert node2.operation.getOutputShape() == f.shape
    assert node2.operation.shapes[0] == f.shape
