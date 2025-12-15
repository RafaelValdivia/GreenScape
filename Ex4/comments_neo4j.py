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
            )
            """
        connection = self.get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM ComentarRec")
        count_new = cursor.fetchone()[0]

        if count_new == 0:
            self.migrate(cursor)
        cursor.execute(init_query)
        connection.close()

    def get_db_connection(self):
        return mq.connect(**self.db_config)

    def migrate(self, cursor):
        cursor.execute("SELECT * FROM Comentar")
        result = cursor.fetchall()
        comment_df = pd.DataFrame(result)
        # cursor.execute("DROP TABLE Comentar")
        for index, row in comment_df.iterrows():
            user_id, publication_id = row["IDU"], row["IDPub"]
            comment_text = row["Texto"]
            self.add_comment(user_id, publication_id, comment_text)
        del comment_df

    def add_comment(self, user_id, publication_id, comment_text, parent_id=None):
        connection = self.get_db_connection()
        cursor = connection.cursor()
        query = "INSERT INTO ComentarRec (IDU, IDPub, Texto, IDPadre) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (user_id, publication_id, comment_text, parent_id))

    def get_parent_comment(self, comment_id):
        connection = self.get_db_connection()
        cursor = connection.cursor()
        query = """
            SELECT IDPadre
            FROM ComentarRec
            WHERE IDComentario = %s
            """
        cursor.execute(query, (comment_id,))
        parent = cursor.fetchone()
        # parent = pd.DataFrame(parent)
        print(parent)

    def get_conversation(self, comment_id, conversation=[]):
        conversation.append(comment_id)
        parent = self.get_parent_comment(comment_id)
        self.get_conversation(parent)
        return conversation[::-1]


if __name__ == "__main__":
    from init import connection_dict as connd

    Comments = MySqlCommentSystem(connd)
