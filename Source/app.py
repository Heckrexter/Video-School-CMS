# Import necessary modules
import ast
import json
import extrafunc
import csv_functions
from type_vars import *
import stat_functions
from external_function import VidSchool
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import flask
import userenum , channelenum , videnum , genlogenum
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
import yaml
import os

# Find Root Path
PROJECT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Load environment variables from env.yml file
with open(os.path.join(PROJECT_PATH+'/env.yml')) as file:
    env = yaml.load(file, Loader=yaml.FullLoader)

# Extract database connection parameters from environment variables
host = env['dbvar']['host']
username = env['dbvar']['dbuser']
password = env['dbvar']['dbpass']
dbname = env['dbvar']['dbname']

# set the environment variable for the google api testing
import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

#youtube api implementation
CLIENT_SECRETS_FILE = "Source/client_secrets.json"
SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/yt-analytics.readonly',
    'https://www.googleapis.com/auth/yt-analytics-monetary.readonly',
    'https://www.googleapis.com/auth/userinfo.profile'
]

# Initialize Flask application
app = Flask(__name__)
app.secret_key = 'your secret key'
app.config['UPLOAD_FOLDER'] = "Data"
ALLOWED_EXTENSIONS = {'csv'}
app.secret_key = 'your secret key'

# Initialize VidSchool object with database connection parameters
cmsobj_db = VidSchool(host, username, password, dbname)


# Redirect request for favicon to static folder
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),'favicon.ico', mimetype='image/vnd.microsoft.icon')

# root path
@app.route('/')
def base():
    # print(session)
    if 'logged_in' in session:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

# login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    # Check if POST request with 'user_email' and 'password' in form data
    if request.method == 'POST' and 'user_email' in request.form and 'password' in request.form:       
        user_email = request.form['user_email']                                                        
        password = request.form['password']                                                            
        # Call external function to validate user credentials
        valid = cmsobj_db.login_user(user_email, password)
        # If credentials are valid
        if valid and valid.get('success'):               
            session['loggedin'] = True                   
            session['username'] = user_email             
            session['user_type'] = valid['user_type']    
            session['user_id'] = valid['user_id']        
            msg = 'Logged in successfully !'             
            return redirect(url_for('dashboard'))
        else:                                            
            msg = "Login Failed!! Contact Administrator" 
            return render_template('login.html', msg=msg)
    # Render login.html template with current message (empty message)    
    return render_template('login.html', msg=msg)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('username', None)
    session.pop('user_type', None)
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if session.get('loggedin'):
        if session['user_type'] == 0:
            # return "Admin Dashboard"
            return render_template('dashboard.html', sessionvar=session, user=userenum.roletype)
        elif session['user_type'] >= 1:
            channellist = cmsobj_db.get_channels_by_user(session['user_id'], session['user_type'])
            # return "Manager Dashboard"
            return render_template('dashboard.html', sessionvar=session, channels=channellist, user=userenum.roletype)
    else:
        return redirect(url_for('login'))

@app.route('/view/<int:channel_id>')
def view_channel(channel_id):
    if session.get('loggedin'):
        channels = cmsobj_db.get_channel(channel_id)
        if session['user_type'] == 4:
            if session['user_id'] != channels[3]:
                return "You are not authorized to view this page"
        elif session['user_type'] == 3:
            if session['user_id'] != channels[4]:
                return "You are not authorized to view this page"
        elif session['user_type'] == 2:
            if session['user_id'] != channels[6]:
                return "You are not authorized to view this page"
        elif session['user_type'] == 1:
            if session['user_id'] != channels[5]:
                return "You are not authorized to view this page"
        videos = cmsobj_db.get_videos_by_channel(channel_id)
        videos.reverse()
        finalvideos = []
        for i in videos:
            # print(i)
            finalvideos.append([i[0], i[1], i[2], i[3], i[4], extrafunc.epoch_to_string(i[5],'date'), extrafunc.epoch_to_string(i[6],'date'), extrafunc.epoch_to_string(i[7],'date'), i[8], i[9]])
        users = {}
        for i in range(3,7):
            user = cmsobj_db.get_user(channels[i])
            if user[5] == USER_STATUS_INACTIVE:
                users[channels[i]] = [user[1], "INACTIVE USER"]
            else:
                users[channels[i]] = [user[1], user[2]]
        return render_template('view_channel.html', sessionvar=session,channel=channels, videos=finalvideos, users=users, platform=channelenum.platform_names, status=videnum.vidstatus)
    else:
        return redirect(url_for('login'))

