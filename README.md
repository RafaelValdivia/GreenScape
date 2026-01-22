# GreenScape - Plataforma de Gestión de Plantas

## Descripción del Proyecto
GreenScape es una plataforma integral para la gestión y análisis de datos relacionados con plantas, que combina múltiples tecnologías de bases de datos (MySQL, MongoDB, Neo4j) con una interfaz web interactiva construida en Streamlit. El sistema permite gestionar documentos técnicos de plantas, analizar conversaciones en redes sociales, ejecutar consultas complejas y realizar análisis de usuarios.

## Estructura del Repositorio

```
GreenScape/
├── Ex2/                          # MERX de la Base de Datos
├── Ex3/                          # Consultas básicas en MySQL
│   └── mysql_queries.py          # Diccionario de consultas SQL
├── Ex4/                          # Sistema de comentarios
│   ├── comments_mysql.py         # Sistema de comentarios en MySQL
│   └── comments_neo4j.py         # Sistema de comentarios en Neo4j
├── Ex5/                          # Gestión de documentos
│   ├── doc_mongodb.py            # Sistema de documentos en MongoDB
│   └── doc_mysql.py              # Sistema de documentos en MySQL
├── Ex6/                          # Interfaz web
│   ├── st_app.py                 # Aplicación principal Streamlit
│   ├── st_sidebar.py             # Barra lateral de navegación
│   ├── st_document.py            # Gestor de documentos (MongoDB)
│   ├── st_comments.py            # Gestor de comentarios (Neo4j)
│   ├── st_queries.py             # Consultas SQL y análisis
├── greenscape_documents/         # Almacenamiento de documentos (generado)
├── docker-compose.yml            # Configuración de contenedores Docker
├── Dockerfile                    # Configuración de la imagen Docker
├── connection.json               # Configuración de conexiones a BD
├── Informe.md                    # Explicación de las desiciones tomadas en el proyecto
├── init.sql                      # Inicializador de todas las tablas de la base de datos en MySQL
├── LICENSE                       # Información de la licencia del Proyecto 
├── Orientación ... .pdf          # Orientación del proyecto dada por nuestro querido profesor
├── requirements.txt              # Dependencias de Python
└── README.md                     # Este archivo
```

## Documentación Técnica de Archivos Python

### doc_mongodb.py - Sistema de Gestión de Documentos en MongoDB

#### Clase: MongoDBPlantDocumentSystem
Sistema para gestionar documentos de plantas utilizando MongoDB como backend.

**Métodos principales:**

1. **`__init__(mongo_uri="mongodb://localhost:27017/", db_name="greenscape_docs", username=None, password=None, auth_source="admin")`**
   - **Parámetros:**
     - `mongo_uri`: URI de conexión a MongoDB
     - `db_name`: Nombre de la base de datos
     - `username`: Usuario para autenticación
     - `password`: Contraseña para autenticación
     - `auth_source`: Fuente de autenticación
   - **Retorna:** Instancia de la clase
   - **Función:** Inicializa la conexión a MongoDB, configura autenticación si se proporcionan credenciales, crea directorios de almacenamiento e índices.

2. **`create_indexes()`**
   - **Parámetros:** Ninguno
   - **Retorna:** None
   - **Función:** Crea índices en la colección para optimizar búsquedas por plant_id, tipo_documento y es_principal.

3. **`save_document_to_filesystem(plant_id, content, filename, is_principal)`**
   - **Parámetros:**
     - `plant_id`: ID de la planta
     - `content`: Contenido del documento (bytes o str)
     - `filename`: Nombre del archivo
     - `is_principal`: Booleano que indica si es documento principal
   - **Retorna:** Ruta del archivo guardado (str)
   - **Función:** Guarda el documento en el sistema de archivos, organizándolo en directorios según plant_id y tipo.

4. **`insert_main_document(plant_id, content, filename, plant_data=None)`**
   - **Parámetros:**
     - `plant_id`: ID de la planta
     - `content`: Contenido del documento
     - `filename`: Nombre del archivo
     - `plant_data`: Metadatos adicionales (opcional)
   - **Retorna:** Documento principal insertado/actualizado (dict)
   - **Función:** Inserta o actualiza el documento principal de una planta, guarda el archivo y registra metadatos en MongoDB.

