import json
import mimetypes
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

import pymongo
from pymongo import MongoClient


class MongoDBPlantDocumentSystem:
    def __init__(
        self,
        mongo_uri="mongodb://localhost:27017/",
        db_name="GreenScape",
        username="root",
        password="mongo_pass",
        auth_source="admin",
    ):
        # If username and password are provided, create authenticated URI
        if username and password:
            # URL encode the username and password
            username = quote_plus(username)
            password = quote_plus(password)
            # Construct authenticated URI
            if "@" in mongo_uri:
                # URI already has credentials, replace them
                parts = mongo_uri.split("@", 1)
                mongo_uri = f"mongodb://{username}:{password}@{parts[1]}"
            else:
                # Add credentials to URI
                mongo_uri = mongo_uri.replace(
                    "mongodb://", f"mongodb://{username}:{password}@"
                )

            # Add authSource parameter
            if "?" in mongo_uri:
                mongo_uri += f"&authSource={auth_source}"
            else:
                mongo_uri += f"?authSource={auth_source}"

        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.documents = self.db.plant_documents
        self.storage_base_path = Path("greenscape_documents")
        self.storage_base_path.mkdir(exist_ok=True)
        self.create_indexes()

    def create_indexes(self):
        try:
            self.documents.create_index("plant_id")
            self.documents.create_index([("plant_id", 1), ("es_principal", 1)])
            self.documents.create_index("tipo_documento")
            print("Indexes created successfully")
        except pymongo.errors.OperationFailure as e:
            print(f"Note: Index creation may require authentication: {e}")

    def save_document_to_filesystem(self, plant_id, content, filename, is_principal):
        if is_principal:
            file_path = self.storage_base_path / str(plant_id) / "principal" / filename
        else:
            file_path = (
                self.storage_base_path / str(plant_id) / "secundarios" / filename
            )

        file_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(content, bytes):
            with open(file_path, "wb") as f:
                f.write(content)
        else:
            if not isinstance(content, str):
                content = str(content)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

        return str(file_path)

    def insert_main_document(self, plant_id, content, filename, plant_data=None):
        file_path = self.save_document_to_filesystem(plant_id, content, filename, True)
        file_size = os.path.getsize(file_path)
        mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

        main_doc = {
            "plant_id": plant_id,
            "tipo_documento": "Ficha Tecnica",
            "nombre_archivo": filename,
            "ruta_archivo": file_path,
            "mime_type": mime_type,
            "tamano": file_size,
            "es_principal": True,
            "documentos_secundarios": [],
            "fecha_creacion": datetime.now(),
            "fecha_actualizacion": datetime.now(),
            "metadata": plant_data or {},
        }

        result = self.documents.update_one(
            {"plant_id": plant_id, "es_principal": True},
            {"$set": main_doc},
            upsert=True,
        )

        return self.documents.find_one({"plant_id": plant_id, "es_principal": True})

    def insert_secondary_document(
        self, plant_id, tipo_documento, content, filename, parent_id=None, metadata=None
    ):
        file_path = self.save_document_to_filesystem(plant_id, content, filename, False)
        file_size = os.path.getsize(file_path)
        mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

        main_doc = self.documents.find_one({"plant_id": plant_id, "es_principal": True})
        parent_doc_id = parent_id or (str(main_doc["_id"]) if main_doc else None)

        secondary_doc = {
            "plant_id": plant_id,
            "tipo_documento": tipo_documento,
            "nombre_archivo": filename,
            "ruta_archivo": file_path,
            "mime_type": mime_type,
            "tamano": file_size,
            "es_principal": False,
            "documento_padre": parent_doc_id,
            "fecha_creacion": datetime.now(),
            "fecha_actualizacion": datetime.now(),
            "metadata": metadata or {},
        }

        result = self.documents.insert_one(secondary_doc)
        return str(result.inserted_id)

    def format_document(self, doc):
        if not doc:
            return None

        formatted = {
            "id": str(doc["_id"]),
            "type": doc["tipo_documento"],
            "filename": doc["nombre_archivo"],
            "filepath": doc["ruta_archivo"],
            "mime_type": doc["mime_type"],
            "size": doc["tamano"],
            "created": doc["fecha_creacion"],
            "updated": doc["fecha_actualizacion"],
            "is_principal": doc.get("es_principal", False),
        }

        if "metadata" in doc:
            formatted["metadata"] = doc["metadata"]

        if "documento_padre" in doc:
            formatted["parent_id"] = doc["documento_padre"]

        return formatted

    def get_plant_documents(self, plant_id):
        main_doc = self.documents.find_one({"plant_id": plant_id, "es_principal": True})

        if not main_doc:
            return None

        # Find secondary documents for this plant
        secondary_docs = list(
            self.documents.find({"plant_id": plant_id, "es_principal": False})
        )

        return {
            "plant_id": plant_id,
            "main_document": self.format_document(main_doc),
            "secondary_documents": [
                self.format_document(doc) for doc in secondary_docs
            ],
            "total_documents": 1 + len(secondary_docs),
        }

    def get_all_plant_ids(self):
        try:
            distinct_ids = self.documents.distinct("plant_id")
            return sorted([pid for pid in distinct_ids if pid is not None])
        except Exception as e:
            print(f"Error getting plant IDs: {e}")
            return []

    def create_test_data(self):
        print("Creating test data...")

        for plant_id in range(1, 6):
            print(f"Creating documents for plant {plant_id}...")

            # Create main document
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

            # Create 3 secondary documents
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

        print("Test data created successfully!")
        return True
