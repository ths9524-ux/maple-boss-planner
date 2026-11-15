import streamlit as st
import pandas as pd
import numpy as np
import requests

# ---------------------------------------------------------
# 1. 다중 앵커 메타데이터 (1억, 2억, 3억, 4억, 5억, 6억, 7억, 7.4억 실측 배율)
# ---------------------------------------------------------
ANCHOR_CPS = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 7.4]) * 100_000_000
MAX_TIME_LIMIT = 20  # 모든 보스 최대 제한 시간: 20분

# (boss_group, difficulty, [1억, 2억, 3억, 4억, 5억, 6억, 7억, 7.4억 배율%], meso_uk, min_time, is_monthly)
MULTI_ANCHOR_BOSS_DATA = [
    # 1행
    ("발드릭스", "익스트림", [5.0, 9.0, 14.0, 18.0, 22.0, 27.0, 31.0, 33.0], 96.00, 8, False),
    ("림보", "익스트림", [6.0, 11.0, 17.0, 23.0, 28.0, 34.0, 40.0, 42.0], 75.00, 8, False),
    ("유피테르", "하드", [8.0, 15.0, 23.0, 30.0, 37.0, 45.0, 52.0, 55.0], 53.87, 7, False),
    ("카링", "익스트림", [3.90, 7.67, 11.64, 15.33, 19.14, 23.00, 26.85, 28.39], 48.45, 8, False),
    ("대적자", "익스트림", [5.14, 10.11, 15.35, 20.22, 25.24, 30.33, 35.41, 37.44], 47.12, 7, False),
    ("칼로스", "익스트림", [6.87, 13.51, 20.51, 27.01, 33.72, 40.52, 47.31, 50.02], 41.04, 7, False),
    ("발드릭스", "하드", [8.10, 15.94, 24.20, 31.87, 39.79, 47.81, 55.82, 59.02], 30.78, 7, False),
    ("벨로나", "하드", [9.68, 19.04, 28.91, 38.07, 47.52, 57.11, 66.68, 70.50], 29.50, 7, False),

    # 2행
    ("림보", "하드", [11.83, 23.26, 35.33, 46.53, 58.08, 69.79, 81.48, 86.16], 23.85, 7, False),
    ("흉성", "하드", [12.39, 24.36, 37.00, 48.73, 60.83, 73.09, 85.34, 90.24], 26.78, 7, False),
    ("유피테르", "노말", [11.61, 22.84, 34.68, 45.68, 57.02, 68.51, 79.99, 84.58], 15.60, 6, False),
    ("대적자", "하드", [16.92, 33.28, 50.54, 66.57, 83.10, 99.85, 116.6, 123.3], 13.90, 6, False),
    ("발드릭스", "노말", [18.18, 35.77, 54.32, 71.54, 89.31, 107.3, 125.3, 132.5], 13.20, 6, False),
    ("카링", "하드", [18.03, 35.47, 53.86, 70.93, 88.55, 106.4, 124.2, 131.4], 15.60, 7, False),
    ("세렌", "익스트림", [18.55, 36.48, 55.40, 72.97, 91.09, 109.5, 127.8, 135.1], 18.40, 6, False),
    ("검은 마법사", "익스트림", [22.33, 43.93, 66.72, 87.87, 109.7, 131.8, 153.9, 162.7], 56.80, 10, True),

    # 3행
    ("림보", "노말", [23.52, 46.26, 70.24, 92.52, 115.5, 138.8, 162.0, 171.3], 9.95, 6, False),
    ("칼로스", "카오스", [28.23, 55.54, 84.33, 111.1, 138.7, 166.6, 196.2, 207.4], 12.30, 6, False),
    ("벨로나", "노말", [32.78, 64.49, 97.92, 129.0, 161.0, 195.1, 227.8, 240.8], 8.24, 5, False),
    ("카링", "노말", [52.91, 104.1, 158.0, 209.9, 262.0, 314.8, 376.7, 398.3], 5.93, 6, False),
    ("흉성", "노말", [56.03, 110.2, 167.4, 222.3, 277.4, 333.4, 398.9, 421.8], 5.76, 5, False),
    ("스우", "익스트림", [64.97, 127.8, 195.7, 257.8, 321.8, 396.3, 462.7, 489.3], 5.45, 5, False),
    ("대적자", "노말", [108.0, 214.2, 325.3, 439.0, 548.0, 658.5, 768.8, 812.9], 5.32, 4, False),
    ("칼로스", "노말", [134.9, 267.5, 416.2, 548.2, 684.4, 822.3, 960.2, 1015.0], 4.79, 4, False),

    # 4행
    ("벨로나", "이지", [173.5, 344.1, 535.4, 705.2, 880.3, 1058.0, 1235.0, 1306.0], 3.96, 4, False),
    ("카링", "이지", [206.9, 417.0, 633.3, 834.0, 1041.0, 1251.0, 1461.0, 1545.0], 3.20, 5, False),
    ("세렌", "하드", [236.7, 477.2, 724.6, 954.3, 1191.0, 1431.0, 1671.0, 1767.0], 3.02, 4, False),
    ("대적자", "이지", [313.6, 632.2, 960.1, 1264.0, 1579.0, 1897.0, 2215.0, 2342.0], 2.61, 3, False),
    ("칼로스", "이지", [406.2, 799.0, 1213.0, 1598.0, 1995.0, 2397.0, 2799.0, 2959.0], 2.38, 3, False),
    ("검은 마법사", "하드", [485.5, 955.4, 1451.0, 1911.0, 2385.0, 2866.0, 3347.0, 3539.0], 4.65, 6, True),
    ("세렌", "노말", [560.1, 1102.0, 1673.0, 2204.0, 2751.0, 3305.0, 3859.0, 4081.0], 1.67, 3, False),
    ("진힐라", "하드", [941.6, 1853.0, 2814.0, 3706.0, 4626.0, 5559.0, 6490.0, 6863.0], 1.00, 3, False),

    # 5행
    ("듄켈", "하드", [1077.0, 2119.0, 3217.0, 4237.0, 5289.0, 6356.0, 7421.0, 7847.0], 0.89, 2, False),
    ("더스크", "카오스", [1134.0, 2232.0, 3390.0, 4465.0, 5574.0, 6697.0, 7820.0, 8268.0], 0.66, 2, False),
    ("슬라임", "카오스", [937.6, 1845.0, 2802.0, 3690.0, 4606.0, 5535.0, 6462.0, 6833.0], 0.71, 3, False),
    ("윌", "하드", [1348.0, 2652.0, 4027.0, 5304.0, 6621.0, 7956.0, 9290.0, 9823.0], 0.73, 4, False),
    ("루시드", "하드", [662.3, 1303.0, 1979.0, 2607.0, 3254.0, 3910.0, 4565.0, 4827.0], 0.60, 3, False),
    ("진힐라", "노말", [1883.0, 3706.0, 5627.0, 7412.0, 9252.0, 11118.0, 12981.0, 13725.0], 0.67, 2, False),
    ("데미안", "하드", [2591.0, 5098.0, 7741.0, 10196.0, 12728.0, 15294.0, 17857.0, 18881.0], 0.46, 3, False),
    ("스우", "하드", [3460.0, 6808.0, 10339.0, 13617.0, 16998.0, 20425.0, 23848.0, 25217.0], 0.49, 2, False),
]

