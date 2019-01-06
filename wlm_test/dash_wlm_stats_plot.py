import dash
from dash.dependencies import Input, Output, Event, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import plotly
from dev_io import wlan_device
import dev_io
import csv
import os
import numpy as np
import datetime

start_date_time = datetime.datetime.now()
wlm_stats_plot_list = []
wlm_stats_cache_list = []
wlm_stats_high_latency_list = []
high_latency_threshold = 60
wlm_stats_ping_cdf_dict = {
	'gaming_server':[],
	'AP':[]
}
total_ping_cnt = 0
tolal_high_latency_cnt = 0
current_test_state = 'start'
id_ac_map = ['VO','VI','BE','BK']
ping_addr_dict = {'gaming_server':'192.168.1.1', 'AP':'192.168.1.1'}
result_csv_file_name = "ping_test_result.csv"


app = dash.Dash(__name__)
#color_list = ['rgb(22, 96, 167)', 'rgb(205, 12, 24)']
app.css.append_css({'external_url': 'https://cdn.rawgit.com/plotly/dash-app-stylesheets/2d266c578d2a6e8850ebce48fdb52759b2aef506/stylesheet-oil-and-gas.css'})  # noqa: E501
#wlan_dev = wlan_device('sim')
wlan_dev = wlan_device('7e2cc7ce')
wlan_dev.prepare_wlm_stats()
app.layout = html.Div(children=[
	html.H1("WLAN ping latency dashboard", style={'textAlign': 'center','color': '#f2f2f2', 'backgroundColor':'#003366'}, className='row'),
	html.Div(children = [
		html.H4(children='ping result', className = 'row'),
		html.Div(children = [
			html.Div(children = [
				html.Div(children = [
					html.Label('gaming server IP address:', className = 'two columns'),
					html.Label('local AP IP address:', className = 'two columns'),
					html.Div(id='test_state_output', className = 'six columns'),
				],className = 'row'),
				html.Div(children = [
					html.Div(children = [
						dcc.Input(id='gaming_server_input', type='text', value=ping_addr_dict['gaming_server']),
					],className='two columns'),	
					html.Div(children = [
						dcc.Input(id='AP_input', type='text', value=ping_addr_dict['AP']),
					],className='two columns'),	
					html.Button('start', id='start_button', n_clicks_timestamp='0', className = 'one column'),
					html.Button('stop', id='stop_button', n_clicks_timestamp='0',className = 'one column'),
					html.Button('restart', id='restart_button', n_clicks_timestamp='0',className = 'one column'),
				],className = 'row'),
			], className = 'row'),
			html.Div(id='ping_output',className='row'),
		], className='row'),
		html.Div(children = html.Div(id='wlm_ping_stats_graphs'), className='row'),
	],className = 'row'),
	html.Hr(),
	html.H4(children='wlm stats', className = 'row'),
	html.Div(children = [
		html.Div(children = [
			html.Div(children = [
				dcc.Checklist(
					id = 'link_checkbox',
					options=[
						{'label': 'bcn_rssi', 'value': 'bcn_rssi'},
						{'label': 'pwr_on_period', 'value': 'pwr_on_period'},
						{'label': 'scan_period', 'value': 'scan_period'},
						{'label': 'congestion_level', 'value': 'congestion_level'},
					],
					values=['bcn_rssi', 'congestion_level', 'pwr_on_period'],
					labelStyle={'display': 'inline-block'},
				),
			], className='row'),
			html.Div(children = html.Div(id='wlm_link_stats_graphs'), className='row'),
		], className='six columns'),
		html.Div(children = [
			html.Div(children = [
				dcc.Checklist(
					id = 'ac_checkbox',
					options=[
						{'label': 'retries', 'value': 'retries'},
						{'label': 'mpdu_lost', 'value': 'mpdu_lost'},
						{'label': 'rx_ampdu', 'value': 'rx_ampdu'},
						{'label': 'rx_mpdu', 'value': 'rx_mpdu'},
						{'label': 'tx_mpdu', 'value': 'tx_mpdu'},
						{'label': 'tx_ampdu', 'value': 'tx_ampdu'},
						{'label': 'contention_time_avg', 'value': 'contention_time_avg'},
					],
					values=['retries', 'mpdu_lost', 'contention_time_avg'],
					labelStyle={'display': 'inline-block'},
				),
			], className='row'),
			html.Div(children = html.Div(id='wlm_ac_stats_graphs'), className='row'),
		], className='six columns'),
	], className='row'),
	html.Hr(),
	html.H4(children='high latency results', className = 'row'),
	html.Div(id='high_latency_threshold_output',className = 'row'),
	html.Div(children = [
		dcc.Slider(
			id = 'high_latency_threshold_slider',
			min=0,
			max=10,
			marks={i: '{}ms'.format(i*30) for i in range(11)},
			value=high_latency_threshold/30,
		),
	],className='row'),
	html.Hr(),
	html.Div(children = [html.Label(' '),html.Div(id='wlm_high_latency_dashtable')], className='row'),
    #dcc.Graph(id='rssi-graph', animate=True),
	dcc.Interval(id='wlm_stats_update', interval=3000),
], style={'backgroundColor':'#f0f0f5'})

