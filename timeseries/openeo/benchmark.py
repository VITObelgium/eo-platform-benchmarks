import os
from datetime import timedelta

import geojson
import openeo
from fire import Fire
from openeo.rest.connection import OpenEoApiError
from shapely.geometry import shape
from config import backend_data

from timeseries.timer import Timer


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

        print(f"Running benchmark on {backend}:\n")

        with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'input_fields', 'europe_20_fields.geojson')) as f:
            input_geojson = geojson.load(f)

        t = Timer()
        t.start()

        for i, f in enumerate(input_geojson.features):
            print(f"Feature {i + 1}:\n")

            polygon = shape(f["geometry"])

            temporal_extents = [["2020-01-01", "2020-05-31"], ["2020-06-01", "2020-10-31"]]

            for temporal_extent in temporal_extents:
                print(f"{temporal_extent[0]} - {temporal_extent[1]}:\n")
                try:
                    connection = self._get_connection(backend)

                    result = connection \
                        .load_collection(backend_data[backend]["collection"],
                                         temporal_extent=temporal_extent,
                                         bands=backend_data[backend]["bands"]) \
                        .polygonal_mean_timeseries(polygon) \
                        .execute()

                    print(f"{result}\n")
                except OpenEoApiError as e:
                    print(f"Failed to execute request: {e}\n")

                print(f"Elapsed time for period: {timedelta(seconds=t.split_period())}\n")

            print(f"Elapsed time for feature: {timedelta(seconds=t.split_feature())}\n")

        print(f"Total elapsed time: {timedelta(seconds=t.stop())}\n")

    @staticmethod
    def _get_connection(backend):
        connection = openeo.connect(backend_data[backend]["url"])
        authentication = backend_data[backend].get("authentication")
        if authentication:
            connection = connection.authenticate_basic(authentication["username"], authentication["password"])

        return connection


if __name__ == "__main__":
    Fire(BenchMark().time_series)
