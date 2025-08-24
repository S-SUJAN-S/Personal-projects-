# save as web_dash_controls_final_fixed.py

"""
A professional, real-time sensor data visualization dashboard using Plotly Dash.

This application simulates and displays data from four sensors, allowing users to
start/stop logging, customize the graph appearance, and export the collected data.

Key enhancements in this version:
- Interactive Graph Toolbar Enabled: The Plotly mode bar is now enabled,
  allowing users to zoom, pan, and select data sections on the graphs.
- Robust Zoom/Pan: The feature to preserve zoom/pan state when paused has
  been fixed to be reliable and error-free.
- Clearer User Workflow: The UI now explicitly states that zoom/pan is
  enabled when logging is paused, guiding the user on how to inspect data.
- Pop-up Settings Modal: Features a well-structured and customizable settings
  modal with an improved layout using CSS Grid.
- Code Readability: The layout is more semantic, and CSS is structured with
  comments, emulating best practices for external stylesheets.
"""

import datetime as dt
import random
from collections import deque
from itertools import islice

import dash
import pandas as pd
import plotly.graph_objs as go
from dash import dcc, html, Input, Output, State

# ---------- Constants & Configuration ----------

# App-level config
APP_TITLE = "Live Sensor Dashboard"
UPDATE_INTERVAL_MS = 500  # Update graphs every 0.5 seconds

# Data buffer config
MAX_BUFFER_SIZE = 10000  # Store up to 10,000 data points in server memory
DEFAULT_DISPLAY_POINTS = 50  # Initially show the last 50 data points

# Plotly graph config
GRAPH_CONFIG = {'displayModeBar': True, 'responsive': True}

# CSS classes and IDs for layout components
ID_BTN_TOGGLE_LOG = "btn-toggle-log"
ID_BTN_EXPORT = "btn-export"
ID_BTN_SETTINGS = "btn-settings"
ID_BTN_CLOSE_MODAL = "btn-close-modal"
ID_STATUS_DIV = "status-div"
ID_MODAL_CONTAINER = "modal-container"
ID_RUNNING_STORE = "running-store"
ID_SETTINGS_VISIBLE_STORE = "settings-visible"
ID_SETTINGS_STORE = "settings-store"
ID_DOWNLOAD_DATA = "download-data"
ID_INTERVAL = "interval-component"
ID_DISPLAY_POINTS_SLIDER = "display-points-slider"
ID_LINE_SHAPE_RADIO = "line-shape-radio"
ID_SHOW_MARKERS_RADIO = "show-markers-radio"
ID_MARKER_SIZE_SLIDER = "marker-size-slider"
ID_SETTINGS_NOTE = "settings-note"

# ---------- App Initialization ----------
external_stylesheets = [
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'
]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = APP_TITLE

