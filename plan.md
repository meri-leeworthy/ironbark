# Task description

**Background**  
Before we can assess whether a street is lit well enough, every streetlight has to be assigned to the road it lights.
  
**The task**

Attached, you will find two layers for a small suburb:

- `roads.geojson`: road centrelines (`road_id`, `road_name`)
- `lights.geojson`: streetlight points (`light_id`, `pole_id`, `lamp_type`)

The key to the task is to identify the ways in which the supplied data may have issues or not have a clearly "correct" result. The data is completely fictional so there is no need to use additional data sources in order to answer the question.

  
For every light, work out which road it belongs to and produce a CSV with at least these columns:

- `light_id` -> the light
- `road_id` -> the road you assigned it to
- `distance_m` -> distance from the light to that road, in metres
- `flag` -> blank if you trust the answer; otherwise a short reason why a person should check it

**Notes**  
Use any language or tool you like. We mostly work in Python (geopandas / shapely), but QGIS, PostGIS, R or anything else is fine. Just tell us what you used.

  
Send us your code (a GitHub repo or a zip), the output CSV, and a short README covering:  

- how to run it
- any key assumptions you made
- anything you noticed in the data
- if/how you have used AI to complete the task

# Notes

## Thinking it through

I'm asked to create a mapping from lights to roads. Roads are of type 'LineString' which is an array of coordinates with (I assume) every neighbouring pair representing a linear segment. 

