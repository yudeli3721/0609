import streamlit as st
from utils import ViewComponents, TaskService, StreamFlowEngine as engine
from utils import AppInitializer
from datetime import date, timedelta

# 💡 開啟寬螢幕模式，讓 KANBAN 多欄位並排時有最好的視覺美感
st.set_page_config(layout="wide")

st.header("📋 團隊任務動態看板")

# 1. 啟動初始化與本地備份讀取機制
AppInitializer.setup()

# 2. 強制宣告並保護系統核心三大欄位
core_categories = ["未指派", "進行中", "已完成"]
for core_cat in core_categories:
    if core_cat not in st.session_state.categories:
        st.session_state.categories.append(core_cat)

today = date.today()

# ===== 🔔 1. 彈出式視窗定義 (Streamlit Dialogs) =====
@st.dialog("🎉 團隊夥伴加入通知")
def show_success_dialog(name):
    st.success(f"### 🤝 成功建立成員：{name}")
    st.markdown(f"系統已將 **{name}** 正式編入專案團隊名冊中，現在您可以開始為其指派專案任務，或由其自主認領工作。")
    if st.button("我知道了，返回看板", use_container_width=True):
        st. certain_rerun = True
        st.rerun()


# ===== 🔍 2. 快捷搜索 & 多維度篩選器 =====
f_assignees, f_tags = ViewComponents.render_filters()

c_search, c_sort = st.columns([2, 1])
with c_search:
    search_query = st.text_input("🔍 快捷搜索任務（實時過濾標題、內容或備註）", value="")
with c_sort:
    sort_order = st.selectbox("排序依據", ["預設排序", "優先級：高 ➔ 低", "優先級：低 ➔ 高"])


# ===== ⚙️ 3. 頂部管理面版 =====
with st.expander("🛠️ 看板設定與團隊成員管理面板", expanded=False):
    c_add, c_partner, c_clear = st.columns(3)
    
    # 【區塊一：看板自訂欄位管理】
    with c_add:
        st.markdown("📂 **看板欄位自訂**")
        new_cat = st.text_input("自訂新分類/欄位名稱", key="add_new_cat_input")
        if st.button("建立新欄位", use_container_width=True) and new_cat:
            if new_cat not in st.session_state.categories:
                st.session_state.categories.append(new_cat)
                AppInitializer.save_data()
                st.toast(f"已新增欄位: {new_cat}")
                st.rerun()
        
        st.divider()
        
        deletable_categories = [cat for cat in st.session_state.categories if cat not in core_categories]
        
        if deletable_categories:
            del_cat = st.selectbox("選擇要刪除的自訂欄位", deletable_categories, key="del_cat_select")
            if st.button("🗑️ 刪除自訂欄位", use_container_width=True):
                cat_tasks_count = len([t for t in st.session_state.tasks if t['category'] == del_cat])
                if cat_tasks_count > 0:
                    st.error(f"⚠️ 無法刪除！「{del_cat}」內還有 {cat_tasks_count} 個任務，請先遷移任務卡片。")
                else:
                    st.session_state.categories.remove(del_cat)
                    AppInitializer.save_data()
                    st.toast(f"已成功移除欄位「{del_cat}」")
                    st.rerun()
        else:
            st.caption("ℹ️ 當前僅有系統核心欄位（未指派/進行中/已完成），皆受系統保護不可刪除。")
            
    # 【區塊二：團隊成員管理】
    with c_partner:
        st.markdown("👥 **團隊成員名冊**")
        new_partner = st.text_input("輸入新成員姓名", key="add_new_partner_input")
        if st.button("➕ 邀請新夥伴加入", use_container_width=True) and new_partner:
            if new_partner not in st.session_state.partners:
                st.session_state.partners.append(new_partner)
                st.session_state.roles[new_partner] = 0
                AppInitializer.save_data()
                show_success_dialog(new_partner)
            else:
                st.warning("該成員姓名已存在於團隊名單中。")
        
        st.divider()
        
        if st.session_state.partners:
            del_partner = st.selectbox("選擇要移出的成員", st.session_state.partners, key="del_partner_select")
            if st.button("❌ 移除此成員身分", use_container_width=True):
                active_tasks_count = len([t for t in st.session_state.tasks if t.get('assignee') == del_partner and t['category'] != '已完成'])
                if active_tasks_count > 0:
                    st.error(f"⚠️ 無法移除！{del_partner} 身上還有 {active_tasks_count} 個未完成任務。")
                else:
                    st.session_state.partners.remove(del_partner)
                    if del_partner in st.session_state.roles:
                        del st.session_state.roles[del_partner]
                    AppInitializer.save_data()
                    st.toast(f"已將 {del_partner} 移出團隊")
                    st.rerun()
                    
    # 【區塊三：已完成任務封存】
    with c_clear:
        st.markdown("🧹 **歷史卡片封存**")
        done_tasks_count = len([t for t in st.session_state.tasks if t['category'] == '已完成'])
        st.write(f"目前歷史封存區共有 **{done_tasks_count}** 個已完成任務。")
        if st.button("✨ 一鍵清理已完成任務卡片", use_container_width=True, disabled=(done_tasks_count == 0)):
            st.session_state.tasks = [t for t in st.session_state.tasks if t['category'] != '已完成']
            AppInitializer.save_data()
            st.success("已成功釋放看板空間！")
            st.rerun()


