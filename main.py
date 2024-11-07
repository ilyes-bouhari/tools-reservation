import streamlit as st
from supabase import create_client
from typing import Literal
from datetime import datetime

@st.cache_resource
def init_connection():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

supabase = init_connection()

# if "user" not in st.session_state:
#     st.session_state.user = 

supabase.auth.sign_in_with_password(
    credentials={
        "email": st.secrets["SUPABASE_USERNAME"], 
        "password": st.secrets["SUPABASE_PASSWORD"]
    }
)

def get_tools(date: datetime.date, session: Literal["1", "2"]) -> list[dict]:
    """Get a list of tools reserved for the given date and session."""
    reserved_tools = (supabase.table("history")
        .select("tool_id")
        .eq("reserved_at", date)
        .eq("session", session)
        .execute().data
    )
    reserved_tool_ids = [tool["tool_id"] for tool in reserved_tools]
    tools = supabase.table("tools").select("*").execute().data
    return [tool for tool in tools if tool["id"] not in reserved_tool_ids]

def clear():

    for tool in st.session_state.tools:
        # check if tool is already reserved
        reserved_tools = (supabase.table("history")
            .select("tool_id")
            .eq("tool_id", tool["id"])
            .eq("reserved_at", st.session_state.date)
            .eq("session", st.session_state.session["value"])
            .execute().data
        )
        
        if len(reserved_tools) > 0:
            st.error(f"{tool['name']} is already reserved!")
            continue

        # reserve tool
        supabase.table("history").insert({
            "teacher_id": st.session_state.teacher["id"],
            "tool_id": tool["id"],
            "reserved_at": str(st.session_state.date),
            "session": st.session_state.session["value"],        
        }).execute()

    st.session_state.teacher = None
    st.session_state.session = None
    st.session_state.date = None
    st.session_state.tools = []

st.selectbox(
    "Teacher", 
    supabase.table("teachers").select("*").execute().data, 
    format_func=lambda x: x["name"],
    index=None,
    key="teacher"
)

st.selectbox(
    "Session", 
    options=[
        {
            "label": "Session 1", 
            "value": "1"
        }, 
        {
            "label": "Session 2", 
            "value": "2"
        }
    ], 
    format_func=lambda x: x["label"], 
    index=None,
    key="session"
)

st.date_input(
    "Date", 
    value=datetime.now().date(),
    key="date"
)

if st.session_state.session and st.session_state.date:
    st.multiselect(
        "Tools", 
        get_tools(st.session_state.date, st.session_state.session["value"]), 
        format_func=lambda x: x["name"],
        key="tools"
    )

st.button(
    "Reserve", 
    on_click=clear, 
    disabled=not (
        st.session_state.teacher and 
        st.session_state.session and
        st.session_state.date and 
        len(st.session_state.tools) 
    )
)