5. **`insert_secondary_document(plant_id, tipo_documento, content, filename, parent_id=None, metadata=None)`**
   - **Parámetros:**
     - `plant_id`: ID de la planta
     - `tipo_documento`: Tipo de documento (ej: "Certificado Fitosanitario")
     - `content`: Contenido del documento
     - `filename`: Nombre del archivo
     - `parent_id`: ID del documento padre (opcional)
     - `metadata`: Metadatos adicionales (opcional)
   - **Retorna:** ID del documento insertado (str)
   - **Función:** Inserta un documento secundario, lo guarda en el sistema de archivos y lo vincula al documento principal.

6. **`format_document(doc)`**
   - **Parámetros:**
     - `doc`: Documento de MongoDB (dict)
   - **Retorna:** Documento formateado (dict)
   - **Función:** Formatea un documento de MongoDB para su visualización, extrayendo campos relevantes.

7. **`get_plant_documents(plant_id)`**
   - **Parámetros:**
     - `plant_id`: ID de la planta
   - **Retorna:** Estructura con documentos principal y secundarios (dict) o None si no existe
   - **Función:** Recupera todos los documentos de una planta, organizados jerárquicamente.

8. **`get_all_plant_ids()`**
   - **Parámetros:** Ninguno
   - **Retorna:** Lista de IDs de plantas (list)
   - **Función:** Obtiene todos los IDs de plantas únicos en la base de datos.

9. **`create_test_data()`**
   - **Parámetros:** Ninguno
   - **Retorna:** True si se crearon datos exitosamente
   - **Función:** Crea datos de prueba con 5 plantas, cada una con un documento principal y 3 secundarios.

### doc_mysql.py - Sistema de Gestión de Documentos en MySQL

#### Clase: PlantDocumentSystem
Sistema alternativo para gestionar documentos de plantas utilizando MySQL como backend.

**Métodos principales:**

1. **`__init__(db_config, base_path="greenscape_docs")`**
   - **Parámetros:**
     - `db_config`: Configuración de conexión a MySQL
     - `base_path`: Ruta base para almacenamiento de archivos
   - **Retorna:** Instancia de la clase
   - **Función:** Inicializa la conexión a MySQL, crea la tabla DocumentoPlanta si no existe y configura directorios.

2. **`create_table()`**
   - **Parámetros:** Ninguno
   - **Retorna:** None
   - **Función:** Crea la tabla DocumentoPlanta con los campos necesarios e índices.

3. **`save_document_file(plant_id, file_content, filename, is_principal=False)`**
   - **Parámetros:**
     - `plant_id`: ID de la planta
     - `file_content`: Contenido del archivo
     - `filename`: Nombre del archivo
     - `is_principal`: Booleano que indica si es documento principal
   - **Retorna:** Ruta del archivo guardado (Path)
   - **Función:** Guarda el archivo en el sistema de archivos organizado por plant_id.

4. **`insert_document_metadata(plant_id, tipo_documento, filename, filepath, mime_type, file_size, is_principal=False, parent_doc_id=None, metadata=None)`**
   - **Parámetros:**
     - `plant_id`: ID de la planta
     - `tipo_documento`: Tipo de documento
     - `filename`: Nombre del archivo
     - `filepath`: Ruta del archivo
     - `mime_type`: Tipo MIME
     - `file_size`: Tamaño del archivo
     - `is_principal`: Si es documento principal
     - `parent_doc_id`: ID del documento padre
     - `metadata`: Metadatos adicionales en JSON
   - **Retorna:** ID del documento insertado (int)
   - **Función:** Inserta metadatos del documento en la base de datos MySQL.

5. **`insert_main_document(plant_id, content, filename, plant_data=None)`**
   - **Parámetros:**
     - `plant_id`: ID de la planta
     - `content`: Contenido del documento
     - `filename`: Nombre del archivo
     - `plant_data`: Metadatos adicionales
   - **Retorna:** ID del documento (int)
   - **Función:** Inserta o actualiza el documento principal de una planta.