BOSS_META = [
    {
        "boss_group": b[0],
        "difficulty": b[1],
        "anchor_mults": np.array(b[2], dtype=float) / 100.0,  # 배율 실수 배열 (100% = 1.0)
        "meso_reward": int(round(b[3] * 100_000_000)),
        "min_time": b[4],
        "is_monthly": b[5],
    }
    for b in MULTI_ANCHOR_BOSS_DATA
]

# ---------------------------------------------------------
# 2. 넥슨 Open API 데이터 수집 파이프라인
# ---------------------------------------------------------
def get_character_combat_power(api_key: str, character_name: str):
    """넥슨 API를 호출하여 캐릭터의 종합 전투력을 추출"""
    headers = {"x-nxopen-api-key": api_key}

    id_url = f"https://open.api.nexon.com/maplestory/v1/id?character_name={character_name}"
    id_res = requests.get(id_url, headers=headers)
    if id_res.status_code != 200:
        return None, f"캐릭터 조회 실패 (코드: {id_res.status_code})"

    ocid = id_res.json().get("ocid")
    if not ocid:
        return None, "캐릭터 OCID를 찾을 수 없습니다."

    stat_url = f"https://open.api.nexon.com/maplestory/v1/character/stat?ocid={ocid}"
    stat_res = requests.get(stat_url, headers=headers)
    if stat_res.status_code != 200:
        return None, f"스탯 조회 실패 (코드: {stat_res.status_code})"

    final_stats = stat_res.json().get("final_stat", [])
    combat_power = 0
    for s in final_stats:
        if s.get("stat_name") == "전투력":
            combat_power = int(s.get("stat_value", 0))
            break

    return combat_power, None

