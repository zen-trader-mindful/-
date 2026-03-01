import streamlit as st
import pandas as pd
import random
import time
import json
import os

# --- 1. 页面配置与美化 ---
st.set_page_config(page_title="正念交易·全能终端", page_icon="🧘", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    .card-box {
        background-color: white; padding: 40px; border-radius: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08); min-height: 250px;
        display: flex; flex-direction: column; justify-content: center;
        align-items: center; text-align: center; border: 1px solid #E9ECEF;
        margin: 20px 0;
    }
    .q-text { font-size: 26px; color: #202124; font-weight: bold; margin-bottom: 20px; }
    .a-text { font-size: 20px; color: #1A73E8; border-top: 2px dashed #E8F0FE; padding-top: 20px; }
    .status-tag { font-size: 14px; padding: 2px 8px; border-radius: 10px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心数据加载 ---
def load_all_data():
    if not os.path.exists('flashcards.csv'):
        st.error("❌ 找不到 flashcards.csv 文件，请确保它在 GitHub 仓库中。")
        return []
    try:
        df = pd.read_csv('flashcards.csv', header=None, names=['q', 'a'])
        return df.to_dict('records')
    except Exception as e:
        st.error(f"数据读取失败: {e}")
        return []

all_cards = load_all_data()
all_answers = [c['a'] for c in all_cards]

# --- 3. 登录与进度管理 ---
st.title("📓 正念交易·精进终端")

c_user, c_mode = st.columns([1, 1])
with c_user:
    u_name = st.text_input("👤 学员姓名", value="guest").strip()
with c_mode:
    app_mode = st.selectbox("🎮 模式选择", ["学习模式", "考试模式"])

# 状态初始化
state_key = f"user_data_{u_name}"
if state_key not in st.session_state:
    path = f"progress_{u_name}.json"
    saved = None
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                saved = json.load(f)
        except: pass
    
    st.session_state[state_key] = {
        "mastered": set(saved['mastered']) if saved else set(),
        "current_idx": saved['last_index'] if saved else 0,
        "show_answer": False
    }

user_data = st.session_state[state_key]

def save_current():
    with open(f"progress_{u_name}.json", "w", encoding="utf-8") as f:
        json.dump({"mastered": list(user_data["mastered"]), "last_index": user_data["current_idx"]}, f)

# --- 4. 学习模式逻辑 (重制版) ---
if app_mode == "学习模式":
    # 快捷键支持脚本
    st.markdown("""<script>
        const doc = window.parent.document;
        doc.onkeydown = function(e) {
            if (e.keyCode === 32) doc.getElementById("btn-reveal").click();
            else if (e.keyCode === 39) doc.getElementById("btn-next").click();
            else if (e.keyCode === 37) doc.getElementById("btn-prev").click();
        };</script>""", unsafe_allow_html=True)

    if not all_cards:
        st.warning("暂无题目数据。")
    else:
        # 进度显示
        total = len(all_cards)
        m_count = len(user_data["mastered"])
        st.progress(m_count / total)
        st.write(f"学员: **{u_name}** | 已内化: {m_count} / {total}")

        # 计算索引并获取题目
        idx = user_data["current_idx"] % total
        card = all_cards[idx]
        is_m = card['q'] in user_data["mastered"]

        # 渲染卡片
        st.markdown(f"""
            <div class="card-box">
                <div style="color: {'#28a745' if is_m else '#ffc107'}; font-weight: bold;">
                    {'✅ 已掌握' if is_m else '⏳ 待复习'} (题目 {idx + 1} / {total})
                </div>
                <div class="q-text">{card['q']}</div>
                {"<div class='a-text'>" + card['a'] + "</div>" if user_data["show_answer"] else ""}
            </div>
        """, unsafe_allow_html=True)

        # 按钮控制
        b1, b2, b3, b4 = st.columns(4)
        with b1:
            if st.button("⬅️ 上一题", key="btn-prev", use_container_width=True):
                user_data["current_idx"] -= 1
                user_data["show_answer"] = False
                st.rerun()
        with b2:
            if st.button("👀 看答案", key="btn-reveal", use_container_width=True):
                user_data["show_answer"] = not user_data["show_answer"]
                st.rerun()
        with b3:
            if is_m:
                if st.button("⭐ 已掌握", type="primary", use_container_width=True):
                    user_data["mastered"].remove(card['q'])
                    save_current()
                    st.rerun()
            else:
                if st.button("标记掌握", use_container_width=True):
                    user_data["mastered"].add(card['q'])
                    save_current()
                    st.rerun()
        with b4:
            if st.button("下一题 ➡️", key="btn-next", use_container_width=True):
                user_data["current_idx"] += 1
                user_data["show_answer"] = False
                save_current()
                st.rerun()
        
        st.caption("提示：支持键盘左右箭头翻页，空格键看答案。")

# --- 5. 考试模式逻辑 (保持原样好用版) ---
else:
    if "exam_list" not in st.session_state:
        st.session_state.exam_list = None

    if st.session_state.exam_list is None:
        st.write("准备好了吗？点击下方按钮开始 20 题模拟考（限时 30 分钟）。")
        if st.button("🏁 开始考试", type="primary"):
            raw_exam = random.sample(all_cards, min(20, len(all_cards)))
            st.session_state.exam_list = []
            for r in raw_exam:
                wrong = random.sample([a for a in all_answers if a != r['a']], 3)
                opts = wrong + [r['a']]
                random.shuffle(opts)
                st.session_state.exam_list.append({"q": r['q'], "o": opts, "a": r['a']})
            st.session_state.exam_start = time.time()
            st.session_state.exam_ans = {}
            st.session_state.done = False
            st.rerun()
    else:
        elapsed = time.time() - st.session_state.exam_start
        left = max(0, 1800 - int(elapsed))
        st.subheader(f"⏳ 剩余时间 {left//60:02d}:{left%60:02d}")

        if left <= 0:
            st.error("时间到！请交卷。")

        with st.form("quiz_form"):
            for i, q in enumerate(st.session_state.exam_list):
                st.write(f"**{i+1}. {q['q']}**")
                st.session_state.exam_ans[i] = st.radio(f"选项_{i}", q['o'], key=f"ex_{i}", index=None, label_visibility="collapsed")
                st.write("---")
            if st.form_submit_button("📤 提交试卷并评分"):
                st.session_state.done = True

        if st.session_state.get("done"):
            score = sum(1 for i, q in enumerate(st.session_state.exam_list) if st.session_state.exam_ans.get(i) == q['a'])
            final_score = int(score / len(st.session_state.exam_list) * 100)
            st.header(f"📊 考试得分：{final_score} 分")
            if final_score >= 80: st.balloons()
            
            with st.expander("查看错题报告"):
                for i, q in enumerate(st.session_state.exam_list):
                    u_a = st.session_state.exam_ans.get(i)
                    is_right = (u_a == q['a'])
                    st.write(f"**Q{i+1}: {q['q']}**")
                    st.write(f"{'✅' if is_right else '❌'} 你的答案: {u_a}")
                    if not is_right: st.write(f"👉 正确答案: {q['a']}")
                    st.divider()

            if st.button("退出考场并清除记录"):
                st.session_state.exam_list = None
                st.session_state.done = False
                st.rerun()
