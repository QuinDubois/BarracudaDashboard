import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import scipy.stats as sp


#######################################################################################################################


# Creates a plotly figure based on the input DataFrame and parameters
#######################################################################################################################
def PlotChart(dataframe, segments, y_col, time_key, show_all, flags):

    fig = go.Figure()

    # Base line trace for the markers to sit on top of
    fig.add_trace(go.Scatter(x=dataframe[time_key],
                             y=dataframe[y_col],
                             mode='lines',
                             line_color=flags["base"][0],
                             showlegend=False))

    trace_count = 1  # Track which trace we are on

    printTrend = True

    print(dataframe.head(20))

    # loop to generate chart contents, do not include markers without a flag in the legend
    for d in flags:
        if flags[d][1] == 1:
            if (d == 'trending up' or d == 'trending down') and printTrend:

                fig = plot_trends(fig, dataframe, segments, y_col, time_key, show_all, trace_count, flags)

                printTrend = False

            # For all other data, we only use scatter plot markers.
            elif d not in ['trending up', 'trending down']:
                print(f"Markers {d}")
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
#######################################################################################################################


# Add trend lines to figure, plots trend lines of imported segments for the dataset.
#######################################################################################################################
def plot_trends(fig, dataframe, segments, y_col, time_key, show_all, trace_count, flags):
    # legend sentinels
    trend_up_legend = False
    trend_down_legend = False
    trend_insig_legend = False

    # Loop through each segment and determine whether or not to plot it's associated trend
    # based on our criteria. (show_all, trending flags, p value significance)
    for start_idx, end_idx in zip(segments[:-1], segments[1:]):
        segment = dataframe.iloc[start_idx:end_idx + 1, :]
        reg = sp.linregress(segment[time_key], segment[y_col])
        fit_color = flags['trending up'][0] if reg.slope > 0 else flags['trending down'][0]

        if show_all == ['true'] and reg.pvalue > 0.05:
            if (flags['trending up'][1] == 1 and reg.slope >= 0) or \
                    (flags['trending down'][1] == 1 and reg.slope < 0):
                trendfig = draw_trendline(segment, y_col, time_key, "rgb(150,150,150,1)")
                fig.add_trace(trendfig.data[1])

                # Show legend only once
                if not trend_insig_legend:
                    fig['data'][trace_count]['showlegend'] = True
                    fig['data'][trace_count]['name'] = "Non-Significant Trend"
                    trend_insig_legend = True

                trace_count += 1

        elif reg.pvalue <= 0.05:
            if (flags['trending up'][1] == 1 and reg.slope >= 0) or \
                    (flags['trending down'][1] == 1 and reg.slope < 0):
                trendfig = draw_trendline(segment, y_col, time_key, fit_color)
                fig.add_trace(trendfig.data[1])

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