def wlm_ping_cdf_graph():
	grap_data_list = []
	max_axis = 0
	for key in wlm_stats_ping_cdf_dict.keys():
		max_axis = max(max(wlm_stats_ping_cdf_dict[key]), max_axis)
	max_axis = int(max_axis) + 50
	for key in wlm_stats_ping_cdf_dict.keys():
		data = wlm_stats_ping_cdf_dict[key]
		hist, bin_edges = np.histogram(data, bins = range(max_axis))
		#print hist
		cdf = np.cumsum(hist)
		grap_data = plotly.graph_objs.Scatter(
			x=bin_edges[1:],
			y=cdf*100/len(data),
			name=key,
			line = dict(
				width = 2,
				)
		)
		grap_data_list.append(grap_data)
		#print cdf*100/len(data)
	grap_layout = plotly.graph_objs.Layout(
		xaxis=dict(range=[0,max_axis]),
		yaxis=dict(range=[0,101], title='%'),
		title='ping_latency_cdf',
		titlefont=dict(size=12),
		legend={'x': 0, 'y': 1},
		height = 300,
		margin = {
		  "r": 20,
		  "t": 30,
		  "b": 30,
		  "l": 50
		},
	)
	graph = dcc.Graph(
		id='ping_cdf',
		animate=False,
		figure={'data': grap_data_list,'layout':grap_layout}
    )
	return graph

def wlm_link_stats_graph(category, graph_name_list, xaxis_title, ext_name, mode):
	xaxis_max = len(wlm_stats_plot_list)
	if xaxis_max == 0:
		return
	grap_data_list = []
	min_yaxis = 100
	max_yaxis = -100
	graph_title = category
	if ext_name != None:
		graph_title = graph_title+':'+ext_name
	for graph_name in graph_name_list:
		y_data = [item[category][graph_name] for item in wlm_stats_plot_list]
		min_yaxis = min(min_yaxis, min(y_data))
		max_yaxis = max(max_yaxis, max(y_data))
		if mode == 'scatter':
			grap_data = plotly.graph_objs.Scatter(
				x=range(0, xaxis_max),
				y=y_data,
				name=graph_name,
				line = dict(
					width = 2,
					)
			)
		elif mode == 'bar':
			grap_data = plotly.graph_objs.Bar(
				x = range(0, xaxis_max),
				y = y_data,
				name = graph_name,
			)
		grap_data_list.append(grap_data)
	min_yaxis = min_yaxis-10
	max_yaxis = max_yaxis+10

	grap_layout = plotly.graph_objs.Layout(
		xaxis=dict(range=[0,xaxis_max]),
		yaxis=dict(range=[min_yaxis,max_yaxis], title=xaxis_title),
		title=graph_title,
		titlefont=dict(size=12),
		legend={'x': 0, 'y': 1},
		height = 300,
		margin = {
		  "r": 20,
		  "t": 30,
		  "b": 30,
		  "l": 50
		},
	)
	graph = dcc.Graph(
		id=graph_title,
		animate=False,
		figure={'data': grap_data_list,'layout':grap_layout}
    )
	return graph

