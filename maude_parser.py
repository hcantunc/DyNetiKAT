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

    def process_match_solutions(self, output, match_terms):
        solutions = output.decode('utf-8')
        result = {}

        if "No match." in solutions:
            return None
        else:
            split = re.findall('Solution [0-9]*', solutions)
            split.append("Bye")

            indv_sol = []
            
            for i, x in enumerate(split):
                if "Bye" in x:
                    break
                solutions = solutions.split(x, 1)[1]
                solutions = solutions.split('\n')
                current_solution = ""
                for y in solutions:
                    if split[i + 1] in y:
                        break
                    if "-->" in y:
                        current_solution = current_solution + "\n" + y
                    elif "    " in y:
                        current_solution = current_solution + " " + y
                indv_sol.append(current_solution)
                solutions = '\n'.join(solutions)
            
            for i, x in enumerate(indv_sol):
                for z in x.rstrip().lstrip().split('\n'):
                    k = re.search('(.*?) -->', z).group().replace('\n', '').replace('    ', ' ').replace('-->', '').rstrip().lstrip()
                    match_terms[k] = z.split("-->")[1].replace('\n', '').replace('    ', ' ').rstrip().lstrip()
                result[i] = match_terms.copy()
        return result

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
