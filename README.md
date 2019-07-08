# netprog_who_is_the_boss
Final project for network programming class @ Uni Bielefeld - Distributed server architecture

# setup

*NEEDS ROOT PRIV*

starting an instance is as simple as:

`python3 main.py [score = 100] [[ip1] [ip2] ... = ['localhost'] ]`

Start the server by executing main.py. By default, all instances start with a score of 100 and look for other server on this machine ('localhost'). This can be overriden by giving the parameters as stated above. The score is increased by seconds since the start of the instance.

Master is the server with the highest score (eg. the longest runtime).

A proper shutdown is performed when pressing *strg + c*