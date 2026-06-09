import streamlit as st
from utils import ViewComponents, TaskService, StreamFlowEngine as engine
from utils import AppInitializer
from datetime import date

st.set_page_config(layout="wide")
st.header("📋 任務看板")

AppInitializer.setup()

core_categories = ["未指派", "進行中", "已完成"]
for core_cat in core_categories:
    if core_cat not in st.session_state.categories:
        st.session_state.categories.append(core_cat)

today = date.today()

# ===== 1. 快捷搜索 & 篩選器 =====
f_assignees, f_tags = ViewComponents.render_filters()

c_search, c_sort = st.columns([2, 1])
with c_search:
    search_query = st.text_input("🔍 快捷搜索任務（實時過濾標題、內容或備註）", value="")
with c_sort:
    sort_order = st.selectbox("排序依據", ["預設排序", "優先級：高 ➔ 低", "優先級：低 ➔ 高"])


# ===== ⚙️ 2. 頂部管理面版 =====
with st.expander("🛠️ 看板設定與團隊成員管理"):
    c_add, c_partner, c_clear = st.columns(3)
    
    with c_add:
        st.markdown("📂 **看板欄位管理**")
        new_cat = st.text_input("自訂新分類/欄位名稱", key="add_new_cat_input")
        if st.button("建立欄位") and new_cat and (new_cat not in st.session_state.categories):
            st.session_state.categories.append(new_cat)
            AppInitializer.save_data()
            st.success(f"已新增欄位: {new_cat}")
            st.rerun()
        
        st.divider()
        
        del_cat = st.selectbox("選擇要刪除的欄位", st.session_state.categories, key="del_cat_select")
        if st.button("🗑️ 刪除欄位"):
            if del_cat in core_categories:
                st.error("❌ 系統核心欄位必須保留，無法刪除！")
            else:
                cat_tasks_count = len([t for t in st.session_state.tasks if t['category'] == del_cat])
                if cat_tasks_count > 0:
                    st.error("無法刪除！該欄位內還有任務。")
                else:
                    st.session_state.categories.remove(del_cat)
                    AppInitializer.save_data()
                    st.rerun()
            
    with c_partner:
        st.markdown("👥 **團隊成員管理**")
        new_partner = st.text_input("輸入新成員姓名", key="add_new_partner_input")
        if st.button("➕ 新增成員") and new_partner:
            if new_partner not in st.session_state.partners:
                st.session_state.partners.append(new_partner)
                AppInitializer.save_data()
                st.success(f"歡迎新成員: {new_partner}")
                st.rerun()
        
        st.divider()
        
        if st.session_state.partners:
            # 💡 這裡完全不需要防呆「未指派」了，因為它根本不在夥伴名單裡！
            del_partner = st.selectbox("選擇要移除的成員", st.session_state.partners, key="del_partner_select")
            if st.button("❌ 移除成員"):
                active_tasks_count = len([t for t in st.session_state.tasks if t.get('assignee') == del_partner and t['category'] != '已完成'])
                if active_tasks_count > 0:
                    st.error("無法移除！該成員目前還有未完成的任務。")
                else:
                    st.session_state.partners.remove(del_partner)
                    AppInitializer.save_data()
                    st.rerun()
        else:
            st.caption("目前無成員可管理")
            
    with c_clear:
        st.markdown("🧹 **任務清理**")
        done_tasks_count = len([t for t in st.session_state.tasks if t['category'] == '已完成'])
        if st.button("✨ 清除已完成任務", use_container_width=True, disabled=(done_tasks_count == 0)):
            st.session_state.tasks = [t for t in st.session_state.tasks if t['category'] != '已完成']
            AppInitializer.save_data()
            st.rerun()


# ===== 🗂️ 3. 看板欄位渲染 =====
cols = st.columns(len(st.session_state.categories))

