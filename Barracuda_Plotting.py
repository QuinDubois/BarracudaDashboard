# Barracuda Dashboard
# Authors: Alex Burnham, Quinlan Dubois
# Latest Revision: 0.1.1
# Latest Revision Date: 10/26/2022


import pandas as pd
from pandas.api.types import is_numeric_dtype
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import datetime
import statsmodels.api as sm


#######################################################################################################################

# Primary Plotting Functions
#######################################################################################################################

def default_chart(color_styles):
    fig = dict(
        data=[dict(x=0, y=0)],
        layout=dict(
            title="Click drag on the map to select counties",
            paper_bgcolor=color_styles["chart_background"],
            plot_bgcolor=color_styles["chart_background"],
            font=dict(color=color_styles["font"]),
            margin=dict(t=75, r=50, b=100, l=75),
        )
    )
    return fig


# Creates a simple line plot.
def plot_line(df, time_val, y_val, color_styles):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df[time_val],
        y=df[y_val],
        mode='lines',
        line={'color': color_styles['line_colors'][0]},
        showlegend=False
    ))

    return fig


# Creates a control chart plotly figure based on the input DataFrame and parameters
def plot_control(dataframe, segments, y_col, time_key, show_all, flags):

    fig = go.Figure()

    # Base line trace for the markers to sit on top of
    fig.add_trace(go.Scatter(x=dataframe[time_key],
                             y=dataframe[y_col],
                             mode='lines',
                             line_color=flags["base"][0],
                             showlegend=False))

    trace_count = 1  # Track which trace we are on

    print_trend = True

    # loop to generate chart contents, do not include markers without a flag in the legend
    for d in flags:
        if flags[d][1] == 1:
            if (d == 'trending up' or d == 'trending down') and print_trend:

                fig = plot_trends(fig, dataframe, segments, y_col, time_key, show_all, flags)

                print_trend = False

            # For all other data, we only use scatter plot markers.
            elif d not in ['trending up', 'trending down']:
                d_filter = d + ' mask'
                df = dataframe.loc[dataframe[d_filter] == 1]
                fig.add_trace(go.Scatter(x=df[time_key],
                                         y=df[y_col],
                                         mode='markers',
                                         name=d,
                                         marker_color=flags[d][0],
                                         showlegend=False if d == 'base' else True))
            trace_count += 1

    # Line indicating average value of the dataset
    fig.add_shape(type="line",
                  line_color='blue',
                  line_width=2,
                  line_dash='dot',
                  x0=0,
                  x1=1,
                  xref='paper',
                  y0=np.average(dataframe[y_col]),
                  y1=np.average(dataframe[y_col]),
                  yref='y'
                  )

    return fig


# Creates Choropleth figure
def plot_choropleth(figure, dataframe, dataframe_label, data_label, data_json, color_styles, years, counties):
    # write if else statement here:
    if data_json[dataframe_label]['space_type'] == 'latlong':
        # plot scatter box
        # find the max value
        dataframe['timeChar'] = dataframe[data_json[dataframe_label]['temporal_key']].astype('str')
        max_val = np.nanmax(dataframe[data_label])

        fig = px.scatter_mapbox(dataframe, lat=data_json[dataframe_label]['space_keys'][0],
                                lon=data_json[dataframe_label]['space_keys'][1],
                                color=data_label,
                                animation_frame='timeChar',
                                range_color=(0, max_val),
                                color_continuous_scale="Viridis",
                                opacity=0.8,
                                )
        fig.update_layout(mapbox_style="carto-darkmatter", mapbox_zoom=4.5, mapbox_center={"lat": 43, "lon": -74}, )
        fig.update_layout(margin={"r": 0, "t": 0, "l": 20, "b": 0},
                          plot_bgcolor=color_styles["chart_background"],
                          paper_bgcolor=color_styles["chart_background"],
                          font=dict(color=color_styles["font"]),
                          # dragmode="lasso",
                          )
        fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 200
        fig.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 200
        fig.layout.coloraxis.showscale = True
        fig.layout.sliders[0].pad.t = 10
        fig.layout.updatemenus[0].pad.t = 10
        fig.layout.height = 600

    else:
        # plot choropleth

        # Find max value for heat map bar
        max_val = max(dataframe[data_label])

        # filter by year
        map_dat_filtered = dataframe[(dataframe[data_json[dataframe_label]['temporal_key']] == years)]

        fig = px.choropleth_mapbox(map_dat_filtered, geojson=counties, locations='fips', color=data_label,
                                   color_continuous_scale="Viridis",
                                   # animation_frame="year",
                                   range_color=(0, max_val),
                                   mapbox_style="carto-darkmatter",
                                   zoom=2.9, center={"lat": 34.640033, "lon": -95.981758},
                                   opacity=0.9,
                                   labels={data_label: ' ', 'time': 'Year', 'Counties': 'County Code'}
                                   )

        fig.update_layout(margin={"r": 0, "t": 0, "l": 20, "b": 0},
                          geo_scope='usa',
                          # dragmode="lasso", #select
                          plot_bgcolor=color_styles["chart_background"],  # 1f2630 dark blue
                          paper_bgcolor=color_styles["chart_background"],  # 7fafdf light blue text
                          font=dict(color=color_styles["font"]),
                          height=600,
                          )

    return fig
#######################################################################################################################


# Add trend lines to figure, plots trend lines of imported segments for the dataset.
#######################################################################################################################
def plot_trends(fig, df_plot, segments, y_col, time_key, show_all, flags):

    for start_idx, end_idx in zip(segments[:-1], segments[1:]):
        segment = df_plot.iloc[start_idx:end_idx + 1, :].copy()

        if not is_numeric_dtype(segment[time_key]):
            segment['serial_time'] = [(d - datetime.datetime(1970, 1, 1)).days for d in segment[time_key]]
        else:
            segment['serial_time'] = segment[time_key]

        x = sm.add_constant(segment['serial_time'])
        model = sm.OLS(segment[y_col], x).fit()
        segment['fitted_values'] = model.fittedvalues

        fit_color = flags['trending up'][0] if model.params['serial_time'] > 0 \
            else flags['trending down'][0]

        trend_name = "Trending Up" if model.params['serial_time'] > 0 else "Trending Down"

        print_trend = False

        if show_all:
            print_trend = True
        else:
            if model.f_pvalue < 0.05:
                if flags['trending up'][1] == 1 and model.params['serial_time'] > 0:
                    print_trend = True
                elif flags['trending down'][1] == 1 and model.params['serial_time'] <= 0:
                    print_trend = True
                else:
                    pass
            else:
                pass

        if print_trend:
            fig.add_trace(go.Scatter(
                x=segment[time_key],
                y=segment['fitted_values'],
                mode='lines',
                line=dict(color=fit_color),
                name=trend_name,
            ))

    # Ensure duplicate legend items get filtered
    legend_names = set()
    fig.for_each_trace(
        lambda trace:
        trace.update(showlegend=False) if (trace.name in legend_names) else legend_names.add(trace.name)
    )

    return fig

#######################################################################################################################
