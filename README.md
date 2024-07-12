# VideoSchool Content Management System (Under Development)
<br>
This is a content management system for a video school. It allows the company to manage employees, videos and channels. The system is build using Python Flask, MySQL, and Apache Web Server.

## Features
- User authentication
- User roles
- User permissions
- Video CRUD
- Channel CRUD
- Employee CRUD
- Action logging

## Pre-requisites
1. Python >= 3.10.14
2. MySQL >= 8.4.0 LTS
3. Apache Web Server >= 2.4


## Installation
1. Clone the repository
2. Make sure you install the valid version of the softwares as mentioned aboved in the prerequisites
3. Enter the project's Source directory
```bash
cd /path/to/Video-School-CMS/Source
```
4. Create a virtual environment
```bash
python3.10 -m venv vscms
```
5. Activate the virtual environment
```bash
source /path/to/Video-School-CMS/Source/vscms/bin/activate
```
6. Install the required packages
```bash
pip install -r requirements.txt --no-cache
```
7. Create an env.py file in both the Source and Setup directories with the following content
```python
host = 'localhost'
dbuser = 'root'
dbpass = '<MySQL password>'
dbname = 'VIDEOSCHOOL'
```
    note: Replace <MySQL password> with your MySQL password and feel free to customize all aspects if you're modifiying the database schema or program
8. To setup the database before use, run the resetdb.py file
```bash
python path/to/Video-School-CMS/Setup/resetdb.py
```
9. To setup a reverse proxy for the server, go to the server's files and make the following changes:-
- Uncomment the follow lines from the httpd.conf file
    ```apache
    LoadModule proxy_module libexec/apache2/mod_proxy.so

    LoadModule proxy_http_module libexec/apache2/mod_proxy_http.so

    Include /private/etc/apache2/extra/httpd-vhosts.conf
    ```
- Add the following lines to httpd-vhosts.conf and comment out the example virtual hosts
    ```apache
    <VirtualHost *:80>
        ProxyPreserveHost On
        ProxyRequests Off
        ServerName videoschool.cms
        ServerAlias www.videoschool.cms
        ProxyPass / http://127.0.0.1:8089/
        ProxyPassReverse / http://127.0.0.1:8089/
    </VirtualHost>
    ```
10. Start the apache server on your local machine and start the python wsgi server by running the following command
```bash
python /path/to/Video-School-CMS/Source/wsgi.py
```
11. The server is now running, to visit it navigate to http://localhost, you can log into the portal with a default admin account with the following credentials:
```bash
username: root@root.com
password: root
```
    (note: This account is only for testing purposes, it is recommended to create a new admin account and delete this one)
