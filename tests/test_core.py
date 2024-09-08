# coding: utf-8
# write reference: https://docs.python.org/zh-tw/3/library/unittest.html

import unittest

from pydantic import BaseModel, Field

import fun_workflow as fw


class TestCore(unittest.TestCase):
    def test_pydantic_type(self):
        class QueryOutput(BaseModel):
            query: str = Field(...)

        class OutputOutput(BaseModel):
            result: str = Field(...)
            query: str = Field(...)

        @fw.start_node()
        def query() -> QueryOutput:
            return QueryOutput(query="test query")

        @fw.node()
        def rewrite(query: str) -> QueryOutput:
            return QueryOutput(query=f"{query} rewrite")

        @fw.end_node()
        def output(query: str) -> OutputOutput:
            return OutputOutput(result="result", query=query)

        @fw.end_node()
        def error_output(query: str, a: str) -> OutputOutput:
            return OutputOutput(result="result", query=query)

        print("=" * 25)

        flow = fw.Flow("query", ["rewrite", "rewrite"], "output", strict=True)
        flow.start()

        (_query, _rewrite, _output) = fw.get_nodes("query", "rewrite", "output")
        fw.get_node(_query)
        _query >> _rewrite >> _output

        with self.assertRaises(NotImplementedError):
            _query >> [_rewrite, _rewrite] >> _output

        with self.assertRaises(ValueError):
            _error_output = fw.get_node("error_output")
            _query >> _rewrite >> _error_output

        with self.assertRaises(ValueError):
            _query.inputs = {"query": "test query"}

        with self.assertRaises(ValueError):
            fw.get_node("unknown_node")

    def test_dict_type(self):
        @fw.start_node()
        def query():
            return {"query": "test query"}

        @fw.node()
        def rewrite(query: str):
            return {"query": "test query rewrite"}

        @fw.end_node()
        def output(query: str):
            return {"result": "result", "query": query}

        @fw.end_node()
        def error_output(query: str, a: str):
            return {"result": "result", "query": query}

        print("=" * 25)

        flow = fw.Flow("query", ["rewrite", "rewrite"], "output", strict=False)
        flow.start()

        (_query, _rewrite, _output) = fw.get_nodes("query", "rewrite", "output")
        fw.get_node(_query)
        _query >> _rewrite >> _output

        with self.assertRaises(NotImplementedError):
            _query >> [_rewrite, _rewrite] >> _output

        with self.assertRaises(ValueError):
            _error_output = fw.get_node("error_output")
            _query >> _rewrite >> _error_output

        with self.assertRaises(ValueError):
            _query.inputs = {"query": "test query"}

        with self.assertRaises(ValueError):
            fw.get_node("unknown_node")


if __name__ == "__main__":
    unittest.main()
    input("press Enter to continue...")
