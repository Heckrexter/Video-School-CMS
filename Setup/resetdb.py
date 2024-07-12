import mysql.connector
import sqlsetup
import envfile

host = envfile.host
username = envfile.dbuser
password = envfile.dbpass
dbname = envfile.dbname

# Connect to database
dbconnect = mysql.connector.connect(
    host=host,
    user=username,
    password=password
)
cursor = dbconnect.cursor()

# Drop database
cursor.execute(f"DROP DATABASE IF EXISTS {dbname}")
cursor.close()
dbconnect.close()
print("Database deleted")

# Recreate database
sqlsetup.mainB()