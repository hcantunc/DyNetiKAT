import os
import re
import threading
from multiprocessing import Pool
from src.python.maude_parser import MaudeComm
from src.python.netkat_parser import NetKATComm
from src.python.util import generate_error_message, generate_outfile



class Preprocessing:
    def __init__(self, direct, maude_path, netkat_path, netkat_version, maude_preprocess_file, 
                 maude_dnk_file, preprocessed=False, num_threads=None):
        self.direct = direct
        self.maude_path = maude_path
        self.netkat_path = netkat_path
        self.netkat_version = netkat_version
        self.maude_preprocess_file = maude_preprocess_file
        self.maude_dnk_file = maude_dnk_file
        self.preprocessed = preprocessed
        self.num_threads = num_threads


    def generate_maude_file(self, file_name, module_name, import_module, recursive_variables, channels, insert_equations):
        '''Generates the Maude module that will be utilized for processing the given input file.'''
        lines = []

        lines.append("load {}".format(import_module))

        lines.append("\n\nfmod {} is \n".format(module_name))

        lines.append("\tprotecting DNA .\n")
        if insert_equations:
            lines.append("\tprotecting PROPERTY-CHECKING .\n\n")

        if len(recursive_variables) == 1:
            lines.append("\top {} : -> Recursive .\n".format(recursive_variables.keys[0]))
        elif len(recursive_variables) > 1:
            lines.append("\tops {} : -> Recursive .\n".format(' '.join(recursive_variables.keys())))

        if len(channels) == 1:
            lines.append("\top {} : -> Channel .\n".format(channels[0]))
        elif len(channels) > 1:
            lines.append("\tops {} : -> Channel .\n\n".format(' '.join(channels)))

        if insert_equations:
            for k, v in recursive_variables.items():
                lines.append("\teq getRecPol({}) = {} .\n".format(k, v))

        lines.append("endfm")

        with open(file_name, "w") as out_file:
            for line in lines:
                out_file.write(line)


    def extract_netkat(self, policy):
        '''Extracts the NetKAT terms in the given input.'''
        netkat_terms = [re.search('@NetKAT(.*)', x).group(1).rstrip().lstrip() for x in policy.split(';') if "@NetKAT" in x]
        return ['"' + re.search('"(.*)"', x).group(1).rstrip().lstrip() + '"' for x in netkat_terms if '"' in x]


    def extract_comm_terms(self, policy):
        '''Extracts the communication terms in the given input.'''
        return [re.search('@Comm(.*)', x).group(1).rstrip().lstrip() for x in policy.split(';') if "@Comm" in x]


    def netkat_process(self, x, k, i):
        '''This method calls the NetKAT decision procedure and checks if the given term is equal to 0.'''
        netkat_parser = NetKATComm(self.direct, self.netkat_path, self.netkat_version, 
                                   generate_outfile(self.direct, "preprocess_netkat_{}_{}".format(k, i)))
        result, error = netkat_parser.execute(x, "zero")
        if result is None:
            generate_error_message("NetKAT tool", k, x, error, True)
        return result


    def preprocess(self, data):
        '''The main method for preprocessing the given input file.'''
        if not self.preprocessed:
            maude_parser = MaudeComm(self.direct, self.maude_path, generate_outfile(self.direct, "preprocess_maude"))

            # if the policies are not already normalized we need to check if any of the NetKAT policies are
            # equal to 0. If some NetKAT term is equal to 0 then what follows after that term is insignificant
            self.generate_maude_file(os.path.join(self.direct, data['file_name']), data['module_name'],
                                     self.maude_preprocess_file, data['recursive_variables'],
                                     data['channels'], False)

            parsed_terms = {}
            netkat_terms = {}

            netkat_results = {}

            if self.num_threads is None:
                netkat_pool = Pool()
            else:
                netkat_pool = Pool(processes=self.num_threads)

            data["comm"] = set()
            for k, v in data['recursive_variables'].items():
                # parse with maude and extract netkat terms and communication terms
                parsed_terms[k], error = maude_parser.execute(os.path.join(self.direct, data['file_name']),
                                                              data['module_name'], v)

                if parsed_terms[k] is None:
                    generate_error_message("Maude", k, v, error, True)

                netkat_terms[k] = self.extract_netkat(parsed_terms[k])

                for i, x in enumerate(netkat_terms[k]):
                    # check if the NetKAT terms are equal to 0
                    # if so rewrite them as 0 so that 0 ; P = bot axiom can apply
                    netkat_results[(k, i)] = netkat_pool.apply_async(self.netkat_process, args=(x, k, i))

                # extract the policies that are being communicated.
                # these are going to be used while using the encapsulation operator
                comm = self.extract_comm_terms(parsed_terms[k])
                for x in comm:
                    data['comm'].add(x)

            netkat_pool.close()
            netkat_pool.join()
            for (k, i), v in netkat_results.items():
                if v.get() == 'true':
                    data['recursive_variables'][k] = data['recursive_variables'][k].replace(netkat_terms[k][i], 'zero')

        self.generate_maude_file(data['file_name'], data['module_name'], self.maude_dnk_file, data['recursive_variables'], data['channels'], True)

        return data
