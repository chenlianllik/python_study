import dash
from dash.dependencies import Input, Output, Event
import dash_core_components as dcc
import dash_html_components as html
import plotly
from dev_io import wlan_device
import dev_io

wlm_stats_list = []
app = dash.Dash(__name__)
#color_list = ['rgb(22, 96, 167)', 'rgb(205, 12, 24)']

wlan_dev = wlan_device('sim')
app.layout = html.Div(children=[
    html.H1(children='wlm_stats_monitor'),
	html.Div(children=html.Div(id='wlm_stats_graphs'), className='row'),
    #dcc.Graph(id='rssi-graph', animate=True),
	dcc.Interval(id='wlm_stats_update', interval=3000),
], className='column')

def wlm_stats_graph(category, graph_name_list, xaxis_title, ext_name, mode):
	xaxis_max = len(wlm_stats_list)
	grap_data_list = []
	min_yaxis = 100
	max_yaxis = -100
	graph_title = category
	if ext_name != None:
		graph_title = graph_title+':'+ext_name
	for graph_name in graph_name_list:
		y_data = [item[category][graph_name] for item in wlm_stats_list]
		min_yaxis = min(min_yaxis, min(y_data))
		max_yaxis = max(max_yaxis, max(y_data))
		if mode == 'scatter':
			grap_data = plotly.graph_objs.Scatter(
				x=range(0, xaxis_max),
				y=y_data,
				name=graph_name,
				mode='lines',
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
	print min_yaxis, max_yaxis

	grap_layout = plotly.graph_objs.Layout(
		xaxis=dict(range=[0,xaxis_max]),
		yaxis=dict(range=[min_yaxis,max_yaxis], title=xaxis_title),
		title=graph_title,
		titlefont=dict(size=22)
	)
	graph = dcc.Graph(
            id=graph_title,
            animate=True,
            figure={'data': grap_data_list,'layout':grap_layout}
            )
	return graph

@app.callback(
	Output('wlm_stats_graphs', 'children'),
	events=[Event('wlm_stats_update', 'interval')]
	)
def update_graph():
	graph_list = []

	ping_addr_list = ['google.com', 'qualcomm.com']
	ping_latency = dict((ip_addr, wlan_dev.get_ping_latency(ip_addr)) for ip_addr in ping_addr_list)
	wlm_stats_list.append({'ping_latency':ping_latency, 'wlm_stats':wlan_dev.get_wlm_stats()})
	if len(wlm_stats_list) > 20:
		wlm_stats_list.pop(0)

	graph_list.append(html.Div(wlm_stats_graph('ping_latency', ping_addr_list, 'ms', None, 'scatter')))
	graph_list.append(html.Div(wlm_stats_graph('wlm_stats', ['bcn_rssi'], 'dbm', 'bcn_rssi', 'scatter')))
	graph_list.append(html.Div(wlm_stats_graph('wlm_stats', ['pwr_on_period', 'scan_on_period'], '%', 'pwr_scan_on_time', 'bar')))
	return graph_list
if __name__ == '__main__':
	#pass
    app.run_server(debug=False,port=8050,host='0.0.0.0')