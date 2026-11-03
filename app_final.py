import streamlit as st
import pandas as pd
import numpy as np
import requests

# ---------------------------------------------------------
# 1. 보스별 기준 앵커 데이터셋 (전투력 만 단위 -> 환산 배율 %)
# ---------------------------------------------------------
BOSS_ANCHORS = [
    {
        "boss_group": "세렌", "difficulty": "익스트림", "meso": 150_000_000, "min_time": 5,
        "anchors": [(50000, 75.0), (60000, 95.0), (70000, 120.0), (100000, 185.0)]
    },
    {
        "boss_group": "림보", "difficulty": "하드", "meso": 115_000_000, "min_time": 5,
        "anchors": [(40000, 60.0), (55000, 84.8), (70000, 115.0), (90000, 160.0)]
    },
    {
        "boss_group": "칼로스", "difficulty": "하드", "meso": 85_000_000, "min_time": 5,
        "anchors": [(40000, 65.0), (55000, 88.9), (65000, 110.0), (80000, 140.0)]
    },
    {
        "boss_group": "카링", "difficulty": "노말", "meso": 75_000_000, "min_time": 4,
        "anchors": [(35000, 65.0), (45000, 83.3), (55000, 105.0), (70000, 135.0)]
    },
    {
        "boss_group": "칼로스", "difficulty": "이지", "meso": 45_000_000, "min_time": 4,
        "anchors": [(25000, 70.0), (35000, 98.0), (45000, 121.5), (60000, 165.0)]
    },
    {
        "boss_group": "세렌", "difficulty": "하드", "meso": 42_000_000, "min_time": 4,
        "anchors": [(25000, 75.0), (35000, 105.0), (45000, 130.5), (60000, 175.0)]
    },
    {
        "boss_group": "루시드", "difficulty": "하드", "meso": 38_000_000, "min_time": 3,
        "anchors": [(20000, 60.0), (30000, 95.0), (40000, 129.3), (60000, 195.0)]
    },
    {
        "boss_group": "윌", "difficulty": "하드", "meso": 40_000_000, "min_time": 4,
        "anchors": [(20000, 60.0), (30000, 95.0), (40000, 133.1), (60000, 200.0)]
    },
    {
        "boss_group": "진힐라", "difficulty": "하드", "meso": 36_000_000, "min_time": 3,
        "anchors": [(15000, 70.0), (25000, 115.0), (35000, 160.4), (50000, 230.0)]
    },
    {
        "boss_group": "더스크", "difficulty": "카오스", "meso": 32_000_000, "min_time": 3,
        "anchors": [(15000, 75.0), (25000, 110.0), (35000, 155.1), (50000, 220.0)]
    },
    {
        "boss_group": "듄케일", "difficulty": "카오스", "meso": 34_000_000, "min_time": 3,
        "anchors": [(15000, 70.0), (25000, 115.0), (35000, 168.8), (50000, 240.0)]
    },
    {
        "boss_group": "가디언엔젤슬라임", "difficulty": "카오스", "meso": 28_000_000, "min_time": 2,
        "anchors": [(10000, 90.0), (15000, 140.0), (20000, 204.3), (30000, 310.0)]
    },
    {
        "boss_group": "루시드", "difficulty": "노말", "meso": 18_000_000, "min_time": 2,
        "anchors": [(5000, 90.0), (8000, 145.0), (11000, 204.3), (20000, 380.0)]
    },
    {
        "boss_group": "윌", "difficulty": "노말", "meso": 20_000_000, "min_time": 2,
        "anchors": [(5000, 85.0), (8000, 140.0), (11000, 237.2), (20000, 420.0)]
    },
    {
        "boss_group": "진힐라", "difficulty": "노말", "meso": 22_000_000, "min_time": 2,
        "anchors": [(4000, 110.0), (8000, 220.0), (11000, 339.8), (20000, 600.0)]
    },
    {
        "boss_group": "스우", "difficulty": "하드", "meso": 24_000_000, "min_time": 2,
        "anchors": [(3000, 120.0), (6000, 240.0), (11000, 481.8), (20000, 880.0)]
    },
    {
        "boss_group": "데미안", "difficulty": "하드", "meso": 23_000_000, "min_time": 2,
        "anchors": [(3000, 120.0), (6000, 240.0), (11000, 481.8), (20000, 880.0)]
    },
    {
        "boss_group": "카루타_4종", "difficulty": "카오스", "meso": 45_000_000, "min_time": 2,
        "anchors": [(1000, 150.0), (2000, 320.0), (5000, 800.0), (11000, 1800.0)]
    }
]

