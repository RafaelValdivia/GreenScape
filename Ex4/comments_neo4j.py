import datetime

from neo4j import GraphDatabase


class Neo4jCommentSystem:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_comment(self, user_id, publication_id, text, parent_comment_id=None):
        """Crear un nuevo comentario, opcionalmente como respuesta a otro"""
        with self.driver.session() as session:
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
                "comment_id": self._get_next_comment_id(),
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
            RETURN
                inicial.id as id_inicial,
                inicial.texto as texto_inicial,
                [(inicial)<-[:ESCRIBIO]-(autor:Usuario) | autor.nombre][0] as autor_inicial,
                collect({
                    id: respuestas.id,
                    texto: respuestas.texto,
                    nivel: nivel,
                    autor: [(respuestas)<-[:ESCRIBIO]-(autor:Usuario) | autor.nombre][0],
                    fecha: respuestas.fechaCreacion
                }) as todas_respuestas
            ORDER BY nivel
            """

            result = session.run(query, {"comment_id": comment_id})
            return result.single()

    def get_conversation_tree(self, comment_id):
        """Obtener la conversación como árbol jerárquico"""
        with self.driver.session() as session:
            query = """
            MATCH (c:Comentario {id: $comment_id})
            CALL apoc.path.subgraphAll(c, {
                relationshipFilter: "<RESPONDE_A",
                labelFilter: "Comentario",
                maxLevel: 20
            })
            YIELD nodes, relationships
            RETURN
                [node in nodes | {
                    id: node.id,
                    texto: node.texto,
                    autor: [(node)<-[:ESCRIBIO]-(u:Usuario) | u.nombre][0],
                    fecha: node.fechaCreacion
                }] as conversacion_completa,
                size(nodes) as total_comentarios
            """

            result = session.run(query, {"comment_id": comment_id})
            return result.single()

    def _get_next_comment_id(self):
        """Obtener el siguiente ID disponible para comentario"""
        with self.driver.session() as session:
            result = session.run("""
            MATCH (c:Comentario)
            RETURN MAX(c.id) as max_id
            """)
            record = result.single()
            return (record["max_id"] or 0) + 1


# Ejemplo de uso
def test_neo4j_implementation():
    # Configurar conexión
    comment_system = Neo4jCommentSystem("bolt://localhost:7687", "neo4j", "password")

    # Crear comentarios de prueba (simulando los mismos que en MySQL)
    print("Creando comentarios de prueba...")

    # Comentario raíz
    comment_system.create_comment(
        user_id=8,
        publication_id=24,
        text="¡Qué interesante publicación sobre plantas! Me encantó ver cómo cuidar las suculentas.",
    )

    # Obtener ID del comentario raíz (asumimos que es 1)
    root_comment_id = 1

    # Crear respuestas (simulando el hilo de 25 comentarios)
    responses = [
        (
            35,
            24,
            "Totalmente de acuerdo. Yo tengo varias suculentas en casa, ¿algún consejo específico?",
            root_comment_id,
        ),
        (
            8,
            24,
            "Lo más importante es el riego. Solo riega cuando la tierra esté completamente seca.",
            2,
        ),
        (19, 24, "¿Cada cuánto tiempo recomiendas regar en invierno?", 3),
        # ... continuar con más respuestas
    ]

    for user_id, pub_id, text, parent_id in responses:
        comment_system.create_comment(user_id, pub_id, text, parent_id)

    # Obtener conversación completa
    print("\nObteniendo conversación completa...")
    conversation = comment_system.get_full_conversation(root_comment_id)

    if conversation:
        print(f"\nConversación a partir del comentario {conversation['id_inicial']}:")
        print(f"Autor: {conversation['autor_inicial']}")
        print(f"Texto: {conversation['texto_inicial']}")
        print(f"\nRespuestas ({len(conversation['todas_respuestas'])}):")

        for resp in conversation["todas_respuestas"]:
            indent = "  " * resp["nivel"]
            print(f"{indent}Nivel {resp['nivel']}: {resp['autor']} - {resp['texto']}")

    # Obtener como árbol jerárquico
    print("\n\nObteniendo árbol jerárquico de conversación...")
    tree = comment_system.get_conversation_tree(root_comment_id)

    if tree:
        print(f"Total comentarios en el árbol: {tree['total_comentarios']}")
        for comment in tree["conversacion_completa"]:
            print(
                f"ID: {comment['id']}, Autor: {comment['autor']}, Fecha: {comment['fecha']}"
            )

    comment_system.close()


# Ejecutar prueba
if __name__ == "__main__":
    test_neo4j_implementation()
