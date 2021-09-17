#install all the dependencies
sudo apt-get update
sudo apt install libncurses5 opam git python3-pip --assume-yes
pip3 install numpy networkx

#install NetKAT tool
git clone https://github.com/netkat-lang/netkat/
cd netkat
opam init -y
eval $(opam env)
opam install mparser=1.2.3 -y
opam install . --deps-only -y
eval $(opam env)
make
cd ..

#download Maude
wget maude.cs.illinois.edu/w/images/3/38/Maude-3.1-linux.zip
unzip Maude-3.1-linux.zip
rm Maude-3.1-linux.zip
cd maude-3.1
chmod +x maude.linux64
