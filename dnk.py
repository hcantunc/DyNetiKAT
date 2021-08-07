import optparse
import os
import sys
import json
from src.python.preprocess import Preprocessing
from src.python.dynetkat import DyNetKAT



direct = os.path.dirname(os.path.realpath(__file__))
output_folder = direct + '/output'
maude_preprocess_file = direct + '/src/maude/preprocess.maude'
maude_dnk_file = direct + '/src/maude/dnk.maude'
maude_path = ''
netkat_path = ''



def is_json(fpath):
    return len(fpath) > 5 and fpath[-5:] == ".json"


def is_exe(fpath):
    return os.path.isfile(fpath) and os.access(fpath, os.X_OK)


if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option("-t", "--threads", type="int", dest="num_threads",
                      help="number of threads (Default: the number of available cores in the system)")
    parser.add_option("-p", "--preprocessed", dest="preprocessed", default=False, action="store_true",
                      help="pass this option if the given input file is already preprocessed")
    (options, args) = parser.parse_args()

    if len(args) < 3:
        print("Error: provide the arguments <path_to_maude> <path_to_netkat> <input_file>.")
        sys.exit()

    if not os.path.exists(args[0]) or not is_exe(args[0]):
        print("Maude could not be found in the given path!")
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
    preprocessor = Preprocessing(direct, maude_path, netkat_path, maude_preprocess_file,
                                 maude_dnk_file, options.preprocessed, options.num_threads)
    data = preprocessor.preprocess(data)
    if not options.preprocessed:
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        with open(os.path.join(output_folder, data["module_name"] + "_preprocessed.json"), 'w') as f:
            data['comm'] = list(data['comm']) #set is not json serializable
            json.dump(data, f, ensure_ascii=False, indent=4)


    # analysis step
    decision_procedure = DyNetKAT(direct, maude_path, netkat_path, maude_preprocess_file,
                                  maude_dnk_file, options.num_threads)
    result = decision_procedure.decide(data)


    # clean up
    if os.path.exists(data['file_name']):
        os.remove(data['file_name'])


    # report the results
    for (packet, prop_num), v in result.items():
        prop_type = data['properties'][str(packet)][prop_num][0]
        prop_result = data['properties'][str(packet)][prop_num][2]

        if v == "error":
            print("Packet: #{} - property: #{}: an error occurred while checking this property."
                  .format(packet, prop_num))
        elif prop_type == "r":
            #reachability property
            if (v == "false" and prop_result == "!0") or (v == "true" and prop_result == "=0"):
                print("Packet: #{} - property: #{}: property satisfied.".format(packet, prop_num))
            else:
                print("Packet: #{} - property: #{}: property violated.".format(packet, prop_num))
        elif prop_type == "w":
            #waypointing property
            if v == "true":
                print("Packet: #{} - property: #{}: property satisfied.".format(packet, prop_num))
            else:
                print("Packet: #{} - property: #{}: property violated.".format(packet, prop_num))
