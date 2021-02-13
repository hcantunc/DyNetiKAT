import subprocess
import re
import os 

class NetKATComm:
    def __init__(self, netkat_path, out_file):
        self.netkat_path = netkat_path
        self.out_file = out_file

    def comm(self, program):
        proc = subprocess.Popen(['{} {}'.format(self.netkat_path, program)],
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True,
                                cwd=os.path.dirname(os.path.realpath(__file__)))

        return proc.communicate()[0]     

    def process_solutions(self, output):
        solutions = output.decode('utf-8')
        split = re.search('Bisimulation result: (.*)', solutions).group(1)
        return split

    def export_file(self, filename, terms):
        f = open(filename, "w")
        f.write(terms)
        f.close()

    def toolFormat(self, term):
        return term.replace('<-', ':=').replace('zero', 'drop').replace('one', 'pass').replace('.', ';')

    def parse(self, term1, term2, return_dict=None):
        terms = '({}) == ({})'.format(self.toolFormat(term1), self.toolFormat(term2)) 
        self.export_file(self.out_file, terms)
        output = self.comm(self.out_file)
        output = self.process_solutions(output)

        if return_dict != None:
            return_dict[self.out_file] = output

        if os.path.exists(self.out_file):
            os.remove(self.out_file)

        return output
