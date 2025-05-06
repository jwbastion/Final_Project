from utils import haversine, format_time_info
from database import InfraDataAccessor
from config import INFRA_TYPES

def filter_properties_by_location(properties, user_state):
    filtered = []
    lat0 = user_state.get("lat")
    lng0 = user_state.get("lng")
    service = user_state.get("service")
    if service == "반경":
        radius = user_state.get("radius", 1000)
        for prop in properties:
            md = prop.metadata
            plat = md.get("lat")
            plng = md.get("lng")
            if plat is None or plng is None:
                continue
            dist = haversine(lat0, lng0, plat, plng)
            if dist <= radius:
                filtered.append(prop)
    elif service == "소요시간":
        time_limit = user_state.get("time_limit", 30)
        movement = user_state.get("movement", "대중교통")
        key = "walk_time" if movement == "도보" else "transit_time"
        station_coords = {}
        for prop in properties:
            md = prop.metadata
            st, lat, lng = md.get("station"), md.get("lat"), md.get("lng")
            if st and isinstance(lat, float) and isinstance(lng, float):
                station_coords.setdefault(st, []).append((lat, lng))
        for st, coords in station_coords.items():
            lats = [c[0] for c in coords]
            lngs = [c[1] for c in coords]
            station_coords[st] = {"lat": sum(lats)/len(lats), "lng": sum(lngs)/len(lngs)}
        dist_list = [(st, haversine(lat0, lng0, c["lat"], c["lng"])) for st, c in station_coords.items()]
        dist_list.sort(key=lambda x: x[1])
        nearest = [st for st, _ in dist_list[:3]]
        for prop in properties:
            md = prop.metadata
            if md.get("station") in nearest and md.get(key, 9999) <= time_limit:
                filtered.append(prop)
    else:
        filtered = properties
    return filtered

def filter_properties_by_budget(properties, user_state):
    rent_limit = user_state.get("rent", 100)
    deposit_limit = user_state.get("deposit", 5000)
    maint_limit = user_state.get("maint", 50)
    filtered = []
    for prop in properties:
        md = prop.metadata
        rent = md.get("rent", float("inf"))
        deposit = md.get("deposit", float("inf"))
        maint = md.get("maint", float("inf"))
        if rent <= rent_limit and deposit <= deposit_limit and maint <= maint_limit:
            filtered.append(prop)
    return filtered

def apply_infra_scores(properties, infra_preferences, infra_data):
    sorted_infra = sorted(infra_preferences.items(), key=lambda x: x[1], reverse=True)
    scored_properties = []
    for prop in properties:
        md = prop.metadata
        prop_info = {
            "address": md.get("address", "주소 정보 없음"),
            "station": md.get("station", "역 정보 없음"),
            "rent": md.get("rent", 0),
            "deposit": md.get("deposit", 0),
            "maint": md.get("maint", 0),
            "lat": md.get("lat"),
            "lng": md.get("lng"),
            "walk_time": md.get("walk_time"),
            "transit_time": md.get("transit_time"),
            "infra_score": 0,
            "infra_details": {}
        }
        if prop_info["lat"] is None or prop_info["lng"] is None:
            scored_properties.append(prop_info)
            continue
        plat = prop_info["lat"]
        plng = prop_info["lng"]
        for infra_type, weight in sorted_infra:
            infra_items = [item for item in infra_data if item["type"] == infra_type]
            if not infra_items:
                continue
            min_dist = float("inf")
            nearest_name = None
            for item in infra_items:
                dist = haversine(plat, plng, item["lat"], item["lng"])
                if dist < min_dist:
                    min_dist = dist
                    nearest_name = item["name"]
            threshold = 500
            if min_dist <= threshold:
                score = weight
            else:
                score = -weight
            prop_info["infra_score"] += score
            prop_info["infra_details"][infra_type] = {
                "distance": min_dist,
                "score": score,
                "nearest": nearest_name
            }
        scored_properties.append(prop_info)
    scored_properties.sort(key=lambda x: x.get("infra_score", 0), reverse=True)
    return scored_properties

