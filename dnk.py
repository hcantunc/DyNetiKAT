import optparse
import os
import sys
import json
from time import perf_counter
from src.python.preprocess import Preprocessing
from src.python.dynetkat import DyNetKAT
from src.python.util import is_exe, is_json



direct = os.path.dirname(os.path.realpath(__file__))
output_folder = os.path.join(direct, 'output')
maude_preprocess_file = os.path.join(direct, 'src/maude/preprocess.maude')
maude_dnk_file = os.path.join(direct, 'src/maude/dnk.maude')
maude_path = ''
netkat_path = ''


if __name__ == "__main__":
    program_start = perf_counter()
    
    parser = optparse.OptionParser()
    parser.add_option("-t", "--threads", type="int", dest="num_threads",
                      help="number of threads (Default: the number of available cores in the system)")
    parser.add_option("-p", "--preprocessed", dest="preprocessed", default=False, action="store_true",
                      help="pass this option if the given input file is already preprocessed")
    parser.add_option("-v", "--netkat-version", dest="netkat_version", default="netkat-idd",
                      help="the version of the netkat tool: netkat-idd or netkat-automata (Default: netkat-idd)")
    parser.add_option("-s", "--time-stats", dest="time_stats", default=False, action="store_true",
                      help="reports the timing information.")
    (options, args) = parser.parse_args()

    if len(args) < 3:
        print("Error: provide the arguments <path_to_maude> <path_to_netkat> <input_file>.")
        sys.exit()

    if not os.path.exists(args[0]) or not is_exe(args[0]):
        print("Please provide the path to the Maude executable!")
        sys.exit()

    if not os.path.exists(args[1]) or not is_exe(args[1]):
        print("NetKAT tool could not be found in the given path!")
        sys.exit()

    if not is_json(args[2]) or not os.path.isfile(args[2]):
        print("Please provide a .json file!")
        sys.exit()

    maude_path = args[0]
    netkat_path = args[1]
    with open(args[2]) as f:
        data = json.load(f)
    data["file_name"] = data['module_name'] + ".maude"


    # preprocessing step
    preprocessing_start = perf_counter()
    preprocessor = Preprocessing(direct, maude_path, netkat_path, options.netkat_version, maude_preprocess_file,
                                 maude_dnk_file, options.preprocessed, options.num_threads)
    data = preprocessor.preprocess(data)
    if not options.preprocessed:
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        with open(os.path.join(output_folder, data["module_name"] + "_preprocessed.json"), 'w') as f:
            data['comm'] = list(data['comm']) #set is not json serializable
            json.dump(data, f, ensure_ascii=False, indent=4)
    preprocessing_stop = perf_counter() 


    # analysis step
    decision_procedure = DyNetKAT(direct, maude_path, netkat_path, options.netkat_version, 
                                  maude_preprocess_file, maude_dnk_file, options.num_threads)
    result = decision_procedure.decide(data)


    # clean up
    if os.path.exists(os.path.join(direct, data['file_name'])):
        os.remove(os.path.join(direct, data['file_name']))


    # report the results
    max_netkat_time = 0
    for (packet, prop_num), (v, netkat_time), in result.items():
        if v == "satisfied":
            print("Packet: {} - property: #{}: property satisfied.".format(packet, prop_num))
        elif v == "violated":
            print("Packet: {} - property: #{}: property violated.".format(packet, prop_num))
        elif v == "error":
            print("Packet: {} - property: #{}: an error occurred while checking this property."
                  .format(packet, prop_num))
        if netkat_time > max_netkat_time:
            max_netkat_time = netkat_time
                  
                  
    # report timing
    if options.time_stats:
        program_stop = perf_counter()
        print("Total time: {:.2f} seconds".format(program_stop-program_start))
        print("Preprocessing time: {:.2f} seconds".format(preprocessing_stop-preprocessing_start))
        print("NetKAT time: {:.2f} seconds".format(max_netkat_time))
