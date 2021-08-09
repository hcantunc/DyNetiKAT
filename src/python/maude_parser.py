import subprocess
import re
import os
from src.python.util import export_file, execute_cmd



class MaudeComm:
    def __init__(self, direct, maude_path, out_file):
        self.direct = direct
        self.maude_path = maude_path
        self.out_file = out_file


    def comm(self, program, maude_input_file):
        '''Generates a system command to run Maude on the given input file and executes it.'''
        cmd = ['{} {} {}'.format(self.maude_path, program, maude_input_file)]
        return execute_cmd(cmd, self.direct)


    def process_output(self, output):
        '''Parses the output obtained from Maude.'''
        try:
            split = re.search('result (.*?):', output).group(1)
            output = output.split('result {}:'.format(split), 1)[1]
            output = output.split('\nBye.\n', 1)[0]
            output = output.rstrip().lstrip()
            output = output.replace('\n', '').replace('    ', ' ')
            return output
        except Exception:
            return None
        

    def execute(self, file_name, module, term):
        '''
        Generates a Maude command to parse a given term, 
        executes it and returns the parsed result.
        '''
        terms = 'red in {} : {} .'.format(module, term)
        export_file(self.out_file, terms)
        output, error = self.comm(file_name, self.out_file)
        output = self.process_output(output)

        if os.path.exists(self.out_file):
            os.remove(self.out_file)

        return output, error