[GeoJSON Standard](https://www.rfc-editor.org/info/rfc7946/#section-3.1.4):
> The "coordinates" member of a Geometry object is composed of [...] an array of positions in the case of a LineString [...] A position is an array of numbers.  There MUST be two or more elements.  The first two elements are longitude and latitude, or easting and northing, precisely in that order and using decimal numbers.  Altitude or elevation MAY be included as an optional third element.

Easting are northing are grid-offsets from an origin in meters. Looking the shape of the numbers (high decimal precision) I can infer the positions are longitude and latitude in all cases, and all positions have 2 numbers. I can't quite tell if there is a specified way to indicate which positioning type a point is but I think for this exercise I will assume all positions are in longitude and latitude and we will only ever have 2 relevant numbers in a position.

> A line between two positions is a straight Cartesian line, the shortest line between those two points in the coordinate reference system (see [Section 4](https://www.rfc-editor.org/info/rfc7946/#section-4)).
   In other words, every point on a line that does not cross the
   antimeridian between a point (lon0, lat0) and (lon1, lat1) can be calculated as
   F(lon, lat) = (lon0 + (lon1 - lon0) * t, lat0 + (lat1 - lat0) * t)
   with t being a real number greater than or equal to 0 and smaller than or equal to 1.  Note that this line may markedly differ from the geodesic path along the curved surface of the reference ellipsoid.

I think what that means is that by default we treat lines as direct between two points, and we don't take into account that the earth's surface is curved.

I'm wondering if the 'problems' in the data will include that some light points are on the intersection of, or equally distant to, two road lines. I'm also noticing that all LineStrings in `roads.geojson` have two positions except the last road which has 13 (12 line segments), and I wonder if this will present a problem in some way. 

I'm asked to find the roads that lights are on. I wonder if the lights sit exactly on the line or if I need to define some distance threshold or find the closest line to the light's point. I think there is a function for this used in linear regression - root mean square? k-nearest-neighbours is used for finding nearest points, not lines...

Say we have a circle that is growing from each point until it intersects with a line / the line is tangent to the circle at that point? Or we have n circles corresponding to n line segments ... No, the line doesn't have to be tangent at all, it could be at any angle and the circle is intersecting with one end of the segment. If the point is a light near a road, and that road is the closest line, then the light point is likely in many cases but not guaranteed to be closer to some point along the line segment than to either of the ends, and only in this case, the smallest circle intersecting with the line would have the line as a tangent to that circle. I'm interested in it being a tangent because that implies the radius of that circle is the shortest distance between the point and any point along the line segment... except in the case where the closest point on any line segment to the light point is the end of a segment...

## Other people's solutions

A DuckDuckGo search for: "If I have a set of line segments and a set of points, how can I find the closest line segment to any given point?"

[First result](https://stackoverflow.com/questions/77937862/fast-way-to-find-closest-line-segment-for-a-large-set-of-planar-points-python) seems to described an optimised solution I should come back to

[One response links to an earlier post](https://stackoverflow.com/questions/849211/shortest-distance-between-a-point-and-a-line-segment/2233538#2233538) describing a simpler solution, which in turn links to [Minimum Distance between a Point and a Line](https://paulbourke.net/geometry/pointlineplane/) (Paul Bourke, 1988):

> The equation of a line defined through two points **P1** (x1,y1) and **P2** (x2,y2) is **P** = **P1** + u (**P2** - **P1**). The point **P3** (x3,y3) is closest to the line at the tangent to the line which passes through **P3**, that is, the dot product of the tangent and line is 0

So tangent here just means line corresponding to a line segment. Dot product of the line and tangent being 0 means we are defining the 'norm' or perpendicular line that intersects through P3. 

[Wikipedia](https://en.wikipedia.org/wiki/Dot_product):
> Geometrically, the scalar product of two vectors is the product of their lengths and the cosine of the angle between them.

The cosine is 0 at pi/2, 3pi/2 or 90/270deg i.e. perpendicular.

> substituting the equation of the line gives \[**P3** - **P1** - u(**P2** - **P1**)] dot (**P2** - **P1**) = 0. Solving this gives the value of u

![](https://paulbourke.net/geometry/pointlineplane/pointline2.gif)

> Substituting this into the equation of the line gives the point of intersection (x,y) of the tangent as 
> x = x1 + u (x2 - x1)  
   y = y1 + u (y2 - y1)
   The distance therefore between the point **P3** and the line is the distance between (x,y) above and **P3**.

u is essentially the fraction of the line segment length at which the closest point lies. So if u is 0 then the closest point is P1, and if u is 1 then the closest point is P2, which addresses my earlier concern.

From the second StackOverflow link:
```python
# Source - https://stackoverflow.com/a/2233538
# Posted by quano, modified by community. See post 'Timeline' for change history
# Retrieved 2026-10-23, License - CC BY-SA 4.0


def dist(x1, y1, x2, y2, x3, y3):  # x3,y3 is the point
    px = x2 - x1
    py = y2 - y1

    norm = px * px + py * py

    u = ((x3 - x1) * px + (y3 - y1) * py) / float(norm)

    if u > 1:
        u = 1
    elif u < 0:
        u = 0

    x = x1 + u * px
    y = y1 + u * py

    dx = x - x3
    dy = y - y3

    # Note: If the actual distance does not matter,
    # if you only want to compare what this function
    # returns to other results of this function, you
    # can just return the squared distance instead
    # (i.e. remove the sqrt) to gain a little performance

    dist = (dx * dx + dy * dy) ** 0.5

    return dist
```

The optimised solution vectorises the algorithm, i.e. applies operations in parallel over an array, rather than looping:

 ```python
 import numpy as np, time


 def dist_fast(p, segment):
     n = p.shape[1]
     segment_closest = np.zeros(n, dtype=int)
     dxs = segment[2, :] - segment[0, :]
     dys = segment[3, :] - segment[1, :]
     q = dxs**2 + dys**2
     dxsq = dxs / q
     dysq = dys / q
     for i in range(n):
         dx = p[0, i] - segment[0]
         dy = p[1, i] - segment[1]
         u = np.clip(dx * dxsq + dy * dysq, 0, 1)
         sqdist = (dx - u * dxs) ** 2 + (dy - u * dys) ** 2
         segment_closest[i] = np.argmin(sqdist)
     return segment_closest


 n = 10**4  # number of points
 m = 10**3  # number of line segments

 # define repeatable random numbers
 np.random.seed(0)
 # create random points and line segments for testing
 p = np.random.rand(2, n)  # x,y of points
 segment = np.random.rand(4, m)  # x1,y1,x2,y2  start and end of line segments

 segment_closest1 = dist_fast(p, segment)
 ```

So `p` has all the x values contiguous in memory and then all the y values contiguous, and likewise for `segment`. `dxs` produces an array of the differences in x, same `dys` for y, all calculated in parallel, or at least faster. Then `q` is the squared lengths of the line segments, and `dxsq` etc are the precomputed scalars on segments independent of `p`. It then loops over `n`, and for each point finds `dx` which is an array of x3-x1 (differences in x between P3 and every P1) and same for y. It then calculates all values of `u`, constraining to values between 0 and 1, and then the squared distance between the closest point on the segments and P3, then `argmin` to find the smallest. This could probably be faster be vectorising over n as well but we aren't dealing with an enormous amount of data in this exercise. 

## Plan for solving the task

We want not only the closest line segment but also the corresponding road. My challenge for myself is here to maintain the performance benefits of the optimised solution, so I think that means for each road keeping offsets into an array. I.e. we load the segments array by iterating over the pairs of coordinates in each road, and then pushing to a list of offsets corresponding to each segment at that road's index. So, we are assuming this is a static analysis task. E.g.
```python
example_offsets = [1, 2, 3...]
# offsets[0] corresponds to roads[0], i.e. Main St,
# and 1 represents the range [0, 1) which contains its one line segment

# I would reach for pandas to load the geojson, but probably worth looking at geopandas
roads = geopandas.read_file(path_to_file) # geodataframe
segments, offsets = extract_line_segments(roads)

# The goal here is that we can retrieve the road for a given segment 
# using the offsets index e.g.
example_segment = segments[31]
example_road_index = offsets[31] # e.g. 26
example_road = roads[example_road_index]
```

### Some potential problems

Noticing now that multiple streets are named 'Main St'. Maybe worth checking that `road_id` and `pole_id` / `light_id` are unique so we can index on them if needed! (Are there multiple lights on one pole?)

Looking a bit closer at the lights data it looks like there are full duplicates of entire features. I'm asked to produce a csv with `light_id` as the first column, so I think I'll assume `light_id` is unique and deduplicate? Or to be safe I could check deep equality and throw if it fails?

### Encapsulating

(Consulted Claude here to find solution for pandas type validation)

The above solution should work but is fairly arcane - the vectorisation means we have a fast but abstract representation. It is safer to encapsulate the behaviour, and we can use pandera to validate the input

```python
import geopandas as gpd
import pandera.pandas as pa
from pandera.typing.geopandas import GeoSeries

class Roads(pa.DataFrameModel):
    id: str
    geometry: GeoSeries
    
    def __init__(self, path):
        self.roads = gpd.read_file(path)
        # validate the geometry is LineString

    def find_closest_roads(lights: Lights):
        # use the dist_fast alg

class Lights(pa.DataFrameModel)
    id: str
    geometry: GeoSeries
    # ...
```

### Todo

- validate roads are Feature, that they have road_id, and geometry is LineString
- validate lights are Feature, they have light_id, and geometry is point
- can we validate the coordinates are lat/long?
- validate that road_id and light_id are unique
- deduplication
- implement
