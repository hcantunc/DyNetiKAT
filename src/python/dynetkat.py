from multiprocessing import Pool
from src.python.maude_parser import MaudeComm
from src.python.netkat_parser import NetKATComm
from src.python.util import generate_error_message, generate_outfile


class DyNetKAT:
    def __init__(self, direct, maude_path, netkat_path, netkat_version, parser_file, dna_file, num_threads=None):
        self.direct = direct
        self.maude_path = maude_path
        self.netkat_path = netkat_path
        self.netkat_version = netkat_version
        self.parser_file = parser_file
        self.dna_file = dna_file
        self.num_threads = num_threads


    def compute_encapsulation_set(self, comm):
        '''Computes the set of all terms of shape x!z and x!?.'''
        delta_h = []
        for x in comm:
            channel, flow_table = x.split(',')
            delta_h.append("({} ! ({}))".format(channel, flow_table))
            delta_h.append("({} ? ({}))".format(channel, flow_table))
        return delta_h


    def hbh_reachability_term(self, in_packet, network, out_packet):
        '''Returns the hop-by-hop reachability term from in_packet to out_packet.'''
        return "(({}) . ({}) . ({}))".format(in_packet, network, out_packet)


    def insert_inside_network(self, predicate, network):
        '''Takes a predicate term and a network term (which is of shape (p . t)*), returns (predicate . p . t)*'''
        if "*" in network:
            return "{} (({}) . {}".format(network[:network.find('(')], 
                                          predicate,
                                          network[network.find('(')+1:])
        return "({}) . ({})".format(predicate, network)


    def waypointing_term(self, in_packet, network, out_packet, waypoint):
        '''
        Computes the right-hand side of the term for checking if a node is a waypoint between in_packet and out_packet.
        That is, the term in_packet . (~out_packet . network)* . waypoint . (~in_packet . network)* . out_packet.
        '''
        out_term = self.insert_inside_network("~ ({})".format(out_packet.replace('(', '').replace(')', '')), network)
        in_term = self.insert_inside_network("~ ({})".format(in_packet.replace('(', '').replace(')', '')), network)
        return "({}) . ({}) . ({}) . ({}) . ({})".format(in_packet, out_term, waypoint, in_term, out_packet)


    def process(self, q, counter, prop_type, prop_maude, rr_or_wp, data):
        '''
        This method calls Maude and NetKAT decision procedure and checks if a property is 
        satisfied. Returns true or false if the calls to Maude and NetKAT tool returns 
        successfully and returns None if an error occurred during execution. 
        '''
        error_occurred = False

        maude_parser = MaudeComm(self.direct, self.maude_path, 
                                 generate_outfile(self.direct, "maude_" + str(q) + "_" + str(counter)))
        prop, error = maude_parser.execute(data['file_name'], data['module_name'], prop_maude)

        if prop is None:
            generate_error_message("Maude", "packet: {}, property: {}".format(q, counter), prop_maude, error, False)
            error_occurred = True
        else:
            netkat_parser = NetKATComm(self.direct, self.netkat_path, self.netkat_version,
                                       generate_outfile(self.direct, "netkat_" + str(q) + "_" + str(counter)))
            if prop_type == "r":
                term1 = self.hbh_reachability_term(data['in_packets'][q], prop, data['out_packets'][q])
                result, error = netkat_parser.execute(term1, "zero")
            elif prop_type == "w":
                term1 = self.hbh_reachability_term(data['in_packets'][q], prop, data['out_packets'][q]) + " + " +\
                        self.waypointing_term(data['in_packets'][q], prop, data['out_packets'][q], rr_or_wp)
                term2 = self.waypointing_term(data['in_packets'][q], prop, data['out_packets'][q], rr_or_wp)
                result, error = netkat_parser.execute(term1, term2)

            if result is None:
                generate_error_message("NetKAT tool", "packet: {}, property: {}".format(q, counter), term1, error, False)
                error_occurred = True

        if error_occurred:
            return None

        return result


    def report_results(self, result, data):
        '''
        Takes the result of the property checking step and information about the properties 
        and returns a dictionary where properties are classified as 'satisfied', 
        'violated' or 'error'. 
        '''
        report = {}
        for (packet, prop_num), v in result.items():
            prop_type = data['properties'][str(packet)][prop_num][0]
            prop_result = data['properties'][str(packet)][prop_num][2]

            if v is None:
                report[(packet, prop_num)] = "error"
            elif prop_type == "r":
                #reachability property
                if (v == "false" and prop_result == "!0") or (v == "true" and prop_result == "=0"):
                    report[(packet, prop_num)] = "satisfied"
                else:
                    report[(packet, prop_num)] = "violated"
            elif prop_type == "w":
                #waypointing property
                if v == "true":
                    report[(packet, prop_num)] = "satisfied"
                else:
                    report[(packet, prop_num)] = "violated"
        return report


    def decide(self, data):
        '''
        Takes a dictionary containing all the information about the network and the properties
        that are being considered for this network and checks whether the given properties are 
        satisfied in the network. 

        For a given property the returned result can be one of the following: 'satisfied', 'violated' 
        or 'error'. 
        '''
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

        return self.report_results(return_dict, data)
