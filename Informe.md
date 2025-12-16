# Informe Técnico: Proyecto GreenScape

## 1. Introducción

El proyecto GreenScape tuvo como objetivo la recuperación y mejora de una plataforma de red social para entusiastas de plantas mediante análisis de datos e ingeniería inversa. Se desarrolló un sistema integral que abarca desde consultas analíticas complejas hasta una aplicación web completa, cumpliendo con todas las especificaciones técnicas establecidas.

## 2. Modelo Entidad-Relación Extendido

Para el modelo entidad-relación se utilizó Excalidraw y luego draw.io para su construcción, priorizando la claridad conceptual.

## 3. Consultas SQL Analíticas

Las consultas SQL implementadas siguieron un enfoque pragmático que balanceó complejidad y rendimiento. Se priorizó el uso de joins estratégicos sobre CTEs complejas, reservando estas últimas solo para casos donde la recursividad era estrictamente necesaria.

## 4. Conversaciones en Comentarios

La implementación de conversaciones jerárquicas en comentarios adoptó un modelo mixto que combina MySQL para datos transaccionales y Neo4j para relaciones sociales. Esta decisión se fundamentó en las fortalezas complementarias de ambas tecnologías: MySQL ofrece consistencia ACID para operaciones críticas, mientras que Neo4j proporciona mejor rendimiento en recorrido de grafos y consultas jerárquicas. Este modelo permite evoluconar gradualmente sin comprometer la estabilidad del sistema existente.

## 5. Sistema de Documentación Jerárquica

Para el sistema de documentación jerárquica de plantas se seleccionó MongoDB como solución principal. Esta decisión se basó en la naturaleza variable de los documentos (PDF, JSON, MD) y su estructura jerárquica natural. MongoDB permite almacenar documentos anidados de forma nativa, facilitando la representación de relaciones principal-secundario. La flexibilidad esquemática de MongoDB es óptimo para un sistema donde los tipos de documentos pueden evolucionar sin migraciones costosas, mientras que su capacidad de consulta sobre documentos jerárquicos satisface el requisito de recuperación organizada.

## 6. Aplicación Web Streamlit

La aplicación web se desarrolló en Streamlit implementando un diseño modular con cinco secciones principales correspondientes a las funcionalidades requeridas. Se adoptó la estética Frutiger Aero mediante CSS personalizado, creando una experiencia de usuario coherente con la temática de jardinería. La aplicación interactúa directamente con la base de datos mediante consultas SQL explícitas, cumpliendo con las restricciones técnicas. Cada sección implementa manejo robusto de errores y validación de entradas, ofreciendo múltiples vistas de los datos adaptadas a diferentes necesidades analíticas.

## 7. Restricciones Técnicas Cumplidas

El proyecto cumplió estrictamente con todas las restricciones técnicas establecidas. Se evitó completamente el uso de ORMs, implementando todas las operaciones de base de datos mediante SQL explícito con mysql-connector-python. La aplicación Streamlit interactúa directamente con los sistemas de almacenamiento mediante sus respectivos drivers nativos, manteniendo separación clara entre lógica de presentación y operaciones de datos.

## 8. Conclusiones

## Conclusiones

El proyecto GreenScape demostró la viabilidad de recuperar sistemas existentes mediante ingeniería inversa y mejoras técnicas focalizadas. Se implementó un modelo híbrido que combina MySQL con Neo4j para conversaciones, aprovechando las fortalezas de cada tecnología: consistencia transaccional y eficiencia en relaciones sociales. Para la documentación jerárquica se adoptó MongoDB, cuya flexibilidad esquemática se alinea perfectamente con la naturaleza variable de los documentos botánicos.

La aplicación Streamlit resultante integra todas las funcionalidades analíticas en una interfaz coherente, cumpliendo estrictamente con las restricciones técnicas de uso directo de SQL. Las decisiones arquitectónicas tomadas establecen bases sólidas para la evolución futura de la plataforma, balanceando estabilidad inmediata con preparación para el crecimiento escalable.
