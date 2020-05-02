import copy
from typing import Any, Union, List, Dict

import pytest

import data_preprocessor.data as data
from data_preprocessor.data import Shape
from data_preprocessor.data.types import Types, ALL_TYPES
from data_preprocessor.flow.OperationDag import OperationDag
from data_preprocessor.flow.OperationHandler import OperationHandler
from data_preprocessor.flow.OperationNode import OperationNode
from data_preprocessor.gui.generic.AbsOperationEditor import AbsOperationEditor
from data_preprocessor.operation.interface import Operation, OutputOperation, InputOperation
from data_preprocessor.operation.all.RenameOp import RenameOp
from data_preprocessor.operation.all.TypeOp import TypeOp


class FakeInput(InputOperation.InputOperation):
    def __init__(self, input):
        super().__init__()
        self.input = input

    def needsOptions(self) -> bool:
        return False

    def inferInputShape(self) -> None:
        self._shape = [self.input.shape]

    def execute(self, *df: data.Frame) -> data.Frame:
        return self.input

    def name(self) -> str:
        pass

    def info(self) -> str:
        pass

    def setOptions(self, *args, **kwargs) -> None:
        pass

    def getOptions(self) -> Any:
        pass

    def getEditor(self) -> AbsOperationEditor:
        pass


class Join(Operation.Operation):
    def __init__(self):
        super().__init__()
        self.__lprefix: str = 'l'
        self.__rprefix: str = 'r'
        self.__type: str = 'left'

    def execute(self, *df: data.Frame) -> data.Frame:
        dfl = df[0]
        dfr = df[1]
        return data.Frame(dfl.getRawFrame().join(dfr.getRawFrame(), how=self.__type,
                                                 lsuffix=self.__lprefix, rsuffix=self.__rprefix))

    def name(self) -> str:
        pass

    def info(self) -> str:
        pass

    def acceptedTypes(self) -> List[Types]:
        return ALL_TYPES

    def setOptions(self, lprefix: str, rprefix: str, type: str) -> None:
        self.__lprefix = lprefix
        self.__rprefix = rprefix
        self.__type = type

    def unsetOptions(self) -> None:
        pass

    def getOptions(self) -> Any:
        pass

    def getEditor(self) -> AbsOperationEditor:
        pass

    def needsOptions(self) -> bool:
        return True

    def getOutputShape(self) -> Union[data.Shape, None]:
        pass

    @staticmethod
    def isOutputShapeKnown() -> bool:
        return True

    @staticmethod
    def minInputNumber() -> int:
        return 2

    @staticmethod
    def maxInputNumber() -> int:
        return 2

    @staticmethod
    def minOutputNumber() -> int:
        return 1

    @staticmethod
    def maxOutputNumber() -> int:
        return -1


class GiveOutOp(OutputOperation.OutputOperation):

    def needsOptions(self) -> bool:
        return True

    def execute(self, *df: data.Frame) -> data.Frame:
        self.__var[1] = df[0]

    def name(self) -> str:
        pass

    def info(self) -> str:
        pass

    def setOptions(self, var) -> None:
        self.__var = var

    def getOptions(self) -> Any:
        pass

    def getEditor(self) -> AbsOperationEditor:
        pass


