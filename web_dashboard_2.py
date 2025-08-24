# save as web_dash_final_multipage.py

"""
A professional, real-time, multi-page sensor data visualization dashboard using Plotly Dash.

This application provides a main dashboard overview and dedicated, full-screen pages for each
of four sensors. It allows users to start/stop logging, customize graph appearance, and export data.

Key enhancements in this version:
- Multi-Page Navigation: Uses dcc.Location to create a true multi-page app with a main
  dashboard and four individual, full-screen sensor detail pages.
- True Live Zoom/Pan: On detail pages, users can zoom and pan while the data continues to
  stream live, without resetting the view, by using the 'extendData' property.
- Full-Featured UI Restored: All components, including the detailed settings modal on the
  dashboard, status indicators, and export functionality, are fully implemented.
- Independent Page Controls: The main dashboard and each detail page have their own
  independent sets of graph controls for tailored visualizations.
- Complete & Organized Code: A comprehensive and well-structured codebase that combines all
  previously developed features into a cohesive, powerful application.
"""

import datetime as dt
import random
from collections import deque
from itertools import islice

import dash
import pandas as pd
import plotly.graph_objs as go
from dash import dcc, html, Input, Output, State, no_update

# ---------- Constants & Configuration ----------
APP_TITLE = "Live Sensor Dashboard"
UPDATE_INTERVAL_MS = 500
MAX_BUFFER_SIZE = 10000
DEFAULT_DISPLAY_POINTS_DASH = 100
DEFAULT_DISPLAY_POINTS_DETAIL = 500

GRAPH_CONFIG = {'displayModeBar': True, 'responsive': True}

# --- IDs for Multi-Page Structure ---
ID_URL = 'url'
ID_PAGE_CONTENT = 'page-content'
ID_NAV_HEADER = 'nav-header'

# --- IDs for Global Controls & Stores ---
ID_RUNNING_STORE = "running-store"
ID_INTERVAL = "interval-component"
ID_DOWNLOAD_DATA = "download-data"
ID_BTN_TOGGLE_LOG = "btn-toggle-log" # Lives on dashboard, but controls global state

# --- IDs for Dashboard Page ---
ID_BTN_EXPORT = "btn-export"
ID_BTN_SETTINGS = "btn-settings"
ID_BTN_CLOSE_MODAL = "btn-close-modal"
ID_STATUS_DIV = "status-div"
ID_MODAL_CONTAINER = "modal-container"
ID_DASH_SETTINGS_STORE = "dashboard-settings-store"
ID_DASH_DISPLAY_POINTS_SLIDER = "dash-display-points-slider"
ID_DASH_LINE_SHAPE_RADIO = "dash-line-shape-radio"
ID_DASH_SHOW_MARKERS_RADIO = "dash-show-markers-radio"
ID_DASH_MARKER_SIZE_SLIDER = "dash-marker-size-slider"
ID_DASH_SETTINGS_NOTE = "dash-settings-note"

# --- IDs for Detail Pages ---
ID_DETAIL_GRAPH = 'detail-graph'
ID_DETAIL_SETTINGS_STORE = 'detail-settings-store'
ID_DETAIL_CONTROLS_WRAPPER = 'detail-controls-wrapper'
ID_DETAIL_DISPLAY_POINTS_SLIDER = "detail-display-points-slider"
ID_DETAIL_LINE_SHAPE_RADIO = "detail-line-shape-radio"
ID_DETAIL_SHOW_MARKERS_RADIO = "detail-show-markers-radio"
ID_DETAIL_MARKER_SIZE_SLIDER = "detail-marker-size-slider"
ID_DETAIL_MARKER_SIZE_WRAPPER = 'detail-marker-size-wrapper'

