import psycopg2
import os

def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="sandy_lab",
        user="sandy",
        password="sandy123",
        port=5433
    )