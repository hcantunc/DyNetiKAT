import os 
import re
import subprocess
import numpy as np
from src.python.util import export_file, execute_cmd



class NetKATComm:
    def __init__(self, direct, netkat_path, netkat_version, out_file):
        self.direct = direct
        self.netkat_path = netkat_path
        self.netkat_version = netkat_version
        self.out_file = out_file


    def comm(self, file1, file2):
        '''Generates a system command to run the NetKAT tool on the given input files and executes it.'''
        cmd = ['{} equiv {} {}'.format(self.netkat_path, file1, file2)]
        return execute_cmd(cmd, self.direct)


    def process_output(self, output):
        '''Parses the output obtained from the NetKAT tool.'''
        try:
            if self.netkat_version == "netkat-idd":
                return re.search('expressions equivalent: (.*)', output).group(1)
            elif self.netkat_version == "netkat-automata":
                return re.search('Bisimulation result: (.*)', output).group(1)
        except Exception:
            return None


    def tool_format(self, term1, term2):
        '''Converts the given terms into the netkat tool's format.'''
        if self.netkat_version == "netkat-idd":
            # convert the numbers that appear inside the terms into binary format
            terms = term1 + term2
            digits = set([int(x) for x in re.findall(r'\d+', terms)])
            max_digit = max(digits)
            width = len(np.binary_repr(max_digit))
            for x in digits:
                term1 = re.sub(r'\b'+str(x)+r'\b', np.binary_repr(x, width=width), term1)
                term2 = re.sub(r'\b'+str(x)+r'\b', np.binary_repr(x, width=width), term2)

            term1 = term1.replace('<-', ':=').replace('zero', 'F').replace('one', 'T').replace('.', ';').replace('"', '')
            term2 = term2.replace('<-', ':=').replace('zero', 'F').replace('one', 'T').replace('.', ';').replace('"', '')
        elif self.netkat_version == "netkat-automata":
            term1 = term1.replace('<-', ':=').replace('zero', 'drop').replace('one', 'pass').replace('.', ';').replace('"', '')
            term2 = term2.replace('<-', ':=').replace('zero', 'drop').replace('one', 'pass').replace('.', ';').replace('"', '')

        return term1, term2


    def execute(self, term1, term2):
        '''
        Generates two files with NetKAT expressions, passes them to 
        the NetKAT tool, parses the obtained result and returns it.
        '''
        outfile_1 = '{}_1.text'.format(self.out_file.split('.')[0])
        outfile_2 = '{}_2.text'.format(self.out_file.split('.')[0])

        term1, term2 = self.tool_format(term1, term2)

        export_file(outfile_1, term1)
        export_file(outfile_2, term2)

        output, error = self.comm(outfile_1, outfile_2)
        output = self.process_output(output)

        if os.path.exists(outfile_1):
            os.remove(outfile_1)
        if os.path.exists(outfile_2):
            os.remove(outfile_2)

        return output, error
