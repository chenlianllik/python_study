import os
import string
import time
import random
import serial 

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