# ---------------------------------------------------------
# 2. 선형 보간 엔진
# ---------------------------------------------------------
def interpolate_ratio(user_cp_man: float, anchors: list) -> float:
    cps = [pt[0] for pt in anchors]
    ratios = [pt[1] for pt in anchors]

    if user_cp_man <= cps[0]:
        return max(0.0, ratios[0] * (user_cp_man / cps[0]))
    elif user_cp_man >= cps[-1]:
        slope = (ratios[-1] - ratios[-2]) / (cps[-1] - cps[-2])
        return ratios[-1] + slope * (user_cp_man - cps[-1])
    else:
        return float(np.interp(user_cp_man, cps, ratios))

# ---------------------------------------------------------
# 3. 넥슨 Open API 통신 (Streamlit Secrets에서 호출)
# ---------------------------------------------------------
def fetch_user_data(char_name: str):
    if "NEXON_API_KEY" in st.secrets:
        api_key = st.secrets["NEXON_API_KEY"]
    else:
        return None, None, "서버 설정 오류: NEXON_API_KEY가 등록되지 않았습니다."

    headers = {"x-nxopen-api-key": api_key}

    # 1. ocid 식별자 조회
    id_url = f"https://open.api.nexon.com/maplestory/v1/id?character_name={char_name}"
    res = requests.get(id_url, headers=headers)
    if res.status_code != 200:
        return None, None, f"캐릭터 조회 실패: 닉네임을 확인하세요 (HTTP {res.status_code})"
    ocid = res.json().get("ocid")

    # 2. 스탯 조회
    stat_url = f"https://open.api.nexon.com/maplestory/v1/character/stat?ocid={ocid}"
    stat_res = requests.get(stat_url, headers=headers)
    if stat_res.status_code != 200:
        return None, None, f"스탯 데이터 조회 실패 (HTTP {stat_res.status_code})"

    final_stats = stat_res.json().get("final_stat", [])
    combat_power = 0
    for s in final_stats:
        if s.get("stat_name") == "전투력":
            combat_power = int(s.get("stat_value", 0))
            break

    # 3. 기본 정보(레벨, 직업)
    basic_url = f"https://open.api.nexon.com/maplestory/v1/character/basic?ocid={ocid}"
    basic_res = requests.get(basic_url, headers=headers)
    basic_info = basic_res.json() if basic_res.status_code == 200 else {}

    return combat_power, basic_info, None

# ---------------------------------------------------------
# 4. 2차원 Knapsack DP 최적화
# ---------------------------------------------------------
def optimize_boss_route(boss_df, total_time_limit_min, prep_time_min, max_boss_count=12):
    groups = boss_df.groupby('boss_group')
    group_list = []

    for _, group in groups:
        options = []
        for _, row in group.iterrows():
            weight = int(row['clear_time_min'] + prep_time_min)
            value = int(row['meso_reward'])
            options.append({
                'name': f"{row['boss_group']} ({row['difficulty']})",
                'weight': weight,
                'value': value,
                'clear_time': row['clear_time_min'],
                'meso': row['meso_reward'],
                'ratio': row['ratio']
            })
        group_list.append(options)

    num_groups = len(group_list)
    W = int(total_time_limit_min)
    C = int(max_boss_count)

    dp = np.zeros((num_groups + 1, W + 1, C + 1), dtype=np.int64)
    choice = np.full((num_groups + 1, W + 1, C + 1), -1, dtype=np.int8)

    for i in range(1, num_groups + 1):
        current_options = group_list[i - 1]
        for w in range(W + 1):
            for c in range(C + 1):
                dp[i][w][c] = dp[i - 1][w][c]
                if c >= 1:
                    for opt_idx, opt in enumerate(current_options):
                        if w >= opt['weight']:
                            cand = dp[i - 1][w - opt['weight']][c - 1] + opt['value']
                            if cand > dp[i][w][c]:
                                dp[i][w][c] = cand
                                choice[i][w][c] = opt_idx

    selected = []
    curr_w, curr_c = W, C
    for i in range(num_groups, 0, -1):
        opt_idx = choice[i][curr_w][curr_c]
        if opt_idx != -1:
            chosen = group_list[i - 1][opt_idx]
            selected.append(chosen)
            curr_w -= chosen['weight']
            curr_c -= 1

    return dp[num_groups][W][C], selected[::-1]

