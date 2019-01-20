import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
from dev_io import wlan_device
import os
import sys
import wlm_monitor
import wlm_parser 
from app import *

current_tab = "wlm_monitor_tab"
app.css.append_css({'external_url': 'https://cdn.rawgit.com/plotly/dash-app-stylesheets/2d266c578d2a6e8850ebce48fdb52759b2aef506/stylesheet-oil-and-gas.css'})  # noqa: E501

app.layout =html.Div([
        # header
	html.H1("Gaming LAtency Measurement platform", style={'textAlign': 'center','color': '#f2f2f2', 'backgroundColor':'#003366'}, className='row'),

	# tabs
	html.Div([
		dcc.Tabs(
			id="wlm_tabs",
			style={"verticalAlign":"middle", "height":'48px', 'borderTop': '1px solid #808080'},
			children=[
				dcc.Tab(label="latency monitor", value="wlm_monitor_tab", selected_style={'fontWeight': 'bold', 'backgroundColor': '#f0f0f5'}, style = {'fontWeight': 'bold'}),
				dcc.Tab(label="latency parser", value="wlm_parser_tab", selected_style={'fontWeight': 'bold', 'backgroundColor': '#f0f0f5'}, style = {'fontWeight': 'bold'}),
			],
			value=current_tab,
			colors={
				"border": "#566573",
				"primary": "blue",
				"background": "#C0C0C0"
			}
		)],
		className="row tabs_div"
		),
   
	# Tab content
	html.Div(id="wlm_tab_content", className="row"),
], style={'backgroundColor':'#f0f0f5'})


@app.callback(Output("wlm_tab_content", "children"), [Input("wlm_tabs", "value")])
def render_content(tab):
    if tab == "wlm_monitor_tab":
        return wlm_monitor.layout
    elif tab == "wlm_parser_tab":
        return wlm_parser.layout
    else:
        return wlm_monitor.layout

if __name__ == "__main__":
	print "start app"
	wlm_monitor.wlan_dev = wlan_device(sys.argv[1])
	if wlm_monitor.wlan_dev.device_port == None:
		wlm_monitor.wlan_dev = wlan_device('sim')
	wlm_monitor.wlan_dev.prepare_wlm_stats()
	wlm_monitor.wlan_dev.set_wlm_latency_mode('normal')
	wlm_monitor.admin_ip = sys.argv[3]
	wlm_monitor.result_csv_file_name = 'ping_test_result_'+wlm_monitor.wlan_dev.device_port+'.csv'
	if wlm_monitor.check_admin_ip_alive(wlm_monitor.admin_ip):
		app.run_server(debug=False,port=int(sys.argv[2]),host='0.0.0.0')