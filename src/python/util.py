import os
import sys
import subprocess 



def is_json(fpath):
    return len(fpath) > 5 and fpath[-5:] == ".json"


def is_exe(fpath):
    return os.path.isfile(fpath) and os.access(fpath, os.X_OK)


def error_handling(tool_name, term_name, term, error, terminate_exec=False):
    print("\n{} could not parse the following term:\n{} --> {}\nError message:\n{}".format(tool_name, term_name, term, error))
    if terminate_exec:
        print("\nTerminating the procedure.")
        sys.exit()


def export_file(filename, terms):
    with open(filename, "w") as f:
        f.write(terms)


def execute_cmd(cmd, direct):
    proc = subprocess.run(cmd, stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          shell=True,
                          cwd=direct)

    return proc.stdout.decode('utf-8'), proc.stderr.decode('utf-8') 