# ---------------------------------------------------------
# 3. 다중 앵커 보간 기반 클리어 소요 시간 역산 (20분 제한)
# ---------------------------------------------------------
def estimate_user_multiplier(user_cp: int, anchor_mults: np.ndarray) -> float:
    """
    1억~7.4억 실측 앵커 테이블을 기반으로 유저 전투력에 따른 예상 환산 배율 산출
    - 1억~7.4억 구간: 구간별 선형 보간 (Piecewise Linear Interpolation)
    - 1억 미만 구간: 1억 기준 원점 비례 스케일링
    - 7.4억 초과 구간: 6.0억~7.4억 구간 상승 기울기를 반영한 선형 외삽
    """
    if user_cp <= ANCHOR_CPS[0]:
        return anchor_mults[0] * (user_cp / ANCHOR_CPS[0])
    elif user_cp >= ANCHOR_CPS[-1]:
        slope = (anchor_mults[-1] - anchor_mults[-3]) / (ANCHOR_CPS[-1] - ANCHOR_CPS[-3])
        return anchor_mults[-1] + slope * (user_cp - ANCHOR_CPS[-1])
    else:
        return float(np.interp(user_cp, ANCHOR_CPS, anchor_mults))


def calculate_clear_times(user_combat_power: int):
    weekly_rows = []
    monthly_rows = []

    for b in BOSS_META:
        user_mult = estimate_user_multiplier(user_combat_power, b["anchor_mults"])

        # 배율 100%(1.0) 미만은 20분 내 솔플 불가 판정
        if user_mult < 1.0:
            continue

        # 100%(1.0)일 때 20분 컷, 배율이 높을수록 기믹 최소 시간(min_time)까지 단축
        raw_time = MAX_TIME_LIMIT / (user_mult ** 0.85)
        estimated_time = max(b["min_time"], int(np.ceil(raw_time)))

        if estimated_time <= MAX_TIME_LIMIT:
            row_data = {
                "boss_group": b["boss_group"],
                "difficulty": b["difficulty"],
                "expected_mult_pct": round(user_mult * 100, 1),
                "clear_time_min": estimated_time,
                "meso_reward": b["meso_reward"],
                "meso_uk": round(b["meso_reward"] / 100_000_000, 2)
            }
            if b["is_monthly"]:
                monthly_rows.append(row_data)
            else:
                weekly_rows.append(row_data)

    return pd.DataFrame(weekly_rows), pd.DataFrame(monthly_rows)

