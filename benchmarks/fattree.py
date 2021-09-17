"""
Parts of this file contain modified codes originally taken from
https://github.com/rabeckett/Temporal-NetKAT/blob/master/scripts/pldi-experiments.py and
https://github.com/frenetic-lang/ocaml-topology/blob/master/scripts/fattree.py
"""

import itertools as it
import json
import networkx as nx
from collections import OrderedDict
from util import calculate_recursive_variables



def generate_fattree_topology(pods):
    num_hosts = (pods ** 3)//4
    num_agg_switches = pods * pods
    num_core_switches = (pods * pods)//4

    print("num_hosts: {}".format(num_hosts))
    print("num_agg_switches: {}".format(num_agg_switches))
    print("num_core_switches: {}".format(num_core_switches))
    print("total_num_switches: {}\n".format(num_hosts+num_agg_switches+num_core_switches))

    hosts = ['h' + str(i) for i in range(1, num_hosts + 1)]
    core_switches = ['s' + str(i) for i in range(1, num_core_switches + 1)]
    agg_switches = ['a' + str(i) for i in range(num_core_switches + 1, num_core_switches + num_agg_switches+ 1)]

    g = nx.DiGraph()
    g.add_nodes_from(hosts)
    g.add_nodes_from(core_switches)
    g.add_nodes_from(agg_switches)

    host_offset = 0
    for pod in range(pods):
        core_offset = 0
        for sw in range(pods//2):
            switch = agg_switches[(pod*pods) + sw]
            # Connect to core switches
            for port in range(pods//2):
                core_switch = core_switches[core_offset]
                g.add_edge(switch, core_switch)
                g.add_edge(core_switch, switch)
                core_offset += 1

            # Connect to aggregate switches in same pod
            for port in range(pods//2, pods):
                lower_switch = agg_switches[(pod*pods) + port]
                g.add_edge(switch, lower_switch)
                g.add_edge(lower_switch, switch)

        for sw in range(pods//2, pods):
            switch = agg_switches[(pod*pods) + sw]
            # Connect to hosts
            for port in range(pods//2, pods): # First k/2 pods connect to upper layer
                host = hosts[host_offset]
                g.add_edge(switch, host)
                g.add_edge(host, switch)
                host_offset += 1
    return g


def generate_policy(nodes, g, dst_map, port_map, shortest_paths):
    per_sw = {}
    host_nodes = [x for x in nodes if "h" in x]

    for nsrc in host_nodes:
        for ntgt in host_nodes:
            if not nsrc == ntgt:
                if not (nsrc, ntgt) in shortest_paths:
                    path = nx.shortest_path(g, nsrc, ntgt)
                    for i, src in enumerate(path):
                        if not (src, ntgt) in shortest_paths:
                            shortest_paths[(src, ntgt)] = path[i:]

    for nsrc in nodes:
        same_destinations = {}
        for ntgt in nodes:
            if nsrc == ntgt:
                tmp = "(dst = " + str(dst_map[ntgt]) + ") . pt <- 0 + " # special port for end host
                if nsrc in per_sw.keys():
                    per_sw[nsrc] = per_sw[nsrc] + tmp
                else:
                    per_sw[nsrc] = tmp
            elif ntgt in host_nodes:
                dst = dst_map[ntgt]
                try:
                    spath = None
                    if (nsrc, ntgt) in shortest_paths:
                        spath = shortest_paths[(nsrc, ntgt)]

                        nhop = spath[1]

                        if port_map[(nsrc, nhop)] in same_destinations:
                            same_destinations[port_map[(nsrc, nhop)]].append(dst)
                        else:
                            same_destinations[port_map[(nsrc, nhop)]] = [dst]

                except nx.NetworkXNoPath:
                    pass

        host_node_nums = [dst_map[x] for x in host_nodes]
        for p, v in same_destinations.items():
            if len(v) > len(host_nodes) / 2:
                non_occ = [i for i in host_node_nums if i not in v]
                v = ["dst = " + str(x) for x in non_occ]
                tmp = "~ (" + " + ".join(v) + ") . pt <- " + str(p) + " + "
            else:
                v = ["(dst = " + str(x) + ")" for x in v]
                tmp = "(" + " + ".join(v) + ") . pt <- " + str(p) + " + "

            if nsrc in per_sw.keys():
                per_sw[nsrc] = per_sw[nsrc] + tmp
            else:
                per_sw[nsrc] = tmp

    policy_term = {}
    for i, (sw, pol) in enumerate(per_sw.items()):
        policy_term[sw] = '((sw = {}) . ({}))'.format(dst_map[sw], pol.rstrip()[:-1].rstrip())

    return policy_term


def construct_fattree(pods):
    if pods >= 2 and pods % 2 == 0:
        g = generate_fattree_topology(pods)

        nodes = g.nodes()
        edges = g.edges()

        # assign address block per node
        dst_map = {}
        for i, n in enumerate(nodes):
            dst_map[n] = i

        # assign ports
        port_map = {}
        port_counter = {x: 0 for x in nodes}

        for x, y in edges:
            port_map[(x, y)] = port_counter[x]
            port_map[(y, x)] = port_counter[y]

            port_counter[x] = port_counter[x] + 1
            port_counter[y] = port_counter[y] + 1

        max_port = 0
        for _, v in port_map.items():
            if v > max_port:
                max_port = v

        # build policy based on destination-based shortest path routing
        prop_src = "h1"
        prop_dst = "h" + str((pods ** 3)//4)
        prop_path = nx.shortest_path(g, prop_src, prop_dst)
        shortest_paths = {}

        for i, nsrc in enumerate(prop_path):
            shortest_paths[(nsrc, prop_dst)] = prop_path[i:]

        policy_term = generate_policy(nodes, g, dst_map, port_map, shortest_paths)

        # build topology term
        per_sw = {}
        topology_term = '('

        for x, y in edges:
            tmp = "(pt = " + str(port_map[(x, y)]) + ") . sw <- " + str(dst_map[y]) + " . pt <- " + str(port_map[(y, x)]) + " + "
            if x in per_sw.keys():
                per_sw[x] = per_sw[x] + tmp
            else:
                per_sw[x] = tmp

        for sw, pol in per_sw.items():
            topology_term += "sw = " + str(dst_map[sw]) + " . ("
            topology_term += pol.rstrip()[:-1].rstrip()
            topology_term += ") + "
        topology_term = topology_term.rstrip()[:-1].rstrip() + ')'

        data = OrderedDict()
        data['policy'] = policy_term
        data['topology'] = topology_term

        return data, g, dst_map, port_map, prop_src, prop_dst, prop_path, nodes
    raise ValueError("n must be a even number greater than 2!")


def merge_two_dicts(x, y):
    z = x.copy()
    z.update(y)
    return z


def generate_tail_sequence(updates):
    out = ""
    for i, (channel, flow_table) in enumerate(updates):
        if i == 0:
            out = 'tail(@Program, {{rcfg({}, "{}")}})'.format(channel, flow_table)
        else:
            out = 'tail({}, {{rcfg({}, "{}")}})'.format(out, channel, flow_table)
    return out


def generate_fat_tree(pods):
    data, g, node_dict, port_map, src, dst, path, nodes = construct_fattree(pods)

    core_node = None
    firewall_node = None
    for x in path:
        if "s" in x:
            core_node = x
        if core_node == None and "a" in x:
            firewall_node = x

    prop_path = None
    new_core_node = None
    agg_node = None
    agg_node_2 = None
    new_firewall_node = None
    all_paths = nx.all_shortest_paths(g, src, dst)
    for p in all_paths:
        if not core_node in p and not firewall_node in p:
            prop_path = p
            for x in p:
                if "s" in x:
                    new_core_node = x
                if agg_node == None and "a" in x:
                    agg_node = x
                if new_core_node != None and agg_node_2 == None and "a" in x:
                    agg_node_2 = x
                if new_core_node == None and "a" in x:
                    new_firewall_node = x
            break

    src_port = port_map[(src, path[1])]
    dst_port = port_map[(dst, path[-2])]

    shortest_paths = {}
    for i, nsrc in enumerate(prop_path):
        shortest_paths[(nsrc, dst)] = prop_path[i:]

    policy_term = generate_policy(nodes, g, node_dict, port_map, shortest_paths)

    # insert the firewall policy
    data['policy'][firewall_node] = '{}'.format(policy_term[firewall_node].replace("(sw = {})".format(node_dict[firewall_node]), "(sw = {}) . (~ (src = {}) + (src = {}) . (dst = {}) . (typ = 0))".format(node_dict[firewall_node], node_dict[src], node_dict[src], node_dict[dst])))

    # define flow tables that may be communicated
    flow_tables = {k: [] for k in node_dict.keys()}
    flow_tables[new_core_node] = [policy_term[new_core_node]]
    flow_tables[agg_node] = [policy_term[agg_node]]
    flow_tables[agg_node_2] = [policy_term[agg_node_2]]
    flow_tables[new_firewall_node] = ['{}'.format(policy_term[new_firewall_node].replace("(sw = {})".format(node_dict[new_firewall_node]), "(sw = {}) . (~ (src = {}) + (src = {}) . (dst = {}) . (typ = 0))".format(node_dict[new_firewall_node], node_dict[src], node_dict[src], node_dict[dst])))]

    channels = ["up" + new_firewall_node, "up" + new_core_node, "up" + agg_node_2, "up" + agg_node]

    # define the property
    in_packets = {"0": "((sw = {}) . (pt = {}) . (src = {}) . (dst = {}) . (typ = 0))".format(node_dict[src], src_port, node_dict[src], node_dict[dst]),
                  "1": "((sw = {}) . (pt = {}) . (src = {}) . (dst = {}) . (typ = 1))".format(node_dict[src], src_port, node_dict[src], node_dict[dst]),
                  "2": "((sw = {}) . (pt = {}) . (src = {}) . (dst = {}))".format(node_dict[src], src_port, node_dict[src], node_dict[dst])}

    out_packets = {"0": "((pt = {}) . (sw = {}) . (dst = {}))".format(dst_port, node_dict[dst], node_dict[dst]),
                   "1": "((pt = {}) . (sw = {}) . (dst = {}))".format(dst_port, node_dict[dst], node_dict[dst]),
                   "2": "((pt = {}) . (sw = {}) . (dst = {}))".format(dst_port, node_dict[dst], node_dict[dst]),}

    updates = [("up" + new_firewall_node, flow_tables[new_firewall_node][0]),
               ("up" + new_core_node, flow_tables[new_core_node][0]),
               ("up" + agg_node_2, flow_tables[agg_node_2][0]),
               ("up" + agg_node, flow_tables[agg_node][0])]

    properties = {"0": [("r", "(head({}))".format(generate_tail_sequence(updates[:1])), "!0", 2),
                        ("r", "(head({}))".format(generate_tail_sequence(updates[:2])), "!0", 3),
                        ("r", "(head({}))".format(generate_tail_sequence(updates[:3])), "!0", 4),
                        ("r", "(head({}))".format(generate_tail_sequence(updates[:4])), "!0", 5)],
                  "1": [("r", "(head({}))".format(generate_tail_sequence(updates[:1])), "=0", 2),
                        ("r", "(head({}))".format(generate_tail_sequence(updates[:2])), "=0", 3),
                        ("r", "(head({}))".format(generate_tail_sequence(updates[:3])), "=0", 4),
                        ("r", "(head({}))".format(generate_tail_sequence(updates[:4])), "=0", 5)],
                  "2": [("w", "(head({}))".format(generate_tail_sequence(updates)), 
                         "(sw = {})".format(node_dict[new_firewall_node]), 5)]}

    switch_rec_vars = calculate_recursive_variables(data['policy'], data['topology'], flow_tables)
    controller = {"Controller": '((up{} ! "{}") ; ((up{} ! "{}") ; ((up{} ! "{}") ; ((up{} ! "{}") ; bot))))'.format(new_firewall_node,
                                                                                                                     flow_tables[new_firewall_node][0],
                                                                                                                     new_core_node,
                                                                                                                     flow_tables[new_core_node][0],
                                                                                                                     agg_node_2,
                                                                                                                     flow_tables[agg_node_2][0],
                                                                                                                     agg_node,
                                                                                                                     flow_tables[agg_node][0])}
    recursive_variables = merge_two_dicts(controller, switch_rec_vars)

    example_data = {}
    example_data['module_name'] = "FAT-TREE"
    example_data['recursive_variables'] = recursive_variables
    example_data['program'] = "SDN-1 || Controller"
    example_data['channels'] = channels
    example_data['in_packets'] = in_packets
    example_data['out_packets'] = out_packets
    example_data['properties'] = properties

    return example_data


if __name__ == "__main__":
    for num_pods in [6, 8, 10, 12, 14, 16]:
        print("number of pods: {}".format(num_pods))
        recursive_variables = generate_fat_tree(num_pods)

        all_properties = recursive_variables['properties'].copy()
        
        recursive_variables['properties'] = {'0': all_properties['0']}
        with open("fattree_{}_pods_reachability_1.json".format(num_pods), 'w') as f:
            json.dump(recursive_variables, f, ensure_ascii=False, indent=4)

        recursive_variables['properties'] = {'1': all_properties['1']}
        with open("fattree_{}_pods_reachability_2.json".format(num_pods), 'w') as f:
            json.dump(recursive_variables, f, ensure_ascii=False, indent=4)

        recursive_variables['properties'] = {'2': all_properties['2']}
        with open("fattree_{}_pods_waypointing.json".format(num_pods), 'w') as f:
            json.dump(recursive_variables, f, ensure_ascii=False, indent=4)

        recursive_variables['properties'] = all_properties
        with open("fattree_{}_pods_all_properties.json".format(num_pods), 'w') as f:
            json.dump(recursive_variables, f, ensure_ascii=False, indent=4)
