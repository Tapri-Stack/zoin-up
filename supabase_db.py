import os
import random
from supabase import create_client, Client
from dotenv import load_dotenv
from functools import wraps
from cachetools import cached, TTLCache


load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


def execute(data_filter=None):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            query = func(self, *args, **kwargs)
            data = query.execute().data
            return data_filter(data) if data and data_filter else data

        return wrapper

    return decorator


class DB:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    def _table(self, table_name: str):
        return self.supabase.table(table_name)

    # -------------------- session --------------------

    @execute
    def create_session(self, id: int):
        return self._table("session").insert({"id": id})

    @execute(lambda data: data[0]["id"])
    def get_curr_session(self):
        return self._table("session").select("id, is_active").eq("is_active", True).order("created_at", desc=True).limit(1)

    @execute
    def end_curr_session(self):
        return self._table("session").update({"is_active": False}).eq("id", self.get_curr_session())

    # -------------------- server --------------------

    @cached({})
    @execute(lambda data: data[0]["id"])
    def get_server_id(self, name: str, kind: str):
        return self._table("server").select("id, name, kind").eq("name", name).eq("kind", kind)

    # -------------------- create activity --------------------

    @execute
    def _create_activity(self, kind: str, value: str, member_id: int):
        return self._table("session").insert({"kind": kind, "value": value, "member_id": member_id})

    def add_agenda(self, agenda: str, member_id: int):
        return self._create_activity("add_agenda", agenda, member_id)

    def add_excuse(self, excuse: str, member_id: int):
        return self._create_activity("add_excuse", excuse, member_id)

    def add_message_hallucination(self, hallucination: str, member_id: int):
        return self._create_activity("add_message_hallucination", hallucination, member_id)

    def add_join_call_hallucination(self, hallucination: str, member_id: int):
        return self._create_activity("add_join_call_hallucination", hallucination, member_id)

    def add_leave_call_hallucination(self, hallucination: str, member_id: int):
        return self._create_activity("add_leave_call_hallucination", hallucination, member_id)

    def add_step_out_hallucination(self, hallucination: str, member_id: int):
        return self._create_activity("add_step_out_hallucination", hallucination, member_id)

    def join_call(self, member_id: int):
        return self._create_activity("join_call", self.get_curr_session(), member_id)

    def leave_call(self, member_id: int, excuse: str):
        return self._create_activity("leave_call", excuse, member_id)

    def step_out(self, member_id: int, excuse: str):
        return self._create_activity("step_out", excuse, member_id)

    def add_manager_call(self, tag: str, member_id: int):
        return self._create_activity("add_manager_call", tag, member_id)

    def add_pm_call(self, tag: str, member_id: int):
        return self._create_activity("add_pm_call", tag, member_id)

    def add_proactive_communication(self, communication: str, member_id: int):
        return self._create_activity("add_proactive_communication", communication, member_id)

    # -------------------- get activity --------------------

    @execute
    def _get_activity(self, kind: str, value: str = None):
        if value:
            return self._table("activity").select("*").eq("kind", kind).eq("value", value)
        return self._table("activity").select("*").eq("kind", kind)

    @execute(lambda data: random.choice(data)["value"])
    def _get_random_activity(self, kind: str):
        return self._table("activity").select("kind, value").eq("kind", kind)

    @execute(lambda data: data[0]["value"])
    def get_latest_agenda(self):
        return self._table("activity").select("kind, value").eq("kind", "add_agenda").order("created_at", desc=True).limit(1)

    def get_random_excuse(self):
        return self._get_random_activity("add_excuse")

    def get_random_message_hallucination(self):
        return self._get_random_activity("add_message_hallucination")

    def get_random_join_call_hallucination(self):
        return self._get_random_activity("add_join_call_hallucination")

    def get_random_leave_call_hallucination(self):
        return self._get_random_activity("add_leave_call_hallucination")

    def get_random_step_out_hallucination(self):
        return self._get_random_activity("add_step_out_hallucination")

    def get_random_proactive_communication(self):
        return self._get_random_activity("add_proactive_communication")

    @cached(TTLCache(ttl=600))
    def get_manager_calls(self):
        return set([item["value"] for item in self._get_activity("add_manager_call")])

    @cached(TTLCache(ttl=600))
    def get_pm_calls(self):
        return set([item["value"] for item in self._get_activity("add_pm_call")])

    def get_joined_members(self):
        return set(item["member_id"] for item in self._get_activity("join_call", self.get_curr_session()))

    def get_left_members(self):
        return set(item["member_id"] for item in self._get_activity("leave_call", self.get_curr_session()))

    def get_active_members(self):
        return self.get_joined_members().difference(self.get_left_members())
