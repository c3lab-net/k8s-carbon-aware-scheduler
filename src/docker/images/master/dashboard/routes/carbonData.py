from flask_restful import Resource
from flask import render_template, make_response, send_file
import json
import requests
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import sys
import matplotlib
from packaging import version
from io import BytesIO
from dateutil import parser

from dashboard.helpers.postgres import *

data = {"request": {"runtime": "01:30:00", "schedule": {"type": "onetime", "start_time": "2023-01-03T00:00:00+00:00", "interval": None, "max_delay": "10:00:00"}, "dataset": {"input_size_gb": 20.0, "output_size_gb": 12.0}, "original_location": "Azure:eastus", "candidate_providers": [], "candidate_locations": [{"id": "Azure:eastus", "latitude": None, "longitude": None}, {"id": "Azure:westus", "latitude": None, "longitude": None}], "carbon_data_source": "c3lab", "use_prediction": False, "desired_renewable_ratio": None, "optimize_carbon": True, "watts_per_core": 5.0, "core_count": 40.0, "use_new_optimization": True}, "original-region": "Azure:eastus", "optimal-regions": [{"rating": 129.343, "candidates": ["Azure:eastus"]}, {"rating": 131.372, "candidates": ["Azure:westus"]}], "isos": {"Azure:eastus": "watttime:PJM_ROANOKE", "Azure:westus": "watttime:CAISO_NORTH"}, "weighted-scores": {"Azure:eastus": 129.343, "Azure:westus": 131.372}, "raw-scores": {"Azure:eastus": {"energy-usage": 0.3, "carbon-emission-from-compute": 87.996, "carbon-emission-from-migration": 0, "carbon-emission": 87.996, "wan-network-usage": 32.0, "energy-usage-unit": "kWh", "carbon-emission-unit": "gCO2"}, "Azure:westus": {"energy-usage": 0.3, "carbon-emission-from-compute": 82.2043, "carbon-emission-from-migration": 11.8806, "carbon-emission": 94.0849, "wan-network-usage": 32.0, "energy-usage-unit": "kWh", "carbon-emission-unit": "gCO2"}}, "warnings": {}, "details": {"Azure:eastus": {"timings": [{"input_transfer_start": "2023-01-03T00:00:00+00:00", "input_transfer_duration": "00:00:00", "input_transfer_end": "2023-01-03T00:00:00+00:00", "compute_start": "2023-01-03T06:00:00+00:00", "compute_duration": "01:30:00", "compute_end": "2023-01-03T07:30:00+00:00", "output_transfer_start": "2023-01-03T07:30:00+00:00", "output_transfer_duration": "00:00:00", "output_transfer_end": "2023-01-03T07:30:00+00:00", "min_start": "2023-01-03T00:00:00+00:00", "max_end": "2023-01-03T11:30:00+00:00", "total_transfer_time": "00:00:00"}], "emission_rates": {"compute": {"2023-01-03T00:00:00.000Z": 0.0177859, "2023-01-03T01:00:00.000Z": 0.0183657, "2023-01-03T02:00:00.000Z": 0.0179324, "2023-01-03T03:00:00.000Z": 0.0173931, "2023-01-03T05:00:00.000Z": 0.0164709, "2023-01-03T06:00:00.000Z": 0.0162135, "2023-01-03T07:00:00.000Z": 0.0164597, "2023-01-03T08:00:00.000Z": 0.0164689, "2023-01-03T09:00:00.000Z": 0.0164241, "2023-01-03T10:00:00.000Z": 0.0166914, "2023-01-03T11:00:00.000Z": 0.0172355, "2023-01-03T12:00:00.000Z": 0.0176811, "2023-01-03T13:00:00.000Z": 0.0}, "transfer": {}, "transfer.network": {}, "transfer.endpoint": {}}, "emission_integral": {"compute": {"2023-01-03T00:00:00.000Z": 96.0439, "2023-01-03T01:00:00.000Z": 99.1747, "2023-01-03T02:00:00.000Z": 96.835, "2023-01-03T03:00:00.000Z": 93.9226, "2023-01-03T05:00:00.000Z": 88.9429, "2023-01-03T06:00:00.000Z": 87.5529, "2023-01-03T07:00:00.000Z": 88.8824, "2023-01-03T08:00:00.000Z": 88.9319, "2023-01-03T09:00:00.000Z": 88.6902, "2023-01-03T10:00:00.000Z": 90.1334, "2023-01-03T11:00:00.000Z": 93.0715, "2023-01-03T12:00:00.000Z": 95.4778, "2023-01-03T13:00:00.000Z": 0.0}, "transfer": {}, "transfer.network": {}, "transfer.endpoint": {}}}, "Azure:westus": {"timings": [{"input_transfer_start": "2023-01-03T04:38:09+00:00", "input_transfer_duration": "00:21:51", "input_transfer_end": "2023-01-03T05:00:00+00:00", "compute_start": "2023-01-03T05:00:00+00:00", "compute_duration": "01:30:00", "compute_end": "2023-01-03T06:30:00+00:00", "output_transfer_start": "2023-01-03T06:46:53+00:00", "output_transfer_duration": "00:13:07", "output_transfer_end": "2023-01-03T07:00:00+00:00", "min_start": "2023-01-03T00:00:00+00:00", "max_end": "2023-01-03T11:30:00+00:00", "total_transfer_time": "00:34:58"}], "emission_rates": {"compute": {"2023-01-03T00:00:00.000Z": 0.0163287, "2023-01-03T01:00:00.000Z": 0.0169694, "2023-01-03T02:00:00.000Z": 0.0163043, "2023-01-03T03:00:00.000Z": 0.0165721, "2023-01-03T04:00:00.000Z": 0.0156701, "2023-01-03T05:00:00.000Z": 0.0151862, "2023-01-03T06:00:00.000Z": 0.0152968, "2023-01-03T07:00:00.000Z": 0.0164424, "2023-01-03T08:00:00.000Z": 0.0165161, "2023-01-03T09:00:00.000Z": 0.0166436, "2023-01-03T10:00:00.000Z": 0.0165509, "2023-01-03T11:00:00.000Z": 0.0169118, "2023-01-03T12:00:00.000Z": 0.0}, "transfer": {"2023-01-03T00:00:00.000Z": 0.00885501, "2023-01-03T01:00:00.000Z": 0.00913387, "2023-01-03T02:00:00.000Z": 0.00884858, "2023-01-03T03:00:00.000Z": 0.00878915, "2023-01-03T04:00:00.000Z": 0.00417408, "2023-01-03T05:00:00.000Z": 0.00820247, "2023-01-03T06:00:00.000Z": 0.00814278, "2023-01-03T07:00:00.000Z": 0.0084643, "2023-01-03T08:00:00.000Z": 0.00847363, "2023-01-03T09:00:00.000Z": 0.00850344, "2023-01-03T10:00:00.000Z": 0.00854352, "2023-01-03T11:00:00.000Z": 0.00878699, "2023-01-03T12:00:00.000Z": 0.00445929, "2023-01-03T13:00:00.000Z": 0.0}, "transfer.network": {"2023-01-03T00:00:00.000Z": 0.000667505, "2023-01-03T01:00:00.000Z": 0.000653451, "2023-01-03T02:00:00.000Z": 0.000631762, "2023-01-03T03:00:00.000Z": 0.000637505, "2023-01-03T04:00:00.000Z": 0.000413255, "2023-01-03T05:00:00.000Z": 0.000604776, "2023-01-03T06:00:00.000Z": 0.00058032, "2023-01-03T07:00:00.000Z": 0.000567792, "2023-01-03T08:00:00.000Z": 0.000557244, "2023-01-03T09:00:00.000Z": 0.000567195, "2023-01-03T10:00:00.000Z": 0.000565383, "2023-01-03T11:00:00.000Z": 0.000591648, "2023-01-03T12:00:00.000Z": 0.000215833, "2023-01-03T13:00:00.000Z": 0.0}, "transfer.endpoint": {"2023-01-03T00:00:00.000Z": 0.00818751, "2023-01-03T01:00:00.000Z": 0.00848042, "2023-01-03T02:00:00.000Z": 0.00821682, "2023-01-03T03:00:00.000Z": 0.00815164, "2023-01-03T04:00:00.000Z": 0.00376082, "2023-01-03T05:00:00.000Z": 0.0075977, "2023-01-03T06:00:00.000Z": 0.00756246, "2023-01-03T07:00:00.000Z": 0.00789651, "2023-01-03T08:00:00.000Z": 0.00791638, "2023-01-03T09:00:00.000Z": 0.00793624, "2023-01-03T10:00:00.000Z": 0.00797814, "2023-01-03T11:00:00.000Z": 0.00819534, "2023-01-03T12:00:00.000Z": 0.00424346, "2023-01-03T13:00:00.000Z": 0.0}}, "emission_integral": {"compute": {"2023-01-03T00:00:00.000Z": 88.175, "2023-01-03T01:00:00.000Z": 91.6348, "2023-01-03T02:00:00.000Z": 88.0433, "2023-01-03T03:00:00.000Z": 89.4894, "2023-01-03T04:00:00.000Z": 84.6185, "2023-01-03T05:00:00.000Z": 82.0053, "2023-01-03T06:00:00.000Z": 82.6025, "2023-01-03T07:00:00.000Z": 88.789, "2023-01-03T08:00:00.000Z": 89.1867, "2023-01-03T09:00:00.000Z": 89.8752, "2023-01-03T10:00:00.000Z": 89.3747, "2023-01-03T11:00:00.000Z": 91.3237, "2023-01-03T12:00:00.000Z": 0.0}, "transfer": {"2023-01-03T00:00:00.000Z": 18.5778, "2023-01-03T01:00:00.000Z": 19.1629, "2023-01-03T02:00:00.000Z": 18.5643, "2023-01-03T03:00:00.000Z": 18.4396, "2023-01-03T04:00:00.000Z": 8.75721, "2023-01-03T05:00:00.000Z": 17.2088, "2023-01-03T06:00:00.000Z": 17.0836, "2023-01-03T07:00:00.000Z": 17.7581, "2023-01-03T08:00:00.000Z": 17.7777, "2023-01-03T09:00:00.000Z": 17.8402, "2023-01-03T10:00:00.000Z": 17.9243, "2023-01-03T11:00:00.000Z": 18.4351, "2023-01-03T12:00:00.000Z": 9.35559, "2023-01-03T13:00:00.000Z": 0.0}, "transfer.network": {"2023-01-03T00:00:00.000Z": 1.40043, "2023-01-03T01:00:00.000Z": 1.37094, "2023-01-03T02:00:00.000Z": 1.32544, "2023-01-03T03:00:00.000Z": 1.33749, "2023-01-03T04:00:00.000Z": 0.867008, "2023-01-03T05:00:00.000Z": 1.26882, "2023-01-03T06:00:00.000Z": 1.21751, "2023-01-03T07:00:00.000Z": 1.19123, "2023-01-03T08:00:00.000Z": 1.1691, "2023-01-03T09:00:00.000Z": 1.18998, "2023-01-03T10:00:00.000Z": 1.18617, "2023-01-03T11:00:00.000Z": 1.24128, "2023-01-03T12:00:00.000Z": 0.452818, "2023-01-03T13:00:00.000Z": 0.0}, "transfer.endpoint": {"2023-01-03T00:00:00.000Z": 17.1774, "2023-01-03T01:00:00.000Z": 17.7919, "2023-01-03T02:00:00.000Z": 17.2389, "2023-01-03T03:00:00.000Z": 17.1022, "2023-01-03T04:00:00.000Z": 7.89021, "2023-01-03T05:00:00.000Z": 15.94, "2023-01-03T06:00:00.000Z": 15.866, "2023-01-03T07:00:00.000Z": 16.5669, "2023-01-03T08:00:00.000Z": 16.6086, "2023-01-03T09:00:00.000Z": 16.6502, "2023-01-03T10:00:00.000Z": 16.7381, "2023-01-03T11:00:00.000Z": 17.1938, "2023-01-03T12:00:00.000Z": 8.90277, "2023-01-03T13:00:00.000Z": 0.0}}}}}



