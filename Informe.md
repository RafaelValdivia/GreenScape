# Informe Técnico: Proyecto GreenScape

## Conversaciones en Comentarios

La implementación de conversaciones jerárquicas en comentarios adoptó un modelo mixto que combina MySQL para datos transaccionales y Neo4j para relaciones sociales. Esta decisión se fundamentó en las fortalezas complementarias de ambas tecnologías: MySQL ofrece consistencia ACID para transacciones, mientras que Neo4j proporciona mejor rendimiento en recorrido de grafos y consultas jerárquicas. Este modelo permite evoluconar gradualmente sin comprometer la estabilidad del sistema existente.

## Sistema de Documentación Jerárquica

Para el sistema de documentación jerárquica de plantas se seleccionó MongoDB como solución principal. Esta decisión se basó en la naturaleza variable de los documentos (PDF, JSON, MD) y su estructura jerárquica natural. MongoDB permite almacenar documentos anidados de forma nativa, facilitando la representación de relaciones principal-secundario. La flexibilidad esquemática de MongoDB es óptimo para un sistema donde los tipos de documentos pueden evolucionar sin migraciones costosas, mientras que su capacidad de consulta sobre documentos jerárquicos satisface el requisito de recuperación organizada.

## Restricciones Técnicas Cumplidas

El proyecto cumplió estrictamente con todas las restricciones técnicas establecidas. Se evitó completamente el uso de ORMs, implementando todas las operaciones de base de datos mediante SQL explícito con mysql-connector-python. La aplicación Streamlit interactúa directamente con los sistemas de almacenamiento mediante sus respectivos drivers nativos, manteniendo separación clara entre lógica de presentación y operaciones de datos.