class RealEstateRecommender:
    def __init__(self, index, user_state, db_config):
        self.index = index
        self.user_state = user_state
        self.data_accessor = InfraDataAccessor(db_config)
        self.recursion_depth = 0

    def search_properties(self):
        try:
            resp = self.index.query(vector=[0.0]*1536, top_k=500, include_metadata=True)
            return resp.matches
        except Exception:
            return []

    def get_all_infra_data(self):
        infra_data = []
        preferences = self.user_state.get("infra_preferences", {})
        if not preferences:
            return []
        for infra_type in preferences.keys():
            type_data = self.data_accessor.get_infra_data(infra_type)
            infra_data.extend(type_data)
        return infra_data

    def get_recommendations(self, is_retry=False):
        self.recursion_depth += 1
        if self.recursion_depth > 2:
            self.recursion_depth = 0
            return {"location_based": [], "budget_based": [], "combined": []}
        all_properties = self.search_properties()
        if not all_properties:
            return self.get_default_recommendations()
        location_filtered = filter_properties_by_location(all_properties, self.user_state)
        budget_filtered = filter_properties_by_budget(all_properties, self.user_state)
        combined_filtered = []
        try:
            location_ids = {getattr(prop, 'id', None) for prop in location_filtered}
            for prop in budget_filtered:
                if getattr(prop, 'id', None) in location_ids:
                    combined_filtered.append(prop)
        except Exception:
            pass
        infra_data = self.get_all_infra_data()
        try:
            location_scored = apply_infra_scores(
                location_filtered,
                self.user_state.get("infra_preferences", {}),
                infra_data
            )
            budget_scored = apply_infra_scores(
                budget_filtered,
                self.user_state.get("infra_preferences", {}),
                infra_data
            )
            combined_scored = apply_infra_scores(
                combined_filtered,
                self.user_state.get("infra_preferences", {}),
                infra_data
            )
        except Exception:
            location_scored = []
            budget_scored = []
            combined_scored = []
        movement = self.user_state.get("movement", "상관없음")
        for prop in location_scored:
            prop["time_info"] = format_time_info(prop, movement)
        for prop in budget_scored:
            prop["time_info"] = format_time_info(prop, movement)
        for prop in combined_scored:
            prop["time_info"] = format_time_info(prop, movement)
        if (not location_scored or not budget_scored or not combined_scored) and not is_retry:
            if self.user_state.get("service") == "반경":
                original_radius = self.user_state.get("radius", 500)
                new_radius = original_radius * 2
                self.user_state.update("radius", new_radius)
            original_rent = self.user_state.get("rent", 50)
            new_rent = int(original_rent * 1.2)
            self.user_state.update("rent", new_rent)
            return self.get_recommendations(is_retry=True)
        self.recursion_depth = 0
        return {
            "location_based": location_scored[:5],
            "budget_based": budget_scored[:5],
            "combined": combined_scored[:5]
        }

    def get_default_recommendations(self):
        default_properties = [
            {
                "address": "서울 강남구 역삼동 123-45",
                "station": "강남역",
                "rent": 45,
                "deposit": 500,
                "maint": 10,
                "time_info": "도보 5분",
                "infra_score": 8.5,
                "infra_details": {
                    "subway": {"distance": 350, "score": 5, "nearest": "강남역"},
                    "park": {"distance": 450, "score": 2.5, "nearest": "역삼공원"},
                    "health": {"distance": 200, "score": 1, "nearest": "역삼헬스센터"}
                }
            },
            {
                "address": "서울 마포구 합정동 456-78",
                "station": "합정역",
                "rent": 40,
                "deposit": 300,
                "maint": 8,
                "time_info": "도보 7분",
                "infra_score": 7.8,
                "infra_details": {
                    "subway": {"distance": 400, "score": 4.5, "nearest": "합정역"},
                    "park": {"distance": 350, "score": 3, "nearest": "망원한강공원"},
                    "health": {"distance": 500, "score": 0.3, "nearest": "마포헬스클럽"}
                }
            }
        ]
        return {
            "location_based": default_properties,
            "budget_based": default_properties,
            "combined": default_properties
        }