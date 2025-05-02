from preprocess.data_loader import load_all_infra, load_subcategories
from preprocess.infra_features import PARENT_RADIUS, SUBCAT_RADIUS, count_subcat_in_radius

infra_dfs   = load_all_infra()
subcats_map = load_subcategories(infra_dfs)


def ask_rating(prompt, scale=5):
    val = int(input(f"{prompt} (1: 전혀, {scale}: 매우): ").strip())
    return max(1, min(scale, val))


def ask_yes_no(prompt):
    return input(f"{prompt} (y/n): ").strip().lower().startswith('y')


def run_chatbot(lat, lon, rent, deposit, maint):
    # 1) 부모 카테고리 중요도 수집
    parent_scores = {parent: ask_rating(f"{parent} 인프라를 얼마나 중요하게 여기시나요?")
                     for parent in PARENT_RADIUS}

    # 2) 서브카테고리별 추가 질문
    sub_scores = {}
    for parent, score in parent_scores.items():
        if score >= 3:
            for subcat in subcats_map[parent]:
                # 다섯 인자: df, lat, lon, subcat, radius
                cnt = count_subcat_in_radius(
                    infra_dfs[parent], lat, lon,
                    subcat, SUBCAT_RADIUS[subcat]
                )
                if parent in ('traffic', 'safety'):
                    ans = ask_yes_no(f"{subcat}이 주변에 {cnt}개 있어요. 우선순위로 두시겠습니까?")
                else:
                    ans = ask_rating(f"{subcat}이 주변에 {cnt}개 있어요. 얼마나 중요하게 보시나요?")
                sub_scores[f"{parent}:{subcat}"] = ans

    print("\n▶ 최종 인프라 선호도 요약:")
    for key, value in {**parent_scores, **sub_scores}.items():
        print(f"  {key} -> {value}")
if __name__ == '__main__':
    # 테스트 
    run_chatbot(37.5055712636346, 126.941856308051, 50, 500, 10)
