import streamlit as st
from utils import ViewComponents, TaskService, StreamFlowEngine as engine
from utils import AppInitializer
from datetime import date  # <--- 💡 引入 date 用於比對今日日期

st.header("📋 任務看板")

AppInitializer.setup()

# 獲取今天的日期
today = date.today()

f_assignees, f_tags = ViewComponents.render_filters()

# ===== 頂部設定區：新增分類 & 一鍵清理 =====
with st.expander("🛠️ 看板設定（功能操作）"):
    c_add, c_clear = st.columns(2)
    
    with c_add:
        new_cat = st.text_input("自訂新分類/欄位名稱")
        if st.button("建立欄位") and new_cat and new_cat not in st.session_state.categories:
            st.session_state.categories.append(new_cat)
            st.rerun()
            
    with c_clear:
        st.write("🧹 任務清理")
        done_tasks_count = len([t for t in st.session_state.tasks if t['category'] == '已完成'])
        
        if st.button(f"✨ 清除已完成任務 ({done_tasks_count})", use_container_width=True, disabled=done_tasks_count == 0):
            st.session_state.tasks = [t for t in st.session_state.tasks if t['category'] != '已完成']
            st.success("已成功清理所有已完成的任務！")
            st.rerun()

# ===== 看板欄位渲染 =====
cols = st.columns(len(st.session_state.categories))

for idx, col in enumerate(cols):
    cat_name = st.session_state.categories[idx]

    with col:
        st.markdown(f"#### 📁 {cat_name}")
        st.divider()

        cat_tasks = TaskService.get_filtered_tasks(
            f_assignees,
            f_tags,
            [t for t in st.session_state.tasks if t['category'] == cat_name]
        )

        for t in cat_tasks:
            with st.container(border=True):
                is_locked, locked_by = TaskService.is_task_locked(t)

                # ===== 💡 今日截止動態紅字警示 =====
                # 判斷任務截止日是否為今天，且該任務尚未「已完成」
                is_due_today = (t['due'] == today and t['category'] != '已完成')
                
                if is_locked:
                    # 如果前置任務未完成（鎖定中）
                    title_text = f"🔒 {t['title']}"
                    if is_due_today:
                        st.markdown(f"### :red[{title_text} (今日截止!)]")
                    else:
                        st.markdown(f"### {title_text}")
                    st.error(f"等待前置：{', '.join(locked_by)}")
                else:
                    # 正常可執行的任務
                    title_text = f"📌 {t['title']}"
                    if is_due_today:
                        st.markdown(f"### :red[{title_text} (今日截止!)]")
                    else:
                        st.markdown(f"### {title_text}")

                st.caption(f"📅 {t['due']} | ⏱️ 累計工時: {t.get('hours_spent', 0)}h")
                st.progress(t.get('progress', 0) / 100.0)

                with st.expander("📝 詳細設定與回報"):

                    # ===== 重要 / 緊急 =====
                    new_imp = st.selectbox(
                        "重要度",
                        ["高", "低"],
                        index=0 if t.get("importance") == "高" else 1,
                        key=f"imp_{t['id']}"
                    )

                    new_urg = st.selectbox(
                        "緊急度",
                        ["高", "低"],
                        index=0 if t.get("urgency") == "高" else 1,
                        key=f"urg_{t['id']}"
                    )

                    t['importance'] = new_imp
                    t['urgency'] = new_urg

                    # ===== progress =====
                    new_prog = st.slider(
                        "完成進度 (%)",
                        0,
                        100,
                        t.get('progress', 0),
                        key=f"prog_{t['id']}"
                    )

                    if new_prog != t.get('progress'):
                        t['progress'] = new_prog
                        engine.add_log(t, f"將進度更新為 {new_prog}%")

                    # ===== 工時 =====
                    add_h = st.number_input(
                        "➕ 新增本次花費工時",
                        min_value=0.0,
                        step=0.5,
                        key=f"add_h_{t['id']}"
                    )

                    if st.button("紀錄工時", key=f"btn_h_{t['id']}") and add_h > 0:
                        t['hours_spent'] = t.get('hours_spent', 0) + add_h
                        engine.add_log(t, f"紀錄了 {add_h} 小時，總計 {t['hours_spent']} 小時")
                        st.rerun()

                    # ===== notes =====
                    t['notes'] = st.text_area(
                        "備註",
                        value=t.get('notes', ''),
                        key=f"note_{t['id']}"
                    )

                    # ===== log =====
                    st.markdown("**📜 活動軌跡**")
                    with st.container(height=100):
                        for log in reversed(t.get('history', [])):
                            st.caption(log)

                # ===== 狀態變更 =====
                new_status = st.selectbox(
                    "變更狀態",
                    st.session_state.categories,
                    index=idx,
                    key=f"move_{t['id']}",
                    disabled=is_locked
                )

                if new_status != t['category'] and not is_locked:
                    engine.add_log(t, f"將狀態從「{t['category']}」移至「{new_status}」")
                    t['category'] = new_status
                    st.rerun()