@app.route('/view/<int:channel_id>/stat')
def view_channel_stats(channel_id):
    if session.get('loggedin'):
        channels = cmsobj_db.get_channel(channel_id)
        if session['user_type'] == 4:
            if session['user_id'] != channels[3]:
                return "You are not authorized to view this page"
        elif session['user_type'] == 3:
            if session['user_id'] != channels[4]:
                return "You are not authorized to view this page"
        elif session['user_type'] == 2:
            if session['user_id'] != channels[6]:
                return "You are not authorized to view this page"
        elif session['user_type'] == 1:
            if session['user_id'] != channels[5]:
                return "You are not authorized to view this page"
        stats = None
        if channels[0] in VidSchool.credentialpool:
            stats = stat_functions.get_main(channels[1], channels[0])
        return render_template('view_channel_stats.html', sessionvar=session, channel=channels, stats=stats)
    else:
        return redirect(url_for('login'))

@app.route('/update', methods=['GET', 'POST'])
def update_status():
    if session.get('loggedin'):
        author = {
            'user_id': session['user_id'],
            'user_type': session['user_type']
        }
        result = cmsobj_db.set_video_status(request.form.to_dict(), author)
        if result!=True:
            return result
        # return "you updated"
        return flask.redirect(request.referrer)
    else:
        return redirect(url_for('login'))

@app.route('/view/<int:channel_id>/delete_video/<int:video_id>')
def delete_video(channel_id,video_id):
    if session.get('loggedin'):
        author = {
            'user_id': session['user_id'],
            'user_type': session['user_type']
        }
        channels = cmsobj_db.get_channel(channel_id)
        if session['user_type'] == 4:
            if session['user_id'] != channels[3]:
                return "You are not authorized to view this page"
        elif session['user_type'] == 3:
            if session['user_id'] != channels[4]:
                return "You are not authorized to view this page"
        elif session['user_type'] == 2:
            if session['user_id'] != channels[6]:
                return "You are not authorized to view this page"
        elif session['user_type'] == 1:
            if session['user_id'] != channels[5]:
                return "You are not authorized to view this page"
        result = cmsobj_db.set_delete_video(video_id=video_id, author=author)
        if result!=True:
            return result
        return flask.redirect(request.referrer)
    else:
        return redirect(url_for('login'))

@app.route('/edit/video/<int:video_id>', methods=['GET', 'POST'])
def edit_video(video_id):
    if session.get('loggedin'):
        video = cmsobj_db.get_video(video_id)
        channel_id = video[4]
        channel = cmsobj_db.get_channel(channel_id)
        if session['user_type'] == 4:
            if session['user_id'] != channel[3]:
                return "You are not authorized to view this page"
        elif session['user_type'] == 3:
            if session['user_id'] != channel[4]:
                return "You are not authorized to view this page"
        elif session['user_type'] == 2:
            if session['user_id'] != channel[6]:
                return "You are not authorized to view this page"
        elif session['user_type'] == 1:
            if session['user_id'] != channel[5]:
                return "You are not authorized to view this page"
        if request.method == 'POST':
            author = {
                'user_id': session['user_id'],
                'user_type': session['user_type']
            }
            passreq = request.form.to_dict()
            passreq['shoot_timestamp'] = extrafunc.string_to_epoch(passreq['shoot_timestamp'])
            passreq['edit_timestamp'] = extrafunc.string_to_epoch(passreq['edit_timestamp'])
            passreq['upload_timestamp'] = extrafunc.string_to_epoch(passreq['upload_timestamp'])
            # print(passreq)
            # result = True
            result = cmsobj_db.update_video(passreq, author)
            if result!=True:
                return result
            return redirect(url_for('view_channel', channel_id=request.form['channel_id']))
        video = cmsobj_db.get_video(video_id)
        finalvidlist = list(video)
        for i in range(5,8):
            finalvidlist[i] = extrafunc.epoch_to_string(finalvidlist[i], 'date')
            print(finalvidlist[i])
        return render_template('edit_video.html', channel=channel, sessionvar=session, video=finalvidlist)
    else:
        return redirect(url_for('login'))

@app.route('/view/<int:channel_id>/add_video', methods=['GET', 'POST'])
def add_video(channel_id):
    if session.get('loggedin'):
        channel = cmsobj_db.get_channel(channel_id)
        if session['user_type'] == 4:
            if session['user_id'] != channel[3]:
                return "You are not authorized to view this page"
        elif session['user_type'] == 3:
            if session['user_id'] != channel[4]:
                return "You are not authorized to view this page"
        elif session['user_type'] == 2:
            if session['user_id'] != channel[6]:
                return "You are not authorized to view this page"
        elif session['user_type'] == 1:
            if session['user_id'] != channel[5]:
                return "You are not authorized to view this page"
        if session["user_type"] >= 3 and session['user_type'] != 4:
            return "You are not authorized to add videos"
        if request.method == 'POST':
            author = {
                'user_id': session['user_id'],
                'user_type': session['user_type']
            }
            result = cmsobj_db.add_video(request.form.to_dict(), author)
            if result!=True:
                return result
            else:
                return render_template('add_video.html', sessionvar=session, channel=channel, msg="Video added Successfully")
            # return redirect(url_for('view_channel', channel_id=channel_id))
        return render_template('add_video.html', sessionvar=session, channel=channel)
    else:
        return redirect(url_for('login'))

