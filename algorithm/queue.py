import string

''' array queue '''
class array_queue:
    def __init__(self, cap):
        self.cap = cap
        self.buff_list = [0 for i in xrange(0,cap)]
        self.head = 0
        self.tail = 0
        self.size = 0

    def is_empty(self):
        return self.head == self.tail

    def is_full(self):
        return self.size == self.cap-1

    def enqueue(self, data):
        if self.is_full():
            print 'queue is full'
            return
        self.buff_list[self.tail] = data
        if self.tail == self.cap - 1:
            self.tail = 0
        else:
            self.tail += 1
            self.size += 1

    def dequeue(self):
        if self.is_empty():
            print 'queue is empty'
            return
        item = self.buff_list[self.head]
        if self.head == self.cap - 1:
            self.head = 0
        else:
            self.head += 1
            self.size -= 1
        return item

    def get_size(self):
        return self.size

    def dump_queue(self):
        print "h:%d t:%d size:%d cap:%d" % (self.head, self.tail, self.size, self.cap)
        for i in xrange(0, self.size):
            if self.head+i >= self.cap:
                print self.buff_list[self.head + i - self.cap]
            else:
                print self.buff_list[self.head+i]

''' link list queue '''
class node:
    def __init__(self, data):
        self.data = data
        self.next = None

class link_list_queue:
    def __init__(self):
        self.head = None
        self.size = 0
        self.tail = None

    def is_empty(self):
        return self.head == None

    def enqueue(self, data):
        new_node = node(data)
        if self.head == None:
            self.head = new_node
            self.tail = new_node
        else:
            self.tail.next = new_node
            self.tail = new_node
        self.size += 1

    def dequeue(self):
        if self.is_empty():
            print 'queue is empty'
            return
        ret_data = self.head.data
        self.head = self.head.next
        if self.head == None:
            self.tail = None
        self.size -= 1
        return ret_data

    def get_size(self):
        return self.size

    def dump_queue(self):
        print "size:%d" % (self.size)
        cur_node = self.head
        while cur_node != None:
            print cur_node.data
            cur_node = cur_node.next

if __name__ == '__main__':
    input_list_alphya = list(string.ascii_lowercase)
    input_list_digit = [0 + i for i in xrange(0,4)]
    #q = array_queue(10)
    print 'init queue:'
    q = link_list_queue()
    q.dump_queue()
    print 'enqueue_test:'
    print 'enqueue_alphya(a-h):'
    for i in input_list_alphya[0:8]:
        q.enqueue(i)
    q.dump_queue()
    print 'enqueue_digit(0-3):'
    for i in input_list_digit:
        q.enqueue(i)
    q.dump_queue()

    print 'dequeue_test:'
    print 'dequeue 5'
    for i in xrange(0,5):
        print q.dequeue()
    q.dump_queue()

    print 'dequeue 15'
    for i in xrange(0,15):
        print q.dequeue()
    q.dump_queue()

    print 'enqueue_digit(0-3):'
    for i in input_list_digit:
        q.enqueue(i)
    q.dump_queue()
