import streamlit as st
import pandas as pd
import random
import os
import json

# --- 1. 页面配置与美化 ---
st.set_page_config(page_title="正念交易学习指南", page_icon="📓", layout="centered")

# 定义持久化文件路径
PROGRESS_FILE = "study_progress.json"

# 加载 CSS (复刻 NotebookLM 风格)
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    .flashcard-container {
        background-color: white; padding: 50px; border-radius: 24px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08); min-height: 300px;
        display: flex; flex-direction: column; justify-content: center;
        align-items: center; text-align: center; border: 1px solid #E9ECEF;
        margin-top: 20px; transition: all 0.3s ease;
    }
    .question-text { font-size: 28px; color: #202124; font-weight: 700; margin-bottom: 25px; line-height: 1.4; }
    .answer-text { font-size: 22px; color: #1A73E8; font-weight: 500; border-top: 2px dashed #E8F0FE; padding-top: 25px; }
    .status-badge { background: #E8F0FE; color: #1967D2; padding: 4px 12px; border-radius: 50px; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心逻辑功能 ---

def save_progress():
    """保存进度到本地文件"""
    data = {
        "mastered": list(st.session_state.mastered),
        "last_index": st.session_state.idx
    }
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)

def load_progress():
    """从本地文件加载进度"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

# --- 3. 初始化状态 ---
if 'cards' not in st.session_state:
    df = pd.read_csv('flashcards.csv', header=None, names=['q', 'a'])
    st.session_state.cards = df.to_dict('records')

if 'initialized' not in st.session_state:
    progress = load_progress()
    if progress:
        # 如果发现历史记录，弹出选择框
        st.info("👋 欢迎回来！检测到上次的练习进度。")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🚀 接着上次继续"):
                st.session_state.mastered = set(progress['mastered'])
                st.session_state.idx = progress['last_index']
                st.session_state.initialized = True
                st.rerun()
        with col_b:
            if st.button("🧹 重新开始"):
                st.session_state.mastered = set()
                st.session_state.idx = 0
                st.session_state.initialized = True
                if os.path.exists(PROGRESS_FILE): os.remove(PROGRESS_FILE)
                st.rerun()
        st.stop()
    else:
        st.session_state.mastered = set()
        st.session_state.idx = 0
        st.session_state.initialized = True

if 'show' not in st.session_state: st.session_state.show = False

# --- 4. 快捷键监听 (黑科技) ---
# 使用 st.components 监听键盘事件
st.markdown("""
<script>
const doc = window.parent.document;
doc.onkeydown = function(e) {
    if (e.keyCode === 32) { // Space
        doc.getElementById("btn-reveal").click();
    } else if (e.keyCode === 39) { // Right Arrow
        doc.getElementById("btn-next").click();
    } else if (e.keyCode === 13) { // Enter
        doc.getElementById("btn-master").click();
    }
};
</script>
""", unsafe_allow_html=True)

# --- 5. 渲染界面 ---
remaining = [c for c in st.session_state.cards if c['q'] not in st.session_state.mastered]

st.title("📓 正念交易·精进指南")

if not remaining:
    st.balloons()
    st.success("🎉 太棒了！你已经完成了所有 75 个知识点的内化。")
    if st.button("重置系统"):
        st.session_state.mastered = set()
        if os.path.exists(PROGRESS_FILE): os.remove(PROGRESS_FILE)
        st.rerun()
else:
    # 进度条
    progress_val = len(st.session_state.mastered) / len(st.session_state.cards)
    st.progress(progress_val)
    st.caption(f"已内化: {len(st.session_state.mastered)} / {len(st.session_state.cards)} | 快捷键: 空格(看答案) , →(下一题) , Enter(掌握)")

    # 当前卡片
    curr_idx = st.session_state.idx % len(remaining)
    card = remaining[curr_idx]

    # 卡片展示
    st.markdown(f"""
        <div class="flashcard-container">
            <div class="status-badge">正念觉察中...</div>
            <div class="question-text">{card['q']}</div>
            {"<div class='answer-text'>" + card['a'] + "</div>" if st.session_state.show else ""}
        </div>
    """, unsafe_allow_html=True)

    # 隐藏的按钮供脚本调用
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("👀 看答案 (空格)", key="btn-reveal", use_container_width=True):
            st.session_state.show = not st.session_state.show
            st.rerun()
    with col2:
        if st.button("✅ 已掌握 (Enter)", key="btn-master", use_container_width=True):
            st.session_state.mastered.add(card['q'])
            st.session_state.show = False
            save_progress()
            st.rerun()
    with col3:
        if st.button("➡️ 下一题 (→)", key="btn-next", use_container_width=True):
            st.session_state.idx += 1
            st.session_state.show = False
            save_progress()
            st.rerun()

    # 退出功能
    st.markdown("---")
    if st.button("🚪 保存并退出学习"):
        save_progress()
        st.toast("进度已保存！下次打开将自动询问是否继续。")
        st.info("你可以直接关闭浏览器窗口了。交易顺遂，保持觉知。")