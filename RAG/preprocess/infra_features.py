import numpy as np
from sklearn.neighbors import BallTree
from math import radians, sin, cos, asin


infra_dfs = {}
trees = {}
earth_radius_km = 6371.0088

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0088  # 지구 반지름 (km)
    lat1, lon1, lat2, lon2 = map(radians, (lat1, lon1, lat2, lon2))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return 2 * R * asin(a**0.5)

def build_trees(infra_dict):
    global infra_dfs, trees
    infra_dfs = infra_dict   
    trees = {}
    for tbl, df in infra_dfs.items():
        coords = np.radians(df[['latitude', 'longitude']].values)
        trees[tbl] = BallTree(coords, metric='haversine')

def find_nearest_tree(tbl, user_lat, user_lng):
    """
    tbl: 테이블명(key)
    user_lat/lng: 사용자 위치
    반환: (row: pandas.Series, dist_m: float)
    """
    tree = trees[tbl]
    pt = np.radians([[user_lat, user_lng]])
    dist_rad, idxs = tree.query(pt, k=1)
    dist_m = dist_rad[0][0] * earth_radius_km * 1000
    row = infra_dfs[tbl].iloc[idxs[0][0]]
    return row, dist_m

def count_in_radius_tree(tbl, user_lat, user_lng, radius_m):
    """
    tbl: 테이블명
    radius_m: 검색 반경 (미터)
    반환: 해당 tbl에서 radius_m 이내 포함된 개수
    """
    tree = trees[tbl]
    pt = np.radians([[user_lat, user_lng]])
    r = (radius_m / 1000) / earth_radius_km
    inds = tree.query_radius(pt, r=r)[0]
    return len(inds)
