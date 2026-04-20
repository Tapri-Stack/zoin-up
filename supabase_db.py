import os
import random
from supabase import create_client, Client
from dotenv import load_dotenv
from functools import wraps
from typing import Callable, Any

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


def query_table(table_name: str, data_filter: Callable[[list], Any]):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            table = self.supabase.table(table_name)
            query = func(self, table, *args, **kwargs)
            data = query.execute().data
            return data_filter(data) if data else None

        return wrapper

    return decorator


class DB:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    @query_table("session", lambda data: data[0])
    def create_session(self, table, msg_id: int):
        return table.insert({"msg_id": msg_id})

    @query_table("session", lambda data: data[0]["msg_id"])
    def get_session(self, table):
        return table.select("msg_id, is_active").eq("is_active", True).order("created_at", desc=True).limit(1)

    @query_table("session", lambda data: data[0])
    def update_session_deactivate(self, table):
        return table.update({"is_active": False}).eq("is_active", True)

    @query_table("excuses", lambda data: data[0])
    def create_excuse(self, table, excuse: str, creator_id: int):
        return table.insert({"excuse": excuse, "creator_id": creator_id})

    @query_table("excuses", lambda data: random.choice(data)["excuse"])
    def get_excuse(self, table):
        return table.select("excuse")

    @query_table("agenda", lambda data: data[0])
    def create_agenda(self, table, agenda: str, creator_id: int, msg_id: int | None = None):
        return table.insert({"agenda": agenda, "creator_id": creator_id, "msg_id": msg_id})

    @query_table("agenda", lambda data: data[0]["agenda"])
    def get_agenda(self, table):
        return table.select("agenda, is_active, created_at").eq("is_active", True).order("created_at", desc=True).limit(1)

    @query_table("agenda", lambda data: data[0])
    def update_agenda_deactivate(self, table):
        return table.update({"is_active": False}).eq("is_active", True)

    @query_table("server", lambda data: data[0]["name"])
    def get_server_id(self, table, name: str, id_type: str):
        return table.select("name, id_type").eq("name", name).eq("id_type", id_type)
