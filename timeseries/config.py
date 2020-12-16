backend_data = {
    "vito": {
        "url": "https://openeo.vito.be/openeo/1.0",
        "collection": "TERRASCOPE_S2_TOC_V2",
        "bands": ["TOC-B02_10M", "TOC-B03_10M", "TOC-B04_10M"],
        "authentication": {
            "username": "*",
            "password": "*"
        }
    },
    "creo": {
        "url": "https://openeo.creo.vito.be/openeo/1.0",
        "collection": "SENTINEL2_L2A",
        "bands": ["B02_10m", "B03_10m", "B04_10m"],
        "authentication": {
            "username": "*",
            "password": "*"
        }
    },
    "gee": {
        "url": "https://earthengine.openeo.org/v1.0",
        "collection": "COPERNICUS/S2_SR",
        "bands": ["B2", "B3", "B4"],
        "authentication": {
            "username": "*",
            "password": "*"
        }
    }
}