for idx, col in enumerate(cols):
    cat_name = st.session_state.categories[idx]

    with col:
        st.markdown(f"#### 📁 {cat_name}")
        st.divider()

        cat_tasks = TaskService.get_filtered_tasks(f_assignees, f_tags, [t for t in st.session_state.tasks if t['category'] == cat_name])

        if search_query:
            q = search_query.lower()
            cat_tasks = [t for t in cat_tasks if (q in t['title'].lower()) or (q in t.get('notes', '').lower())]

        # 排序權重
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


        # ===== 🎴 4. 渲染任務卡片 =====
        for t in cat_tasks:
            with st.container(border=True):
                is_locked, locked_by = TaskService.is_task_locked(t)
                is_due_today = (t['due'] == today and t['category'] != '已完成')
                
                if is_locked:
                    st.markdown(f"### 🔒 {t['title']}")
                    st.error(f"等待前置: {', '.join(locked_by)}")
                else:
                    if is_due_today:
                        st.markdown(f"### :red[📌 {t['title']} (今日截止!)]")
                    else:
                        st.markdown(f"### 📌 {t['title']}")

                # 💡 UI 渲染修正：如果為 None，優雅地顯示為「💡 暫無負責人」
                display_assignee = t.get('assignee') if t.get('assignee') else "💡 暫無負責人"
                st.caption(f"👤 負責人: **{display_assignee}**")
                st.caption(f"🎯 優先級: 重{t.get('importance','低')} | 🚀 急{t.get('urgency','低')}")
                st.caption(f"📅 截止日: `{t['due']}` | ⏱️ 工時: `{t.get('hours_spent', 0)}h`")
                st.progress(float(t.get('progress', 0)) / 100.0)

                with st.expander("📝 詳細設定與回報"):
                    # 💡 核心改造：建構一個包含「未指派」虛擬選項的下拉清單
                    assignee_options = ["-- 尚未指派 (等待認領) --"] + st.session_state.partners
                    
                    if t.get('assignee') in st.session_state.partners:
                        current_idx = assignee_options.index(t.get('assignee'))
                    else:
                        current_idx = 0
                        
                    selected_opt = st.selectbox(
                        "👤 變更負責人",
                        assignee_options,
                        index=current_idx,
                        key=f"assignee_{t['id']}"
                    )
                    
                    # 判斷對應後台資料的轉變
                    target_assignee_value = None if selected_opt == "-- 尚未指派 (等待認領) --" else selected_opt
                    
                    if target_assignee_value != t.get('assignee'):
                        old_name = t.get('assignee') if t.get('assignee') else "未指派"
                        new_name = target_assignee_value if target_assignee_value else "未指派"
                        engine.add_log(t, f"將負責人從「{old_name}」變更為「{new_name}」")
                        t['assignee'] = target_assignee_value
                        st.rerun()

                    st.divider()

                    # (以下進度、工時、備註功能完全相同...)
                    new_imp = st.selectbox("重要度", ["高", "低"], index=0 if t.get("importance") == "高" else 1, key=f"imp_{t['id']}")
                    new_urg = st.selectbox("緊急度", ["高", "低"], index=0 if t.get("urgency") == "高" else 1, key=f"urg_{t['id']}")
                    if (new_imp != t.get('importance')) or (new_urg != t.get('urgency')):
                        t['importance'] = new_imp
                        t['urgency'] = new_urg
                        AppInitializer.save_data()
                        st.rerun()

                    new_prog = st.slider("完成進度 (%)", 0, 100, int(t.get('progress', 0)), key=f"prog_{t['id']}")
                    if new_prog != t.get('progress'):
                        t['progress'] = new_prog
                        engine.add_log(t, f"更新進度至 {new_prog}%")
                        st.rerun()

                    add_h = st.number_input("➕ 新增本次工時", min_value=0.0, step=0.5, key=f"add_h_{t['id']}")
                    if st.button("送出工時", key=f"btn_h_{t['id']}") and add_h > 0:
                        t['hours_spent'] = float(t.get('hours_spent', 0)) + float(add_h)
                        engine.add_log(t, f"投入工時 {add_h} 小時")
                        st.rerun()

                    old_notes = t.get('notes', '')
                    t['notes'] = st.text_area("備註說明", value=old_notes, key=f"note_{t['id']}")
                    if t['notes'] != old_notes:
                        AppInitializer.save_data()

                    st.markdown("🔗 **卡片變更歷史軌跡**")
                    with st.container(height=110):
                        for log in reversed(t.get('history', [])):
                            st.caption(log)

                # 看板狀態遷移
                new_status = st.selectbox("🚀 移動卡片至欄位", st.session_state.categories, index=st.session_state.categories.index(cat_name), key=f"move_{t['id']}", disabled=is_locked)
                if (new_status != t['category']) and (not is_locked):
                    engine.add_log(t, f"將狀態從「{t['category']}」移至「{new_status}」")
                    t['category'] = new_status
                    if new_status == "已完成":
                        st.balloons()
                    st.rerun()
