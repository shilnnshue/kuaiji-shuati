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
    st.session_state.exam_answers = {}        # 键：题号，值：用户答案字符串
    st.session_state.favorites = set()        # 收藏的题号
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
    if st.button("❤️ 我的收藏", use_container_width=True):
        fav_qs = [q for q in st.session_state.questions if q['number'] in st.session_state.favorites]
        if fav_qs:
            st.session_state.mode = "practice"
            st.session_state.q_list = fav_qs
            st.session_state.index = 0
            st.session_state.show_result = False
            st.rerun()
        else:
            st.warning("暂无收藏题目")

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
    """selected: 对于多选是排序后的字符串，对于单选/判断是单个字母"""
    if q['type'] == 'multiple':
        if not selected:
            return False, "", q['answer']
        # selected 已经是排序后的字符串，直接比较
        return selected == q['answer'], selected, q['answer']
    else:
        if mapping and selected in mapping:
            selected_orig = mapping[selected]
        else:
            selected_orig = selected
        return selected_orig == q['answer'], selected_orig, q['answer']

def clear_practice_state():
    st.session_state.show_result = False
    st.session_state.result_info = None

def add_favorite(q_num):
    st.session_state.favorites.add(q_num)
    st.toast(f"已收藏第 {q_num} 题", icon="❤️")

def remove_favorite(q_num):
    st.session_state.favorites.discard(q_num)
    st.toast(f"已取消收藏第 {q_num} 题", icon="💔")

# ---------------------------- 页面内容 ----------------------------
st.title("📖 会计刷题系统")

# 主菜单
if st.session_state.mode == "menu":
    st.info("👈 请从左侧侧边栏选择练习模式")
    st.markdown("### 功能说明")
    st.markdown("- **顺序/随机练习**：直接开始\n- **按章节练习**：选择特定章节\n- **按题型练习**：单选/多选/判断\n- **模拟考试**：随机抽题，最后判分\n- **搜索题目**：查找题目详情\n- **我的收藏**：查看已收藏的题目")

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
        st.session_state.exam_answers = {}       # 清空已有答案
        clear_practice_state()
        st.rerun()
    if st.button("返回"):
        st.session_state.mode = "menu"
        st.rerun()

# 考试中（带答题卡）
elif st.session_state.mode == "exam":
    total = len(st.session_state.q_list)
    idx = st.session_state.index
    
    # 侧边栏显示答题卡
    with st.sidebar:
        st.markdown("### 📋 答题卡")
        col1, col2, col3 = st.columns(3)
        for i, q in enumerate(st.session_state.q_list):
            q_num = q['number']
            answered = q_num in st.session_state.exam_answers
            bg_color = "green" if answered else "gray"
            # 每列放置多个按钮（简单分列）
            if i % 3 == 0:
                with col1:
                    if st.button(f"{q_num}", key=f"exam_jump_{i}", help=f"题目{'已答' if answered else '未答'}"):
                        st.session_state.index = i
                        st.rerun()
            elif i % 3 == 1:
                with col2:
                    if st.button(f"{q_num}", key=f"exam_jump_{i}"):
                        st.session_state.index = i
                        st.rerun()
            else:
                with col3:
                    if st.button(f"{q_num}", key=f"exam_jump_{i}"):
                        st.session_state.index = i
                        st.rerun()
        st.markdown("---")
        if st.button("提交试卷"):
            # 计算得分
            score = 0
            for q in st.session_state.q_list:
                user_ans = st.session_state.exam_answers.get(q['number'], "")
                if user_ans == q['answer']:
                    score += 1
            st.session_state.mode = "exam_result"
            st.session_state.exam_score = score
            st.rerun()
    
    if idx < total:
        q = st.session_state.q_list[idx]
        st.subheader(f"第 {idx+1}/{total} 题")
        opts, mapping = display_question(q, st.session_state.shuffle_opts)
        st.write(f"**{q['number']}. {q['text']}**")
        
        # 获取当前题目的已有答案（如果之前答过）
        saved_answer = st.session_state.exam_answers.get(q['number'], "")
        user_ans = None
        
        # 使用动态key确保每次重新渲染时组件状态重置
        if q['type'] == 'multiple':
            selected = []
            for k, v in opts.items():
                is_checked = (saved_answer and k in saved_answer)  # 简单判断，但多选答案可能含多个字母
                if st.checkbox(f"{k}. {v}", value=is_checked, key=f"exam_multi_{idx}_{k}"):
                    selected.append(k)
            if selected:
                if mapping:
                    orig = [mapping[ch] for ch in selected if ch in mapping]
                else:
                    orig = selected
                orig.sort()
                user_ans = ''.join(orig)
        elif q['type'] == 'judge':
            # 判断题：默认无选中，所以要给radio设置index=None，但需要特殊处理
            # 这里用选择框代替，避免默认选中
            choice = st.radio("请选择", ["正确", "错误"], key=f"exam_judge_{idx}", horizontal=False, index=None)
            if choice == "正确":
                selected = "A"
            elif choice == "错误":
                selected = "B"
            else:
                selected = ""
            if selected and mapping:
                user_ans = mapping.get(selected, selected)
            else:
                user_ans = selected
        else:
            opt_keys = list(opts.keys())
            # 同样设置index=None避免默认选中
            choice = st.radio("请选择", [f"{k}. {opts[k]}" for k in opt_keys], key=f"exam_single_{idx}", horizontal=False, index=None)
            if choice:
                selected = choice.split(".")[0].strip()
                if mapping:
                    user_ans = mapping.get(selected, selected)
                else:
                    user_ans = selected
            else:
                user_ans = ""
        
        # 保存答案按钮
        if st.button("保存本题答案", key=f"save_exam_{idx}"):
            if user_ans:
                st.session_state.exam_answers[q['number']] = user_ans
                st.success("答案已保存")
            else:
                st.warning("请先选择一个选项")
        
        # 显示当前已保存的答案
        if q['number'] in st.session_state.exam_answers:
            st.info(f"当前已保存答案：{st.session_state.exam_answers[q['number']]}")
        
        # 上一题/下一题按钮
        col1, col2 = st.columns(2)
        with col1:
            if idx > 0:
                if st.button("上一题"):
                    st.session_state.index -= 1
                    st.rerun()
        with col2:
            if idx < total - 1:
                if st.button("下一题"):
                    st.session_state.index += 1
                    st.rerun()