# FIX 1: RESTORED FULL CSS STYLING BLOCK THAT WAS ACCIDENTALLY REMOVED
app.index_string = """<!DOCTYPE html>
<html>
<head>
    {%metas%}
    <title>{%title%}</title>
    {%favicon%}
    {%css%}
    <style>
        /* --- Best Practice Note --- */
        /* In a real-world Dash app, this CSS would be in an 'assets/style.css' file */
        /* for better organization and browser caching. */

        /* --- Main Variables --- */
        :root {
            --font-family-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            --bg-color: #111827; /* Dark Slate Blue */
            --panel-color: #1F2937; /* Lighter Slate */
            --border-color: #374151; /* Muted Border */
            --text-color: #F9FAFB; /* Almost White */
            --text-muted-color: #9CA3AF; /* Gray */
            --accent-color: #3B82F6; /* Bright Blue */
            --success-color: #22C55E; /* Green */
            --danger-color: #EF4444; /* Red */
            --warning-color: #F59E0B; /* Amber for pause state */
            --border-radius: 8px;
        }

        /* --- Base Styles --- */
        body {
            margin: 0;
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: var(--font-family-sans);
            overscroll-behavior-x: none;
        }

        /* --- Layout Components --- */
        .header {
            padding: 1rem 1.5rem;
            background-color: var(--panel-color);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
        }
        .header-title {
            font-size: 1.5rem;
            margin: 0;
            font-weight: 600;
            letter-spacing: -0.5px;
        }
        .header-icon {
            font-size: 1.75rem;
            margin-right: 0.75rem;
            color: var(--accent-color);
        }

        .container {
            display: flex;
            height: calc(100vh - 65px); /* Full height minus header */
        }

        .sidebar {
            width: 280px;
            background-color: var(--bg-color);
            padding: 1.5rem;
            box-sizing: border-box;
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }

        .main-content {
            flex: 1; /* Use flex-grow to fill remaining space */
            padding: 1.5rem;
            box-sizing: border-box;
            overflow-y: auto;
        }

        /* --- Control & UI Elements --- */
        .control-panel, .status-panel {
            background-color: var(--panel-color);
            border-radius: var(--border-radius);
            padding: 1rem;
            border: 1px solid var(--border-color);
        }

        .panel-title {
            margin-top: 0;
            margin-bottom: 1rem;
            font-size: 1.1rem;
            font-weight: 600;
        }

        .control-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            width: 100%;
            padding: 0.75rem;
            margin-bottom: 0.75rem;
            border-radius: 6px;
            border: 1px solid transparent;
            font-weight: 600;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.2s ease-in-out;
        }
        .control-btn:last-child { margin-bottom: 0; }
        .btn-primary { background-color: var(--accent-color); color: white; }
        .btn-primary:hover { background-color: #2563EB; }
        .btn-secondary { background-color: var(--border-color); color: var(--text-color); }
        .btn-secondary:hover { background-color: #4B5563; }
        .btn-success { background-color: var(--success-color); color: white; }
        .btn-danger { background-color: var(--danger-color); color: white; }


        .status-indicator {
            padding: 1rem;
            font-weight: 700;
            text-align: center;
            border-radius: 6px;
            transition: all 0.3s ease;
        }

        .graph-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
        }

        /* --- Settings Modal Styles --- */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.7);
            z-index: 1000;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .modal-content {
            position: relative;
            background-color: var(--panel-color);
            border-radius: var(--border-radius);
            border: 1px solid var(--border-color);
            padding: 1.5rem 2rem 2rem 2rem;
            width: 90%;
            max-width: 600px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        }

        .modal-header {
            padding-bottom: 1rem;
            margin-bottom: 1.5rem;
            border-bottom: 1px solid var(--border-color);
        }

        .modal-title {
            margin: 0;
            font-size: 1.25rem;
        }

        .modal-close-btn {
            position: absolute;
            top: 0.75rem;
            right: 1rem;
            background: none;
            border: none;
            color: var(--text-muted-color);
            font-size: 1.75rem;
            font-weight: bold;
            cursor: pointer;
            transition: color 0.2s ease;
        }
        .modal-close-btn:hover { color: var(--text-color); }

        .settings-row {
            display: grid;
            grid-template-columns: 140px 1fr;
            gap: 1.5rem;
            align-items: center;
            margin-bottom: 1.25rem;
        }

        .settings-label {
            color: var(--text-muted-color);
            font-size: 0.9rem;
            font-weight: 500;
            text-align: right;
        }

        .settings-note {
            color:var(--text-muted-color);
            margin-top:1.5rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border-color);
            font-size:0.85rem;
            text-align: center;
        }

        /* --- Responsive Design --- */
        @media (max-width: 1200px) {
            .sidebar { width: 240px; }
        }
        @media (max-width: 992px) {
            .container { flex-direction: column; height: auto; }
            .sidebar, .main-content { width: 100%; border: 0; }
            .graph-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap">
    {%app_entry%}
    <footer>
        {%config%}
        {%scripts%}
        {%renderer%}
    </footer>
</body>
</html>"""

# ---------- Data Buffers (Server-Side) ----------
time_data = deque(maxlen=MAX_BUFFER_SIZE)
sensor_data = {
    's1': deque(maxlen=MAX_BUFFER_SIZE), 's2': deque(maxlen=MAX_BUFFER_SIZE),
    's3': deque(maxlen=MAX_BUFFER_SIZE), 's4': deque(maxlen=MAX_BUFFER_SIZE),
}

