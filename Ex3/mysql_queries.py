queries = {
    "a": """
        SELECT * FROM Producto
        """,
    "b": """
        SELECT
            usu.Nombre AS Nombre_Autor,
            pub.Texto,
            pub.IDPub,
            COUNT(rcc.IDU) AS Cantidad_Reacciones
        FROM Publicacion pub
        JOIN Usuario usu ON pub.IDU = usu.IDU
        LEFT JOIN Reaccionar rcc ON pub.IDPub = rcc.IDPub
        GROUP BY pub.IDPub, usu.Nombre, pub.Texto
        ORDER BY Cantidad_Reacciones DESC
        """,
    "c": """
        SELECT
            plt.Categoria,
            COUNT(*) AS Total_Reacciones_Positivas
        FROM Gustar gus
        JOIN Planta plt ON gus.IDProd = plt.IDProd
        GROUP BY plt.Categoria
        ORDER BY Total_Reacciones_Positivas DESC
        LIMIT 3
        """,
    "d": """
        SELECT
            usu.IDU,
            usu.Nombre,
            usu.Email,
            usu.DireccionParticular,
            MAX(GREATEST(
                COALESCE(rcc.Fecha, '0000-00-00'),
                COALESCE(con.Fecha, '0000-00-00')
            )) AS Ultima_Fecha_Actividad
        FROM Usuario usu
        LEFT JOIN Reaccionar rcc ON usu.IDU = rcc.IDU
            AND rcc.Fecha >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
        LEFT JOIN Contribucion con ON usu.IDU = con.IDU
            AND con.Fecha >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
        GROUP BY usu.IDU, usu.Nombre, usu.Email, usu.DireccionParticular
        HAVING Ultima_Fecha_Actividad > '0000-00-00'
        """,
    "e": """
        SELECT
            pub.IDPub,
            pub.Texto,
            usu.Nombre AS Nombre_Autor,
            COUNT(rcc.IDU) AS Total_Reacciones,
            SUM(CASE
                WHEN rcc.Tipo IN ('Me gusta', 'Me encanta', 'Me asombra', 'Me divierte')
                THEN 1 ELSE 0
            END) AS Positivas,
            SUM(CASE
                WHEN rcc.Tipo IN ('Me enoja', 'Me entristece')
                THEN 1 ELSE 0
            END) AS Negativas
        FROM Publicacion pub
        JOIN Usuario usu ON pub.IDU = usu.IDU
        LEFT JOIN Reaccionar rcc ON pub.IDPub = rcc.IDPub
        GROUP BY pub.IDPub, pub.Texto, usu.Nombre
        HAVING Positivas > Negativas
        ORDER BY Total_Reacciones DESC
        """,
    "f": """
        SELECT DISTINCT
            plt.NombreComun AS Planta
        FROM Planta plt
        JOIN Contribucion c1 ON plt.IDProd = c1.IDProd
        JOIN Contribucion c2 ON plt.IDProd = c2.IDProd
        WHERE PERIOD_DIFF(
            DATE_FORMAT(c1.Fecha, '%Y%m'),
            DATE_FORMAT(c2.Fecha, '%Y%m')
        ) = 1
        AND c1.Fecha <> c2.Fecha
        """,
    "g": """
        WITH UsuarioMultimedia AS (
            SELECT
                pub.IDU,
                DATE_FORMAT(rcc.Fecha, '%Y-%m') AS Mes,
                COUNT(DISTINCT CASE WHEN pub.IDV IS NOT NULL THEN pub.IDV END) AS Videos,
                COUNT(DISTINCT tf.IDF) AS Fotos
            FROM Publicacion pub
            LEFT JOIN Tener_Foto tf ON pub.IDPub = tf.IDPub
            LEFT JOIN Reaccionar rcc ON pub.IDPub = rcc.IDPub
            WHERE rcc.Fecha >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
            GROUP BY pub.IDU, DATE_FORMAT(rcc.Fecha, '%Y-%m')
        ),
        TopUsuarios AS (
            SELECT
                IDU,
                AVG(Videos + Fotos) AS Promedio_Multimedia_Mensual,
                RANK() OVER (ORDER BY SUM(Videos + Fotos) DESC) AS Ranking
            FROM UsuarioMultimedia
            GROUP BY IDU
        )
        SELECT
            usu.IDU,
            usu.Nombre,
            ROUND(tu.Promedio_Multimedia_Mensual, 2) AS Promedio_Actividad_Mensual
        FROM TopUsuarios tu
        JOIN Usuario usu ON tu.IDU = usu.IDU
        WHERE tu.Ranking <= 10
        ORDER BY tu.Ranking
        """,
    "h": """
        WITH UsuariosEdad AS (
            SELECT
                IDU,
                TIMESTAMPDIFF(YEAR, FechaDeNacimiento, CURDATE()) AS Edad
            FROM Usuario
        )
        SELECT
            CASE
                WHEN Edad BETWEEN 0 AND 10 THEN '0-10'
                WHEN Edad BETWEEN 11 AND 20 THEN '11-20'
                WHEN Edad BETWEEN 21 AND 30 THEN '21-30'
                WHEN Edad BETWEEN 31 AND 40 THEN '31-40'
                WHEN Edad BETWEEN 41 AND 50 THEN '41-50'
                WHEN Edad BETWEEN 51 AND 60 THEN '51-60'
                WHEN Edad BETWEEN 61 AND 70 THEN '61-70'
                WHEN Edad BETWEEN 71 AND 80 THEN '71-80'
                WHEN Edad BETWEEN 81 AND 90 THEN '81-90'
                WHEN Edad BETWEEN 91 AND 100 THEN '91-100'
                ELSE '100+'
            END AS Rango_Edad,
            COUNT(*) AS Cantidad_Usuarios,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM Usuario), 2) AS Porcentaje
        FROM UsuariosEdad
        GROUP BY Rango_Edad
        ORDER BY MIN(Edad)
        """,
    "i": """
        WITH VentasMensuales AS (
            SELECT
                IDProd,
                DATE_FORMAT(Fecha, '%Y-%m') AS Mes,
                SUM(Cantidad) AS Total_Ventas
            FROM Compra
            WHERE Fecha >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
            GROUP BY IDProd, DATE_FORMAT(Fecha, '%Y-%m')
        ),
        Comparacion AS (
            SELECT
                IDProd,
                Mes,
                Total_Ventas,
                LAG(Total_Ventas) OVER (
                    PARTITION BY IDProd
                    ORDER BY Mes
                ) AS Ventas_Mes_Anterior
            FROM VentasMensuales
        ),
        ProductosConIncremento AS (
            SELECT DISTINCT IDProd
            FROM Comparacion
            WHERE Ventas_Mes_Anterior IS NOT NULL
                AND Total_Ventas > Ventas_Mes_Anterior
        )
        SELECT DISTINCT vm.IDProd, prod.Nombre
        FROM VentasMensuales vm
        JOIN Producto prod ON vm.IDProd = prod.IDProd
        WHERE vm.IDProd NOT IN (SELECT IDProd FROM ProductosConIncremento)
        """,
    "j": """
        WITH ContribucionesPorClima AS (
            SELECT
                p.IDC,
                c.IDProd,
                COUNT(*) AS Num_Contribuciones,
                ROW_NUMBER() OVER (
                    PARTITION BY p.IDC
                    ORDER BY COUNT(*) DESC
                ) AS Ranking
            FROM Contribucion c
            JOIN Planta p ON c.IDProd = p.IDProd
            GROUP BY p.IDC, c.IDProd
        )
        SELECT
            cli.Tipo AS Clima,
            plt.NombreComun AS Planta_Mas_Popular,
            cp.Num_Contribuciones
        FROM ContribucionesPorClima cp
        JOIN Planta plt ON cp.IDProd = plt.IDProd
        JOIN Clima cli ON cp.IDC = cli.IDC
        WHERE cp.Ranking = 1
        ORDER BY cli.Tipo
        """,
    "k": """
        WITH ContribucionesAnuales AS (
            SELECT
                c.IDU,
                YEAR(c.Fecha) AS Anio,
                p.Categoria,
                COUNT(*) AS Num_Contribuciones
            FROM Contribucion c
            JOIN Planta p ON c.IDProd = p.IDProd
            GROUP BY c.IDU, YEAR(c.Fecha), p.Categoria
        ),
        CategoriasRankeadas AS (
            SELECT
                IDU,
                Anio,
                Categoria,
                Num_Contribuciones,
                RANK() OVER (
                    PARTITION BY IDU, Anio
                    ORDER BY Num_Contribuciones DESC
                ) AS Posicion
            FROM ContribucionesAnuales
        ),
        CambiosCategoria AS (
            SELECT
                cr1.IDU,
                cr1.Anio AS Anio1,
                cr1.Categoria AS Categoria1,
                cr2.Anio AS Anio2,
                cr2.Categoria AS Categoria2
            FROM CategoriasRankeadas cr1
            JOIN CategoriasRankeadas cr2
                ON cr1.IDU = cr2.IDU
                AND cr1.Anio = cr2.Anio - 1
            WHERE cr1.Posicion = 1
                AND cr2.Posicion = 1
                AND cr1.Categoria <> cr2.Categoria
        )
        SELECT
            cc.IDU,
            usu.Nombre,
            cc.Anio1,
            cc.Categoria1,
            cc.Anio2,
            cc.Categoria2
        FROM CambiosCategoria cc
        JOIN Usuario usu ON cc.IDU = usu.IDU
        """,
    "l": """
        WITH ComprasAnalizadas AS (
            SELECT
                com.IDUC AS IDU,
                com.IDProd,
                CASE
                    WHEN gus.IDProd IS NOT NULL THEN 1
                    ELSE 0
                END AS Gustada
            FROM Compra com
            LEFT JOIN Gustar gus
                ON com.IDUC = gus.IDU
                AND com.IDProd = gus.IDProd
        ),
        ResumenCompras AS (
            SELECT
                IDU,
                SUM(Gustada) AS Compras_Gustadas,
                SUM(CASE WHEN Gustada = 0 THEN 1 ELSE 0 END) AS Compras_No_Gustadas
            FROM ComprasAnalizadas
            GROUP BY IDU
        )
        SELECT
            usu.IDU,
            usu.Nombre,
            rc.Compras_Gustadas,
            rc.Compras_No_Gustadas
        FROM ResumenCompras rc
        JOIN Usuario usu ON rc.IDU = usu.IDU
        WHERE rc.Compras_No_Gustadas > rc.Compras_Gustadas
        ORDER BY rc.Compras_No_Gustadas DESC
        """,
    "m": """
        SELECT
            usu.IDU,
            usu.Nombre,
            usu.Email
        FROM Usuario usu
        WHERE NOT EXISTS (
            SELECT 1
            FROM Publicacion pub
            WHERE pub.IDU = usu.IDU
                AND (pub.IDV IS NOT NULL
                     OR EXISTS (
                         SELECT 1
                         FROM Tener_Foto tf
                         WHERE tf.IDPub = pub.IDPub
                     )
                )
        )
        ORDER BY usu.IDU
        """,
    "n": """
        SELECT
            usu.IDU AS ID_Vendedor,
            usu.Nombre AS Nombre_Vendedor,
            usu.Email,
            usu.DireccionParticular,
            COUNT(DISTINCT com.IDProd) AS Total_Productos_Vendidos,
            ROUND(AVG(com.Puntuacion), 2) AS Calificacion_Promedio,
            SUM(com.Cantidad) AS Unidades_Vendidas
        FROM Compra com
        JOIN Usuario usu ON com.IDUV = usu.IDU
        WHERE com.Puntuacion IS NOT NULL
        GROUP BY usu.IDU, usu.Nombre, usu.Email, usu.DireccionParticular
        ORDER BY Calificacion_Promedio DESC
        LIMIT 5
        """,
}


