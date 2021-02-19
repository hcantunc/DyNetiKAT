This is a network verification tool based on the *DyNetKAT* language. We build upon the reachability checking method in [NetKAT](https://dl.acm.org/doi/10.1145/2578855.2535862) where checking for reachability is reduced to equivalence checking. The inputs to our tool are a *DyNetKAT* program *p*, a list of input predicates *in*, a list of output predicates *out*, and the equivalences that describe the desired properties. Our tool utilizes the Maude Rewriting Logic and the NetKAT tool in the background.


## Requirements

Maude 3.0 or higher, which can be obtained from:
http://maude.cs.illinois.edu/w/index.php/All_Maude_3_versions

NetKAT tool, which can be obtained from:
https://github.com/frenetic-lang/netkat-automata

Python 3.5 or higher


## Usage

python dnk.py <path_to_maude> <path_to_netkat> <input_file>


## Input format

.json file containing the keys:

* fields: A list of strings which describe the fields that appear in the program, e.g. ["pt", "sw", "src", "sw"].
* in_packets: A list of predicates describing the ingress points, e.g. ["sw = 1 . pt = 1"]. Note that every element in this list must have a corresponding element in *out_packets* list with the same index. 
* out_packets: A list of predicates describing the egress points, e.g. ["sw = 2 . pt = 2"]. Note that every element in this list must have a corresponding element in *in_packets* list with the same index. 
* pi_unfolding: The maximum number of unfoldings of the projection operator.
* recursive_variables: Names and definitions of recursive variables that appear in the program.
* channels: Names of the channels that appear in the program.
* program: The program to execute.
* module_name: The name of the module that is going to be included in the Maude programs.
* properties: A dictionary which contains a list of properties for every pair of elements in the lists *in_packets* and *out_packets*. 

An example input file may be found in stateful_firewall.json.


## Note

As already described in the tool's [repository](https://github.com/frenetic-lang/netkat-automata), the NetKAT tool is not being actively developed and users might face certain issues during installation and use. We used the software provided in the *extended_netkat* branch of the repository.
