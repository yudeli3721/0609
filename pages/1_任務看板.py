import streamlit as st
from utils import ViewComponents, TaskService, StreamFlowEngine as engine
from utils import AppInitializer
from datetime import date

st.set_page_config(layout="wide")

st.header("📋 任務看板")

# 1. 啟動初始化與存檔讀取機制
AppInitializer.setup()

# 2. 強制定義與保護核心三大欄位
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


# ===== ⚙️ 2. 頂部設定區 =====
with st.expander("🛠️ 看板設定與團隊成員管理（功能操作）"):
    c_add, c_partner, c_clear = st.columns(3)
    
    # 【區塊一：看板欄位管理】
    with c_add:
        st.markdown("📂 **看板欄位管理**")
        new_cat = st.text_input("自訂新分類/欄位名稱", key="add_new_cat_input")
        if st.button("建立欄位") and new_cat and new_cat not in st.session_state.categories:
            st.session_state.categories.append(new_cat)
            AppInitializer.save_data()
            st.success(f"已新增欄位「{new_cat}」")
            st.rerun()
        
        st.divider()
        
        del_cat = st.selectbox("選擇要刪除的欄位", st.session_state.categories, key="del_cat_select")
        if st.button("🗑️ 刪除欄位"):
            if del_cat in core_categories:
                st.error(f"❌ 系統核心欄位「{del_cat}」必須保留，無法刪除！")
            else:
                cat_tasks_count = len([t for t in st.session_state.tasks if t['category'] == del_cat])
                if cat_tasks_count > 0:
                    st.error(f"無法刪除！「{del_cat}」欄位內還有 {cat_tasks_count} 個任務，請先將任務移至其他欄位。")
                else:
                    st.session_state.categories.remove(del_cat)
                    AppInitializer.save_data()
                    st.toast(f"已刪除自訂欄位「{del_cat}」")
                    st.rerun()
            
    # 【區塊二：團隊成員管理】
    with c_partner:
        st.markdown("👥 **團隊成員管理**")
        
        new_partner = st.text_input("輸入新成員姓名", key="add_new_partner_input")
        if st.button("➕ 新增成員") and new_partner:
            if new_partner not in st.session_state.partners:
                st.session_state.partners.append(new_partner)
                AppInitializer.save_data()
                st.success(f"🎉 歡迎新成員「{new_partner}」加入團隊！")
                st.rerun()
            else:
                st.warning("該成員已在團隊列表中。")
        
        st.divider()
        
        if st.session_state.partners:
            del_partner = st.selectbox("選擇要移除的成員", st.session_state.partners, key="del_partner_select")
            if st.button("❌ 移除成員"):
                if del_partner == "未指派":
                    st.error("❌ 「未指派」為系統保留預設身分，無法移除！")
                else:
                    active_tasks_count = len([t for t in st.session_state.tasks if t.get('assignee') == del_partner and t['category'] != '已完成'])
                    
                    if active_tasks_count > 0:
                        st.error(f"無法移除！「{del_partner}」目前還有 {active_tasks_count} 個未完成的任務，請先將任務移交給他人。")
                    else:
                        st.session_state.partners.remove(del_partner)
                        AppInitializer.save_data()
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
            AppInitializer.save_data()
            st.success("已成功清理所有已完成的任務！")
            st.rerun()


# ===== 🗂️ 3. 看板雙層動態欄位渲染 =====
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

        if search_query:
            q = search_query.lower()
            cat_tasks = [
                t for t in cat_tasks
                if q in t['title'].lower() 
                or q in t.get('notes', '').lower()
            ]

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


        # ===== 🎴 4. 渲染單張任務卡片 =====
        for t in cat_tasks:
            with st.container(border=True):
                is_locked, locked_by = TaskService.is_task_locked(t)
                is_due_today = (t['due'] == today and t['category'] != '已完成')
                
                # 💡 安全修正：將複雜的 markdown 彩色字串與 f-string 完全拆開，避免 ast.parse 語法錯誤
                if is_locked:
                    if is_due_today:
                        st.error(f"🔒 {t['title']} (今日截止!)")
                    else:
                        st.markdown(f"### 🔒 {t['title']}")
                    st.error(f"等待前置：{', '.join(locked_by)}")
                else:
                    if is_due_today:
                        st.error(f"📌 {t['title']} (今日截止!)")
                    else:
                        st.markdown(f"### 📌 {t['title']}")

                st.caption(f"👤 負責人: **{t.get('assignee', '未指派')}**")
                st.caption(f"🎯 優先級: 重{t.get('importance','低')} | 🚀 急{t.get('urgency','低')}")
                st.caption(f"📅 截止日: {t['due']} | ⏱️ 累
