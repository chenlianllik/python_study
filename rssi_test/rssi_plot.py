import os
import serial 
import string
import csv
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time
import sys
import gc
import random
import Queue
import threading
from matplotlib import style
from subprocess import Popen, PIPE

class wlan_device(object):
	def __init__(self, device_port):
		if device_port == 'sim':
			self.device_port = device_port
			self.__pwr_state = 'off'
			return None
		out = os.popen('adb devices')
		cmd_out = out.read()
		if device_port in cmd_out:
			print "find adb device:"+device_port
			os.popen('adb -s ' + device_port + ' root')
			time.sleep(3)
			os.popen('adb -s ' + device_port + ' wait-for-device root')
		else:
			print "can't find adb device:"+self.device_port
			self.device_port = None
			return
		self.device_port = device_port
		self.__pwr_state = 'off'

	def get_rssi(self):
		if self.device_port == 'sim':
			rssi_meta_list = [random.uniform(-5, 5), random.uniform(-40, -45), random.uniform(-30, -35), random.uniform(-30, -45)]
			print rssi_meta_list
			return rssi_meta_list
		if self.device_port != None:
			os.popen('adb -s ' + self.device_port + ' wait-for-device root')
			rssi_meta_list = list()
			out = os.popen('adb -s ' + self.device_port + ' shell iw wlan0 station dump')
			cmd_out = out.read()
			print cmd_out
			if cmd_out.find('dBm') == -1:
				return rssi_meta_list
			ch0_rssi = int(cmd_out[cmd_out.find('[')+1:cmd_out.find(',')], 10)
			ch1_rssi = int(cmd_out[cmd_out.find(',')+2:cmd_out.find(']')], 10)
			cmb_rssi = int(cmd_out[cmd_out.find('dBm')-4:cmd_out.find('dBm')-1], 10)
			rssi_meta_list = [float(ch0_rssi - ch1_rssi), float(ch0_rssi), float(ch1_rssi), float(cmb_rssi)]
			print rssi_meta_list
			return rssi_meta_list

	def set_power_state(self, pwr_state):
		if self.device_port == 'sim':
			if pwr_state != self.__pwr_state:
				self.__pwr_state = pwr_state
			return
		if self.device_port != None:
			if pwr_state == 'off' and self.__pwr_state == 'on':
				os.popen('adb -s ' + self.device_port + ' shell iwpriv wlan0 setUnitTestCmd 19 3 1 0 1')
				self.__pwr_state = pwr_state
			elif pwr_state == 'on' and self.__pwr_state == 'off':
				os.popen('adb -s ' + self.device_port + ' shell iwpriv wlan0 setUnitTestCmd 19 3 1 0 0')
				self.__pwr_state = pwr_state

class turn_table_device(object):
	def __init__(self, com_port):
		try:
			self.__device_port = serial.Serial(com_port, 9600, timeout=1)
		except serial.SerialException:
			print 'can not find com port:' + com_port
			self.__device_port = None
		self.__angle_set_cnt = 0
	
	def close(self):
		if self.__device_port != None:
			self.__device_port.close()
	
	def angle_set(self, cmd, val):
		if cmd == 'step':
			self.__angle_set_cnt += val
			if self.__device_port != None:
				self.__device_port.write(str(val*800)+'s'+'\n')		
				time.sleep(4*val)
		elif cmd == 'reset':
			self.__angle_set_cnt = 0
			if self.__device_port != None:
				self.__device_port.write(str(self.__angle_set_cnt*(-800))+'s'+'\n')
				time.sleep(35)
		elif cmd == 'init':
			self.__angle_set_cnt = 0
			if self.__device_port != None:
				self.__device_port.write('0g'+'\n')
				time.sleep(10)
		print "angle set cmd:%s val:%d angle_set_cnt:%d" % (cmd, val, self.__angle_set_cnt)

