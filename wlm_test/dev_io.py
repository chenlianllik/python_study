import os
import string
import time
import datetime
import random
import serial 
from offset_parser import wlm_offset_parser

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
		self.__wlm_offset_map = None
		self.__wlm_stats_req_time = time.time()
		self.__wlam_last_ac_stats_dict = dict()

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
	
	def get_ping_latency(self, ip_addr, count):
		if self.device_port == 'sim':
			if ip_addr == '':
				return float(-1)
			out = os.popen('ping -n 1 -w 2 '+ ip_addr)
			cmd_out = out.read()
			print cmd_out
			if "timed out" in cmd_out:
				return 1000
			elif "time<" in cmd_out:
				return 1
			else:
				cmd_out = cmd_out[cmd_out.find('Average =')+len('Average ='):]
				cmd_out = cmd_out[:cmd_out.find('ms')]
				return float(cmd_out)
		else:
			if ip_addr == '':
				return float(-1)
			ping_cmd = 'adb -s {} shell ping -i 0.08 -c {} -W 1 {}'.format(self.device_port, count, ip_addr)
			out = os.popen(ping_cmd)
			cmd_out = out.read()
			print cmd_out
			if '100% packet loss' in cmd_out:
				return float(1000)
			cmd_out = cmd_out[cmd_out.find('mdev = ')+len('mdev = '):]
			cmd_out = cmd_out[:cmd_out.find(' ms')]
			print float(cmd_out.split('/')[1])
			
			return float(cmd_out.split('/')[1])
	
	def get_wlm_link_stats(self, stats_value_list):
		wlm_link_stats_dict = {}
		if self.device_port == 'sim':
			wlm_link_stats_dict['timestamp'] = "{0:.3f}".format(time.time() - self.__wlm_stats_req_time)
			wlm_link_stats_dict['pwr_on_period'] =  random.randint(0, 100)
			wlm_link_stats_dict['congestion_level'] =  random.randint(0, 50)
			wlm_link_stats_dict['bcn_rssi'] =  random.randint(-96, 0)
			wlm_link_stats_dict['scan_period'] =  random.randint(0, 50)
			wlm_link_stats_dict['phy_err'] =  random.randint(0, 100)
			wlm_link_stats_dict['mpdu_err'] =  random.randint(0, 100)
			wlm_link_stats_dict['last_tx_rate'] =  random.randint(0, 100)
			#self.__last_wlm_stats_req_time = time.time()
		else:
			wlm_link_stats_dict['timestamp'] = "{0:.3f}".format(time.time() - self.__wlm_stats_req_time)
			wlm_link_stats_dict['pwr_on_period'] =  int(stats_value_list[self.__wlm_offset_map['pwr_on_period'][0]], 16)
			wlm_link_stats_dict['congestion_level'] =  int(stats_value_list[self.__wlm_offset_map['congestion_level'][0]], 16)
			tmp_str = stats_value_list[self.__wlm_offset_map['bcn_rssi'][0]]
			tmp_str = tmp_str[len(tmp_str)-2:]
			wlm_link_stats_dict['bcn_rssi'] =  int(tmp_str, 16) - 256
			wlm_link_stats_dict['scan_period'] =  int(stats_value_list[self.__wlm_offset_map['scan_period'][0]], 16)
			wlm_link_stats_dict['phy_err'] =  int(stats_value_list[self.__wlm_offset_map['phy_err'][0]], 16)
			wlm_link_stats_dict['mpdu_err'] =  int(stats_value_list[self.__wlm_offset_map['mpdu_err'][0]], 16)
			wlm_link_stats_dict['last_tx_rate'] =  int(stats_value_list[self.__wlm_offset_map['last_tx_rate'][0]], 16)
		#print wlm_link_stats_dict
		return wlm_link_stats_dict

	def get_wlm_ac_stats(self, stats_value_list):
		wlm_ac_stats_dict = {}
		if self.device_port == 'sim':
			wlm_ac_stats_dict['tx_mpdu'] = [random.randint(0, 20),random.randint(0, 40),random.randint(0, 60),random.randint(0, 20)]
			wlm_ac_stats_dict['rx_mpdu'] = [random.randint(0, 20),random.randint(0, 40),random.randint(0, 60),random.randint(0, 20)]
			wlm_ac_stats_dict['tx_ampdu'] = [random.randint(0, 10),random.randint(0, 30),random.randint(0, 50),random.randint(0, 10)]
			wlm_ac_stats_dict['rx_ampdu'] = [random.randint(0, 10),random.randint(0, 30),random.randint(0, 50),random.randint(0, 10)]
			wlm_ac_stats_dict['mpdu_lost'] = [random.randint(0, 10),random.randint(0, 30),random.randint(0, 50),random.randint(0, 10)]
			wlm_ac_stats_dict['retries'] = [random.randint(0, 10),random.randint(0, 10),random.randint(0, 10),random.randint(0, 10)]
			wlm_ac_stats_dict['contention_time_avg'] = [random.randint(0, 100),random.randint(0, 100),random.randint(0, 100),random.randint(0, 100)]
			#self.__last_wlm_stats_req_time = time.time()
		else:
			def __calc_wlm_ac_stats(stats_value_list, ac_stats_name):
				tmp_list = [int(stats_value_list[offset], 16) for offset in self.__wlm_offset_map[ac_stats_name]]
				if not self.__wlam_last_ac_stats_dict.has_key(ac_stats_name):
					self.__wlam_last_ac_stats_dict[ac_stats_name] = tmp_list
					return tmp_list
				else:
					delta_list = [tmp_list[i] - self.__wlam_last_ac_stats_dict[ac_stats_name][i] for i in xrange(len(tmp_list))]
					self.__wlam_last_ac_stats_dict[ac_stats_name] = tmp_list
					return delta_list
			wlm_ac_stats_dict['tx_mpdu'] = __calc_wlm_ac_stats(stats_value_list, 'tx_mpdu')
			wlm_ac_stats_dict['rx_mpdu'] = __calc_wlm_ac_stats(stats_value_list, 'rx_mpdu')
			wlm_ac_stats_dict['tx_ampdu'] = __calc_wlm_ac_stats(stats_value_list, 'tx_ampdu')
			wlm_ac_stats_dict['rx_ampdu'] = __calc_wlm_ac_stats(stats_value_list, 'rx_ampdu')
			wlm_ac_stats_dict['mpdu_lost'] = __calc_wlm_ac_stats(stats_value_list, 'mpdu_lost')
			wlm_ac_stats_dict['retries'] = __calc_wlm_ac_stats(stats_value_list, 'retries')
			wlm_ac_stats_dict['contention_time_avg'] = [int(stats_value_list[offset], 16) for offset in self.__wlm_offset_map['contention_time_avg']]
		#print wlm_ac_stats_dict
		return wlm_ac_stats_dict

	def get_wlm_stats(self):
		if self.device_port == 'sim':
			return self.get_wlm_link_stats(None), self.get_wlm_ac_stats(None)
		else:
			stats_value_list = []
			out = os.popen('adb -s ' + self.device_port + ' shell iwpriv wlan0 get_wlm_stats 3')
			cmd_out = out.read()
			cmd_out = cmd_out[cmd_out.find('data')+6:].rstrip()
			stats_value_list = cmd_out.split(' ')
			#print stats_value_list
		return self.get_wlm_link_stats(stats_value_list), self.get_wlm_ac_stats(stats_value_list)
	def prepare_wlm_stats(self):
		if self.device_port == 'sim':
			pass
		else:
			if self.__wlm_offset_map == None:
				self.__wlm_offset_map = wlm_offset_parser('wlm_stats_offset_map.csv')
				out = os.popen('adb -s ' + self.device_port + ' shell iwpriv wlan0 get_wlm_stats 3')
				cmd_out = out.read()
				cmd_out = cmd_out[cmd_out.find('data')+6:].rstrip()
				stats_value_list = cmd_out.split(' ')
				self.get_wlm_ac_stats(stats_value_list)
	def set_wlm_latency_mode(self, mode):
		if self.device_port == 'sim':
			pass
		else:
			if mode == 'ultra-low':
				os.popen('adb -s ' + self.device_port + ' shell iwpriv wlan0 setUnitTestCmd 0x2f 5 0 3 20 20 0xc83')
			elif mode == 'Moderate':
				os.popen('adb -s ' + self.device_port + ' shell iwpriv wlan0 setUnitTestCmd 0x2f 5 0 1 60 60 0x8')
			elif mode == 'low':
				os.popen('adb -s ' + self.device_port + ' shell iwpriv wlan0 setUnitTestCmd 0x2f 5 0 2 40 40 0x8a')
			elif mode == 'normal':
				os.popen('adb -s ' + self.device_port + ' shell iwpriv wlan0 setUnitTestCmd 0x2f 5 0 0 0 0 0x0 ')
			else:
				print "do not support this mode:{}".format(mode) 

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
	wlan_dev = wlan_device('7e2cc7ce')
	wlan_dev.prepare_wlm_stats()
	test_count = 10
	while test_count > 0:
		wlan_dev.get_wlm_stats()
		time.sleep(3)
		test_count -= 1
