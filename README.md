# netprog_who_is_the_boss
Final project for network programming class @ Uni Bielefeld - Distributed server architecture

# setup

In the test environment the list of ips is set to only contain 'localhost'. For production this could be read from a configuration file.
Start the server by executing main.py. By default, all instances start with a score of 100. This can be overriden by giving an parameter when starting main.py. The score is increased by seconds since the start of the instance.

Master is the Server with the highest score.
