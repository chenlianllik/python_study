import os
import string
import time
import datetime
import random
import serial 

class wlan_device(object):
	def __init__(self, device_port):
		if device_port == 'sim':
			self.device_port = device_port
			self.__pwr_state = 'off'
			self.__wlm_stats_req_time = time.time()
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
			rssi_meta_list = [random.randint(-5, 5), random.randint(-40, -45), random.randint(-30, -35), random.randint(-30, -45)]
			print rssi_meta_list
			return rssi_meta_list
		if self.device_port != None:
			#os.popen('adb -s ' + self.device_port + ' wait-for-device root')
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
	
	def get_link_info(self):
		if self.device_port != None:
			link_info_dict = dict()
			out = os.popen('adb -s ' + self.device_port + ' shell iw wlan0 link')
			cmd_list = out.read().split('\n')
			for cmd in cmd_list:
				tmp_list = cmd.split(': ')
				if 'SSID' in cmd:
					link_info_dict[tmp_list[0]] = tmp_list[1]
				if 'freq' in cmd:
					link_info_dict[tmp_list[0]] = tmp_list[1]
		return link_info_dict
	
	def get_ping_latency(self, ip_addr):
		if self.device_port == 'sim':
			out = os.popen('ping -n 1 -w 2 '+ ip_addr)
			cmd_out = out.read()
			#print cmd_out
			if "timed out" in cmd_out:
				return 2000
			elif "time<" in cmd_out:
				return 1
			else:
				latency_str = cmd_out[cmd_out.find('Average = ')+len('Average = '):]
				#print latency_str
				return int(latency_str[:latency_str.find('ms')])
		else:
			pass
	
	def get_wlm_link_stats(self, cmd_str):
		wlm_link_stats_dict = {}
		if self.device_port == 'sim':
			wlm_link_stats_dict['timestamp'] = time.time() - self.__wlm_stats_req_time
			wlm_link_stats_dict['pwr_on_period'] =  random.randint(0, 100)
			wlm_link_stats_dict['congestion_level'] =  random.randint(0, 50)
			wlm_link_stats_dict['bcn_rssi'] =  random.randint(-96, 0)
			wlm_link_stats_dict['scan_on_period'] =  random.randint(0, 50)
			#self.__last_wlm_stats_req_time = time.time()
		else:
			pass
		print wlm_link_stats_dict
		return wlm_link_stats_dict
	def get_wlm_ac_stats(self, cmd_str):
		wlm_ac_stats_dict = {}
		if self.device_port == 'sim':
			wlm_ac_stats_dict['tx_mpdu'] = [random.randint(0, 20),random.randint(0, 40),random.randint(0, 60),random.randint(0, 20)]
			wlm_ac_stats_dict['rx_mpdu'] = [random.randint(0, 20),random.randint(0, 40),random.randint(0, 60),random.randint(0, 20)]
			wlm_ac_stats_dict['tx_ampdu'] = [random.randint(0, 10),random.randint(0, 30),random.randint(0, 50),random.randint(0, 10)]
			wlm_ac_stats_dict['rx_ampdu'] = [random.randint(0, 10),random.randint(0, 30),random.randint(0, 50),random.randint(0, 10)]
			wlm_ac_stats_dict['mpdu_lost'] = [random.randint(0, 10),random.randint(0, 30),random.randint(0, 50),random.randint(0, 10)]
			wlm_ac_stats_dict['total_retries'] = [random.randint(0, 10),random.randint(0, 10),random.randint(0, 10),random.randint(0, 10)]
			wlm_ac_stats_dict['contention_time_avg'] = [random.randint(0, 100),random.randint(0, 100),random.randint(0, 100),random.randint(0, 100)]
			#self.__last_wlm_stats_req_time = time.time()
		else:
			pass
		print wlm_ac_stats_dict
		return wlm_ac_stats_dict

	def get_wlm_stats(self):
		return self.get_wlm_link_stats(None), self.get_wlm_ac_stats(None)

def get_wlan_device_list():
	out = os.popen('adb devices')
	cmd_list = out.read().split('\n')
	dev_id = list()
	for cmd in cmd_list:
		if '\tdevice' in cmd:
			dev_id.append(cmd[:cmd.find('\tdevice')])
	
	return dev_id
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

if __name__ == '__main__':
	wlan_dev = wlan_device('sim')
	test_count = 10
	while test_count > 0:
		ap_latency = wlan_dev.get_ping_latency('192.168.1.1')
		print "ap latency:{0}ms".format(ap_latency)
		game_server_latency = wlan_dev.get_ping_latency('52.94.8.22')
		print "ap game_server_latency:{0}ms".format(game_server_latency)
		wlan_dev.get_wlm_stats()
		time.sleep(3)
		test_count -= 1
	