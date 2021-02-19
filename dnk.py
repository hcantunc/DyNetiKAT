import optparse 
import re
import os 
import sys
import json
from maude_parser import MaudeComm
from netkat_parser import NetKATComm
from multiprocessing import Process, Manager


direct = os.path.dirname(os.path.realpath(__file__))
parser_file = direct + '/parser.maude'
dna_file = direct + '/dna.maude'
maude_path = ''
netkat_path = ''



def extractNetkat(policy):
    split = [re.search('@NetKAT(.*)', x).group(1).rstrip().lstrip() for x in policy.split(';') if "@NetKAT" in x]
    return split

def extractComm(policy):
    split = [re.search('@Comm(.*)', x).group(1).rstrip().lstrip().replace('(','').replace(')','') for x in policy.split(';') if "@Comm" in x]
    return split

def insertRecursiveDefs(maude_file, module, recursive_variables, channels, fields, insert_equations):
    #check whether the module is already contained 
    with open(maude_file, "r") as in_file:
        buf = in_file.readlines()

    inside_module = False
    with open(maude_file, "w") as out_file:
        for line in buf:
            if "fmod {} is".format(module) in line :
                inside_module = True 
            elif "endfm" in line and inside_module == True:
                inside_module = False
            elif not inside_module:
                out_file.write(line)

    with open(maude_file, "r") as in_file:
        buf = in_file.readlines()

    lines = []
    if buf[-1] == "\n" and buf[-2] == "\n":
        lines.append("fmod {} is \n".format(module))
    elif buf[-1] == "\n":
        lines.append("\nfmod {} is \n".format(module))
    else:
        lines.append("\n\nfmod {} is \n".format(module))

    lines.append("\tprotecting DNA .\n")
    if insert_equations:
        lines.append("\tprotecting PROPERTY-CHECKING .\n\n")
    

    if len(recursive_variables) == 1:
        lines.append("\top {} : -> Recursive .\n".format(recursive_variables.keys[0]))
    elif len(recursive_variables) > 1:
        lines.append("\tops {} : -> Recursive .\n".format(' '.join(recursive_variables.keys())))

    channels = list(channels)
    if len(channels) == 1:
        lines.append("\top {} : -> Channel .\n".format(channels[0]))
    elif len(channels) > 1:
        lines.append("\tops {} : -> Channel .\n".format(' '.join(channels)))

    if len(fields) == 1:
        lines.append("\top {} : -> Field .\n\n".format(fields[0]))
    elif len(fields) > 1:
        lines.append("\tops {} : -> Field .\n\n".format(' '.join(fields)))

    if insert_equations:
        for k, v in recursive_variables.items():
            lines.append("\teq getRecPol({}) = {} .\n".format(k, v))

    lines.append("endfm")

    with open(maude_file, "a") as out_file:
        for line in lines:
            out_file.write(line)


def clean_maude_files(maude_file, module):
    with open(maude_file, "r") as in_file:
        buf = in_file.readlines()

    inside_module = False
    with open(maude_file, "w") as out_file:
        for line in buf:
            if "fmod {} is".format(module) in line :
                inside_module = True 
            elif "endfm" in line and inside_module == True:
                inside_module = False
            elif not inside_module:
                out_file.write(line)

    with open(maude_file, "r") as in_file:
        buf = in_file.readlines()

def compute_encapsulation_set(comm):
    delta_h = []
    for x in comm:
        channel, ft = x.split(',')
        delta_h.append("{} ! {}".format(channel, ft))
        delta_h.append("{} ? {}".format(channel, ft))
    return delta_h

def is_json(f):
  return len(f) > 5 and f[-5:] == ".json"

def is_exe(fpath):
    return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

def generate_outfile(number):
    return direct + '/output_{}.txt'.format(number)



