import dash
from dash.dependencies import Input, Output, Event, State
import dash_core_components as dcc
import dash_html_components as html
from app import *

layout = html.Div(children=[
	html.H1("WLAN ping latency parser"),
])
