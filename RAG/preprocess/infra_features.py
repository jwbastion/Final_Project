from haversine import haversine

# 대분류별 기본 반경 (미터)
PARENT_RADIUS = {
    'life':        200,
    'traffic':     250,
    'safety':      500,
    'health_care': 400,
    'health':      300,
    'play':        300,
}

# 서브카테고리별 반경 (미터)
SUBCAT_RADIUS = {
    '편의점': 200, '대형마트': 200, '백화점': 200, '카페': 200, '공원': 200,
    '지하철역': 250, '버스정류장': 250, '우체국': 200,
    '파출소': 500, '지구대': 500, '주민센터': 200,
    '병원': 400, '약국': 400, '다이소': 300, '버스': 300, '지하철': 300,
    '헬스장': 300, '골프연습장': 300, '골프장': 300,
    'PC방': 300, '영화관': 300, '노래방': 300,
}

def count_in_radius(df, user_lat, user_lon, radius_m):
    """
    df: DataFrame with 'latitude' and 'longitude' columns.
    Returns count of rows within radius_m (meters) from user location.
    """
    def within(row):
        dist_km = haversine((user_lat, user_lon), (row['latitude'], row['longitude']))
        return dist_km * 1000 <= radius_m
    return int(df.apply(within, axis=1).sum())

def count_subcat_in_radius(df, user_lat, user_lon, subcat, radius_m):
    """
    df: DataFrame with 'category', 'latitude', 'longitude' columns.
    subcat: subcategory name to filter.
    radius_m: radius in meters.
    """
    sub_df = df[df['category'] == subcat]
    return count_in_radius(sub_df, user_lat, user_lon, radius_m)

def extract_features(infra_dfs, user_lat, user_lon):
    """
    infra_dfs: dict of DataFrames keyed by parent category.
    Returns dict of parent_count features.
    """
    features = {}
    for cat, df in infra_dfs.items():
        cnt = count_in_radius(df, user_lat, user_lon, PARENT_RADIUS.get(cat, 0))
        features[f'{cat}_count'] = cnt
    return features
