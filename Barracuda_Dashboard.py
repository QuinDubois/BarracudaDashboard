# Barracuda Dashboard
# Authors: Alex Burnham, Quinlan Dubois
# Latest Revision: 0.1.1
# Latest Revision Date: 10/26/2022


# File Header containing imports, constants, and start-up processing.
#######################################################################################################################
import pathlib
import json
import numpy as np
from urllib.request import urlopen
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd

from App import app
from App import server

from Barracuda_Processing import control_sort
from Barracuda_Plotting import default_chart, plot_line, plot_control, plot_choropleth

# Style constants
DEFAULT_OPACITY = 0.8

COLOR_STYLES = {
    "chart_background": "#E6E4E6",
    "chart_grid": "#B3B1B3",
    "tick_font": "#111111",
    "font": "#111111",
    "line_colors": [
        "#21A0A6"
    ],
    "marker_colors": [
        "#FAEA48",
        "#c47e0e",
        "#4951de",
        "#bd51c9",
        "#4cbf39",
        "#c95034",
    ]
}

# flags for sorting the selected data
data_styles = {
    "base": [COLOR_STYLES["line_colors"][0], 1],
    "above average": [COLOR_STYLES["marker_colors"][0], 1],
    "below average": [COLOR_STYLES["marker_colors"][1], 1],
    "deviation above": [COLOR_STYLES["marker_colors"][2], 1],
    "deviation below": [COLOR_STYLES["marker_colors"][3], 1],
    "trending up": [COLOR_STYLES["marker_colors"][4], 1],
    "trending down": [COLOR_STYLES["marker_colors"][5], 1]
}

# Load data
APP_PATH = str(pathlib.Path(__file__).parent.resolve())

# set mapbox token and style
mapbox_access_token = "pk.eyJ1IjoicGxvdGx5bWFwYm94IiwiYSI6ImNrOWJqb2F4djBnMjEzbG50amg0dnJieG4ifQ.Zme1-Uzoi75IaFbieBDl3A"
mapbox_style = "mapbox://styles/plotlymapbox/cjvprkf3t1kns1cqjxuxmwixz"

# read in fips shape data
file = open("data/geojson-counties-fips.json")
counties = json.load(file)

# Dataset Loader
#     - A new line needs to be added here when a new dataset is added to the dashboard
#############################################################################
# read in climate data
data_annual_climate = "data/output.csv"
df_annual_climate = pd.read_csv(data_annual_climate, dtype={'fips': str})

# read in kestral range shift data
data_kestral_model = "data/kestralModel.csv"
df_kestral_model = pd.read_csv(data_kestral_model)

# read in carya ovata range shift data
data_carya_ovata = "data/Carya_ovata.csv"
df_carya_ovata = pd.read_csv(data_carya_ovata)

# read in carya ovata range shift data imported from spacetime API
data_carya_ovata_spacetime = "data/carya_ovata_10km.csv"
df_carya_ovata_spacetime = pd.read_csv(data_carya_ovata_spacetime)

#############################################################################
# Import Data labels JSON
data_json_path = "data/dataset-names.json"
data_json_dict = {}
try:
    with open(data_json_path) as json_file:
        data_json_dict = json.load(json_file)
except json.JSONDecodeError as error:
    print(">>> JSON ERROR: JSON empty or invalid structure. Dataframe Selectors will not work properly! <<<")
    data_json_dict = {}
except FileNotFoundError as error:
    print(
        ">>> JSON ERROR: JSON " + data_json_path + " does not exist. Dataframe Selectors will not work properly! <<<")
    data_json_dict = {}

# Create dropdown list for datasets
dataset_options = []
for key in data_json_dict.keys():
    dataset_options.append(
        {'label': data_json_dict[key]['dataset_label'],
         'value': key}
    )
# Create list of control chart selectors for checklist
data_style_options = []
for key in data_styles:
    data_style_options.append({'label': key, 'value': key})

#######################################################################################################################