# 考试结果
elif st.session_state.mode == "exam_result":
    total = len(st.session_state.q_list)
    score = st.session_state.exam_score
    st.subheader("📊 考试结果")
    st.success(f"得分：{score}/{total} ({score/total*100:.1f}%)")
    # 展示错题解析
    for q in st.session_state.q_list:
        user_ans = st.session_state.exam_answers.get(q['number'], "")
        if user_ans != q['answer']:
            st.error(f"第 {q['number']} 题 错误")
            st.write(f"你的答案：{user_ans}，正确答案：{q['answer']}")
            st.info(f"解析：{q['explanation']}")
    if st.button("返回主菜单"):
        st.session_state.mode = "menu"
        st.rerun()

# 搜索题目（显示完整内容）
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
            st.warning("未找到题目")
        else:
            for q in results:
                # 直接展示完整题目，不用expander
                st.markdown(f"**【{q['type']}】{q['number']}. {q['text']}**")
                for opt, txt in q['options'].items():
                    st.write(f"{opt}. {txt}")
                st.write(f"答案：{q['answer']}")
                st.write(f"解析：{q['explanation']}")
                st.markdown("---")
    if st.button("返回主菜单"):
        st.session_state.mode = "menu"
        st.rerun()

# 普通练习（顺序/随机/章节/题型/收藏）
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
        
        # 使用动态key并设置index=None，确保默认不选中
        user_ans = None
        
        if q['type'] == 'multiple':
            selected = []
            for k, v in opts.items():
                if st.checkbox(f"{k}. {v}", key=f"multi_{idx}_{k}"):
                    selected.append(k)
            if selected:
                if mapping:
                    orig = [mapping[ch] for ch in selected if ch in mapping]
                else:
                    orig = selected
                orig.sort()
                user_ans = ''.join(orig)
        elif q['type'] == 'judge':
            choice = st.radio("请选择", ["正确", "错误"], key=f"judge_{idx}", horizontal=False, index=None)
            if choice == "正确":
                selected = "A"
            elif choice == "错误":
                selected = "B"
            else:
                selected = ""
            if selected and mapping:
                user_ans = mapping.get(selected, selected)
            else:
                user_ans = selected
        else:
            opt_keys = list(opts.keys())
            choice = st.radio("请选择", [f"{k}. {opts[k]}" for k in opt_keys], key=f"single_{idx}", horizontal=False, index=None)
            if choice:
                selected = choice.split(".")[0].strip()
                if mapping:
                    user_ans = mapping.get(selected, selected)
                else:
                    user_ans = selected
            else:
                user_ans = ""
        
        # 提交答案
        if st.button("提交答案", key=f"submit_{idx}"):
            if user_ans is None or user_ans == "":
                st.warning("请先选择一个选项")
            else:
                ok, ua, ca = check_selected(q, user_ans, mapping if q['type'] != 'multiple' else None)
                if ok:
                    st.session_state.result_info = f"✅ 回答正确！ 正确答案：{ca}"
                else:
                    st.session_state.result_info = f"❌ 回答错误！ 你的答案：{ua}，正确答案：{ca}"
                if q['explanation']:
                    st.session_state.result_info += f"\n📖 解析：{q['explanation']}"
                st.session_state.show_result = True
        
        if st.session_state.show_result and st.session_state.result_info:
            st.info(st.session_state.result_info)
        
        # 收藏按钮
        col_btns = st.columns([1,1,1,1])
        with col_btns[0]:
            if q['number'] in st.session_state.favorites:
                if st.button("💔 取消收藏", key=f"unfav_{idx}"):
                    remove_favorite(q['number'])
                    st.rerun()
            else:
                if st.button("❤️ 收藏本题", key=f"fav_{idx}"):
                    add_favorite(q['number'])
                    st.rerun()
        with col_btns[1]:
            if idx > 0:
                if st.button("⬅️ 上一题", key="prev_btn"):
                    st.session_state.index -= 1
                    st.session_state.show_result = False
                    st.session_state.result_info = None
                    st.rerun()
        with col_btns[2]:
            if idx < total - 1:
                if st.button("下一题 ➡️", key="next_btn"):
                    st.session_state.index += 1
                    st.session_state.show_result = False
                    st.session_state.result_info = None
                    st.rerun()
        with col_btns[3]:
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