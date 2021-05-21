This is a network verification tool based on the [DyNetKAT](https://arxiv.org/abs/2102.10035) language. We exploit the sound and ground-complete equational theory of the language to provide an efficient reasoning method about safety properties for dynamic networks. DyNetiKAT utilizes  Maude rewriting system and [NetKAT](https://dl.acm.org/doi/10.1145/2578855.2535862)  decision procedure in the background.


## Requirements

[Maude 3.0](http://maude.cs.illinois.edu/w/index.php/All_Maude_3_versions) or higher

[NetKAT tool](https://github.com/netkat-lang/netkat)

[Python 3.7](https://www.python.org/downloads/) or higher


## Usage

python dnk.py <path_to_maude_executable> <path_to_netkat_tool_build_dir/install/default/bin/katbv> <input_file> 


## Input format

The input to DyNetiKAT is a .json file which contains the following data:

* in_packets: A dictionary with predicates describing the ingress points, e.g.: 
	`{"first_packet": "sw = 1 . pt = 1", "second_packet": "sw = 2 . pt = 2"}` 
Note that every element in this dictionary must have a corresponding element in *out_packets* with the same key. 
* out_packets: A dictionary with predicates describing the egress points, e.g.:
`{"first_packet": "sw = 2 . pt = 2", "second_packet": "sw = 1 . pt = 1"}` 
Note that every element in this dictionary must have a corresponding element in *out_packets* with the same key. 
* recursive_variables: Names and definitions of recursive variables that appear in the program, e.g.:
`{"Switch": "\"(pt = 1 . pt <- 2)\" ; Switch o+ (secConReq ? \"one\") ; SwitchPrime"}`
Note that the NetKAT terms inside the definitions must be enclosed with double quotes.
* channels: A list containing the names of the channels that appear in the program.
* program: The program to execute.
* module_name: The name of the program. The output files will be based on this name.
* properties: A dictionary which contains a list of properties. All the properties are associated with an ingress and egress point from the *in_packets* and *out_packets*. There are two kinds of properties that can be given as input: reachability and waypointing. Every property is a list with 4 elements:
	*  The first element describes the type of property and can be either  **r** or **w** where **r** denotes a reachability property and **w** denotes a waypointing property.
	* The second element is the property itself. The constructs that can be used to define a property are as follows: **head(@Program)**, **tail(@Program, R)**. Here, **@Program** is referring to DyNetKAT program that is given as input, and **R** is a set containing elements of shape **rcfg(X,N)**. Please see the [paper](https://arxiv.org/abs/2102.10035) for more details on **head** and **tail** operators.
	* For reachability properties, the third element can be either **!0** or **=0** where **!0** denotes that the associated egress point should be reachable from the associated ingress point , whereas **=0** denotes that the associated egress should be unreachable from the associated ingress point. For waypointing properties, the third element is a predicate which denotes the waypoint.
	* The fourth element denotes the maximum number of unfoldings to perform in the projection operator while checking for the property. 
 

An example input file can be found in benchmarks/stateful_firewall.json.
