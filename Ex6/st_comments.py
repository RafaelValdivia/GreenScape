import sys

import mysql.connector as mq
import streamlit as st

sys.path.append("Ex4")

from Ex4.comments_mysql import MySqlCommentSystem
from Ex4.comments_neo4j import Neo4jCommentSystem


def init_neo4j_from_streamlit():
    import json

    with open("connection.json", "r") as connections:
        file = json.load(connections)

        try:
            neo4j_system = Neo4jCommentSystem(
                **file["neo4j"], mysql_db_connection=file["mysql"]
            )
            st.session_state.neo4j_system = neo4j_system
            st.session_state.neo4j_connected = True
            st.success("✅ Conexión exitosa a Neo4j")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error de conexión: {str(e)}")


def display_comment_tree(conversation_data):
    if not conversation_data:
        st.info("No hay comentarios en esta publicación.")
        return

    def show_comment(comment, level=0):
        with st.container():
            col1, col2 = st.columns([1, 4])
            with col1:
                st.write(f"**👤 Usuario {comment.get('user_id', 'Anónimo')}**")
            with col2:
                st.write(comment["texto"])
                st.caption(
                    f"ID: {comment['id']} • Respuestas: {len(comment.get('responses', []))}"
                )

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
    current_pub = st.selectbox("Selecciona una Publicación", all_pubs)
    display_comment_tree(
        st.session_state.neo4j_system.get_full_conversation(current_pub)
    )
