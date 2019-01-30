import csv

def wlm_offset_parser(csv_file_name):
	offset_map_dict = {}
	cur_offset = 0
	struct_array_num = 1
	struct_size = 0
	with open(csv_file_name) as csv_file:
		reader = csv.reader(csv_file)
		for row in reader:
			if 'WMITLV_TAG_STRUC' in row[0]:
				struct_size = int(row[1][-4:], 16)
				struct_array_num = int(row[2])
				struct_size = struct_size/4
				
			else:
				offset_map_dict[row[0]] = [cur_offset + i*struct_size for i in xrange(struct_array_num) ]
				cur_offset+=1
			
	print offset_map_dict
	return offset_map_dict
if __name__ == '__main__':
	wlm_offset_parser('wlm_stats_offset_map.csv')