# ---------- Helper Functions ----------
def get_current_time() -> dt.datetime:
    return dt.datetime.now()

def generate_new_data():
    current_time = get_current_time()
    time_data.append(current_time)
    for name, buffer in sensor_data.items():
        last_val = buffer[-1] if buffer else 50.0
        new_val = last_val + random.uniform(-2.5, 2.5) - (last_val - 50) * 0.1
        sensor_data[name].append(max(0, min(120, new_val)))

def create_base_figure(title: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        title={'text': title, 'x': 0.05, 'xanchor': 'left', 'font': {'size': 18}},
        xaxis_title="Time", yaxis_title="Value", template="plotly_dark",
        plot_bgcolor='#1F2937', paper_bgcolor='#1F2937', font=dict(color='#F9FAFB'),
        margin=dict(l=40, r=20, t=50, b=40), height=360,
        xaxis=dict(gridcolor='rgba(255,255,255,0.1)', zeroline=False),
        yaxis=dict(gridcolor='rgba(255,255,255,0.1)', zeroline=False),
    )
    return fig

def create_settings_row(label: str, control_component):
    return html.Div([
        html.Label(label, className='settings-label'),
        control_component
    ], className='settings-row')

# ---------- App Layout ----------
app.layout = html.Div([
    html.Header(className='header', children=[
        html.I(className='fa-solid fa-satellite-dish header-icon'),
        html.H1('Live Sensor Dashboard', className='header-title')
    ]),
    html.Div(className='container', children=[
        html.Aside(className='sidebar', children=[
            html.Div(className='control-panel', children=[
                html.H2("Controls", className='panel-title'),
                html.Button(id=ID_BTN_TOGGLE_LOG, n_clicks=0, className='control-btn'),
                html.Button([html.I(className='fa-solid fa-cog'), " Settings"], id=ID_BTN_SETTINGS, n_clicks=0, className='control-btn btn-secondary'),
                html.Button([html.I(className='fa-solid fa-download'), " Export Data"], id=ID_BTN_EXPORT, n_clicks=0, className='control-btn btn-secondary'),
            ]),
            html.Div(className='status-panel', children=[
                html.H2("Status", className='panel-title'),
                html.Div(id=ID_STATUS_DIV, className='status-indicator'),
            ]),
        ]),
        html.Main(className='main-content', children=[
            html.Div(className='graph-grid', children=[
                dcc.Graph(id='sensor1-graph', config=GRAPH_CONFIG),
                dcc.Graph(id='sensor2-graph', config=GRAPH_CONFIG),
                dcc.Graph(id='sensor3-graph', config=GRAPH_CONFIG),
                dcc.Graph(id='sensor4-graph', config=GRAPH_CONFIG),
            ]),
        ]),
    ]),
    html.Div(id=ID_MODAL_CONTAINER, className='modal-overlay', style={'display': 'none'}, children=[
        html.Div(className='modal-content', children=[
            html.Div(className='modal-header', children=[
                html.H3('Graph Settings', className='modal-title'),
                html.Button('×', id=ID_BTN_CLOSE_MODAL, n_clicks=0, className='modal-close-btn'),
            ]),
            create_settings_row('Display Points',
                dcc.Slider(id=ID_DISPLAY_POINTS_SLIDER, min=10, max=500, step=10, value=DEFAULT_DISPLAY_POINTS)
            ),
            create_settings_row('Line Shape',
                dcc.RadioItems(id=ID_LINE_SHAPE_RADIO, options=[{'label': 'Linear', 'value': 'linear'}, {'label': 'Spline', 'value': 'spline'}], value='linear', labelStyle={'display': 'inline-block', 'marginRight': '12px'})
            ),
            create_settings_row('Show Markers',
                dcc.RadioItems(id=ID_SHOW_MARKERS_RADIO, options=[{'label': 'Off', 'value': 'off'}, {'label': 'On', 'value': 'on'}], value='off', labelStyle={'display': 'inline-block', 'marginRight': '12px'})
            ),
            create_settings_row('Marker Size',
                dcc.Slider(id=ID_MARKER_SIZE_SLIDER, min=2, max=12, step=1, value=6, disabled=True)
            ),
            html.Div(id=ID_SETTINGS_NOTE, className='settings-note')
        ])
    ]),
    dcc.Store(id=ID_RUNNING_STORE, data=False),
    dcc.Store(id=ID_SETTINGS_VISIBLE_STORE, data=False),
    dcc.Store(id=ID_SETTINGS_STORE, data={
        'display_points': DEFAULT_DISPLAY_POINTS, 'line_shape': 'linear',
        'show_markers': 'off', 'marker_size': 6
    }),
    dcc.Download(id=ID_DOWNLOAD_DATA),
    dcc.Interval(id=ID_INTERVAL, interval=UPDATE_INTERVAL_MS, n_intervals=0)
])

