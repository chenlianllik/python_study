import base64
import datetime
import io

import dash
from dash.dependencies import Input, Output, Event, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import plotly
import pandas as pd
import numpy as np
from app import *
from collections import OrderedDict

import wlm_monitor

df = None
max_samples_per_page = 500
samples_last_page = 0
current_filtered_page_index = 1
current_page = 1
total_pages = 0
column_name_list = []
high_latency_threshold = 0
filtered_page_list = []
last_btn_timestamp = 0
connection_info = ''

div_border_style = {'borderStyle': 'dashed', 'borderWidth': '1px', "border-color":"#d6d6d6" }
summary_div_border_style = {'borderStyle': 'dashed', 'borderWidth': '2px'}
layout = html.Div(children=[
	html.Div([
		dcc.Upload(
			id='upload_latency_data',
			children=html.Div([
				'Drag and Drop or ',
				html.A('Select File')
			]),
			style={
				'width': '100%',
				'height': '60px',
				'lineHeight': '60px',
				'borderWidth': '1px',
				'borderStyle': 'dashed',
				'borderRadius': '5px',
				'textAlign': 'center',
				'margin': '10px'
			},
			# Allow multiple files to be uploaded
			multiple=True
		),
		html.Div(id='plot_latency_data'),
	])
])

def generate_wlm_plot_graph_comonentes():
	return html.Div(children = html.Div(id='wlm_plot_graph_graphs'), className='row')

def generate_wlm_plot_top_components(filename):
	global column_name_list
	global total_pages
	global max_samples_per_page
	global df
	
	def get_total_ac_stats_str(stats_name):
		ac_str_list = df.loc[:, stats_name].tolist()
		ac_int_list = list(zip(*[map(int, item[1:-1].split(', ')) for item in ac_str_list]))
		return [sum(list(item)) for item in ac_int_list]

	total_tx_mpdu = get_total_ac_stats_str('tx_mpdu')
	print total_tx_mpdu
	total_rx_mpdu = get_total_ac_stats_str('rx_mpdu')
	total_retries = get_total_ac_stats_str('retries')
	summary_output_str = '''
		file_name:"{}", total_samples:"{}", total_pages:"{}",
		connection_info:"{}",
		ac_result[VO,VI,BE,BK]: tx_mpdu:"{}", rx_mpdu:"{}", tx_retries:"{}",
		avg_scan_period:"{}%", avg_pwr_on_period:"{}%" avg_rssi:"{}dbm"
		'''.format(filename, df.shape[0], total_pages, \
		connection_info, \
		total_tx_mpdu, total_rx_mpdu, total_retries, \
		df['scan_period'].mean(), df['pwr_on_period'].mean(), df['bcn_rssi'].mean())
	return html.Div(children = [
		html.Div([
			html.Label(summary_output_str, className = 'six columns'),
			html.Div([
				wlm_parser_plot_ping_cdf_graph(['AP', 'gaming_server'])
			],className = 'six columns')
		], className = "row", style = summary_div_border_style),
		html.Div([
			html.Div([
				html.Div(children = [
					html.Label('select page:', className = 'six columns'),
				], className = 'row'),
				html.Div(children = [
					html.Button('prev', id='prev_button', n_clicks_timestamp='0', className = 'three columns'),
					html.Button('next', id='next_button', n_clicks_timestamp='0', className = 'three columns'),
				], className = 'row'),
				html.Div(children = [
					html.Div(id='current_page_output', className = 'twelve columns'),
				], className = 'row')
			], className = 'six columns', style = div_border_style),
			html.Div([
				html.Div(children = [
					html.Label('high latency filter:', className = 'six columns'),
				], className = 'row'),
				html.Div(children = [
					dcc.Input(id='high_latency_filter_input', type='text', value=str(high_latency_threshold)),
				],className='row'),
				html.Div(children = [
					html.Div(id='high_latency_filter_output', className = 'twelve columns'),
				], className = 'row')
			], className = 'six columns', style = div_border_style)
		], className = 'row'),
		html.Div(children = [
			dcc.Checklist(
				id = 'plot_checkbox',
				options=[
					{'label':mode,'value':mode} for mode in column_name_list
				],
				values=['bcn_rssi', 'congestion_level', 'pwr_on_period', 'scan_period', 'phy_err', 'retries', 'tx_mpdu', 'contention_time_avg'],
				labelStyle={'display': 'inline-block'},
			),
		], className='row')
	])

def calc_high_latency_page_list(thres):
	global df
	global filtered_page_list
	global max_samples_per_page
	global current_filtered_page_index
	high_latency_index = df.index[(df['AP'] > thres) | (df['gaming_server'] > thres)].tolist()
	filtered_page_list = list(OrderedDict.fromkeys([(i/max_samples_per_page)+1 for i in high_latency_index]))
	print filtered_page_list
	current_filtered_page_index = 0
	
	
