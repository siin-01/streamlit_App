import streamlit as st
import random
import time

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 기본 세션 상태 초기화
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Code RPG", page_icon="⚔️", layout="wide")

if "player" not in st.session_state:
    st.session_state.player = {
        "level": 1,
        "exp": 0,
        "max_exp": 50,  # 초기 필요 경험치 감소 (빠른 레벨업)
        "hp": 100,
        "max_hp": 100,
        "mp": 50,
        "max_mp": 50,
        "str": 10,      # 힘 (물리 데미지)
        "dex": 5,       # 민첩 (시간 단축, 회피율)
        "luck": 5,      # 운 (치명타 확률 & 데미지)
        "stat_points": 0,
        "gold": 100,
        "weapon_power": 0,
        "inventory": {"food": 0},
        "skills": ["기본 공격", "파이어볼"]
    }

if "location" not in st.session_state:
    st.session_state.location = "마을 광장"

if "logs" not in st.session_state:
    st.session_state.logs = []

p = st.session_state.player

def add_log(msg):
    st.session_state.logs.append(msg)
    if len(st.session_state.logs) > 15:
        st.session_state.logs.pop(0)

# -----------------------------------------------------------------------------
# 2. 게임 계산용 유틸리티 함수
# -----------------------------------------------------------------------------
def get_action_time(base_time):
    # 민첩이 높을수록 행동/이동 시간 단축 (최대 70% 감소)
    reduction = min(0.7, p["dex"] * 0.02)
    return round(base_time * (1 - reduction), 1)

def check_level_up():
    while p["exp"] >= p["max_exp"]:
        p["exp"] -= p["max_exp"]
        p["level"] += 1
        p["max_exp"] = int(p["max_exp"] * 1.25)  # 완만하게 증가하여 빠른 레벨업 유도
        p["stat_points"] += 5
        p["max_hp"] += 20
        p["max_mp"] += 10
        p["hp"] = p["max_hp"]
        p["mp"] = p["max_mp"]
        add_log(f"🎉 **레벨 업!** 현재 레벨: {p['level']} (스탯 포인트 +5)")
        
        # 5레벨마다 새 스킬 습득
        if p["level"] % 5 == 0:
            new_skill = f"알고리즘 폭발 (Lv.{p['level']})"
            p["skills"].append(new_skill)
            add_log(f"✨ **새로운 스킬 습득!**: {new_skill}")

# -----------------------------------------------------------------------------
# 3. 사이드바 : 플레이어 정보, 스탯, 인벤토리, 보유 스킬
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("🛡️ 플레이어 정보")
    st.write(f"**레벨**: {p['level']} (EXP: {p['exp']}/{p['max_exp']})")
    st.write(f"**체력(HP)**: {p['hp']}/{p['max_hp']}")
    st.write(f"**마나(MP)**: {p['mp']}/{p['max_mp']}")
    st.write(f"**소지금**: {p['gold']} G")
    st.markdown("---")
    
    st.subheader("📊 능력치 (💡 마우스를 올려 상세정보 확인)")
    st.write(f"💪 **힘 (STR)**: {p['str']}", help="물리 기본 데미지를 증가시킵니다.")
    st.write(f"🪄 **최대 MP**: {p['max_mp']}", help="스킬 사용 가능 횟수 및 스킬 데미지를 증가시킵니다.")
    st.write(f"⚡ **민첩 (DEX)**: {p['dex']}", help="지역 이동, 낚시, 휴식 시간을 단축시키고 몬스터 공격 회피율을 높입니다.")
    st.write(f"🍀 **운 (LUCK)**: {p['luck']}", help="치명타(크리티컬) 발동 확률과 치명타 데미지를 증가시킵니다.")
    
    if p["stat_points"] > 0:
        st.success(f"남은 스탯 포인트: {p['stat_points']}")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if st.button("+ 힘 (STR)"):
                p["str"] += 1
                p["stat_points"] -= 1
                st.rerun()
            if st.button("+ 민첩 (DEX)"):
                p["dex"] += 1
                p["stat_points"] -= 1
                st.rerun()
        with col_s2:
            if st.button("+ 최대 MP"):
                p["max_mp"] += 10
                p["stat_points"] -= 1
                st.rerun()
            if st.button("+ 운 (LUCK)"):
                p["luck"] += 1
                p["stat_points"] -= 1
                st.rerun()

    st.markdown("---")
    st.subheader("🎒 인벤토리")
    st.write(f"🐟 **보유 음식(생선)**: {p['inventory']['food']}개")
    st.write(f"🗡️ **장착 무기 위력**: +{p['weapon_power']}")

    st.markdown("---")
    st.subheader("📜 보유 스킬")
    for sk in p["skills"]:
        st.write(f"- {sk}")

