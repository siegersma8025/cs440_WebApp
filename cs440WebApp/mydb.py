# Used to create a mySQL database, already ran so do not need to run/use this file again

import mysql.connector

# Database information needed for connection
dataBase = mysql.connector.connect(
    host = '138.49.184.177',
    user = 'Group3',
    passwd = 'Gr0upThree@Dmin2025$'
)

# Create cursor object
cursorObject = dataBase.cursor()

# Create a database
cursorObject.execute("CREATE DATABASE calender")

print("Created Database")