def wlm_ac_stats_graph(graph_name):
	xaxis_max = len(wlm_stats_plot_list)
	if xaxis_max == 0:
		return
	grap_data_list = []
	min_yaxis = 1000000000
	max_yaxis = -1000000000
	graph_title = 'wlm_ac_stats:'+graph_name
	#print graph_name
	for i in xrange(len(id_ac_map)):
		y_data = [item['wlm_ac_stats'][graph_name][i] for item in wlm_stats_plot_list]
		min_yaxis = min(min_yaxis, min(y_data))
		max_yaxis = max(max_yaxis, max(y_data))
		grap_data = plotly.graph_objs.Scatter(
			x=range(0, xaxis_max),
			y=y_data,
			name=id_ac_map[i],
			line = dict(
				width = 2,
				)
		)
		grap_data_list.append(grap_data)
	min_yaxis = min_yaxis-10
	max_yaxis = max_yaxis+10

	grap_layout = plotly.graph_objs.Layout(
		xaxis=dict(range=[0,xaxis_max]),
		yaxis=dict(range=[min_yaxis,max_yaxis]),
		title=graph_title,
		paper_bgcolor="white",
        plot_bgcolor="white",
		titlefont=dict(size=12),
		legend={'x': 0, 'y': 1},
		height = 300,
		margin = {
		  "r": 20,
		  "t": 30,
		  "b": 30,
		  "l": 50
		},
	)
	graph = dcc.Graph(
		id=graph_title,
		animate=False,
		figure={'data': grap_data_list,'layout':grap_layout}
    )
	return graph

csv_columns = ['timestamp','gaming_server','AP','bcn_rssi', 'pwr_on_period', 'scan_period', 'congestion_level', 'retries', 'mpdu_lost', 'rx_ampdu', 'rx_mpdu', 'tx_mpdu', 'tx_ampdu', 'contention_time_avg']
high_latency_columns = []
def update_analysis_result(wlm_stats_result_dict):
	#pass
	print wlm_stats_result_dict
	global wlm_stats_cache_list
	global total_ping_cnt
	global tolal_high_latency_cnt
	total_ping_cnt += 1
	wlm_stats_cache_list.append(wlm_stats_result_dict)

	#save to csv file
	first_write = False
	if not os.path.exists(result_csv_file_name):
		first_write = True
	#print len(wlm_stats_cache_list)
	if len(wlm_stats_cache_list) >= 20:
		with open(result_csv_file_name, 'ab') as csvfile:
			writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
			if first_write:
				writer.writeheader()
			for data in wlm_stats_cache_list:
				writer.writerow(data)
		wlm_stats_cache_list = []

	#ping latency cdf result
	wlm_stats_ping_cdf_dict['gaming_server'].append(wlm_stats_result_dict['gaming_server'])
	wlm_stats_ping_cdf_dict['AP'].append(wlm_stats_result_dict['AP'])
	if len(wlm_stats_ping_cdf_dict['gaming_server']) > 500:
		wlm_stats_ping_cdf_dict['gaming_server'].pop(0)
		wlm_stats_ping_cdf_dict['AP'].pop(0)

	#high latency items
	if wlm_stats_result_dict['gaming_server'] > high_latency_threshold:
		convert_dict = {}
		gen_columns = False
		if len(high_latency_columns) == 0:
			gen_columns = True
		for key in csv_columns:
			if type(wlm_stats_result_dict[key]) is list:
				for i in xrange(len(wlm_stats_result_dict[key])):
					convert_dict[key+id_ac_map[i]] = wlm_stats_result_dict[key][i]
					if gen_columns:
						high_latency_columns.append({"name":[key,id_ac_map[i]], "id":key+id_ac_map[i]})
			else:
				convert_dict[key] = wlm_stats_result_dict[key]
				if gen_columns:
					high_latency_columns.append({"name":["", key], "id":key})
		wlm_stats_high_latency_list.append(convert_dict)
		tolal_high_latency_cnt+=1
		if len(wlm_stats_high_latency_list) > 500:
			wlm_stats_high_latency_list.pop(0)

