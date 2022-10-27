# Barracuda Dashboard
# Authors: Alex Burnham, Quinlan Dubois
# Latest Revision: 0.1.1
# Latest Revision Date: 10/26/2022


import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import scipy.stats as sp


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

                fig = plot_trends(fig, dataframe, segments, y_col, time_key, show_all, trace_count, flags)

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
        max_val = np.nanmax(dataframe[data_label])

        fig = px.scatter_mapbox(dataframe, lat=data_json[dataframe_label]['space_keys'][0],
                                lon=data_json[dataframe_label]['space_keys'][1],
                                color=data_label,
                                animation_frame=data_json[dataframe_label]['temporal_key'],
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
def plot_trends(fig, dataframe, segments, y_col, time_key, show_all, trace_count, flags):
    # legend sentinels
    trend_up_legend = False
    trend_down_legend = False
    trend_insig_legend = False

    # Loop through each segment and determine regardless of whether we plot it's associated trend or not,
    # based on our criteria. (show_all, trending flags, p value significance)
    for start_idx, end_idx in zip(segments[:-1], segments[1:]):
        segment = dataframe.iloc[start_idx:end_idx + 1, :]
        reg = sp.linregress(segment[time_key], segment[y_col])
        fit_color = flags['trending up'][0] if reg.slope > 0 else flags['trending down'][0]

        if show_all == ['true'] and reg.pvalue > 0.05:
            if (flags['trending up'][1] == 1 and reg.slope >= 0) or \
                    (flags['trending down'][1] == 1 and reg.slope < 0):
                trend_fig = draw_trendline(segment, y_col, time_key, "rgb(150,150,150,1)")
                fig.add_trace(trend_fig.data[1])

                # Show legend only once
                if not trend_insig_legend:
                    fig['data'][trace_count]['showlegend'] = True
                    fig['data'][trace_count]['name'] = "Non-Significant Trend"
                    trend_insig_legend = True

                trace_count += 1

        elif reg.pvalue <= 0.05:
            if (flags['trending up'][1] == 1 and reg.slope >= 0) or \
                    (flags['trending down'][1] == 1 and reg.slope < 0):
                trend_fig = draw_trendline(segment, y_col, time_key, fit_color)
                fig.add_trace(trend_fig.data[1])

                # Show legend only once
                if reg.slope >= 0 and not trend_up_legend:
                    fig['data'][trace_count]['showlegend'] = True
                    fig['data'][trace_count]['name'] = "Trending Up"
                    trend_up_legend = True
                elif reg.slope < 0 and not trend_down_legend:
                    fig['data'][trace_count]['showlegend'] = True
                    fig['data'][trace_count]['name'] = "Trending Down"
                    trend_down_legend = True

                trace_count += 1

    return fig

#######################################################################################################################


# Helper functions
#######################################################################################################################

# Draw a single trend line
def draw_trendline(segment, y_col, time_key, fit_color):
    return px.scatter(x=segment[time_key],
                      y=segment[y_col],
                      trendline='ols',
                      trendline_color_override=fit_color,
                      )

#######################################################################################################################