# App layout
#######################################################################################################################
app.layout = html.Div(
    id="root",
    children=[
        html.Div(
            id="header",
            children=[
                html.A(
                    html.Img(id="logo", src=app.get_asset_url("barracuda_logo_final.png")),
                    href="https://www.uvm.edu/",
                ),
                html.H4(children=" Barracuda Data Visualization Dashboard"),
                html.P(
                    id="description",
                    children="Biodiversity and Rural Response to Climate Change Using Data Analysis",
                ),
            ],
        ),

        # App Container
        html.Div(
            id="app-container",
            children=[

                # Top row
                html.Div(
                    id="top-row",
                    children=[

                        # Left panel
                        html.Div(
                            id="choropleth-container",
                            children=[
                                html.Div(
                                    id="dropdown-container",
                                    children=[

                                        # Dataframe Selector Dropdown
                                        html.P(id="dataframe-title", children="Select a Dataset"),
                                        dcc.Dropdown(
                                            options=dataset_options,
                                            value='output.csv',
                                            id="dataframe-dropdown"
                                        ),

                                        # Data Selector Dropdown
                                        html.P(id="data-title", children="Select a Variable to Plot"),
                                        dcc.Dropdown(
                                            options=[
                                                {
                                                    "label": "Average of Nighttime Minimum Temperature, (deg. C)",
                                                    "value": "tmin",
                                                },
                                                {
                                                    "label": "Average of Daytime High Temperature, (deg. C)",
                                                    "value": "tmax",
                                                },
                                                {
                                                    "label": "Average of Daily Mean Temperature, (deg. C)",
                                                    "value": "tmean",
                                                },
                                                {
                                                    "label": "Total Annual Precipitation, (mm)",
                                                    "value": "prec",
                                                },
                                                {
                                                    "label": "Total April Precipitation, (mm)",
                                                    "value": "aprec",
                                                },
                                                {
                                                    "label": "Length of Frost Free Period, (days)",
                                                    "value": "ffp",
                                                },
                                            ],
                                            value="tmin",
                                            id="data-dropdown",
                                        ),
                                    ],
                                ),

                                # Choropleth Chart
                                html.Div(
                                    id="heatmap-container",
                                    children=[
                                        html.P(
                                            "Heatmap Over Time (Select Year Below Map)",
                                            id="heatmap-title",
                                        ),
                                        dcc.Graph(
                                            id="county-choropleth",
                                            figure=dict(
                                                layout=dict(
                                                    mapbox=dict(
                                                        layers=[],
                                                        accesstoken=mapbox_access_token,
                                                        style=mapbox_style,
                                                        center=dict(
                                                            lat=38.72490, lon=-95.61446
                                                        ),
                                                        pitch=0,
                                                        zoom=3.5,
                                                    ),
                                                    autosize=True,
                                                ),
                                            ),
                                        ),
                                    ],
                                ),

                                # Year Selector Slider
                                html.Div(
                                    id="year-container",
                                    children=[
                                        html.P(id="year-title", children="Select a Year to Plot"),
                                        dcc.Slider(
                                            value=1950,
                                            min=1950,
                                            max=2019,
                                            step=1,
                                            marks={
                                                1950: {'label': '1950'},
                                                1967: {'label': '1967'},
                                                1985: {'label': '1985'},
                                                2002: {'label': '2002'},
                                                2019: {'label': '2019'},
                                            },
                                            tooltip={"placement": "bottom", "always_visible": True},
                                            id="year-slider",
                                        ),
                                    ], style={'display': 'block'},
                                ),

                            ],
                        ),

                        # Top Right, Graph Container
                        html.Div(
                            id="graph-container",
                            children=[

                                # Chart Swapper
                                html.Div(
                                    children=[
                                        dcc.Dropdown(
                                            options=[
                                                {
                                                    "label": "Line Chart",
                                                    "value": "linechart",
                                                },
                                                {
                                                    "label": "Control Chart",
                                                    "value": "controlchart",
                                                },
                                                {
                                                    "label": "Statespace Chart",
                                                    "value": "statespace",
                                                },
                                            ],
                                            value="linechart",
                                            id="chart-swapper",
                                        ),
                                    ],
                                ),

                                # Aggregation Selector
                                html.P(id="aggregation-title", children="Select summary statistic to plot:"),
                                dcc.Dropdown(
                                    options=[
                                        {
                                            "label": "Mean Value",
                                            "value": "mean",
                                        },
                                        {
                                            "label": "Median Value",
                                            "value": "median",
                                        },
                                        {
                                            "label": "Min. Value",
                                            "value": "min",
                                        },
                                        {
                                            "label": "Max. Value ",
                                            "value": "max",
                                        },
                                    ],
                                    value="mean",
                                    id="aggregation-dropdown",
                                ),
                                html.P(id="controls-text",
                                       children="Control options are below charts.",
                                       style={'display': 'none'}),

                                # Line Chart
                                dcc.Graph(
                                    className="top-right-panel-graph",
                                    id="selected-data",
                                    figure=dict(
                                        data=[dict(x=0, y=0)],
                                        layout=dict(
                                            paper_bgcolor="#F4F4F8",
                                            plot_bgcolor="#F4F4F8",
                                            autofill=True,
                                            margin=dict(t=75, r=50, b=100, l=50),
                                        ),
                                    ),
                                    style={'display': 'block'}
                                ),

                                # Control Chart
                                dcc.Graph(
                                    className="top-right-panel-graph",
                                    id="selected-control-data",
                                    figure=dict(
                                        data=[dict(x=0, y=0)],
                                        layout=dict(
                                            paper_bgcolor="#F4F4F8",
                                            plot_bgcolor="#F4F4F8",
                                            autofill=True,
                                            margin=dict(t=75, r=50, b=100, l=50),
                                        ),
                                    ),
                                    style={'display': 'none'}
                                ),

                                # State-space Chart
                                dcc.Graph(
                                    className="top-right-panel-graph",
                                    id="selected-statespace-data",
                                    figure=dict(
                                        data=[dict(x=0, y=0)],
                                        layout=dict(
                                            paper_bgcolor="#F4F4F8",
                                            plot_bgcolor="#F4F4F8",
                                            autofill=True,
                                            margin=dict(t=75, r=50, b=100, l=50),
                                        ),
                                    ),
                                    style={'display': 'none'}
                                ),

                            ],
                        ),
                    ],
                ),

                # Bottom Row
                html.Div(
                    id="bottom-row",
                    children=[
                        html.Div(className="hidden", children=[]),

                        # Controls container
                        html.Div(
                            id="control-container",
                            children=[
                                html.H4(children="Chart Display Options: "),
                                html.Div(className="slider-box", children=[
                                    html.P(className="control_title",
                                           children="Display outlying values by deviation amount:"),
                                    dcc.Slider(
                                        id='deviation-slider',
                                        value=1,
                                        min=1,
                                        max=3,
                                        step=1,
                                        marks={
                                            0: {'label': '0'},
                                            1: {'label': '1'},
                                            2: {'label': '2'},
                                            3: {'label': '3'}
                                        },
                                        tooltip={'placement': 'bottom', 'always_visible': True}
                                    ),
                                ]),
                                html.Div(className="slider-box", children=[
                                    html.P(className="control-title",
                                           children="Minimum amount of years for a trend to occur:"),
                                    dcc.Slider(
                                        id='trend-slider',
                                        value=10,
                                        min=2,
                                        max=20,
                                        step=1,
                                        marks={
                                            2: {'label': '2'},
                                            10: {'label': '10'},
                                            20: {'label': '20'}
                                        },
                                        tooltip={'placement': 'bottom', 'always_visible': True}
                                    ),
                                ]),
                                html.Div(className="control-box", children=[
                                    html.P(className="control-title", children="Select which markers to display:"),
                                    dcc.Checklist(
                                        id='flag-checklist',
                                        options=data_style_options[1:],
                                        value=list(data_styles.keys())[1:],
                                        labelStyle={'display': 'block'}
                                    ),
                                ]),
                                html.Div(children=[
                                    html.P(className="control-title", children="Display non-significant trend lines:"),
                                    dcc.Checklist(
                                        id='all-trend-checklist',
                                        options=[{'label': 'True',
                                                  'value': 'true'}],
                                        value=[],
                                        labelStyle={'display': 'inline'}
                                    ),
                                ]),
                            ],
                        )
                    ],
                    style={'display': 'none'}
                )
            ],
        ),
    ],
)
#######################################################################################################################

