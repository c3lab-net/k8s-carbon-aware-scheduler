from flask_restful import Resource
from flask import request, redirect
from flask import render_template, make_response

from dashboard.helpers.postgres import *

class Table(Resource):
    def __init__(self):
        super().__init__()
        self.dbconn = get_db_connection()

    def get(self):
        headers = {'Content-Type': 'text/html'}

        all_jobs_table = self.get_table_data()

        jobId = request.args.get('jobId')
        if (jobId != None):
            job_info_table = self.get_job_info_table(jobId)
            return make_response(render_template("jobInfo.html", jobInfoHeadings=job_info_table['headers'], jobEvents=job_info_table['jobs']), 200, headers)
            '''
            return make_response(render_template("table.html", allJobsHeadings=all_jobs_table['headers'], jobs=all_jobs_table['jobs'], 
                             jobInfoHeadings=job_info_table['headers'], jobEvents=job_info_table['jobs']), 200, headers)
            '''
        
        return make_response(render_template("table.html", allJobsHeadings=all_jobs_table['headers'], jobs=all_jobs_table['jobs']), 200, headers)
    

    def get_job_info_table(self, jobId):
        cursor = self.dbconn.cursor()
        result = psql_execute_list(
                cursor,
                "SELECT q.name, p.time AT TIME ZONE 'America/Los_Angeles', p.event "
                    + "FROM jobhistory AS p INNER JOIN jobrequest AS q "
                    + "ON p.job_id = q.job_id WHERE q.job_id = '" + jobId + "'",
                fetch_result=True)
        columns = ["name", "time", "event"]
        df = postgres_to_dataframe(result, columns)
        df['time'] = df.apply(convert_time_format, axis=1)

        headers = tuple(df.columns.values)
        df_tuple = tuple(df.itertuples(index=False, name=None))
        table = {
            "headers": headers,
            "jobs": df_tuple
        }
        return table
        
        
    
    def get_table_data(self):
        cursor = self.dbconn.cursor()
        result = psql_execute_list(
                cursor,
                "SELECT p.job_id, q.name, p.time AT TIME ZONE 'America/Los_Angeles', "
                    + "p.origin, s.job_config FROM jobhistory as p "
                    + "INNER JOIN jobrequest AS q ON p.job_id = q.job_id "
                    + "INNER JOIN jobconfig AS s ON p.job_id = s.job_id",
                fetch_result=True)
        columns = ["id", "name", "time", "origin", "job_config"]
        df = postgres_to_dataframe(result, columns)
        df = df.drop_duplicates(subset=['id'])
        
        cores_col = df.apply(number_cores, axis=1)
        df = df.drop('job_config', axis=1)
        df.insert(loc=3, column="cores", value=cores_col)

        df['time'] = df.apply(convert_time_format, axis=1)
        df = df.sort_values(by=['time'], ascending=True)

        headers = tuple(df.columns.values)
        df_tuple = tuple(df.itertuples(index=False, name=None))
        table = {
            "headers": headers,
            "jobs": df_tuple
        }
        return table

def number_cores(row):
    return int(row['job_config']['spec']['template']['spec']['containers'][0]['resources']['requests']['cpu'])

def convert_time_format(row):
    return row['time'].date()


class CheckJob(Resource):
    def __init__(self):
        super().__init__()
        self.dbconn = get_db_connection()

    def get(self):
        cursor = self.dbconn.cursor()

        jobName = request.args.get('jobName')

        result = psql_execute_list(
                cursor,
                "SELECT COUNT(*) FROM jobrequest WHERE jobrequest.name = '" + jobName + "'",
                fetch_result=True)
        return result[0][0]
