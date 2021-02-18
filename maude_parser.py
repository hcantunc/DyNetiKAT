import subprocess
import re
import os 



class MaudeComm:
    def __init__(self, maude_path, parse_file, normalize_file, out_file):
        self.maude_path = maude_path
        self.parse_file = parse_file
        self.normalize_file = normalize_file
        self.out_file = out_file

    def comm(self, program, cmd):
        proc = subprocess.Popen(['{} {} {}'.format(self.maude_path, program, cmd)],
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True,
                                cwd=os.path.dirname(os.path.realpath(__file__)))

        return proc.communicate()[0]     

    def process_solutions(self, output):
        solutions = output.decode('utf-8')
        split = re.search('result (.*?):', solutions).group(1)
        solutions = solutions.split('result {}:'.format(split), 1)[1]
        solutions = solutions.split('\nBye.\n', 1)[0]
        solutions = solutions.rstrip().lstrip()
        solutions = solutions.replace('\n', '').replace('    ', ' ')

        return solutions

    def export_file(self, filename, terms):
        f = open(filename, "w")
        f.write(terms)
        f.close()

    def parse(self, module, term):
        terms = 'red in {} : {} .'.format(module, term) 
        self.export_file(self.out_file, terms)
        output = self.comm(self.parse_file, self.out_file)
        output = self.process_solutions(output)

        if os.path.exists(self.out_file):
            os.remove(self.out_file)

        return output

    def normalize(self, module, term):
        terms = 'red in {} : {} .'.format(module, term) 
        self.export_file(self.out_file, terms)
        output = self.comm(self.normalize_file, self.out_file)
        output = self.process_solutions(output)
        
        if os.path.exists(self.out_file):
            os.remove(self.out_file)

        return output
