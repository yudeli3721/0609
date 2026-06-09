import streamlit as st
import json
import os
from datetime import datetime, date, timedelta

class WorkflowEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)

class AppInitializer:
    DB_FILE = "workflow_db.json"

    @classmethod
    def save_data(cls):
        data_to_save = {
            "categories": st.session_state.categories,
            "tasks": st.session_state.tasks,
            "partners": st.session_state.partners,
            "meetings": st.session_state.meetings,
            "approvals": st.session_state.approvals,
            "tags_list": st.session_state.tags_list,
            "roles": st.session_state.roles,
            "current_user": st.session_state.current_user
        }
        with open(cls.DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, cls=WorkflowEncoder, ensure_ascii=False, indent=4)

    @classmethod
    def setup(cls):
        if "categories" not in st.session_state:
            st.session_state.categories = ["未指派", "進行中", "已完成"]
            
        if "tasks" not in st.session_state:
            if os.path.exists(cls.DB_FILE):
                try:
                    with open(cls.DB_FILE, "r", encoding="utf-8") as f:
                        saved_data = json.load(f)
                    st.session_state.categories = saved_data.get("categories", ["未指派", "進行中", "已完成"])
                    # 💡 團隊名單更新
                    st.session_state.partners = saved_data.get("partners", ["王大明", "陳小華", "林志玲", "乓"])
                    st.session_state.current_user = saved_data.get("current_user", "乓")
                    st.session_state.roles = saved_data.get("roles", {"乓": 2, "王大明": 1, "陳小華": 0, "林志玲": 0})
                    st.session_state.meetings = saved_data.get("meetings", [])
                    st.session_state.approvals = saved_data.get("approvals", [])
                    st.session_state.tags_list = saved_data.get("tags_list", ["設計", "開發", "測試"])
                    
                    loaded_tasks = saved_data.get("tasks", [])
                    for t in loaded_tasks:
                        if isinstance(t.get("due"), str):
                            t["due"] = date.fromisoformat(t["due"])
                    st.session_state.tasks = loaded_tasks
                except Exception as e:
                    st.warning(f"存檔讀取失敗，啟用預設資料。錯誤原因: {e}")
                    cls._load_default_mock_data()
            else:
                cls._load_default_mock_data()
                cls.save_data()

            st.session_state.cal_year = date.today().year
            st.session_state.cal_month = date.today().month
            st.session_state.selected_date = date.today()

    @classmethod
    def _load_default_mock_data(cls):
        st.session_state.tasks = [
            {"id": 1, "title": "資料庫設計", "category": "進行中", "due": date.today()+timedelta(days=2), "assignee": "王大明", "status": "Active", "progress": 80, "hours_spent": 4.5, "importance": "高", "urgency": "高", "history": []},
            {"id": 2, "title": "API 開發", "category": "未指派", "due": date.today()+timedelta
