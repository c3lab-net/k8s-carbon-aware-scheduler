from flask import render_template, make_response
from flask import request
from flask import jsonify
from flask import Response
from flask_restful import Resource
import matplotlib
import matplotlib.pyplot as plt
from datetime import datetime
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import plotly
import plotly.express as px
import json
import numpy as np
import pandas as pd

# from job_scheduler.api.helpers.postgres import *

from dashboard.helpers.postgres import *


matplotlib.use('agg')

class Dashboard(Resource):
    def __init__(self):
        super().__init__()
        self.dbconn = get_db_connection()
    
    def get(self):
        graphs = self.get_number_of_active_jobs_cores()
        return self.make_response_graphs(graphs)
    
    def make_response_graphs(self, graphs):
        graphJSON_num_jobs = graphs["num_jobs_graph"]
        graphJSON_num_cores = graphs["num_cores_graph"]
        headers = {'Content-Type': 'text/html'}
        return make_response(render_template('dashboard.html', graphJSON_num_jobs=graphJSON_num_jobs, graphJSON_num_cores=graphJSON_num_cores), 200, headers)
    
    
    def post(self):
        data = request.get_json()
        subject = data['subject']
        filter = data['filter']

        if filter == 'ActiveJobs':
            graphs = self.get_number_of_active_jobs_cores()
            if subject == 'jobs':
                return graphs["num_jobs_graph"]
            else:
                return graphs["num_cores_graph"]
            
        if subject == 'jobs':
            return self.get_jobs_by_status_graph(filter)
        else:
            return self.get_cores_by_status_graph(filter)
    
    def get_cores_by_status_graph(self, filter):
        cores = self.get_cores_by_status_df(filter)
        cores_sampled = cores.resample('H', on='time').sum().cumsum()

        num_cores_fig, num_cores_ax = plt.subplots(figsize=(8, 6))
        x_num_cores = cores_sampled.index
        y_num_cores = cores_sampled['num_cores']
        num_cores_df = pd.DataFrame({'Time': x_num_cores, '# of Cores': y_num_cores})
        num_cores_fig = px.line(num_cores_df, x='Time', y='# of Cores', title='Cores', width=1500)
        num_cores_fig.update_layout(title_x=0.5)
        num_cores_fig.update_xaxes(rangeslider_visible=True)

        graphJSON_num_cores = json.dumps(num_cores_fig, cls=plotly.utils.PlotlyJSONEncoder)

        return graphJSON_num_cores
    
    def get_cores_by_status_df(self, status):
        cursor = self.dbconn.cursor()
        result = psql_execute_list(
                cursor,
                "SELECT jobhistory.time AT TIME ZONE 'America/Los_Angeles', jobconfig.job_config "
                    + "FROM jobhistory INNER JOIN jobconfig ON jobhistory.job_id = jobconfig.job_id WHERE jobhistory.event = \'" + status + "\'",
                fetch_result=True)
        
        columns = ["time", "job_config"]
        df = postgres_to_dataframe(result, columns)
        num_cores = np.empty(len(df.index))
        for i, job_config in df['job_config'].items():
            numCoresForJob = int(job_config['spec']['template']['spec']['containers'][0]['resources']['requests']['cpu'])
            num_cores[i] = numCoresForJob
        df["num_cores"] = num_cores
        return df
    
    
    def get_jobs_by_status_graph(self, filter):
        jobs = self.get_jobs_by_status_df(filter)
        jobs_sampled = jobs.resample('H', on='time').sum().cumsum()

        num_jobs_fig, num_jobs_ax = plt.subplots(figsize=(8, 6))
        x_num_jobs = jobs_sampled.index
        y_num_jobs = jobs_sampled['num_jobs']
        num_jobs_df = pd.DataFrame({'Time': x_num_jobs, '# of Jobs': y_num_jobs})
        num_jobs_fig = px.line(num_jobs_df, x='Time' ,y='# of Jobs', title='Jobs', width=1500)
        num_jobs_fig.update_layout(title_x=0.5)
        num_jobs_fig.update_xaxes(rangeslider_visible=True)

        graphJSON_num_jobs = json.dumps(num_jobs_fig, cls=plotly.utils.PlotlyJSONEncoder)

        return graphJSON_num_jobs
    
    def get_jobs_by_status_df(self, status):
        cursor = self.dbconn.cursor()
        result = psql_execute_list(
                cursor,
                "SELECT jobhistory.job_id, jobhistory.event, jobhistory.time AT TIME ZONE 'America/Los_Angeles' FROM public.jobhistory " 
                    + "WHERE event = \'" + status + "\'",
                fetch_result=True)
        columns = ["job_id", "event", "time"]
        df = postgres_to_dataframe(result, columns)
        num_jobs = np.ones(len(df.index))
        df['num_jobs'] = num_jobs
        return df
    

    def get_number_of_active_jobs_cores(self):
        job_history_configs = self.get_all_jobs_history_and_config_df()

        jobs_sampled = job_history_configs.resample('H', on='time').sum().cumsum()

        num_jobs_fig, num_jobs_ax = plt.subplots(figsize=(8, 6))
        x_num_jobs = jobs_sampled.index
        y_num_jobs = jobs_sampled['job_added']
        num_jobs_df = pd.DataFrame({'Time': x_num_jobs, '# of Jobs': y_num_jobs})
        num_jobs_fig = px.line(num_jobs_df,x='Time',y='# of Jobs', title='Jobs', width=1500)
        num_jobs_fig.update_layout(title_x=0.5)
        num_jobs_fig.update_xaxes(rangeslider_visible=True)

        num_cores_fig, num_cores_ax = plt.subplots(figsize=(8, 6))
        x_num_cores = jobs_sampled.index
        y_num_cores = jobs_sampled['cores_added']
        num_cores_df = pd.DataFrame({'Time': x_num_cores, '# of Cores': y_num_cores})
        num_cores_fig = px.line(num_cores_df,x='Time',y='# of Cores', title='Cores', width=1500)
        num_cores_fig.update_layout(title_x=0.5)
        num_cores_fig.update_xaxes(rangeslider_visible=True)
        

        graphJSON_num_jobs = json.dumps(num_jobs_fig, cls=plotly.utils.PlotlyJSONEncoder)
        graphJSON_num_cores = json.dumps(num_cores_fig, cls=plotly.utils.PlotlyJSONEncoder)

        graphs = {
            "num_jobs_graph": graphJSON_num_jobs,
            "num_cores_graph": graphJSON_num_cores
        }
        return graphs
    
    def get_all_jobs_history_and_config_df(self):
        cursor = self.dbconn.cursor()
        result = psql_execute_list(
                cursor,
                "SELECT jobhistory.event, jobhistory.time AT TIME ZONE 'America/Los_Angeles', jobconfig.job_config "
                    + "FROM jobhistory INNER JOIN jobconfig ON jobhistory.job_id = jobconfig.job_id",
                fetch_result=True)
        columns = ["event", "time", "job_config"]
        df = postgres_to_dataframe(result, columns)
        
        df['job_added'] = df.apply(add_number_jobs, axis=1)
        df['cores_added'] = df.apply(add_number_cores, axis=1)
        testdf = df[['time', 'event', 'job_added', 'cores_added']]
        df = df.drop('job_config', axis=1)
        return df


def add_number_jobs(row):
    if row['event'] == 'Created':
        val = 1
    elif row['event'] == 'Completed' or row['event'] == 'Failed': # include failure jobs
        val = -1
    else:
        val = 0
    return val

def add_number_cores(row):
    number_of_cores = int(row['job_config']['spec']['template']['spec']['containers'][0]['resources']['requests']['cpu'])
    if row['event'] == 'Created':
        val = number_of_cores
    elif row['event'] == 'Completed':
        val = 0 - number_of_cores
    else:
        val = 0
    return val
