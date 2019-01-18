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
	html.H1("WLAN ping latency dashboard", style={'textAlign': 'center','color': '#f2f2f2', 'backgroundColor':'#003366'}, className='row'),

	# tabs
	html.Div([
		dcc.Tabs(
			id="wlm_tabs",
			style={"verticalAlign":"middle", "height":'44px', 'borderTop': '1px solid #d6d6d6'},
			children=[
				dcc.Tab(label="wlm_monitor", value="wlm_monitor_tab", selected_style={'fontWeight': 'bold'}, style = {'fontWeight': 'bold'}),
				dcc.Tab(label="wlm_parser", value="wlm_parser_tab", selected_style={'fontWeight': 'bold'}, style = {'fontWeight': 'bold'}),
			],
			value=current_tab,
			colors={
				"border": "#d6d6d6",
				"primary": "blue",
				"background": '#f0f0f5'
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
	wlm_monitor.wlan_dev = wlan_device('sim')
	wlm_monitor.admin_ip = "192.168.1.7"
	wlm_monitor.result_csv_file_name = 'ping_test_result_'+wlm_monitor.wlan_dev.device_port+'.csv'
	
	app.run_server(debug=False,port=8050,host='0.0.0.0')