# ---------- App Initialization ----------
external_stylesheets = ['https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
app.title = APP_TITLE

app.index_string = """<!DOCTYPE html>
<html>
<head>
    {%metas%}
    <title>{%title%}</title>
    {%favicon%}
    {%css%}
    <style>
        :root {
            --font-family-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            --bg-color: #111827; --panel-color: #1F2937; --border-color: #374151;
            --text-color: #F9FAFB; --text-muted-color: #9CA3AF; --accent-color: #3B82F6;
            --success-color: #22C55E; --danger-color: #EF4444; --warning-color: #F59E0B;
            --border-radius: 8px;
        }
        body { margin: 0; background-color: var(--bg-color); color: var(--text-color); font-family: var(--font-family-sans); overflow: hidden; }
        .header { padding: 1rem 1.5rem; background-color: var(--panel-color); border-bottom: 1px solid var(--border-color); display: flex; align-items: center; justify-content: space-between; }
        .header-title-section { display: flex; align-items: center; }
        .header-title { font-size: 1.5rem; margin: 0; font-weight: 600; }
        .header-icon { font-size: 1.75rem; margin-right: 0.75rem; color: var(--accent-color); }
        .nav-header { display: flex; gap: 0.5rem; }
        .nav-link { color: var(--text-muted-color); text-decoration: none; padding: 0.5rem 1rem; border-radius: 6px; font-weight: 500; transition: all 0.2s ease; }
        .nav-link:hover { background-color: var(--border-color); color: var(--text-color); }
        .nav-link.active { background-color: var(--accent-color); color: white; font-weight: 600; }
        .container { display: flex; height: calc(100vh - 65px); }
        .sidebar { width: 280px; padding: 1.5rem; box-sizing: border-box; border-right: 1px solid var(--border-color); display: flex; flex-direction: column; gap: 1.5rem; }
        .main-content { flex: 1; padding: 1.5rem; box-sizing: border-box; overflow-y: auto; }
        .control-panel, .status-panel { background-color: var(--panel-color); border-radius: var(--border-radius); padding: 1rem; border: 1px solid var(--border-color); }
        .panel-title { margin-top: 0; margin-bottom: 1rem; font-size: 1.1rem; font-weight: 600; }
        .control-btn { display: flex; align-items: center; justify-content: center; gap: 0.5rem; width: 100%; padding: 0.75rem; margin-bottom: 0.75rem; border-radius: 6px; border: 1px solid transparent; font-weight: 600; font-size: 1rem; cursor: pointer; transition: all 0.2s ease-in-out; }
        .control-btn:last-child { margin-bottom: 0; }
        .btn-secondary { background-color: var(--border-color); color: var(--text-color); }
        .btn-secondary:hover { background-color: #4B5563; }
        .btn-success { background-color: var(--success-color); color: white; }
        .btn-danger { background-color: var(--danger-color); color: white; }
        .status-indicator { padding: 1rem; font-weight: 700; text-align: center; border-radius: 6px; transition: all 0.3s ease; }
        .graph-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
        .detail-page-container { padding: 1.5rem; display: flex; flex-direction: column; height: calc(100vh - 65px); box-sizing: border-box; }
        .detail-page-header { margin-bottom: 1rem; }
        .detail-page-title { margin: 0; font-size: 1.75rem; }
        .detail-graph-container { flex-grow: 1; min-height: 0; }
        .detail-controls-panel { flex-shrink: 0; background-color: var(--panel-color); border: 1px solid var(--border-color); border-radius: var(--border-radius); padding: 1rem 1.5rem; margin-top: 1.5rem; display: flex; gap: 2rem; align-items: center; flex-wrap: wrap; }
        .settings-row { display: grid; grid-template-columns: 120px 1fr; gap: 1rem; align-items: center; }
        .settings-label { color: var(--text-muted-color); font-size: 0.9rem; font-weight: 500; text-align: right; }
        .modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.7); z-index: 1000; display: flex; justify-content: center; align-items: center; }
        .modal-content { position: relative; background-color: var(--panel-color); border-radius: var(--border-radius); border: 1px solid var(--border-color); padding: 1.5rem 2rem 2rem 2rem; width: 90%; max-width: 600px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
        .modal-header { padding-bottom: 1rem; margin-bottom: 1.5rem; border-bottom: 1px solid var(--border-color); }
        .modal-title { margin: 0; font-size: 1.25rem; }
        .modal-close-btn { position: absolute; top: 0.75rem; right: 1rem; background: none; border: none; color: var(--text-muted-color); font-size: 1.75rem; cursor: pointer; }
    </style>
</head>
<body><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap">{%app_entry%}<footer>{%config%}{%scripts%}{%renderer%}</footer></body></html>"""

# ---------- Data Buffers (Server-Side - Single Source of Truth) ----------
time_data = deque(maxlen=MAX_BUFFER_SIZE)
sensor_data = {
    f's{i}': deque(maxlen=MAX_BUFFER_SIZE) for i in range(1, 5)
}

# ---------- Helper Functions ----------
def get_current_time(): return dt.datetime.now()

def generate_new_data():
    time_data.append(get_current_time())
    for name, buffer in sensor_data.items():
        last_val = buffer[-1] if buffer else 50.0
        new_val = last_val + random.uniform(-2.5, 2.5) - (last_val - 50) * 0.1
        sensor_data[name].append(max(0, min(120, new_val)))

def create_base_figure(title_text="", height=360):
    fig = go.Figure()
    fig.update_layout(
        title={'text': title_text, 'x': 0.05, 'xanchor': 'left', 'font': {'size': 18}},
        template="plotly_dark", plot_bgcolor='#1F2937', paper_bgcolor='#1F2937',
        font=dict(color='#F9FAFB'), margin=dict(l=40, r=20, t=50, b=40), height=height,
        xaxis=dict(gridcolor='rgba(255,255,255,0.1)'), yaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
    )
    return fig

def create_settings_row(label, control):
    return html.Div([html.Label(label, className='settings-label'), control], className='settings-row')

# ---------- Page Layout Generation Functions ----------

def create_navigation_header():
    return html.Header(className='header', children=[
        html.Div(className='header-title-section', children=[
            html.I(className='fa-solid fa-satellite-dish header-icon'),
            html.H1('Live Sensor Dashboard', className='header-title')
        ]),
        html.Nav(id=ID_NAV_HEADER, className='nav-header')
    ])

def create_layout_dashboard():
    return html.Div(className='container', children=[
        html.Aside(className='sidebar', children=[
            html.Div(className='control-panel', children=[
                html.H2("Controls", className='panel-title'),
                html.Button(id=ID_BTN_TOGGLE_LOG, n_clicks=0, className='control-btn'),
                html.Button([html.I(className='fa-solid fa-cog'), " Settings"], id=ID_BTN_SETTINGS, className='control-btn btn-secondary'),
                html.Button([html.I(className='fa-solid fa-download'), " Export Data"], id=ID_BTN_EXPORT, className='control-btn btn-secondary'),
            ]),
            html.Div(className='status-panel', children=[
                html.H2("Status", className='panel-title'),
                html.Div(id=ID_STATUS_DIV, className='status-indicator'),
            ]),
        ]),
        html.Main(className='main-content', children=[
            html.Div(className='graph-grid', children=[
                dcc.Graph(id=f'sensor{i}-graph', config=GRAPH_CONFIG) for i in range(1, 5)
            ]),
        ]),
        html.Div(id=ID_MODAL_CONTAINER, className='modal-overlay', style={'display': 'none'}, children=[
            html.Div(className='modal-content', children=[
                html.Div(className='modal-header', children=[
                    html.H3('Dashboard Graph Settings', className='modal-title'),
                    html.Button('×', id=ID_BTN_CLOSE_MODAL, className='modal-close-btn'),
                ]),
                create_settings_row('Display Points', dcc.Slider(id=ID_DASH_DISPLAY_POINTS_SLIDER, min=10, max=500, step=10, value=DEFAULT_DISPLAY_POINTS_DASH)),
                create_settings_row('Line Shape', dcc.RadioItems(id=ID_DASH_LINE_SHAPE_RADIO, options=[{'label': 'Linear', 'value': 'linear'}, {'label': 'Spline', 'value': 'spline'}], value='linear', labelStyle={'marginRight': '12px'})),
                create_settings_row('Show Markers', dcc.RadioItems(id=ID_DASH_SHOW_MARKERS_RADIO, options=[{'label': 'Off', 'value': 'off'}, {'label': 'On', 'value': 'on'}], value='off', labelStyle={'marginRight': '12px'})),
                create_settings_row('Marker Size', dcc.Slider(id=ID_DASH_MARKER_SIZE_SLIDER, min=2, max=12, value=6, disabled=True)),
            ])
        ])
    ])

def create_layout_sensor_detail(sensor_index):
    return html.Div(className='detail-page-container', children=[
        html.Div(className='detail-page-header', children=[
            html.H1(f'Sensor {sensor_index} - Detailed View', className='detail-page-title'),
        ]),
        html.Div(className='detail-graph-container', children=[
            dcc.Graph(id=ID_DETAIL_GRAPH, config=GRAPH_CONFIG, style={'height': '100%'})
        ]),
        html.Div(id=ID_DETAIL_CONTROLS_WRAPPER, className='detail-controls-panel', children=[
            create_settings_row('Display Points', dcc.Slider(id=ID_DETAIL_DISPLAY_POINTS_SLIDER, min=100, max=MAX_BUFFER_SIZE, step=100, value=DEFAULT_DISPLAY_POINTS_DETAIL)),
            create_settings_row('Line Shape', dcc.RadioItems(id=ID_DETAIL_LINE_SHAPE_RADIO, options=[{'label': 'Linear', 'value': 'linear'}, {'label': 'Spline', 'value': 'spline'}], value='spline', labelStyle={'marginRight': '12px'})),
            create_settings_row('Show Markers', dcc.RadioItems(id=ID_DETAIL_SHOW_MARKERS_RADIO, options=[{'label': 'Off', 'value': 'off'}, {'label': 'On', 'value': 'on'}], value='off', labelStyle={'marginRight': '12px'})),
            html.Div(id=ID_DETAIL_MARKER_SIZE_WRAPPER, children=[
                create_settings_row('Marker Size', dcc.Slider(id=ID_DETAIL_MARKER_SIZE_SLIDER, min=2, max=12, value=6))
            ], style={'display': 'none'})
        ])
    ])

# ---------- Main App Layout (Router) ----------
app.layout = html.Div([
    dcc.Location(id=ID_URL, refresh=False),
    create_navigation_header(),
    html.Div(id=ID_PAGE_CONTENT),
    dcc.Store(id=ID_RUNNING_STORE, data=False),
    dcc.Store(id=ID_DASH_SETTINGS_STORE, data={}),
    dcc.Store(id=ID_DETAIL_SETTINGS_STORE, data={}),
    dcc.Download(id=ID_DOWNLOAD_DATA),
    dcc.Interval(id=ID_INTERVAL, interval=UPDATE_INTERVAL_MS, n_intervals=0)
])

# ---------- Callbacks ----------

# --- 1. Main Router and Navigation Callback ---
@app.callback(
    Output(ID_PAGE_CONTENT, 'children'),
    Output(ID_NAV_HEADER, 'children'),
    Input(ID_URL, 'pathname')
)
def display_page(pathname):
    nav_links = [dcc.Link('Dashboard', href='/', className='nav-link')]
    nav_links.extend([dcc.Link(f'Sensor {i}', href=f'/sensor-{i}', className='nav-link') for i in range(1, 5)])
    for link in nav_links:
        if link.href == pathname: link.className += ' active'

    if pathname and pathname.startswith('/sensor-'):
        try:
            sensor_index = int(pathname.split('-')[-1])
            if 1 <= sensor_index <= 4:
                return create_layout_sensor_detail(sensor_index), nav_links
        except (ValueError, IndexError):
            pass # Fall through to 404
    
    if pathname == '/':
        return create_layout_dashboard(), nav_links
    
    return html.H1("404: Not found"), nav_links

# --- 2. Global Control Callbacks ---
@app.callback(Output(ID_RUNNING_STORE, 'data'), Input(ID_BTN_TOGGLE_LOG, 'n_clicks'), State(ID_RUNNING_STORE, 'data'), prevent_initial_call=True)
def toggle_running_state(n, is_running): return not is_running

@app.callback(Output(ID_BTN_TOGGLE_LOG, 'children'), Output(ID_BTN_TOGGLE_LOG, 'className'), Input(ID_RUNNING_STORE, 'data'))
def update_toggle_button_ui(is_running):
    if is_running: return [html.I(className='fa-solid fa-pause'), " Stop Logging"], 'control-btn btn-danger'
    return [html.I(className='fa-solid fa-play'), " Start Logging"], 'control-btn btn-success'

@app.callback(Output(ID_STATUS_DIV, 'children'), Output(ID_STATUS_DIV, 'style'), Input(ID_RUNNING_STORE, 'data'), Input(ID_BTN_EXPORT, 'n_clicks'))
def update_status_display(is_running, export_clicks):
    base_style = {'fontWeight': '700', 'color': 'white'}
    if dash.ctx.triggered_id == ID_BTN_EXPORT: return "Exported CSV", {**base_style, 'backgroundColor': 'var(--accent-color)'}
    if not time_data: return "Waiting for data...", {**base_style, 'backgroundColor': '#6B7280'}
    if is_running: return "Logging: RUNNING", {**base_style, 'backgroundColor': 'var(--success-color)'}
    return "PAUSED - Zoom/Pan Enabled", {**base_style, 'backgroundColor': 'var(--warning-color)'}

@app.callback(Output(ID_DOWNLOAD_DATA, 'data'), Input(ID_BTN_EXPORT, 'n_clicks'), prevent_initial_call=True)
def export_data_as_csv(n_clicks):
    df_data = {"timestamp": list(time_data)}
    df_data.update({name: list(buffer) for name, buffer in sensor_data.items()})
    df = pd.DataFrame(df_data)
    timestamp = get_current_time().strftime("%Y%m%d_%H%M%S")
    return dict(content=df.to_csv(index=False), filename=f"sensor_data_{timestamp}.csv")

# --- 3. Dashboard Page Callbacks ---
@app.callback(Output(ID_MODAL_CONTAINER, 'style'), Input(ID_BTN_SETTINGS, 'n_clicks'), Input(ID_BTN_CLOSE_MODAL, 'n_clicks'), prevent_initial_call=True)
def toggle_settings_modal(n1, n2):
    is_opening = dash.ctx.triggered_id == ID_BTN_SETTINGS
    return {'display': 'flex'} if is_opening else {'display': 'none'}

@app.callback(Output(ID_DASH_MARKER_SIZE_SLIDER, 'disabled'), Input(ID_DASH_SHOW_MARKERS_RADIO, 'value'))
def toggle_dash_marker_slider(marker_status): return marker_status == 'off'

@app.callback(Output(ID_DASH_SETTINGS_STORE, 'data'),
              [Input(ID_DASH_DISPLAY_POINTS_SLIDER, 'value'), Input(ID_DASH_LINE_SHAPE_RADIO, 'value'),
               Input(ID_DASH_SHOW_MARKERS_RADIO, 'value'), Input(ID_DASH_MARKER_SIZE_SLIDER, 'value')])
def sync_dash_settings_to_store(points, shape, markers, size):
    return {'points': points, 'shape': shape, 'markers': markers, 'size': size}

@app.callback([Output(f'sensor{i}-graph', 'figure') for i in range(1, 5)],
              Input(ID_INTERVAL, 'n_intervals'),
              State(ID_RUNNING_STORE, 'data'),
              State(ID_DASH_SETTINGS_STORE, 'data'),
              [State(f'sensor{i}-graph', 'relayoutData') for i in range(1, 5)])
def update_dashboard_graphs(n, is_running, settings, relayout1, relayout2, relayout3, relayout4):
    if is_running: generate_new_data()

    settings = settings or {}
    points = settings.get('points', DEFAULT_DISPLAY_POINTS_DASH)
    shape = settings.get('shape', 'linear')
    show_markers = settings.get('markers') == 'on'
    size = settings.get('size', 6)

    num_total = len(time_data)
    start_idx = max(0, num_total - points)
    x_slice = list(islice(time_data, start_idx, num_total))
    
    mode = 'lines+markers' if show_markers else 'lines'
    marker_dict = dict(size=size) if show_markers else {}
    line_dict = dict(shape=shape, width=2)
    
    outputs = []
    relayouts = [relayout1, relayout2, relayout3, relayout4]
    for i, relayout in enumerate(relayouts, 1):
        sensor_name = f's{i}'
        fig = create_base_figure(f'Sensor {i}')
        y_slice = list(islice(sensor_data[sensor_name], start_idx, num_total))
        if x_slice:
            fig.add_trace(go.Scatter(x=x_slice, y=y_slice, mode=mode, marker=marker_dict, line=line_dict))
        
        if not is_running and relayout:
            if 'xaxis.range[0]' in relayout and 'yaxis.range[0]' in relayout:
                fig.update_layout(xaxis_range=[relayout['xaxis.range[0]'], relayout['xaxis.range[1]']],
                                  yaxis_range=[relayout['yaxis.range[0]'], relayout['yaxis.range[1]']])
        outputs.append(fig)
    return outputs

# --- 4. Sensor Detail Page Callbacks ---
@app.callback(Output(ID_DETAIL_MARKER_SIZE_WRAPPER, 'style'), Input(ID_DETAIL_SHOW_MARKERS_RADIO, 'value'))
def toggle_detail_marker_slider_visibility(marker_status):
    return {'display': 'grid'} if marker_status == 'on' else {'display': 'none'}

@app.callback(Output(ID_DETAIL_SETTINGS_STORE, 'data'),
              [Input(ID_DETAIL_DISPLAY_POINTS_SLIDER, 'value'), Input(ID_DETAIL_LINE_SHAPE_RADIO, 'value'),
               Input(ID_DETAIL_SHOW_MARKERS_RADIO, 'value'), Input(ID_DETAIL_MARKER_SIZE_SLIDER, 'value')])
def sync_detail_settings_to_store(points, shape, markers, size):
    return {'points': points, 'shape': shape, 'markers': markers, 'size': size}

@app.callback(Output(ID_DETAIL_GRAPH, 'figure'),
              Output(ID_DETAIL_GRAPH, 'extendData'),
              Input(ID_INTERVAL, 'n_intervals'),
              Input(ID_DETAIL_SETTINGS_STORE, 'data'),
              State(ID_URL, 'pathname'),
              State(ID_RUNNING_STORE, 'data'))
def update_detail_graph_live(n, settings, pathname, is_running):
    triggered_id = dash.ctx.triggered_id
    try:
        sensor_index = int(pathname.split('-')[-1])
        sensor_name = f's{sensor_index}'
    except (ValueError, IndexError, TypeError):
        return no_update, no_update

    # Scenario 1: Live update, append one point
    if triggered_id == ID_INTERVAL and is_running and time_data:
        new_time, new_value = time_data[-1], sensor_data[sensor_name][-1]
        # The format for extendData is (data_dict, trace_indices, max_points)
        points_to_keep = settings.get('points', DEFAULT_DISPLAY_POINTS_DETAIL)
        return no_update, (dict(x=[[new_time]], y=[[new_value]]), [0], points_to_keep)

    # Scenario 2: Page load or settings change, do a full redraw
    else:
        settings = settings or {}
        points = settings.get('points', DEFAULT_DISPLAY_POINTS_DETAIL)
        shape = settings.get('shape', 'spline')
        show_markers = settings.get('markers') == 'on'
        size = settings.get('size', 6)

        num_total = len(time_data)
        start_idx = max(0, num_total - points)
        x_slice = list(islice(time_data, start_idx, num_total))
        y_slice = list(islice(sensor_data[sensor_name], start_idx, num_total))
        
        fig = create_base_figure(height=None) # Auto-height for flexbox
        mode = 'lines+markers' if show_markers else 'lines'
        marker_dict = dict(size=size) if show_markers else {}
        line_dict = dict(shape=shape, width=2)
        
        if x_slice:
            fig.add_trace(go.Scatter(x=x_slice, y=y_slice, mode=mode, marker=marker_dict, line=line_dict))
        
        return fig, no_update


if __name__ == '__main__':
    app.run(debug=False)
