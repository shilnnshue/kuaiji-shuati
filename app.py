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

SUBJECTS = {
    "初级会计实务": "questions.json",
    "经济法基础": "jingjifa.json"
}

# 初始化 session_state
if "subject" not in st.session_state:
    st.session_state.subject = "初级会计实务"
    st.session_state.questions = load_questions(SUBJECTS[st.session_state.subject])
    st.session_state.shuffle_opts = False
    st.session_state.mode = "menu"
    st.session_state.q_list = []
    st.session_state.index = 0
    st.session_state.exam_answers = []
    st.session_state.selected_options = []
    st.session_state.radio_choice = None
    st.session_state.show_result = False
    st.session_state.result_info = None

# ---------------------------- 侧边栏 ----------------------------
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

def check_selected(q, selected, mapping=None):
    if q['type'] == 'multiple':
        if mapping:
            selected_orig = [mapping[ch] for ch in selected if ch in mapping]
        else:
            selected_orig = selected
        selected_orig.sort()
        user_ans = ''.join(selected_orig)
        return user_ans == q['answer'], user_ans, q['answer']
    else:
        if mapping and selected in mapping:
            selected_orig = mapping[selected]
        else:
            selected_orig = selected
        return selected_orig == q['answer'], selected_orig, q['answer']

def clear_practice_state():
    st.session_state.show_result = False
    st.session_state.result_info = None
    st.session_state.selected_options = []
    st.session_state.radio_choice = None

# ---------------------------- 页面内容 ----------------------------
st.title("📖 会计刷题系统")

# 主菜单
if st.session_state.mode == "menu":
    st.info("👈 请从左侧侧边栏选择练习模式")
    st.markdown("### 功能说明")
    st.markdown("- **顺序/随机练习**：直接开始\n- **按章节练习**：选择特定章节\n- **按题型练习**：单选/多选/判断\n- **模拟考试**：随机抽题，最后判分\n- **搜索题目**：查找题目详情")

# 按章节选择
elif st.session_state.mode == "chapter_select":
    st.subheader("📚 选择章节")
    chapters = st.session_state.temp_chapters
    selected_ch = st.selectbox("章节", chapters)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("顺序练习该章节"):
            q_list = [q for q in st.session_state.questions if q['chapter'] == selected_ch]
            st.session_state.mode = "practice"
            st.session_state.q_list = q_list
            st.session_state.index = 0
            clear_practice_state()
            st.rerun()
    with col2:
        if st.button("随机练习该章节"):
            q_list = [q for q in st.session_state.questions if q['chapter'] == selected_ch]
            random.shuffle(q_list)
            st.session_state.mode = "practice"
            st.session_state.q_list = q_list
            st.session_state.index = 0
            clear_practice_state()
            st.rerun()
    if st.button("返回主菜单"):
        st.session_state.mode = "menu"
        st.rerun()

# 按题型选择
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
            clear_practice_state()
            st.rerun()
    with col2:
        if st.button("随机练习"):
            q_list = [q for q in st.session_state.questions if q['type'] == selected_type]
            random.shuffle(q_list)
            st.session_state.mode = "practice"
            st.session_state.q_list = q_list
            st.session_state.index = 0
            clear_practice_state()
            st.rerun()
    if st.button("返回主菜单"):
        st.session_state.mode = "menu"
        st.rerun()

# 模拟考试设置
elif st.session_state.mode == "exam_setup":
    st.subheader("✍️ 模拟考试")
    num = st.number_input("题目数量", min_value=1, max_value=len(st.session_state.questions), value=30)
    if st.button("开始考试"):
        exam_qs = random.sample(st.session_state.questions, min(num, len(st.session_state.questions)))
        st.session_state.mode = "exam"
        st.session_state.q_list = exam_qs
        st.session_state.index = 0
        st.session_state.exam_answers = []
        clear_practice_state()
        st.rerun()
    if st.button("返回"):
        st.session_state.mode = "menu"
        st.rerun()

