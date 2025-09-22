import mysql.connector

# Database information needed for connection
dataBase = mysql.connector.connect(
    host = 'localhost',
    user = 'root',
    passwd = 'password'
)

# Create cursor object
cursorObject = dataBase.cursor()

# Create a database
cursorObject.execute("CREATE DATABASE calender")

print("Created Database")