'''
Below are the Callbacks for updating elements when the user interacts with the dashboard.

update_year_slider_visibility - Updates the visibility of the year slider based on the spatial data type of the 
                                dataset. Datasets with county level data need a manual slider, while 
                                latitude/longitude centric datasets have an animated slider built in. 
                                
                  display_map - Updates the choropleth chart with the selected data.
                                
        display_selected_data - Updates the plot charts using the data selected on the choropleth chart.
                                
                 change_panel - Updates the panel containing the plots to display the currently selected plot.
                                
         update_data_selector - Updates the variable selector dropdown with the relevant variables present in the
                                chosen dataset.
'''


#######################################################################################################################
# Update Year Slider visibility, county based datasets need a manual slider.
@app.callback(
    Output(component_id='year-container', component_property='style'),
    [
        Input(component_id='dataframe-dropdown', component_property='value')
    ]
)
def update_year_slider_visibility(visibility_state):
    if data_json_dict[visibility_state]['space_type'] == 'latlong':
        return {'display': 'none'}


# Callback for Cloropleth figure
@app.callback(
    Output("county-choropleth", "figure"),
    [
        State("county-choropleth", "figure"),
        Input("data-dropdown", "value"),
        Input("dataframe-dropdown", "value"),
        Input("year-slider", "value"),
    ],
)
def display_map(figure, data_dropdown, dataframe_dropdown, year_slider):
    map_dat = select_dataframe(dataframe_dropdown)
    fig = plot_choropleth(
        figure, map_dat, dataframe_dropdown, data_dropdown, data_json_dict, COLOR_STYLES, year_slider, counties
    )

    return fig


