import ast
import json
import bcrypt
import mysql.connector
import time
import api_functions as api_functions
import extrafunc
from genlogenum import log_type

from rep_var import *

class VidSchool:
    # constructor function
    def __init__(self, dbhost, dbusername, dbpassword, dbname):
        print("Object initialized NOW")
        self.db_controller = Db_operator(dbhost, dbusername, dbpassword, dbname)
        VidSchool.credentialpool = {}
        VidSchool.start_credential_pool(self)
    
    # destructor function
    def __del__(self):
        if self.dbconnect.is_connected():
            self.dbconnect.close()
            print("Disconnected from database")

    # hashing and salting password for security with bcrypt library
    def hash_password(self, password):
        password = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password, salt)
        return hashed.decode('utf-8')

    # Setup the database with the proper schema
    def setupdb(self):
        for command in self.sqlcommands:
            self.cursor.execute(command)
            self.dbconnect.commit()
        print("Setup complete")

    @staticmethod
    def start_credential_pool(self):
        sql = "SELECT * FROM Channel WHERE JSON_LENGTH(tokens) > 0;"
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        # add credentials to credential pool
        if result == []:
            print("No channels found")
            VidSchool.credentialpool = {}
            return False
        for i in list(result):
            cred = [i[8]]
            cred = ast.literal_eval(cred[0])
            VidSchool.credentialpool[i[0]] = cred
        print("Credential pool started")

        # # Refresh all access tokens
        for i in VidSchool.credentialpool:
            oldcred = VidSchool.credentialpool[i]
            # oldcred = ast.literal_eval(oldcred)
            VidSchool.credentialpool[i] = api_functions.refresh_token(oldcred)
        print("Credential pool refreshed")

    @staticmethod
    def check_credential_pool():
        for i in VidSchool.credentialpool:
            if VidSchool.credentialpool[i][1] > time.time():
                cred = VidSchool.credentialpool[i][0]
                # cred = ast.literal_eval(cred)
                VidSchool.credentialpool[i] = api_functions.refresh_token(cred)
        return True

    @staticmethod
    def get_credentials(channel_id):
        VidSchool.check_credential_pool()
        if channel_id not in VidSchool.credentialpool:
            print("Channel not found")
            return False
        # cred = ast.literal_eval(VidSchool.credentialpool[channel_id][0])
        cred = VidSchool.credentialpool[channel_id][0]
        return cred

    ### USER FUNCTIONS
    # function to add a user to the database ONLY FOR ADMIN
    
    def add_user(self,request, author):
        if author['user_type'] == USER_TYPE_ADMIN:
            User = self.db_controller.AddToUser(request['user_name'], request['user_email'], self.hash_password(request['password']), int(request['user_type']), USER_ACTIVE)
            if User.__contains__("error"):
                return User
            log_data = {
                "action":'Add_User',
                "author_id": author['user_id'],
                "data": {
                    "user_id": User[0],
                    "user_name": User[1],
                    "user_email": User[2],
                    "user_type": User[4]
                }
            }
            self.log_action(LOG_USER, log_data)
            return True
        else:
            return "You do not have permission to add users"

    # sets user to INACTIVE
    def delete_user(self, user_id, author):
        if author['user_type'] == USER_TYPE_ADMIN:
            print('new delete user function')
            user = self.db_controller.GetUser(user_id)
            if user[4] == USER_TYPE_ADMIN:
                return "You cannot delete the admin user"
            result = self.db_controller.UpdateUser(user[0], user[1], user[2], user[4], USER_INACTIVE)
            if result == True:
                log_data = {
                    "action": "Delete_User",
                    "author_id": author['user_id'],
                    "data":{
                        "user_id": user[0],
                        "user_name": user[1],
                        "user_email": user[2],
                    }
                }
                self.log_action(LOG_USER, log_data)
                return True
            else:
                return result
        else:
            return "You do not have permission to delete this user"


    def olddelete_user( self, user_id, author):
        # checks permissions
        if author['user_type'] == USER_TYPE_ADMIN:
            user = self.get_user(user_id)
            if user[4] == 0:
                return "You cannot delete the admin user"
            # executes SQL command
            sql = "UPDATE User SET status = 1 WHERE ID = %s"
            val = (user_id,)
            self.cursor.execute(sql, val)
            self.dbconnect.commit()
            # Logging
            log_data = {
                "action": "delete_user",
                "author_id": author['user_id'],
                "data" : {
                    "user_id": user_id
                }
            }
            self.log_action(1, log_data)
            return True
        else:
            return "You do not have permission to delete this user"


    # function to get all users in the database
    # NEW
    def get_users(self, author):
        if author['user_type'] == USER_TYPE_ADMIN:
            Users = self.db_controller.GetUsers()
            return Users
        else:
            return "You do not have permission to view this data"
    
    def get_users_by_role(self, user_type):
        Users = self.db_controller.GetUsers()
        role_users = []
        for user in Users:
            if user[4] == user_type:
                role_users.append(user)
        return role_users

    def get_user(self, user_id):
        User = self.db_controller.GetUser(user_id)
        return User

    # function to get a specific user from the database
    def oldget_user(self, user_id):
        # executes SQL command
        sql = "SELECT * FROM User WHERE ID = %s"
        val = (user_id,)
        self.cursor.execute(sql, val)
        result = self.cursor.fetchone()
        return result
    
    # function to edit a user in the database
    def edit_user(self, request, author):
        # checks permissions
        if author['user_type'] == USER_TYPE_ADMIN:
            # stores default values from DB
            user_id = int(request['user_id'])
            if user_id == 0:
                return "You cannot edit the admin user"
            user_name = request['user_name']
            user_email = request['user_email']
            user_type = int(request['user_type'])
            status = int(request['status'])
            defvalue = self.get_user(user_id)
            # sets values to default if None
            user_name = user_name if user_name != "" else defvalue[1]
            user_email = user_email if user_email != "" else defvalue[2]
            user_type = user_type if user_type != "" else defvalue[4]
            status = status if status != "" else defvalue[5]
            # executes SQL command
            sql = "UPDATE User SET name = %s, email = %s, role = %s, status = %s WHERE ID = %s"
            val = (user_name, user_email, user_type, status, user_id)
            self.cursor.execute(sql, val)
            self.dbconnect.commit()
            # Logging
            log_data = {
                "action": "edit_user",
                "author_id": author['user_id'],
                "data": {
                    "user_id": user_id,
                    "user_email": user_email,
                    "user_type": user_type
                }
            }
            self.log_action(1, log_data)
            return True
        else:
            return {
                "error": "You do not have permission to edit this user"
            }

    ### VIDEO FUNCTIONS
    # function to add a video to the database
    def add_video(self, request, author):
        # checks user is higher permissions than ops
        video_title = request['video_title']
        channel_id = request['channel_id']
        if author['user_type'] <= 2 or author['user_type'] == 4:
            # executes SQL command
            sql = "INSERT INTO Video (title, channel_id, status) VALUES (%s, %s, 0)"
            val = (video_title, channel_id,)
            self.cursor.execute(sql, val)
            self.dbconnect.commit()
            # Logging
            log_data = {
                "action": "add_video",
                "author_id": author['user_id'],
                "data": {
                    "video_title": video_title,
                    "channel_id": channel_id,
                }
            }
            self.log_action(3, log_data)
            return True
        else:
            return {
                "error": "You do not have permission to add videos"
            }

    def add_videos_bulk(self, videos, channel_id, author):
        if author['user_type'] == USER_TYPE_ADMIN:
            for video in videos:
                sql = "INSERT INTO Video (old_id, title, url, channel_id, shoot_timestamp, edit_timestamp, upload_timestamp, status, comment) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                val = (video[0], video[1], video[2], channel_id, video[3], video[4], video[5], video[6], video[7])
                self.cursor.execute(sql, val)
                self.dbconnect.commit()
            log_data = {
                "action": "add_videos_bulk",
                "author_id": author['user_id'],
                "data": {
                    "numebr_of_videos": len(videos)-1,
                    "channel_id": channel_id
                }
            }

    # function to update a video in the database
    def update_video(self, request, author):
        if author['user_type'] <= 2 or author['user_type'] == 4:
            # stores values from DB as default
            video_id = int(request['video_id']) 
            video_title = request['video_title']
            video_url = request['video_url']
            channel_id = int(request['channel_id'])
            shoot_timestamp = request['shoot_timestamp']
            edit_timestamp = request['edit_timestamp']
            upload_timestamp = request['upload_timestamp']
            status = int(request['status'])
            comment = request['comment']
            
            defvalue = self.get_video(video_id)
            # if value is None, set to default value
            video_title = video_title if video_title != '' else defvalue[2]
            video_url = video_url if video_url != '' else defvalue[3]
            channel_id = channel_id if channel_id != '' else defvalue[4]
            shoot_timestamp = shoot_timestamp if shoot_timestamp != '' else defvalue[5]
            edit_timestamp = edit_timestamp if edit_timestamp != '' else defvalue[6]
            upload_timestamp = upload_timestamp if upload_timestamp != '' else defvalue[7]
            status = status if status != '' else defvalue[8]
            comment = comment if comment != '' else defvalue[9]
            # executes SQL command
        # executes SQL command
            sql = "UPDATE Video SET title = %s, url = %s,channel_id = %s, shoot_timestamp = %s, edit_timestamp = %s, upload_timestamp = %s, status = %s, comment = %s WHERE id = %s"
            val = (video_title, video_url, channel_id, shoot_timestamp, edit_timestamp, upload_timestamp, status, comment, video_id)
            self.cursor.execute(sql, val)
            self.dbconnect.commit()
            # Logging
            log_data = {
                "action": "update_video",
                "author_id": author['user_id'],
                "data": {
                    "video_id": video_id,
                    "video_title": video_title,
                    "channel_id": channel_id,
                    "shoot_timestamp": shoot_timestamp,
                    "edit_timestamp": edit_timestamp,
                    "upload_timestamp": upload_timestamp,
                    "status": status
                }
            }
            self.log_action(3, log_data)
            return True
        else:
            return {
                "error": "You do not have permission to update this video"
            }

    # function to set the status of a video
    def set_video_status(self, request, author):
        video_id = int(request['video_id'])
        status = int(request["status"])
        comment = request['comment']
        # checks if comment is set
        if comment == '':
            comment = None
        # checks different usertypes to check if action is permitted
        # creator
        print(author['user_type']," : ",status)
        if author['user_type'] == 4:
            if status != 1:
                return {
                    "error": "You do not have permission to set that status"
                }
        # editor
        elif author['user_type'] == 3:
            if status != 2:
                return {
                    "error": "You do not have permission to set that status"
                }
        # operations
        elif author['user_type'] == 2:
            if status != 3 and status != 4 and status != 6:
                return {
                    "error": "You do not have permission to set that status"
                }
        elif author['user_type'] == 1 or author['user_type'] == USER_TYPE_ADMIN:
            print("Manager or Admin")
        else:
            # return if invalid author
            return {
                "error": "INVALID AUTHOR"
            }
        # executes SQL command
        sql = "UPDATE Video SET status = %s, comment = %s WHERE ID = %s"
        # executes SQL command
        val = (status, comment, video_id,)
        self.cursor.execute(sql, val)
        self.dbconnect.commit()
        # Logging
        log_data = {
            "action": "set_video_status",
            "author_id": author['user_id'],
            "data": {
                "video_id": video_id,
                "status": status
            }
        }
        self.log_action(3, log_data)
        return True
    
    # function to delete a video from the database
    def set_delete_video(self, video_id, author):
        # checks that user is higher than ops
        if author['user_type'] <=2:
            # executes SQL command
            sql = "UPDATE Video SET status = 7 WHERE ID = %s"
            val = (video_id,)
            self.cursor.execute(sql, val)
            self.dbconnect.commit()
            # Logging
            log_data = {
                "action": "delete_video",
                "author_id": author['user_id'],
                "data": {
                    "video_id": video_id
                }
            }
            self.log_action(3, log_data)
            return True
        else:
            return {
                "error": "You do not have permission to delete this video"
            }
    # function to get all videos from the database
    def get_videos(self):
        # executes SQL command
        sql = "SELECT * FROM Video"
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        return result
    
    # function to get videos assigned to a user
    def get_videos_by_user(self, user_id, user_type):
        # creator
        if user_type == USER_TYPE_CREATOR:
            # executes SQL command
            sql = "SELECT ID FROM Channel WHERE creator_id = %s"
            val = (user_id,)
            self.cursor.execute(sql, val)
            Channels = self.cursor.fetchall()
            if Channels == []:
                return False
        # editor
        elif user_type == USER_TYPE_EDITOR:
            # executes SQL command
            sql = "SELECT ID FROM Channel WHERE editor_id = %s"
            val = (user_id,)
            self.cursor.execute(sql, val)
            Channels = self.cursor.fetchall()
            if Channels == []:
                return False
        # operations
        elif user_type == USER_TYPE_OPS:
            # executes SQL command
            sql = "SELECT ID FROM Channel WHERE ops_id = %s"
            val = (user_id,)
            self.cursor.execute(sql, val)
            Channels = self.cursor.fetchall()
            if Channels == []:
                return False
        elif user_type == USER_TYPE_MANAGER:
            # executes SQL command
            sql = "SELECT ID FROM Channel WHERE manager_id = %s"
            val = (user_id,)
            self.cursor.execute(sql, val)
            Channels = self.cursor.fetchall()
            if Channels == []:
                return False
            print("channels:-")
            print(Channels)
        else:
            return {
                "error": "INVALID USER TYPE"
            }
        Videos = []
        for i in Channels:
            sql = "SELECT * FROM Video WHERE channel_id = %s"
            val = (i[0],)
            self.cursor.execute(sql, val)
            result = self.cursor.fetchall()
            if result != []:
                Videos+=result
        return Videos

    def set_video_uploaded(self, video_id, url,author):
        if author['user_type'] <= 2:
            sql = "UPDATE Video SET status = 3, url = %s WHERE ID = %s"
            val = (url, video_id)
            self.cursor.execute(sql, val)
            self.dbconnect.commit()
            log_data = {
                "action":"upload video",
                "author_id": author['user_id'],
                "data": {
                    "video_id": video_id,
                    "url": url
                }
            }
            self.log_action(3, log_data)
        else:
            return {
                "error": "You do not have permission to upload videos"
            }

    def get_relevant_videos(self, user_id,user_type):
        if user_type == USER_TYPE_CREATOR:
            sql = "SELECT * FROM Channel WHERE creator_id = %s"
            val = (user_id,)
            self.cursor.execute(sql, val)
            Channels = self.cursor.fetchall()
            if Channels == []:
                return False
            video = []
            for I in Channels:
                sql = "SELECT * FROM Video WHERE channel_id = %s AND (status = 0 OR status = 3)"
                val = (I[0],)
                self.cursor.execute(sql, val)
                result = self.cursor.fetchall()
                video.append(result)
        elif user_type == USER_TYPE_EDITOR:
            sql = "SELECT * FROM Channel WHERE editor_id = %s"
            val = (user_id,)
            self.cursor.execute(sql, val)
            Channels = self.cursor.fetchall()
            if Channels == []:
                return False
            video = []
            for I in Channels:
                sql = "SELECT * FROM Video WHERE channel_id = %s AND (status = 1 OR status = 4)"
                val = (I[0],)
                self.cursor.execute(sql, val)
                result = self.cursor.fetchall()
                video.append(result)
        elif user_type == USER_TYPE_OPS:
            sql = "SELECT * FROM Channel WHERE ops_id = %s"
            val = (user_id,)
            self.cursor.execute(sql, val)
            Channels = self.cursor.fetchall()
            if Channels == []:
                return False
            video = []
            for I in Channels:
                sql = "SELECT * FROM Video WHERE channel_id = %s AND status = 2"
                val = (I[0],)
                self.cursor.execute(sql, val)
                result = self.cursor.fetchall()
                video.append(result)

    # get videos by channel
    def get_videos_by_channel(self, channel_id):
        # executes SQL command
        sql = "SELECT * FROM Video WHERE channel_id = %s"
        val = (channel_id,)
        self.cursor.execute(sql, val)
        result = self.cursor.fetchall()
        return result

    # get video by role
    def get_videos(self, author):
        # creator
        if author['user_type'] == USER_TYPE_CREATOR:
            # executes SQL command
            sql = "SELECT * FROM Video WHERE status = 0 OR status = 3"
            self.cursor.execute(sql)
            result = self.cursor.fetchall()
            return result
        # editor
        elif author['user_type'] == USER_TYPE_EDITOR:
            # executes SQL command
            sql = "SELECT * FROM Video WHERE status = 1 OR status = 4"
            self.cursor.execute(sql)
            result = self.cursor.fetchall()
            return result
        # operations
        elif author['user_type'] == USER_TYPE_OPS:
            # executes SQL command
            sql = "SELECT * FROM Video WHERE status = 3"
            self.cursor.execute(sql)
            result = self.cursor.fetchall()
            return result
        # manager and admin
        elif author['user_type'] == USER_TYPE_MANAGER or author['user_type'] == USER_TYPE_ADMIN:
            # executes SQL command
            sql = "SELECT * FROM Video"
            self.cursor.execute(sql)
            result = self.cursor.fetchall()
            return result
        else:
            return {
                "error":"INVALID AUTHOR"
            }

    # function to get a specific video from the database
    def get_video(self, video_id):
        # executes SQL command
        sql = "SELECT * FROM Video WHERE ID = %s"
        val = (video_id,)
        self.cursor.execute(sql, val)
        result = self.cursor.fetchone()
        return result
    
    ### CHANNEL FUNCTIONS
    def add_channel(self, request, author):
        channel_name = request['channel_name']
        platform = request['platform']
        creator_id = request['creator_id']
        editor_id = request['editor_id']
        manager_id = request['manager_id']
        ops_id = request['ops_id']
        if author['user_type'] == USER_TYPE_ADMIN:
            # executes SQL command
            sql = "INSERT INTO Channel (name ,platform, creator_id, editor_id, manager_id, ops_id, status) VALUES (%s, %s, %s, %s, %s, %s, 0)"
            val = (channel_name, platform, creator_id, editor_id, manager_id, ops_id)
            self.cursor.execute(sql, val)
            self.dbconnect.commit()
            # gets channel ID after adding
            sql = "SELECT ID FROM Channel WHERE name = %s AND platform = %s"
            val = (channel_name, platform)
            self.cursor.execute(sql, val)
            channel = self.cursor.fetchone()
            channel_id = channel[0]
            # Logging
            log_data = {  
                "action": "add_channel",
                "author_id": author['user_id'],
                "data": {
                    "channel_id": channel_id,
                    "channel_name": channel_name,
                    "platform": platform
                }
            }
            self.log_action(2, log_data)
            return channel_id
        else:
            return "You do not have permission to add channels"

    # function get user channels
    def get_channels_by_user(self, user_id, user_type):
        # check usertype and set sql command
        if user_type == USER_TYPE_CREATOR:
            sql = "SELECT * FROM Channel WHERE creator_id = %s"
        elif user_type == USER_TYPE_EDITOR:
            sql = "SELECT * FROM Channel WHERE editor_id = %s"
        elif user_type == USER_TYPE_OPS:
            sql = "SELECT * FROM Channel WHERE ops_id = %s"
        elif user_type == USER_TYPE_MANAGER:
            sql = "SELECT * FROM Channel WHERE manager_id = %s"
        val = (user_id,)
        self.cursor.execute(sql, val)
        result = self.cursor.fetchall()
        return result

    # function to delete a channel from the database
    def delete_channel(self, channel_id, author):
        # checks if user is admin
        if author['user_type'] == USER_TYPE_ADMIN:
            # executes SQL command
            sql = "UPDATE Channel SET status = 3 WHERE ID = %s"
            val = (channel_id,)
            self.cursor.execute(sql, val)
            self.dbconnect.commit()
            # logging
            log_data = {
                "action": "delete_channel",
                "author_id": author['user_id'],
                "data": {
                    "channel_id": channel_id
                }
            }
            self.log_action(2, log_data)

    def link_channel(self, channel_id, token, author):
        if author['user_type'] == USER_TYPE_ADMIN:
            try:
            # print(jsontoken)
                print("Linking channel")
                sql = "UPDATE Channel SET tokens = %s WHERE id=%s"
                val = (token, channel_id)
                self.cursor.execute(sql, val)
                self.dbconnect.commit()
                log_data = {
                    "action": "link_channel",
                    "author_id": author['user_id'],
                    "data": {
                        "channel_id": channel_id,
                    }
                }
                self.log_action(2, log_data)
                VidSchool.start_credential_pool(self)
                return True
            except Exception as e:
                print(e)
                return str(e)
        else:
            return "You do not have permission to link channels"

    def unlink_channel(self, channel_id, author):
        if author['user_type'] == USER_TYPE_ADMIN:
            try:
                sql = "update channel set tokens=JSON_OBJECT() where id=%s"
                val = (channel_id,)
                self.cursor.execute(sql, val)
                self.dbconnect.commit()
                log_data = {
                    "action": "unlink_channel",
                    "author_id": author['user_id'],
                    "data": {
                        "channel_id": channel_id,
                    }
                }
                self.log_action(2, log_data)
                VidSchool.start_credential_pool(self)
                return True
            except Exception as e:
                print(e)
                return str(e)
        else:
            return "You do not have permission to unlink channels"

    # function to edit a channel in the database
    def edit_channel(self, request, author):
        channel_id = request['channel_id']
        channel_name = request['channel_name']
        platform = request['platform']
        creator_id = request['creator_id']
        editor_id = request['editor_id']
        manager_id = request['manager_id']
        ops_id = request['ops_id']
        status = request['status']
        # checks if user is admin
        if author['user_type'] == USER_TYPE_ADMIN:
            # executes SQL command
            sql = "UPDATE Channel SET name = %s, platform = %s, creator_id = %s, editor_id = %s, manager_id = %s, ops_id = %s, status = %s WHERE ID = %s"
            val = (channel_name, platform, creator_id, editor_id, manager_id, ops_id, status, channel_id)
            self.cursor.execute(sql, val)
            self.dbconnect.commit()
            # logging
            log_data = {
                "action": "edit_channel",
                "author_id": author['user_id'],
                "data": {
                    "channel_id": channel_id,
                    "channel_name": channel_name,
                    "platform": platform,
                    "creator_id": creator_id,
                    "editor_id": editor_id,
                    "manager_id": manager_id,
                    "ops_id": ops_id,
                    "status": status
                }
            }
            self.log_action(2, log_data)
            return True
        else:
            return "You do not have permission to edit this channel"

    # function to update the status of a channel
    def update_channel_status(self, channel_id, status, author):
        # checks if user is admin
        if author['user_type'] == USER_TYPE_ADMIN:
            # executes SQL command
            sql = "UPDATE Channel SET status = %s WHERE ID = %s"
            val = (status, channel_id)
            self.cursor.execute(sql, val)
            self.dbconnect.commit()
            # logging
            log_data = {
                "action": "update_channel_status",
                "author_id": author['user_id'],
                "data": {
                    "channel_id": channel_id,
                    "status": status
                }
            }
            self.log_action(2, log_data)
    # gets all channels from the database
    def get_channels(self):
        # executes SQL command
        sql = "SELECT * FROM Channel;"
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        return result
    
    # gets a specific channel from the database
    def get_channel(self, channel_id):
        # executes SQL command
        sql = "SELECT * FROM Channel WHERE ID = %s"
        val = (channel_id,)
        self.cursor.execute(sql, val)
        result = self.cursor.fetchone()
        return result

        # creator
        if user_type == '4':
            # sets SQL command
            sql = "UPDATE Channel SET creator_id = %s WHERE ID = %s"
        # editor
        elif user_type == '3':
            # sets SQL command
            sql = "UPDATE Channel SET editor_id = %s WHERE ID = %s"
        # operations
        elif user_type == '2':
            # sets SQL command
            sql = "UPDATE Channel SET ops_id = %s WHERE ID = %s"
        # manager
        elif user_type == '1':
            # sets SQL command
            sql = "UPDATE Channel SET manager_id = %s WHERE ID = %s"
        # executes SQL command
        val = (user_id, channel_id)
        self.cursor.execute(sql, val)
        self.dbconnect.commit()
        # Logging
        log_data = {
            "action": "assign_user_to_channel",
            "author_id": author['user_id'],
            "data": {
                "user_id": user_id,
                "channel_id": channel_id,
                "user_type": user_type
            }
        }
        self.log_action(2, log_data)

    # function to login a user and return user details if successfull
    def login_user(self, user_email, password):
        # executes SQL command
        sql = "SELECT * FROM User WHERE email = %s"
        val = (user_email,)
        self.cursor.execute(sql, val)
        result = self.cursor.fetchone()
        # User not found
        if result == None:
            return {
                "success": False,
                "error": "User does not exist"
            }
        # User deleted
        elif result[5] == 1:
            return {
                "success": False,
                "error": "User is disabled or deleted please contact the Administrator"
            }
        # User found
        elif result[5] == 0: 
            # checks if password is correct
            if bcrypt.checkpw(password.encode('utf-8'), result[3].encode('utf-8')):
                # Logging
                log_data = {
                    "action": "login",
                    "data": {
                        "user_id": result[0],
                        "user_email": user_email,
                        "login_time": int( time.time() )
                    }
                }
                self.log_action(0, log_data)
                # returns infor for session storage
                return {
                    "success": True,
                    "user_id": result[0],
                    "user_name": result[1],
                    "user_email": result[2],
                    "user_type": result[4],
                }
        # if all else fails
        else:
            return {
                "success": False,
                "error": "invalid database?"
            }
        
    # log every action
    def log_action(self, log_type, log_data, log_time = int( time.time() )):
        # converts log_data to JSON
        log_data = json.dumps(log_data)
        result = self.db_controller.AddToLog(log_type, log_time, log_data)
        if result == True:
            return True
        else:
            return result

    def oldlog_action(self, log_type, log_data, log_time = int( time.time() )):
        # converts log_data to JSON
        log_data = json.dumps(log_data)
        # executes SQL command
        sql = "INSERT INTO Log_Table (type, date, data) VALUES (%s, %s, %s)"
        val = (log_type, log_time, log_data)
        self.cursor.execute(sql, val)
        self.dbconnect.commit()

    def get_logs(self):
        logs = self.db_controller.GetLogs()
        final_logs = []
        for log in list(logs):
            final_logs.append(
                int(log[0]),
                log_type[int(log[1])],
                extrafunc.Epoch_to_Date(log[2],'datetime'),
                ast.literal_eval(log[3].replace("null", "None"))
            )
        return final_logs

    # get all logs
    def oldget_logs(self):
        # executes SQL command
        sql = "SELECT * FROM Log_Table"
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        return result

    ## TEST FUNCTIONS FOR DEBUGGING
    # Clear the database, ONLY FOR TESTING AND DEBUGGING PURPOSES
    def clearpro(self):
        self.cursor.execute("DROP DATABASE {}".format(self.dbname))
        self.dbconnect.commit()
        print("Database cleared")


