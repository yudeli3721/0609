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
            {"id": 2, "title": "API 開發", "category": "未指派", "due": date.today()+timedelta(days=5), "assignee": None, "status": "Active", "progress": 0, "hours_spent": 0.0, "importance": "高", "urgency": "低", "history": []}
        ]
        st.session_state.partners = ["王大明", "陳小華", "林志玲", "乓"]
        st.session_state.current_user = "乓"
        st.session_state.roles = {"乓": 2, "王大明": 1, "陳小華": 0, "林志玲": 0}
        st.session_state.meetings = []
        st.session_state.approvals = []
        st.session_state.tags_list = ["設計", "開發", "測試"]


class ViewComponents:
    @staticmethod
    def render_filters():
        with st.expander("🔍 進階多維度篩選器", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                f_a = st.multiselect("篩選指派對象", ["⚠️ 暫無負責人"] + st.session_state.partners)
            with c2:
                f_t = st.multiselect("篩選標籤", st.session_state.tags_list)
            return f_a, f_t


class StreamFlowEngine:
    @staticmethod
    def add_log(task, message):
        if "history" not in task:
            task["history"] = []
        time_str = datetime.now().strftime("%m-%d %H:%M")
        task["history"].append(f"[{time_str}] {st.session_state.current_user} {message}")
        AppInitializer.save_data()


class TaskService:
    @staticmethod
    def get_filtered_tasks(f_assignees, f_tags, tasks=None):
        if tasks is None:
            tasks = st.session_state.tasks
        filtered = []
        for t in tasks:
            if t["status"] != "Active":
                continue
            task_assignee = t.get("assignee")
            if not f_assignees:
                match_assignee = True
            else:
                if task_assignee is None and "⚠️ 暫無負責人" in f_assignees:
                    match_assignee = True
                else:
                    match_assignee = task_assignee in f_assignees

            task_tags = t.get("tags", [])
            if isinstance(task_tags, list):
                match_tag = (not f_tags) or any(tag in f_tags for tag in task_tags)
            else:
                match_tag = (not f_tags) or (task_tags in f_tags)
            if match_assignee and match_tag:
                filtered.append(t)
        return filtered

    @staticmethod
    def is_task_locked(task):
        locked_by = [t["title"] for t in st.session_state.tasks if t["id"] in task.get("depends_on", []) and t["category"] != "已完成" and t["status"] == "Active"]
        return len(locked_by) > 0, locked_by

    @staticmethod
    def calculate_team_capacity():
        import pandas as pd
        active_tasks = [t for t in st.session_state.tasks if t["status"] == "Active"]
        load_data = []
        for p in st.session_state.partners:
            active_count = len([t for t in active_tasks if t.get('assignee') == p and t['category'] == '進行中'])
            ready_count = len([t for t in active_tasks if t.get('assignee') == p and t['category'] == '未指派'])
            weight = (active_count * 1.0) + (ready_count * 0.3)
            load_data.append({"夥伴": p, "進行中(權重1.0)": active_count, "待辦(權重0.3)": ready_count, "總負載權重": round(weight, 1)})
        return pd.DataFrame(load_data)


class MeetingService:
    @staticmethod
    def get_visible_meetings(target_date=None):
        user = st.session_state.current_user
        role_level = st.session_state.roles.get(user, 0)
        meetings = st.session_state.meetings
        visible = [m for m in meetings if (user in m["attendees"] or role_level > st.session_state.roles.get(m["owner"], 0) or user == m["owner"])]
        if target_date:
            visible = [m for m in visible if m["time"] == target_date]
        return visible


class ApprovalService:
    @staticmethod
    def process_action(approval, action, reason, transfer_to=None):
        now_str = datetime.now().strftime("%m-%d %H:%M")
        if action == "同意":
            approval["status"] = "已同意"
            approval["history"].append(f"[{now_str}] {st.session_state.current_user} 同意。意見: {reason}")
        elif action == "駁回":
            approval["status"] = "已駁回"
            approval["history"].append(f"[{now_str}] {st.session_state.current_user} 駁回。意見: {reason}")
        elif action == "轉交":
            approval["current_signer"] = transfer_to
            approval["history"].append(f"[{now_str}] {st.session_state.current_user} 轉交給 {transfer_to}。意見: {reason}")
        AppInitializer.save_data()