6. **`insert_secondary_document(plant_id, tipo_documento, content, filename, parent_id=None, metadata=None)`**
   - **Parámetros:**
     - `plant_id`: ID de la planta
     - `tipo_documento`: Tipo de documento
     - `content`: Contenido del documento
     - `filename`: Nombre del archivo
     - `parent_id`: ID del documento padre
     - `metadata`: Metadatos adicionales
   - **Retorna:** ID del documento insertado (int)
   - **Función:** Inserta un documento secundario vinculado al principal.

7. **`get_plant_documents(plant_id)`**
   - **Parámetros:**
     - `plant_id`: ID de la planta
   - **Retorna:** Estructura jerárquica de documentos (dict) o None
   - **Función:** Obtiene todos los documentos de una planta organizados jerárquicamente.

8. **`get_document_content(doc_id)`**
   - **Parámetros:**
     - `doc_id`: ID del documento
   - **Retorna:** Contenido del archivo (str) o None
   - **Función:** Lee el contenido del archivo desde la ruta almacenada en la base de datos.

9. **`update_document_metadata(doc_id, metadata_updates)`**
   - **Parámetros:**
     - `doc_id`: ID del documento
     - `metadata_updates`: Diccionario con actualizaciones de metadatos
   - **Retorna:** True si se actualizó correctamente
   - **Función:** Actualiza los metadatos de un documento existente.

### st_app.py - Aplicación Principal Streamlit

#### Funciones:

1. **`init_session_state()`**
   - **Parámetros:** Ninguno
   - **Retorna:** None
   - **Función:** Inicializa variables de estado de la sesión Streamlit.

2. **`show_user_analisis()`**
   - **Parámetros:** Ninguno
   - **Retorna:** None
   - **Función:** Muestra el selector de consultas para análisis de usuario (función placeholder).

3. **`show_product_manager()`**
   - **Parámetros:** Ninguno
   - **Retorna:** None
   - **Función:** Muestra el selector de consultas para gestor de precios (función placeholder).

4. **Función principal** (`if __name__ == "__main__":`)
   - **Parámetros:** Ninguno
   - **Retorna:** None
   - **Función:** Configura la aplicación Streamlit, inicializa el estado y dirige a la página seleccionada.

### st_comments.py - Módulo de Gestión de Comentarios

#### Funciones:

1. **`init_neo4j_from_streamlit()`**
   - **Parámetros:** Ninguno
   - **Retorna:** None
   - **Función:** Inicializa la conexión a Neo4j desde Streamlit y guarda la instancia en session_state.

2. **`display_comment_tree(conversation_data)`**
   - **Parámetros:**
     - `conversation_data`: Datos de conversación en formato de árbol
   - **Retorna:** None
   - **Función:** Muestra un árbol de comentarios jerárquico en la interfaz Streamlit.

3. **`show_conversation_manager()`**
   - **Parámetros:** Ninguno
   - **Retorna:** None
   - **Función:** Interfaz principal para gestionar conversaciones, permite seleccionar publicaciones y ver sus comentarios.

### st_document.py - Módulo de Gestión de Documentos

#### Funciones:

1. **`show_document_system()`**
   - **Parámetros:** Ninguno
   - **Retorna:** None
   - **Función:** Interfaz completa para gestionar documentos de plantas, incluye:
     - Configuración de MongoDB
     - Visualización de documentos por planta
     - Carga de nuevos documentos
     - Creación de datos de prueba
     - Estadísticas de documentos

### st_queries.py - Módulo de Consultas SQL y Análisis

#### Funciones principales:

1. **`get_db_connection(connection=db_connection)`**
   - **Parámetros:**
     - `connection`: Configuración de conexión (por defecto de connection.json)
   - **Retorna:** Conexión a MySQL
   - **Función:** Establece y retorna una conexión a la base de datos MySQL.

