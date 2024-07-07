import sys

if sys.version_info[:2] < (3, 10):
    import importlib_resources
else:
    import importlib.resources as importlib_resources

import os
import plistlib
import shutil
import typing

from . import _progress, apptemplate
from .util import make_exec, make_path, mergecopy, mergetree, skipscm


def create_appbundle(
    destdir: typing.Union[str, os.PathLike[str]],
    name: str,
    *,
    progress: _progress.Progress,
    extension: str = ".app",
    platform: str = "MacOS",
    copy: typing.Callable[[str, str], None] = mergecopy,
    mergetree: typing.Callable[
        [str, str, typing.Callable[[str], bool], typing.Callable[[str, str], None]],
        None,
    ] = mergetree,
    condition: typing.Callable[[str], bool] = skipscm,
    plist: typing.Optional[typing.Dict[str, typing.Any]] = None,
    arch: typing.Optional[str] = None,
    use_old_sdk: bool = False,
    redirect_stdout: bool = False,
) -> typing.Tuple[str, typing.Dict[str, typing.Any]]:
    destpath = make_path(destdir)

    if plist is None:
        plist = {}

    kw = apptemplate.plist_template.infoPlistDict(
        plist.get("CFBundleExecutable", name), plist
    )
    app = destpath / (kw["CFBundleName"] + extension)
    if app.exists():
        # Remove any existing build artifacts to ensure that
        # we're getting a clean build
        shutil.rmtree(app)

    contents = app / "Contents"
    resources = contents / "Resources"
    platdir = contents / platform
    dirs = [contents, resources, platdir]
    plist = {}
    plist.update(kw)
    plistPath = contents / "Info.plist"
    for d in dirs:
        progress.trace(f"Create {d}")
        d.mkdir(parents=True, exist_ok=True)

    with open(plistPath, "wb") as stream:
        progress.trace(f"Write {plistPath}")
        plistlib.dump(plist, stream)

    srcmain = apptemplate.setup.main(
        arch=arch, redirect_asl=redirect_stdout, use_old_sdk=use_old_sdk
    )
    destmain = os.path.join(platdir, kw["CFBundleExecutable"])

    (contents / "PkgInfo").write_text(
        kw["CFBundlePackageType"] + kw["CFBundleSignature"]
    )

    progress.trace(f"Copy {srcmain!r} -> {destmain!r}")
    copy(srcmain, destmain)
    make_exec(destmain)

    # XXX: Below here some pathlib.Path instances are converted
    # back to strings for compatibility with other code.
    # This will be changed when that legacy code has been updated.
    with importlib_resources.path(apptemplate.__name__, "lib") as p:
        mergetree(
            str(p),
            str(resources),
            condition,
            copy,
        )
    return str(app), plist
