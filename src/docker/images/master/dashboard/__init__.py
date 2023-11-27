from flask import Flask
from flask_restful import Api
from dashboard.routes.dashboard import Dashboard
from dashboard.routes.table import Table, CheckJob
from dashboard.routes.carbonData import CarbonData, CarbonDataFig

import sys
import pprint

app = Flask(__name__)
api = Api(app)

pprint.pprint(sys.path)

'''def create_app():
    app = Flask(__name__)
    api = Api(app)

    from dashboard.routes.dashboard import Dashboard
    api.add_resource(Dashboard, '/')'''


api.add_resource(Dashboard, '/dashboard')
api.add_resource(Table, '/table')
api.add_resource(CheckJob, '/checkJob')
api.add_resource(CarbonData, '/carbonData')
api.add_resource(CarbonDataFig, '/carbonDataFig')

if __name__ == "__main__":
    app.run(debug=True)