# Metadata

metadata = {
    'emission_rates': {
        'ylabel': 'gCO2/s',
        'title': 'Instantaneous emission rates'
    },
    'emission_integral': {
        'ylabel': 'gCO2',
        'title': 'Emission integral over its duration'
    },
}

class CarbonData(Resource):

    def __init__(self):
        super().__init__()
        self.dbconn = get_db_connection()

    def get(self):
        headers = {'Content-Type': 'text/html'}
        return make_response(render_template("carbonData.html"), 200, headers)
    
class CarbonDataFig(Resource):
    def __init__(self):
        super().__init__()
        self.dbconn = get_db_connection()

    def get(self):
        return self.getCarbonDataJSON();
    
    def getCarbonDataJSON(self):
        res = {}

        series_names = ["emission_rates", "emission_integral"]
        for series_name in series_names:
        # # Get max value for y-axis
        # max_y_value = get_max_value(data['details'], series_name)

            res[series_name] = {}
            for region in data['details']:
                res[series_name][region] = {}
                compute_data = data["details"][region][series_name]["compute"]
                transfer_data = data["details"][region][series_name]["transfer"]
                timings = data["details"][region]['timings'][0] # Assume single occurence per job
                min_start = datetime.fromisoformat(timings['min_start'])
                max_end = datetime.fromisoformat(timings['max_end'])

                # Convert timestamp strings to datetime objects
                compute_df = create_dataframe_for_plotting(compute_data, min_start, max_end)
                transfer_df = create_dataframe_for_plotting(transfer_data, min_start, max_end)

                # compute_df['Timestamp'] = compute_df['Timestamp'].apply(lambda x: x.strftime("%m-%d %H"))
                # if not transfer_df.empty:
                    # transfer_df['Timestamp'] = transfer_df['Timestamp'].apply(lambda x: x.strftime("%m-%d %H"))
                
                res[series_name][region]["compute_df"] = json.loads(compute_df.to_json())
                res[series_name][region]["transfer_df"] = json.loads(transfer_df.to_json())

                timings_df = pd.DataFrame(list(timings.items()), columns=["Label", "Timestamp"])
                timings_df["Timestamp"] = pd.to_datetime(timings_df["Timestamp"])
                timings_df = timings_df.set_index("Label");
                res[series_name][region]["timings_df"] = json.loads(timings_df.to_json(orient="index"))

        return res



