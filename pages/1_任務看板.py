import streamlit as st
from utils import ViewComponents, TaskService, StreamFlowEngine as engine
from utils import AppInitializer
from datetime import date

st.set_page_config(layout="wide") # 💡 建議開啟寬螢幕模式，看多個看板欄位更直覺

st.header("📋 任務看板")

# 1. 啟動初始化與存檔讀取機制
AppInitializer.setup()

# 2. 強制定義與保護核心三大欄位
core_categories = ["未指派", "進行中", "已完成"]
for core_cat in core_categories:
    if core_cat not in st.session_state.categories:
        st.session_state.categories.append(core_cat)

# 獲取今天的日期（用於今日截止警示）
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


# ===== ⚙️ 2. 頂部設定區：分類、成員管理 & 一鍵清理 =====
with st.expander("🛠️ 看板設定與團隊成員管理（功能操作）"):
    # 將設定區切成三個功能區塊
    c_add, c_partner, c_clear = st.columns(3)
    
    # 【區塊一：看板欄位管理】
    with c_add:
        st.markdown("📂 **看板欄位管理**")
        new_cat = st.text_input("自訂新分類/欄位名稱", key="add_new_cat_input")
        if st.button("建立欄位") and new_cat and new_cat not in st.session_state.categories:
            st.session_state.categories.append(new_cat)
            AppInitializer.save_data() # 💡 存入 JSON 存檔
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
                    AppInitializer.save_data() # 💡 存入 JSON 存檔
                    st.toast(f"已刪除自訂欄位「{del_cat}」")
                    st.rerun()
            
    # 【區塊二：團隊成員管理（可新增、刪除人）】
    with c_partner:
        st.markdown("👥 **團隊成員管理**")
        
        # 新增成員
        new_partner = st.text_input("輸入新成員姓名", key="add_new_partner_input")
        if st.button("➕ 新增成員") and new_
