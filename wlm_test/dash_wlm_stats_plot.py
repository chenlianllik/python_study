import dash
from dash.dependencies import Input, Output, Event, State
import dash_core_components as dcc
import dash_html_components as html
import plotly
from dev_io import wlan_device
import dev_io
import csv
import os
import numpy as np

wlm_stats_plot_list = []
wlm_stats_cache_list = []
wlm_stats_ping_cdf_dict = {
	'gaming_server':[],
	'AP':[]
}

id_ac_map = ['VO','VI','BE','BK']
ping_addr_dict = {'gaming_server':'qualcomm.com', 'AP':'VI-HASTINGS-08'}
result_csv_file_name = "ping_test_result.csv"

app = dash.Dash(__name__)
#color_list = ['rgb(22, 96, 167)', 'rgb(205, 12, 24)']
app.css.append_css({'external_url': 'https://cdn.rawgit.com/plotly/dash-app-stylesheets/2d266c578d2a6e8850ebce48fdb52759b2aef506/stylesheet-oil-and-gas.css'})  # noqa: E501
wlan_dev = wlan_device('sim')
app.layout = html.Div(children=[
    html.H1(children='WLAN ping latency dashboard', className = 'row'),
	html.Div(children = [
		html.H4(children='ping result', className = 'row'),
		html.Div(children = [
			html.Label('set IP addres:'),
			dcc.Input(id='gaming_server_input', type='text', value=ping_addr_dict['gaming_server']),
			dcc.Input(id='AP_input', type='text', value=ping_addr_dict['AP']),
			html.Div(id='ping_output'),
		], className='row'),
		html.Div(children = html.Div(id='wlm_ping_stats_graphs'), className='row'),
	],className = 'row'),
	html.H4(children='wlm stats', className = 'row'),
	html.Div(children = [
		html.Div(children = [
			html.Div(children = [
				dcc.Checklist(
					id = 'link_checkbox',
					options=[
						{'label': 'bcn_rssi', 'value': 'bcn_rssi'},
						{'label': 'pwr_on_period', 'value': 'pwr_on_period'},
						{'label': 'scan_on_period', 'value': 'scan_on_period'},
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
						{'label': 'total_retries', 'value': 'total_retries'},
						{'label': 'mpdu_lost', 'value': 'mpdu_lost'},
						{'label': 'rx_ampdu', 'value': 'rx_ampdu'},
						{'label': 'rx_mpdu', 'value': 'rx_mpdu'},
						{'label': 'tx_mpdu', 'value': 'tx_mpdu'},
						{'label': 'tx_ampdu', 'value': 'tx_ampdu'},
						{'label': 'contention_time_avg', 'value': 'contention_time_avg'},
					],
					values=['total_retries', 'mpdu_lost', 'contention_time_avg'],
					labelStyle={'display': 'inline-block'},
				),
			], className='row'),
			html.Div(children = html.Div(id='wlm_ac_stats_graphs'), className='row'),
		], className='six columns'),
	], className='row'),
    #dcc.Graph(id='rssi-graph', animate=True),
	dcc.Interval(id='wlm_stats_update', interval=2000),
])

def wlm_ping_cdf_graph():
	grap_data_list = []

	for key in wlm_stats_ping_cdf_dict.keys():
		data = wlm_stats_ping_cdf_dict[key]
		hist, bin_edges = np.histogram(data, bins = range(100))
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
		xaxis=dict(range=[0,101]),
		yaxis=dict(range=[0,101], title='%'),
		title='ping_latency_cdf',
		titlefont=dict(size=22),
		legend={'x': 10, 'y': 1}
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
		titlefont=dict(size=22),
		legend={'x': 0, 'y': 1}
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
	print graph_name
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
		titlefont=dict(size=22),
		legend={'x': 0, 'y': 1}
	)
	graph = dcc.Graph(
		id=graph_title,
		animate=False,
		figure={'data': grap_data_list,'layout':grap_layout}
    )
	return graph

