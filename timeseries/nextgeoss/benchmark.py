import configparser
import json
import logging
import xml.etree.ElementTree as ET
from datetime import timedelta
from os.path import abspath, dirname, join
from time import sleep
from typing import List

import geojson
import requests
from fire import Fire
from shapely.geometry import shape

import re

import os

from timeseries.histogram import create_histogram
from timeseries.timer import Timer

config = configparser.ConfigParser()
config.read('./config/prod_onda.conf')

result_path = config['wps']['results']

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s [%(levelname)s] %(message)s',
                    handlers=[
                        logging.FileHandler(f'{result_path}.txt',  mode='w'),
                        logging.StreamHandler()
                    ]
                    )


class BenchMark:

    def __init__(self, params):
        self.params = params
        self.proxies = {}
        if 'proxies' in params:
            self.proxies = {
                'http': params['proxies']['http']
            }

    def read_workflow_template(self, start: str, end: str, bbox: List[float], feature: dict):
        content = ''
        with open(self.params['wps']['template'], 'r') as template:
            content = ' '.join(template.readlines())
            content = content.replace('{{WORKFLOW_IDENTIFIER}}', self.params['wps']['workflow_id'])
            content = content.replace('{{PARAM_START}}', start)
            content = content.replace('{{PARAM_END}}', end)
            content = content.replace('{{PARAM_BBOX_LOWER}}',
                                      ' '.join(str(c) for c in bbox[:2]))
            content = content.replace('{{PARAM_BBOX_UPPER}}',
                                      ' '.join(str(c) for c in bbox[2:]))
            content = content.replace('{{PARAM_GEOMETRY}}', json.dumps(feature))
            content = content.replace('{{PARAM_FILTER}}', self.params['wps']['filter'])
            template.close()
        return content

    def execute_workflow(self, start, end, feature):
        bounds = shape(feature["geometry"]).bounds
        wps_url = '{}/WebProcessingService?service=WPS&version=1.0.0&request=execute'.format(self.params['wps']['base'])
        workflow_data = self.read_workflow_template(start, end, bounds, feature)
        headers = {
            'Content-Type': 'text/xml',
            'Accept': 'text/xml'
        }
        resp = requests.post(wps_url, data=workflow_data, headers=headers, proxies=self.proxies)
        return self.get_xml(resp.text)

    def get_xml(self, text):
        return ET.fromstring(text)

    def get_status(self, doc):
        url = re.sub(r'http:.*wps', self.params['wps']['base'], doc.attrib['statusLocation'])
        status_txt = requests.get(url, proxies=self.proxies).text
        resp = self.get_xml(status_txt)
        if 'ProcessFailed' in resp[1][0].tag:
            return 'FAILED'
        elif 'ProcessSucceeded' in resp[1][0].tag:
            return 'DONE'
        return 'RUNNING'

    def download_results(self, doc):
        # Get status XML
        url = re.sub(r'http:.*wps', self.params['wps']['base'], doc.attrib['statusLocation'])
        status_txt = requests.get(url, proxies=self.proxies).text
        resp = self.get_xml(status_txt)

        # Download metalink
        metalink_url = resp[2][0][2][0][0].get('href')
        metalink_txt = requests.get(metalink_url, proxies=self.proxies).text
        metalink_resp = self.get_xml(metalink_txt)

        # Download results
        result = list()
        for file in metalink_resp[0]:
            date_result = requests.get(file[0][0].text, proxies=self.proxies).json()
            result.append({
                'date': date_result['date'][0],
                'stat': date_result['stats'][0],
                'time': date_result['time']
            })
        return sorted(result, key=lambda x:x['date'])

    def time_series(self):
        logging.info(f'Running benchmark on nextgeoss:')
        with open(os.path.join(abspath(dirname(dirname(__file__))), config['wps']['samples'])) as f:
            input_geojson = geojson.load(f)

        t = Timer()
        t.start()

        logging.info(f'Benchmarking with {len(input_geojson.features)} features')
        for i, f in enumerate(input_geojson.features):
            logging.info(f'Feature {i + 1}:')
            temporal_extents = [['2019-01-01', '2019-10-31']]
            for temporal_extent in temporal_extents:

                # Execute workflow
                logging.info(f'{temporal_extent[0]} - {temporal_extent[1]}:')
                try:
                    result = self.execute_workflow(start=temporal_extent[0], end=temporal_extent[1], feature=f)
                    done = False
                    while not done:
                        sleep(5)
                        status = self.get_status(result)
                        logging.debug(f'Checking status for feature {i + 1} - {status}')
                        done = status in ['DONE', 'FAILED']
                except Exception as e:
                    logging.error(f"Failed to execute request: {e}")
                logging.info(f'Elapsed time for period: {timedelta(seconds=t.split_period())}')

                # Dowload the results
                if status == 'DONE':
                    try:
                        logging.info(f'Downloading the results')
                        logging.info(f'{self.download_results(result)}')
                    except Exception as e:
                        logging.error(f'Failed to download results: {e}')

            logging.info(f'Elapsed time for feature: {timedelta(seconds=t.split_feature())}')

        timings = t.stop()

        logging.info(f'Total elapsed time: {timedelta(seconds=timings["elapsed_time"])}')

        logging.info('Statistics:')
        logging.info(f'Min: {timedelta(seconds=timings["stats"]["min"])}')
        logging.info(f'Max: {timedelta(seconds=timings["stats"]["max"])}')
        logging.info(f'Mean: {timedelta(seconds=timings["stats"]["mean"])}')
        logging.info(f'StDev: {timedelta(seconds=timings["stats"]["stdev"])}')

        create_histogram(result_path, timings['feature_timings'])


if __name__ == '__main__':
    Fire(BenchMark(config).time_series)
