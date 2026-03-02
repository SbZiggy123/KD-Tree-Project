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
            elif result == "EQUAL":
                print("node is equal")
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
            print("added to result")   
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
    
    def regionQuery():
        pass
    
    def nearestNeighbour():
        pass
    
    def deleteRoot():
        pass
    
    def deleteRandom():
        pass
    
    def optimise():
        pass
    

tree = KDtree(2)

points = [
    [5, 5],
    [2, 3],
    [8, 7],
    [1, 9],
    [3, 4],
    [7, 2],
    [9, 6]
]

for p in points:
    tree.insert(node(p))

print("Tree built.")


print("\n--- Exact Search Tests ---")

target = node([3, 4])
found = tree.exactSearch(target)

if found:
    print("Found:", found.key)
else:
    print("Not found.")

target2 = node([10, 10])
found2 = tree.exactSearch(target2)

if found2:
    print("Found:", found2.key)
else:
    print("Correctly not found.")
    
    
print("\n--- Partial Search: x = 3 ---")

results = tree.partialSearch({0: 3})

for r in results:
    print(r.key)
    
    
print("\n--- Partial Search: x = 7, y = 2 ---")

results = tree.partialSearch({0: 7, 1: 2})

for r in results:
    print(r.key)