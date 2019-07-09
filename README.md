# netprog_who_is_the_boss
Final project for network programming class @ Uni Bielefeld - Distributed server architecture

# setup

*NEEDS ROOT PRIV*

starting an instance is as simple as:

`python3 main.py [score = 100] [[ip1] [ip2] ... = ['localhost'] ]`

Start the server by executing main.py. By default, all instances start with a score of 100 and look for other server on this machine ('localhost'). This can be overriden by giving the parameters as stated above. The score is increased by seconds since the start of the instance.

Master is the server with the highest score (eg. the longest runtime). If the score is equal, the server with that score but the lowest port is taken.

A proper shutdown is performed when pressing *strg + c*

# issues
- there is a race condition for when the info-message from the master needs quite long and both servers have a similiar score. the score for the current slave is then updated when the message from the master is received but then the slaves score might be higher. Both would tell they are master.
- don't know what would happen if one instance is connected via ip and the same instance again by something like the computer name. instances might need ids