# ===== ⚡ 4. 快速建立新任務 =====
with st.container(border=True):
    st.markdown("### ➕ 快速建立新任務（自動分流至「未指派」欄位）")
    c_title, c_due, c_tags_sel = st.columns([2, 1, 1])
    
    with c_title:
        new_task_title = st.text_input("📌 任務名稱 / 代辦事項標題", placeholder="例如：優化網頁 UI 視覺美感...", key="fast_task_title")
    with c_due:
        new_task_due = st.date_input("📅 預計截止日期", date.today() + timedelta(days=3), key="fast_task_due")
    with c_tags_sel:
        new_task_tags = st.multiselect("🏷️ 任務標籤", st.session_state.tags_list, key="fast_task_tags")
        
    if st.button("🚀 發布並新增至未指派欄位", use_container_width=True):
        if not new_task_title.strip():
            st.error("❌ 任務名稱不可為空！")
        else:
            new_id = max([t['id'] for t in st.session_state.tasks]) + 1 if st.session_state.tasks else 1
            
            new_task_obj = {
                "id": new_id,
                "title": new_task_title.strip(),
                "category": "未指派",  
                "due": new_task_due,
                "assignee": None,       
                "status": "Active",
                "progress": 0,
                "hours_spent": 0.0,
                "importance": "低",
                "urgency": "低",
                "tags": new_task_tags,
                "history": [f"[{date.today().strftime('%m-%d')}] 由 {st.session_state.current_user} 成功建立任務並歸類於未指派。"]
            }
            st.session_state.tasks.append(new_task_obj)
            AppInitializer.save_data() 
            st.toast(f"🎉 成功建立任務「{new_task_title}」！")
            st.rerun()


st.write("") 