# Update the other charts using the data selected in the choropleth.
@app.callback(
    [
        Output("selected-data", "figure"),
        Output('selected-control-data', 'figure'),
        Output('selected-statespace-data', 'figure'),
    ],
    [
        Input("county-choropleth", "selectedData"),
        Input("aggregation-dropdown", "value"),
        Input("data-dropdown", "value"),
        Input("dataframe-dropdown", "value"),
        Input("trend-slider", "value"),
        Input("deviation-slider", "value"),
        Input("flag-checklist", "value"),
        Input("all-trend-checklist", "value"),
        State("data-dropdown", "options"),
    ],
)
def display_selected_data(selected_data, chart_dropdown, data_dropdown, dataframe_dropdown, trend, deviation,
                          flag_checklist,
                          all_trends, opts):
    if selected_data is None:
        fig = default_chart(COLOR_STYLES)
        return fig, fig, fig

    chart_dat = select_dataframe(dataframe_dropdown)
    y_val = data_dropdown
    lat_val = data_json_dict[dataframe_dropdown]['space_keys'][0]
    lon_val = data_json_dict[dataframe_dropdown]['space_keys'][1]
    time_val = data_json_dict[dataframe_dropdown]['temporal_key']

    # find points from the selected data
    pts = selected_data["points"]

    the_label = [x['label'] for x in opts if x['value'] == data_dropdown]

    the_label = str(the_label).replace('[', '').replace(']', '')

    if data_json_dict[dataframe_dropdown]["space_type"] == 'latlong':

        lat_vals = [d["lat"] for d in pts if "lat" in d]
        lon_vals = [d["lon"] for d in pts if "lon" in d]

        vals = list(zip(lat_vals, lon_vals))

        # find the values for all selected counties for all years
        df = chart_dat.set_index([lat_val, lon_val], drop=False)

        sub_df = df.loc[df.index.isin(vals)]

    else:
        fips_val = data_json_dict[dataframe_dropdown]['space_keys'][2]

        # get a list of all locations selected
        vals = [d['location'] for d in pts if 'location' in d]

        # find the values for all selected counties for all years
        df = chart_dat.set_index([fips_val])
        sub_df = df.loc[df.index.isin(vals)]

    if sub_df.empty:
        fig = default_chart(COLOR_STYLES)
        return fig, fig, fig

    # select the data to plot
    ##########################################################################################
    if chart_dropdown == "mean":
        # summary by time
        summ_df = sub_df.groupby(time_val).mean().reset_index()

    if chart_dropdown == "median":
        # summary by time
        summ_df = sub_df.groupby(time_val).median().reset_index()

    if chart_dropdown == "min":
        # summary by time
        summ_df = sub_df.groupby(time_val).min().reset_index()

    if chart_dropdown == "max":
        # summary by time
        summ_df = sub_df.groupby(time_val).max().reset_index()
    ##########################################################################################

    # Line Chart Figure
    ##########################################################################################
    line_fig = plot_line(summ_df, time_val, y_val, COLOR_STYLES)

    fig_layout = style_figure(line_fig["layout"], the_label)
    ##########################################################################################

    # Control Chart Figure
    ##########################################################################################
    flag_dict = data_styles
    for fkey in flag_dict:
        if fkey not in flag_checklist:
            flag_dict[fkey][1] = 0
        else:
            flag_dict[fkey][1] = 1

    # Control Chart Dataframe Analysis and Plotting
    con_df, segments = control_sort(summ_df, y_val, time_val, trend, deviation, flag_dict)
    control_fig = plot_control(con_df, segments, y_val, time_val, all_trends, flag_dict)

    c_fig_layout = style_figure(control_fig["layout"], the_label)
    ##########################################################################################

    # State-Space Chart Figure
    ##########################################################################################
    statespace_fig = go.Figure()

    if chart_dropdown != "mean":
        # State-space specific Aggregation
        ###############################################################
        statespace_df = sub_df[[time_val, y_val, lat_val, lon_val]]

        # If we just did median on an even length dataset, we would find the average between the two middle values
        # which often does not exist in the dataset. Knock the maximum value off the top of the dataset and grab the
        # now middle value.
        if chart_dropdown == "median":
            if len(vals) % 2 == 0:
                sorted_ss_df = statespace_df.sort_values(by=[y_val], ascending=True)
                statespace_chart_df = sorted_ss_df.groupby(time_val).apply(
                    lambda x: x[x[y_val] == x[y_val].iloc[0:(int(len(x) - 1))].median()])
            else:
                statespace_chart_df = statespace_df.groupby(time_val).apply(lambda x: x[x[y_val] == x[y_val].median()])

        if chart_dropdown == "max":
            statespace_chart_df = statespace_df.groupby(time_val).apply(lambda x: x[x[y_val] == x[y_val].max()])

        if chart_dropdown == "min":
            statespace_chart_df = statespace_df.groupby(time_val).apply(lambda x: x[x[y_val] == x[y_val].min()])

        # State-space plotting
        ################################################################
        statespace_fig.add_trace(go.Scatter(x=statespace_chart_df[time_val],
                                            y=statespace_chart_df[lat_val],
                                            mode='lines',
                                            name="Latitude", ))
        statespace_fig.add_trace(go.Scatter(x=statespace_chart_df[time_val],
                                            y=statespace_chart_df[lon_val],
                                            mode='lines',
                                            name="Longitude", ))

    statespace_fig_layout = style_figure(statespace_fig["layout"], the_label)

    return line_fig, control_fig, statespace_fig


