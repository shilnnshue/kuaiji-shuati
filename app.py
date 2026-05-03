import streamlit as st
import json
import random

st.set_page_config(page_title="会计刷题系统", page_icon="📚", layout="wide")
st.title("📖 会计刷题系统（无数据存储版）")

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

# ---------------------------- 科目配置 ----------------------------
SUBJECTS = {
    "初级会计实务": "questions.json",
    "经济法基础": "jingjifa.json"
}

# 初始化 session_state
if "subject" not in st.session_state:
    st.session_state.subject = "初级会计实务"
    st.session_state.questions = load_questions(SUBJECTS[st.session_state.subject])
    st.session_state.shuffle_opts = False
    st.session_state.mode = None
    st.session_state.q_list = []
    st.session_state.index = 0
    st.session_state.exam_answers = []

# 侧边栏：科目切换 + 选项乱序
with st.sidebar:
    st.header("⚙️ 设置")
    new_subject = st.selectbox("选择科目", list(SUBJECTS.keys()), index=0)
    if new_subject != st.session_state.subject:
        st.session_state.subject = new_subject
        st.session_state.questions = load_questions(SUBJECTS[new_subject])
        st.session_state.mode = None
        st.rerun()
    st.session_state.shuffle_opts = st.checkbox("选项乱序", value=st.session_state.shuffle_opts)
    st.markdown("---")
    st.caption("提示：本系统不保存任何练习记录，刷新页面即重置。")

# 如果题库为空，显示错误
if not st.session_state.questions:
    st.error(f"未找到题库文件：{SUBJECTS[st.session_state.subject]}，请检查文件是否存在。")
    st.stop()

# ---------------------------- 辅助函数 ----------------------------
def display_question(q):
    opts = q['options']
    if st.session_state.shuffle_opts and q['type'] != 'judge':
        items = list(opts.items())
        random.shuffle(items)
        opts = dict(items)
        mapping = {chr(65+i): k for i, (k, v) in enumerate(items)}
        return opts, mapping
    return opts, None

def check_answer(q, user_ans, mapping=None):
    if q['type'] == 'multiple':
        user = ''.join(sorted([x.strip() for x in user_ans.replace(',', '').replace(' ', '')]))
        if mapping:
            user = ''.join(sorted([mapping[ch] for ch in user if ch in mapping]))
        return user == q['answer'], user, q['answer']
    else:
        user = user_ans.strip().upper()
        if mapping and len(user)==1 and user in mapping:
            user = mapping[user]
        return user == q['answer'], user, q['answer']

def start_practice(q_list):
    st.session_state.mode = "practice"
    st.session_state.q_list = q_list
    st.session_state.index = 0

# ---------------------------- 主菜单 ----------------------------
if st.session_state.mode is None:
    st.header("🏠 主菜单")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📖 顺序练习（全部）", use_container_width=True):
            start_practice(st.session_state.questions[:])
        if st.button("🎲 随机练习（全部）", use_container_width=True):
            q_list = st.session_state.questions[:]
            random.shuffle(q_list)
            start_practice(q_list)
        if st.button("📚 按章节练习", use_container_width=True):
            chapters = sorted(set(q['chapter'] for q in st.session_state.questions))
            st.session_state.temp_chapters = chapters
            st.session_state.mode = "select_chapter"
            st.rerun()
        if st.button("🔍 按题型练习", use_container_width=True):
            st.session_state.mode = "select_type"
            st.rerun()
    with col2:
        if st.button("✍️ 模拟考试", use_container_width=True):
            st.session_state.mode = "exam_setup"
            st.rerun()
        if st.button("🔎 搜索题目", use_container_width=True):
            st.session_state.mode = "search"
            st.rerun()
        if st.button("🚪 退出系统", use_container_width=True):
            st.balloons()
            st.stop()

# ---------------------------- 按章节练习 --------------------------
elif st.session_state.mode == "select_chapter":
    st.header("📚 按章节练习")
    selected = st.selectbox("选择章节", st.session_state.temp_chapters)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("顺序练习该章节"):
            q_list = [q for q in st.session_state.questions if q['chapter'] == selected]
            start_practice(q_list)
    with col2:
        if st.button("随机练习该章节"):
            q_list = [q for q in st.session_state.questions if q['chapter'] == selected]
            random.shuffle(q_list)
            start_practice(q_list)
    if st.button("返回主菜单"):
        st.session_state.mode = None
        st.rerun()

# ---------------------------- 按题型练习 --------------------------
elif st.session_state.mode == "select_type":
    st.header("🔍 按题型练习")
    type_map = {"单选题": "single", "多选题": "multiple", "判断题": "judge"}
    selected_type_label = st.selectbox("选择题型", list(type_map.keys()))
    selected_type = type_map[selected_type_label]
    col1, col2 = st.columns(2)
    with col1:
        if st.button("顺序练习"):
            q_list = [q for q in st.session_state.questions if q['type'] == selected_type]
            start_practice(q_list)
    with col2:
        if st.button("随机练习"):
            q_list = [q for q in st.session_state.questions if q['type'] == selected_type]
            random.shuffle(q_list)
            start_practice(q_list)
    if st.button("返回主菜单"):
        st.session_state.mode = None
        st.rerun()