def test_doubleInputInner():
    d = {'col1': [1, 2, 32, 4, 10], 'col2': ['no', 'ciao', 'aa', 'chiamo', 'e sono']}
    f = data.Frame(d)
    e = {'col11': [2, 10, 4, 11], 'col2': ['mi', 'russo', 'Jon', 'saq']}
    g = data.Frame(e)
    f = f.setIndex('col1')
    g = g.setIndex('col11')

    in1 = FakeInput(f)
    in2 = FakeInput(g)
    joino = Join()
    joino.setOptions('_L', '_R', 'inner')

    graph = OperationDag()
    op1 = OperationNode(in1)
    op2 = OperationNode(in2)
    graph.addNode(op1)
    graph.addNode(op2)

    op3 = OperationNode(joino)
    graph.addNode(op3)
    graph.addConnection(op1.uid, op3.uid, 0)
    graph.addConnection(op2.uid, op3.uid, 1)

    output: Dict[int, data.Frame] = {1: data.Frame()}

    nodeo = OperationNode(GiveOutOp())
    graph.addNode(nodeo)
    graph.updateNodeOptions(nodeo.uid, output)

    graph.addConnection(op3.uid, nodeo.uid, 0)

    handler = OperationHandler(graph)
    # nx.draw(graph.getNxGraph())
    # plt.show()
    handler.execute()

    out = output[1].to_dict()

    assert out == {'col1': [2, 4, 10], 'col11': [2, 4, 10], 'col2_L': ['ciao', 'chiamo', 'e sono'],
                   'col2_R': ['mi', 'Jon', 'russo']}
    s = Shape()
    s.col_names = ['col1', 'col2_L', 'col11', 'col2_R']
    s.col_types = [Types.Numeric, Types.String, Types.Numeric, Types.String]
    s.n_columns = 4
    s.n_rows = 3
    s.index = None  # Inner join does not maintain index
    assert output[1].shape == s


def test_JoinLR():
    d = {'col1': [1, 2, 32, 4, 10], 'col2': ['no', 'ciao', 'aa', 'chiamo', 'e sono']}
    f = data.Frame(d)
    e = {'col11': [2, 10, 4, 11], 'col2': ['mi', 'russo', 'Jon', 'saq']}
    g = data.Frame(e)
    f = f.setIndex('col1')
    g = g.setIndex('col11')

    in1 = FakeInput(f)
    in2 = FakeInput(g)
    joino = Join()
    joino.setOptions('_L', '_R', 'right')

    graph = OperationDag()
    op1 = OperationNode(in1)
    op2 = OperationNode(in2)
    graph.addNode(op1)
    graph.addNode(op2)

    op3 = OperationNode(joino)
    graph.addNode(op3)
    graph.addConnection(op1.uid, op3.uid, slot=0)
    graph.addConnection(op2.uid, op3.uid, slot=1)

    output: Dict[int, data.Frame] = {1: data.Frame()}

    nodeo = OperationNode(GiveOutOp())
    graph.addNode(nodeo)
    graph.updateNodeOptions(nodeo.uid, output)

    graph.addConnection(op3.uid, nodeo.uid, 0)

    handler = OperationHandler(graph)
    handler.execute()

    not_nan = output[1].getRawFrame().dropna().to_dict(orient='list')

    assert not_nan == {'col1': [2.0, 10.0, 4.0], 'col11': [2, 10, 4],
                       'col2_R': ['mi', 'russo', 'Jon'],
                       'col2_L': ['ciao', 'e sono', 'chiamo']}
    s = Shape()
    s.col_names = ['col1', 'col2_L', 'col11', 'col2_R']
    s.col_types = [Types.Numeric, Types.String, Types.Numeric, Types.String]
    s.n_columns = 4
    s.n_rows = 4
    s.index = 'col11'
    assert output[1].shape == s


def test_add_remove_exc():
    n1 = OperationNode(RenameOp())
    n2 = OperationNode(TypeOp())
    dag = OperationDag()

    dag.addNode(n2)
    with pytest.raises(ValueError):
        dag.addConnection(n1.uid, n2.uid, 0)

    with pytest.raises(ValueError):
        dag.removeConnection(n1.uid, n2.uid)


