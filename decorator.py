from __future__ import annotations
import hashlib
import os
from pathlib import Path
import tarfile

import rich_click as click
from flytekit import task
from flytekit.tools.repo import find_common_root
from finder import find_local_imports_recursively

def set_permissions(tarinfo: tarfile.TarInfo) -> tarfile.TarInfo:
    """adds concistency in tar-ball"""
    tarinfo.mode = int("0755", base=8)
    tarinfo.mtime = 0
    tarinfo.uid = 1
    tarinfo.gid = 1
    tarinfo.uname = ""
    tarinfo.gname = ""
    tarinfo.pax_headers = {}
    return tarinfo


def fast_package(
    path: os.PathLike,
    source: os.PathLike,
    output_dir: os.PathLike,
) -> os.PathLike:
    """
    Find all local files that are imported by path 
    add them to a tar to later get checksum from
    """

    archive_fname = "fast-package.tar.gz"
    archive_fname = Path(output_dir) / archive_fname
    archive_fname.unlink(missing_ok=True)

    with tarfile.open(archive_fname, "w", dereference=False) as tar:

        files = [
            x[1] for x in list(set(find_local_imports_recursively(path, source)))
        ]

        for ws_file in sorted(files):
            tar.add(
                os.path.join(source, ws_file),
                arcname=ws_file,
                recursive=False,
                filter=set_permissions,
            )

    return archive_fname

def dynamic_cache_version(fn: function) -> str:
    """get cache version

    Find the file that is decorated with @override_task
    Check which files it imports
    Run a md5 checksum on it and return

    Args:
        fn (function): _description_

    Returns:
        str: _description_
    """
    path = Path(fn.__code__.co_filename)
    detected_root = find_common_root([path])

    seek_path = path.relative_to(detected_root)
    fancy_path = seek_path.with_suffix("") / fn.__name__
    fancy_path = str(fancy_path).replace("/", ".")

    out = fast_package(str(seek_path), detected_root, detected_root + "/.flyte_output")
    out = Path(out)
    resolved_md5 = hashlib.md5(out.read_bytes()).hexdigest()
    click.secho(
        f"Setting {fancy_path} to cache version: {resolved_md5}",
        fg="green",
    )
    return resolved_md5




def override_task(**kwargs):
    """Overwrites Flyte's @task decorator to allow extra controls."""

    def wrapper(fn):
        fn.name = fn.__name__

        cache_version = dynamic_cache_version(fn)
        kwargs['cache'] = True
        kwargs['cache_version'] = cache_version
        kwargs['cache_serialize'] = False

        return task(**kwargs)(fn)

    return wrapper


### Example

from xyz import foo
import bar
import baz as buzz

@override_task(container_image="some-docker")
def get_annotation(name: str) -> str:
    return f"Hello {name}!"