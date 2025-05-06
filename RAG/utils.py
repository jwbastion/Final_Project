import math

def haversine(lat1, lng1, lat2, lng2):
    """두 지점 간의 거리 계산 (미터 단위)"""
    R = 6371000  # 지구 반경 (미터)
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def format_time_info(prop, movement):
    """이동 시간 정보 포맷팅"""
    walk = prop.get("walk_time", 9999)
    trans = prop.get("transit_time", 9999)
    
    if movement == "도보": 
        return f"도보 {walk}분"
    elif movement == "대중교통": 
        return f"대중교통 {trans}분"
    else:
        t, mode = (walk, "도보") if walk <= trans else (trans, "대중교통")
        return f"{mode} {t}분"