# Update display for graph panel
@app.callback([
    Output("selected-control-data", "style"),
    Output("selected-statespace-data", "style"),
    Output("selected-data", "style"),
    Output("bottom-row", "style"),
    Output("controls-text", "style"),
    Output("aggregation-dropdown", "options"),
    Output("aggregation-dropdown", "value")
],
    [
        Input("chart-swapper", "value"),
        Input("aggregation-dropdown", "value")
    ],
    prevent_initial_call=True
)
def change_panel(chart_swapper, aggregation_dropdown):
    agg_opts = [
        {
            "label": "Mean Value",
            "value": "mean",
        },
        {
            "label": "Median Value",
            "value": "median",
        },
        {
            "label": "Min. Value",
            "value": "min",
        },
        {
            "label": "Max. Value ",
            "value": "max",
        },
    ]

    agg_val = aggregation_dropdown

    # Return Values:
    ##################################
    # Control Chart Visibility
    # State-Space Chart Visibility
    # Line Chart Visibility
    # Bottom Row Visibility
    # Controls Visibility
    # Aggregation Dropdown Options
    # Aggregation Dropdown Value
    ##################################
    if chart_swapper == "controlchart":
        return {'display': 'block'}, \
               {'display': 'none'}, \
               {'display': 'none'}, \
               {'display': 'flex'}, \
               {'display': 'flex'}, \
               agg_opts, \
               agg_val
    elif chart_swapper == "statespace":
        agg_opts.pop(0)
        if agg_val == "mean":
            agg_val == "median"
        return {'display': 'none'}, \
               {'display': 'block'}, \
               {'display': 'none'}, \
               {'display': 'none'}, \
               {'display': 'none'}, \
               agg_opts, \
               agg_val
    elif chart_swapper == "linechart":
        return {'display': 'none'}, \
               {'display': 'none'}, \
               {'display': 'block'}, \
               {'display': 'none'}, \
               {'display': 'none'}, \
               agg_opts, \
               agg_val