# ---------- Callbacks ----------

@app.callback(
    Output(ID_RUNNING_STORE, 'data'),
    Input(ID_BTN_TOGGLE_LOG, 'n_clicks'),
    State(ID_RUNNING_STORE, 'data'),
    prevent_initial_call=True
)
def toggle_running_state(n_clicks, is_running):
    return not is_running

@app.callback(
    Output(ID_SETTINGS_VISIBLE_STORE, 'data'),
    Input(ID_BTN_SETTINGS, 'n_clicks'),
    Input(ID_BTN_CLOSE_MODAL, 'n_clicks'),
    State(ID_SETTINGS_VISIBLE_STORE, 'data'),
    prevent_initial_call=True
)
def toggle_settings_visibility(settings_clicks, close_clicks, is_visible):
    return not is_visible

@app.callback(
    Output(ID_DOWNLOAD_DATA, 'data'),
    Input(ID_BTN_EXPORT, 'n_clicks'),
    prevent_initial_call=True
)
def export_data_as_csv(n_clicks):
    df_data = {"timestamp": list(time_data)}
    df_data.update({name: list(buffer) for name, buffer in sensor_data.items()})
    df = pd.DataFrame(df_data)
    timestamp = get_current_time().strftime("%Y%m%d_%H%M%S")
    return dict(content=df.to_csv(index=False), filename=f"sensor_data_{timestamp}.csv")

@app.callback(
    Output(ID_BTN_TOGGLE_LOG, 'children'),
    Output(ID_BTN_TOGGLE_LOG, 'className'),
    Input(ID_RUNNING_STORE, 'data')
)
def update_toggle_button_ui(is_running):
    if is_running:
        return [html.I(className='fa-solid fa-pause'), " Stop Logging"], 'control-btn btn-danger'
    return [html.I(className='fa-solid fa-play'), " Start Logging"], 'control-btn btn-success'

@app.callback(
    Output(ID_STATUS_DIV, 'children'),
    Output(ID_STATUS_DIV, 'style'),
    Input(ID_RUNNING_STORE, 'data'),
    Input(ID_BTN_EXPORT, 'n_clicks')
)
def update_status_display(is_running, export_clicks):
    base_style = {'fontWeight': '700', 'color': 'white'}
    if dash.ctx.triggered_id == ID_BTN_EXPORT:
        return "Exported CSV", {**base_style, 'backgroundColor': 'var(--accent-color)'}
    if not time_data:
        return "Waiting for data...", {**base_style, 'backgroundColor': '#6B7280'}
    if is_running:
        return "Logging: RUNNING", {**base_style, 'backgroundColor': 'var(--success-color)'}
    return "PAUSED - Zoom/Pan Enabled", {**base_style, 'backgroundColor': 'var(--warning-color)'}

@app.callback(
    Output(ID_MODAL_CONTAINER, 'style'),
    Input(ID_SETTINGS_VISIBLE_STORE, 'data')
)
def show_hide_settings_modal(is_visible):
    return {'display': 'flex'} if is_visible else {'display': 'none'}