# @app.route('/view/<int:channel_id>/add_video/import', methods=['GET', 'POST'])
# def import_videos(channel_id):
#     if session.get('loggedin'):
#         channel = cmsobj_db.get_channel(channel_id)
#         if session['user_type'] == 4:
#             if session['user_id'] != channel[3]:
#                 return "You are not

@app.route('/users')
def view_users():
    if session.get('loggedin'):
        if session['user_type'] == 0:
            author = {
                'user_id': session['user_id'],
                'user_type': session['user_type']
            }
            users = cmsobj_db.get_users(author=author)
            roles = userenum.roletype
            status = userenum.userstatus
            return render_template('view_user.html', users=users, roles=roles, status=status)
        else:
            return "You are not authorized to view this page"
    else:
        return redirect(url_for('login'))

@app.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if session.get('loggedin'):
        if session['user_type'] == 0:
            if request.method == 'POST':
                author = {
                    'user_id': session['user_id'],
                    'user_type': session['user_type']
                }
                # print(request.form.to_dict())
                result = cmsobj_db.edit_user(request.form.to_dict(), author)
                if result!=True:
                    return result
                return redirect(url_for('view_users'))
            user = cmsobj_db.get_user(user_id)
            return render_template('edit_user.html', user=user)
        else:
            return "You are not authorized to view sthis page"
    else:
        return redirect(url_for('login'))

@app.route('/users/delete/<int:user_id>')
def delete_user(user_id):
    if session.get('loggedin'):
        if session['user_type'] == 0:
            author = {
                'user_id': session['user_id'],
                'user_type': session['user_type']
            }
            result = cmsobj_db.delete_user(user_id, author)
            if result!=True:
                return result
            elif result == True:
                return redirect(url_for('view_users'))
        else:
            return "You are not authorized to view this page"

@app.route('/users/add', methods=['GET', 'POST'])
def add_user():
    if session.get('loggedin'):
        if session['user_type'] == 0:
            if request.method == 'POST':
                author = {
                    'user_id': session['user_id'],
                    'user_type': session['user_type']
                }
                result = cmsobj_db.add_user(request.form.to_dict(), author)
                if result!=True:
                    return render_template('add_user.html', msg=result)
                else:
                    return render_template('add_user.html', msg="User added Successfully")
            return render_template('add_user.html')
        else:
            return "You are not authorized to view this page"
    else:
        return redirect(url_for('login'))

@app.route('/channels')
def view_channels():
    if session.get('loggedin'):
        if session['user_type'] == 0:
            author = {
                'user_id': session['user_id'],
                'user_type': session['user_type']
            }
            channels = cmsobj_db.get_channels()
            users = cmsobj_db.get_users(author=author)
            finaluserlist = {}
            for user in list(users):
                if user[5] == USER_STATUS_INACTIVE:
                    finaluserlist[user[0]] = [user[1], "INACTIVE USER"]
                else:
                    finaluserlist[user[0]] = [user[1], user[2]]
            return render_template('view_all_channels.html', channels=channels, user=finaluserlist, status=channelenum.channelstatus, platform=channelenum.platform_names)
        else:
            return "You are not authorized to view this page"
    else:
        return redirect(url_for('login'))

@app.route('/channels/edit/<int:channel_id>', methods=['GET', 'POST'])
def edit_channel(channel_id):
    if session.get('loggedin'):
        if session['user_type'] == 0:
            if request.method == 'POST':
                author = {
                    'user_id': session['user_id'],
                    'user_type': session['user_type']
                }
                # print(request.form.to_dict())
                # return request.form.to_dict()
                result = cmsobj_db.edit_channel(request.form.to_dict(), author)
                if result!=True:
                    return result
                if 'addcredentials' in session:
                    # print("linking channel")
                    linkres = link_channel(channel_id)
                    if linkres!=True:
                        return linkres
                return redirect(url_for('view_channels'))
            channel = cmsobj_db.get_channel(channel_id)
            creator = cmsobj_db.get_users_by_role(4)
            editor = cmsobj_db.get_users_by_role(3)
            ops = cmsobj_db.get_users_by_role(2)
            manager = cmsobj_db.get_users_by_role(1)
            return render_template('edit_channel.html', channel=channel, creators=creator, editors=editor, opss=ops, managers=manager, status=channelenum.channelstatus, platform=channelenum.platform_names)
        else:
            return "You are not authorized to view this page"
    else:
        return redirect(url_for('login'))