if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option("-n", "--normalize", dest="normalize", action="store_true", help="")
    (options, args) = parser.parse_args()


    if len(args) < 3:
        print("Error: provide the arguments <path_to_maude> <path_to_netkat> <input_file>")
        sys.exit()

    if not os.path.exists(args[0]) or is_exe(args[0]) == False:
        print("Maude could not be found in the given path!")
        sys.exit()

    if not os.path.exists(args[1]) or is_exe(args[1]) == False:
        print("NetKAT tool could not be found in the given path!")
        sys.exit()

    if not is_json(args[2]) or os.path.isfile(args[2]) == False:
        print("Please provide a .json file")
        sys.exit()


    maude_path = args[0]
    netkat_path = args[1]

    with open(args[2]) as f:
        data = json.load(f)
    
    netkat_parser = NetKATComm(netkat_path, generate_outfile("netkat"))
    maude_parser = MaudeComm(maude_path, parser_file, dna_file, generate_outfile("maude"))

    data["comm"] = set()

    if options.normalize:
        # if the policies are not already normalized
        # we need to check if any of the NetKAT policies are equal to 0
        # if some NetKAT term is equal to 0 then 
        # what follows after that term is insignificant
        insertRecursiveDefs(parser_file, data['module_name'], data['recursive_variables'], data['channels'].values(), data['fields'], False)

        parsed_terms = {}
        netkat_terms = {}
        for k, v in data['recursive_variables'].items():
            # parse with maude and extract netkat terms
            parsed_terms[k] = maude_parser.parse(data['module_name'], v)
            netkat_terms[k] = extractNetkat(parsed_terms[k])
            comm = extractComm(parsed_terms[k])
            for x in comm:
                data['comm'].add(x)
            

            for x in netkat_terms[k]:
                #check if the NetKAT terms are equal to 0
                #if so rewrite them as 0 so that 0 ; P = bot axiom can apply
                netkat_result = {}
                netkat_result = netkat_parser.parse(x, "drop", netkat_result)
                if netkat_result == 'true':
                    data['recursive_variables'][k] = data['recursive_variables'][k].replace(x, 'zero') 
    
        with open("normalized.json", 'w') as f:
            json.dump(data['recursive_variables'], f, ensure_ascii=False, indent=4)
    else:
        # if normalize is false then just extract the  
        # communication terms to comptue the delta h set 
        insertRecursiveDefs(parser_file, data['module_name'], data['recursive_variables'], data['channels'].values(), data['fields'], False)

        parsed_terms = {}
        for k, v in data['recursive_variables'].items():
            parsed_terms[k] = maude_parser.parse(data['module_name'], v)
            comm = extractComm(parsed_terms[k])
            for x in comm:
                data['comm'].add(x)


    insertRecursiveDefs(dna_file, data['module_name'], data['recursive_variables'], data['channels'].values(), data['fields'], True)


    # perform property checking
    pi_program = data['program']
    delta_h = compute_encapsulation_set(data["comm"])   
    

    p = "delta{" + ', '.join(delta_h) + "}(pi{"+ str(data['pi_unfolding']) +"}(" + pi_program + "))"
    result = maude_parser.normalize(data['module_name'], p)


    processes = {}
    manager = Manager()
    return_dict = manager.dict()

    for q in range(0, len(data['in_packets'])):
        counter = 0 

        for prop, prop_result in data['properties'][str(q)]:
            counter += 1
            prop = prop.replace("@Program", result).replace("{", "").replace("}", ", RSet:TermSet")

            result2 = maude_parser.normalize(data['module_name'], prop)
            netkat_parser = NetKATComm(netkat_path, generate_outfile(str(q) + "_" + str(counter)))
            processes[(q, counter, prop_result)] = Process(target=netkat_parser.parse, args=("(({}) . ({}) . ({}))".format(data['in_packets'][q], result2, data['out_packets'][q]), "drop", return_dict))
            processes[(q, counter, prop_result)].start()



    for (q, counter, prop_result), p in processes.items():
        p.join()

        netkat_result = return_dict[generate_outfile(str(q) + "_" + str(counter))]

        if (netkat_result == "false" and prop_result == "!0") or (netkat_result == "true" and prop_result == "=0"):
            print("Packet: #{}, property: #{}: property satisfied.".format(q, counter))
        else:
            print("Packet: #{}, property: #{}: property violated.".format(q, counter))



    #remove the inserted module declarations in the maude files
    for x in [parser_file, dna_file]:
        clean_maude_files(x, data['module_name'])