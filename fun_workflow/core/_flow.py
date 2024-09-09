# coding: utf-8

from __future__ import annotations

import logging
import pprint
from typing import List, Union

from pydantic import BaseModel

from .._types import FlowLifeState, NodeType
from ._node import BaseNode, StartNode, _mapping, check_node_can_link, get_node, get_nodes
from .util import get_function_used_params

__all__ = ("Flow",)


__logger_level = "INFO"
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


class Flow:
    def __init__(
        self,
        *args,
        strict: bool = True,
        description: str = None,
        **kwds,
    ):
        self._strict = strict
        self._description = description
        self._nodes: List[Union[NodeType, List[NodeType]]] = list()
        self.state = FlowLifeState.Create
        self._signal = False
        self._inputs = list()
        self._outputs = list()
        self._settings = kwds

        for nodes in args:
            self.next(nodes, check=strict)

        logger.debug(pprint.pformat(self._nodes))

    def __str__(self) -> str:  # pragma: no cover
        return self.__repr__()

    def __repr__(self) -> str:
        return f"<Flow, description: '{self._description}'>"

    def stop(self):
        self._signal = True
        self.state = FlowLifeState.Stopping

    def start(self):
        self.state = FlowLifeState.Running
        outputs = dict()
        try:
            for node in self._nodes:
                logger.debug(node)
                logger.debug(f"outputs: {outputs}")
                if self._signal:
                    self.state = FlowLifeState.Stop
                    break

                if isinstance(node, list):
                    _internal_inputs = list()
                    _internal_outputs = list()
                    for _internal_node in node:
                        _inputs = get_function_used_params(_internal_node._func, **outputs, **self._settings)
                        _internal_node.inputs = _inputs
                        _outputs = _internal_node.run()
                        _internal_inputs.append(_inputs)
                        _internal_outputs.append(_outputs)
                        logger.debug(f"_outputs: {_outputs}")
                    self._inputs.append(_internal_inputs)
                    self._outputs.append(_internal_outputs)

                else:
                    _inputs = get_function_used_params(node._func, **outputs, **self._settings)
                    node.inputs = _inputs
                    _outputs = node.run()
                    self._inputs.append(_inputs)
                    self._outputs.append(_outputs)
                    logger.debug(f"_outputs: {_outputs}")
                outputs = _outputs  # TODO: only use last output, maybe is wrong?
                logger.debug("-" * 25)

            self.state = FlowLifeState.Finish
        except Exception as e:
            self.state = FlowLifeState.Error
            raise e

    async def async_start(self):
        self.state = FlowLifeState.Running
        outputs = dict()
        try:
            for node in self._nodes:
                if self._signal:
                    self.state = FlowLifeState.Stop
                    break

                if isinstance(node, list):
                    for _internal_node in node:
                        _internal_node.inputs = outputs
                        _outputs = await _internal_node.async_run()

                else:
                    node.inputs = outputs
                    _outputs = await node.async_run()
                outputs = _outputs
            self.state = FlowLifeState.Finish
        except Exception as e:
            self.state = FlowLifeState.Error
            raise e

    def next(
        self,
        nodes: Union[NodeType, List[NodeType], str, List[str]],
        *,
        check: bool = True,
    ) -> Flow:
        if isinstance(nodes, list):
            _node = list()
            for node in nodes:
                _node.append(get_node(node))
        elif isinstance(nodes, str):
            _node = get_node(nodes)
        elif isinstance(nodes, NodeType):
            _node = nodes
        else:  # pragma: no cover
            raise TypeError("nodes type not support")

        if (self._strict or check) and self._nodes:
            _last_node = self._nodes[-1]
            _last_node = _last_node[0] if isinstance(_last_node, list) else _last_node
            if isinstance(_node, list):
                for __internal_node in _node:
                    check_node_can_link(_last_node, __internal_node, raise_exception=True)
            else:
                check_node_can_link(_last_node, _node, raise_exception=True)

        if not self._nodes and not isinstance(_node, StartNode):
            raise ValueError("First node need be StartNode")
        self._nodes.append(_node)
        return self