columns = {
    "a": ["IDProd", "Nombre", "Descripcion", "Precio"],
    "b": ["Nombre_Autor", "Texto", "IDPub", "Cantidad_Reacciones"],
    "c": ["Categoria", "Total_Reacciones_Positivas"],
    "d": ["IDU", "Nombre", "Email", "DireccionParticular", "Ultima_Fecha_Actividad"],
    "e": [
        "IDPub",
        "Texto",
        "Nombre_Autor",
        "Total_Reacciones",
        "Positivas",
        "Negativas",
    ],
    "f": ["Planta"],
    "g": ["IDU", "Nombre", "Promedio_Actividad_Mensual"],
    "h": ["Rango_Edad", "Cantidad_Usuarios", "Porcentaje"],
    "i": ["IDProd", "Nombre"],
    "j": ["Clima", "Planta_Mas_Popular", "Num_Contribuciones"],
    "k": ["IDU", "Nombre", "Anio1", "Categoria1", "Anio2", "Categoria2"],
    "l": ["IDU", "Nombre", "Compras_Gustadas", "Compras_No_Gustadas"],
    "m": ["IDU", "Nombre", "Email"],
    "n": [
        "ID_Vendedor",
        "Nombre_Vendedor",
        "Email",
        "DireccionParticular",
        "Total_Productos_Vendidos",
        "Calificacion_Promedio",
        "Unidades_Vendidas",
    ],
}