class wlan_rssi_plot(object):
	def __init__(self, **kargs):
		device_port = kargs['device_port']
		test_type = kargs['test_type']
		plot_type = kargs['plot_type']
		self.__wlan_device = wlan_device(device_port)
		self.__wlan_device_port = self.__wlan_device.device_port
		if self.__wlan_device_port != None:
			style.use('fivethirtyeight')
			if test_type == 'rssi_monitor':
				self.__fig = plt.figure()
				self.__fig.canvas.set_window_title(test_type+'_'+self.__wlan_device_port)
				self.__ch_rssi_ax = self.__fig.add_subplot(212)
				self.__ch_imbalance_ax = self.__fig.add_subplot(211)
			elif test_type == 'rssi_turn_table':
				self.__fig = plt.figure(figsize=(10,5))
				self.__fig.canvas.set_window_title(test_type+'_'+self.__wlan_device_port)
				self.__ch_rssi_ax = self.__fig.add_subplot(122)
				self.__ch_imbalance_ax = self.__fig.add_subplot(121, projection='polar')
				self.__turn_table_test_cnt = kargs['turn_table_cnt']
				self.__turn_table_device = turn_table_device(kargs['com_port'])
				self.__rssi_avg_list = list()
			else:
				print "invalid test type:" + test_type
				return
			self.__test_type = test_type
			self.__ch_imbalance_ys = list()
			self.__ch0_rssi_ys = list()
			self.__ch1_rssi_ys = list()
			self.__cmb_rssi_ys = list()
			self.__rssi_dump_list = list()
			self.__plot_type = plot_type
			self.__q = Queue.Queue()
			self.__thread_term = False
			self.__rssi_thread = threading.Thread(target=self.__rssi_thread_func, name = 'rssi_thread')
			self.__rssi_thread.setDaemon(True)
			self.__rssi_thread.start()

			#output folder clean up
			if not os.path.exists(self.__test_type):
				os.mkdir(self.__test_type)
			fileList = os.listdir(self.__test_type)
			for filename in fileList:
				if self.__wlan_device_port in filename:
					os.remove(self.__test_type+'/'+filename)

	def __dump_rssi_to_csv(self, postfix):
		print "dump %d rssi entries to csv file" % len(self.__rssi_dump_list)
		if postfix != '':
			postfix = '_'+postfix
		file_name = self.__test_type+'/'+'rssi_dump_'+self.__wlan_device_port+ postfix +'.csv'
		first_write = False
		if not os.path.exists(file_name):
			first_write = True
		
		with open(file_name, 'ab') as csvfile:
			writer = csv.writer(csvfile)
			if first_write == True:
				writer.writerow(['ch_imbalance', 'ch0_rssi', 'ch1_rssi', 'cmb_rssi'])

			for rssi_entry in self.__rssi_dump_list:
				writer.writerow([rssi_entry[0], rssi_entry[1], rssi_entry[2], rssi_entry[3]])
	
	def __rssi_plot(self, xs_list):
		if self.__ch_rssi_ax != None:
			min_y, max_y= min(self.__cmb_rssi_ys), max(self.__cmb_rssi_ys)
			min_x, max_x = self.__cmb_rssi_ys.index(min_y), self.__cmb_rssi_ys.index(max_y)
			self.__ch_rssi_ax.clear()
			if min(self.__ch0_rssi_ys) != 0:
				self.__ch_rssi_ax.set_ylim([min(min(min_y, min(self.__ch0_rssi_ys)),min(self.__ch1_rssi_ys)) -10, max(max(max_y, max(self.__ch0_rssi_ys)),max(self.__ch1_rssi_ys))+10])
			else:
				self.__ch_rssi_ax.set_ylim([min_y-10, max_y+10])
			self.__ch_rssi_ax.set_title('ch_rssi', fontsize = 10)
			self.__ch_rssi_ax.annotate('min:'+str(min_y), xy=(min_x, min_y-3), fontsize=5, alpha=0.6)
			self.__ch_rssi_ax.annotate('max:'+str(max_y), xy=(max_x, max_y+2), fontsize=5, alpha=0.6)
			self.__ch_rssi_ax.plot(xs_list, self.__cmb_rssi_ys, '-', lw=2)
			self.__ch_rssi_ax.plot(xs_list, self.__ch0_rssi_ys, '-', lw=1, alpha=0.6)
			self.__ch_rssi_ax.plot(xs_list, self.__ch1_rssi_ys, '-', lw=1, alpha=0.6)
			self.__ch_rssi_ax.tick_params(labelsize=6)
			self.__ch_rssi_ax.legend(['cmb','ch0', 'ch1'], loc=1, fontsize=6)

		if self.__ch_imbalance_ax != None:
			self.__ch_imbalance_ax.clear()
			min_y, max_y= min(self.__ch_imbalance_ys), max(self.__ch_imbalance_ys)
			min_x, max_x = self.__ch_imbalance_ys.index(min_y), self.__ch_imbalance_ys.index(max_y)
			self.__ch_imbalance_ax.set_ylim([min_y-10, max_y+10])
			if self.__test_type == "rssi_turn_table":
				self.__ch_imbalance_ax.plot([float(item)/(57) for item in xs_list ], self.__ch_imbalance_ys, lw=2)
			else:
				self.__ch_imbalance_ax.annotate('min:'+str(min_y), xy=(min_x, min_y-3), fontsize=5, alpha=0.6)
				self.__ch_imbalance_ax.annotate('max:'+str(max_y), xy=(max_x, max_y+2), fontsize=5, alpha=0.6)
				self.__ch_imbalance_ax.plot(xs_list, self.__ch_imbalance_ys, lw=2)
			self.__ch_imbalance_ax.set_title('imbalance,ch0-ch1', fontsize = 10)
			self.__ch_imbalance_ax.tick_params(labelsize=6)

		plt.tight_layout()
		print gc.collect()

	def __rssi_thread_func(self):
		q = self.__q
		if self.__plot_type == 'poll':
			wlan_port = self.__wlan_device_port
			os.popen('adb -s ' + wlan_port + ' shell logcat -c')
			cmd = 'adb -s ' + wlan_port +  ' shell logcat -v time *:V | grep -i "L2ConnectedState !CMD_RSSI_POLL"'
			p = Popen(cmd, stdout=PIPE)
			while True:
				if self.__thread_term:
					return
				rssi_meta_list = list()
				cmd_out = p.stdout.readline()
				print "%s cmd:%s" %(threading.current_thread().name, cmd_out)
				if 'CMD_RSSI_POLL' in cmd_out:
					os.popen('adb -s ' + wlan_port + ' shell logcat -c')
					#break
				#time.sleep(1)
				#print cmd_out
				ch0_rssi = 0
				ch1_rssi = 0
				cmb_rssi = int(cmd_out[cmd_out.find('rssi=')+5:cmd_out.find('f=')-1], 10)
				print cmb_rssi
				rssi_meta_list = [float(ch0_rssi - ch1_rssi), float(ch0_rssi), float(ch1_rssi), float(cmb_rssi)]
				q.put(rssi_meta_list)
		else:
			while True:
				if self.__thread_term:
					return
				q.put(self.__wlan_device.get_rssi())
				time.sleep(3)

	def __animate_rssi_monitor_func(self, i):
		rssi_list = list()
		xs = list()
		rssi_list =	self.__q.get(True)

		if len(rssi_list) == 0:
			return
		self.__rssi_dump_list.append(rssi_list)
		if len(self.__rssi_dump_list) == 10:
			self.__dump_rssi_to_csv('')
			self.__rssi_dump_list[:] = []
		self.__ch_imbalance_ys.append(rssi_list[0])
		self.__ch0_rssi_ys.append(rssi_list[1])
		self.__ch1_rssi_ys.append(rssi_list[2])
		self.__cmb_rssi_ys.append(rssi_list[3])

		if len(self.__cmb_rssi_ys) > 60:
			self.__ch_imbalance_ys.pop(0)
			self.__ch0_rssi_ys.pop(0)
			self.__ch1_rssi_ys.pop(0)
			self.__cmb_rssi_ys.pop(0)

		for j in range(0, len(self.__cmb_rssi_ys)):	
			xs.append(j)
		self.__rssi_plot(xs)
		
	def __animate_chain_imbalance_turntable_func(self, i):
		rssi_list = list()
		xs = list()
		tmp_rssi_list = list()
		if len(self.__rssi_dump_list) == 35:
			print "done turn table test_cnt:%d" % self.__turn_table_test_cnt
			plt.savefig(self.__test_type+'/'+'chain_imbalance_turntable_'+self.__wlan_device_port+'_'+str(self.__turn_table_test_cnt)+'.png')
			self.__dump_rssi_to_csv(str(self.__turn_table_test_cnt))
			self.__turn_table_test_cnt -= 1
			self.__rssi_dump_list[:] = []
			self.__ch_imbalance_ys[:] = []
			self.__ch0_rssi_ys[:] = []
			self.__ch1_rssi_ys[:] = []
			self.__cmb_rssi_ys[:] = []

			print "reset turn table and wait for 35 sec"
			self.__turn_table_device.angle_set('reset', 0)
			if self.__turn_table_test_cnt == 0:
				self.wlan_device.set_power_state('off')
				exit()
		tmp_rssi_list = self.__q.get(True)
		if len(tmp_rssi_list) == 0:
			return
		self.__rssi_avg_list.append(tmp_rssi_list)
		if len(self.__rssi_avg_list)%10 == 0:
			rssi_list = [sum(zip_item)/len(zip_item) for zip_item in zip(*self.__rssi_avg_list)]
			print rssi_list
			self.__rssi_avg_list[:] = []
			self.__rssi_dump_list.append(rssi_list)
			self.__ch_imbalance_ys.append(rssi_list[0])
			self.__ch0_rssi_ys.append(rssi_list[1])
			self.__ch1_rssi_ys.append(rssi_list[2])
			self.__cmb_rssi_ys.append(rssi_list[3])
			if len(self.__rssi_dump_list) < 35:
				self.__turn_table_device.angle_set('step', 1)
		else:
			return

		for j in range(0, len(self.__cmb_rssi_ys)):	
			xs.append(j*10)
		self.__rssi_plot(xs)

	def __animate_run(self, intval):
		if self.__wlan_device_port == None:
			return
		if self.__test_type == "rssi_monitor":
			ani = animation.FuncAnimation(self.__fig, self.__animate_rssi_monitor_func, interval=intval)
			plt.show()
			self.__dump_rssi_to_csv('')
		elif self.__test_type == "rssi_turn_table":
			self.__wlan_device.set_power_state('on')
			self.__turn_table_device.angle_set('init', 0)
			ani = animation.FuncAnimation(self.__fig, self.__animate_chain_imbalance_turntable_func, interval=intval)
			plt.show()
			self.__wlan_device.set_power_state('off')
			self.__turn_table_device.angle_set('reset', 0)
			self.__turn_table_device.close()

	def plot_run(self, intval, use_thread):
		# TODO: use threading
		if use_thread == True:
			pass
			#self.plot_process = Process(target=self.animate_run,args=(intval,))
			#self.plot_process.daemon = True
			#self.plot_process.start()
			#self.plot_process.join()
			#print "thread exit"
		else:
			self.__animate_run(intval)
			print "end ploting"
			self.__thread_term = True
			self.__rssi_thread.join()
			
if __name__ == "__main__":
	if len(sys.argv) >= 3:
		adb_port = sys.argv[1]
		if sys.argv[2] == '1':#turn table test
			com_port = 'COM8'
			turn_table_cnt = 3
			if len(sys.argv) > 3: 
				com_port = sys.argv[3]
			if len(sys.argv) > 4:
				turn_table_cnt = int(sys.argv[4],10)
			rssi_turn_plt = wlan_rssi_plot(device_port = adb_port, test_type = 'rssi_turn_table', com_port=com_port, turn_table_cnt=turn_table_cnt, plot_type = 'sync')
			rssi_turn_plt.plot_run(500, False)	
		else:#rssi moinitor
			rssi_mon_plt = wlan_rssi_plot(device_port = adb_port, test_type = 'rssi_monitor', plot_type = 'poll')
			rssi_mon_plt.plot_run(500, False)			
	else:
		print "invalid test case " + test_case
