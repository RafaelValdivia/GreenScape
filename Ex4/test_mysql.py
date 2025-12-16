# Ejercicio 4: Casos de prueba para conversaciones en MySQL
import mysql.connector as mq
from comments_mysql import MySqlCommentSystem

db_config = {
    "host": "localhost",
    "user": "greenscape_user",
    "password": "greenscape_pass",
    "database": "GreenScape",
    "port": 3306,
}

comment_system_mysql = MySqlCommentSystem(db_config)

# Datos de prueba para 5 conversaciones
conversations_data = [
    {
        "publication_id": 1,
        "root_comment": {"user_id": 1, "text": "¡Excelente publicación sobre plantas!"},
        "replies": [
            {"user_id": 2, "text": "Totalmente de acuerdo, muy informativo."},
            {"user_id": 3, "text": "¿Dónde puedo conseguir estas plantas?"},
            {"user_id": 4, "text": "En cualquier vivero local."},
            {"user_id": 5, "text": "Yo las compré en línea."},
            {"user_id": 6, "text": "¿Alguien tiene experiencia con el riego?"},
            {"user_id": 7, "text": "Riego cada 3 días en verano."},
            {"user_id": 8, "text": "Yo uso riego por goteo."},
            {"user_id": 9, "text": "¿Qué fertilizante recomiendan?"},
            {"user_id": 10, "text": "Fertilizante orgánico es mejor."},
            {"user_id": 11, "text": "Concuerdo con el fertilizante orgánico."},
            {"user_id": 12, "text": "¿Alguien sabe sobre plagas?"},
            {"user_id": 13, "text": "Usa aceite de neem para plagas."},
            {"user_id": 14, "text": "El aceite de neem funciona bien."},
            {"user_id": 15, "text": "¿Y para hongos?"},
            {"user_id": 16, "text": "Canela en polvo ayuda."},
            {"user_id": 17, "text": "Interesante, no sabía lo de la canela."},
            {"user_id": 18, "text": "¿Alguna recomendación de macetas?"},
            {"user_id": 19, "text": "Macetas de barro son las mejores."},
            {"user_id": 20, "text": "Prefiero las de plástico."},
            {"user_id": 21, "text": "Las de barro permiten mejor respiración."},
        ],
    },
    {
        "publication_id": 2,
        "root_comment": {
            "user_id": 22,
            "text": "Muy buenos consejos para principiantes.",
        },
        "replies": [
            {"user_id": 23, "text": "Soy principiante y me sirvió mucho."},
            {"user_id": 24, "text": "¿Cuál es la mejor planta para empezar?"},
            {"user_id": 25, "text": "La planta serpiente es muy resistente."},
            {"user_id": 26, "text": "El potos también es buena opción."},
            {"user_id": 27, "text": "Yo empecé con un cactus."},
            {"user_id": 28, "text": "Los cactus son fáciles de cuidar."},
            {"user_id": 29, "text": "¿Necesitan mucha luz?"},
            {"user_id": 30, "text": "Sí, necesitan luz directa."},
            {"user_id": 31, "text": "Pero no demasiada agua."},
            {"user_id": 32, "text": "Riego una vez al mes."},
            {"user_id": 33, "text": "Yo riego cada 15 días."},
            {"user_id": 34, "text": "Depende del clima."},
            {"user_id": 35, "text": "En verano riego más seguido."},
            {"user_id": 36, "text": "¿Alguien tiene suculentas?"},
            {"user_id": 37, "text": "Tengo varias, son hermosas."},
            {"user_id": 38, "text": "Las suculentas necesitan buen drenaje."},
            {"user_id": 39, "text": "Sí, el drenaje es crucial."},
            {"user_id": 40, "text": "Uso una mezcla de arena y tierra."},
            {"user_id": 41, "text": "Yo uso tierra especial para suculentas."},
            {"user_id": 42, "text": "Donde consigo esa tierra?"},
        ],
    },
    {
        "publication_id": 3,
        "root_comment": {"user_id": 43, "text": "¿Alguien tiene plantas de interior?"},
        "replies": [
            {"user_id": 44, "text": "Yo tengo varias en mi apartamento."},
            {"user_id": 45, "text": "¿Cuáles recomiendas para poca luz?"},
            {"user_id": 46, "text": "El potos y la planta serpiente."},
            {"user_id": 47, "text": "La lengua de suegra también."},
            {"user_id": 48, "text": "¿Cómo las cuidas?"},
            {"user_id": 49, "text": "Riego moderado y luz indirecta."},
            {"user_id": 50, "text": "Yo uso luz artificial."},
            {"user_id": 1, "text": "¿Funciona la luz artificial?"},
            {"user_id": 2, "text": "Sí, con luces LED especiales."},
            {"user_id": 3, "text": "¿Cuántas horas de luz?"},
            {"user_id": 4, "text": "Entre 8 y 12 horas diarias."},
            {"user_id": 5, "text": "¿Y la humedad?"},
            {"user_id": 6, "text": "Algunas necesitan humedad alta."},
            {"user_id": 7, "text": "Puedes usar un humidificador."},
            {"user_id": 8, "text": "O agrupar las plantas."},
            {"user_id": 9, "text": "¿Alguna recomendación de fertilizante?"},
            {"user_id": 10, "text": "Fertilizante líquido cada mes."},
            {"user_id": 11, "text": "En invierno no fertilizo."},
            {"user_id": 12, "text": "¿Por qué no en invierno?"},
            {"user_id": 13, "text": "Porque están en reposo."},
        ],
    },
    {
        "publication_id": 4,
        "root_comment": {
            "user_id": 14,
            "text": "Comparto mi experiencia con orquídeas.",
        },
        "replies": [
            {"user_id": 15, "text": "¡Qué hermosas! Siempre quise tener."},
            {"user_id": 16, "text": "Son difíciles de cuidar?"},
            {"user_id": 17, "text": "Requieren atención especial."},
            {"user_id": 18, "text": "¿Qué sustrato usas?"},
            {"user_id": 19, "text": "Corteza de pino y musgo."},
            {"user_id": 20, "text": "¿Cada cuánto riegas?"},
            {"user_id": 21, "text": "Una vez por semana."},
            {"user_id": 22, "text": "Yo riego cuando el sustrato se seca."},
            {"user_id": 23, "text": "¿Y la luz?"},
            {"user_id": 24, "text": "Luz indirecta brillante."},
            {"user_id": 25, "text": "No les gusta el sol directo."},
            {"user_id": 26, "text": "¿Cómo las fertilizas?"},
            {"user_id": 27, "text": "Fertilizante especial para orquídeas."},
            {"user_id": 28, "text": "Cada dos semanas en crecimiento."},
            {"user_id": 29, "text": "¿Problemas con plagas?"},
            {"user_id": 30, "text": "A veces cochinillas."},
            {"user_id": 31, "text": "Uso alcohol para limpiarlas."},
            {"user_id": 32, "text": "¿Y la floración?"},
            {"user_id": 33, "text": "Florecen una vez al año."},
            {"user_id": 34, "text": "A veces dos si tienen buen cuidado."},
        ],
    },
    {
        "publication_id": 5,
        "root_comment": {
            "user_id": 35,
            "text": "¿Cómo preparar abono orgánico en casa?",
        },
        "replies": [
            {"user_id": 36, "text": "Con restos de cocina y jardín."},
            {"user_id": 37, "text": "¿Qué materiales se necesitan?"},
            {"user_id": 38, "text": "Cáscaras de fruta, verduras, hojas."},
            {"user_id": 39, "text": "No usar carne ni lácteos."},
            {"user_id": 40, "text": "¿Y el proceso?"},
            {"user_id": 41, "text": "Se hace una pila y se voltea."},
            {"user_id": 42, "text": "Tarda varios meses."},
            {"user_id": 43, "text": "¿Hay método más rápido?"},
            {"user_id": 44, "text": "Con lombrices es más rápido."},
            {"user_id": 45, "text": "¿Lombricompost?"},
            {"user_id": 46, "text": "Sí, con lombrices rojas."},
            {"user_id": 47, "text": "¿Dónde consigo las lombrices?"},
            {"user_id": 48, "text": "En tiendas de jardinería."},
            {"user_id": 49, "text": "¿Y el contenedor?"},
            {"user_id": 50, "text": "Puedes hacerlo con cajas."},
            {"user_id": 1, "text": "¿Cada cuánto se cosecha?"},
            {"user_id": 2, "text": "Cada 2-3 meses."},
            {"user_id": 3, "text": "El té de compost también es bueno."},
            {"user_id": 4, "text": "¿Cómo se hace el té?"},
            {"user_id": 5, "text": "Se remueve compost en agua."},
        ],
    },
]

# Crear las conversaciones en MySQL
for conv in conversations_data:
    comment_id = comment_system_mysql.get_next_comment_id()
    publication_id = conv["publication_id"]
    root = conv["root_comment"]
    comment_system_mysql.add_comment(root["user_id"], publication_id, root["text"])
    root_comment_id = comment_id
    for reply in conv["replies"]:
        comment_id += 1
        comment_system_mysql.add_comment(
            reply["user_id"], publication_id, reply["text"], comment_id - 1
        )
