# bash_importer.py

import importlib.util
import os
import shlex
import sys
from typing import Optional, Tuple, List


def _convert_bash_line(line) -> Tuple[str, Optional[List[str]]]:
    cmd, *args = shlex.split(line)
    if cmd == 'ls':
        # Assume simple form, e.g. 'ls [path]'.
        if args:
            assert len(args) == 1
            assert not args[0].startswith('-')
            pattern = args[0]
        else:
            pattern = '*'
        return f"print('  '.join(glob.glob('{pattern}')))", ['glob']

    elif cmd == 'echo':
        return f"print('{' '.join(args)}')", None

    elif cmd == 'cp':
        assert len(args) == 2
        path1 = f"os.path.abspath(os.path.expanduser('{args[0]}'))"
        path2 = f"os.path.abspath(os.path.expanduser('{args[1]}'))"
        return f"shutil.copy2({path1}, {path2})", ['shutil', 'os']

    else:
        raise RuntimeError("Unrecognised command")



def _bash_to_python(file_path):
    with open(file_path, 'r') as f:
        bash_lines = f.readlines()
    bash_lines = [stmt.strip() for line in bash_lines for stmt in line.split(';') if stmt.strip()]
    converted_lines = []
    all_imports = set()
    for line in bash_lines:
        python_line, line_imports = _convert_bash_line(line)
        converted_lines.append(python_line)
        if line_imports:
            all_imports.update(line_imports)

    imports = '\n'.join(['import ' + i for i in all_imports])
    body = '\n    '.join(converted_lines) if converted_lines else 'pass'
    code = f"""\
# This code was auto-generated as a conversion of {file_path}.

{imports}

def main():
    {body}

if __name__ == '__main__':
    main()
    """
    return code


class BashImporter:
    @classmethod
    def find_spec(cls, modname, path=None, target=None):
        # print(f"file_spec({modname, path})", file=sys.stderr)
        if path is None:
            path = sys.path
        for p in path:
            full_path = os.path.join(p, modname + '.sh')
            if os.path.exists(full_path):
                return importlib.util.spec_from_loader(modname, BashLoader(), origin=full_path)
        return None


class BashLoader:
    def create_module(self, spec):
        return None

    def exec_module(self, module):
        # print(f"exec_module({module})", file=sys.stderr)
        try:
            module.__file__ = module.__spec__.origin
            code = _bash_to_python(module.__spec__.origin)
            print("Generated code:\n" + code, file=sys.stderr)
            code_obj = compile(code, module.__spec__.origin, 'exec')
            exec(code_obj, module.__dict__)
        except Exception as e:
            raise ImportError(f"Failed to import module {module.name}") from e


def install_importer():
    sys.meta_path.append(BashImporter)
