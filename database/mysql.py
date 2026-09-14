import mysql.connector

from config.settings import MYSQL_CONFIG



def get_connection():

    return mysql.connector.connect(
        **MYSQL_CONFIG
    )