# Update Data Selection Dropdown
@app.callback([
    Output("data-dropdown", "options"),
    Output("data-dropdown", "value")
],
    [
        Input("dataframe-dropdown", "value")
    ]
)
def update_data_selector(dataframe_dropdown):
    data_opts = []

    data_opts = data_json_dict[dataframe_dropdown]['fields']
    data_value = data_json_dict[dataframe_dropdown]['fields'][0]["value"]

    return data_opts, data_value


#######################################################################################################################


# Additional Helper Functions
#######################################################################################################################
# Style the chart figures for consistency
def style_figure(layout, title):
    fig_layout = layout

    # See plot.ly/python/reference
    fig_layout["yaxis"]["title"] = title
    fig_layout["xaxis"]["title"] = "Time (years)"
    fig_layout["yaxis"]["fixedrange"] = True
    fig_layout["xaxis"]["fixedrange"] = False
    fig_layout["hovermode"] = "closest"
    fig_layout["legend"] = dict(orientation="v")
    fig_layout["autosize"] = True
    fig_layout["paper_bgcolor"] = COLOR_STYLES["chart_background"]
    fig_layout["plot_bgcolor"] = COLOR_STYLES["chart_background"]
    fig_layout["font"]["color"] = COLOR_STYLES["font"]
    fig_layout["xaxis"]["tickfont"]["color"] = COLOR_STYLES["tick_font"]
    fig_layout["yaxis"]["tickfont"]["color"] = COLOR_STYLES["tick_font"]
    fig_layout["xaxis"]["gridcolor"] = COLOR_STYLES["chart_grid"]
    fig_layout["yaxis"]["gridcolor"] = COLOR_STYLES["chart_grid"]

    return fig_layout


# Function for selecting which dataframe to load when we need to load a dataframe into a callback.
#   - A line needs to be added here when adding a new dataframe to the dashboard.
def select_dataframe(dataframe_label):
    if dataframe_label == 'output.csv':
        return df_annual_climate
    elif dataframe_label == 'kestralModel.csv':
        return df_kestral_model
    elif dataframe_label == 'Carya_ovata.csv':
        return df_carya_ovata
    elif dataframe_label == 'carya_ovata_10km.csv':
        return df_carya_ovata_spacetime
    else:
        return pd.Dataframe()


#######################################################################################################################


# run the server
#######################################################################################################################
if __name__ == "__main__":
    app.run_server(debug=True)
