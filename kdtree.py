#implementation made by me, based on the original 1975 paper.

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
            
    def insert(self, node):     #function to add a new node to the tree
        if self.root is None:   #if tree is empty, set node as root.
            self.root = node
            node.disc = 0
            return

        Q = self.root
        while True:             #if there is a root, loop down tree until node finds a spot
            result = self.successor(node, Q)
            if result == "HIGHER":
                node.disc = (Q.disc + 1) % self.k
                if Q.hison is None:
                    Q.hison = node
                    return
                Q = Q.hison
            elif result == "LOWER":
                node.disc = (Q.disc + 1) % self.k
                if Q.loson is None:
                    Q.loson = node
                    return
                Q = Q.loson
            else:
                return  # equal, don't insert
            
        
        
    def successor(self, node, Q):   #function to handle the measuring the input against the current node(Q) on its disc and returning a result.
        for i in range(0, self.k):  #starting with current disc, cycle through every disc in order until a non equal value is found, and judge it on that.
            sdisc = (Q.disc + i) % self.k
            
            if node.key[sdisc] < Q.key[sdisc]:
                return "LOWER"
            elif node.key[sdisc] > Q.key[sdisc]:
                return "HIGHER"
            
        return "EQUAL"  
            
            
    
    def exactSearch(self, target):  #finds the target node in the tree.
        Q = self.root
        while Q is not None:
            result = self.successor(target, Q)
            if result == "EQUAL":
                return Q
            elif result == "HIGHER":
                Q = Q.hison
            else:
                Q = Q.loson
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
    
        self.root = self.buildBalanced(allNodes, 0, 0, len(allNodes))


    def flatten(self, Q, allNodes): #pops every node in the tree and makes it a flat list.
        stack = [Q]
        while stack:
            node = stack.pop()
            if node is None:
                continue
            allNodes.append(node)
            stack.append(node.loson)
            stack.append(node.hison)

    
    def buildBalanced(self, nodes, depth, lo, hi):  #takes in the cleaned and flattened node list and builds a new balanced kd tree out of it
        if lo >= hi:
            return None
    
        disc = depth % self.k
        nodes[lo:hi] = sorted(nodes[lo:hi], key=lambda n: n.key[disc])  # sort only the slice in place
    
        medianIdx = (lo + hi) // 2
        medianNode = nodes[medianIdx]
        medianNode.disc = disc
    
        medianNode.loson = self.buildBalanced(nodes, depth + 1, lo, medianIdx)  #fill in the rest of the tree by recursively repeating the process
        medianNode.hison = self.buildBalanced(nodes, depth + 1, medianIdx + 1, hi)
    
        return medianNode