properties="reachability_1  reachability_2  waypointing  all_properties"

for pods in 6 8 10 12 14 16
do
   for prop in $properties
   do
      echo "Running FatTree experiment with $pods pods - Property: $prop"
      python3 dnk.py ./maude-3.1/maude.linux64 ./netkat/_build/install/default/bin/katbv ./benchmarks/fattree_"$pods"_pods_$prop.json -s
      echo "----\n\n"
   done
done
