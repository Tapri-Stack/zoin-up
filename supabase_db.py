import os
import random
from supabase import create_client, Client
from dotenv import load_dotenv
from functools import wraps
from dataclasses import dataclass, asdict

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


@dataclass
class DBActivityMetadata:
    use_count: int = 0
    vote_count: int = 0


class DB:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    def _table(self, table_name: str):
        return self.supabase.table(table_name=table_name)

    # -------------------- session --------------------

    @execute
    def create_session(self, id: int):
        return self._table("session").insert({"id": id}).execute()

    @execute(lambda data: data[0]["id"])
    def get_session(self):
        return self._table("session").select("id, is_active").eq("is_active", True).order("created_at", desc=True).limit(1)

    @execute
    def deactivate_session(self):
        id = self.get_session()
        return self._table("session").update({"is_active": False}).eq("id", id)

    @execute(lambda data: data[0]["logs"])
    def get_session_logs(self):
        id = self.get_session()
        return self._table("session").select("id, logs").eq("id", id)

    @execute
    def add_session_log(self, log: str):
        id = self.get_session()
        logs = f"{self.get_session_logs()}\n{log}"
        return self._table("session").update({"logs": logs}).eq("id", id)

    # -------------------- server --------------------

    @execute(lambda data: data[0]["id"])
    def get_server_id(self, name: str, kind: str):
        return self._table("server").select("id, name, kind").eq("name", name).eq("kind", kind)

    # -------------------- create activity --------------------

    @execute
    def _create_activity(self, kind: str, value: str, member_id: int, metadata: DBActivityMetadata | None = None):
        if not metadata:
            metadata = DBActivityMetadata()

        return self._table("session").insert({"kind": kind, "value": value, "member_id": member_id, "metadata": asdict(metadata)})

    def add_agenda(self, agenda: str, member_id: int):
        return self._create_activity("add_agenda", agenda, member_id)

    def add_excuse(self, excuse: str, member_id: int):
        return self._create_activity("add_excuse", excuse, member_id)

    def add_hallucination(self, hallucination: str, member_id: int):
        return self._create_activity("add_hallucination", hallucination, member_id)

    def join_call(self, member_id: int):
        session_id = self.get_session()
        return self._create_activity("join_call", session_id, member_id)

    def leave_call(self, member_id: int):
        session_id = self.get_session()
        return self._create_activity("leave_call", session_id, member_id)

    def pause_call(self, member_id: int):
        session_id = self.get_session()
        return self._create_activity("pause_call", session_id, member_id)

    # -------------------- get activity --------------------

    @execute
    def _get_activity(self, kind: str, value: str):
        return self._table("activity").select("*").eq("kind", kind).eq("value", value)

    @execute(lambda data: data[0]["value"])
    def get_latest_agenda(self):
        return self._table("activity").select("kind, value").eq("kind", "add_agenda").order("created_at", desc=True).limit(1)

    @execute(lambda data: random.choice(data)["value"])
    def get_random_excuse(self):
        return self._table("activity").select("kind, value").eq("kind", "add_excuse")

    @execute(lambda data: random.choice(data)["value"])
    def get_random_hallucination(self):
        return self._table("activity").select("kind, value").eq("kind", "add_hallucination")

    def get_active_members(self):
        session_id = self.get_session()

        join_call_data = self._get_activity("join_call", session_id)
        joined = set(item["member_id"] for item in join_call_data)

        left_call_data = self._get_activity("left_call", session_id)
        left = set(item["member_id"] for item in left_call_data)

        return list(joined.difference(left))

    # -------------------- update activity metadata --------------------

    @execute
    def _update_metadata(self, kind: str, value: str, metadata: DBActivityMetadata):
        return self._table("activity").update({"metadata": asdict(metadata)}).eq("kind", kind).eq("value", value)

    def _use_activity(self, kind: str, value: str):
        for item in self._get_activity(kind, value):
            metadata = DBActivityMetadata(**item["metadata"])
            metadata.use_count += 1

            self._update_metadata(item["kind"], item["value"], metadata)

    def _vote_activity(self, kind: str, value: str):
        for item in self._get_activity(kind, value):
            metadata = DBActivityMetadata(**item["metadata"])
            metadata.vote_count += 1

            self._update_metadata(item["kind"], item["value"], metadata)

    def use_agenda(self, agenda: str):
        return self._use_activity("add_agenda", agenda)

    def use_excuse(self, excuse: str):
        return self._use_activity("add_excuse", excuse)

    def use_hallucination(self, hallucination: str):
        return self._use_activity("add_hallucination", hallucination)

    def vote_agenda(self, agenda: str):
        return self._vote_activity("add_agenda", agenda)

    def vote_excuse(self, excuse: str):
        return self._vote_activity("add_excuse", excuse)

    def vote_hallucination(self, hallucination: str):
        return self._vote_activity("add_hallucination", hallucination)