# ---------------------------------------------------------
# 5. UI 화면
# ---------------------------------------------------------
def main():
    st.set_page_config(page_title="메이플 주간 보스 최적 경로 산출기", layout="wide")
    st.title("🍁 메이플 주간 보스 최적 루트 플래너")
    st.caption("캐릭터 닉네임만 입력하면 넥슨 공식 API와 자체 보간 엔진이 즉시 최적 경로를 도출합니다.")

    st.sidebar.header("🕹️ 플레이 환경 설정")
    total_time_limit = st.sidebar.slider("가용 보스 플레이 시간 (분)", 30, 180, 60, 5)
    prep_time = st.sidebar.slider("보스 간 정비/입장 시간 (분)", 0, 3, 1)

    char_name = st.text_input("캐릭터 닉네임을 입력하세요", placeholder="예: 타락파워전사")

    if st.button("🚀 데이터 분석 및 최적 루트 산출"):
        if not char_name.strip():
            st.warning("닉네임을 입력해주세요.")
            return

        with st.spinner("넥슨 공식 API에서 최신 스펙을 동기화 중..."):
            combat_power, basic_info, err = fetch_user_data(char_name)

        if err:
            st.error(err)
            return

        user_cp_man = combat_power / 10000.0

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("직업", basic_info.get("character_class", "알 수 없음"))
        col_b.metric("레벨", f"Lv. {basic_info.get('character_level', 0)}")
        col_c.metric("종합 전투력", f"{combat_power:,}")

        valid_bosses = []
        for b in BOSS_ANCHORS:
            predicted_ratio = interpolate_ratio(user_cp_man, b["anchors"])
            if predicted_ratio >= 100.0:
                calc_time = int(np.ceil(2000.0 / predicted_ratio))
                clear_time = max(b["min_time"], calc_time)
                valid_bosses.append({
                    "boss_group": b["boss_group"],
                    "difficulty": b["difficulty"],
                    "ratio": predicted_ratio,
                    "clear_time_min": clear_time,
                    "meso_reward": b["meso"]
                })

        df_valid = pd.DataFrame(valid_bosses)

        if df_valid.empty:
            st.warning("현재 스펙으로 솔플 가능한(배율 100% 이상) 보스가 없습니다.")
            return

        max_meso, route = optimize_boss_route(df_valid, total_time_limit, prep_time, 12)
        total_time = sum(b['weight'] for b in route)

        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("총 획득 예상 메소", f"{max_meso:,} 메소")
        m1.caption(f"{max_meso / 100_000_000:.2f} 억 메소")
        m2.metric("총 소요 시간 (정비 포함)", f"{total_time}분 / {total_time_limit}분")
        m3.metric("처치 보스 개수", f"{len(route)}마리 / 12마리")

        result_rows = []
        for idx, b in enumerate(route, 1):
            result_rows.append({
                "추천 순서": idx,
                "보스 명": b['name'],
                "추정 배율": f"{b['ratio']:.1f}%",
                "순수 공략": f"{b['clear_time']}분",
                "정비 포함": f"{b['weight']}분",
                "결정석 가격": f"{b['meso']:,} 메소",
                "분당 효율": f"{int(b['meso'] / b['weight']):,} 메소/분"
            })

        st.subheader("🏆 시간 대비 최대 수익 공략 순서")
        st.dataframe(pd.DataFrame(result_rows), use_container_width=True)

if __name__ == "__main__":
    main()
