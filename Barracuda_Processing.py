# Barracuda Dashboard
# Authors: Alex Burnham, Quinlan Dubois
# Latest Revision: 0.1.1
# Latest Revision Date: 10/26/2022


import pandas as pd
import numpy as np

#######################################################################################################################


# Flag records in the input dataset with the input flags
#######################################################################################################################
def control_sort(dataframe, y_col, time_key, trend_size, deviation, flags):
    avg = np.average(dataframe[y_col])          # average of the dataset
    std = np.std(dataframe[y_col])              # standard deviation of the dataset
    std_co = deviation                          # coefficient to determine the minimum deviations we care about
    relevant_bounds_idx = []                    # an index of bounds for the segments of the trend chart

    # Main process loop, for every enabled flag, mark the relevant data.
    for key in flags:
        if flags[key][1] == 1:
            if key == 'above average':
                dataframe[key+' mask'] = np.where(dataframe[y_col].values >= avg, 1, 0)

            if key == 'below average':
                dataframe[key + ' mask'] = np.where(dataframe[y_col].values < avg, 1, 0)

            if key == 'deviation above':
                dataframe[key + ' mask'] = np.where(dataframe[y_col].values >= avg + (std*std_co), 1, 0)

            if key == 'deviation below':
                dataframe[key + ' mask'] = np.where(dataframe[y_col].values < avg - (std * std_co), 1, 0)

            if key == 'trending up' or key == 'trending down':
                relevant_bounds_idx = trend_by_slope(dataframe, y_col, time_key, trend_size)

    return dataframe, relevant_bounds_idx
#######################################################################################################################


# Trend detection, runs cumulative linear slope calculations over the dataset, marking segments that constitute trends
# based on our input data
#######################################################################################################################
def trend_by_slope(dataframe, y_col, time_key, t_size):
    min_change = t_size
    curr_changes = 0
    last_sign = 1
    last_change_idx = 0
    bounds_idx = [0]
    cumulative_slope = [0]

    dataframe['row'] = np.arange(len(dataframe))

    for i in range(1, dataframe.shape[0]):
        segment = dataframe.iloc[0:i+1, :]

        slope = calc_slope(segment, time_key, y_col)
        cumulative_slope.append(slope)

        # compare the current cumulative slope with the previous, and keep track of whether it increased or decreased
        # as well as how many times it has changed in that direction, and where it last changed direction
        if abs(cumulative_slope[i]) < abs(cumulative_slope[i-1]):
            if last_sign == 1:
                curr_changes = 0
            if curr_changes == 0:
                last_change_idx = i
            curr_changes += 1
            last_sign = -1

        elif abs(cumulative_slope[i]) > abs(cumulative_slope[i-1]):
            if last_sign == -1:
                curr_changes = 0
            if curr_changes == 0:
                last_change_idx = i
            curr_changes += 1
            last_sign = 1

        # if we meet the minimum amount of times the slope changes in a direction, mark the last time it changed
        # and reset the change counter
        if curr_changes == min_change:
            curr_changes = 0
            bounds_idx.append(last_change_idx)

    # add the last point in the dataset to the bounds just to ensure we encapsulate all points
    bounds_idx.append(dataframe.shape[0]-1)

    return bounds_idx
#######################################################################################################################


# Helper Functions
#######################################################################################################################
# helper function to calculate slope of a dataframe
def calc_slope(df, time_key, y_val):
    slope = np.polyfit(df['row'], df[y_val], 1)
    return slope[0]
