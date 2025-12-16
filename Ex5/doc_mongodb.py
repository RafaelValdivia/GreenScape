import json
import mimetypes
import os
from datetime import datetime
from pathlib import Path

import pymongo
from pymongo import MongoClient


class MongoDBPlantDocumentSystem:
    def __init__(
        self, mongo_uri="mongodb://localhost:27017/", db_name="greenscape_docs",
        mysql_db_connection
    ):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.documents = self.db.plant_documents
        self.create_indexes()

    def create_indexes(self):
        self.documents.create_index("plant_id")
        self.documents.create_index([("plant_id", 1), ("es_principal", 1)])
        self.documents.create_index("tipo_documento")

    def save_document_to_filesystem(self, plant_id, content, filename, is_principal):
        base_path = Path("/greenscape_documents")
        if is_principal:
            file_path = base_path / str(plant_id) / "principal" / filename
        else:
            file_path = base_path / str(plant_id) / "secundarios" / filename

        file_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(content, bytes):
            with open(file_path, "wb") as f:
                f.write(content)
        else:
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
        return result.inserted_id

    def format_document(self, doc):
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

    def get_plant_documents(self, plant_id, piprincipal=None, secondary=None):
        pipeline = [
            {"$match": {"plant_id": plant_id}},
            {"$sort": {"es_principal": -1, "tipo_documento": 1, "fecha_creacion": 1}},
        ]

        docs = list(self.documents.aggregate(pipeline))

        if not docs:
            return None

        main_doc = next((d for d in docs if d["es_principal"]), None)
        secondary_docs = [d for d in docs if not d["es_principal"]]

        result = {
            "plant_id": plant_id,
            "main_document": self.format_document(main_doc) if main_doc else None,
            "secondary_documents": [self.format_document(d) for d in secondary_docs],
        }

        return result

    def search_documents(
        self,
        plant_id=None,
        doc_type=None,
        filename=None,
        is_principal=None,
        page=1,
        page_size=20,
        sort_criteria="fecha_creacion",
        desc=True,
    ):
        query = {}
        if plant_id:
            query["plant_id"] = plant_id
        if doc_type:
            query["tipo_documento"] = doc_type
        if filename:
            query["nombre_archivo"] = {"$regex": filename, "$options": "i"}
        if is_principal is not None:
            query["es_principal"] = is_principal

        skip = (page - 1) * page_size
        cursor = (
            self.documents.find(query)
            .skip(skip)
            .limit(page_size)
            .sort(sort_criteria, -1 if desc else 1)
        )
        total = self.documents.count_documents(query)
        return {
            "results": [self.format_document(doc) for doc in cursor],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    def update_document_metadata(self, document_id, metadata_updates):
        update_data = {
            "fecha_actualizacion": datetime.now(),
            "metadata": metadata_updates,
        }
        result = self.documents.update_one({"_id": document_id}, {"$set": update_data})
        return result.modified_count > 0