2. **`mysql_run_query(query: str)`**
   - **Parámetros:**
     - `query`: Consulta SQL a ejecutar
   - **Retorna:** Resultados de la consulta (list[tuple])
   - **Función:** Ejecuta una consulta SQL y retorna los resultados.

3. **`mysql_get_query_results(inciso: str)`**
   - **Parámetros:**
     - `inciso`: Letra que identifica la consulta (ej: "a", "b", etc.)
   - **Retorna:** DataFrame de pandas con resultados
   - **Función:** Ejecuta una consulta predefinida y la retorna en formato DataFrame.

4. **`handle_query_trigger_auditoria()`**
   - **Parámetros:** Ninguno
   - **Retorna:** None
   - **Función:** Maneja la interfaz para el trigger de auditoría de precios, incluye:
     - Creación del trigger si no existe
     - Interfaz para modificar precios
     - Visualización del historial de cambios
     - Métricas de cambios de precios

5. **`handle_query_stored_procedure()`**
   - **Parámetros:** Ninguno
   - **Retorna:** None
   - **Función:** Implementa análisis detallado de actividad de usuario con:
     - Selección de usuario y rango de fechas
     - Análisis temporal con series de tiempo
     - Gráficos de actividad por día/semana/mes
     - Métricas de actividad e intensidad
     - Heatmaps y visualizaciones avanzadas

6. **`handle_query_influencers()`**
   - **Parámetros:** Ninguno
   - **Retorna:** None
   - **Función:** Analiza influencers y su impacto en ventas:
     - Identificación de top influencers por interacciones
     - Análisis de impacto en ventas de plantas específicas
     - Cálculo de tasa de conversión de seguidores a compradores
     - Métricas de incremento porcentual en ventas

7. **`handle_query_anomalous_patterns()`**
   - **Parámetros:** Ninguno
   - **Retorna:** None
   - **Función:** Detección de patrones anómalos en vendedores:
     - Variaciones de precio significativas
     - Patrones de calificación inconsistentes
     - Análisis de compradores únicos
     - Identificación de vendedores sospechosos

8. **`show_query_selector(selected_query=None)`**
   - **Parámetros:**
     - `selected_query`: Consulta específica a mostrar (opcional)
   - **Retorna:** None
   - **Función:** Selector principal de consultas, maneja las 25+ consultas predefinidas y las especiales.

### st_sidebar.py - Módulo de Barra Lateral

#### Funciones:

1. **`sidebar()`**
   - **Parámetros:** Ninguno
   - **Retorna:** None
   - **Función:** Crea la barra lateral de navegación con:
     - Logo y título de la aplicación
     - Botones de navegación entre páginas
     - Indicador de página actual
     - Botón de recarga

2. **`show_home()`**
   - **Parámetros:** Ninguno
   - **Retorna:** None
   - **Función:** Página de inicio (actualmente vacía, puede personalizarse).

### mysql_queries.py - Diccionario de Consultas SQL

#### Variables:

1. **`queries`** (dict)
   - **Contenido:** Diccionario con 25+ consultas SQL predefinidas
   - **Claves:** Letras de "a" a "q"
   - **Valores:** Consultas SQL correspondientes
   - **Función:** Centraliza todas las consultas SQL para mantenimiento fácil

2. **`columns`** (dict)
   - **Contenido:** Nombres de columnas para cada consulta
   - **Claves:** Letras de "a" a "n"
   - **Valores:** Listas de nombres de columnas
   - **Función:** Proporciona nombres descriptivos para las columnas de resultados

### comments_mysql.py - Sistema de Comentarios en MySQL

#### Clase: MySqlCommentSystem

**Métodos principales:**

1. **`__init__(db_config)`**
   - **Parámetros:**
     - `db_config`: Configuración de conexión a MySQL
   - **Retorna:** Instancia de la clase
   - **Función:** Inicializa el sistema, crea la tabla ComentarRec si no existe y migra datos.

2. **`migrate(connection, cursor)`**
   - **Parámetros:**
     - `connection`: Conexión a MySQL
     - `cursor`: Cursor de MySQL
   - **Retorna:** None
   - **Función:** Migra datos desde la tabla Comentar original a ComentarRec.

