import mysql.connector
import logging
from flask import jsonify 
# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def connect_to_mysql():
    try:
        connection = mysql.connector.connect(
            host = 'localhost',
            user='root',
            port='5435',
            password='1234',
            database='task1'
        )
        return connection
    except mysql.connector.Error as err:
        logger.error(f"Error connecting to mysql : {err}")
        return jsonify({"detail": "Error in connect to mysql"}), 500