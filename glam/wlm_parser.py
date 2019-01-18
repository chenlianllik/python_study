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
from app import *

df = None
max_samples_per_page = 500
current_page = 1
total_pages = 0
column_name_list = []

layout = html.Div(children=[
	html.Div([
		dcc.Upload(
			id='upload_latency_data',
			children=html.Div([
				'Drag and Drop or ',
				html.A('Select Files')
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
	return html.Div(children = [
		html.H5(filename),
		html.Div(children = [
			html.Div(id='plot_top_output',className='four columns'),
			html.Div(children = [
				html.Button('prev', id='prev_button', n_clicks_timestamp='0'),
				dcc.Input(id='current_page_input', type='text', value=str(current_page)),
				html.Button('next', id='next_button', n_clicks_timestamp='0'),
			], className = 'four columns'),	
		], className = 'row')
	])

def parse_contents(contents, filename, date):
	global df
	global total_pages
	global current_page
	div_list = []
	content_type, content_string = contents.split(',')
	decoded = base64.b64decode(content_string)
	try:
		if 'csv' in filename:
			# Assume that the user uploaded a CSV file
			df = pd.read_csv(
				io.StringIO(decoded.decode('utf-8')))
	except Exception as e:
		print(e)
		return html.Div([
			'There was an error processing this file.'
		])

	total_pages = df.shape[0]/max_samples_per_page
	current_page = 1
	print total_pages
	column_name_list = df.columns.tolist()
	print column_name_list
	div_list.append(generate_wlm_plot_top_components(filename))
	div_list.append(generate_wlm_plot_graph_comonentes())
	return html.Div(div_list)

def wlm_plot_graph(plot_name, graph_name_list, xaxis_title, mode):
	global df
	global current_page
	global max_samples_per_page
	xaxis_max = max_samples_per_page
	page_start_index = (current_page - 1)*max_samples_per_page
	grap_data_list = []
	min_yaxis = 100
	max_yaxis = -100
	graph_title = plot_name
	print "wlm_plot_graph current_page:{}".format(current_page)
	for graph_name in graph_name_list:
		#y_data = df[graph_name][page_start_index : page_start_index+max_samples_per_page]
		y_data = df.loc[page_start_index : page_start_index+max_samples_per_page, graph_name].tolist()
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

@app.callback(Output('plot_latency_data', 'children'),
              [Input('upload_latency_data', 'contents')],
              [State('upload_latency_data', 'filename'),
               State('upload_latency_data', 'last_modified')])
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children

@app.callback(Output('plot_top_output', 'children'),
              [Input('prev_button', 'n_clicks_timestamp'),
               Input('next_button', 'n_clicks_timestamp')])
def display_plot_output(btn1, btn2):
	global total_pages
	global max_samples_per_page
	global current_page
	print "display_plot_output"
	if int(btn1) > int(btn2):
		if current_page > 1:
			current_page -= 1
	elif int(btn2) > int(btn1):
		if current_page < total_pages:
			current_page += 1
	print "display_plot_output current_page:{}".format(current_page)
	return '''
		total pages:{}, {} samples/page, current page:{}
	'''.format(total_pages, max_samples_per_page, current_page)

@app.callback(
	Output('wlm_plot_graph_graphs', 'children'),
	[Input('plot_top_output', 'children')]
	)
def update_wlm_plot_graph(top_output):
	graph_list = []
	graph_list.append(html.Div(wlm_plot_graph('ping_latency', ['AP', 'gaming_server'], 'ms',  'scatter'), className = 'twelve columns'))
	return graph_list