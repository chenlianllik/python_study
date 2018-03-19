import string
''' single link list '''
class single_list_node:
	def __init__(self, data):
		self.data = data
		self.next = None

class single_link_list:
	def __init__(self):
		self.head = None
		self.size = 0
	
	def is_empty(self):
		return self.head == None
	
	def insert(self, data, index):
		if index > self.size:
			print "insert index out of range, index:%d size:%d" % (index, self.size)
			return
		new_node = single_list_node(data)
		if self.is_empty(): 
			self.head = new_node
		elif index == 0:
			new_node.next = self.head
			self.head = new_node
		else:
			cur_node = self.head
			while index-1 > 0:
				cur_node = cur_node.next
				index -= 1
			new_node.next = cur_node.next
			cur_node.next = new_node
		self.size += 1
	
	def find(self, data):
		cur_node = self.head
		index = 0
		while cur_node != None:
			if cur_node.data == data:
				return index
			index += 1
			cur_node = cur_node.next
		return None
	
	def reverse(self):
		if self.head == None:
			return
		if self.head.next == None:
			return
		pre_node = self.head
		self.head = self.head.next
		pre_node.next = None
		while self.head != None:
			cur_node = self.head
			self.head = self.head.next
			cur_node.next = pre_node
			pre_node = cur_node
		self.head = pre_node

	def delete(self, data):
		cur_node = pre_node = self.head
		
		while cur_node != None:
			if cur_node.data == data:
				pre_node.next = cur_node.next
				self.size -= 1
				return 
			pre_node = cur_node
			cur_node = cur_node.next
	
	def get_size(self):
		return self.size
	
	def dump_list(self):
		print 'size:%d' % (self.size)
		cur_node = self.head
		dump_list = []
		while cur_node != None:
			dump_list.append(cur_node.data)
			cur_node = cur_node.next
		if dump_list:
			print dump_list

if __name__ == '__main__':
	input_list_alphya = list(string.ascii_lowercase)
	input_list_digit = [0 + i for i in xrange(0,4)]
	print 'init single_link_list:'
	ll = single_link_list()
	ll.dump_list()

	print 'insert_test:'
	print 'insert_alphya(a-h) from 0:'
	for i in input_list_alphya[0:8]:
		ll.insert(i,0)
	ll.dump_list()

	print 'insert_digit(0-3) from 2:'
	for i in input_list_digit:
		ll.insert(i,2)
	ll.dump_list()
	
	print 'find_alphya a:'
	print ll.find('a')
	print 'find_alphya x:'
	print ll.find('x')
	print 'find_alphya 1:'
	print ll.find(1)	
	print 'delete_alphya a:'
	ll.delete('a')
	ll.dump_list()
	print 'delete_alphya x:'
	ll.delete('x')
	ll.dump_list()
	print 'delete_digit 1:'
	ll.delete(1)
	ll.dump_list()
	print 'reverse:'
	ll.reverse()
	ll.dump_list()