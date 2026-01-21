import json
import mimetypes
import os
from datetime import datetime
from pathlib import Path

import mysql.connector as mq


class PlantDocumentSystem:
    def __init__(self, db_config, base_path="greenscape_docs"):
        self.db_config = db_config
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        self.create_table()

    def get_db_connection(self):
        return mq.connect(**self.db_config)

    def create_table(self):
        connection = self.get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS DocumentoPlanta (
            IDDocumento INT AUTO_INCREMENT PRIMARY KEY,
            IDProd INT NOT NULL,
            TipoDocumento VARCHAR(100) NOT NULL,
            NombreArchivo VARCHAR(255) NOT NULL,
            RutaArchivo TEXT NOT NULL,
            MimeType VARCHAR(100),
            Tamano INT,
            EsPrincipal BOOLEAN DEFAULT FALSE,
            DocumentoPadre INT,
            FechaCreacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            FechaActualizacion DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            MetadatosAdicionales JSON,
            INDEX idx_plant (IDProd),
            INDEX idx_principal (IDProd, EsPrincipal)
        )
        """)

        connection.commit()
        cursor.close()
        connection.close()

    def get_plant_directory(self, plant_id):
        plant_dir = self.base_path / str(plant_id)
        plant_dir.mkdir(parents=True, exist_ok=True)
        return plant_dir

    def save_document_file(self, plant_id, file_content, filename, is_principal=False):
        plant_dir = self.get_plant_directory(plant_id)

        if is_principal:
            target_dir = plant_dir / "principal"
            target_dir.mkdir(exist_ok=True)
        else:
            target_dir = plant_dir / "secundarios"
            target_dir.mkdir(exist_ok=True)

        filepath = target_dir / filename

        if isinstance(file_content, bytes):
            with open(filepath, "wb") as f:
                f.write(file_content)
        else:
            if not isinstance(file_content, str):
                file_content = str(file_content)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(file_content)

        return filepath

    def insert_document_metadata(
        self,
        plant_id,
        tipo_documento,
        filename,
        filepath,
        mime_type,
        file_size,
        is_principal=False,
        parent_doc_id=None,
        metadata=None,
    ):
        connection = self.get_db_connection()
        cursor = connection.cursor()

        if metadata and not isinstance(metadata, str):
            metadata = json.dumps(metadata)

        query = """
        INSERT INTO DocumentoPlanta
        (IDProd, TipoDocumento, NombreArchivo, RutaArchivo, MimeType, Tamano, EsPrincipal, DocumentoPadre, MetadatosAdicionales)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (
                plant_id,
                tipo_documento,
                filename,
                str(filepath),
                mime_type,
                file_size,
                is_principal,
                parent_doc_id,
                metadata,
            ),
        )

        document_id = cursor.lastrowid
        connection.commit()
        cursor.close()
        connection.close()

        return document_id

    def insert_main_document(self, plant_id, content, filename, plant_data=None):
        mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

        connection = self.get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT IDDocumento FROM DocumentoPlanta WHERE IDProd = %s AND EsPrincipal = TRUE",
            (plant_id,),
        )
        existing_main = cursor.fetchone()

        if existing_main:
            cursor.execute(
                """
                UPDATE DocumentoPlanta
                SET NombreArchivo = %s, RutaArchivo = %s, MimeType = %s, Tamano = %s, MetadatosAdicionales = %s
                WHERE IDDocumento = %s
                """,
                (
                    filename,
                    str(self.save_document_file(plant_id, content, filename, True)),
                    mime_type,
                    len(content) if isinstance(content, str) else len(content),
                    json.dumps(plant_data) if plant_data else None,
                    existing_main["IDDocumento"],
                ),
            )
            doc_id = existing_main["IDDocumento"]
        else:
            filepath = self.save_document_file(plant_id, content, filename, True)
            file_size = os.path.getsize(filepath)

            doc_id = self.insert_document_metadata(
                plant_id=plant_id,
                tipo_documento="Ficha Tecnica",
                filename=filename,
                filepath=filepath,
                mime_type=mime_type,
                file_size=file_size,
                is_principal=True,
                metadata=plant_data,
            )

        connection.commit()
        cursor.close()
        connection.close()
        return doc_id

    def insert_secondary_document(
        self, plant_id, tipo_documento, content, filename, parent_id=None, metadata=None
    ):
        mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

        if parent_id is None:
            connection = self.get_db_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT IDDocumento FROM DocumentoPlanta WHERE IDProd = %s AND EsPrincipal = TRUE",
                (plant_id,),
            )
            main_doc = cursor.fetchone()
            cursor.close()
            connection.close()

            if main_doc:
                parent_id = main_doc["IDDocumento"]

        filepath = self.save_document_file(plant_id, content, filename, False)
        file_size = os.path.getsize(filepath)

        doc_id = self.insert_document_metadata(
            plant_id=plant_id,
            tipo_documento=tipo_documento,
            filename=filename,
            filepath=filepath,
            mime_type=mime_type,
            file_size=file_size,
            is_principal=False,
            parent_doc_id=parent_id,
            metadata=metadata,
        )

        return doc_id

    def get_plant_documents(self, plant_id):
        connection = self.get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT * FROM DocumentoPlanta
            WHERE IDProd = %s AND EsPrincipal = TRUE
            """,
            (plant_id,),
        )

        principal_doc = cursor.fetchone()

        if not principal_doc:
            cursor.close()
            connection.close()
            return None

        cursor.execute(
            """
            SELECT * FROM DocumentoPlanta
            WHERE IDProd = %s AND EsPrincipal = FALSE
            ORDER BY TipoDocumento, FechaCreacion
            """,
            (plant_id,),
        )

        secondary_docs = cursor.fetchall()

        hierarchical_structure = {
            "plant_id": plant_id,
            "main_document": self.format_document(principal_doc),
            "secondary_documents": [
                self.format_document(doc) for doc in secondary_docs
            ],
            "total_documents": 1 + len(secondary_docs),
        }

        cursor.close()
        connection.close()
        return hierarchical_structure

    def format_document(self, doc):
        if not doc:
            return None

        formatted = {
            "id": doc["IDDocumento"],
            "type": doc["TipoDocumento"],
            "filename": doc["NombreArchivo"],
            "filepath": doc["RutaArchivo"],
            "mime_type": doc["MimeType"],
            "size": doc["Tamano"],
            "created": doc["FechaCreacion"],
            "updated": doc["FechaActualizacion"],
            "is_principal": doc["EsPrincipal"],
        }

        if doc.get("MetadatosAdicionales"):
            try:
                formatted["metadata"] = json.loads(doc["MetadatosAdicionales"])
            except:
                formatted["metadata"] = doc["MetadatosAdicionales"]

        if doc.get("DocumentoPadre"):
            formatted["parent_id"] = doc["DocumentoPadre"]

        return formatted

    def get_all_plant_ids(self):
        connection = self.get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT DISTINCT IDProd FROM DocumentoPlanta ORDER BY IDProd")
        plant_ids = [row[0] for row in cursor.fetchall()]

        cursor.close()
        connection.close()
        return plant_ids

    def create_test_data(self):
        for plant_id in range(1, 6):
            main_content = f"""FICHA TÉCNICA - Planta {plant_id}