csv_columns = ['timestamp','gaming_server','AP','bcn_rssi', 'pwr_on_period', 'scan_on_period', 'congestion_level', 'total_retries', 'mpdu_lost', 'rx_ampdu', 'rx_mpdu', 'tx_mpdu', 'tx_ampdu', 'contention_time_avg']
def update_analysis_result(wlm_stats_result_dict):
	#pass
	global wlm_stats_cache_list
	wlm_stats_cache_list.append(wlm_stats_result_dict)

	#save to csv file
	first_write = False
	if not os.path.exists(result_csv_file_name):
		first_write = True
	print len(wlm_stats_cache_list)
	if len(wlm_stats_cache_list) >= 20:

		with open(result_csv_file_name, 'ab') as csvfile:
			writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
			if first_write:
				writer.writeheader()
			for data in wlm_stats_cache_list:
				writer.writerow(data)
		wlm_stats_cache_list = []

	wlm_stats_ping_cdf_dict['gaming_server'].append(wlm_stats_result_dict['gaming_server'])
	wlm_stats_ping_cdf_dict['AP'].append(wlm_stats_result_dict['AP'])
	if len(wlm_stats_ping_cdf_dict['gaming_server']) > 500:
		wlm_stats_ping_cdf_dict['gaming_server'].pop(0)
		wlm_stats_ping_cdf_dict['AP'].pop(0)

@app.callback(Output('ping_output', 'children'),
              [Input('gaming_server_input', 'n_submit'), Input('gaming_server_input', 'n_blur'),
               Input('AP_input', 'n_submit'), Input('AP_input', 'n_blur')],
              [State('gaming_server_input', 'value'),
               State('AP_input', 'value')],
			   events=[Event('wlm_stats_update', 'interval')]
			  )
def update_output(ns1, nb1, ns2, nb2, input1, input2):
	ping_addr_dict['gaming_server'] = input1
	ping_addr_dict['AP'] = input2
	return '''
		gaming_server IP is "{}",
		and AP IP is "{}"
	'''.format( ping_addr_dict['gaming_server'], ping_addr_dict['AP'])

@app.callback(
	Output('wlm_ping_stats_graphs', 'children'),
	events=[Event('wlm_stats_update', 'interval')]
	)
def update_wlm_ping_stats_graph():
	graph_list = []
	if len(wlm_stats_plot_list) == 0:
		if os.path.exists(result_csv_file_name):
			os.remove(result_csv_file_name)
	ping_latency = dict((ip_addr, wlan_dev.get_ping_latency(ping_addr_dict[ip_addr])) for ip_addr in ping_addr_dict.keys())
	link_stats, ac_stats = wlan_dev.get_wlm_stats()
	wlm_stats_plot_list.append({'ping_latency':ping_latency, 'wlm_link_stats':link_stats, 'wlm_ac_stats':ac_stats})
	update_analysis_result(dict(ping_latency.items()+link_stats.items()+ac_stats.items()))

	graph_list.append(html.Div(wlm_link_stats_graph('ping_latency', ['AP', 'gaming_server'], 'ms', None, 'scatter'), className = 'six columns'))
	graph_list.append(html.Div(wlm_ping_cdf_graph(), className = 'six columns'))
	return graph_list

@app.callback(
	Output('wlm_link_stats_graphs', 'children'),
	[Input('link_checkbox', 'values')],
	events=[Event('wlm_stats_update', 'interval')]
	)
def update_wlm_link_stats_graph(link_list):
	graph_list = []
	#print wlm_stats_cache_list
	if len(wlm_stats_plot_list) > 60:
		wlm_stats_plot_list.pop(0)
	if 'bcn_rssi' in link_list:
		graph_list.append(html.Div(wlm_link_stats_graph('wlm_link_stats', ['bcn_rssi'], 'dbm', 'bcn_rssi', 'scatter'), className = 'row'))
	if 'congestion_level' in link_list:
		graph_list.append(html.Div(wlm_link_stats_graph('wlm_link_stats', ['congestion_level'], '%', 'congestion_level', 'bar'), className = 'row'))
	if 'pwr_on_period' in link_list:
		graph_list.append(html.Div(wlm_link_stats_graph('wlm_link_stats', ['pwr_on_period'], '%', 'pwr_on_period', 'bar'), className = 'row'))
	if 'scan_on_period' in link_list:
		graph_list.append(html.Div(wlm_link_stats_graph('wlm_link_stats', ['scan_on_period'], '%', 'scan_on_period', 'bar'), className = 'row'))
	return graph_list

@app.callback(
	Output('wlm_ac_stats_graphs', 'children'),
	[Input('ac_checkbox', 'values')],
	events=[Event('wlm_stats_update', 'interval')]
	)
def update_wlm_ac_stats_graph(ac_list):
	graph_list = []
	for ac_name in ac_list:
		graph_list.append(html.Div(wlm_ac_stats_graph(ac_name), className = 'row'))
	return graph_list
if __name__ == '__main__':
	#pass
    app.run_server(debug=False,port=8050,host='0.0.0.0')
