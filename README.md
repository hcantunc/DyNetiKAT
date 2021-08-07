

## DyNetiKAT

This is a network verification tool based on the [DyNetKAT](https://arxiv.org/abs/2102.10035) language which provides a reasoning method on reachability and waypointing properties for dynamic networks. DyNetiKAT utilizes [Maude](https://www.sciencedirect.com/science/article/pii/S0304397501003590) rewriting system and [NetKAT](https://dl.acm.org/doi/10.1145/2578855.2535862) decision procedure in the background.

  
## Requirements
  
[Python (>= 3.7)](https://www.python.org/downloads/) including the package [NumPy](https://numpy.org/)

[Maude (>= 3.0)](http://maude.cs.illinois.edu/w/index.php/All_Maude_3_versions)

[NetKAT tool](https://github.com/netkat-lang/netkat)

  

## Usage

python dnk.py <path_to_maude_executable>  <path_to_netkat_tool_build_dir/install/default/bin/katbv>  <input_file>

  
## Encoding 

In the following we describe how the operators of NetKAT and DyNetKAT can be represented in in the tool. DyNetKAT operators are encoded as follows:   
 - The dummy policy<img src="https://render.githubusercontent.com/render/math?math=\bot">is encoded as `bot`
 - The sequential composition operator is encoded as `arg1 ; arg2`. Here, `arg1` can either be a NetKAT policy or a communication term and `arg2` is always required to be a DyNetKAT term.
 -  The communication terms sending <img src="https://render.githubusercontent.com/render/math?math=arg1 ! arg2"> and receiving <img src="https://render.githubusercontent.com/render/math?math=arg1 ? arg2"> are encoded as `arg1 ! arg2` and `arg1 ? arg2`. Here, `arg1` is a channel name and `arg2` is a NetKAT policy.
 - The parallel composition of DyNetKAT policies <img src="https://render.githubusercontent.com/render/math?math=arg1 \parallel arg2"> is encoded as `arg1 || arg2`.  
 - Non-deterministic choice of DyNetKAT policies <img src="https://render.githubusercontent.com/render/math?math=arg1 \oplus arg2"> is encoded as `arg1 o+ arg2`
 - The constant <img src="https://render.githubusercontent.com/render/math?math=\mathbf{rcfg}_{arg1, arg2}"> that pinpoints a communication step is encoded as `rcfg(arg1, arg2)`. Here, `arg1` is a channel name and `arg2` is a NetKAT policy.
 - Recursive variables are explicitly defined in the file that is given as input to the tool. 

<br />

The NetKAT operators are encoded as follows:  
 - The predicate <img src="https://render.githubusercontent.com/render/math?math=0"> for dropping a packet is encoded as `zero`
 - The predicate <img src="https://render.githubusercontent.com/render/math?math=1"> which passes on a packet without any modification is encoded as `one` 
 - The predicate <img src="https://render.githubusercontent.com/render/math?math=f=n"> which checks if the field `arg1` of a packet has value `arg2` is is encoded as `arg1 = arg2`
 - The negation operator<img src="https://render.githubusercontent.com/render/math?math=\neg arg1"> is encoded as `~ arg1`
 - The modification operator <img src="https://render.githubusercontent.com/render/math?math=arg1 \leftarrow arg2"> which assigns the value `arg2` into the field `arg1` in the current packet is encoded as `arg1 <- arg2`
- The union (and disjunction) operator <img src="https://render.githubusercontent.com/render/math?math=arg1"> + <img src="https://render.githubusercontent.com/render/math?math=arg2"> is encoded as `arg1 + arg2`
- The sequential composition (and conjunction) operator <img src="https://render.githubusercontent.com/render/math?math=arg1 \cdot arg2"> is encoded as `arg1 . arg2`
-  The iteration operator <img src="https://render.githubusercontent.com/render/math?math=arg1^*"> is encoded as `arg1 *` 

## Properties

Two types of properties can be checked with DyNetiKAT: reachability and waypointing. Our procedure for checking such properties builds upon the methods introduced in NetKAT for checking reachability and waypointing properties. In NetKAT, these properties are defined with respect to an ingress point <img src="https://render.githubusercontent.com/render/math?math=in">,  an egress point  <img src="https://render.githubusercontent.com/render/math?math=out">,  a  switch  policy  <img src="https://render.githubusercontent.com/render/math?math=p"> , a topology  <img src="https://render.githubusercontent.com/render/math?math=t"> and, a waypoint <img src="https://render.githubusercontent.com/render/math?math=w"> for waypointing properties.  The following NetKAT  equivalences characterize reachability and waypointing properties:  

 1. <img src="https://render.githubusercontent.com/render/math?math=in \cdot (p \cdot t)^* \cdot out \nequiv 0"> 
 2. <img src="https://render.githubusercontent.com/render/math?math=in \cdot (p \cdot t)^* \cdot out \equiv 0"> 
 3. <img src="https://render.githubusercontent.com/render/math?math=in \cdot (p \cdot t)^* \cdot out"> + <img src="https://render.githubusercontent.com/render/math?math=in \cdot (\neg out \cdot p \cdot t)^* \cdot w \cdot (\neg in \cdot p \cdot t)^* \cdot out \notag \equiv in \cdot (\neg out \cdot p \cdot t)^* \cdot w \cdot (\neg in \cdot p \cdot t)^* \cdot out"> 

If the equivalence in (1) holds then this implies that the egress point is reachable from the ingress point. Analogously, if the equivalence in (2) holds then this implies that the egress point is not reachable from the ingress point.  If the equivalence in (3) holds then this implies that all the packets from the ingress point to the egress point travel through the waypoint. DyNetKAT provides a mechanism that enables checking such properties in a dynamic setting. This entails utilizing the operators `head(D)` and `tail(D, R)` where `D` is a DyNetKAT term and `R` is a set of terms of shape `rcfg(X, N).` Intuitively, the operator  `head(D)` returns a NetKAT policy which represents the current configuration in the input `D`.  The operator `tail(D, R)` returns  a  DyNetKAT  policy  which is the sum of DyNetKAT policies inside `D` that appear after the synchronization events in  `R`.  Please see [here](https://arxiv.org/abs/2102.10035) for more details on the `head` and `tail` operators. 

For a given DyNetKAT term `D` we first apply our equational reasoning framework to unfold the expression and rewrite it into the normal form. This is achieved by utilizing the projection operator <img src="https://render.githubusercontent.com/render/math?math=\pi_n(-)">. Note that the number of unfoldings (i.e. the value `n` inside the projection operator) is a fixed value specified by the user. We then apply the restriction operator <img src="https://render.githubusercontent.com/render/math?math=\delta_H(-)"> to . The term that we compute in is as follows: <img src="https://render.githubusercontent.com/render/math?math=\delta_H(\pi_n(D))"> where H is the set of all terms of shape `X!Z` and `X?Z` that appear in `D`. Then, we extract the desired configurations by using the head and tail operators. After this step, the resulting expression is a purely NetKAT term  and  we  utilize  the  NetKAT  decision  procedure  for  checking  the  desired properties.

In our tool a property is defined as 4-tuple containing the following elements:

 1. The first element describes the type of property and can be either `r` or `w` where `r` denotes a reachability property and `w` denotes a waypointing property.
 2. The second element is the property itself. The constructs that can be used to define a property are as follows: `head(@Program)`, `tail(@Program, R)`. Here, `@Program` is referring to DyNetKAT program that is given as input, and `R` is a set containing elements of shape `rcfg(X,N)`. 
 3.  For reachability properties, the third element can be either `!0` or `=0` where `!0` denotes that the associated egress point should be reachable from the associated ingress point, whereas `=0` denotes that the associated egress should be unreachable from the associated ingress point. For waypointing properties, the third element is a predicate which denotes the waypoint.
 4. The fourth element denotes the maximum number of unfoldings to perform in the projection operator.
 For an example,  `(r, head(@Program), !0, 100)` encodes a reachability property and `(w, head(@Program), sw = 1, 100)` encodes a waypointing property. Furthermore, every property is associated with an ingress point and an egress point. 


## Input format

The input to DyNetiKAT is a .json file which contains the following data:

* in_packets: A dictionary with predicates describing the ingress points, e.g.:

`{"first_packet": "sw = 1 . pt = 1", "second_packet": "sw = 2 . pt = 2"}`

Note that every element in this dictionary must have a corresponding element in *out_packets* with the same key.

* out_packets: A dictionary with predicates describing the egress points, e.g.:

`{"first_packet": "sw = 2 . pt = 2", "second_packet": "sw = 1 . pt = 1"}`

As aforementioned, every element in this dictionary must have a corresponding element in *in_packets* with the same key.

* recursive_variables: Names and definitions of recursive variables that appear in the program, e.g.:

`{"Switch": "\"(pt = 1 . pt <- 2)\" ; Switch o+ (secConReq ? \"one\") ; SwitchPrime"}`

Note that the NetKAT terms inside the definitions must be enclosed with double quotes.

* channels: A list containing the names of the channels that appear in the program.

* program: The program to execute.

* module_name: The name of the program. The output files will be based on this name.

* properties: A dictionary which contains a list of properties. All the properties are associated with an ingress and egress point from the *in_packets* and *out_packets*. For example, consider the following encoding:
`{ "first_packet": [["r", 
                "head(@Program)", 
                "!0", 
                100], 
            ["w", 
                "head(@Program)", 
                "sw = 1", 
                100]], "second_packet": [[
                "r", 
                "head(@Program)",  
                "!0", 
                100]] 
    }` 
The above encoding defines a reachability property and a waypointing property for the `first_packet` and a reachability property for the`second_packet`.     

An example input file can be found in benchmarks/stateful_firewall.json.


## FatTree Benchmarks

The FatTree topologies and the associated properties that are described [here](https://arxiv.org/abs/2102.10035) can be generated using the script `generate_fattree.py` under the folder `benchmarks`. This script requires Python 2 and the package [NetworkX](https://networkx.org/).
