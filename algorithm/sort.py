''' sort class '''
import random
import datetime

class algo_sort:
	def __init__(self):
		pass
	
	def bubble_sort(self, nums):
		cur_time = datetime.datetime.now()
		if len(nums) <= 1:
			return nums
		
		for i in reversed(xrange(0,len(nums))):
			changes = 0
			for j in xrange(0, i):
				if nums[j]> nums[j+1]:
					tmp = nums[j]
					nums[j] = nums[j+1]
					nums[j+1] = tmp
					changes = 1
			
			# changes == 0 means the list has been sorted in this iteration
			if changes == 0:
				break
		print 'bubble_sort cost:' 
		print datetime.datetime.now() - cur_time
		return nums
	
	def select_sort(self,nums):
		cur_time = datetime.datetime.now()
		if len(nums) <= 1:
			return nums
		num_len = len(nums)
		for i in xrange(0, num_len-1):
			changes = 0
			for j in xrange(i+1, num_len):
				if nums[j] < nums[i]:
					tmp = nums[i]
					nums[i] = nums[j]
					nums[j] = tmp
					changes = 1
			if changes == 0:
				break
		print 'select_sort cost:' 
		print datetime.datetime.now() - cur_time
		return nums
		
	def quick_sort(self, nums):
		cur_time = datetime.datetime.now()
		if len(nums) <= 1:
			return nums
		def _quick_sort(nums, left, right):
			if left >= right:
				return
			mid = nums[left]
			i,j= left,right
			while i < j:
				while nums[j] > mid and i < j:
					j-=1
				if i == j:
					nums[j] = mid
					break
				nums[i] = nums[j]
				i+=1
				while nums[i] < mid and i < j:
					i+=1
				if i == j:
					nums[j] = mid
					break
				nums[j] = nums[i]
				j-=1
			_quick_sort(nums, left, i-1)
			_quick_sort(nums, i+1, right)
		_quick_sort(nums, 0, len(nums)-1)
		print 'quick_sort cost:' 
		print datetime.datetime.now() - cur_time		
		return nums

	def merge_sort(self, nums):
		def _merge(nums, left, mid, right):
			sorted_list = []
			left_len = mid - left + 1 #important! can't use mid-left, otherwise left can't be selected in  l:0 m:0 r:1 case.
			right_len = right - mid
			i, j = 0, 0
			#print "left:%d mid:%d right:%d" % (left, mid, right)
			while i < left_len and j < right_len:
				#print "i:%d j:%d" % (i,j)
				if nums[left+i] <= nums[mid+j+1]:
					sorted_list.append(nums[left+i])
					i += 1
				else:
					sorted_list.append(nums[mid+j+1])
					j += 1
			while i < left_len:
				sorted_list.append(nums[left+i])
				i += 1
			while j < right_len:
				sorted_list.append(nums[mid+j+1])
				j += 1
			#print sorted_list
			for item in xrange(0,len(sorted_list)):
				nums[left+item] = sorted_list[item]

		def _merge_sort(nums, left, right):
			if left < right:
				mid = left + (right-left)/2
				_merge_sort(nums, left, mid)
				_merge_sort(nums, mid+1, right)
				_merge(nums, left, mid, right)
		cur_time = datetime.datetime.now()
		if len(nums) <= 1:
			return nums
		_merge_sort(nums, 0, len(nums)-1)
		print 'merge_sort cost:' 
		print datetime.datetime.now() - cur_time	
		return nums
if __name__ == '__main__':
	input_list = []
	for x in range(0, 100):
		input_list.append(random.randint(0, 100))
	
	print "input_list:"
	print input_list
	my_sort = algo_sort()
	#print my_sort.select_sort(input_list)
	#print my_sort.bubble_sort(input_list)
	#print my_sort.quick_sort(input_list)
	input_list = []
	print my_sort.merge_sort(input_list)
	for x in range(0, 1):
		input_list.append(random.randint(0, 100))
	print "input_list:"
	print input_list
	print my_sort.merge_sort(input_list)
	
	
	