import mysql.connector as mq
import pandas as pd


class MySqlCommentSystem:
    def __init__(self, db_config):
        self.db_config = db_config
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
        connection = self.get_db_connection()
        cursor = connection.cursor()
        cursor.execute(init_query)
        self.migrate(connection, cursor)
        connection.commit()
        connection.close()

    def migrate(self, connection, cursor):
        cursor.execute("SELECT EXISTS(SELECT 1 FROM ComentarRec);")
        not_empty = cursor.fetchall()
        not_empty = not_empty[0][0]
        if not not_empty:
            cursor.execute("SELECT * FROM Comentar")
            original_table = cursor.fetchall()
            for row in original_table:
                row = list(row)
                row += [None]
                row = tuple(row)
                cursor.execute(
                    "INSERT INTO ComentarRec (IDU, IDPub, Texto, IDPadre) VALUES (%s, %s, %s, %s)",
                    row,
                )
            connection.commit()

    def get_db_connection(self):
        return mq.connect(**self.db_config)

    def add_comment(self, user_id, publication_id, comment_text, parent_id=None):
        connection = self.get_db_connection()
        cursor = connection.cursor()
        query = "INSERT INTO ComentarRec (IDU, IDPub, Texto, IDPadre) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (user_id, publication_id, comment_text, parent_id))
        connection.commit()

    def get_parent(self, comment_id):
        connection = self.get_db_connection()
        cursor = connection.cursor()
        query = """
            SELECT IDPadre
            FROM ComentarRec
            WHERE IDComentario = %s
            """
        cursor.execute(query, (comment_id,))
        parent = cursor.fetchone()
        connection.close()
        if parent:
            return parent[0]
        return None

    def get_children(self, comment_id):
        connection = self.get_db_connection()
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT IDComentario, IDU, IDPub, Texto, IDPadre, FechaCreacion
            FROM ComentarRec
            WHERE IDPadre = %s
            """
        cursor.execute(query, (comment_id,))
        children = cursor.fetchall()
        connection.close()
        return children

    def get_next_comment_id(self):
        connection = self.get_db_connection()
        cursor = connection.cursor()
        query = """
            SELECT MAX(cr.IDComentario)
            FROM ComentarRec cr
            """
        cursor.execute(query)
        max_id = cursor.fetchone()
        connection.close()
        if max_id and max_id[0] is not None:
            return max_id[0] + 1
        return 1
