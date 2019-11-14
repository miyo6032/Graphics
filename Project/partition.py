import numpy as np
import networkx as nx
import random as rnd

def tabulate_ek(G,z,c):
    # This function tabulates the e_rs and kappa_r auxiliary data structures for the DC-SBM
    #
    # input  : G is simple graph with n nodes
    #        : z is n x 1 partition of G into c groups
    #        : c is scalar, number of possible groups
    # output : ers, kpr
    
    ers = np.zeros([c,c]) # count of stubs from group r to group s
    kpr = np.zeros(c) # total degree of group r

    ##### do not modify above here #####
    for i, j in G.edges():   
        
        # Assumption here is that there are no self loops because then those would be double counted
        ers[z[i]][z[j]] += 1;
        ers[z[j]][z[i]] += 1;
        
    for node in G.nodes():
        kpr[z[node]] += G.degree(node) # Adds the node's degree to its group
        
    ##### do not modify below here #####

    return ers,kpr

# input  : number of nodes n, and number of groups c
# output : returns a random partition z (n x 1), in which z_i = Uniform(0,c-1)
def random_z(n,c):
    rnd.seed()
    
    z = np.zeros(n, dtype=int)

    for i in range(n):
        z[i] = np.random.choice([i for i in range(c)])
    
    return z

def dcsbm_LogL(ers,kpr):
    # This function calculates the log-likelihood of the degree-corrected stochastic block model (DC-SBM)
    # See Eq. (9) in Lecture 6.
    #
    # input  : ers is a c x c np.array of stub counts
    #        : kpr is a c x 1 np.array of stub counts 
    # output : the dcsbm log-likelihood
    
    c = ers.shape[1]  # number of groups
    
    logL = 0
    for r in range(c):
        for s in range(c):
            if ers[r,s] < 1 or kpr[r] < 1 or kpr[s] < 1:
                temp = 0 # define 0^0 = 1
            else:
                temp = ers[r,s]*np.log( ers[r,s] / (kpr[r]*kpr[s]) )
            logL = logL + temp
    
    return logL

def makeAMove(G,z,c,f):
    # For each non 'frozen' node in the current partition, this function tries all (c-1) possible group moves for it
    # It returns the combination of [node i and new group r] that produces the best log-likelihood over the non-frozen set
    # input  : G a graph
    #        : z a nx1 partition of G's nodes
    #        : c the number of groups
    #        : fr a nx1 binary vector of frozen nodes
    # output : bestL, the best log-likelihood found
    #        : bestMove, [i,r] the node i and new group r to achieve bestL
    
    bestL    = -np.inf         # the best log-likelihood over all considered moves
    bestMove = [-1, -1]         # [node i, group r] assignment for bestL
    for i in G.nodes():
        #print(z)
        if f[i] == 0:          # if i is not a 'frozen' node
            s = int(z[i])      #  the current label of i
            for r in range(c): #  try all the groups
                            
                if r != s: # We don't want to consider not making a move at all (aka setting i from group s -> group s)
                    z[i] = r
                    likelihood = dcsbm_LogL(*tabulate_ek(G,z,c))
                    if likelihood > bestL:
                        bestL = likelihood
                        bestMove = [i, r]

            z[i] = s # We don't want to actually change the groups in this function
                ##### do not modify below here #####    
                
    return bestL,bestMove

def get_partition(G, c = 3):
    n  = G.order()                      # n, number of nodes
    T  = 30                             # maximum number of phases
    LL = []                             # log-likelihoods over the entire algorithm (.appended)
    flag_converged = 0                  # early-convergence flag
    z       = random_z(n,c)       # z0, initial partition
    ers,kpr = tabulate_ek(G,z,c)  # ers, kpr, initial DC-SBM parameters
    pc = 0  # counter for number of phases completed
    l_max = dcsbm_LogL(ers,kpr) # Basically replaces the purpose of Lt and simplifies keeping track of the max found
    z_max = z

    while not flag_converged:

        f     = np.zeros([n,1],dtype=int)  # no nodes frozen
        l_max_phase = l_max # Tracks the max liklihood of this phase
        z_max_phase = z # Tracks the best partition of this phase
        LL.append(l_max_phase)

        # This loop represents one phase
        for j in range(n):

            choiceL, choiceMove = makeAMove(G,z,c,f)
            f[choiceMove[0]] = 1
            z[choiceMove[0]] = choiceMove[1]
            LL.append(choiceL)

            if choiceL > l_max_phase: # Finds the max liklihood of this phase
                z_max_phase = list(z)
                l_max_phase = choiceL

        # This if statement decides if the algorithm should do another phase
        # If this phase hasn't improved anything since our last phase, then we have converged
        if l_max_phase <= l_max or pc > T:
            # If the max in this phase is no better than that of the previous phase
            flag_converged = True
        else:
            l_max = l_max_phase # Set the max of this phase for the next phase
            z = z_max_phase # Sets the starting partition of the next phase to the best partition found in this phase
            z_max = z_max_phase
            pc+=1
            
    return l_max, z, LL, pc

def get_partition_n(G, c = 2, trials = 1):
    # Keep track of the data we need to return when we find the best partition found among the different times we run the algorithm
    # Formatted as (likelihood, partition, recorded likelihoods, pc)
    data_max = (-np.inf, [], [], 0)
    
    for i in range(trials):
        data = get_partition(G, c = c)
        if data[0] > data_max[0]:
            data_max = data
            
    return data_max[1]