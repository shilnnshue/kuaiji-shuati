import streamlit as st
import json
import random

st.set_page_config(page_title="会计刷题系统", page_icon="📚", layout="wide")

# ---------------------------- 加载题库 ----------------------------
@st.cache_resource
def load_questions(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            qs = json.load(f)
        for q in qs:
            if 'chapter' not in q or not q['chapter']:
                q['chapter'] = "未分类"
        return qs
    except FileNotFoundError:
        return []

# 科目配置
SUBJECTS = {
    "初级会计实务": "questions.json",
    "经济法基础": "jingjifa.json"
}

# 初始化 session_state
if "subject" not in st.session_state:
    st.session_state.subject = "初级会计实务"
    st.session_state.questions = load_questions(SUBJECTS[st.session_state.subject])
    st.session_state.shuffle_opts = False
    st.session_state.mode = "menu"           # menu, practice, exam, chapter_select, type_select, search
    st.session_state.q_list = []
    st.session_state.index = 0
    st.session_state.exam_answers = []
    st.session_state.user_answer = ""        # 当前题目的临时答案
    st.session_state.show_result = False     # 是否显示判题结果
    st.session_state.result_info = None      # 存储判题结果信息

# ---------------------------- 侧边栏设置 ----------------------------
with st.sidebar:
    st.header("⚙️ 设置")
    new_subject = st.selectbox("选择科目", list(SUBJECTS.keys()))
    if new_subject != st.session_state.subject:
        st.session_state.subject = new_subject
        st.session_state.questions = load_questions(SUBJECTS[new_subject])
        st.session_state.mode = "menu"
        st.rerun()
    st.session_state.shuffle_opts = st.checkbox("选项乱序", value=st.session_state.shuffle_opts)
    st.markdown("---")
    st.caption("📌 点击下方菜单开始练习")
    
    # 主菜单按钮（始终显示）
    if st.button("🏠 主菜单", use_container_width=True):
        st.session_state.mode = "menu"
        st.rerun()
    if st.button("📖 顺序练习（全部）", use_container_width=True):
        st.session_state.mode = "practice"
        st.session_state.q_list = st.session_state.questions[:]
        st.session_state.index = 0
        st.session_state.show_result = False
        st.rerun()
    if st.button("🎲 随机练习（全部）", use_container_width=True):
        q_list = st.session_state.questions[:]
        random.shuffle(q_list)
        st.session_state.mode = "practice"
        st.session_state.q_list = q_list
        st.session_state.index = 0
        st.session_state.show_result = False
        st.rerun()
    if st.button("📚 按章节练习", use_container_width=True):
        chapters = sorted(set(q['chapter'] for q in st.session_state.questions))
        st.session_state.temp_chapters = chapters
        st.session_state.mode = "chapter_select"
        st.rerun()
    if st.button("🔍 按题型练习", use_container_width=True):
        st.session_state.mode = "type_select"
        st.rerun()
    if st.button("✍️ 模拟考试", use_container_width=True):
        st.session_state.mode = "exam_setup"
        st.rerun()
    if st.button("🔎 搜索题目", use_container_width=True):
        st.session_state.mode = "search"
        st.rerun()

# ---------------------------- 辅助函数 ----------------------------
def display_question(q, shuffle):
    opts = q['options']
    if shuffle and q['type'] != 'judge':
        items = list(opts.items())
        random.shuffle(items)
        opts = dict(items)
        mapping = {chr(65+i): k for i, (k, v) in enumerate(items)}
        return opts, mapping
    return opts, None

def check_answer(q, user_ans, mapping=None):
    if q['type'] == 'multiple':
        # 多选答案处理，例如 "A,C" -> "AC"
        user = ''.join(sorted([x.strip() for x in user_ans.replace(',', '').replace(' ', '')]))
        if mapping:
            user = ''.join(sorted([mapping[ch] for ch in user if ch in mapping]))
        return user == q['answer'], user, q['answer']
    else:
        user = user_ans.strip().upper()
        if mapping and len(user) == 1 and user in mapping:
            user = mapping[user]
        return user == q['answer'], user, q['answer']

def clear_practice_state():
    st.session_state.q_list = []
    st.session_state.index = 0
    st.session_state.show_result = False
    st.session_state.result_info = None
    st.session_state.user_answer = ""

# ---------------------------- 页面内容 ----------------------------
st.title("📖 会计刷题系统")

# 模式：主菜单
if st.session_state.mode == "menu":
    st.info("👈 请从左侧侧边栏选择练习模式")
    st.image("https://img.icons8.com/color/96/000000/books.png", width=100)
    st.markdown("""
    ### 功能说明
    - **顺序练习**：按题库顺序做题
    - **随机练习**：打乱顺序
    - **按章节练习**：选择特定章节
    - **按题型练习**：单选/多选/判断
    - **模拟考试**：随机抽题，最后判分
    - **搜索题目**：按题号或关键词查找
    """)

# 模式：按章节选择
elif st.session_state.mode == "chapter_select":
    st.subheader("📚 选择章节")
    chapters = st.session_state.temp_chapters
    col1, col2 = st.columns(2)
    with col1:
        selected_ch = st.selectbox("章节", chapters)
    with col2:
        if st.button("顺序练习该章节"):
            q_list = [q for q in st.session_state.questions if q['chapter'] == selected_ch]
            st.session_state.mode = "practice"
            st.session_state.q_list = q_list
            st.session_state.index = 0
            st.session_state.show_result = False
            st.rerun()
        if st.button("随机练习该章节"):
            q_list = [q for q in st.session_state.questions if q['chapter'] == selected_ch]
            random.shuffle(q_list)
            st.session_state.mode = "practice"
            st.session_state.q_list = q_list
            st.session_state.index = 0
            st.session_state.show_result = False
            st.rerun()
    if st.button("返回主菜单"):
        st.session_state.mode = "menu"
        st.rerun()

# 模式：按题型选择
elif st.session_state.mode == "type_select":
    st.subheader("🔍 按题型练习")
    type_map = {"单选题": "single", "多选题": "multiple", "判断题": "judge"}
    selected_label = st.selectbox("题型", list(type_map.keys()))
    selected_type = type_map[selected_label]
    col1, col2 = st.columns(2)
    with col1:
        if st.button("顺序练习"):
            q_list = [q for q in st.session_state.questions if q['type'] == selected_type]
            st.session_state.mode = "practice"
            st.session_state.q_list = q_list
            st.session_state.index = 0
            st.session_state.show_result = False
            st.rerun()
    with col2:
        if st.button("随机练习"):
            q_list = [q for q in st.session_state.questions if q['type'] == selected_type]
            random.shuffle(q_list)
            st.session_state.mode = "practice"
            st.session_state.q_list = q_list
            st.session_state.index = 0
            st.session_state.show_result = False
            st.rerun()
    if st.button("返回主菜单"):
        st.session_state.mode = "menu"
        st.rerun()

# 模式：模拟考试设置
elif st.session_state.mode == "exam_setup":
    st.subheader("✍️ 模拟考试")
    num = st.number_input("题目数量", min_value=1, max_value=len(st.session_state.questions), value=30)
    if st.button("开始考试"):
        exam_qs = random.sample(st.session_state.questions, min(num, len(st.session_state.questions)))
        st.session_state.mode = "exam"
        st.session_state.q_list = exam_qs
        st.session_state.index = 0
        st.session_state.exam_answers = []
        st.session_state.show_result = False
        st.rerun()
    if st.button("返回"):
        st.session_state.mode = "menu"
        st.rerun()

# 模式：考试中
elif st.session_state.mode == "exam":
    total = len(st.session_state.q_list)
    idx = st.session_state.index
    if idx >= total:
        # 考试结束，判分
        score = 0
        st.subheader("考试结果")
        for q, ua in st.session_state.exam_answers:
            if ua == q['answer']:
                score += 1
            else:
                st.error(f"❌ 第 {q['number']} 题 错误，正确答案：{q['answer']}，你的答案：{ua}")
                st.info(f"解析：{q['explanation']}")
        st.success(f"得分：{score}/{total} ({score/total*100:.1f}%)")
        if st.button("返回主菜单"):
            st.session_state.mode = "menu"
            st.rerun()
    else:
        q = st.session_state.q_list[idx]
        st.subheader(f"第 {idx+1}/{total} 题")
        opts, mapping = display_question(q, st.session_state.shuffle_opts)
        st.write(f"**{q['number']}. {q['text']}**")
        for opt_char, opt_text in opts.items():
            st.write(f"{opt_char}. {opt_text}")
        if q['type'] == 'multiple':
            user_ans = st.text_input("答案（多选用逗号分隔，如 A,C）", key=f"exam_{idx}")
        else:
            user_ans = st.text_input("答案（填字母）", key=f"exam_{idx}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("下一题", key=f"next_exam_{idx}"):
                st.session_state.exam_answers.append((q, user_ans.strip().upper()))
                st.session_state.index += 1
                st.rerun()
        with col2:
            if st.button("退出考试"):
                st.session_state.mode = "menu"
                st.rerun()

# 模式：搜索题目
elif st.session_state.mode == "search":
    st.subheader("🔎 搜索题目")
    keyword = st.text_input("输入题号或关键词")
    if keyword:
        if keyword.isdigit():
            qid = int(keyword)
            results = [q for q in st.session_state.questions if q['number'] == qid]
        else:
            results = [q for q in st.session_state.questions if keyword.lower() in q['text'].lower() or any(keyword.lower() in opt.lower() for opt in q['options'].values())]
        if not results:
            st.warning("未找到")
        else:
            for q in results[:20]:
                with st.expander(f"【{q['type']}】{q['number']}. {q['text'][:80]}"):
                    for opt, txt in q['options'].items():
                        st.write(f"{opt}. {txt}")
                    st.write(f"答案：{q['answer']}")
                    st.write(f"解析：{q['explanation']}")
    if st.button("返回主菜单"):
        st.session_state.mode = "menu"
        st.rerun()

# 模式：普通练习（顺序/随机/按章节/按题型）
elif st.session_state.mode == "practice":
    total = len(st.session_state.q_list)
    idx = st.session_state.index
    
    if idx >= total:
        st.success("🎉 恭喜！你已完成本轮练习！")
        if st.button("返回主菜单"):
            st.session_state.mode = "menu"
            st.rerun()
    else:
        q = st.session_state.q_list[idx]
        st.subheader(f"第 {idx+1} / {total} 题")
        
        # 显示题目和选项
        opts, mapping = display_question(q, st.session_state.shuffle_opts)
        st.write(f"**{q['number']}. {q['text']}**")
        for opt_char, opt_text in opts.items():
            st.write(f"{opt_char}. {opt_text}")
        
        # 输入答案
        if q['type'] == 'multiple':
            user_ans = st.text_input("你的答案（多选用逗号分隔，如 A,C）", value=st.session_state.user_answer, key=f"ans_{idx}")
        else:
            user_ans = st.text_input("你的答案（填字母）", value=st.session_state.user_answer, key=f"ans_{idx}")
        st.session_state.user_answer = user_ans
        
        # 提交按钮
        if st.button("提交答案", key=f"submit_{idx}"):
            ok, ua, ca = check_answer(q, user_ans, mapping)
            if ok:
                st.session_state.result_info = f"✅ 回答正确！ 正确答案：{ca}"
            else:
                st.session_state.result_info = f"❌ 回答错误！ 你的答案：{ua}，正确答案：{ca}"
            if q['explanation']:
                st.session_state.result_info += f"\n📖 解析：{q['explanation']}"
            st.session_state.show_result = True
        
        # 显示判题结果
        if st.session_state.show_result and st.session_state.result_info:
            st.info(st.session_state.result_info)
        
        # 下一题按钮（独立于提交，确保先提交才能点下一题）
        if st.session_state.show_result:
            if st.button("下一题 ➡️", key=f"next_{idx}"):
                st.session_state.index += 1
                st.session_state.show_result = False
                st.session_state.result_info = None
                st.session_state.user_answer = ""
                st.rerun()
        
        # 退出练习按钮
        if st.button("退出练习"):
            st.session_state.mode = "menu"
            st.rerun()