# -----------------------------------------------------------------------------
# 4. 상단 내비게이션 (장소 이동)
# -----------------------------------------------------------------------------
st.title("💻 Code RPG: 알고리즘 던전")
st.caption("자동 전투 설정과 전략으로 던전을 탐험하세요!")

col_nav1, col_nav2, col_nav3, col_nav4 = st.columns(4)

with col_nav1:
    if st.button("🏰 1. 시작 마을", use_container_width=True, type="primary" if st.session_state.location == "마을 광장" else "secondary"):
        st.session_state.location = "마을 광장"
with col_nav2:
    if st.button("🌲 2. 던전 입구", use_container_width=True, type="primary" if st.session_state.location == "던전" else "secondary"):
        st.session_state.location = "던전"
with col_nav3:
    if st.button("🎣 3. 낚시터", use_container_width=True, type="primary" if st.session_state.location == "낚시터" else "secondary"):
        st.session_state.location = "낚시터"
with col_nav4:
    if st.button("🏠 4. 집 (휴식)", use_container_width=True, type="primary" if st.session_state.location == "집" else "secondary"):
        st.session_state.location = "집"

st.markdown("---")

# -----------------------------------------------------------------------------
# 5. 장소별 이벤트 처리
# -----------------------------------------------------------------------------

# --- 1. 마을 광장 ---
if st.session_state.location == "마을 광장":
    st.header("🏰 시작하는 마을 광장")
    st.write("다양한 상인이 모여있는 활기찬 광장입니다.")
    
    t1, t2, t3 = st.tabs(["🗡️ 무기 상인", "🍎 식품 상인", "🏺 아티팩트 상인"])
    
    with t1:
        st.subheader("무기 점빵")
        weapons = [
            {"name": "철검", "power": 15, "price": 50},
            {"name": "강철 장검", "power": 35, "price": 150},
            {"name": "알고리즘 마스터 대검", "power": 80, "price": 400},
        ]
        for w in weapons:
            col_w1, col_w2 = st.columns([3, 1])
            col_w1.write(f"**{w['name']}** (물리 데미지 +{w['power']})")
            if col_w2.button(f"{w['price']} G 구매", key=f"w_{w['name']}"):
                if p["gold"] >= w["price"]:
                    p["gold"] -= w["price"]
                    p["weapon_power"] = w["power"]
                    add_log(f"⚔️ {w['name']}을(를) 장착했습니다! (물리 데미지 +{w['power']})")
                    st.success("구매 완료!")
                    st.rerun()
                else:
                    st.error("골드가 부족합니다.")
                    
    with t2:
        st.subheader("식품 점빵")
        st.write("구매한 음식은 **인벤토리**로 들어가며, 던전 전투 시 자동 섭취 설정을 해둘 수 있습니다.")
        if st.button("구운 생선 구매 (가방 보관 / HP 40 회복) - 20G"):
            if p["gold"] >= 20:
                p["gold"] -= 20
                p["inventory"]["food"] += 1
                add_log("🐟 구운 생선을 구매하여 인벤토리에 넣었습니다.")
                st.success("구매 완료! 가방에 추가되었습니다.")
                st.rerun()
            else:
                st.error("골드가 부족합니다.")

    with t3:
        st.subheader("아티팩트 점빵")
        st.info("💡 준비 중인 신비한 아티팩트 상점입니다.")

