from pathlib import Path
from typing import cast

import geopandas as gpd
import numpy as np
import pandas as pd
import pandera.pandas as pa
import shapely
from pandera.typing import Series
from pandera.typing.geopandas import GeoDataFrame, GeoSeries
from shapely.geometry import LineString, Point


class Lights(pa.DataFrameModel):
    light_id: Series[str] = pa.Field(unique=True)
    geometry: GeoSeries[Point]

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
    geometry: GeoSeries[LineString]

    @pa.dataframe_check
    def linestring_only(self, gdf: GeoDataFrame) -> pd.Series:
        return gdf.geometry.geom_type == "LineString"

    def find_closest_roads(self, lights: Lights):
        # use the dist_fast alg
        return None

def load_roads(path: Path):
    gdf = gpd.read_file(path)

    if "road_id" not in gdf.columns:
        raise ValueError(f"{path} has no road_id property on its features")

    gdf = gdf.dropna(subset=["road_id"]) # filter null id

    duplicates = gdf[gdf.duplicated(subset="road_id", keep="first")]
    if not duplicates.empty:
        print(f"Warning: dropping {len(duplicates)} features with duplicate ids")

    gdf = gdf.drop_duplicates(subset="road_id", keep="first")

    return cast(GeoDataFrame[Roads], Roads.validate(gdf, lazy=True))

class Segments:
    road_idx: np.ndarray # road for each segment
    starts: np.ndarray # segments start index each road
    x1: np.ndarray
    y1: np.ndarray
    x2: np.ndarray
    y2: np.ndarray

    def __init__(self, roads: GeoDataFrame[Roads]):
        road_geometries = roads.geometry.to_crs(epsg=7855).to_numpy() # map roads to LineStrings
        coords, coord_idx = shapely.get_coordinates(road_geometries, return_index=True) # all coordinates and mapping to roads
        same_line = coord_idx[:-1] == coord_idx[1:] # is a coordinate pair part of the same LineString
        a, b = coords[:-1], coords[1:] # exclude last, exclude first
        a, b = a[same_line], b[same_line] # keep only coordinates from same line
        self.road_idx = coord_idx[:-1][same_line] # road for each segment
        self.starts = np.searchsorted(self.road_idx, np.arange(len(roads) + 1))

        self.x1, self.y1 = a[:, 0], a[:, 1] # a, because start of segment can never be last array
        self.x2, self.y2 = b[:, 0], b[:, 1] # second coords in each segment

    # get columnar segment coordinates for a road position
    def get(self, road_pos: int):
        if not 0 <= road_pos < len(self.starts):
            raise IndexError(f"road {road_pos} not in range")
        s = slice(self.starts[road_pos], self.starts[road_pos+1])
        return self.x1[s], self.y1[s], self.x2[s], self.y2[s]

    # return closest road idx for list of points
    def closest_roads(self, points: GeoSeries[Point]):
        n = points.shape[0]
        road_closest = np.zeros(n, dtype=int)
        road_distance = np.zeros(n, dtype=float)
        road_flag = np.zeros(n, dtype=bool)
        dxs = self.x2 - self.x1
        dys = self.y2 - self.y1
        q = dxs**2 + dys**2
        dxsq = dxs / q
        dysq = dys / q
        for i in range(n): # for each point
            dx = points.x.iloc[i] - self.x1
            dy = points.y.iloc[i] - self.y1
            u = np.clip(dx * dxsq + dy * dysq, 0, 1)

            # array of square distances (same order as x1, x2...)
            sqdist = (dx - u * dxs) ** 2 + (dy - u * dys) ** 2

            # position of smallest distance in array
            min_pos = np.argmin(sqdist)
            closest = sqdist[min_pos]

            threshold = (np.sqrt(closest) + 5) ** 2 # smallest + 5 metres, squared
            roads_in_threshold = np.unique(self.road_idx[sqdist <= threshold])

            road_closest[i] = self.road_idx[min_pos]
            road_distance[i] = np.sqrt(sqdist[min_pos])
            road_flag[i] = len(roads_in_threshold) > 1
        return road_closest, road_distance, road_flag



def main():
    lights = load_lights(Path("lights.geojson"))
    roads = load_roads(Path("roads.geojson"))

    segments = Segments(roads)
    points = cast(GeoSeries[Point], lights.geometry.to_crs(epsg=7855)) # metric, Melbourne
    closest_roads, distances, flags = segments.closest_roads(points)

    pd.DataFrame({
        "light_id": lights["light_id"].to_numpy(),
        "road_id": roads["road_id"].to_numpy()[closest_roads],
        "distance_m": distances.round(2),
        "flag": flags
    }).to_csv("light_roads.csv", index=False)


if __name__ == "__main__":
    main()
