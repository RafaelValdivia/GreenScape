import datetime
from ast import USub

import mysql.connector as mq
from neo4j import GraphDatabase


class Neo4jCommentSystem:
    def __init__(self, uri, user, password, mysql_db_connection=None):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        if mysql_db_connection is not None:
            self.migrate(mysql_db_connection)

    def migrate(self, db_connection):
        connection = mq.connect(**db_connection)
        cursor = connection.cursor()
        cursor.execute("SELECT IDU FROM Usuario U")
        usuarios = cursor.fetchall()
        cursor.execute("SELECT IDPub FROM Publicacion P")
        publicaciones = cursor.fetchall()
        cursor.execute("SELECT IDU, IDPub, Comentario FROM Comentar")
        comentarios = cursor.fetchall()
        for usuario in usuarios:
            self.add_user(usuario[0])
        for publicacion in publicaciones:
            self.add_publication(publicacion[0])
        for comentario in comentarios:
            print(comentario)
            self.add_comment(comentario[0], comentario[1], comentario[2])

    def clear_database(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("Base de datos limpiada")

    def close(self):
        self.driver.close()

    def add_user(self, user_id):
        with self.driver.session() as session:
            query = """
            CREATE (u:Usuario {id: $user_id})
            """
            params = {"user_id": user_id}
            session.run(query, params)

    def add_publication(self, pub_id):
        with self.driver.session() as session:
            query = """
            CREATE (p:Publicatcon {id: $pub_id})
            """
            params = {"pub_id": pub_id}
            session.run(query, params)

    def add_comment(self, user_id, publication_id, text, parent_comment_id=None):
        """Crear un nuevo comentario, opcionalmente como respuesta a otro"""
        with self.driver.session() as session:
            comment_id = self._get_next_comment_id()
            query = """
            MATCH (u:Usuario {id: $user_id})
            MATCH (p:Publicacion {id: $publication_id})
            CREATE (c:Comentario {
                id: $comment_id,
                texto: $text,
                fechaCreacion: datetime()
            })
            CREATE (u)-[:ESCRIBIO]->(c)
            CREATE (c)-[:PERTENECE_A]->(p)
            """

            params = {
                "user_id": user_id,
                "publication_id": publication_id,
                "text": text,
                "comment_id": comment_id,
            }

            session.run(query, params)

            # Si es respuesta, crear relación RESPONDE_A
            if parent_comment_id:
                response_query = """
                MATCH (hijo:Comentario {id: $child_id})
                MATCH (padre:Comentario {id: $parent_id})
                CREATE (hijo)-[:RESPONDE_A]->(padre)
                """
                session.run(
                    response_query,
                    {"child_id": params["comment_id"], "parent_id": parent_comment_id},
                )

    def get_full_conversation(self, comment_id):
        """Obtener toda la conversación a partir de un comentario inicial"""
        with self.driver.session() as session:
            query = """
            MATCH (inicial:Comentario {id: $comment_id})
            OPTIONAL MATCH path = (inicial)<-[:RESPONDE_A*]-(respuestas:Comentario)
            WITH inicial, respuestas, length(path) as nivel
            WITH inicial,
                    collect({
                    respuesta: respuestas,
                    nivel: nivel
                    }) as respuestas_con_nivel
            WITH inicial,
                    [r in respuestas_con_nivel |
                    {id: r.respuesta.id,
                        texto: r.respuesta.texto,
                        nivel: r.nivel,
                        autor: [(r.respuesta)<-[:ESCRIBIO]-(autor:Usuario) | autor.nombre][0],
                        fecha: r.respuesta.fechaCreacion
                    }
                    ] as respuestas_ordenadas
            ORDER BY respuestas_ordenadas.nivel
            RETURN
                inicial.id as id_inicial,
                inicial.texto as texto_inicial,
                [(inicial)<-[:ESCRIBIO]-(autor:Usuario) | autor.nombre][0] as autor_inicial,
                inicial.fechaCreacion as fecha_inicial,
                respuestas_ordenadas as todas_respuestas
            """

            result = session.run(query, {"comment_id": comment_id})
            return result.single()

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
            return record["max_id"]


# Ejecutar prueba
if __name__ == "__main__":
    connections = {
        "mysql": {
            "host": "localhost",
            "user": "greenscape_user",
            "password": "greenscape_pass",
            "database": "GreenScape",
            "port": 3306,
        },
        "mongodb": {
            "uri": "mongodb://root:mongo_pass@localhost:27017/GreenScape?authSource=admin",
            "database": "GreenScape",
        },
        "neo4j": {
            "uri": "bolt://localhost:7687",
            "user": "neo4j",
            "password": "neo4j_password",
        },
    }
    neo4j_conn = connections["neo4j"]
    uri = neo4j_conn["uri"]
    user = neo4j_conn["user"]
    pswd = neo4j_conn["password"]
    neo4j_comments = Neo4jCommentSystem(uri, user, pswd, connections["mysql"])
    # neo4j_comments.clear_database()
    # print(neo4j_comments._get_next_comment_id())