Nombre: Planta Ejemplo {plant_id}
Especie: Especie {plant_id}
Familia: Familia Botánica {plant_id}
Origen: Región {plant_id}
Dificultad: Media
Luz: Indirecta
Riego: Moderado
Temperatura: 18-24°C

Descripción: Esta es una planta de ejemplo con características únicas.
Cuidados básicos: Regar cuando el sustrato esté seco al tacto."""

            self.insert_main_document(
                plant_id=plant_id,
                content=main_content,
                filename=f"ficha_tecnica_{plant_id}.txt",
                plant_data={
                    "especie": f"Especie_{plant_id}",
                    "dificultad": "Media",
                    "origen": f"Región {plant_id}",
                },
            )

            secondary_types = [
                "Certificado Fitosanitario",
                "Guía de Riego Estacional",
                "Manual de Tratamiento de Plagas",
            ]

            for doc_type in secondary_types:
                sec_content = f"""{doc_type.upper()}
Planta: #{plant_id}
Fecha de Emisión: {datetime.now().strftime("%Y-%m-%d")}

Contenido:
Este documento proporciona información específica sobre {doc_type.lower()}.
Incluye recomendaciones y procedimientos para el cuidado óptimo de la planta.

Estado: Válido
Válido hasta: {(datetime.now().replace(year=datetime.now().year + 1)).strftime("%Y-%m-%d")}"""

                self.insert_secondary_document(
                    plant_id=plant_id,
                    tipo_documento=doc_type,
                    content=sec_content,
                    filename=f"{doc_type.lower().replace(' ', '_')}_{plant_id}.txt",
                )

        return True

    def get_document_content(self, doc_id):
        connection = self.get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT RutaArchivo FROM DocumentoPlanta WHERE IDDocumento = %s", (doc_id,)
        )
        doc = cursor.fetchone()

        cursor.close()
        connection.close()

        if doc:
            try:
                with open(doc["RutaArchivo"], "r", encoding="utf-8") as f:
                    return f.read()
            except:
                return None

        return None

    def update_document_metadata(self, doc_id, metadata_updates):
        connection = self.get_db_connection()
        cursor = connection.cursor()

        current_metadata = {}
        cursor.execute(
            "SELECT MetadatosAdicionales FROM DocumentoPlanta WHERE IDDocumento = %s",
            (doc_id,),
        )
        result = cursor.fetchone()

        if result and result[0]:
            try:
                current_metadata = json.loads(result[0])
            except:
                current_metadata = {}

        current_metadata.update(metadata_updates)

        cursor.execute(
            "UPDATE DocumentoPlanta SET MetadatosAdicionales = %s WHERE IDDocumento = %s",
            (json.dumps(current_metadata), doc_id),
        )

        connection.commit()
        cursor.close()
        connection.close()
        return True
