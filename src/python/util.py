import os
import sys
import subprocess 



def is_json(fpath):
    '''Takes a file path and checks if the file is in .json format.'''
    return len(fpath) > 5 and fpath[-5:] == ".json"


def is_exe(fpath):
    '''Takes a file path and checks if the file is an executable.'''
    return os.path.isfile(fpath) and os.access(fpath, os.X_OK)


def generate_error_message(tool_name, term_name, term, error, terminate_exec=False):
    '''Generates an error message with respect to the given arguments.'''
    print("\n{} could not parse the following term:\n{} --> {}\nError message:\n{}".format(tool_name, term_name, term, error))
    if terminate_exec:
        print("\nTerminating the procedure.")
        sys.exit()


def generate_outfile(direct, name):
    '''Generates an output file with respect to the given path and name.'''
    return os.path.join(direct, 'output_{}.txt'.format(name))


def export_file(filename, contents):
    '''Exports a file with the given name and contents.'''
    with open(filename, "w") as f:
        f.write(contents)


def execute_cmd(cmd, direct):
    '''Executes a given system command and returns the obtained output.'''
    proc = subprocess.run(cmd, stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          shell=True)

    return proc.stdout.decode('utf-8'), proc.stderr.decode('utf-8')
