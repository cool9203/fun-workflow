# coding: utf-8

from enum import Enum

from .core._node import NodeType


class FlowLifeState(Enum):
    Create = 0
    Running = 1
    Finish = 2
    Error = -1
    Stopping = -2
    Stop = -3
