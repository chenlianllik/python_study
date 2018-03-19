import string

''' array stack '''

class array_stack:
    def __init__(self, cap):
        self.cap = cap
        self.buff_list = [0 for i in xrange(0, cap)]
        self.top = 0

    def is_empty(self):
        return self.top == 0

    def is_full(self):
        return self.top == self.cap

    def push(self, data):
        if self.is_full():
            print 'stack is full'
            return
        self.buff_list[self.top] = data
        self.top += 1

    def pop(self):
        if self.is_empty():
            print 'stack is empty'
            return
        self.top -= 1
        return self.buff_list[self.top]

    def get_size(self):
        return self.top

    def dump_stack(self):
        print "size:%d cap:%d" % (self.top, self.cap)
        for i in xrange(0, self.top):
            print self.buff_list[self.top - i - 1]

''' link list stack '''

class node:
    def __init__(self, data):
        self.data = data
        self.next = None

class link_list_stack:
    def __init__(self):
        self.top = None
        self.size = 0

    def is_empty(self):
        return self.top == None

    def push(self, data):
        new_node = node(data)
        if self.is_empty():
            self.top = new_node
        else:
            new_node.next = self.top
            self.top = new_node
        self.size += 1

    def pop(self):
        if self.is_empty():
            print 'stack is empty'
            return
        ret_data = self.top.data
        self.top = self.top.next
        self.size -= 1
        return ret_data

    def get_size(self):
        return self.size

    def dump_stack(self):
        print "size:%d" % (self.size)
        cur_node = self.top
        while cur_node != None:
            print cur_node.data
            cur_node = cur_node.next

if __name__ == '__main__':
    input_list_alphya = list(string.ascii_lowercase)
    input_list_digit = [0 + i for i in xrange(0,4)]
    print 'init stack:'
    #s = array_stack(10)
    s = link_list_stack()
    s.dump_stack()
    print 'push_test:'
    print 'push_alpha(a-h)'
    for i in input_list_alphya[0:8]:
        s.push(i)
    s.dump_stack()
    print 'push_digit(0-3):'
    for i in input_list_digit:
        s.push(i)
    s.dump_stack()

    print 'pop_test:'
    print 'pop 5'
    for i in xrange(0,5):
        print s.pop()
    s.dump_stack()

    print 'pop 15'
    for i in xrange(0,15):
        print s.pop()
    s.dump_stack()

    print 'push(0-3):'
    for i in input_list_digit:
        s.push(i)
    s.dump_stack()