def restart_test():
	print "restart_test"
	global wlm_stats_plot_list
	global wlm_stats_cache_list
	global wlm_stats_high_latency_list
	global wlm_stats_ping_cdf_dict
	global total_ping_cnt
	global tolal_high_latency_cnt
	wlm_stats_plot_list = []
	wlm_stats_cache_list = []
	wlm_stats_high_latency_list = []
	wlm_stats_ping_cdf_dict['gaming_server'] = []
	wlm_stats_ping_cdf_dict['AP'] = []
	total_ping_cnt = 0
	tolal_high_latency_cnt = 0
	if os.path.exists(result_csv_file_name):
		os.remove(result_csv_file_name)

@app.callback(Output('ping_output', 'children'),
              [Input('gaming_server_input', 'n_submit'), Input('gaming_server_input', 'n_blur'),
               Input('AP_input', 'n_submit'), Input('AP_input', 'n_blur'), Input('wlm_stats_update', 'n_intervals')],
              [State('gaming_server_input', 'value'),
               State('AP_input', 'value')]
			  )
def update_ping_addr_output(ns1, nb1, ns2, nb2,n, input1, input2):
	ping_addr_dict['gaming_server'] = input1
	ping_addr_dict['AP'] = input2
	return '''
		gaming_server address: {},
		and AP address: {}, current time: {}
	'''.format( ping_addr_dict['gaming_server'], ping_addr_dict['AP'], datetime.datetime.now())

@app.callback(Output('test_state_output', 'children'),
              [Input('start_button', 'n_clicks_timestamp'),
               Input('stop_button', 'n_clicks_timestamp'),
               Input('restart_button', 'n_clicks_timestamp')])
def displayClick(btn1, btn2, btn3):
	global current_test_state
	global start_date_time
	if int(btn1) > int(btn2) and int(btn1) > int(btn3):
		if current_test_state != 'start':
			current_test_state = 'start'
			start_date_time = datetime.datetime.now()
	elif int(btn2) > int(btn1) and int(btn2) > int(btn3):
		current_test_state = 'stop'
	elif int(btn3) > int(btn1) and int(btn3) > int(btn2):
		restart_test()
		start_date_time = datetime.datetime.now()
		current_test_state = 'start'
	print current_test_state
	
	return '''
		current test state "{}", start time: {}
	'''.format(current_test_state, start_date_time, )

@app.callback(Output('wlm_stats_update', 'interval'),
              [Input('start_button', 'n_clicks_timestamp'),
               Input('stop_button', 'n_clicks_timestamp'),
               Input('restart_button', 'n_clicks_timestamp')])
def buttonClick(btn1, btn2, btn3):
	if int(btn1) > int(btn2) and int(btn1) > int(btn3):
		return 3000
	elif int(btn2) > int(btn1) and int(btn2) > int(btn3):
		return 300000
	elif int(btn3) > int(btn1) and int(btn3) > int(btn2):
		return 3000
	return 3000

@app.callback(
	Output('wlm_ping_stats_graphs', 'children'),
	[Input('wlm_stats_update', 'n_intervals')]
	)
def update_wlm_ping_stats_graph(n):
	graph_list = []
	global current_test_state
	if len(wlm_stats_plot_list) == 0:
		if os.path.exists(result_csv_file_name):
			os.remove(result_csv_file_name)
	if current_test_state == 'start':
		ping_latency = dict((ip_addr, wlan_dev.get_ping_latency(ping_addr_dict[ip_addr])) for ip_addr in ping_addr_dict.keys())
		link_stats, ac_stats = wlan_dev.get_wlm_stats()
		wlm_stats_plot_list.append({'ping_latency':ping_latency, 'wlm_link_stats':link_stats, 'wlm_ac_stats':ac_stats})
		update_analysis_result(dict(ping_latency.items()+link_stats.items()+ac_stats.items()))

	graph_list.append(html.Div(wlm_link_stats_graph('ping_latency', ['AP', 'gaming_server'], 'ms', None, 'scatter'), className = 'six columns'))
	graph_list.append(html.Div(wlm_ping_cdf_graph(), className = 'six columns'))	
	return graph_list

