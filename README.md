# fun-workflow

Mean fun(ction) workflow.

A lite workflow engine, support fastapi and flask api endpoint.

work in progress...


## Example

```python
import fun_workflow as fw

@fw.start_node()
def query():
    return {"query": "test query"}

@fw.node()
def rewrite(query: str):
    return {"query": f"{query} rewrite"}

@fw.end_node()
def output(query: str, aaa=123):
    return {"result": "result", "query": query}

print("=" * 25)

# Normal
flow = fw.Flow("query", "rewrite", "output")
flow.start()

# Or list node
flow = fw.Flow("query", ["rewrite", "rewrite"], "output")
flow.start()

# Or use node, last node need be `EndNode`, else will not run last node
(_query, _rewrite, _output) = fw.get_nodes("query", "rewrite", "output")
_query >> _rewrite >> _output
```