# ---------------------------------------------------------
# 4. 2차원 Knapsack DP 최적화 알고리즘 (주간 보스 최대 12마리)
# ---------------------------------------------------------
def optimize_boss_route(boss_df: pd.DataFrame, total_time_limit_min: int, prep_time_min: int, max_boss_count: int = 12):
    if boss_df.empty:
        return 0, []

    groups = boss_df.groupby('boss_group')
    group_list = []

    for _, group in groups:
        options = []
        for _, row in group.iterrows():
            weight = int(row['clear_time_min'] + prep_time_min)
            value = int(row['meso_reward'])
            options.append({
                'name': f"{row['boss_group']} ({row['difficulty']})",
                'mult_pct': row['expected_mult_pct'],
                'weight': weight,
                'value': value,
                'clear_time': int(row['clear_time_min']),
                'meso': int(row['meso_reward'])
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
                            candidate_val = dp[i - 1][w - opt['weight']][c - 1] + opt['value']
                            if candidate_val > dp[i][w][c]:
                                dp[i][w][c] = candidate_val
                                choice[i][w][c] = opt_idx

    selected_bosses = []
    curr_w = W
    curr_c = C

    for i in range(num_groups, 0, -1):
        opt_idx = choice[i][curr_w][curr_c]
        if opt_idx != -1:
            chosen = group_list[i - 1][opt_idx]
            selected_bosses.append(chosen)
            curr_w -= chosen['weight']
            curr_c -= 1

    # 효율(시간당 메소) 높은 순으로 정렬하여 동선 출력
    selected_bosses.sort(key=lambda x: x['meso'] / x['weight'], reverse=True)
    return int(dp[num_groups][W][C]), selected_bosses

# ---------------------------------------------------------
# 5. UI 화면 구성
# ---------------------------------------------------------
def main():
    st.set_page_config(page_title="메이플 주간 보스 동선 최적화", layout="wide")
    st.title("⚡ 넥슨 Open API 기반 주간 보스 동선 최적화")
    st.caption("8개 구간(1억~7.4억) 40종 보스 실측 환산 배율 보간 모델 & 20분 제한시간 2D Knapsack DP")

    st.sidebar.header("⚙️ 설정 및 유저 정보")
    nexon_api_key = st.sidebar.text_input("Nexon Open API Key (선택)", type="password", help="미입력 시 수동 전투력으로 시뮬레이션 가능")
    char_name = st.sidebar.text_input("캐릭터 닉네임", value="")

    total_time_limit = st.sidebar.slider("가용 제한 시간 (분)", 10, 240, 60, 5)
    prep_time = st.sidebar.number_input("보스 간 정비/이동 시간 (분)", 0, 5, 1)
    max_bosses = st.sidebar.number_input("주간 결정석 판매 한도 (개)", 1, 12, 12)

    user_combat_power = 0
    if nexon_api_key and char_name:
        with st.spinner("넥슨 API에서 스펙 데이터 수신 중..."):
            cp, err = get_character_combat_power(nexon_api_key, char_name)
            if err:
                st.sidebar.error(err)
            else:
                user_combat_power = cp
                st.sidebar.success(f"조회 성공! 종합 전투력: {cp:,}")

    if user_combat_power == 0:
        cp_uk = st.sidebar.number_input("수동 전투력 테스트 입력 (단위: 억)", min_value=0.1, max_value=50.0, value=5.0, step=0.1)
        user_combat_power = int(cp_uk * 100_000_000)

    # 1. 클리어 가능 보스 및 예상 시간 역산
    weekly_df, monthly_df = calculate_clear_times(user_combat_power)

    col_left, col_right = st.columns([2, 1])
    with col_left:
        st.subheader(f"📊 전투력 {user_combat_power / 100_000_000:.2f}억 기준 솔플 가능 주간 보스 ({len(weekly_df)}종)")
        if not weekly_df.empty:
            display_df = weekly_df[["boss_group", "difficulty", "expected_mult_pct", "clear_time_min", "meso_uk"]].copy()
            display_df.columns = ["보스", "난이도", "예상 배율(%)", "예상 클리어(분)", "결정석(억)"]
            st.dataframe(display_df, use_container_width=True, height=340)
        else:
            st.warning("현재 전투력으로 20분 내 솔플 가능한 주간 보스가 없습니다.")

    with col_right:
        st.subheader("🌑 월간 보스 (검은 마법사)")
        if not monthly_df.empty:
            m_display = monthly_df[["boss_group", "difficulty", "expected_mult_pct", "clear_time_min", "meso_uk"]].copy()
            m_display.columns = ["보스", "난이도", "배율(%)", "소요(분)", "결정석(억)"]
            st.dataframe(m_display, use_container_width=True)
            best_bm = monthly_df.iloc[0]
            st.info(f"추천 월간 클리어: **{best_bm['boss_group']} ({best_bm['difficulty']})** (+{best_bm['meso_uk']}억)")
        else:
            st.caption("솔플 가능 난이도 없음 (배율 100% 미만)")

    st.divider()

    # 2. DP 최적화 실행
    if st.button("🚀 최적 주간 보스 동선 계산 (Knapsack DP)", type="primary", use_container_width=True):
        max_meso, route = optimize_boss_route(weekly_df, total_time_limit, prep_time, max_bosses)
        total_time = sum(b['weight'] for b in route)

        c1, c2, c3 = st.columns(3)
        c1.metric("주간 총 획득 메소", f"{max_meso / 100_000_000:.2f} 억", f"{max_meso:,} 메소")
        c2.metric("총 소요 시간", f"{total_time}분 / {total_time_limit}분")
        c3.metric("처치 보스 수", f"{len(route)}마리 / {max_bosses}마리")

        if route:
            result_rows = []
            for idx, b in enumerate(route, 1):
                result_rows.append({
                    "추천 순서": idx,
                    "보스 명": b['name'],
                    "예상 배율": f"{b['mult_pct']}%",
                    "순수 공략(분)": b['clear_time'],
                    "정비 포함(분)": b['weight'],
                    "결정석 가격": f"{b['meso'] / 100_000_000:.2f} 억",
                    "분당 효율": f"{int(b['meso'] / b['weight'] / 10_000):,} 만/분"
                })

            st.subheader("🏆 시간 대비 최대 수익 보스 공략 순서")
            st.dataframe(pd.DataFrame(result_rows), use_container_width=True)
        else:
            st.error("설정한 제한 시간 내에 클리어 가능한 보스 조합이 없습니다.")

if __name__ == "__main__":
    main()