@app.callback(
    Output(ID_MARKER_SIZE_SLIDER, 'disabled'),
    Input(ID_SHOW_MARKERS_RADIO, 'value')
)
def toggle_marker_size_slider(marker_status):
    return marker_status == 'off'

@app.callback(
    Output(ID_SETTINGS_STORE, 'data'),
    Input(ID_DISPLAY_POINTS_SLIDER, 'value'),
    Input(ID_LINE_SHAPE_RADIO, 'value'),
    Input(ID_SHOW_MARKERS_RADIO, 'value'),
    Input(ID_MARKER_SIZE_SLIDER, 'value'),
    prevent_initial_call=True
)
def sync_settings_to_store(display_points, line_shape, show_markers, marker_size):
    return {
        'display_points': display_points, 'line_shape': line_shape,
        'show_markers': show_markers, 'marker_size': marker_size
    }

@app.callback(
    Output(ID_SETTINGS_NOTE, 'children'),
    Input(ID_SETTINGS_STORE, 'data')
)
def update_settings_summary_note(settings):
    dp = settings.get('display_points', DEFAULT_DISPLAY_POINTS)
    ls = settings.get('line_shape', 'linear').capitalize()
    markers = 'On' if settings.get('show_markers') == 'on' else 'Off'
    msize = settings.get('marker_size', 6)
    return f"Displaying last {dp} points | Shape: {ls} | Markers: {markers} (Size: {msize})"

@app.callback(
    Output('sensor1-graph', 'figure'), Output('sensor2-graph', 'figure'),
    Output('sensor3-graph', 'figure'), Output('sensor4-graph', 'figure'),
    Input(ID_INTERVAL, 'n_intervals'),
    State(ID_RUNNING_STORE, 'data'),
    State(ID_SETTINGS_STORE, 'data'),
    State('sensor1-graph', 'relayoutData'), State('sensor2-graph', 'relayoutData'),
    State('sensor3-graph', 'relayoutData'), State('sensor4-graph', 'relayoutData'),
)
def update_graphs(n, is_running, settings, relayout1, relayout2, relayout3, relayout4):
    if is_running:
        generate_new_data()

    display_points = settings.get('display_points', DEFAULT_DISPLAY_POINTS)
    line_shape = settings.get('line_shape', 'linear')
    show_markers = settings.get('show_markers') == 'on'
    marker_size = settings.get('marker_size', 6)

    num_points = len(time_data)
    start_index = max(0, num_points - display_points)
    x_slice = list(islice(time_data, start_index, num_points))
    sensor_slices = {name: list(islice(buf, start_index, num_points)) for name, buf in sensor_data.items()}

    mode = 'lines+markers' if show_markers else 'lines'
    marker_dict = dict(size=marker_size, color='#3B82F6') if show_markers else {}
    line_dict = dict(shape=line_shape, width=2, color='#3B82F6')

    def create_trace(x_data, y_data):
        return go.Scatter(x=x_data, y=y_data, mode=mode, marker=marker_dict, line=line_dict)

    outputs = []
    relayouts = [relayout1, relayout2, relayout3, relayout4]
    for i, relayout_data in enumerate(relayouts, 1):
        sensor_name = f's{i}'
        fig = create_base_figure(f'Sensor {i}')
        if x_slice:
            fig.add_trace(create_trace(x_slice, sensor_slices[sensor_name]))

        # FIX 2: Added checks to prevent KeyError if only one axis is changed
        # This makes the zoom/pan feature robust and error-free.
        if not is_running and relayout_data:
            if 'xaxis.range[0]' in relayout_data and 'xaxis.range[1]' in relayout_data:
                fig.update_layout(xaxis_range=[relayout_data['xaxis.range[0]'], relayout_data['xaxis.range[1]']])
            if 'yaxis.range[0]' in relayout_data and 'yaxis.range[1]' in relayout_data:
                fig.update_layout(yaxis_range=[relayout_data['yaxis.range[0]'], relayout_data['yaxis.range[1]']])

        outputs.append(fig)

    return tuple(outputs)

# ---------- Run Application ----------
if __name__ == '__main__':
    app.run(debug=False)
