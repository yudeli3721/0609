import streamlit as st
from datetime import datetime, date, timedelta
import json
import os

# 輔助函式：自訂 JSON 序列化工具，用來處理 datetime.date 轉換問題
class WorkflowEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)

class AppInitializer:
    DB_FILE = "workflow_db.json"  # 在地資料庫檔案名稱

    @classmethod
    def save_data(cls):
        """核心功能：隨時將記憶體資料強制備份到 JSON 檔案中"""
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
        # 1. 確保基礎核心欄位初始結構（防止重整遺失）
        if 'categories' not in st.session_state:
            st.session_state.categories = ["未指派", "進行中", "已完成"]

        # 2. 檢查是否有歷史存檔紀錄
        if 'tasks' not in st.session_state:
            if os.path.exists(cls.DB_FILE):
                try:
                    with open(cls.DB_FILE, "r", encoding="utf-8") as f:
                        saved_data = json.load(f)
                    
                    st.session_state.categories = saved_data.get("categories", ["未指派", "進行中", "已完成"])
                    st.session_state.partners = saved_data.get("partners", ["未指派", "王大明", "陳小華", "林志玲", "闕老師"])
                    st.session_state.current_user = saved_data.get("current_user", "闕老師")
                    st.session_state.roles = saved_data.get("roles", {"闕老師": 2, "王大明": 1, "陳小華": 0, "林志玲": 0, "未指派": 0})
                    st.session_state.meetings = saved_data.get("meetings", [])
                    st.session_state.approvals = saved_data.get("approvals", [])
                    st.session_state.tags_list = saved_data.get("tags_list", ["設計", "開發", "測試"])
                    
                    # 將 JSON 中的字串型態日期轉回 date 物件
                    loaded_tasks = saved_data.get("tasks", [])
                    for t in loaded_tasks:
                        if isinstance(t.get('due'), str):
                            t['due'] = date.fromisoformat(t['due'])
                    st.session_state.tasks = loaded_tasks
                    
                except Exception as e:
                    st.warning(f"存檔讀取失敗，啟用預設資料。錯誤原因: {e}")
                    cls._load_default_mock_data()
            else:
                # 第一次執行，查無檔案，加載預設 mock 資料並建立檔案
                cls._load_default_mock_data()
                cls.save_data()

            # 行事曆專用常駐變數初始設定
            st.session_state.cal_year = date.today().year
            st.session_state.cal_month = date.today().month
            st.session_state.selected_date = date.today()

    @classmethod
    def _load_default_mock_data(cls):
        """內部預設 mock 資料"""
        st.session_state.tasks = [
            {"id": 1, "title": "資料庫設計", "category": "進行中", "due": date.today()+timedelta(days=2), "assignee": "王大明", "status": "Active", "progress": 80, "hours_spent": 4.5, "importance": "高", "urgency": "高", "history": []},
            {"id": 2, "title": "API 開發", "category": "未指派", "due": date.today()+timedelta(days=5), "assignee": "陳小華", "status": "Active", "progress": 0, "hours_spent": 0.0, "importance": "高", "urgency": "低", "history": []}
        ]
        st.session_state.partners = ["未指派", "王大明", "陳小華", "林志玲", "闕老師"]
        st.session_state.current_user = "闕老師"
        st.session_state.roles = {"闕老師": 2, "王大明": 1, "陳小華": 0, "林志玲": 0, "未指派": 0}
        st.session_state.meetings = []
        st.session_state.approvals = []
        st.session_state.tags_list = ["設計", "開發", "測試"]


class ViewComponents:
    """可重用的 UI 元件"""
    @staticmethod
    def render_filters():
        with st.expander("🔍 進階多維度篩選器", expanded=False):
            c1, c2 = st.columns(2)
            with c1: f_a = st.multiselect("篩選指派對象", st.session_state.partners)
            with c2: f_t = st.multiselect("篩選標籤", st.session_state.tags_list)
            return f_a, f_t


class StreamFlowEngine:
    @staticmethod
    def add_log(task, message):
        if 'history' not in task: task['history'] = []
        time_str = datetime.now().strftime('%m-%d %H:%M')
        task['history'].append(f"[{time_str}] {st.session_state.current_user} {message}")
        AppInitializer.save_data()  # 任務異動時，自動觸發本地資料存檔


class TaskService:
    """處理所有與任務相關的邏輯"""
    @staticmethod
    def get_filtered_tasks(f_assignees, f_tags, tasks=None):
        if tasks is None: tasks = st.session_state.tasks
        filtered = []
        for t in tasks:
            if t['status'] != 'Active': continue
            
            task_assignee = t.get('assignee', '未指派')
            match_assignee = (not f_assignees) or (task_assignee in f_assignees)
            
            task_tags = t.get('tags', [])
            if isinstance(task_tags, list):
                match_tag = (not f_tags) or any(tag in f_tags for tag in task_tags)
            else:
                match_tag = (not f_tags) or (task_tags in f_tags)
                
            if match_assign
