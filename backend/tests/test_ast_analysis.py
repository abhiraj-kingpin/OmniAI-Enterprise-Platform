from app.modules.coding_assistant.ast_analysis import analyze

SAMPLE = '''
import os
from typing import Any

class Foo(Bar):
    """A demo class."""
    def method(self, x):
        if x > 0:
            for i in range(x):
                print(i)
        return x

async def bar(a, b):
    """Adds two numbers."""
    return a + b
'''


def test_imports_extracted():
    result = analyze(SAMPLE)
    assert "os" in result.imports
    assert "typing.Any" in result.imports


def test_functions_extracted():
    result = analyze(SAMPLE)
    names = {f.name for f in result.functions}
    assert names == {"method", "bar"}
    bar = next(f for f in result.functions if f.name == "bar")
    assert bar.is_async
    assert bar.args == ["a", "b"]
    assert bar.docstring == "Adds two numbers."


def test_classes_extracted():
    result = analyze(SAMPLE)
    assert len(result.classes) == 1
    cls = result.classes[0]
    assert cls.name == "Foo"
    assert cls.bases == ["Bar"]
    assert cls.methods == ["method"]


def test_complexity_counts_branches():
    result = analyze(SAMPLE)
    # baseline (1) + if + for
    assert result.approx_complexity == 3


def test_invalid_python_raises_syntax_error():
    import pytest

    with pytest.raises(SyntaxError):
        analyze("def broken(:\n    pass")
