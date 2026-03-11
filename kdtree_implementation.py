#implementation made by me, based on the original 1975 paper.
import time
import random

class node:
    def __init__(self, key):
        self.key = key                  #an array with the value of this node at EACH dimension
        self.loson = None               #left child. disc must be lower than self on selfs k.
        self.hison = None               #right child. disc must higher then self on selfs k
        self.disc = 0                   #the dimension that this node is in. should always be between 0 and k-1
        
    
class KDtree:
    def __init__(self, k):
        self.root = None                #the root node of the kd tree
        self.k = k                      #the amount of dimensions in the kd tree
            
    def insert(self, node, Q = None):   #function to add a new node to the tree
        if Q == None:                   #the only time Q would be None would be on an empty tree
            Q = self.root
            
        if self.root == None:           #if tree is empty, set node as root.
            self.root = node 
            node.disc = 0
            return
            
        else:                            #if there is a root, recursively go down tree until node finds a spot
            result = self.successor(node, Q)
            if result == "HIGHER":
                node.disc = (Q.disc + 1) % self.k
                if Q.hison == None:
                    Q.hison = node
                    return
                else:
                    self.insert(node, Q.hison)
            elif result == "LOWER":
                node.disc = (Q.disc + 1) % self.k
                if Q.loson == None:
                    Q.loson = node
                    return
                else:
                    self.insert(node, Q.loson)
        return
            
        
        
    def successor(self, node, Q):   #function to handle the measuring the input against the current node(Q) on its disc and returning a result.
        for i in range(0, self.k):  #starting with current disc, cycle through every disc in order until a non equal value is found, and judge it on that.
            sdisc = (Q.disc + i) % self.k
            
            if node.key[sdisc] < Q.key[sdisc]:
                return "LOWER"
            elif node.key[sdisc] > Q.key[sdisc]:
                return "HIGHER"
            
        return "EQUAL"  
            
            
    
    def exactSearch(self, target, Q = None):    #search for a node matching the target node exactly.
        if Q == None:                           #like in insert(), in exactSearch, Node is only none on the first input. it sets it to the root.
            Q = self.root                       
            if Q == None:                       
                return "Tree is empty"
        result = self.successor(target, Q)
        if result == "EQUAL":
            return Q
        elif result == "HIGHER":
            if Q.hison:
                return self.exactSearch(target, Q.hison)
        else:
            if Q.loson:
                return self.exactSearch(target, Q.loson)
        return None
        
    
    def partialSearch(self, constraints, Q = None, result = None):      #constraints should be a dictionary like {dimension: target-at-dimension, dimension2: target-at-dimension2, ...}
        if result is None:
            result = []
        
        if Q == None:                                                   #again, would only happen on the first use.                       
            Q = self.root                       
            if Q == None:                       
                return "Tree is empty"
            
        match = True                                                    #check if the current Q fits the constraints searched for
        for dim, value in constraints.items():
            if Q.key[dim] != value:
                match = False
                break
            
        if match:                                                       #if it does, added it to the result  
            result.append(Q)
            
        if Q.disc in constraints:                                       #if the current Qs disc is a constraint, only search down the side that the cosntaint fits.
            if Q.key[Q.disc] < constraints[Q.disc] and Q.hison != None:
                result = self.partialSearch(constraints, Q.hison, result)
                
            elif Q.key[Q.disc] > constraints[Q.disc] and Q.loson != None:
                result = self.partialSearch(constraints, Q.loson, result)
            
            else:                                                       #if the constraint is equal, go both sides.
                if Q.hison != None:    
                    result = self.partialSearch(constraints, Q.hison, result)
                if Q.loson != None:
                    result = self.partialSearch(constraints, Q.loson, result)
        else:                                                           #if its not, search down both sides
            if Q.hison != None:    
                result = self.partialSearch(constraints, Q.hison, result)
            if Q.loson != None:
                result = self.partialSearch(constraints, Q.loson, result)
            
        return result
    
    
    def regionQuery(self, upper, lower): #upper and lower are the bounds of the queried region
        if self.root == None:
            return []
            
        lowerB = [-float("inf")] * self.k   #lower and upper B are the bounds of the searchable area. these will be filled in with an actual number on each level to filter out more of the tree.
        upperB = [ float("inf")] * self.k                  
        result = []
        
        self.regionSearch(self.root, lower, upper, lowerB, upperB, result)
        
        return result
            
            
    def regionSearch(self, P, lowerR, upperR, lowerB, upperB, result):      #lowerR and upperR represent the bounds of the target region while lowerB and upperB represent the bounds of the current subtree. P is the current node. the root on the first call.
        if P == None:
            return
        
        if self.inRegion(P, lowerR, upperR):
            result.append(P)
            
        J = P.disc
        
        if P.loson != None:
            left_lower = lowerB.copy()
            left_upper = upperB.copy()
            
            left_upper[J] = P.key[J]
            
            if self.Bounds_interRegion(left_lower, left_upper, lowerR, upperR): #if left_upper does not intersect with the target area, then the entire left subtree can be dismissed. this is checking that. this is the main strength of kd trees in regionQueries.
                self.regionSearch(P.loson, lowerR, upperR, left_lower, left_upper, result)
                
        if P.hison != None:
            right_lower = lowerB.copy()
            right_upper = upperB.copy()

            right_lower[J] = P.key[J]

            if self.Bounds_interRegion(right_lower, right_upper, lowerR, upperR): # the same can be done for right_lower. if right_lower is higher then upperR, then the entire right subtree can be dismissed.
                self.regionSearch(P.hison, lowerR, upperR, right_lower, right_upper, result)

    def inRegion(self, P, lower, upper): #returns true if P is in the target region.
        for i in range(len(P.key)):
            if P.key[i] < lower[i] or P.key[i] > upper[i]:
                return False
        return True
    
    def Bounds_interRegion(self, lowerB, upperB, lowerR, upperR): #checks if the minimum bounds on one of the two regions exceeds the max on the other. and vice versa. if they do, the regions do not intersect.
        for i in range(len(lowerB)):
            if lowerB[i] > upperR[i]:
                return False
            if upperB[i] < lowerR[i]:
                return False            #if none of these intersect, theres no need to go down this subtree as everything in it is outside the target region
        return True
    
    
    def nearestNeighbour1(self, T):  #T for Target. it should be k length array of coordinates. a wrapper node for the actual recursive function in nearest
        #this is a more simple version of nearest neighbour based on split-plane pruning. it was the one Bentley originally used, however a more version was later developed.
        if self.root == None:
            return None
        Bnode = self.root            #Best(closest) node. starts as root.
        Bdist = float("inf")         #current Best(lowest) distance
        
        Bnode, Bdist = self.nearest(self.root, T, Bnode, Bdist)
        
        return Bnode
    
    def nearest(self, P, target, Bnode, Bdist): #recursive. compares P to target, then recurses to P's hison and/or loson.
        if P == None:
            return Bnode, Bdist
        
        d = self.distance(P, target)
        if d < Bdist:
            Bnode = P
            Bdist = d
            
        J = P.disc
        
        if target[J] < P.key[J]:    #if the target is above or below on this axis, then the nearest neighbour is more likely to be down the aligned subtree. so it tries that one first.
            prim = P.loson          
            sec = P.hison
        else:
            prim = P.hison
            sec = P.loson
            
        if prim is not None:
            Bnode, Bdist = self.nearest(prim, target, Bnode, Bdist)
        
        pdist = (target[J] - P.key[J]) ** 2 #this tests the distance on purely the J axis. ignoring all other dimensions
        
        if pdist < Bdist:                   #if the distance on J is less then the best total distance, then its possible there is a node in sec subtree that is closer than Bnode.
            Bnode, Bdist = self.nearest(sec, target, Bnode, Bdist)
    
        return Bnode, Bdist
    
    
    def distance(self, Node, P):    #returns the distance from an inputted node to inputted coordinates in an array, P
        result = 0
        for i in range(self.k):
            result += (Node.key[i] - P[i]) ** 2 #   uses squared distance because its faster to compute.
        return result
    
    '''This version judges whether to explore a secondary subtree by computing the minimum possible distance to its bounding box across all dimensions simultaneously. 
       This gives a tighter lower bound than only measuring the gap to the current split plane on one axis. For example, a secondary subtree might be close on the current split axis, say, d=3, 
       but far away in another dimension d could equal 10, making its true minimum box distance large enough to prune. The previous version only sees the distance-3 axis and recurses in, 
       potentially wasting several levels of traversal before the other dimensions reveal it was never worth searching.
       
       this version has higher overhead but outcompetes the basic version at higher K levels. '''
    def nearestNeighbour2(self, T):
        if self.root == None:
            return None
        
        lowerB = [-float("inf")] * self.k   #initial bounds for the kdTree. at each layer, the node will mark boundaries for the still explorable area
        upperB = [ float("inf")] * self.k
        
        Bnode = self.root            #Best(closest) node. starts as root.
        Bdist = float("inf")         #current Best(lowest) distance
        
        Bnode, Bdist = self.nearest2(self.root, T, Bnode, Bdist, lowerB, upperB)
        
        return Bnode
    

    def nearest2(self, P, target, Bnode, Bdist, lowerB, upperB): #recursive. compares P to target, then recurses to P's hison and/or loson.
        if P is None:
            return Bnode, Bdist
    
        d = self.distance(P, target)
        if d < Bdist:
            Bnode = P
            Bdist = d
        
        J = P.disc
    
        if target[J] < P.key[J]:                           # determine directions before copying, so we only copy what we need
            prim, sec = P.loson, P.hison
            prim_lower, prim_upper = lowerB.copy(), upperB.copy()
            prim_upper[J] = P.key[J]                        # left subtree is bounded above by P on axis J
        else:
            prim, sec = P.hison, P.loson
            prim_lower, prim_upper = lowerB.copy(), upperB.copy()
            prim_lower[J] = P.key[J]                        # right subtree is bounded below by P on axis J

        if prim is not None:                                # guard: no point recursing into an empty subtree
            Bnode, Bdist = self.nearest2(prim, target, Bnode, Bdist, prim_lower, prim_upper)
    
        if sec is not None:
            sec_lower, sec_upper = lowerB.copy(), upperB.copy()
            if target[J] < P.key[J]:                        # clip sec bounds on the opposite side from prim
                sec_lower[J] = P.key[J]
            else:
                sec_upper[J] = P.key[J]
            box_dist = self.distanceToBox(target, sec_lower, sec_upper)

            if box_dist < Bdist:                            # only search if the minimum distance from the box is less than the current best distance
                Bnode, Bdist = self.nearest2(sec, target, Bnode, Bdist, sec_lower, sec_upper)

        return Bnode, Bdist
    
    def distanceToBox(self, T, lowerB, upperB):
        minD = 0    #minimum possible distance to box
        for i in range(len(lowerB)):
            if T[i] < lowerB[i]:
                minD += (T[i] - lowerB[i]) ** 2
            elif T[i] > upperB[i]:
                minD += (T[i] - upperB[i]) ** 2
        return minD
    
    
    def deleteRoot(self):   #bentley included this as a special case
        self.deleteNode(self.root)
    
    def deleteNode(self, target, Q=None, parent=None, side=None):   #remove a node from the tree. rewiring the nodes around it.
        if Q is None:
            Q = self.root
            if Q is None:
                return "Tree is empty"

        result = self.successor(target, Q)

        if result == "HIGHER":
            if Q.hison is None:
                return None
            return self.deleteNode(target, Q.hison, Q, "hison")
        elif result == "LOWER":
            if Q.loson is None:
                return None
            return self.deleteNode(target, Q.loson, Q, "loson")
        
        if Q.loson is None and Q.hison is None: #if its a leaf, just remove it without fuss
            if parent is None:
                self.root = None
            elif side == "hison":
                parent.hison = None
            else:
                parent.loson = None
            return
        
        if Q.hison is not None:
            replacement = self.findMin(Q.hison, Q.disc)
            Q.key = replacement.key[:]                  # copy replacement's key into Q
            self.deleteNode(replacement, Q.hison, Q, "hison")  # delete the replacement from where it was

        else:
            replacement = self.findMax(Q.loson, Q.disc)
            Q.key = replacement.key[:]
            self.deleteNode(replacement, Q.loson, Q, "loson")

            Q.hison = Q.loson                           # migrate left subtree to right, as explained above
            Q.loson = None
    
    
    def findMin(self, Q, disc): #find the minimum value for the given disc in that subtree
        if Q is None:
            return None

        if Q.disc == disc:
            if Q.loson is None:
                return Q                                # nothing smaller to the left, Q is the min
            return self.findMin(Q.loson, disc)

        candidates = [Q]
        left  = self.findMin(Q.loson, disc)
        right = self.findMin(Q.hison, disc)

        if left:  candidates.append(left)
        if right: candidates.append(right)

        return min(candidates, key=lambda n: n.key[disc])


    def findMax(self, Q, disc):             #findmin but inverted for max
        if Q is None:
            return None

        if Q.disc == disc:
            if Q.hison is None:
                return Q
            return self.findMax(Q.hison, disc)

        candidates = [Q]
        left  = self.findMax(Q.loson, disc)
        right = self.findMax(Q.hison, disc)

        if left:  candidates.append(left)
        if right: candidates.append(right)

        return max(candidates, key=lambda n: n.key[disc])
    
    def optimise(self): #gather all the nodes as a flat list, then recreate the tree so that it is balanced. wrapper for buildBalanced
        if self.root is None:
            return
    
        allNodes = []
        self.flatten(self.root, allNodes)
    
        for n in allNodes:  #remove all relations in nodes in the flattened list for rebuilding
            n.loson = None
            n.hison = None
            n.disc = 0
    
        self.root = None
        self.root = self.buildBalanced(allNodes, 0)


    def flatten(self, Q, allNodes): #recursively visits every node in the tree and appends it to a list.
        if Q is None:
            return
        allNodes.append(Q)
        self.flatten(Q.loson, allNodes)
        self.flatten(Q.hison, allNodes)


    def buildBalanced(self, nodes, depth):  #takes in the cleaned and flattened node list and builds a new balanced kd tree out of it 
        if not nodes:
            return None
    
        if len(nodes) == 1:
            nodes[0].disc = depth % self.k
            return nodes[0]
        
        disc = depth % self.k
        nodes.sort(key=lambda n: n.key[disc])  #sort the list to be in the order of the current dimension
    
        medianIdx = len(nodes) // 2     #once sorted, pick the median as the root.
        medianNode = nodes[medianIdx]
        medianNode.disc = disc
    
        medianNode.loson = self.buildBalanced(nodes[:medianIdx], depth + 1) #fill in the rest of the tree by recursively repeating the process
        medianNode.hison = self.buildBalanced(nodes[medianIdx + 1:], depth + 1)
    
        return medianNode
    
