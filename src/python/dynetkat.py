from multiprocessing import Pool
from src.python.maude_parser import MaudeComm
from src.python.netkat_parser import NetKATComm




class DyNetKAT:
    def __init__(self, direct, maude_path, netkat_path, parser_file, dna_file, num_threads=None):
        self.direct = direct
        self.maude_path = maude_path
        self.netkat_path = netkat_path
        self.parser_file = parser_file
        self.dna_file = dna_file
        self.num_threads = num_threads


    def generate_outfile(self, number):
        return self.direct + '/output_{}.txt'.format(number)


    def compute_encapsulation_set(self, comm):
        delta_h = []
        for x in comm:
            channel, flow_table = x.split(',')
            delta_h.append("({} ! ({}))".format(channel, flow_table))
            delta_h.append("({} ? ({}))".format(channel, flow_table))
        return delta_h


    def hbh_reachability_term(self, in_packet, network, out_packet):
        return "(({}) . ({}) . ({}))".format(in_packet, network, out_packet)


    def insert_inside_network(self, term, network):
        if "*" in network:
            return "{} (({}) . {}".format(network[:network.find('(')], term,
                                          network[network.find('(')+1:])
        return network


    def waypointing_term(self, in_packet, network, out_packet, waypoint):
        out_term = self.insert_inside_network("~ ({})".format(out_packet.replace('(', '').replace(')', '')), network)
        in_term = self.insert_inside_network("~ ({})".format(in_packet.replace('(', '').replace(')', '')), network)
        return "({}) . ({}) . ({}) . ({}) . ({})".format(in_packet, out_term, waypoint, in_term, out_packet)


    def process(self, q, counter, prop_type, prop, rr_or_wp, data):
        try:
            maude_parser = MaudeComm(self.direct, self.maude_path, self.generate_outfile("maude_" + str(q) + "_" + str(counter)))
            prop = maude_parser.parse(data['file_name'], data['module_name'], prop)

            netkat_parser = NetKATComm(self.direct, self.netkat_path, self.generate_outfile("netkat_" + str(q) + "_" + str(counter)))
            if prop_type == "r":
                result = netkat_parser.parse(self.hbh_reachability_term(data['in_packets'][q], prop, data['out_packets'][q]), "zero")
            elif prop_type == "w":
                result = netkat_parser.parse(self.hbh_reachability_term(data['in_packets'][q], prop, data['out_packets'][q]) + " + " +
                                             self.waypointing_term(data['in_packets'][q], prop, data['out_packets'][q], rr_or_wp),
                                             self.waypointing_term(data['in_packets'][q], prop, data['out_packets'][q], rr_or_wp))
        except Exception as err:
            print("packet: {}, property: {}, error: {}\n\n".format(q, counter, err))
            return "error"

        return result


    def decide(self, data):
        delta_h = self.compute_encapsulation_set(data["comm"])

        if self.num_threads is None:
            pool = Pool()
        else:
            pool = Pool(processes=self.num_threads)
        results = {}
        for q in data['in_packets']:
            if q in data['properties']:
                for counter, (prop_type, prop, rr_or_wp, pi_unfolding) in enumerate(data['properties'][q]):
                    program = 'delta{' + ', '.join(delta_h) + '}(pi{' + str(pi_unfolding) + '}(' + data['program'] + '))'
                    prop = prop.replace("{", "").replace("}", ", RSet:TermSet").replace("@Program", program)
                    results[(q, counter)] = pool.apply_async(self.process, args=(q, counter, prop_type, prop, rr_or_wp, data))

        pool.close()
        pool.join()

        return_dict = {}
        for k, v in results.items():
            return_dict[k] = v.get()
    
        return return_dict