def test_GraphAdd():
    d = {'col1': [1, 2, 0.5, 4, 10], 'col2': [3, 4, 5, 6, 0]}
    f = data.Frame(d)
    dag = OperationDag()

    op0 = FakeInput(f)
    op1 = RenameOp()
    op2 = TypeOp()
    op3 = GiveOutOp()

    node0 = OperationNode(op0)
    node1 = OperationNode(op1)
    node2 = OperationNode(op2)
    node3 = OperationNode(op3)

    dag.addNode(node0)
    dag.addNode(node1)
    dag.addNode(node2)
    dag.addNode(node3)

    # Rename -> Type
    assert dag.addConnection(node1.uid, node2.uid, 0) is True
    assert op2._shape == [None]
    assert op1._shape == [None]

    # Input -> Rename
    assert dag.addConnection(node0.uid, node1.uid, 0) is True
    assert op1._shape == [f.shape]
    assert op2._shape == [f.shape]
    assert op3._shape == [None]

    assert dag.addConnection(node2.uid, node3.uid, 0) is True
    assert op3._shape == [f.shape]
    assert dag.addConnection(node2.uid, node1.uid, 0) is False
    assert dag.addConnection(node1.uid, node3.uid, 1) is False

    # Rename
    dag.updateNodeOptions(node1.uid, {1: 'name_test'})
    assert op1._shape == [f.shape]
    new_shape = copy.deepcopy(f.shape)
    new_shape.col_names = ['col1', 'name_test']
    assert op2._shape == [new_shape]
    assert op3._shape == [new_shape]

    output2 = {1: data.Frame()}
    dag.updateNodeOptions(node3.uid, output2)

    # Type
    dag.updateNodeOptions(node2.uid, {1: Types.String, 0: Types.Numeric})
    new_shape1 = copy.deepcopy(new_shape)
    new_shape1.col_types[1] = Types.String
    assert op2._shape == [new_shape] and op2._shape != [new_shape1]
    assert op3._shape == [new_shape1]

    output1: Dict[int, data.Frame] = {1: data.Frame()}
    op4 = GiveOutOp()
    node4 = OperationNode(op4)
    dag.addNode(node4)
    dag.addConnection(node1.uid, node4.uid, 0)
    assert [op1.getOutputShape()] == node4.operation._shape
    dag.updateNodeOptions(node4.uid, output1)

    handler = OperationHandler(dag)
    handler.execute()
    er1 = {'col1': [1, 2, 0.5, 4, 10], 'name_test': [3, 4, 5, 6, 0]}
    er2 = {'col1': [1, 2, 0.5, 4, 10], 'name_test': ['3', '4', '5', '6', '0']}

    assert output1[1].to_dict() == er1
    assert output2[1].to_dict() == er2

    ns1 = copy.deepcopy(f.shape)
    ns1.col_names[1] = 'name_test'

    ns2 = copy.deepcopy(ns1)
    ns2.col_types[0] = Types.Numeric
    ns2.col_types[1] = Types.String

    assert output1[1].shape == ns1
    assert output2[1].shape == ns2


def test_removeNode():
    d = {'col1': [1, 2, 0.5, 4, 10], 'col2': [3, 4, 5, 6, 0]}
    f = data.Frame(d)
    dag = OperationDag()

    op0 = FakeInput(f)
    op1 = RenameOp()
    op2 = TypeOp()
    op3 = GiveOutOp()

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
    node3_is = copy.deepcopy(node3.operation._shape)
    node2_is = copy.deepcopy(node2.operation._shape)
    node1_is = copy.deepcopy(node1.operation._shape)
    node0_is = copy.deepcopy(node0.operation._shape)
    node0_os = copy.deepcopy(node0.operation.getOutputShape())
    node1_os = copy.deepcopy(node1.operation.getOutputShape())
    node2_os = copy.deepcopy(node2.operation.getOutputShape())
    node3_os = copy.deepcopy(node3.operation.getOutputShape())
    assert node3_os == node0_os == node2_os
    # Remove a node
    dag.removeNode(node1.uid)
    assert node3.operation.getOutputShape() == node2.operation.getOutputShape() != node0.operation.getOutputShape()
    # Reinsert the same node and its connections
    assert dag.addNode(node1) is True
    assert dag.addNode(node1) is False
    assert dag.addConnection(node0.uid, node1.uid, 0) is True
    assert dag.addConnection(node1.uid, node2.uid, 0) is True
    # See if everything is as before
    assert node0.operation._shape == node0_is
    assert node1.operation._shape == node1_is
    assert node2.operation._shape == node2_is
    assert node3.operation._shape == node3_is
    assert node0.operation.getOutputShape() == node0_os
    assert node1.operation.getOutputShape() == node1_os
    assert node2.operation.getOutputShape() == node2_os
    assert node3.operation.getOutputShape() == node3_os