# 考试中（保持原样）
elif st.session_state.mode == "exam":
    total = len(st.session_state.q_list)
    idx = st.session_state.index
    if idx >= total:
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
        
        if q['type'] == 'multiple':
            selected = []
            for k, v in opts.items():
                if st.checkbox(f"{k}. {v}", key=f"exam_multi_{idx}_{k}"):
                    selected.append(k)
            user_ans = ''.join(sorted([mapping[k] if mapping else k for k in selected]))
        elif q['type'] == 'judge':
            choice = st.radio("请选择", ["正确", "错误"], key=f"exam_judge_{idx}", horizontal=False)
            user_ans = "A" if choice == "正确" else "B"
            if mapping:
                user_ans = mapping.get(user_ans, user_ans)
        else:
            opt_keys = list(opts.keys())
            choice = st.radio("请选择", [f"{k}. {opts[k]}" for k in opt_keys], key=f"exam_single_{idx}", horizontal=False)
            user_ans = choice.split(".")[0].strip()
            if mapping:
                user_ans = mapping.get(user_ans, user_ans)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("下一题", key=f"next_exam_{idx}"):
                st.session_state.exam_answers.append((q, user_ans))
                st.session_state.index += 1
                st.rerun()
        with col2:
            if st.button("退出考试"):
                st.session_state.mode = "menu"
                st.rerun()

# 搜索题目
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

# ---------------------------- 普通练习（支持左右键，上下题同时显示）----------------------------
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
        
        opts, mapping = display_question(q, st.session_state.shuffle_opts)
        st.write(f"**{q['number']}. {q['text']}**")
        
        user_ans = None
        
        if q['type'] == 'multiple':
            selected = []
            for k, v in opts.items():
                if st.checkbox(f"{k}. {v}", key=f"multi_{idx}_{k}"):
                    selected.append(k)
            if selected:
                if mapping:
                    orig_selected = [mapping[ch] for ch in selected if ch in mapping]
                else:
                    orig_selected = selected
                orig_selected.sort()
                user_ans = ''.join(orig_selected)
        elif q['type'] == 'judge':
            choice = st.radio("请选择", ["正确", "错误"], key=f"judge_{idx}", horizontal=False)
            selected = "A" if choice == "正确" else "B"
            if mapping:
                user_ans = mapping.get(selected, selected)
            else:
                user_ans = selected
        else:
            opt_keys = list(opts.keys())
            choice = st.radio("请选择", [f"{k}. {opts[k]}" for k in opt_keys], key=f"single_{idx}", horizontal=False)
            selected = choice.split(".")[0].strip()
            if mapping:
                user_ans = mapping.get(selected, selected)
            else:
                user_ans = selected
        
        # 提交按钮
        if st.button("提交答案", key=f"submit_{idx}"):
            if user_ans is None:
                st.warning("请先选择一个选项")
            else:
                ok, ua, ca = check_selected(q, user_ans, mapping if q['type']!='multiple' else None)
                if ok:
                    st.session_state.result_info = f"✅ 回答正确！ 正确答案：{ca}"
                else:
                    st.session_state.result_info = f"❌ 回答错误！ 你的答案：{ua}，正确答案：{ca}"
                if q['explanation']:
                    st.session_state.result_info += f"\n📖 解析：{q['explanation']}"
                st.session_state.show_result = True
        
        if st.session_state.show_result and st.session_state.result_info:
            st.info(st.session_state.result_info)
        
        # 上一题 / 下一题 按钮（始终显示，只要存在即可）
        col_left, col_mid, col_right = st.columns([1,1,1])
        with col_left:
            if idx > 0:
                if st.button("⬅️ 上一题", key="prev_btn"):
                    st.session_state.index -= 1
                    st.session_state.show_result = False
                    st.session_state.result_info = None
                    st.rerun()
        with col_right:
            if idx < total - 1:
                if st.button("下一题 ➡️", key="next_btn"):
                    st.session_state.index += 1
                    st.session_state.show_result = False
                    st.session_state.result_info = None
                    st.rerun()
        with col_mid:
            if st.button("退出练习"):
                st.session_state.mode = "menu"
                st.rerun()
        
        # 键盘左右键监听
        st.markdown("""
        <script>
        document.addEventListener('keydown', function(e) {
            if (e.key === 'ArrowLeft') {
                var buttons = document.querySelectorAll('button');
                for (var btn of buttons) {
                    if (btn.innerText.includes('上一题')) {
                        btn.click();
                        break;
                    }
                }
            } else if (e.key === 'ArrowRight') {
                var buttons = document.querySelectorAll('button');
                for (var btn of buttons) {
                    if (btn.innerText.includes('下一题')) {
                        btn.click();
                        break;
                    }
                }
            }
        });
        </script>
        """, unsafe_allow_html=True)