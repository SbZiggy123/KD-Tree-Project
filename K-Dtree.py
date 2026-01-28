class kdTree:
	def __init__(self, P, d=0):
		n = len(P)
		m = n // 2
		P.sort(key = lambda x:x[d])
		self.point = P[m]
		self.d = d
		d = (d+1) % len(P[0])
		self.left = None
		self.right = None
		if m > 0:
			self.left = kdTree(P[:m], d)
		if n - (m+1) > 0:
			self.right = kdTree(P[m+1:], d)

	def rangeSearch(self, box):
		p = self.point
		if inbox(p, box):
			yield p
		min, max = box[self.d]
		split = p[self.d]
		if self.left is not None and split >= min:
			yield from self.left.rangeSearch(box)
		if self.right is not None and split <= max:
  			yield from self.right.rangeSearch(box)
      
    
def inbox(p, box):
    return all(box[0][i] <= p[i] <= box[1][i] for i in range(len(p)))


P = [(1,2),(3,4),(5,6)]
T = kdTree(P)
print(list(T.rangeSearch([(4, 4), (7, 7)])))