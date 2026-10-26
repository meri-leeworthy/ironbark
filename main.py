from pathlib import Path
from typing import cast

import geopandas as gpd
import numpy as np
import pandas as pd
import pandera.pandas as pa
import shapely
from pandera.typing import Series
from pandera.typing.geopandas import GeoDataFrame, GeoSeries


class Lights(pa.DataFrameModel):
    light_id: Series[str] = pa.Field(unique=True)
    geometry: GeoSeries

    @pa.dataframe_check
    def points_only(self, gdf: GeoDataFrame) -> pd.Series:
        return gdf.geometry.geom_type == "Point"

    class Config(pa.DataFrameModel.Config):
        strict = "filter"
        coerce = False

def load_lights(path: Path):
    gdf = gpd.read_file(path)

    if "light_id" not in gdf.columns:
        raise ValueError(f"{path} has no light_id property on its features")

    gdf = gdf.dropna(subset=["light_id"]) # filter null id

    duplicates = gdf[gdf.duplicated(subset="light_id", keep="first")]
    if not duplicates.empty:
        print(f"Warning: dropping {len(duplicates)} features with duplicate ids")

    gdf = gdf.drop_duplicates(subset="light_id", keep="first")

    return cast(GeoDataFrame[Lights], Lights.validate(gdf, lazy=True))

class Roads(pa.DataFrameModel):
    road_id: Series[str] = pa.Field(unique=True)
    geometry: GeoSeries

    @pa.dataframe_check
    def linestring_only(self, gdf: GeoDataFrame) -> pd.Series:
        return gdf.geometry.geom_type == "LineString"

    def find_closest_roads(self, lights: Lights):
        # use the dist_fast alg
        return None

def load_roads(path: Path):
    gdf = gpd.read_file(path)
    return cast(GeoDataFrame[Roads], Roads.validate(gdf, lazy=True))

class Segments:
    road_idx: np.ndarray # road for each segment
    starts: np.ndarray # segments start index each road
    x1: np.ndarray
    y1: np.ndarray
    x2: np.ndarray
    y2: np.ndarray

    def __init__(self, roads: GeoDataFrame[Roads]):
        road_geometries = roads.geometry.to_numpy() # map roads to LineStrings
        coords, coord_idx = shapely.get_coordinates(road_geometries, return_index=True) # all coordinates and mapping to roads

        same_line = coord_idx[:-1] == coord_idx[1:] # is a coordinate pair part of the same LineString
        a, b = coords[:-1], coords[1:] # exclude last, exclude first
        a, b = a[same_line], b[same_line] # keep only coordinates from same line
        self.road_idx = coord_idx[:-1][same_line] # road for each segment
        self.starts = np.searchsorted(self.road_idx, np.arange(len(roads) + 1))

        self.x1, self.y1 = a[:, 0], a[:, 1] # a, because start of segment can never be last array
        self.x2, self.y2 = b[:, 0], b[:, 1] # second coords in each segment

    def get(self, road_pos: int):
        if not 0 <= road_pos < len(self.starts):
            raise IndexError(f"road {road_pos} not in range")
        print(self.starts[road_pos])

def main():
    lights = load_lights(Path("lights.geojson"))
    # print(lights)
    roads = load_roads(Path("roads.geojson"))

    segments = Segments(roads)
    segments.get(500)


if __name__ == "__main__":
    main()
