queries = {
    "a": "SELECT * FROM Producto",
    "b": """
        SELECT
            usu.nombre,
            pub.texto,
            COUNT(*) AS cantidad_de_reacciones
        FROM Reaccionar rcc
        JOIN Publicacion pub ON rcc.idpub = pub.idpub
        JOIN Usuario usu ON pub.idu = usu.idu
        GROUP BY rcc.idpub, pub.texto, usu.nombre
        """,
    "c": """
        SELECT
            gus.idprod,
            COUNT(*) AS likes
        FROM Gustar gus
        GROUP BY gus.idprod
        """,
    "d": """
        SELECT
            usu.idu,
            usu.nombre,
            usu.direccionparticular,
            MAX(
                CASE
                    WHEN rcc.fecha >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
                         OR ctr.fecha >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
                    THEN GREATEST(COALESCE(rcc.fecha, '1223-01-01'), COALESCE(ctr.fecha, '1223-01-01'))
                    ELSE NULL
                END
            ) AS fecha
        FROM Usuario usu
        LEFT JOIN Reaccionar rcc ON usu.idu = rcc.idu
        LEFT JOIN Contribucion ctr ON usu.idu = ctr.idu
        GROUP BY usu.idu
        """,
    "e": """
        SELECT
            pub.*,
            COUNT(rcc.idu)
        FROM Publicacion pub
        JOIN Reaccionar rcc ON pub.idpub = rcc.idpub
        GROUP BY pub.idpub
        HAVING
            COUNT(CASE WHEN rcc.tipo IN ('me encanta', 'me gusta', 'me asombra', 'me divierte') THEN 1 END) >
            COUNT(CASE WHEN rcc.tipo IN ('me enoja', 'me entristece') THEN 1 END)
        """,
    "f": """
        SELECT
            plt.nombrecomun
        FROM Planta plt
        JOIN Contribucion AS ctr ON plt.idprod = ctr.idprod
        JOIN Contribucion AS octr ON octr.idu = ctr.idu
        WHERE (
            DATE_FORMAT(ctr.fecha, '%y-%m-01') = DATE_ADD(DATE_FORMAT(octr.fecha, '%y-%m-01'), INTERVAL 1 MONTH)
            OR DATE_FORMAT(octr.fecha, '%y-%m-01') = DATE_ADD(DATE_FORMAT(ctr.fecha, '%y-%m-01'), INTERVAL 1 MONTH)
        )
        AND ctr.idprod = octr.idprod
        """,
    "g": "",
    "h": """
        SELECT
            CASE
                WHEN YEAR(CURDATE()) - YEAR(usu.fechadenacimiento) < 11 THEN 'wtf'
                WHEN YEAR(CURDATE()) - YEAR(usu.fechadenacimiento) BETWEEN 11 AND 20 THEN '11-20'
                WHEN YEAR(CURDATE()) - YEAR(usu.fechadenacimiento) BETWEEN 21 AND 30 THEN '21-30'
                WHEN YEAR(CURDATE()) - YEAR(usu.fechadenacimiento) BETWEEN 31 AND 40 THEN '31-40'
                WHEN YEAR(CURDATE()) - YEAR(usu.fechadenacimiento) BETWEEN 41 AND 50 THEN '41-50'
                WHEN YEAR(CURDATE()) - YEAR(usu.fechadenacimiento) BETWEEN 51 AND 60 THEN '51-60'
                WHEN YEAR(CURDATE()) - YEAR(usu.fechadenacimiento) BETWEEN 61 AND 70 THEN '61-70'
                WHEN YEAR(CURDATE()) - YEAR(usu.fechadenacimiento) BETWEEN 71 AND 80 THEN '71-80'
                WHEN YEAR(CURDATE()) - YEAR(usu.fechadenacimiento) BETWEEN 81 AND 90 THEN '81-90'
                WHEN YEAR(CURDATE()) - YEAR(usu.fechadenacimiento) BETWEEN 91 AND 100 THEN '91-100'
                WHEN YEAR(CURDATE()) - YEAR(usu.fechadenacimiento) > 100 THEN 'en mis tiempos...'
                ELSE 'revisate eso'
            END AS rango_de_edad,
            COUNT(*) AS cant_de_usuarios,
            (COUNT(*) * 100 / (SELECT COUNT(*) FROM Usuario)) AS por_ciento
        FROM Usuario usu
        GROUP BY rango_de_edad
        ORDER BY rango_de_edad
        """,
    "i": """
        SELECT
            com.idprod
        FROM Compra com
        JOIN Compra com2 ON com.idprod = com2.idprod
            AND (DATE_FORMAT(com.fecha, '%y-%m') <> DATE_FORMAT(com2.fecha, '%y-%m') OR com.iduv <> com2.iduv)
        WHERE com.fecha BETWEEN DATE_SUB(CURDATE(), INTERVAL 1 YEAR) AND CURDATE()
            AND com2.fecha BETWEEN DATE_SUB(CURDATE(), INTERVAL 1 YEAR) AND CURDATE()
        GROUP BY com.idprod
        HAVING COUNT(*) = SUM(
            CASE
                WHEN DATE_FORMAT(com.fecha, '%y-%m') > DATE_FORMAT(com2.fecha, '%y-%m')
                    AND com.cantidad > com2.cantidad
                THEN 0
                ELSE 1
            END
        )
        """,
    "j": "",
    "k": "",
    "l": """
        SELECT
            CASE
                WHEN SUM(CASE WHEN com.idprod = plt.idprod AND com.idprod = gus.idprod THEN 1 ELSE 0 END) <
                     SUM(CASE WHEN com.idprod = plt.idprod AND com.idprod <> gus.idprod THEN 1 ELSE 0 END)
                THEN usu.idu
            END AS raritos
        FROM Usuario usu
        JOIN Gustar gus ON gus.idu = usu.idu
        JOIN Compra com ON com.iduc = usu.idu
        JOIN Planta plt ON plt.idprod = com.idprod
        GROUP BY usu.idu
        ORDER BY usu.idu
        """,
    "m": """
        SELECT
            usu.idu
        FROM Usuario usu
        WHERE usu.idu NOT IN (
            SELECT DISTINCT pub.idu
            FROM Publicacion pub
            LEFT JOIN Tener_Foto tf ON tf.idpub = pub.idpub
            WHERE tf.idf OR pub.idv
        )
        ORDER BY usu.idu
        """,
    "n": "",
    "ñ": "",
    "o": "",
    "p": """
        SELECT
            pub.idu,
            AVG((rcc.peso + com.cant * 2) / (rcc.cant + com.cant)) AS puntaje_de_interacciones
        FROM Publicacion pub
        LEFT JOIN (
            SELECT
                rcc.idpub,
                COALESCE(SUM(
                    CASE
                        WHEN rcc.tipo = 'me gusta' THEN 1
                        WHEN rcc.tipo = 'me encanta' THEN 2
                        WHEN rcc.tipo = 'me asombra' THEN 1.5
                    END
                ), 0) AS peso,
                COALESCE(SUM(CASE WHEN rcc.tipo IN ('me gusta', 'me encanta', 'me asombra') THEN 1 END), 0) AS cant
            FROM Reaccionar rcc
            GROUP BY rcc.idpub
        ) rcc ON pub.idpub = rcc.idpub
        LEFT JOIN (
            SELECT
                com.idpub,
                COALESCE(SUM(CASE WHEN com.comentario IS NOT NULL THEN 1 ELSE 0 END), 0) AS cant
            FROM Comentar com
            GROUP BY com.idpub
        ) com ON com.idpub = pub.idpub
        GROUP BY pub.idu
        ORDER BY puntaje_de_interacciones DESC
        LIMIT 5
        """,
    "q": "",
}
columns = {
    "a": [],
    "b": [],
    "c": [],
    "d": [],
    "e": [],
    "f": [],
    "g": [],
    "h": [],
    "i": [],
    "j": [],
    "k": [],
    "l": [],
    "m": [],
    "n": [],
    "ñ": [],
    "o": [],
    "p": [],
    "q": [],
}
