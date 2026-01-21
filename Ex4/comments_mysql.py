from datetime import datetime

import mysql.connector as mq
import pandas as pd


class MySqlCommentSystem:
    def __init__(self, db_config):
        self.db_config = db_config
        self.connection = self.get_db_connection()
        self.init_database()

    def init_database(self):
        cursor = self.connection.cursor()

        init_query = """
            CREATE TABLE IF NOT EXISTS ComentarRec (
                IDComentario INT NOT NULL AUTO_INCREMENT,
                IDU INT NOT NULL,
                IDPub INT NOT NULL,
                Texto TEXT NOT NULL,
                IDPadre INT NULL,
                FechaCreacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (IDComentario),
                FOREIGN KEY (IDU) REFERENCES Usuario(IDU) ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY (IDPub) REFERENCES Publicacion(IDPub) ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY (IDPadre) REFERENCES ComentarRec(IDComentario) ON DELETE CASCADE ON UPDATE CASCADE
            );
        """

        cursor.execute(init_query)

        cursor.execute("SELECT COUNT(*) FROM ComentarRec")
        count = cursor.fetchone()[0]

        if count == 0:
            self.migrate_comments()

        self.connection.commit()
        cursor.close()

    def migrate_comments(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT IDU, IDPub, Comentario FROM Comentar")
        original_comments = cursor.fetchall()

        for comment in original_comments:
            user_id, pub_id, text = comment
            query = "INSERT INTO ComentarRec (IDU, IDPub, Texto, IDPadre) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (user_id, pub_id, text, None))

        self.connection.commit()
        cursor.close()

    def get_db_connection(self):
        return mq.connect(**self.db_config)

    def add_comment(self, user_id, publication_id, comment_text, parent_id=None):
        cursor = self.connection.cursor()
        query = "INSERT INTO ComentarRec (IDU, IDPub, Texto, IDPadre) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (user_id, publication_id, comment_text, parent_id))
        comment_id = cursor.lastrowid
        self.connection.commit()
        cursor.close()
        return comment_id

    def get_full_conversation(self, publication_id):
        cursor = self.connection.cursor(dictionary=True)

        query = """
            SELECT
                c.IDComentario as id,
                c.Texto as texto,
                c.FechaCreacion as fechaCreacion,
                c.IDPadre as parent_id,
                c.IDU as user_id
            FROM ComentarRec c
            WHERE c.IDPub = %s
            ORDER BY c.FechaCreacion
        """

        cursor.execute(query, (publication_id,))
        rows = cursor.fetchall()

        if not rows:
            return {"Publicacion": publication_id, "comments": []}

        comments_by_id = {}
        roots = []

        for row in rows:
            comment_id = row["id"]
            comments_by_id[comment_id] = {
                "id": comment_id,
                "texto": row["texto"],
                "fechaCreacion": row["fechaCreacion"],
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

        cursor.close()
        return {
            "Publicacion": publication_id,
            "comments": roots,
            "total_comments": len(comments_by_id),
        }

    def get_all_publications(self):
        cursor = self.connection.cursor()
        query = """
            SELECT DISTINCT p.IDPub
            FROM Publicacion p
            INNER JOIN ComentarRec c ON p.IDPub = c.IDPub
            ORDER BY p.IDPub
        """
        cursor.execute(query)
        publications = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return publications

    def create_test_conversations(self):
        cursor = self.connection.cursor()

        print("Creando conversaciones de prueba (20+ comentarios)...")

        publication_id = 1
        user_id = 1

        root_comments = []

        for i in range(1, 6):
            text = f"Comentario raíz {i}"
            query = "INSERT INTO ComentarRec (IDU, IDPub, Texto, IDPadre) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (user_id, publication_id, text, None))
            root_id = cursor.lastrowid
            root_comments.append(root_id)

            for j in range(1, 4):
                reply_text = f"Respuesta {j} al comentario {i}"
                cursor.execute(
                    query, (user_id + j, publication_id, reply_text, root_id)
                )
                reply_id = cursor.lastrowid

                for k in range(1, 3):
                    nested_reply = f"Respuesta anidada {k} a la respuesta {j}"
                    cursor.execute(
                        query, (user_id + k, publication_id, nested_reply, reply_id)
                    )

        self.connection.commit()
        cursor.close()
        print(f"Creados {len(root_comments) * 10} comentarios de prueba")
        return True

    def clear_comments(self):
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM ComentarRec")
        self.connection.commit()
        cursor.close()
        return True

    def get_parent(self, comment_id):
        cursor = self.connection.cursor()
        query = "SELECT IDPadre FROM ComentarRec WHERE IDComentario = %s"
        cursor.execute(query, (comment_id,))
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else None

    def get_children(self, comment_id):
        cursor = self.connection.cursor(dictionary=True)
        query = """
            SELECT IDComentario, IDU, IDPub, Texto, IDPadre, FechaCreacion
            FROM ComentarRec
            WHERE IDPadre = %s
            ORDER BY FechaCreacion
        """
        cursor.execute(query, (comment_id,))
        children = cursor.fetchall()
        cursor.close()
        return children

    def get_next_comment_id(self):
        cursor = self.connection.cursor()
        query = "SELECT MAX(IDComentario) FROM ComentarRec"
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()
        return (result[0] or 0) + 1

    def close(self):
        if self.connection:
            self.connection.close()
