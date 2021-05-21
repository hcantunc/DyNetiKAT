import subprocess
import re
import os 



class MaudeComm:
    def __init__(self, direct, maude_path, out_file):
        self.direct = direct
        self.maude_path = maude_path
        self.out_file = out_file


    def comm(self, program, cmd):
        proc = subprocess.run(['{} {} {}'.format(self.maude_path, program, cmd)],
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True,
                                cwd=self.direct)

        return proc.stdout.decode('utf-8')    


    def process_solutions(self, output):
        split = re.search('result (.*?):', output).group(1)
        output = output.split('result {}:'.format(split), 1)[1]
        output = output.split('\nBye.\n', 1)[0]
        output = output.rstrip().lstrip()
        output = output.replace('\n', '').replace('    ', ' ')
        return output


    def export_file(self, filename, terms):
        with open(filename, "w") as f:
            f.write(terms)
        

    def parse(self, file_name, module, term):
        terms = 'red in {} : {} .'.format(module, term) 
        self.export_file(self.out_file, terms)
        output = self.comm(file_name, self.out_file)
        output = self.process_solutions(output)
        
        if os.path.exists(self.out_file):
            os.remove(self.out_file)

        return output



