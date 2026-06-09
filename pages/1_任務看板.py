import streamlit as st
from utils import ViewComponents, TaskService, StreamFlowEngine as engine
from utils import AppInitializer
from datetime import date

# 💡 開啟寬螢幕模式，讓多個 KANBAN 欄位並排時更加美觀直覺
st.set_page_config(layout="wide")

st.header("📋 任務看板")

# 1. 啟動初始化與本地 JSON 存檔讀取機制
AppInitializer.setup()

# 2. 強制定義與保護系統核心三大欄位
core_categories = ["未指派", "進行中", "已完成"]
for core_cat in core_categories:
    if core_cat not in st.session_state.categories:
        st.session_state.categories.append(core_cat)

# 獲取今天的日期，用作截止日動態提醒
today = date.today()

# ===== 1. 快捷搜索 & 多維度篩選器 =====
f_assignees, f_tags = ViewComponents.render_filters()

c_search, c_sort = st.columns([2, 1])

with c_search:
    search_query = st.text_input("🔍 快捷搜索任務（可實時過濾標題、內容或備註）", value="")

with c_sort:
    sort_order = st.selectbox(
        "排序依據",
        ["預設排序", "優先級：高 ➔ 低", "優先級：低 ➔ 高"]
    )


# ===== ⚙️ 2. 頂部大工具箱：分類欄位、團隊成員管理 & 一鍵清理 =====
with st.expander("🛠️ 看板設定與團隊成員管理（多功能操作面板）"):
    c_add, c_partner, c_clear = st.columns(3)
    
    # 【區塊一：看板自訂欄位管理】
    with c_add:
        st.markdown("📂 **看板欄位管理**")
        new_cat = st.text_input("自訂新分類/欄位名稱", key="add_new_cat_input")
        if st.button("建立欄位", use_container_width=True) and new_cat:
            if new_cat not in st.session_state.categories:
                st.session_state.categories.append(new_cat)
                AppInitializer.save_data() # 自動同步持久化檔案
                st.success(f"🎉 已成功建立自訂欄位「{new_cat}」")
                st.rerun()
        
        st.divider()
        
        del_cat = st.selectbox("選擇要刪除的欄位", st.session_state.categories, key="del_cat_select")
        if st.button("🗑️ 刪除選取欄位", use_container_width=True):
            if del_cat in core_categories:
                st.error(f"❌ 系統核心欄位「{del_cat}」必須保留，不允許刪除！")
            else:
                cat_tasks_count = len([t for t in st.session_state.tasks if t['category'] == del_cat])
                if cat_tasks_count > 0:
                    st.error(f"⚠️ 無法刪除！該欄位內目前還有 {cat_tasks_count} 個任務，請先遷移任務。")
                else:
                    st.session_state.categories.remove(del_cat)
                    AppInitializer.save_data() # 自動同步持久化檔案
                    st.toast(f"已移除自訂欄位「{del_cat}」")
                    st.rerun()
            
    # 【區塊二：團隊成員管理（內建任務關聯鎖）】
    with c_partner:
        st.markdown("👥 **團隊成員管理**")
        
        new_partner = st.text_input("輸入新成員姓名", key="add_new_partner_input")
        if st.button("➕ 邀請新成員加入", use_container_width=True) and new_partner:
            if new_partner not in st.session_state.partners:
                st.session_state.partners.append(new_partner)
                AppInitializer.save_data() # 自動同步持久化檔案
                st.success(f"🤝 歡迎新成員「{new_partner}」加入專案團隊！")
                st.rerun()
            else:
                st.warning("該成員已在團隊清單中。")
        
        st.divider()
        
        if st.session_state.partners:
            del_partner = st.selectbox("選擇要移除的成員", st.session_state.partners, key="del_partner_select")
            if st.button("❌ 移除此成員身分", use_container_width=True):
                if del_partner == "未指派":
                    st.error("❌ 「未指派」為系統預設常駐留白身分，無法移除！")
                else:
                    active_tasks_count = len([t for t in st.session_state.tasks if t.get('assignee') == del_partner and t['category'] != '已完成'])
                    if active_tasks_count > 0:
                        st.error(f"⚠️ 無法移除！「{del_partner}」目前身上還有 {active_tasks_count} 個未完成任務，請先交接。")
                    else:
                        st.session_state.partners.remove(del_partner)
                        AppInitializer.save_data() # 自動同步持久化檔案
