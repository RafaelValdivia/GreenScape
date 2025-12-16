import json
import mimetypes
import os
from datetime import datetime
from pathlib import Path

import mysql.connector as mq


class PlantDocumentSystem:
    def __init__(self, db_config, base_path="/greenscape_docs"):
        self.db_config = db_config
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)

    def get_db_connection(self):
        return mq.connect(**self.db_config)

    def get_plant_directory(self, plant_id):
        plant_dir = self.base_path / str(plant_id)
        plant_dir.mkdir(parents=True, exist_ok=True)
        return plant_dir

    def detect_mime_type(self, filename):
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type

    def save_document_file(self, plant_id, file_content, filename, is_principal=False):
        plant_dir = self.get_plant_directory(plant_id)

        if is_principal:
            target_dir = plant_dir / "principal"
            target_dir.mkdir(exist_ok=True)
            for existing_file in target_dir.glob("*.json"):
                existing_file.unlink()
        else:
            target_dir = plant_dir / "secundarios"
            target_dir.mkdir(exist_ok=True)

        filepath = target_dir / filename

        if isinstance(file_content, bytes):
            with open(filepath, "wb") as f:
                f.write(file_content)
        else:
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
    ):
        connection = self.get_db_connection()
        cursor = connection.cursor()

        query = """
        INSERT INTO DocumentoPlanta
        (IDProd, TipoDocumento, NombreArchivo, RutaArchivo, MimeType, Tamano, EsPrincipal, DocumentoPadre)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
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
            ),
        )

        document_id = cursor.lastrowid
        connection.commit()
        cursor.close()
        connection.close()

        return document_id

    def create_main_document(
        self,
        plant_id,
        file_content,
        filename,
        mime_type=None,
    ):
        json_mime_types = [
            "application/json",
            "application/json; charset=utf-8",
            "text/json",
            "application/x-json",
        ]
        if not mime_type:
            mime_type = self.detect_mime_type(filename)
        if mime_type not in json_mime_types:
            raise TypeError("Main document must be of json extension")

        filepath = self.save_document_file(
            plant_id, file_content, filename, is_principal=True
        )
        file_size = os.path.getsize(filepath)

        doc_id = self.insert_document_metadata(
            plant_id=plant_id,
            tipo_documento="Ficha Tecnica",
            filename=filename,
            filepath=filepath,
            mime_type=mime_type,
            file_size=file_size,
            is_principal=True,
        )

        return doc_id

    def create_secondary_document(
        self,
        plant_id,
        tipo_documento,
        file_content,
        filename,
        title=None,
        mime_type=None,
        parent_doc_id=None,
    ):
        if not title:
            title = filename
        if not mime_type:
            mime_type = self.detect_mime_type(filename)
        filepath = self.save_document_file(
            plant_id, file_content, filename, is_principal=False
        )
        file_size = os.path.getsize(filepath)

        doc_id = self.insert_document_metadata(
            plant_id=plant_id,
            tipo_documento=tipo_documento,
            filename=filename,
            filepath=filepath,
            mime_type=mime_type,
            file_size=file_size,
            is_principal=False,
            parent_doc_id=parent_doc_id,
        )

        plant_dir = self.get_plant_directory(plant_id)
        prdoc_dir = plant_dir / "principal"
        for doc in prdoc_dir.glob("*.json"):
            with open(doc, "w") as file:
                content = json.load(file)
                content["secondary_documents"][title] = plant_dir / "secundarios"
                json.dump(content, file, indent=4)

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
            "main_document": {
                "id": principal_doc["IDDocumento"],
                "type": principal_doc["TipoDocumento"],
                "filename": principal_doc["NombreArchivo"],
                "filepath": principal_doc["RutaArchivo"],
                "mime_type": principal_doc["MimeType"],
                "size": principal_doc["Tamano"],
                "created": principal_doc["FechaCreacion"],
                "updated": principal_doc["FechaActualizacion"],
                "additional_metadata": principal_doc["MetadatosAdicionales"],
            },
            "secondary_documents": [
                {
                    "id": doc["IDDocumento"],
                    "type": doc["TipoDocumento"],
                    "filename": doc["NombreArchivo"],
                    "filepath": doc["RutaArchivo"],
                    "mime_type": doc["MimeType"],
                    "size": doc["Tamano"],
                    "created": doc["FechaCreacion"],
                    "updated": doc["FechaActualizacion"],
                    "parent_id": doc["DocumentoPadre"],
                    "additional_metadata": doc["MetadatosAdicionales"],
                }
                for doc in secondary_docs
            ],
        }
        return hierarchical_structure
