import json
import os
import sys
import subprocess as sp
from functools import partial

import nbconvert


def build_cmd(notebook, timeout):
    cmd = [
        "jupyter", "nbconvert",
        "--log-level=ERROR",
        "--ExecutePreprocessor.timeout=" + timeout,
        "--execute",
        "--inplace",
        "--to", "notebook"
    ]

    if nbconvert.__version__ < '4.2.0':
        cmd.extend(['--output', notebook])
    cmd.append(notebook)

    return cmd

def build_notebook(target, source, env, timeout="120"):
    notebook = str(source[0])
    code = sp.call(build_cmd(notebook, timeout))
    if code != 0:
        raise RuntimeError("Error executing notebook")

    # we need to touch each of the targets so that they have a later
    # modification time than the source -- otherwise scons will think that the
    # targets always are out of date and need to be rebuilt
    for t in target:
        if not str(t).startswith('.phony'):
            os.utime(str(t), None)

    return None


def build_cmd_script(script):
    return ['python', script]


def build_script(target, source, env, script, timeout='120'):
    notebook = str(source[0])
    script_dir, nbook = os.path.split(os.path.abspath(notebook))
    code = sp.call(build_cmd_script(nbook), cwd=script_dir)
    if code != 0:
        raise RuntimeError("Error executing script")


def build_func(target, source, env, script, timeout='120'):
    ext = os.path.splitext(os.path.basename(script))[1]
    if ext == '.py':
        build_script(target, source, env, script, timeout)
    elif ext == '.ipynb':
        build_notebook(target, source, env, timeout)

    return None

def print_cmd_line(s, targets, sources, env):
    """s       is the original command line string
       targets is the list of target nodes
       sources is the list of source nodes
       env     is the environment"""
    if len(targets) == 0:
        sys.stdout.write("%s --> None\n"% str(sources[0]))
    else:
        for target in targets:
            if str(target).startswith('.phony'):
                target = 'None'
            sys.stdout.write("%s --> %s\n"% (str(sources[0]), str(target)))


def setup(env, directories, args):
    env['PRINT_CMD_LINE_FUNC'] = print_cmd_line
    env.Decider('timestamp-newer')
    DEPENDENCIES = json.loads(sp.check_output([sys.executable, "-m", "nbflow"] + directories).decode('UTF-8'))
    timeout = args.get('timeout', None)
    if timeout is not None:
        build_notebook_timeout = partial(build_notebook, timeout=str(timeout))
    else:
        build_notebook_timeout = build_notebook
    for script in DEPENDENCIES:
        deps = DEPENDENCIES[script]
        if len(deps['targets']) == 0:
            targets = ['.phony_{}'.format(script)]
        else:
            targets = deps['targets']
        build_func_partial = partial(build_func, script=script)
        env.Command(targets, [script] + deps['sources'], build_func_partial)
