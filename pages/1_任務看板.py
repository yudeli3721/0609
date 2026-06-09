import streamlit as st
from utils import ViewComponents, TaskService, StreamFlowEngine as engine
from utils import AppInitializer
from datetime import date

st.header("📋 任務看板")

AppInitializer.setup()

# 確保基礎核心欄位一定存在（防呆雙重保險）
core_categories = ["未指派", "進行中", "已完成"]
for core_cat in core_categories:
    if core_cat not in st.session_state.categories:
        st.session_state.categories.append(core_cat)

# 獲取今天的日期
today = date.today()

# ===== 1. 快捷搜索 & 篩選器擴充 =====
f_assignees, f_tags = ViewComponents.render_filters()

c_search, c_sort = st.columns([2, 1])

with c_search:
    search_query = st.text_input("🔍 快捷搜索任務（實時過濾標題、內容或備註）", value="")

with c_sort:
    sort_order = st.selectbox(
        "排序依據",
        ["預設排序", "優先級：高 ➔ 低", "優先級：低 ➔ 高"]
    )


# ===== ⚙️ 頂部設定區：分類、成員管理 & 一鍵清理 =====
with st.expander("🛠️ 看板設定與團隊成員管理（功能操作）"):
    # 將設定區切成三個區塊
    c_add, c_partner, c_clear = st.columns(3)
    
    # 【區塊一：💡 欄位分類管理（保留並保護核心欄位）】
    with c_add:
        st.markdown("📂 **看板欄位管理**")
        new_cat = st.text_input("自訂新分類/欄位名稱", key="add_new_cat_input")
        if st.button("建立欄位") and new_cat and new_cat not in st.session_state.categories:
            st.session_state.categories.append(new_cat)
            st.success(f"已新增欄位「{new_cat}」")
            st.rerun()
        
        st.divider()
        
        # 刪除自訂欄位功能（加入核心欄位保護）
        del_cat = st.selectbox("選擇要刪除的欄位", st.session_state.categories, key="del_cat_select")
        if st.button("🗑️ 刪除欄位"):
            if del_cat in core_categories:
                st.error(f"❌ 系統核心欄位「{del_cat}」必須保留，無法刪除！")
            else:
                # 檢查該欄位內是否還有任務
                cat_tasks_count = len([t for t in st.session_state.tasks if t['category'] == del_cat])
                if cat_tasks_count > 0:
                    st.error(f"無法刪除！「{del_cat}」欄位內還有 {cat_tasks_count} 個任務，請先將任務移至其他欄位。")
                else:
                    st.session_state.categories.remove(del_cat)
                    st.toast(f"已刪除自訂欄位「{del_cat}」")
                    st.rerun()
            
    # 【區塊二：團隊成員管理（新增/刪除人）】
    with c_partner:
        st.markdown("👥 **團隊成員管理**")
        
        # 新增成員
        new_partner = st.text_input("輸入新成員姓名", key="add_new_partner_input")
        if st.button("➕ 新增成員") and new_partner:
            if new_partner not in st.session_state.partners:
                st.session_state.partners.append(new_partner)
                st.success(f"🎉 歡迎新成員「{new_partner}」加入團隊！")
                st.rerun()
            else:
                st.warning("該成員已在團隊列表中。")
        
        st.divider()
        
        # 刪除成員
        if st.session_state.partners:
            del_partner = st.selectbox("選擇要移除的成員", st.session_state.partners, key="del_partner_select")
            if st.button("❌ 移除成員"):
                active_tasks_count = len([t for t in st.session_state.tasks if t.get('assignee') == del_partner and t['category'] != '已完成'])
                
                if active_tasks_count > 0:
                    st.error(f"無法移除！「{del_partner}」目前還有 {active_tasks_count} 個未完成的任務，請先移交任務。")
                else:
                    st.session_state.partners.remove(del_partner)
                    st.toast(f"已將「{del_partner}」移出團隊。")
                    st.rerun()
        else:
            st.caption("目前無成員可刪除")
            
    # 【區塊三：任務清理】
    with c_clear:
        st.markdown("🧹 **任務清理**")
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

        # 基礎過濾：夥伴與標籤
        cat_tasks = TaskService.get_filtered_tasks(
            f_assignees,
            f_tags,
            [t for t in st.session_state.tasks if t['category'] == cat_name]
        )

        # 實時關鍵字搜尋過濾
        if search_query:
            q = search_query.lower()
            cat_tasks = [
                t for t in cat_tasks
                if q in t['title'].lower() 
                or q in t.get('notes', '').lower()
            ]

        # 優先級排序邏輯
        def get_priority_weight(task):
            imp = task.get('importance', '低')
            urg = task.get('urgency', '低')
            if imp == '高' and urg == '高': return 4
            if imp == '高' and urg == '低': return 3
            if imp == '低' and urg == '高': return 2
            return 1

        if sort_order == "優先級：高 ➔ 低":
            cat_tasks = sorted(cat_tasks, key=get_priority_weight, reverse=True)
        elif sort_order == "優先級：低 ➔ 高":
            cat_tasks = sorted(cat_tasks, key=get_priority_weight)


        # 渲染任務卡片
        for t in cat_tasks:
            with st.container(border=True):
                is_locked, locked_by = TaskService.is_task_locked(t)

                # 今日截止動態紅字警示
                is_due_today = (t['due'] == today and t['category'] != '已完成')
                
                if is_locked:
                    title_text = f"🔒 {t['title']}"
                    if is_due_today:
                        st.markdown(f"### :red[{title_text} (今日截止!)]")
                    else:
                        st.markdown(f"### {title_text}")
                    st.error(f"等待前置：{', '.join(locked_by)}")
                else:
                    title_text = f"📌 {t['title']}"
                    if is_due_today:
                        st.markdown(f"### :red[{title_text} (今日截止!)]")
                    else:
                        st.markdown(f"### {title_text}")

                # 顯示當前負責人
                st.caption(f"👤 負責人: **{t.get('assignee', '未指派')}**")
                st.caption(f"🎯 優先級: 重{t.get('importance','低')} | 🚀 急{t.get('urgency','低')}")
                st.caption(f"📅 {t['due']} | ⏱️ 累計工時: {t.get('hours_spent', 0)}h")
                st.progress(t.get('progress', 0) / 100.0)

                with st.expander("📝 詳細設定與回報"):

                    # ===== 隨時更改負責人功能 =====
                    try:
                        current_assignee_idx = st.session_state.partners.index(t.get('assignee'))
                    except ValueError:
                        current_assignee_idx = 0
                        
                    new_assignee = st.selectbox(
                        "👤 變更負責人",
                        st.session_state.partners,
                        index=current_assignee_idx,
                        key=f"assignee_{t['id']}"
                    )
                    
                    if new_assignee != t.get('assignee'):
                        engine.add_log(t, f"將負責人從「{t.get('assignee')}」更換為「{new_assignee}」")
                        t['assignee'] = new_assignee
                        st.rerun()

                    st.divider()

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

                    if new_imp != t.get('importance') or new_urg != t.get('urgency'):
                        t['importance'] = new_imp
                        t['urgency'] = new_urg
                        st.rerun()

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
                        st.rerun()

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
                    
                    if new_status == "已完成":
                        st.balloons()
                        st.toast(f"🎉 太棒了！任務「{t['title']}」已完成！")
                    
                    st.rerun()
