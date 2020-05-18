from typing import Any

import networkx as nx

from data_preprocessor import data
from data_preprocessor.data import Frame
from data_preprocessor.data.types import Types
from data_preprocessor.flow.OperationHandler import OperationHandler
from data_preprocessor.flow.OperationNode import OperationNode
from data_preprocessor.gui.editor.interface import AbsOperationEditor
from data_preprocessor.operation.interface import InputGraphOperation
from data_preprocessor.operation.rename import RenameOp
from data_preprocessor.operation.PrintOp import PrintOp


class FakeInput(InputOperation):
    def __init__(self, input):
        super().__init__()
        self.input = input

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


if __name__ == "__main__":
    d = {'col1': [1, 2, 0.5, 4, 10], 'col2': [3, 4, 5, 6, 0]}
    f = Frame(d)
    op0 = FakeInput(f)
    op1 = RenameOp()
    op1.setOptions(names={0: 'newcol1'})
    op2 = TypeOp()
    op2.setOptions(new_types={0: Types.String})
    op3 = PrintOp()

    tree = nx.DiGraph()
    node0 = OperationNode(op0)
    node1 = OperationNode(op1)
    node2 = OperationNode(op2)
    node3 = OperationNode(op3)
    tree.add_node(node0)
    tree.add_node(node1)
    tree.add_node(node2)
    tree.add_node(node3)
    tree.add_edge(node0, node1)
    tree.add_edge(node1, node2)
    tree.add_edge(node2, node3)
    tree.add_edge(node1, node3)

    handler = OperationHandler(tree)
    handler.execute()
