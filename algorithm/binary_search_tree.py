''' binary search tree '''
import random
class bst_node:
	def __init__(self, data):
		self.data = data
		self.left_child = None
		self.right_child = None
		self.parent = None
class binary_search_tree:
	def __init__(self):
		self.root = None

	def insert(self, data):
		if self.root == None:
			self.root = bst_node(data)
			return
		
		def _insert(node, data):
			if data == node.data:
				return
			elif node == None:
				return
				
			if data > node.data:
				if node.right_child == None:
					node.right_child = bst_node(data)
					node.right_child.parent = node
				else:
					_insert(node.right_child, data)
			else:
				if node.left_child == None:
					node.left_child = bst_node(data)
					node.left_child.parent = node
				else:
					_insert(node.left_child, data)
		_insert(self.root, data)
	def node_type(self, node):
		type = ''
		if node.parent == None:
			type += "root"
		if node.left_child == None and node.right_child == None:#leaf node
			type += "leaf" 
		elif node.left_child == None:#only has right child
			type += "right"
		elif node.right_child == None:#only has left child
			type += "left"
		else:
			type += "two child"
		return type
	def delete(self, data):
		def _find_min(node):
			if node.left_child == None:
				return node.data
			return _find_min(node.left_child)
		def _delete(node, data):
			if node:
				if data == node.data:
					#print "find:%d" % (data)
					if node.left_child == None and node.right_child == None:#leaf node
						if node.parent == None:#root node delete
							self.root = None
						elif node.parent.left_child == node:
							node.parent.left_child = None
						else:
							node.parent.right_child = None
					elif node.left_child == None:#only has right child
						if node.parent == None:#root node delete
							self.root = node.right_child
							node.right_child.parent = None
						elif node.parent.left_child == node:
							node.parent.left_child = node.right_child
							node.right_child.parent = node.parent
						else:
							node.parent.right_child = node.right_child
							node.right_child.parent = node.parent
					elif node.right_child == None:#only has left child
						if node.parent == None:#root node delete
							self.root = node.left_child
							node.left_child.parent = None
						elif node.parent.left_child == node:
							node.parent.left_child = node.left_child
							node.left_child.parent = node.parent
						else:
							node.parent.right_child = node.left_child
							node.left_child.parent = node.parent
					else:
						right_min = _find_min(node.right_child)#find min in right child tree
						node.data = right_min#exchange right_min with this node
						print 'del min %d' % (right_min)
						_delete(node.right_child, right_min)#delete right min
				elif data > node.data:
					#print ">:%d %s" % (node.data, self.node_type(node))
					_delete(node.right_child, data)
				else:
					#print "<:%d %s" % (node.data, self.node_type(node))
					_delete(node.left_child, data)
		_delete(self.root, data)
	def traversal(self):
		print '<<<<<<<<<<<<<<<<<<<<<'
		def _inorder_travesal(node):
			if node:
				_inorder_travesal(node.left_child)
				type = self.node_type(node)
				print "%s:%d" % (type, node.data)
				_inorder_travesal(node.right_child)
		_inorder_travesal(self.root)	
		print '>>>>>>>>>>>>>>>>>>>>>>'
if __name__ == '__main__':
	#input_list = [96, 39, 47, 70, 95, 40, 94, 50, 45, 78]
	input_list = []
	for x in range (0, 10):
		input_list.append(random.randint(0, 100))
	print 'input_list:'
	print input_list
	bst = binary_search_tree()
	print 'insert test:'
	for i in input_list:
		bst.insert(i)
	bst.traversal()
	print 'del test:'
	for i in input_list:
		print 'del:%d' % (i)
		bst.delete(i)
		bst.traversal()
	