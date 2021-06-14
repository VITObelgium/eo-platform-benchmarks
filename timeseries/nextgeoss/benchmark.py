import base64
import configparser
import json
import urllib.parse
from datetime import timedelta
from os.path import abspath, dirname, join
from typing import List

import geojson
import requests
from fire import Fire
from owslib.wps import WebProcessingService
from shapely.geometry import shape

from timeseries.histogram import create_histogram
from timeseries.timer import Timer

config = configparser.ConfigParser()
config.read('./config/dev.conf')


class BenchMark:

    def __init__(self, params):
        self.params = params

    def read_workflow_template(self, start: str, end: str, bbox: List[float], feature: dict):
        content = ''
        with open(self.params['wps']['template'], 'r') as template:
            content = ' '.join(template.readlines())
            content = content.replace('{{WORKFLOW_IDENTIFIER}}', self.params['wps']['workflow_id'])
            content = content.replace('{{PARAM_START}}', start)
            content = content.replace('{{PARAM_END}}', end)
            content = content.replace('{{PARAM_BBOX}}',
                                      ','.join(str(c) for c in bbox).replace(" ", "%20").replace(",", "%2C"))
            content = content.replace('{{PARAM_GEOMETRY}}', urllib.parse.quote(json.dumps(feature)))
            content = content.replace('{{PARAM_FILTER}}', self.params['wps']['filter'])
            template.close()
        return content

    def execute_workflow(self, start, end, feature):
        bounds = shape(feature["geometry"]).bounds
        wps_url = '{}?service=WPS&version=1.0.0&request=execute'.format(self.params['wps']['base'])
        workflow_data = self.read_workflow_template(start, end, bounds, feature)
        headers = {
            'Content-Type': 'text/xml',
            'Accept': 'text/xml'
        }
        resp = requests.post(wps_url, data=workflow_data, headers=headers)
        return 1

    def time_series(self):

        result_path = f"./results/nextgeoss"

        with open(f"{result_path}.txt", "w+") as file:
            file.write(f"Running benchmark on nextgeoss:\n\n")

            with open(
                    join(abspath(dirname(dirname(__file__))), 'nextgeoss', 'workflow', 'samples', 'sample.json')) as f:
                input_geojson = geojson.load(f)

            t = Timer()
            t.start()

            for i, f in enumerate(input_geojson.features):
                file.write(f"Feature {i + 1}:\n\n")
                temporal_extents = [["2021-06-05", "2021-06-10"]]
                for temporal_extent in temporal_extents:
                    file.write(f"{temporal_extent[0]} - {temporal_extent[1]}:\n\n")
                    try:
                        result = self.execute_workflow(start=temporal_extent[0], end=temporal_extent[1], feature=f)
                        file.write(f"{result}\n\n")
                    except Exception as e:
                        file.write(f"Failed to execute request: {e}\n\n")
                    file.write(f"Elapsed time for period: {timedelta(seconds=t.split_period())}\n\n")

                file.write(f"Elapsed time for feature: {timedelta(seconds=t.split_feature())}\n\n")

            timings = t.stop()

            file.write(f"Total elapsed time: {timedelta(seconds=timings['elapsed_time'])}\n\n")

            file.write("Statistics:\n\n")
            file.write(f"Min: {timedelta(seconds=timings['stats']['min'])}\n")
            file.write(f"Max: {timedelta(seconds=timings['stats']['max'])}\n")
            file.write(f"Mean: {timedelta(seconds=timings['stats']['mean'])}\n")
            file.write(f"StDev: {timedelta(seconds=timings['stats']['stdev'])}\n")

            create_histogram(result_path, timings['feature_timings'])


if __name__ == "__main__":
    Fire(BenchMark(config).time_series)
