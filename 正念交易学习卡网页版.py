import streamlit as st
import pandas as pd
import random
import time
import json
import os

# --- 1. 页面配置 ---
st.set_page_config(page_title="正念交易·考场", page_icon="🎓", layout="centered")

# CSS 样式（保持 NotebookLM 风格并增加考场氛围）
st.markdown("""
    <style>
    .stApp { background-color: #F4F7F9; }
    .exam-card {
        background-color: white; padding: 30px; border-radius: 15px;
        border-left: 5px solid #1A73E8; box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .question-text { font-size: 20px; font-weight: 600; color: #333; margin-bottom: 15px; }
    .timer-text { font-size: 24px; font-weight: bold; color: #D93025; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 数据加载与处理 ---
@st.cache_data
def load_data():
    df = pd.read_csv('flashcards.csv', header=None, names=['q', 'a'])
    return df.to_dict('records')

all_cards = load_data()
all_answers = [c['a'] for c in all_cards]

# --- 3. 核心逻辑：生成考卷 ---
def generate_exam(count=20):
    exam_questions = random.sample(all_cards, min(count, len(all_cards)))
    quiz_data = []
    for item in exam_questions:
        correct_split = item['a']
        # 随机抽取 3 个错误答案
        distractors = random.sample([a for a in all_answers if a != correct_split], 3)
        options = distractors + [correct_split]
        random.shuffle(options)
        quiz_data.append({
            "question": item['q'],
            "options": options,
            "answer": correct_split
        })
    return quiz_data

# --- 4. Session State 初始化 ---
if 'mode' not in st.session_state: st.session_state.mode = "学习"
if 'exam_data' not in st.session_state: st.session_state.exam_data = None
if 'start_time' not in st.session_state: st.session_state.start_time = None
if 'submitted' not in st.session_state: st.session_state.submitted = False

# --- 5. 侧边栏：模式切换 ---
with st.sidebar:
    st.title("🎯 模式选择")
    mode = st.radio("请选择当前状态：", ["常规练习", "考场模式"])
    st.session_state.mode = mode
    
    if mode == "考场模式":
        st.warning("⚠️ 考场规则：\n1. 随机 20 题\n2. 限时 30 分钟\n3. 提交后显示评分")
        if st.button("🏁 开始新考试"):
            st.session_state.exam_data = generate_exam(20)
            st.session_state.start_time = time.time()
            st.session_state.submitted = False
            st.session_state.user_answers = {}
            st.rerun()

# --- 6. 渲染界面 ---

# --- A. 常规练习模式 (保留你之前的代码逻辑) ---
if st.session_state.mode == "常规练习":
    st.title("📓 正念交易·精进指南")
    st.info("当前为学习模式，请点击侧边栏进入考场模式进行测试。")
    # (此处可插入你之前的闪卡代码，为简洁此处省略，实际使用时建议合并)

# --- B. 考场模式 ---
else:
    st.title("🎓 正念交易·模拟考场")
    
    if st.session_state.exam_data is None:
        st.info("请点击左侧按钮“开始新考试”生成考卷。")
    else:
        # 计时器逻辑
        elapsed = time.time() - st.session_state.start_time
        remaining = max(0, 1800 - int(elapsed)) # 30分钟 = 1800秒
        
        col1, col2 = st.columns([3, 1])
        with col2:
            st.markdown(f'<div class="timer-text">⏳ {remaining//60:02d}:{remaining%60:02d}</div>', unsafe_allow_html=True)
        
        if remaining <= 0 and not st.session_state.submitted:
            st.error("⏰ 时间到！系统已自动交卷。")
            st.session_state.submitted = True

        # 显示题目
        with st.form("exam_form"):
            for i, q in enumerate(st.session_state.exam_data):
                st.markdown(f'<div class="exam-card">', unsafe_allow_html=True)
                st.markdown(f'<div class="question-text">{i+1}. {q["question"]}</div>', unsafe_allow_html=True)
                
                # 用户选择
                st.session_state.user_answers[i] = st.radio(
                    "选择正确答案：", 
                    q["options"], 
                    key=f"q{i}",
                    index=None,
                    label_visibility="collapsed"
                )
                st.markdown('</div>', unsafe_allow_html=True)
            
            submit_btn = st.form_submit_button("📤 提交考卷")
            if submit_btn:
                st.session_state.submitted = True
                st.rerun()

        # 评分系统
        if st.session_state.submitted:
            score = 0
            results = []
            for i, q in enumerate(st.session_state.exam_data):
                u_ans = st.session_state.user_answers.get(i)
                is_correct = (u_ans == q["answer"])
                if is_correct: score += 1
                results.append({"q": q["question"], "u": u_ans, "correct": q["answer"], "res": is_correct})
            
            final_score = int((score / len(st.session_state.exam_data)) * 100)
            
            st.markdown("---")
            st.header(f"📊 考试成绩：{final_score} 分")
            if final_score >= 80: st.balloons()
            
            # 错题回顾
            with st.expander("查看答题报告"):
                for r in results:
                    color = "green" if r['res'] else "red"
                    st.markdown(f"**问：{r['q']}**")
                    st.markdown(f"您的答案：:{color}[{r['u']}]")
                    if not r['res']:
                        st.markdown(f"正确答案：:green[{r['correct']}]")
                    st.write("---")