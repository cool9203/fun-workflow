# coding: utf-8

from __future__ import annotations

import asyncio
import copy
import logging
from functools import partial
from inspect import _empty, signature
from typing import Callable, Dict, List, Tuple, Union

from pydantic import BaseModel

__all__ = (
    "BaseNode",
    "ConditionNode",
    "EndNode",
    "Node",
    "NodeType",
    "StartNode",
    "_mapping",
    "condition_node",
    "end_node",
    "get_node",
    "get_nodes",
    "node",
    "start_node",
)

__logger_level = "DEBUG"
# __logger_format = "%(levelname)s %(asctime)s %(pathname)s.%(lineno)d %(message)s"
__logger_format = "%(levelname)s %(pathname)s.%(lineno)d %(message)s"
# __logger_format = "%(levelname)s %(asctime)s %(message)s"
DATEFMT_STD = "%Y/%m/%d %I:%M:%S"
logger = logging.getLogger(__name__)
logger.setLevel(__logger_level)
formatter = logging.Formatter(__logger_format, datefmt=DATEFMT_STD)

handler = logging.StreamHandler()
handler.setLevel(__logger_level)
handler.setFormatter(formatter)
logger.addHandler(handler)


_mapping = dict()


class BaseNode:
    """_summary_"""

    def __init__(
        self,
        *,
        func: Callable = None,
        name: str = None,
        description: str = None,
        inputs: Union[Dict, BaseModel] = {},
    ):
        self._func = func
        self._node_name = name
        self._description = description
        self.finish: bool = False
        self._inputs = inputs
        self.outputs = None

    def require_parameters(self):
        return signature(self._func).parameters

    def outputs_type(self):
        return signature(self._func).return_annotation

    @property
    def inputs(self) -> Dict:
        return self._inputs

    @inputs.setter
    def inputs(self, inputs: Union[Dict, BaseModel]):
        if isinstance(inputs, dict):
            self._inputs = inputs
        elif issubclass(type(inputs), BaseModel):
            self._inputs = inputs.model_dump()
        else:  # pragma: no cover
            raise TypeError("BaseNode.inputs need be dict or pydantic.BaseModel")

    def __str__(self) -> str:  # pragma: no cover
        return self.__repr__()

    def __repr__(self) -> str:
        function_name = self._func.__name__ if self._func else ""
        return (
            f"<{self.__class__.__name__}: '{self._node_name}', "
            + f"Function: '{function_name}', "
            + f"Description: '{self._description}', "
            + f"Finish: {self.finish}>"
        )

    def __rshift__(self, node: NodeType):
        self.outputs = self.run()
        if isinstance(node, (list, tuple)):
            # TODO: Need support
            # for _internal_node in node:
            #     _internal_node.inputs = self.outputs
            raise NotImplementedError
        else:
            node.inputs = self.outputs
        if isinstance(node, EndNode):
            node.run()
        return node

    def _dynamic_check(self):
        """Check parameter is already

        Raises:
            ValueError: _description_
        """
        for parameter_name, parameter in self.require_parameters().items():
            if parameter.default == _empty and parameter_name not in self.inputs:
                raise ValueError(f"Node `{self._node_name}` missing parameter: {parameter_name}")

    def run(self) -> Dict:
        self._dynamic_check()
        logger.debug(f"name: {self._node_name}")
        logger.debug(f"inputs: {self.inputs}")
        self.output = self._func(**self.inputs)
        self.finish = True
        logger.debug(f"output: {self.output}")
        logger.debug("-" * 25)
        return self.output

    async def async_run(self) -> Dict:
        self._dynamic_check()
        logger.debug(f"name: {self._node_name}")
        logger.debug(f"inputs: {self.inputs}")
        if asyncio.iscoroutinefunction(self._func):
            self.output = await self._func(**self.inputs)
        else:
            self.output = await asyncio.to_thread(self._func(**self.inputs))
        self.finish = True
        logger.debug(f"output: {self.output}")
        logger.debug("-" * 25)
        return self.output


class StartNode(BaseNode):
    @property
    def inputs(self) -> Dict:
        return self._inputs

    @inputs.setter
    def inputs(self, inputs: Dict):
        # Block StartNode have input parameter
        if inputs:
            raise ValueError


class Node(BaseNode): ...


class ConditionNode(BaseNode): ...


class EndNode(BaseNode): ...


def __node_decorator(
    *,
    description: str = None,
    node_class: Callable = None,
):
    def __wrapper(func: Callable):
        name = func.__name__
        _mapping[name] = node_class(
            func=func,
            name=name,
            description=description,
        )

        logger.debug(f"Register {node_class.__name__} of `{name}`")

        return func

    return __wrapper


def get_node(node_name: str) -> NodeType:
    if isinstance(node_name, str) and node_name in _mapping:
        return copy.deepcopy(_mapping.get(node_name))
    elif isinstance(node_name, NodeType):
        return node_name
    else:
        raise ValueError(f"Node `{node_name}` not register")


def get_nodes(*args: List[str]) -> Tuple[NodeType]:
    nodes = list()
    for node_name in args:
        nodes.append(get_node(node_name))
    return tuple(nodes)


def check_node_can_link(
    node1: NodeType,
    node2: NodeType,
    raise_exception: bool = False,
) -> bool:
    outputs_type = node1.outputs_type()
    next_input_type = node2.require_parameters()

    if not issubclass(outputs_type, BaseModel):
        if raise_exception:  # pragma: no cover
            raise ValueError("need output hint and pydantic.BaseModel")
        return False

    logger.debug(outputs_type.model_fields)

    # Check parameters
    for parameter_name, parameter in next_input_type.items():
        if parameter.default == _empty and parameter_name not in outputs_type.model_fields:
            if raise_exception:  # pragma: no cover
                raise ValueError(
                    f"Node '{node1._node_name}' outputs or Node '{node2._node_name}' inputs missing parameter '{parameter_name}'"
                )
            return False

    return True


start_node = partial(__node_decorator, node_class=StartNode)
end_node = partial(__node_decorator, node_class=EndNode)
condition_node = partial(__node_decorator, node_class=ConditionNode)
node = partial(__node_decorator, node_class=Node)
NodeType = Union[
    BaseNode,
    StartNode,
    Node,
    ConditionNode,
    EndNode,
]