def get_max_value(data_details: dict, series_name: str):
    max_value = 0
    for region in data_details:
        compute_data = data_details[region][series_name]["compute"]
        transfer_data = data_details[region][series_name]["transfer"]
        max_value = max(max_value, max(compute_data.values(), default=0), max(transfer_data.values(), default=0))
    return max_value

def resample_timeseries(df: pd.DataFrame, interval: str):
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df.set_index("Timestamp", inplace=True)
    df_resampled = df.resample(interval).ffill().reset_index()
    return df_resampled

def create_dataframe_for_plotting(timeseries: dict[str, float], min_start: datetime, max_end: datetime) -> pd.DataFrame:
    """Convert a time series data to a dataframe, while removing out of bound timestamps.
    
        Args:
            timeseries: A dictionary of timestamp strings and values.
            min_start: The minimum cutoff time for the timeseries.
            max_end: The maximum cutoff time for the timeseries.
    """

    timeseries_in_datatime = {datetime.strptime(key, "%Y-%m-%dT%H:%M:%S.%f%z"): value for key, value in timeseries.items()}
    df = pd.DataFrame(list(timeseries_in_datatime.items()), columns=["Timestamp", "Value"])

    if df.empty:
        return df
    resampled = resample_timeseries(df, "30s")
    mask = (resampled["Timestamp"] >= pd.to_datetime(min_start)) & (resampled["Timestamp"] <= pd.to_datetime(max_end))
    return resampled[mask]