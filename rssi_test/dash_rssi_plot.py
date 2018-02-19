import dash
from dash.dependencies import Input, Output, Event
import dash_core_components as dcc
import dash_html_components as html
import plotly
from rssi_plot import wlan_device
import rssi_plot

zipped_rssi_list = dict()
rssi_dict = dict()
app = dash.Dash()
wlan_dev_dict = dict()
wlan_port = list()
wlan_port = rssi_plot.get_wlan_device_list()
print wlan_port

for port in wlan_port:
	wlan_dev_dict[port] = wlan_device(port)
rssi_list = list()
app.layout = html.Div(children=[
    html.H1(children='Dash RSSI monitor'),
	dcc.Dropdown(id='wlan_dev',
		options=[{'label': s, 'value': s} for s in wlan_port],
		value=wlan_port,
		multi=True),
	html.Div(children=html.Div(id='rssi-graphs'), className='row'),
    #dcc.Graph(id='rssi-graph', animate=True),
	dcc.Interval(id='rssi_update', interval=3000),
])

@app.callback(
	Output('rssi-graphs', 'children'),
	[Input('wlan_dev', 'value')],
	events=[Event('rssi_update', 'interval')]
	)
def update_graph(data_names):
	graphs = []
	global rssi_dict
	if len(data_names)>2:
		class_choice = 'col s12 m6 l4'
	elif len(data_names)==2:
		class_choice = 'col s12 m6 l6'
	else:
		class_choice = 'col s12'

	for data_name in data_names:
		wlan_dev = wlan_dev_dict[data_name]
		#if
		tmp_list = wlan_dev.get_rssi()
		if len(tmp_list) != 0:
			rssi_dict.setdefault(data_name, []).append(tmp_list)
		if len(rssi_dict[data_name]) > 60:
			rssi_dict[data_name].pop(0)
		zipped_rssi_list[data_name] = list(zip(*rssi_dict[data_name]))
		xaxis_max = len(list(zipped_rssi_list[data_name][3]))
		cmb_rssi_data = plotly.graph_objs.Scatter(
			x=range(0, xaxis_max),
			y=list(zipped_rssi_list[data_name][3]),
			name='cmb_rssi',
			mode='lines',
			line = dict(
				color = ('rgb(22, 96, 167)'),
				width = 5,
				)
		)
		ch0_rssi_data = plotly.graph_objs.Scatter(
			x=range(0, xaxis_max),
			y=list(zipped_rssi_list[data_name][1]),
			name='ch0_rssi',
			mode='lines',
			line = dict(
				color = ('rgb(205, 12, 24)'),
				width = 2,
				)
		)

		ch1_rssi_data = plotly.graph_objs.Scatter(
			x=range(0, xaxis_max),
			y=list(zipped_rssi_list[data_name][2]),
			name='ch1_rssi',
			mode='lines',

		)
		min_yaxis = min(list(zipped_rssi_list[data_name][1]))
		max_yaxis = max(list(zipped_rssi_list[data_name][1]))
		min_yaxis = min(min_yaxis, min(list(zipped_rssi_list[data_name][2])))
		max_yaxis = max(max_yaxis, max(list(zipped_rssi_list[data_name][2])))
		min_yaxis = min(min_yaxis, min(list(zipped_rssi_list[data_name][3])))
		max_yaxis = max(max_yaxis, max(list(zipped_rssi_list[data_name][3])))
		min_yaxis = min_yaxis-10
		max_yaxis = max_yaxis+10
		print min_yaxis, max_yaxis
		rssi_layout = plotly.graph_objs.Layout(
			xaxis=dict(range=[0,xaxis_max]),
			yaxis=dict(range=[min_yaxis,max_yaxis], title='dbm'),
			title='ch_rssi_'+data_name)
	
		graphs.append(html.Div(dcc.Graph(
            id=data_name,
            animate=True,
            figure={'data': [ch0_rssi_data, ch1_rssi_data, cmb_rssi_data],'layout':rssi_layout}
            ), className=class_choice))
	#return {'data':[ch0_rssi_data, ch1_rssi_data, cmb_rssi_data], 'layout':rssi_layout}
	return graphs
if __name__ == '__main__':
	#pass
    app.run_server(debug=True)