class Db_operator:
    def __init__(self, dbhost, dbusername, dbpassword, dbname):
        print("Object initialized NOW")
        self.dbconnect = mysql.connector.connect(
            host = dbhost,
            user = dbusername,
            password = dbpassword
        )
        self.cursor = self.dbconnect.cursor()
        self.dbname = dbname
        self.sqlcommands = [
            "USE  {}".format(dbname),
            ]
        print("Connected to database")
                    
    def __del__(self):
        if self.dbconnect.is_connected():
            self.dbconnect.close()
            print("Disconnected from database")

    def AddToChannel(self, channel_id, channel_name, platform, creator_id, editor_id, manager_id, ops_id, status, tokens):
        sql = "INSERT INTO Channel (id, name, platform, creator_id, editor_id, manager_id, ops_id, status, tokens) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        val = (channel_id, channel_name, platform, creator_id, editor_id, manager_id, ops_id, status, tokens)
        self.cursor.execute(sql, val)
        self.dbconnect.commit()
        return True

    def UpdateChannel(self, channel_id, channel_name, platform, creator_id, editor_id, manager_id, ops_id, status, tokens):
        sql = "UPDATE Channel SET name = %s, platform = %s, creator_id = %s, editor_id = %s, manager_id = %s, ops_id = %s, status = %s, tokens = %s WHERE id = %s"
        val = (channel_name, platform, creator_id, editor_id, manager_id, ops_id, status, tokens, channel_id)
        self.cursor.execute(sql, val)
        self.dbconnect.commit()
        return True
    
    def GetChannel(self, channel_id):
        sql = "SELECT * FROM Channel WHERE ID = %s"
        val = (channel_id,)
        self.cursor.execute(sql, val)
        result = self.cursor.fetchone()
        return result
    
    def GetChannels(self):
        sql = "SELECT * FROM Channel"
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        return result
    
    def AddToVideo(self, video_id, old_id, title, url, channel_id, shoot_timestamp, edit_timestamp, upload_timestamp, status, comment):
        sql = "INSERT INTO Video (id, old_id, title, url, channel_id, shoot_timestamp, edit_timestamp, upload_timestamp, status, comment) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        val = (video_id, old_id, title, url, channel_id, shoot_timestamp, edit_timestamp, upload_timestamp, status, comment)
        self.cursor.execute(sql, val)
        self.dbconnect.commit()
        return True
    
    def UpdateVideo(self, video_id, title, url, channel_id, shoot_timestamp, edit_timestamp, upload_timestamp, status, comment):
        sql = "UPDATE Video SET title = %s, url = %s, channel_id = %s, shoot_timestamp = %s, edit_timestamp = %s, upload_timestamp = %s, status = %s, comment = %s WHERE id = %s"
        val = (title, url, channel_id, shoot_timestamp, edit_timestamp, upload_timestamp, status, comment, video_id)
        self.cursor.execute(sql, val)
        self.dbconnect.commit()
        return True
    
    def GetVideo(self, video_id):
        sql = "SELECT * FROM Video WHERE ID = %s"
        val = (video_id,)
        self.cursor.execute(sql, val)
        result = self.cursor.fetchone()
        return result
    
    def GetVideos(self):
        sql = "SELECT * FROM Video"
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        return result
    
    def AddToUser(self, user_name, user_email, password, role, status):
        try:
            # Add User to Table
            sql = "INSERT INTO User (name, email, password, role, status) VALUES (%s, %s, %s, %s, %s)"
            val = (user_name, user_email, password, role, status)
            self.cursor.execute(sql, val)
            self.dbconnect.commit()
            # Get User from Table
            sql2 = "SELECT * FROM User WHERE name = %s AND email = %s"
            val2 = (user_name, user_email)
            self.cursor.execute(sql2, val2)
            result = self.cursor.fetchone()
            # return User
            return result
        except Exception as e:
            return {
                "error": str(e)
            }
    
    def UpdateUser(self, user_id, user_name, user_email, password, role, status):
        sql = "UPDATE User SET name = %s, email = %s, password = %s, role = %s, status = %s WHERE id = %s"
        val = (user_name, user_email, password, role, status, user_id)
        self.cursor.execute(sql, val)
        self.dbconnect.commit()
        return True
    
    def GetUser(self, user_id):
        sql = "SELECT * FROM User WHERE ID = %s"
        val = (user_id,)
        self.cursor.execute(sql, val)
        result = self.cursor.fetchone()
        return result
    
    def GetUsers(self):
        sql = "SELECT * FROM User"
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        return result
    
    def AddToLog(self, log_type, log_date, log_data):
        try:
            sql = "INSERT INTO Log_Table (type, date, data) VALUES (%s, %s, %s, %s)"
            val = (log_type, log_date, log_data)
            self.cursor.execute(sql, val)
            self.dbconnect.commit()
            return True
        except Exception as e:
            return {
                "error": str(e)
            }
    
    def GetLogs(self):
        sql = "SELECT * FROM Log_Table"
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        return result