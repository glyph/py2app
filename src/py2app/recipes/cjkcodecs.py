import typing

from modulegraph.modulegraph import ModuleGraph

from .. import build_app
from ._types import RecipeInfo


def check(cmd: "build_app.py2app", mf: ModuleGraph) -> typing.Optional[RecipeInfo]:
    name = "cjkcodecs"
    m = mf.findNode(name)
    if m is None or m.filename is None:
        return None
    mf.import_hook(name, m, ["*"])
    return {}
