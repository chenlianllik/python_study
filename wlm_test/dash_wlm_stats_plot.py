import dash
from dash.dependencies import Input, Output, Event
import dash_core_components as dcc
import dash_html_components as html
import plotly
from dev_io import wlan_device
import dev_io
import csv
import os

wlm_stats_plot_list = []
wlm_stats_cache_list = []

id_ac_map = ['VO','VI','BE','BK']
ping_addr_dict = {'gaming_server':'49.51.196.180', 'AP':'192.168.1.1'}
result_csv_file_name = "ping_test_result.csv"

app = dash.Dash(__name__)
#color_list = ['rgb(22, 96, 167)', 'rgb(205, 12, 24)']
app.css.append_css({'external_url': 'https://cdn.rawgit.com/plotly/dash-app-stylesheets/2d266c578d2a6e8850ebce48fdb52759b2aef506/stylesheet-oil-and-gas.css'})  # noqa: E501
wlan_dev = wlan_device('sim')
app.layout = html.Div(children=[
    html.H1(children='wlm_stats_monitor', className = 'row'),
	html.Div(children = [
		html.Div(children = [
			html.Div(children = [
				dcc.Checklist(
					id = 'plot_checkbox',
					options=[
						{'label': 'ping_latency', 'value': 'ping_latency'},
						{'label': 'wlm_link_stats', 'value': 'wlm_link_stats'},
					],
					values=['ping_latency', 'wlm_link_stats'],
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
					width = 3,
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
				width = 3,
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

@app.callback(
	Output('wlm_link_stats_graphs', 'children'),
	[Input('plot_checkbox', 'values')],
	events=[Event('wlm_stats_update', 'interval')]
	)
def update_wlm_link_stats_graph(plot_list):
	graph_list = []
	if len(wlm_stats_plot_list) == 0:
		if os.path.exists(result_csv_file_name):
			os.remove(result_csv_file_name)
	ping_latency = dict((ip_addr, wlan_dev.get_ping_latency(ping_addr_dict[ip_addr])) for ip_addr in ping_addr_dict.keys())
	link_stats, ac_stats = wlan_dev.get_wlm_stats()
	wlm_stats_plot_list.append({'ping_latency':ping_latency, 'wlm_link_stats':link_stats, 'wlm_ac_stats':ac_stats})
	update_analysis_result(dict(ping_latency.items()+link_stats.items()+ac_stats.items()))

	#print wlm_stats_cache_list
	if len(wlm_stats_plot_list) > 60:
		wlm_stats_plot_list.pop(0)
	if 'ping_latency' in plot_list:
		graph_list.append(html.Div(wlm_link_stats_graph('ping_latency', ['gaming_server', 'AP'], 'ms', None, 'scatter'), className = 'row'))
	if 'wlm_link_stats' in plot_list:
		graph_list.append(html.Div(wlm_link_stats_graph('wlm_link_stats', ['bcn_rssi'], 'dbm', 'bcn_rssi', 'scatter'), className = 'row'))
		graph_list.append(html.Div(wlm_link_stats_graph('wlm_link_stats', ['pwr_on_period','scan_on_period', 'congestion_level'], '%', 'pwr_scan_on_time', 'bar'), className = 'row'))
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