#TESTING

K        = 8        # number of dimensions
N        = 100000   # number of nodes in the tree
REPEATS  = 1000     # number of times each test is repeated for timing
VALRANGE = 10000    # range of numbers for values


tree = KDtree(K)

points = [[random.randint(0, VALRANGE) for _ in range(K)] for _ in range(N)]

for p in points:
    tree.insert(node(p))

print(f"Tree built. ({N} nodes, {K} dimensions)\n")

start = time.perf_counter()
tree.optimise()
end = time.perf_counter()
print(f"Tree optimised in {(end - start):.6f} seconds\n")


print("--- Exact Search Timing ---")

exact_targets = [node(random.choice(points)) for _ in range(5)]

start = time.perf_counter()
for _ in range(REPEATS):
    for t in exact_targets:
        tree.exactSearch(t)
end = time.perf_counter()

print(f"Total time: {(end - start):.6f} seconds")
print(f"Average per search: {(end - start) / (REPEATS * len(exact_targets)):.9f} seconds\n")


print("--- Partial Search Timing ---")

partial_tests = [
    {i: random.randint(0, VALRANGE) for i in range(K // 2 + 1)}   # constrain just over half the dims
    for _ in range(5)
]

start = time.perf_counter()
for _ in range(REPEATS):
    for constraints in partial_tests:
        tree.partialSearch(constraints)
end = time.perf_counter()

print(f"Total time: {(end - start):.6f} seconds")
print(f"Average per search: {(end - start) / (REPEATS * len(partial_tests)):.9f} seconds\n")


print("--- Region Query Timing ---")

# generate regions that are roughly 10% of the total value range on each dimension.
region_size = VALRANGE // 10
region_tests = []
for _ in range(5):
    lower = [random.randint(0, VALRANGE - region_size) for _ in range(K)]
    upper = [l + region_size for l in lower]
    region_tests.append((upper, lower))

start = time.perf_counter()
for _ in range(REPEATS):
    for upper, lower in region_tests:
        tree.regionQuery(upper, lower)
end = time.perf_counter()

print(f"Total time: {(end - start):.6f} seconds")
print(f"Average per query: {(end - start) / (REPEATS * len(region_tests)):.9f} seconds\n")


print("--- NearestNeighbour Timing ---")

# random targets spread across the value range — not necessarily in the tree
nn_tests = [[random.randint(0, VALRANGE) for _ in range(K)] for _ in range(5)]

start = time.perf_counter()
for _ in range(REPEATS):
    for target in nn_tests:
        tree.nearestNeighbour1(target)
end = time.perf_counter()
nn1_time = end - start

print(f"NN1 total time: {nn1_time:.6f} seconds")
print(f"NN1 average per search: {nn1_time / (REPEATS * len(nn_tests)):.9f} seconds\n")

start = time.perf_counter()
for _ in range(REPEATS):
    for target in nn_tests:
        tree.nearestNeighbour2(target)
end = time.perf_counter()
nn2_time = end - start

print(f"NN2 total time: {nn2_time:.6f} seconds")
print(f"NN2 average per search: {nn2_time / (REPEATS * len(nn_tests)):.9f} seconds\n")

# direct comparison so the difference is immediately obvious
if nn2_time < nn1_time:
    print(f"NN2 was faster by {((nn1_time - nn2_time) / nn1_time * 100):.1f}%")
else:
    print(f"NN1 was faster by {((nn2_time - nn1_time) / nn2_time * 100):.1f}% — NN2 overhead not yet paying off at K={K}")