# ---------------------------- 模拟考试 --------------------------
elif st.session_state.mode == "exam_setup":
    st.header("✍️ 模拟考试")
    num = st.number_input("题目数量", min_value=1, max_value=len(st.session_state.questions), value=30)
    if st.button("开始考试"):
        exam_qs = random.sample(st.session_state.questions, min(num, len(st.session_state.questions)))
        st.session_state.mode = "exam"
        st.session_state.q_list = exam_qs
        st.session_state.index = 0
        st.session_state.exam_answers = []
        st.rerun()
    if st.button("返回"):
        st.session_state.mode = None
        st.rerun()

elif st.session_state.mode == "exam":
    total = len(st.session_state.q_list)
    idx = st.session_state.index
    if idx >= total:
        # 考试结束，判卷
        score = 0
        st.subheader("考试结果")
        for q, ua in st.session_state.exam_answers:
            if ua == q['answer']:
                score += 1
            else:
                st.write(f"❌ 第 {q['number']} 题 错误，正确答案：{q['answer']}，你的答案：{ua}")
                st.write(f"解析：{q['explanation']}")
        st.success(f"得分：{score}/{total}，正确率：{score/total*100:.1f}%")
        if st.button("返回主菜单"):
            st.session_state.mode = None
            st.rerun()
    else:
        q = st.session_state.q_list[idx]
        st.subheader(f"第 {idx+1}/{total} 题")
        opts, mapping = display_question(q)
        st.write(f"**{q['number']}. {q['text']}**")
        for opt_char, opt_text in opts.items():
            st.write(f"{opt_char}. {opt_text}")
        if q['type'] == 'multiple':
            user_ans = st.text_input("答案（多选用逗号分隔）", key=f"exam_{idx}")
        else:
            user_ans = st.text_input("答案（填字母）", key=f"exam_{idx}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("下一题", key="next_exam"):
                # 不判对错，只记录答案
                user_ans_clean = user_ans.strip().upper()
                st.session_state.exam_answers.append((q, user_ans_clean))
                st.session_state.index += 1
                st.rerun()
        with col2:
            if st.button("退出考试"):
                st.session_state.mode = None
                st.rerun()

# ---------------------------- 搜索题目 --------------------------
elif st.session_state.mode == "search":
    st.header("🔎 搜索题目")
    keyword = st.text_input("输入题号或关键词")
    if keyword:
        if keyword.isdigit():
            qid = int(keyword)
            for q in st.session_state.questions:
                if q['number'] == qid:
                    st.subheader(f"题目 {qid}")
                    st.write(q['text'])
                    for opt, text in q['options'].items():
                        st.write(f"{opt}. {text}")
                    st.write(f"答案：{q['answer']}")
                    st.write(f"解析：{q['explanation']}")
                    break
            else:
                st.warning("未找到该题号")
        else:
            results = [q for q in st.session_state.questions if keyword.lower() in q['text'].lower() or any(keyword.lower() in opt.lower() for opt in q['options'].values())]
            if not results:
                st.warning("未找到匹配题目")
            else:
                st.subheader(f"找到 {len(results)} 道题目：")
                for q in results[:20]:
                    st.write(f"**{q['number']}.** {q['text'][:100]}...")
    if st.button("返回主菜单"):
        st.session_state.mode = None
        st.rerun()

# ---------------------------- 通用练习模式 --------------------------
elif st.session_state.mode == "practice":
    total = len(st.session_state.q_list)
    idx = st.session_state.index
    if idx >= total:
        st.success("恭喜！你已完成本次练习！")
        if st.button("返回主菜单"):
            st.session_state.mode = None
            st.rerun()
    else:
        q = st.session_state.q_list[idx]
        st.subheader(f"第 {idx+1}/{total} 题")
        opts, mapping = display_question(q)
        st.write(f"**{q['number']}. {q['text']}**")
        for opt_char, opt_text in opts.items():
            st.write(f"{opt_char}. {opt_text}")
        if q['type'] == 'multiple':
            user_ans = st.text_input("你的答案（多选用逗号分隔）", key=f"ans_{idx}")
        else:
            user_ans = st.text_input("你的答案（填字母）", key=f"ans_{idx}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("提交并继续", key=f"submit_{idx}"):
                ok, ua, ca = check_answer(q, user_ans, mapping)
                st.write("---")
                if ok:
                    st.success("✓ 回答正确")
                else:
                    st.error(f"✗ 回答错误，你的答案：{ua}，正确答案：{ca}")
                if q['explanation']:
                    st.info(f"📖 解析：{q['explanation']}")
                if st.button("下一题"):
                    st.session_state.index += 1
                    st.rerun()
        with col2:
            if st.button("退出练习"):
                st.session_state.mode = None
                st.rerun()