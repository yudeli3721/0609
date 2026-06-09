import streamlit as st
from datetime import datetime

# 在 utils.py 最上方加入這段
class AppInitializer:
    @staticmethod
    def setup():
        from datetime import date, timedelta
        
        # 確保基礎核心欄位存在
        if 'categories' not in st.session_state:
            st.session_state.categories = ["未指派", "進行中", "已完成"]

        if 'tasks' not in st.session_state:
            st.session_state.tasks = [
                {
                    "id": 1, 
                    "title": "資料庫設計", 
                    "category": "進行中", 
                    "due": date.today()+timedelta(days=2), 
                    "assignee": "王大明", # 💡 修正：統一改為單人 'assignee' 字串
                    "status": "Active", 
                    "progress": 80, 
                    "hours_spent": 4.5, 
                    "importance": "高", 
                    "urgency": "高", 
                    "history": []
                },
                {
                    "id": 2, 
                    "title": "API 開發", 
                    "category": "未指派", # 💡 修正：對齊核心基礎欄位
                    "due": date.today()+timedelta(days=5), 
                    "assignee": "陳小華", # 💡 修正：統一改為單人 'assignee' 字串
                    "status": "Active", 
                    "progress": 0, 
                    "hours_spent": 0.0, 
                    "importance": "高", 
                    "urgency": "低", 
                    "history": []
                }
            ]
            # 💡 增加「未指派」選項在成員名單中，這樣一開始沒人做的任務才選得到
            st.session_state.partners = ["未指派", "王大明", "陳小華", "林志玲", "闕老師"]
            st.session_state.current_user = "闕老師"
            st.session_state.roles = {"闕老師": 2, "王大明": 1, "陳小華": 0, "林志玲": 0, "未指派": 0}
            st.session_state.meetings = []
            st.session_state.approvals = []
            st.session_state.tags_list = ["設計", "開發", "測試"]
            st.session_state.cal_year = date.today().year
            st.session_state.cal_month = date.today().month
            st.session_state.selected_date = date.today()

class ViewComponents:
    """可重用的 UI 元件"""
    @staticmethod
    def render_filters():
        with st.expander("🔍 進階多維度
