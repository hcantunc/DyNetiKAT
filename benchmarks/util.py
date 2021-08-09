import itertools as it



def calculate_recursive_variables(initial_policy, topology, flow_tables):
    rec_var_name = "SDN"
    rec_var_def = '"((@Pol) . ({})) *" ; @IRV o+ @sum'.format(topology)

    merged_dict = {}
    for k, v in flow_tables.items():
        id_list = []
        for i, x in enumerate(v):
            id_list.append(k + "-" + str(i+2))
        id_list.insert(0, k + "-1")
        merged_dict[k] = id_list

    combinations = list(it.product(*(merged_dict[x] for x in merged_dict.keys())))

    id_dict = {}
    comms = {}
    for k, v in merged_dict.items():
        for x in v:
            number = int(x.rsplit("-")[1])
            if number == 1:
                id_dict[x] = initial_policy[k]
            else:
                comms[x] = ("up" + k, flow_tables[k][number-2])
                id_dict[x] = flow_tables[k][number-2]

    output = {}
    counter = 1

    for x in combinations:
        current_var = rec_var_name + "-" + str(counter)
        counter += 1

        args = []
        for i in x:
            args.append(id_dict[i])
        initial_term = ' + '.join(args)

        comm = []
        for i, v in comms.items():
            find_term = []
            for j in x:
                if j.rsplit('-')[0] != i.rsplit('-')[0]:
                    find_term.append(j)
                else:
                    find_term.append(i)
            index = combinations.index(tuple(find_term))
            comm.append("(" + v[0] + ' ? "' + v[1] + '") ; {}-{}'.format(rec_var_name, index + 1))
        output[current_var] = rec_var_def.replace("@Pol", initial_term).replace("@IRV", current_var).replace("@sum", ' o+ '.join(comm))

    return output


def merge_two_dicts(x, y):
    z = x.copy()
    z.update(y)
    return z