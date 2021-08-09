import json
from collections import OrderedDict
from util import calculate_recursive_variables, merge_two_dicts



def generate_distributed_independent_controllers():
    policy = {}
    policy["S1"] = "pt = 2 . pt <- 4"
    policy["S2"] = "pt = 12 . pt <- 14"
    policy["S3"] = "zero"
    policy["S4"] = "zero"
    policy["S5"] = "pt = 6 . pt <- 7"
    policy["S6"] = "pt = 8 . pt <- 10"

    flow_tables = {}
    flow_tables["S1"] = []
    flow_tables["S2"] = []
    flow_tables["S3"] = ["pt = 1 . pt <- 3"]
    flow_tables["S4"] = ["pt = 11 . pt <- 13"]
    flow_tables["S5"] = ["pt = 5 . pt <- 7"]
    flow_tables["S6"] = ["pt = 8 . pt <- 9"]

    topology = "((pt = 3 . pt <- 5) + (pt = 4 . pt <- 6) + (pt = 7 . pt <- 8) + (pt = 9 . pt <- 11) + (pt = 10 . pt <- 12) + (pt = 13 . pt <- 15) + (pt = 14 . pt <- 16))"

    channels = ["upS1", "upS2", "upS3", "upS4", "upS5", "upS6"]

    switch_rec_vars = calculate_recursive_variables(policy, topology, flow_tables)
    
    controllers = {}
    controllers["C1"] = '((upS1 ! "zero") ; bot) || ((upS3 ! "{}") ; bot) || ((upS5 ! "{}") ; bot)'.format(flow_tables["S3"][0], flow_tables["S5"][0])
    controllers["C2"] = '((upS2 ! "zero") ; bot) || ((upS4 ! "{}") ; bot) || ((upS6 ! "{}") ; bot)'.format(flow_tables["S4"][0], flow_tables["S6"][0])

    recursive_variables = merge_two_dicts(controllers, switch_rec_vars)

    in_packets = {"H1_to_H4": "(pt = 2)", "H3_to_H2": "(pt = 1)"}
    out_packets = {"H1_to_H4": "(pt = 15)", "H3_to_H2": "(pt = 16)"}

    all_rcfgs = []
    all_rcfgs.append('rcfg(upS1, "zero")')
    all_rcfgs.append('rcfg(upS2, "zero")')
    all_rcfgs.append('rcfg(upS3, "{}")'.format(flow_tables["S3"][0])) 
    all_rcfgs.append('rcfg(upS4, "{}")'.format(flow_tables["S4"][0]))
    all_rcfgs.append('rcfg(upS5, "{}")'.format(flow_tables["S5"][0]))
    all_rcfgs.append('rcfg(upS6, "{}")'.format(flow_tables["S6"][0]))

    properties = {
                  "H1_to_H4": [
                               ("r", "(head(@Program))", "=0", 2),
                               ("r", '(head(tail(@Program, {{ {} }})))'.format(' , '.join(all_rcfgs)), "=0", 3)
                              ],
                  "H3_to_H2": [
                               ("r", "(head(@Program))", "=0", 2),
                               ("r", '(head(tail(@Program, {{ {} }})))'.format(' , '.join(all_rcfgs)), "=0", 3)
                              ]
                 }

    data = OrderedDict()
    data['module_name'] = "DISTRIBUTED-INDEPENDENT-CONTROLLERS"
    data['recursive_variables'] = recursive_variables
    data['program'] = "SDN-1 || C1 || C2"
    data['channels'] = channels
    data['in_packets'] = in_packets
    data['out_packets'] = out_packets
    data['properties'] = properties

    return data


def generate_distributed_synchronized_controllers():
    policy = {}
    policy["S1"] = "pt = 2 . pt <- 4"
    policy["S2"] = "pt = 12 . pt <- 14"
    policy["S3"] = "zero"
    policy["S4"] = "zero"
    policy["S5"] = "pt = 6 . pt <- 7"
    policy["S6"] = "pt = 8 . pt <- 10"

    flow_tables = {}
    flow_tables["S1"] = []
    flow_tables["S2"] = []
    flow_tables["S3"] = ["pt = 1 . pt <- 3"]
    flow_tables["S4"] = ["pt = 11 . pt <- 13"]
    flow_tables["S5"] = ["pt = 5 . pt <- 7"]
    flow_tables["S6"] = ["pt = 8 . pt <- 9"]

    topology = "((pt = 3 . pt <- 5) + (pt = 4 . pt <- 6) + (pt = 7 . pt <- 8) + (pt = 9 . pt <- 11) + (pt = 10 . pt <- 12) + (pt = 13 . pt <- 15) + (pt = 14 . pt <- 16))"

    channels = ["upS1", "upS2", "upS3", "upS4", "upS5", "upS6", "syn"]

    switch_rec_vars = calculate_recursive_variables(policy, topology, flow_tables)
    
    controllers = {}
    controllers["C1"] = '((upS1 ! "zero") ; ((syn ! "one") ; ((upS3 ! "{}") ; ((upS5 ! "{}") ; bot))))'.format(flow_tables["S3"][0], flow_tables["S5"][0])
    controllers["C2"] = '((upS2 ! "zero") ; ((syn ? "one") ; ((upS4 ! "{}") ; ((upS6 ! "{}") ; bot))))'.format(flow_tables["S4"][0], flow_tables["S6"][0])

    recursive_variables = merge_two_dicts(controllers, switch_rec_vars)

    in_packets = {"H1_to_H4": "(pt = 2)", "H3_to_H2": "(pt = 1)"}
    out_packets = {"H1_to_H4": "(pt = 15)", "H3_to_H2": "(pt = 16)"}

    all_rcfgs = []
    all_rcfgs.append('rcfg(upS1, "zero")')
    all_rcfgs.append('rcfg(upS2, "zero")')
    all_rcfgs.append('rcfg(upS3, "{}")'.format(flow_tables["S3"][0])) 
    all_rcfgs.append('rcfg(upS4, "{}")'.format(flow_tables["S4"][0]))
    all_rcfgs.append('rcfg(upS5, "{}")'.format(flow_tables["S5"][0]))
    all_rcfgs.append('rcfg(upS6, "{}")'.format(flow_tables["S6"][0]))
    all_rcfgs.append('rcfg(syn, "one")')

    properties = {
                  "H1_to_H4": [
                               ("r", "(head(@Program))", "=0", 2),
                               ("r", '(head(tail(@Program, {{ {} }})))'.format(' , '.join(all_rcfgs)), "=0", 3)
                              ],
                  "H3_to_H2": [
                               ("r", "(head(@Program))", "=0", 2),
                               ("r", '(head(tail(@Program, {{ {} }})))'.format(' , '.join(all_rcfgs)), "=0", 3)
                              ]
                 }

    data = OrderedDict()
    data['module_name'] = "DISTRIBUTED-CONTROLLER-SYNCHRONIZED"
    data['recursive_variables'] = recursive_variables
    data['program'] = "SDN-1 || C1 || C2"
    data['channels'] = channels
    data['in_packets'] = in_packets
    data['out_packets'] = out_packets
    data['properties'] = properties

    return data


if __name__ == "__main__":
    data_independent = generate_distributed_independent_controllers()
    with open("distributed_controller_independent.json", 'w') as f:
        json.dump(data_independent, f, ensure_ascii=False, indent=4)

    data_synchronized = generate_distributed_synchronized_controllers()    
    with open("distributed_controller_synchronized.json", 'w') as f:
        json.dump(data_synchronized, f, ensure_ascii=False, indent=4)