def parse_contents(contents, filename, date):
	global df
	global total_pages
	global current_page
	global column_name_list
	global samples_last_page
	global high_latency_threshold
	global filtered_page_list
	global connection_info

	div_list = []
	content_type, content_string = contents.split(',')
	decoded = base64.b64decode(content_string)
	print filename
	if 'csv' in filename:
		# Assume that the user uploaded a CSV file
		# don't know how to solve \n issue with pandas to read first line in csv
		io.StringIO(decoded.decode('utf-8'))
		with open(filename) as f:
			connection_info = f.readline()
		print connection_info
		df = pd.read_csv((filename), header=1)
	else:
		return html.Div([
			'Please select a csv file'
		])

	current_page = 1
	total_pages, samples_last_page = df.shape[0]/max_samples_per_page, df.shape[0]%max_samples_per_page
	if samples_last_page > 0:
		total_pages += 1
	column_name_list = df.columns.tolist()
	if "gaming_server" not in column_name_list:
		return html.Div([
			'Not a glam log file'
		])
	column_name_list.remove("AP")
	column_name_list.remove("gaming_server")
	column_name_list.remove("timestamp")
	print column_name_list
	calc_high_latency_page_list(high_latency_threshold)
	div_list.append(generate_wlm_plot_top_components(filename))
	div_list.append(generate_wlm_plot_graph_comonentes())
	return html.Div(div_list)

def wlm_parser_plot_ping_cdf_graph(graph_name_list):
	global df
	grap_data_list = []
	max_axis = 0
	for item in graph_name_list:
		max_axis = max(df[item].max(), max_axis)
	max_axis = int(max_axis) + 50
	for item in graph_name_list:
		data = df[item].tolist()
		hist, bin_edges = np.histogram(data, bins = range(max_axis))
		#print hist
		cdf = np.cumsum(hist)
		grap_data = plotly.graph_objs.Scatter(
			x=bin_edges[1:],
			y=cdf*100/len(data),
			name=item,
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
		height = 250,
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

def wlm_parser_plot_ac_graph(graph_name):
	global df
	global current_page
	global max_samples_per_page
	global samples_last_page
	global total_pages
	xaxis_max = max_samples_per_page
	if current_page == total_pages and samples_last_page != 0:
		xaxis_max = min(xaxis_max, samples_last_page)
	page_start_index = (current_page - 1)*max_samples_per_page
	grap_data_list = []
	min_yaxis = 1000000000
	max_yaxis = -1000000000
	graph_title = graph_name
	#print graph_name
	print "wlm_parser_plot_ac_graph:{} current_page:{}".format(graph_name, current_page)
	ac_str_list = df.loc[page_start_index : page_start_index+xaxis_max, graph_name].tolist()
	ac_zip_list = list(zip(*[map(int, item[1:-1].split(', ')) for item in ac_str_list]))
	for i in xrange(len(wlm_monitor.id_ac_map)):
		y_data = ac_zip_list[i]
		min_yaxis = min(min_yaxis, min(y_data))
		max_yaxis = max(max_yaxis, max(y_data))
		grap_data = plotly.graph_objs.Scatter(
			x=range(0, xaxis_max),
			y=y_data,
			name=wlm_monitor.id_ac_map[i],
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
		titlefont=dict(size=12),
		legend={'x': 0, 'y': 1},
		height = 300,
		margin = {
		  "r": 20,
		  "t": 30,
		  "b": 30,
		  "l": 50
		},
		plot_bgcolor = '#f0f0f5',
	)
	graph = dcc.Graph(
		id=graph_title,
		animate=False,
		figure={'data': grap_data_list,'layout':grap_layout}
    )
	return graph

def wlm_parser_plot_generic_graph(plot_name, graph_name_list, xaxis_title, mode):
	global df
	global current_page
	global max_samples_per_page
	global samples_last_page
	global total_pages
	xaxis_max = max_samples_per_page
	if current_page == total_pages and samples_last_page != 0:
		xaxis_max = min(xaxis_max, samples_last_page)
	page_start_index = (current_page - 1)*max_samples_per_page
	grap_data_list = []
	min_yaxis = 100
	max_yaxis = -100
	graph_title = plot_name
	print "wlm_parser_plot_generic_graph:{} current_page:{}".format(plot_name, current_page)
	for graph_name in graph_name_list:
		y_data = df.loc[page_start_index : page_start_index+xaxis_max, graph_name].tolist()
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
		plot_bgcolor = '#f0f0f5',
	)
	graph = dcc.Graph(
		id=graph_title,
		animate=False,
		figure={'data': grap_data_list,'layout':grap_layout}
    )
	return graph

@app.callback(Output('plot_latency_data', 'children'),
              [Input('upload_latency_data', 'contents')],
              [State('upload_latency_data', 'filename'),
               State('upload_latency_data', 'last_modified')])
def update_output(list_of_contents, list_of_names, list_of_dates):
	if wlm_monitor.is_addmin_access():
		if list_of_contents is not None:
			children = [
				parse_contents(c, n, d) for c, n, d in
				zip(list_of_contents, list_of_names, list_of_dates)]
			return children

