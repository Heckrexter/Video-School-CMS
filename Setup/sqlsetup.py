import mysql.connector
import bcrypt
import envfile
host = envfile.host
username = envfile.dbuser
password = envfile.dbpass
dbname = envfile.dbname

def hash_password(password):
    password = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password, salt)
    return hashed.decode('utf-8')

sqlcommands = [
    "DROP DATABASE IF EXISTS {}".format(dbname),
    # create database if not exists
    "CREATE DATABASE {}".format(dbname),
    # user the database
    "USE  {}".format(dbname),
    # create user table if it doesn't exists
    "CREATE TABLE User (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255) NOT NULL,email VARCHAR(255) UNIQUE NOT NULL, password VARCHAR(255) NOT NULL, role TINYINT NOT NULL DEFAULT 0, status TINYINT NOT NULL DEFAULT 0)",
    # add default admin user
    f"INSERT INTO User (name, email, password, role, status) VALUES ('root user','root@root.com', '{hash_password('root')}', 0, 0)",
    ## DEBUGGING ONLY
    f"INSERT INTO User (name, email, password, role, status) VALUES ('manager user','manager@root.com', '{hash_password('root')}', 1, 0)",
    f"INSERT INTO User (name, email, password, role, status) VALUES ('manager2 user','manager2@root.com', '{hash_password('root')}', 1, 0)",
    f"INSERT INTO User (name, email, password, role, status) VALUES ('manager3 user','manager3@root.com', '{hash_password('root')}', 1, 0)",
    f"INSERT INTO User (name, email, password, role, status) VALUES ('ops user','ops@root.com', '{hash_password('root')}', 2, 0)",
    f"INSERT INTO User (name, email, password, role, status) VALUES ('ops2 user','ops2@root.com', '{hash_password('root')}', 2, 0)",
    f"INSERT INTO User (name, email, password, role, status) VALUES ('ops3 user','ops3@root.com', '{hash_password('root')}', 2, 0)",
    f"INSERT INTO User (name, email, password, role, status) VALUES ('editor user','editor@root.com', '{hash_password('root')}', 3, 0)",
    f"INSERT INTO User (name, email, password, role, status) VALUES ('editor2 user','editor2@root.com', '{hash_password('root')}', 3, 0)",
    f"INSERT INTO User (name, email, password, role, status) VALUES ('editor3 user','editor3@root.com', '{hash_password('root')}', 3, 0)",
    f"INSERT INTO User (name, email, password, role, status) VALUES ('creator user','creator@root.com', '{hash_password('root')}', 4, 0)",
    f"INSERT INTO User (name, email, password, role, status) VALUES ('creator2 user','creator2@root.com', '{hash_password('root')}', 4, 0)",
    f"INSERT INTO User (name, email, password, role, status) VALUES ('creator3 user','creator3@root.com', '{hash_password('root')}', 4, 0)",
    # create channel table if it doesn't exists
    "CREATE TABLE Channel (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255) UNIQUE NOT NULL, platform TINYINT NOT NULL DEFAULT 0, creator_id INT, editor_id INT, manager_id INT, ops_id INT, status TINYINT NOT NULL DEFAULT 0, tokens JSON NOT NULL DEFAULT ('{}'))",

    # add two test channels
    ## DEBUGGING ONLY
    "INSERT INTO Channel (name, platform, creator_id, editor_id, manager_id, ops_id, status) VALUES ('testchannel1', 0, 11, 8, 2, 5, 0)",
    "INSERT INTO Channel (name, platform, creator_id, editor_id, manager_id, ops_id, status) VALUES ('testchannel2', 0, 11, 8, 2, 5, 0)",
    # create video table if it doesn't exists
    ## ADD URL TO VIDEO TABLE
    "CREATE TABLE Video (id INT AUTO_INCREMENT PRIMARY KEY, old_id VARCHAR(6) UNIQUE, title VARCHAR(255) UNIQUE NOT NULL, url VARCHAR(255),channel_id INT NOT NULL, shoot_timestamp INT, edit_timestamp INT, upload_timestamp INT, status TINYINT NOT NULL DEFAULT 0, comment LONGTEXT DEFAULT NULL)",
    # create log_table table if it doesn't exists
    "CREATE TABLE Log_Table (id INT AUTO_INCREMENT PRIMARY KEY, type TINYINT NOT NULL DEFAULT 0, date INT NOT NULL, data JSON NOT NULL DEFAULT ('{}'))",
]

def mainB():
    dbconnect = mysql.connector.connect(
        host=host,
        user=username,
        password=password
    )
    cursor = dbconnect.cursor()
    for command in sqlcommands:
        print("Executing command: ", command)
        cursor.execute(command)

# mainB()