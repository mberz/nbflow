import sys
import os
import shutil

from textwrap import dedent
from .util import run_command, clear_notebooks, create_notebook
import json


def test_nbflow_no_args(temp_cwd):
    run_command([sys.executable, "-m", "nbflow"], retcode=1)


def test_notebook_long_excecution(temp_cwd, sconstruct):
    # copy example files
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "example"))
    shutil.copytree(os.path.join(root, "analyses"), "analyses")
    shutil.copy(os.path.join(root, "SConstruct"), "SConstruct")
    clear_notebooks("analyses")

    run_command(["scons","timeout=1"], retcode=2)

def test_example(temp_cwd):
    # copy example files
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "example"))
    shutil.copytree(os.path.join(root, "analyses"), "analyses")
    shutil.copy(os.path.join(root, "SConstruct"), "SConstruct")
    clear_notebooks("analyses")

    # check the explicit output of the nbflow command
    output = run_command([sys.executable, "-m", "nbflow", "analyses"])
    if sys.platform == 'win32':
        json_path = os.path.abspath(os.path.realpath(temp_cwd))
        json_escaped_path = json_path.replace("\\", "\\\\")
        expected = dedent(
            """
            {
              "analyses\\\\analyze_data.ipynb": {
                "sources": [
                  "%(path)s\\\\results\\\\data.json"
                ],
                "targets": [
                  "%(path)s\\\\results\\\\stats.json"
                ]
              },
              "analyses\\\\gen_data.ipynb": {
                "sources": [],
                "targets": [
                  "%(path)s\\\\results\\\\data.json"
                ]
              }
            }
            """ % dict(path=json_escaped_path)
        ).lstrip()
    else:
        expected = dedent(
            """
            {
              "analyses/analyze_data.ipynb": {
                "sources": [
                  "%(path)s/results/data.json"
                ],
                "targets": [
                  "%(path)s/results/stats.json"
                ]
              },
              "analyses/gen_data.ipynb": {
                "sources": [],
                "targets": [
                  "%(path)s/results/data.json"
                ]
              }
            }
            """ % dict(path=os.path.abspath(os.path.realpath(temp_cwd)))
        ).lstrip()

    output_decoded = output.decode('UTF-8')
    json_output = json.loads(output_decoded)
    json_expected = json.loads(expected)
    assert json_output == json_expected

    # try running scons
    if sys.platform == 'win32':
        expected = dedent(
            """
            scons: Reading SConscript files ...
            scons: done reading SConscript files.
            scons: Building targets ...
            analyses\\gen_data.ipynb --> results\\data.json
            analyses\\analyze_data.ipynb --> results\\stats.json
            scons: done building targets.
            """
        ).lstrip()
    else:
        expected = dedent(
            """
            scons: Reading SConscript files ...
            scons: done reading SConscript files.
            scons: Building targets ...
            analyses/gen_data.ipynb --> results/data.json
            analyses/analyze_data.ipynb --> results/stats.json
            scons: done building targets.
            """
        ).lstrip()

    output = run_command(["scons"])

    output_replace = output.decode().replace('\r', '')
    assert output_replace.encode('utf-8') == expected.encode('utf-8')

    # run scons again, make sure it doesn't want to do anything
    output = run_command(["scons", "-n"])
    expected = dedent(
        """
        scons: Reading SConscript files ...
        scons: done reading SConscript files.
        scons: Building targets ...
        scons: `.' is up to date.
        scons: done building targets.
        """
    ).lstrip()

    output_replace = output.decode().replace('\r', '')
    output_replace = output_replace.replace('\nNone', '')
    assert output_replace.encode('utf-8') == expected.encode('utf-8')


def test_empty_notebook(temp_cwd, sconstruct):
    create_notebook("test.ipynb", [
        "__depends__ = []\n__dest__ = None"
    ])
    output = run_command(["scons"])
    expected = dedent(
        """
        scons: Reading SConscript files ...
        scons: done reading SConscript files.
        scons: Building targets ...
        test.ipynb --> None
        scons: done building targets.
        """
    ).lstrip()

    output_replace = output.decode().replace('\r', '')
    assert output_replace.encode('utf-8') == expected.encode('utf-8')


def test_notebook_with_errors(temp_cwd, sconstruct):
    create_notebook("test.ipynb", [
        "__depends__ = []\n__dest__ = None",
        "assert False"
    ])
    run_command(["scons"], retcode=2)


def test_notebook_without_depends(temp_cwd, sconstruct):
    create_notebook("test.ipynb", [
        "__dest__ = None"
    ])
    output = run_command(["scons"])
    expected = dedent(
        """
        scons: Reading SConscript files ...
        scons: done reading SConscript files.
        scons: Building targets ...
        scons: `.' is up to date.
        scons: done building targets.
        """
    ).lstrip()

    output_replace = output.decode().replace('\r', '')
    assert output_replace.encode('utf-8') == expected.encode('utf-8')


def test_notebook_without_dest(temp_cwd, sconstruct):
    create_notebook("test.ipynb", [
        "__depends__ = []"
    ])
    output = run_command(["scons"], retcode=2)


def test_multiple_notebooks_with_no_dests(temp_cwd, sconstruct):
    create_notebook("test1.ipynb", [
        "__depends__ = []\n__dest__ = []"
    ])
    create_notebook("test2.ipynb", [
        "__depends__ = []\n__dest__ = []"
    ])
    output = run_command(["scons"])
    expected = dedent(
        """
        scons: Reading SConscript files ...
        scons: done reading SConscript files.
        scons: Building targets ...
        test1.ipynb --> None
        test2.ipynb --> None
        scons: done building targets.
        """
    ).lstrip()

    output_replace = output.decode().replace('\r', '')
    assert output_replace.encode('utf-8') == expected.encode('utf-8')
