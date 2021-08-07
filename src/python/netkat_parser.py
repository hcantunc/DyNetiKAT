import os 
import re
import subprocess
import numpy as np



class NetKATComm:
    def __init__(self, direct, netkat_path, out_file):
        self.direct = direct
        self.netkat_path = netkat_path
        self.out_file = out_file


    def comm(self, file1, file2):
        proc = subprocess.run(['{} equiv {} {}'.format(self.netkat_path, file1, file2)],
                              stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              shell=True,
                              cwd=self.direct)

        return proc.stdout.decode('utf-8')


    def process_solutions(self, output):
        split = re.search('expressions equivalent: (.*)', output).group(1)
        return split


    def export_file(self, filename, terms):
        with open(filename, "w") as f:
            f.write(terms)


    def tool_format(self, term1, term2):
        terms = term1 + term2
        digits = set([int(x) for x in re.findall(r'\d+', terms)])
        max_digit = max(digits)
        width = len(np.binary_repr(max_digit))
        for x in digits:
            term1 = re.sub(r'\b'+str(x)+r'\b', np.binary_repr(x, width=width), term1)
            term2 = re.sub(r'\b'+str(x)+r'\b', np.binary_repr(x, width=width), term2)

        term1 = term1.replace('<-', ':=').replace('zero', 'F').replace('one', 'T').replace('.', ';').replace('"', '')
        term2 = term2.replace('<-', ':=').replace('zero', 'F').replace('one', 'T').replace('.', ';').replace('"', '')

        return term1, term2


    def parse(self, term1, term2):
        outfile_1 = '{}_1.text'.format(self.out_file.split('.')[0])
        outfile_2 = '{}_2.text'.format(self.out_file.split('.')[0])

        term1, term2 = self.tool_format(term1, term2)

        self.export_file(outfile_1, term1)
        self.export_file(outfile_2, term2)

        output = self.comm(outfile_1, outfile_2)
        output = self.process_solutions(output)

        if os.path.exists(outfile_1):
            os.remove(outfile_1)
        if os.path.exists(outfile_2):
            os.remove(outfile_2)

        return output
