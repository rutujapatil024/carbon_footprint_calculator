# db_config.py
import mysql.connector

def get_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",          
            password="@Rutuja0422@",    
            database="carbon_footprint"
        )
        return conn
    except mysql.connector.Error as err:
        print("MySQL Error:", err)
        return None
