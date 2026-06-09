import streamlit as st
from utils import ViewComponents, TaskService, StreamFlowEngine as engine
from utils import AppInitializer
from datetime import date

st.header("📋 任務看板")

AppInitializer.setup()

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
    
    # 【區塊一：欄位分類管理】
    with c_add:
        st.markdown("📂 **看板欄位**")
        new_cat = st.text_input("自訂新分類/欄位名稱", key="add_new_cat_input")
        if st.button("建立欄位") and new_cat and new_cat not in st.session_state.categories:
            st.session_state.categories.append(new_cat)
            st.success(f"已新增欄位「{new_cat}」")
            st.rerun()
            
    # 【區塊二：💡 團隊成員管理（新增/刪除人）】
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
        
        st.divider() # 小分隔線
        
        # 刪除成員
        if st.session_state.partners:
            del_partner = st.selectbox("選擇要移除的成員", st.session_state.partners, key="del_partner_select")
            if st.button("❌ 移除成員"):
                # 檢查該成員目前是否有未完成的任務，避免誤刪導致系統找不到人
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
            st.session
