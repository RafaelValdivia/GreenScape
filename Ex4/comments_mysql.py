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
        return parent[0]

    def get_children(self, comment_id):
        connection = self.get_db_connection()
        cursor = connection.cursor()
        query = """

            FROM ComentarRec cr1 LEFT JOIN ComentarRec cr2 WHERE cr1.IDU == cr2.

            """
        cursor.execute(query, (comment_id,))
        parent = cursor.fetchone()
        return parent[0]


if __name__ == "__main__":
    from init import connection_dict as connd

    Comments = MySqlCommentSystem(connd)
    Comments.add_comment(27, 30, "sample", 39)
    conn = mq.connect(**connd)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ComentarRec")
    result = cursor.fetchall()
    print(result)