# --- 2. 던전 ---
elif st.session_state.location == "던전":
    st.header("🌲 던전 입구")
    
    dungeon_diff = st.selectbox("던전 난이도 선택", ["초급 던전 (강해진 슬라임)", "중급 던전 (정예 고블린)", "상급 던전 (보스 드래곤)"])
    
    # 강화된 몬스터 데이터 설정
    if "초급" in dungeon_diff:
        enemy = {"name": "강해진 슬라임", "hp": 120, "max_hp": 120, "atk": 15, "exp": 40, "gold": 25}
    elif "중급" in dungeon_diff:
        enemy = {"name": "정예 고블린", "hp": 350, "max_hp": 350, "atk": 30, "exp": 120, "gold": 80}
    else:
        enemy = {"name": "보스 드래곤", "hp": 850, "max_hp": 850, "atk": 65, "exp": 400, "gold": 300}

    st.markdown("### ⚙️ 전투 설정 (자동 전투 알고리즘)")
    st.write("몬스터를 처치할 조건을 설정해 두세요. 조건에 맞는 행동을 우선 실행합니다.")

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        cond_1 = st.selectbox("조건 1 (우선순위 최고)", ["내 HP < 40%", "적 HP < 30%", "내 MP >= 20", "항상 실행"])
        action_1 = st.selectbox("행동 1", ["음식 섭취 (HP 회복)", "피니시 스킬 사용", "스킬 공격", "기본 평타 공격"])
    with col_b2:
        cond_2 = st.selectbox("조건 2 (서브 조건)", ["내 HP < 40%", "내 MP >= 10", "항상 실행"])
        action_2 = st.selectbox("행동 2", ["음식 섭취 (HP 회복)", "스킬 공격", "기본 평타 공격"])

    if st.button("⚔️ 자동 전투 시작", type="primary"):
        st.subheader("🎬 전투 진행 중...")
        
        turn = 0
        while enemy["hp"] > 0 and p["hp"] > 0 and turn < 30:
            turn += 1
            time.sleep(0.4)
            
            # --- 1. 플레이어 턴 (조건 검사) ---
            chosen_action = "기본 평타 공격"
            
            # 조건 1 검사
            if cond_1 == "내 HP < 40%" and (p["hp"] / p["max_hp"]) < 0.4:
                chosen_action = action_1
            elif cond_1 == "적 HP < 30%" and (enemy["hp"] / enemy["max_hp"]) < 0.3:
                chosen_action = action_1
            elif cond_1 == "내 MP >= 20" and p["mp"] >= 20:
                chosen_action = action_1
            elif cond_1 == "항상 실행":
                chosen_action = action_1
            # 조건 2 검사
            elif cond_2 == "내 HP < 40%" and (p["hp"] / p["max_hp"]) < 0.4:
                chosen_action = action_2
            elif cond_2 == "내 MP >= 10" and p["mp"] >= 10:
                chosen_action = action_2
            else:
                chosen_action = action_2

            # 크리티컬 데미지 계산
            crit_chance = p["luck"] * 0.02
            is_crit = random.random() < crit_chance
            crit_mult = 1.5 + (p["luck"] * 0.01) if is_crit else 1.0

            # 행동 수행
            if chosen_action == "음식 섭취 (HP 회복)":
                if p["inventory"]["food"] > 0:
                    p["inventory"]["food"] -= 1
                    heal = 40
                    p["hp"] = min(p["max_hp"], p["hp"] + heal)
                    add_log(f"🍱 [턴 {turn}] 가방에서 음식을 꺼내 먹어 HP를 {heal} 회복했습니다. (남은 음식: {p['inventory']['food']}개)")
                else:
                    # 음식 없을 시 평타 전환
                    dmg = int((p["str"] + p["weapon_power"]) * crit_mult)
                    enemy["hp"] -= dmg
                    add_log(f"⚔️ [턴 {turn}] 음식이 없어 기본 공격! {enemy['name']}에게 {dmg} 데미지!")

            elif chosen_action == "피니시 스킬 사용" and p["mp"] >= 15:
                p["mp"] -= 15
                dmg = int((p["max_mp"] * 1.8) * crit_mult)
                enemy["hp"] -= dmg
                add_log(f"💥 [턴 {turn}] 피니시 스킬 발동! {enemy['name']}에게 {dmg} 데미지! {'(크리티컬!)' if is_crit else ''}")

            elif chosen_action == "스킬 공격" and p["mp"] >= 10:
                p["mp"] -= 10
                dmg = int((p["max_mp"] * 1.0) * crit_mult)
                enemy["hp"] -= dmg
                add_log(f"🪄 [턴 {turn}] 스킬 공격! {enemy['name']}에게 {dmg} 데미지!")

            else: # 기본 평타
                dmg = int((p["str"] + p["weapon_power"]) * crit_mult)
                enemy["hp"] -= dmg
                add_log(f"⚔️ [턴 {turn}] 기본 공격! {enemy['name']}에게 {dmg} 데미지!")

            # 몬스터 처치 체크
            if enemy["hp"] <= 0:
                add_log(f"🏆 {enemy['name']}을(를) 처치했습니다! (+{enemy['exp']} EXP, +{enemy['gold']} Gold)")
                p["exp"] += enemy["exp"]
                p["gold"] += enemy["gold"]
                check_level_up()
                break

            # --- 2. 몬스터 턴 ---
            dodge_chance = min(0.5, p["dex"] * 0.02)
            if random.random() < dodge_chance:
                add_log(f"💨 {enemy['name']}의 강력한 공격을 민첩하게 회피했습니다!")
            else:
                p["hp"] -= enemy["atk"]
                add_log(f"🩸 {enemy['name']}에게 {enemy['atk']} 데미지를 입었습니다. (남은 HP: {p['hp']})")

            if p["hp"] <= 0:
                p["hp"] = 1
                add_log("☠️ 전투에서 패배했습니다... 체력 1 상태로 마을로 후송되었습니다.")
                break

        st.rerun()