3. **`add_comment(user_id, publication_id, comment_text, parent_id=None)`**
   - **Parámetros:**
     - `user_id`: ID del usuario
     - `publication_id`: ID de la publicación
     - `comment_text`: Texto del comentario
     - `parent_id`: ID del comentario padre (opcional)
   - **Retorna:** None
   - **Función:** Agrega un comentario a la base de datos.

4. **`get_parent(comment_id)`**
   - **Parámetros:**
     - `comment_id`: ID del comentario
   - **Retorna:** ID del comentario padre o None
   - **Función:** Obtiene el ID del comentario padre.

5. **`get_children(comment_id)`**
   - **Parámetros:**
     - `comment_id`: ID del comentario
   - **Retorna:** Lista de comentarios hijos
   - **Función:** Obtiene todos los comentarios hijos de un comentario.

### comments_neo4j.py - Sistema de Comentarios en Neo4j

#### Clase: Neo4jCommentSystem

**Métodos principales:**

1. **`__init__(uri, user, password, mysql_db_connection=None)`**
   - **Parámetros:**
     - `uri`: URI de conexión a Neo4j
     - `user`: Usuario de Neo4j
     - `password`: Contraseña de Neo4j
     - `mysql_db_connection`: Configuración para migración desde MySQL
   - **Retorna:** Instancia de la clase
   - **Función:** Inicializa conexión a Neo4j, limpia duplicados, crea constraints y migra datos si se proporciona conexión MySQL.

2. **`migrate(mysql_db_connection)`**
   - **Parámetros:**
     - `mysql_db_connection`: Configuración de conexión a MySQL
   - **Retorna:** None
   - **Función:** Migra datos de comentarios desde MySQL a Neo4j.

3. **`add_comment(user_id, publication_id, text, comment_id=None, parent_comment_id=None)`**
   - **Parámetros:**
     - `user_id`: ID del usuario
     - `publication_id`: ID de la publicación
     - `text`: Texto del comentario
     - `comment_id`: ID específico para el comentario (opcional)
     - `parent_comment_id`: ID del comentario padre (opcional)
   - **Retorna:** ID del comentario creado
   - **Función:** Agrega un comentario al grafo de Neo4j, creando relaciones con usuario, publicación y comentario padre.

4. **`get_full_conversation(publication_id)`**
   - **Parámetros:**
     - `publication_id`: ID de la publicación
   - **Retorna:** Estructura de árbol de comentarios
   - **Función:** Obtiene todos los comentarios de una publicación organizados en árbol jerárquico.

## Configuración con Docker

El proyecto incluye configuración Docker completa. Para iniciar todas las bases de datos:

```bash
docker-compose up -d
```

Esto iniciará:
- MySQL en puerto 3306
- MongoDB en puerto 27017
- Neo4j en puerto 7687
- phpMyAdmin en puerto 8080

## Ejecución de la Aplicación

```bash
cd Ex6
streamlit run st_app.py
```

Acceder en navegador: `http://localhost:8501`

## Notas Técnicas

- **Autenticación MongoDB:** El sistema soporta autenticación básica y construcción de URIs con credenciales.
- **Migración de datos:** Los sistemas de comentarios incluyen funciones para migrar datos entre MySQL y Neo4j.
- **Almacenamiento dual:** Los documentos se almacenan tanto en base de datos (metadatos) como en sistema de archivos (contenido).
- **Streamlit session_state:** Se utiliza extensivamente para mantener estado entre interacciones.
- **Consultas parametrizadas:** Todas las consultas SQL utilizan parámetros para prevenir inyección SQL.

## Dependencias Principales

- Streamlit 1.28.0+ para la interfaz web
- pymongo 4.5.0+ para MongoDB
- mysql-connector-python 8.1.0+ para MySQL
- neo4j 5.14.0+ para Neo4j
- pandas 2.1.0+ para manipulación de datos

Para una lista completa, ver `requirements.txt`.