@app.callback(Output('high_latency_filter_output', 'children'),
              [Input('high_latency_filter_input', 'value')])
def update_high_latency_filter_output(thres):
	global high_latency_threshold
	global filtered_page_list
	if int(thres) != high_latency_threshold:
		high_latency_threshold = int(thres)
		calc_high_latency_page_list(high_latency_threshold)
	return '''
		threshold:"{}"ms, "{}" pages have high latency samples
	'''.format(high_latency_threshold, len(filtered_page_list))

@app.callback(Output('current_page_output', 'children'),
              [Input('prev_button', 'n_clicks_timestamp'),
               Input('next_button', 'n_clicks_timestamp'),
			   Input('high_latency_filter_output', 'children')])
def display_cur_page_output(btn1, btn2, filter):
	global total_pages
	global current_page
	global current_filtered_page_index
	global filtered_page_list
	global last_btn_timestamp
	
	if int(btn1) > int(btn2) and last_btn_timestamp != int(btn1):
		if current_filtered_page_index > 0:
			current_filtered_page_index -= 1
		last_btn_timestamp = int(btn1)
			
	elif int(btn2) > int(btn1) and last_btn_timestamp != int(btn2):
		current_filtered_page_index += 1
		if current_filtered_page_index == len(filtered_page_list):
			current_filtered_page_index = 0
		last_btn_timestamp = int(btn2)
	#print filtered_page_list
	if len(filtered_page_list) != 0:
		current_page = filtered_page_list[current_filtered_page_index]
	print "display_cur_page_output current_page:{}".format(current_page)
	return '''
		current page:"{}"
	'''.format(current_page)

@app.callback(
	Output('wlm_plot_graph_graphs', 'children'),
	[Input('current_page_output', 'children'),
	Input('plot_checkbox', 'values')]
	)
def update_wlm_plot_graph(top_output, plot_list):
	global column_name_list
	graph_list = []
	graph_list.append(html.Hr())
	graph_list.append(html.Div(wlm_parser_plot_generic_graph('ping_latency', ['AP', 'gaming_server'], 'ms',  'scatter'), style = div_border_style, className = 'twelve columns'))
	# easter egg
	if len(filtered_page_list) == 0:
		return html.Div([
            html.Img(src='http://orig00.deviantart.net/4caa/f/2013/012/1/c/teemo_business_card_by_dasqui-d5r9mbn.png', height='279', width='500')
        ], className="ten columns padded"),
	check_box_plot_name_list = [str(r) for r in plot_list]
	plot_to_show = list(set(column_name_list) & set(check_box_plot_name_list))
	if 'bcn_rssi' in plot_to_show:
		graph_list.append(html.Div(wlm_parser_plot_generic_graph('bcn_rssi', ['bcn_rssi'], 'dbm',  'scatter'), style = div_border_style, className = 'twelve columns'))
	if 'congestion_level' in plot_to_show:
		graph_list.append(html.Div(wlm_parser_plot_generic_graph('congestion_level', ['congestion_level'], '%',  'bar'), style = div_border_style, className = 'twelve columns'))
	if 'pwr_on_period' in plot_to_show:
		graph_list.append(html.Div(wlm_parser_plot_generic_graph('pwr_on_period', ['pwr_on_period'], '%',  'bar'), style = div_border_style, className = 'twelve columns'))
	if 'scan_period' in plot_to_show:
		graph_list.append(html.Div(wlm_parser_plot_generic_graph('scan_period', ['scan_period'], '%',  'bar'), style = div_border_style, className = 'twelve columns'))
	if 'phy_err' in plot_to_show:
		graph_list.append(html.Div(wlm_parser_plot_generic_graph('phy_err', ['phy_err'], ' ',  'bar'), style = div_border_style, className = 'twelve columns'))
	if 'last_tx_rate' in plot_to_show:
		graph_list.append(html.Div(wlm_parser_plot_generic_graph('last_tx_rate', ['last_tx_rate'], 'Mbps',  'scatter'), style = div_border_style, className = 'twelve columns'))
	if 'retries' in plot_to_show:
		graph_list.append(html.Div(wlm_parser_plot_ac_graph('retries'), style = div_border_style, className = 'twelve columns'))
	if 'rx_mpdu' in plot_to_show:
		graph_list.append(html.Div(wlm_parser_plot_ac_graph('rx_mpdu'), style = div_border_style, className = 'twelve columns'))
	if 'tx_mpdu' in plot_to_show:
		graph_list.append(html.Div(wlm_parser_plot_ac_graph('tx_mpdu'), style = div_border_style, className = 'twelve columns'))
	if 'contention_time_avg' in plot_to_show:
		graph_list.append(html.Div(wlm_parser_plot_ac_graph('contention_time_avg'), style = div_border_style, className = 'twelve columns'))
	return graph_list