# --- 3. 낚시터 ---
elif st.session_state.location == "낚시터":
    st.header("🎣 평화로운 낚시터")
    st.write("낚시를 통해 획득한 음식은 **가방에 보관**되며, 판매하거나 던전에서 회복용으로 사용됩니다.")
    
    cost_time = get_action_time(3.0)
    st.write(f"⏱️ 낚시 소모 시간: **{cost_time}초** (민첩 스탯에 의해 단축됨)")
    
    if st.button("🎣 찌 던지기"):
        with st.spinner("물고기가 찌를 물 때까지 기다리는 중..."):
            time.sleep(cost_time)
            
        catch_success = random.random() < 0.8
        if catch_success:
            p["inventory"]["food"] += 1
            add_log("🐟 오동통한 생선을 낚았습니다! (가방 보관함 +1)")
            st.success("생선을 낚아 인벤토리에 저장했습니다!")
        else:
            add_log("🌊 찌만 흔들리고 아무것도 낚지 못했습니다.")
            st.warning("아쉽게 놓쳤습니다.")

    st.markdown("---")
    st.subheader("🎒 가방 & 판매")
    st.write(f"보유 중인 생선: **{p['inventory']['food']}개**")
    if st.button("생선 1개 판매 (15G)"):
        if p["inventory"]["food"] > 0:
            p["inventory"]["food"] -= 1
            p["gold"] += 15
            add_log("💰 생선을 팔아 15 Gold를 얻었습니다.")
            st.rerun()

# --- 4. 집 ---
elif st.session_state.location == "집":
    st.header("🏠 나의 집")
    st.write("따뜻한 침대에서 휴식을 취하고 체력과 마나를 완전 회복하세요.")
    
    rest_time = get_action_time(5.0)
    st.write(f"⏱️ 휴식 소모 시간: **{rest_time}초** (민첩 스탯에 의해 단축됨)")
    
    if st.button("🛌 휴식하기"):
        with st.spinner("쿨쿨... Zzz..."):
            time.sleep(rest_time)
        
        p["hp"] = p["max_hp"]
        p["mp"] = p["max_mp"]
        add_log("✨ 수면을 취하여 체력과 마나가 완전히 회복되었습니다!")
        st.success("체력과 마나가 모두 회복되었습니다!")

# -----------------------------------------------------------------------------
# 6. 하단 실시간 게임 로그 출력
# -----------------------------------------------------------------------------
st.markdown("---")
st.subheader("📜 모험 일지 (Game Logs)")
for log in reversed(st.session_state.logs):
    st.write(log)
