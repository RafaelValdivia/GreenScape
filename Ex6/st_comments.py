import json
import sys

import mysql.connector as mq
import streamlit as st

sys.path.append("Ex4")

from Ex4.comments_mysql import MySqlCommentSystem
from Ex4.comments_neo4j import Neo4jCommentSystem

with open("connection.json", "r") as connections:
    file = json.load(connections)
    neo4j_conn = file["neo4j"]
    mysql_conn = file["mysql"]


def init_neo4j_from_streamlit():
    try:
        neo4j_system = Neo4jCommentSystem(**neo4j_conn, mysql_db_connection=mysql_conn)
        st.session_state.neo4j_system = neo4j_system
        st.session_state.neo4j_connected = True
        st.success("✅ Conexión exitosa a Neo4j")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Error de conexión: {str(e)}")


def display_comment_tree(pub_id, replier_id):
    conversation_data = st.session_state.neo4j_system.get_full_conversation(pub_id)
    if not conversation_data:
        st.info("No hay comentarios en esta publicación.")
        return

    if st.button("Create Test Data for this publication"):
        st.session_state.neo4j_system.create_test_conversations(pub_id, replier_id)
        st.rerun()

    def show_comment(comment, level=0):
        comment_id = comment["id"]
        user_id = comment["user_id"]
        if level > 0:
            cols = st.columns([level, 12 - level])
        else:
            cols = st.columns(1)
        with cols[-1]:
            col1, col2 = st.columns([1, 4])
            with col1:
                st.write(f"**👤 Usuario {user_id}**")
            with col2:
                st.write(comment["texto"])
                st.caption(
                    f"ID: {comment_id} • Respuestas: {len(comment.get('responses', []))}"
                )
                reply_text = st.text_input(
                    "Write a Reply", key=f"reply_text {comment_id}"
                )
                if st.button("Responder", key=f"reply_button {comment_id}"):
                    st.session_state.neo4j_system.add_comment(
                        replier_id, pub_id, reply_text, parent_comment_id=comment_id
                    )
                    st.rerun()

        for reply in comment.get("responses", []):
            with st.container():
                st.markdown(
                    """
                <div style="margin-left: 30px; padding-left: 10px; border-left: 2px solid #4CAF50;">
                """,
                    unsafe_allow_html=True,
                )
                show_comment(reply, level + 1)
                st.markdown("</div>", unsafe_allow_html=True)

    for comment in conversation_data["comments"]:
        show_comment(comment)
        st.divider()

    st.metric("Total de comentarios", conversation_data.get("total_comments", 0))


def show_conversation_manager():
    if "neo4j_system" not in st.session_state:
        init_neo4j_from_streamlit()
    all_pubs = st.session_state.neo4j_system.get_all_publications()
    all_users = st.session_state.neo4j_system.get_all_users()
    col1, col2 = st.columns(2)
    with col1:
        current_pub = st.selectbox("Selecciona una Publicación", all_pubs)
    with col2:
        current_user = st.selectbox("Selecciona un Usuario", all_users)
    display_comment_tree(current_pub, current_user)