@app.route('/channels/add', methods=['GET', 'POST'])
def add_channel():
    if session.get('loggedin'):
        if session['user_type'] == 0:
            channel_name = None
            if "temp_channel_name" in session:
                channel_name = session["temp_channel_name"]
            creator = cmsobj_db.get_users_by_role(4)
            editor = cmsobj_db.get_users_by_role(3)
            ops = cmsobj_db.get_users_by_role(2)
            manager = cmsobj_db.get_users_by_role(1)
            if request.method == 'POST':
                author = {
                    'user_id': session['user_id'],
                    'user_type': session['user_type']
                }
                if "temp_channel_name" in session:
                    session.pop("temp_channel_name")
                channel_id = cmsobj_db.add_channel(request.form.to_dict(), author)
                if type(channel_id)!=int:
                    return channel_id
                elif type(channel_id)==int:
                    if "addcredentials" in session:
                        result = link_channel(channel_id)
                        if result!=True:
                            return result
                        else:
                            return render_template('add_channel.html', channel_name=None, creators=creator, editors=editor, opss=ops, managers=manager, status=channelenum.channelstatus, platform=channelenum.platform_names, msg="Channel added and linked Successfully")
                    else:
                        return render_template('add_channel.html', channel_name=None, creators=creator, editors=editor, opss=ops, managers=manager, status=channelenum.channelstatus, platform=channelenum.platform_names, msg="Channel added Successfully")
            return render_template('add_channel.html', channel_name=channel_name, creators=creator, editors=editor, opss=ops, managers=manager, status=channelenum.channelstatus, platform=channelenum.platform_names)
        else:
            return "You are not authorized to view this page"
    else:
        return redirect(url_for('login'))

@app.route('/channels/link/<int:channel_id>', methods=['GET','POST'])
def link_channel(channel_id):
    if session.get('loggedin'):
        if session['user_type'] == 0:
            if request.method == 'POST':
                author = {
                    'user_id': session['user_id'],
                    'user_type': session['user_type']
                }
                tokens = json.dumps(session['addcredentials'])
                session.pop('addcredentials')
                # print(tokens)
                result = cmsobj_db.link_channel(channel_id=channel_id, token=tokens, author=author)
                if result!=True:
                    return result
                else:
                    return True
        else:
            return "You are not authorized to view this page"
    else:
        return redirect(url_for('login'))

@app.route('/channels/unlink/<int:channel_id>')
def unlink_channel(channel_id):
    if session.get('loggedin'):
        if session['user_type'] == 0:
            author = {
                'user_id': session['user_id'],
                'user_type': session['user_type']
            }
            result = cmsobj_db.unlink_channel(channel_id, author)
            if result!=True:
                return result
            elif result == True:
                return redirect(request.referrer)
        else:
            return "You are not authorized to view this page"
    else:
        return redirect(url_for('login'))

@app.route('/logs')
def get_logs():
    if session.get('loggedin'):
        if session['user_type'] == 0:
            author = {
                'user_id': session['user_id'],
                'user_type': session['user_type']
            }
            logs = cmsobj_db.get_logs()
            finallogs = []
            finaluserlist = {}
            users = cmsobj_db.get_users(author=author)
            for log in logs:
                finallogs.append([log[0], log[1], extrafunc.epoch_to_string(log[2], 'datetime'), ast.literal_eval(log[3].replace('null', 'None'))])
            for user in list(users):
                finaluserlist[user[0]] = [user[1], user[2]]
            finallogs.reverse()
            return render_template('view_logs.html', logs=finallogs, users=finaluserlist, action=genlogenum.log_type)
        else:
            return "You are not authorized to view this page"
    else:
        return redirect(url_for('login'))

# Oauth page 1
@app.route('/oauth')
def oauth():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)
    auth_url,state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')
    session['state'] = state
    session['return_url'] = request.referrer
    return flask.redirect(auth_url)

# Oauth page 2
@app.route('/oauth2callback')
def oauth2callback():
    state = session['state']
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)
    auth_response = flask.request.url
    flow.fetch_token(authorization_response=auth_response)
    
    credentials = flow.credentials
    youtube = build('youtube', 'v3', credentials=credentials)
    request = youtube.channels().list(
        part="snippet",
        mine=True
    )
    response = request.execute()
    if response['items']:
        channel_name = response['items'][0]['snippet']['title']
    else:
        channel_name = "No channel found"
    
    # store channels name and credentials in session
    session['temp_channel_name'] = channel_name
    session['addcredentials'] = extrafunc.credtodict(credentials)
    # print(session['addcredentials'])
    return_url = session['return_url']
    session.pop('return_url')
    return flask.redirect(return_url)

# Main entry point of the application
if __name__ == '__main__':
    cmsobj_db.setupdb()                                            # Setup any necessary components from extfun module
    app.run(debug=True, port=8089,host='localhost')                                            # Run the Flask application in debug mode
