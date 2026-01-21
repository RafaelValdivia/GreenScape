import datetime
from ast import USub

import mysql.connector as mq
from neo4j import GraphDatabase


class Neo4jCommentSystem:
    def __init__(self, uri, user, password, mysql_db_connection=None):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self._cleanup_duplicates()
        self._setup_constraints()
        if mysql_db_connection is not None:
            self.migrate(mysql_db_connection)

    def _cleanup_duplicates(self):
        """Clean up duplicate nodes before setting constraints"""
        with self.driver.session() as session:
            session.run("""
                    MATCH (u:Usuario)
                    WITH u.id as userId, collect(u) as nodes
                    WHERE size(nodes) > 1
                    UNWIND tail(nodes) as toDelete
                    DETACH DELETE toDelete
                """)

            session.run("""
                    MATCH (p:Publicacion)
                    WITH p.id as pubId, collect(p) as nodes
                    WHERE size(nodes) > 1
                    UNWIND tail(nodes) as toDelete
                    DETACH DELETE toDelete
                """)

            session.run("""
                    MATCH (c:Comentario)
                    WITH c.id as commentId, collect(c) as nodes
                    WHERE size(nodes) > 1
                    UNWIND tail(nodes) as toDelete
                    DETACH DELETE toDelete
                """)

    def _setup_constraints(self):
        with self.driver.session() as session:
            try:
                session.run("""
                    CREATE CONSTRAINT IF NOT EXISTS FOR (u:Usuario)
                    REQUIRE u.id IS UNIQUE
                """)
                session.run("""
                    CREATE CONSTRAINT IF NOT EXISTS FOR (p:Publicacion)
                    REQUIRE p.id IS UNIQUE
                """)
                session.run("""
                    CREATE CONSTRAINT IF NOT EXISTS FOR (c:Comentario)
                    REQUIRE c.id IS UNIQUE
                """)
            except Exception as e:
                print(f"Warning: Could not create constraints: {e}")

    def migrate(self, db_connection):
        connection = mq.connect(**db_connection)
        cursor = connection.cursor()

        cursor.execute("SELECT DISTINCT IDU FROM Usuario")
        usuarios = cursor.fetchall()

        cursor.execute("SELECT DISTINCT IDPub FROM Publicacion")
        publicaciones = cursor.fetchall()

        cursor.execute("""
                SELECT DISTINCT
                    c.IDU,
                    c.IDPub,
                    c.Comentario,
                    ROW_NUMBER() OVER (ORDER BY c.IDU, c.IDPub) + 1000 as comment_id
                FROM Comentar c
            """)
        comentarios = cursor.fetchall()

        connection.close()

        processed_users = set()
        for usuario in usuarios:
            user_id = usuario[0]
            if user_id not in processed_users:
                self.add_user(user_id)
                processed_users.add(user_id)

        processed_pubs = set()
        for publicacion in publicaciones:
            pub_id = publicacion[0]
            if pub_id not in processed_pubs:
                self.add_publication(pub_id)
                processed_pubs.add(pub_id)

        for comentario in comentarios:
            user_id = comentario[0]
            publication_id = comentario[1]
            text = comentario[2]
            comment_id = comentario[3]

            if user_id not in processed_users:
                self.add_user(user_id)
                processed_users.add(user_id)

            if publication_id not in processed_pubs:
                self.add_publication(publication_id)
                processed_pubs.add(publication_id)

            self.add_comment(user_id, publication_id, text, comment_id=comment_id)

    def clear_database(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("Base de datos limpiada")

    def close(self):
        self.driver.close()

    def add_user(self, user_id):
        with self.driver.session() as session:
            query = """
            MERGE (u:Usuario {id: $user_id})
            """
            params = {"user_id": user_id}
            session.run(query, params)

    def add_publication(self, pub_id):
        with self.driver.session() as session:
            query = """
            MERGE (p:Publicacion {id: $pub_id})
            """
            params = {"pub_id": pub_id}
            session.run(query, params)

    def add_comment(
        self, user_id, publication_id, text, comment_id=None, parent_comment_id=None
    ):
        with self.driver.session() as session:
            if not comment_id:
                comment_id = self._get_next_comment_id()

            query = """
                MERGE (u:Usuario {id: $user_id})
                MERGE (p:Publicacion {id: $publication_id})
                CREATE (c:Comentario {
                    id: $comment_id,
                    texto: $text,
                    fechaCreacion: datetime()
                })
                CREATE (u)-[:ESCRIBIO]->(c)
                CREATE (c)-[:PERTENECE_A]->(p)
                RETURN c.id as comment_id
                """

            params = {
                "user_id": user_id,
                "publication_id": publication_id,
                "text": text,
                "comment_id": comment_id,
            }

            result = session.run(query, params)
            created_id = result.single()["comment_id"]

            if parent_comment_id:
                session.run(
                    """
                        MATCH (child:Comentario {id: $child_id})
                        MATCH (parent:Comentario {id: $parent_id})
                        MERGE (child)-[:RESPONDE_A]->(parent)
                    """,
                    {"child_id": created_id, "parent_id": parent_comment_id},
                )

            return created_id

    def get_all_publications(self):
        with self.driver.session() as session:
            query = """
            MATCH (p:Publicacion)
            RETURN p.id as id
            ORDER BY p.id
            """
            results = session.run(query)
            return [record["id"] for record in results]

    def get_all_users(self):
        with self.driver.session() as session:
            query = """
            MATCH (u:Usuario)
            RETURN u.id as id
            ORDER BY u.id
            """
            results = session.run(query)
            return [record["id"] for record in results]

    def get_all_comments(self):
        with self.driver.session() as session:
            query = """
            MATCH (c:Comentario)
            RETURN c.id as id
            ORDER BY c.id
            """
            results = session.run(query)
            return [record["id"] for record in results]

    def get_full_conversation(self, publication_id):
        with self.driver.session() as session:
            query = """
                MATCH (c:Comentario)-[:PERTENECE_A]->(p:Publicacion {id: $pub_id})
                OPTIONAL MATCH (c)-[:RESPONDE_A]->(parent:Comentario)
                OPTIONAL MATCH (u:Usuario)-[:ESCRIBIO]->(c)
                RETURN c.id as id,
                       c.texto as texto,
                       c.fechaCreacion as fecha,
                       parent.id as parent_id,
                       u.id as user_id
                ORDER BY c.fechaCreacion
                """

            result = session.run(query, {"pub_id": publication_id})
            rows = list(result)

            if not rows:
                return {"Publicacion": publication_id, "comments": []}

            comments_by_id = {}
            roots = []

            for row in rows:
                comment_id = row["id"]
                comments_by_id[comment_id] = {
                    "id": comment_id,
                    "texto": row["texto"],
                    "fechaCreacion": row["fecha"],
                    "user_id": row["user_id"],
                    "responses": [],
                }

            for row in rows:
                comment_id = row["id"]
                parent_id = row["parent_id"]

                if parent_id and parent_id in comments_by_id:
                    comments_by_id[parent_id]["responses"].append(
                        comments_by_id[comment_id]
                    )
                elif not parent_id:
                    roots.append(comments_by_id[comment_id])

            return {
                "Publicacion": publication_id,
                "comments": roots,
                "total_comments": len(comments_by_id),
            }

    def _get_next_comment_id(self):
        """Obtener el siguiente ID disponible para comentario"""
        with self.driver.session() as session:
            result = session.run("""
            OPTIONAL MATCH (c:Comentario)
            RETURN MAX(c.id) as max_id
            """)
            record = result.single()
            if record is None or record["max_id"] is None:
                return 1
            return record["max_id"] + 1

    def create_test_conversations(self, publication_id=1, user_id=1):
        root_comments = []

        for i in range(1, 6):
            text = f"Root comment {i}"
            root_id = self.add_comment(
                user_id=user_id, publication_id=publication_id, text=text
            )
            root_comments.append(root_id)

            for j in range(1, 4):
                reply_text = f"Reply {j} to comment {i}"
                reply_id = self.add_comment(
                    user_id=user_id + j,
                    publication_id=publication_id,
                    text=reply_text,
                    parent_comment_id=root_id,
                )

                for k in range(1, 3):
                    nested_text = f"Nested reply {k} to reply {j}"
                    self.add_comment(
                        user_id=user_id + k,
                        publication_id=publication_id,
                        text=nested_text,
                        parent_comment_id=reply_id,
                    )

        total = len(root_comments) * (1 + 3 + 3 * 2)
        return True