@app.callback(
	Output('wlm_link_stats_graphs', 'children'),
	[Input('link_checkbox', 'values'),
	 Input('wlm_stats_update', 'n_intervals')]
	)
def update_wlm_link_stats_graph(link_list, n):
	graph_list = []
	#print wlm_stats_cache_list
	if len(wlm_stats_plot_list) > 100:
		wlm_stats_plot_list.pop(0)
	if 'bcn_rssi' in link_list:
		graph_list.append(html.Div(wlm_link_stats_graph('wlm_link_stats', ['bcn_rssi'], 'dbm', 'bcn_rssi', 'scatter'), className = 'row'))
	if 'congestion_level' in link_list:
		graph_list.append(html.Div(wlm_link_stats_graph('wlm_link_stats', ['congestion_level'], '%', 'congestion_level', 'bar'), className = 'row'))
	if 'pwr_on_period' in link_list:
		graph_list.append(html.Div(wlm_link_stats_graph('wlm_link_stats', ['pwr_on_period'], '%', 'pwr_on_period', 'bar'), className = 'row'))
	if 'scan_period' in link_list:
		graph_list.append(html.Div(wlm_link_stats_graph('wlm_link_stats', ['scan_period'], '%', 'scan_period', 'bar'), className = 'row'))
	return graph_list

@app.callback(
	Output('wlm_ac_stats_graphs', 'children'),
	[Input('ac_checkbox', 'values'),
	 Input('wlm_stats_update', 'n_intervals')]
	)
def update_wlm_ac_stats_graph(ac_list, n):
	graph_list = []
	for ac_name in ac_list:
		graph_list.append(html.Div(wlm_ac_stats_graph(ac_name), className = 'row'))
	return graph_list

@app.callback(
	Output('high_latency_threshold_output', 'children'),
	[Input('high_latency_threshold_slider', 'value'),
	 Input('wlm_stats_update', 'n_intervals')]
	)
def update_high_latency_output(threshold, n):
	global high_latency_threshold
	global tolal_high_latency_cnt
	global total_ping_cnt
	if threshold*30 != high_latency_threshold:
		high_latency_threshold = threshold*30
	if total_ping_cnt == 0:
		high_latency_percent = 0
	else:
		high_latency_percent = float(tolal_high_latency_cnt)/total_ping_cnt
		high_latency_percent = high_latency_percent * 100
	return '''
		high latency threshold {}ms, {}% of total ping iterations is higher than threshold
		'''.format(high_latency_threshold, high_latency_percent)
@app.callback(
	Output('wlm_high_latency_dashtable', 'children'),
	[Input('wlm_stats_update', 'n_intervals')]
	)
def update_high_latency_dashtable(n):
	#print high_latency_columns
	if len(wlm_stats_high_latency_list) != 0:
		#print tmp_col
		return dash_table.DataTable(
			id='high_latency_list',
			#columns=csv_columns,
			columns=high_latency_columns,
			data=wlm_stats_high_latency_list,
			merge_duplicate_headers=True,
			style_table={
				'maxHeight': '400',
				'overflowY': 'scroll',
				'border': 'thin lightgrey solid'
			},
			style_cell={'textAlign': 'left'},
			style_cell_conditional=[
				{
					'if': {'column_id': 'Region'},
					'textAlign': 'left'
				}
			] + [
				{
					'if': {'row_index': 'odd'},
					'backgroundColor': 'rgb(248, 248, 248)'
				}
			],
			style_header={
				'backgroundColor': 'white',
				'fontWeight': 'bold'
			}
		)

if __name__ == '__main__':
	#pass
    app.run_server(debug=False,port=8050,host='0.0.0.0')
