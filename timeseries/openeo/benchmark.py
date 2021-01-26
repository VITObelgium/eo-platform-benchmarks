from datetime import timedelta
from os.path import abspath, dirname, join

import geojson
import openeo
from fire import Fire
from openeo.rest.connection import OpenEoApiError
from shapely.geometry import shape

from config import backend_data
from timeseries.timer import Timer
from timeseries.histogram import create_histogram


class BenchMark:

    def time_series(self, backend=None):
        if backend is None:
            for b in backend_data:
                self._time_series(b)
        else:
            self._time_series(backend)

    def _time_series(self, backend):
        if not backend_data[backend]:
            return

        result_path = f"./results/{backend}"

        with open(f"{result_path}.txt", "w+") as file:
            file.write(f"Running benchmark on {backend}:\n\n")

            with open(join(abspath(dirname(dirname(__file__))), 'input_fields', 'europe_20_fields.geojson')) as f:
                input_geojson = geojson.load(f)

            t = Timer()
            t.start()

            for i, f in enumerate(input_geojson.features):
                file.write(f"Feature {i + 1}:\n\n")

                polygon = shape(f["geometry"])

                temporal_extents = [["2020-01-01", "2020-10-31"]]

                for temporal_extent in temporal_extents:
                    file.write(f"{temporal_extent[0]} - {temporal_extent[1]}:\n\n")
                    try:
                        connection = self._get_connection(backend)

                        result = connection \
                            .load_collection(backend_data[backend]["collection"],
                                             temporal_extent=temporal_extent,
                                             bands=backend_data[backend]["bands"]) \
                            .polygonal_mean_timeseries(polygon) \
                            .execute()

                        file.write(f"{result}\n\n")
                    except OpenEoApiError as e:
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

    @staticmethod
    def _get_connection(backend):
        connection = openeo.connect(backend_data[backend]["url"])
        authentication = backend_data[backend].get("authentication")
        if authentication:
            connection = connection.authenticate_basic(authentication["username"], authentication["password"])

        return connection


if __name__ == "__main__":
    Fire(BenchMark().time_series)