# ===== 🗂️ 5. 看板多列動態欄位渲染 =====
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


        # ===== 🎴 6. 渲染單張任務卡片 =====
        for t in cat_tasks:
            with st.container(border=True):
                is_locked, locked_by = TaskService.is_task_locked(t)
                is_due_today = (t['due'] == today and t['category'] != '已完成')
                
                if is_locked:
                    st.markdown(f"### {t['title']}")
                    st.error(f"等待前置任務完成: {', '.join(locked_by)}")
                else:
                    if is_due_today:
                        st.markdown(f"### :red[📌 {t['title']} (今日截止!)]")
                    else:
                        st.markdown(f"### 📌 {t['title']}")

                display_assignee = t.get('assignee') if t.get('assignee') else "💡 暫無負責人"
                st.caption(f"👤 負責人: **{display_assignee}**")
                st.caption(f"🎯 優先級: 重{t.get('importance','低')} | 🚀 急{t.get('urgency','低')}")
                st.caption(f"📅 截止日: `{t['due']}` | ⏱️ 工時: `{t.get('hours_spent', 0)}h`")
                if t.get('tags'):
                    st.markdown(" ".join([f"`{tag}`" for tag in t['tags']]))
                st.progress(float(t.get('progress', 0)) / 100.0)


                # ===== ⚡ 核心優化：使用 st.form 建立獨立儲存確認機制 =====
                with st.expander("📝 詳細設定與回報"):
                    with st.form(key=f"task_form_{t['id']}"):
                        
                        # 1. 變更負責人下拉選單
                        assignee_options = ["-- 尚未指派 (等待認領) --"] + st.session_state.partners
                        current_idx = assignee_options.index(t.get('assignee')) if t.get('assignee') in st.session_state.partners else 0
                        selected_opt = st.selectbox("👤 變更負責人", assignee_options, index=current_idx)
                        
                        st.divider()

                        # 2. 優先級設定
                        new_imp = st.selectbox("重要度", ["高", "低"], index=0 if t.get("importance") == "高" else 1)
                        new_urg = st.selectbox("緊急度", ["高", "低"], index=0 if t.get("urgency") == "高" else 1)

                        # 3. 進度與工時
                        new_prog = st.slider("完成進度 (%)", 0, 100, int(t.get('progress', 0)))
                        add_h = st.number_input("➕ 新增本次工時 (小時)", min_value=0.0, step=0.5)

                        # 4. 備註欄
                        new_notes = st.text_area("備註說明", value=t.get('notes', ''))

                        # 5. 💡 實體確認更新按鍵 (按下才會寫入並重整)
                        submit_settings = st.form_submit_button("💾 儲存並更新卡片設定", use_container_width=True)
                        
                        if submit_settings:
                            has_changed = False
                            
                            # 判定負責人異動
                            target_assignee_value = None if selected_opt == "-- 尚未指派 (等待認領) --" else selected_opt
                            if target_assignee_value != t.get('assignee'):
                                old_name = t.get('assignee') if t.get('assignee') else "未指派"
                                new_name = target_assignee_value if target_assignee_value else "未指派"
                                engine.add_log(t, f"將負責人從「{old_name}」變更為「{new_name}」")
                                t['assignee'] = target_assignee_value
                                has_changed = True
                                
                            # 判定優先級異動
                            if (new_imp != t.get('importance')) or (new_urg != t.get('urgency')):
                                t['importance'] = new_imp
                                t['urgency'] = new_urg
                                has_changed = True
                                
                            # 判定進度異動
                            if new_prog != t.get('progress'):
                                engine.add_log(t, f"更新進度至 {new_prog}%")
                                t['progress'] = new_prog
                                has_changed = True
                                
                            # 判定追加工時
                            if add_h > 0:
                                t['hours_spent'] = float(t.get('hours_spent', 0)) + float(add_h)
                                engine.add_log(t, f"投入工時 {add_h} 小時")
                                has_changed = True
                                
                            # 判定備註異動
                            if new_notes != t.get('notes', ''):
                                t['notes'] = new_notes
                                has_changed = True
                                
                            # 有任何變更才儲存資料庫並觸發畫面重整
                            if has_changed:
                                AppInitializer.save_data()
                                st.toast(f"👍 「{t['title']}」設定已成功儲存！")
                                st.rerun()

                    st.markdown("🔗 **變更歷史軌跡**")
                    with st.container(height=110):
                        for log in reversed(t.get('history', [])):
                            st.caption(log)


                # ===== 🚀 跨欄位移動 (保持原本選取即時重整的直覺體驗) =====
                new_status = st.selectbox(
                    "🚀 移動卡片至欄位",
                    st.session_state.categories,
                    index=st.session_state.categories.index(cat_name),
                    key=f"move_{t['id']}",
                    disabled=is_locked
                )

                if (new_status != t['category']) and (not is_locked):
                    engine.add_log(t, f"將狀態從「{t['category']}」移至「{new_status}」欄位")
                    t['category'] = new_status
                    
                    if new_status == "已完成":
                        st.balloons()
                        st.toast(f"🎉 太棒了！任務「{t['title']}」已順利結案！")
                    
                    st.rerun()
