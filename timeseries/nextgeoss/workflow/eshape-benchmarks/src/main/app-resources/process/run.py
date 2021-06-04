import argparse
import json
import logging
import os
import re
import time
from datetime import datetime
from typing import List

import pyproj
import rasterio
from rasterstats import zonal_stats
from shapely.geometry import shape
import geopandas as gpd
from shapely.ops import transform


"""

"""

# ---------------------------------------------------------
#                  Logging
# ---------------------------------------------------------
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# ---------------------------------------------------------
#                  Argument parser
# ---------------------------------------------------------
parser = argparse.ArgumentParser(description='Calculate the statistics of a given geometry for a given raster file')
parser.add_argument('-d', required=True, action='store', dest='directory', help='Input directory to the raster file')
parser.add_argument('-f', required=False, action='store', dest='regex', default='*',
                    help='Regex to select the files in the given directory')
parser.add_argument('-g', required=True, action='store', dest='geojson', help='Input geojson to calculate the '
                                                                              'statistics')
parser.add_argument('-o', required=True, action='store', dest='output', help='Output directory')

args = parser.parse_args()


def read_geojson(file: str) -> dict:
    with open(file, 'r') as input:
        features = json.load(input)
        input.close()
    return features


def get_date(file) -> str:
    return datetime.strftime(datetime.strptime(re.search('\d{8}T\d{6}', file).group(0), '%Y%m%dT%H%M%S'),
                             '%Y-%m-%dT%H:%M:%SZ')


def reproject_shape(field: shape, file: str) -> shape:
    raster = rasterio.open(file)
    raster_proj = pyproj.CRS(raster.crs)
    field_proj = pyproj.CRS('EPSG:4326')
    project = pyproj.Transformer.from_crs(field_proj, raster_proj, always_xy=True).transform
    return transform(project, field)


def get_stats(field: dict, file: str) -> float:
    geom = reproject_shape(shape(field['geometry']), file)
    stats = zonal_stats(geom, file, stats=['mean'])
    if stats is not None and len(stats) > 0:
        return stats[0]['mean']
    else:
        raise Exception('Could not calculate statistics')
    return None


def get_stat_list(field: dict, files: List[str]) -> List[float]:
    result = list()
    for file in files:
        logging.debug("Getting zonal stats for from {}".format(file))
        result.append(get_stats(field, file))
    return result

def save_results(output_file:str, date: str, stats: List[float], time: float):
    with open(output_file, 'w') as output:
        json.dump({
            "date": date,
            "stats": stats,
            "time": time
        }, output, indent=4)
        output.close()


if __name__ == '__main__':

    start_time = time.time()

    logging.info('Reading first GeoJSON feature')
    field = read_geojson(args.geojson)
    logging.debug('Read field: {}'.format(field))

    files = ['{}/{}'.format(args.directory, f) for f in os.listdir(args.directory) if
             re.search(re.compile(args.regex), f)]
    logging.info('Found {} matching files'.format(len(files)))
    logging.debug('Matching files: {}'.format(','.join(files)))

    if len(files) > 0:
        date = get_date(files[0]),
        logging.info('Extracted date {}'.format(date))

        stats= get_stat_list(field, files)
        logging.info('Got {} stats'.format(len(stats)))

        logging.debug('Saving results to {}'.format(args.output))
        time_diff = time.time() - start_time
        save_results(args.output, date, stats, time_diff)
    else:
        raise Exception('Could not find any matching files')
