import optparse 
import re
import os 
import sys
import json
import time
from python_sources.preprocess import Preprocessing
from python_sources.dynetkat import DyNetKAT



direct = os.path.dirname(os.path.realpath(__file__))
output_folder = direct + '/output'
maude_preprocess_file = direct + '/maude_sources/preprocess.maude'
maude_dnk_file = direct + '/maude_sources/dnk.maude'
maude_path = ''
netkat_path = ''



def is_json(f):
  return len(f) > 5 and f[-5:] == ".json"


def is_exe(fpath):
    return os.path.isfile(fpath) and os.access(fpath, os.X_OK)



if __name__ == "__main__":
    start = time.time()
    parser = optparse.OptionParser()
    parser.add_option("-t", "--threads", type="int", dest="num_threads", 
                      help="number of threads (Default: the number of available cores in the system)")
    parser.add_option("-p", "--preprocessed", dest="preprocessed", default=False, action="store_true", 
                      help="pass this option if the given input file is already preprocessed")
    (options, args) = parser.parse_args()


    if len(args) < 3:
        print("Error: provide the arguments <path_to_maude> <path_to_netkat> <input_file>.")
        sys.exit()

    if not os.path.exists(args[0]) or is_exe(args[0]) == False:
        print("Maude could not be found in the given path!")
        sys.exit()

    if not os.path.exists(args[1]) or is_exe(args[1]) == False:
        print("NetKAT tool could not be found in the given path!")
        sys.exit()

    if not is_json(args[2]) or os.path.isfile(args[2]) == False:
        print("Please provide a .json file!")
        sys.exit()


    maude_path = args[0]
    netkat_path = args[1]

    with open(args[2]) as f:
        data = json.load(f)
    data["file_name"] = data['module_name'] + ".maude"



    #preprocessing step
    preprocess_start = time.time()
    pp = Preprocessing(direct, maude_path, netkat_path, maude_preprocess_file, maude_dnk_file, options.preprocessed, options.num_threads)
    data = pp.preprocess(data)
    if not options.preprocessed:
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        with open(os.path.join(output_folder, data["module_name"] + "_preprocessed.json"), 'w') as f:
            data['comm'] = list(data['comm']) #set is not json serializable
            json.dump(data, f, ensure_ascii=False, indent=4)
    preprocess_time = time.time() - preprocess_start



    #analysis step
    analysis_start = time.time()
    dp = DyNetKAT(direct, maude_path, netkat_path, maude_preprocess_file, maude_dnk_file, options.num_threads)
    result = dp.decide(data)
    analysis_time = time.time() - analysis_start 



    #clean up 
    if os.path.exists(data['file_name']):
        os.remove(data['file_name'])



    #report the results
    for (packet, prop_num), v in result.items():
        prop_type = data['properties'][str(packet)][prop_num][0]
        prop_result = data['properties'][str(packet)][prop_num][2]

        if v == "error":
            print("Packet: #{} - property: #{}: an error occurred while checking this property.".format(packet, prop_num))
        elif prop_type == "r":
            #rechability property
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

    
    total_time = time.time() - start
    if not options.preprocessed:
        print("preprocess time: {} seconds".format(preprocess_time))
    print("analysis time: {} seconds".format(analysis_time))
    print("total time: {} seconds".format(total_time))


