from datetime import timedelta
from os.path import abspath, dirname, join

import geojson
from fire import Fire
from sentinelhub import FisRequest, CRS, DataCollection, Geometry, DownloadFailedException
from sentinelhub import SHConfig
from shapely.geometry import shape

from timeseries.timer import Timer


class BenchMark:

    def __init__(self):
        self._endpoints = [
            'https://services.sentinel-hub.com',
            'https://creodias.sentinel-hub.com',
            'https://shservices.mundiwebservices.com'
        ]

        self._config = SHConfig()
        self._config.instance_id = 'b3d8b1b7-4703-4116-a211-333a1a692482'

    def time_series(self):
        for endpoint in self._endpoints:
            with open(f"./results/{endpoint.replace('https://', '')}.txt", "w+") as file:
                file.write(f"Running benchmark on {endpoint}:\n\n")

                self._config.sh_base_url = endpoint

                with open(join(abspath(dirname(dirname(__file__))), 'input_fields', 'europe_20_fields.geojson')) as f:
                    input_geojson = geojson.load(f)

                    # Feature doesn't exist on shservices.mundiwebservices.com
                    del input_geojson.features[16]

                t = Timer()
                t.start()

                for i, f in enumerate(input_geojson.features):
                    file.write(f"Feature {i + 1}:\n\n")

                    geometry = Geometry(shape(f["geometry"]), CRS.WGS84)
                    temporal_extent = ("2020-01-01", "2020-10-31")

                    fis_request = FisRequest(
                        data_collection=DataCollection.SENTINEL2_L1C,
                        layer='S2L1C',
                        geometry_list=[geometry],
                        time=temporal_extent,
                        resolution='10m',
                        data_folder='./data',
                        config=self._config
                    )

                    try:
                        fis_data = fis_request.get_data()

                        file.write(f"{fis_data}\n\n")
                    except DownloadFailedException as e:
                        file.write(f"Failed to execute request: {e}\n\n")

                    file.write(f"Elapsed time for feature: {timedelta(seconds=t.split_feature())}\n\n")

                file.write(f"Total elapsed time: {timedelta(seconds=t.stop())}\n")


if __name__ == "__main__":
    Fire(BenchMark().time_series)
