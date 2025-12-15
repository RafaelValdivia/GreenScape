import mysql.connector as mq

connection_dict = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "root",
    "database": "GreenScape",
    "auth_plugin": "mysql_native_password",
}

if __name__ == "__main__":
    import pandas as pd

    connection = mq.connect(**connection_dict)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Comentar")
    result = cursor.fetchall()
    print(pd.DataFrame(result))
