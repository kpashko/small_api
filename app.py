from flask import Flask, redirect, url_for
from flask_mysqldb import MySQL
import requests
import yaml
import logging.config
from random import randint
import os
app = Flask(__name__)

app.config["MYSQL_USER"]  = os.environ.get("MYSQL_USER")
app.config["MYSQL_PASSWORD"] = os.environ.get("MYSQL_PASSWORD")
app.config["MYSQL_HOST"] = os.environ.get("MYSQL_HOST")
app.config["MYSQL_DB"] = os.environ.get("MYSQL_DB")
app.config["MYSQL_CURSORCLASS"] = 'DictCursor'

mysql = MySQL(app)

logging.config.dictConfig(yaml.load(open('logging.cfg'), Loader=yaml.FullLoader))
logger = logging.getLogger('file')


def get_link():
    idx = randint(1, 100)
    return f"https://jsonplaceholder.typicode.com/todos/{idx}"


def add_data(database, data):
    cur = mysql.connection.cursor()
    usr_id = data["userId"]
    title = data["title"]
    todo_id = data["id"]
    try:
        cur.execute('''INSERT INTO ''' + database + ''' VALUES (%s,%s,%s)''', (todo_id, usr_id, title,))
        mysql.connection.commit()
        logger.info(f"added userid: {usr_id} with title: {title} to the database")
        return f"added userid: {usr_id} with title: {title} to the database"
    except mysql.connection.Error as err:
        logger.error(f"Failed adding item to the database: {err}")
        return "Failed adding to the database: {}".format(err)


@app.route('/')
def index():
    cur = mysql.connection.cursor()
    cur.close()
    return 'hi'


@app.route('/fetch')
def hello_world():
    """Fetching data from request and storing it in the database"""
    db_name = "stories"
    r = requests.get(get_link())
    data = r.json()
    if data["completed"]:
        return add_data(db_name, data)
    else:
        return "Nothing was added to the db  " + str(data)


@app.route('/story/<id>')
def by_story(id):
    """Prints title of the given record id"""
    cur = mysql.connection.cursor()
    try:
        cur.execute('''SELECT * FROM stories WHERE id = %s''', (id,))
        results = cur.fetchall()
        return str(results)
    except mysql.connection.Error as err:
        logger.error(f"While fetching the story by id, '{id}' an error occurred: {err}")
        return f"While fetching the story by id, '{id}' an error occurred: {err}"


@app.route('/user/<userId>')
def by_userid(userId):
    """All stories related to userId"""
    cur = mysql.connection.cursor()
    try:
        cur.execute('''SELECT title FROM stories WHERE userId = %s''', (userId,))
        results = cur.fetchall()
        return str(results)
    except mysql.connection.Error as err:
        logger.error(f"While fetching the stories of the user '{userId}', an error occurred: {err}")
        return f"While fetching the stories of the user '{userId}', an error occurred: {err}"


@app.route('/title/<word>')
def title_search(word):
    """Getting titles that include word"""
    cur = mysql.connection.cursor()
    try:
        cur.execute('''SELECT title FROM stories WHERE title LIKE %s ''', ('%' + word + '%',))
        results = cur.fetchall()
        return str(results)
    except mysql.connection.Error as err:
        logger.error(f"While fetching the stories by word '{word}', an error occurred: {err}")
        return f"While fetching the stories by word '{word}', an error occurred: {err}"


@app.route('/db/<name>')
def stor(name):
    """Viewing the values of a given table"""
    cur = mysql.connection.cursor()
    try:
        cur.execute('''SELECT * FROM ''' + name)
        results = cur.fetchall()
        return str(results)
    except mysql.connection.Error as err:
        logger.error(f"An error occurred while trying to get data from '{name}': {err}")
        return redirect(url_for('.tbls'))


@app.route('/create_table/<name>')
def crt(name):
    """Creating a table with a given name"""
    cur = mysql.connection.cursor()
    try:
        cur.execute('''CREATE TABLE ''' + name + ''' (id INTEGER UNIQUE, userId INTEGER, title VARCHAR(255))''')
        mysql.connection.commit()
        logger.info(f"Table {name} created!")
        return f"Table {name} created!"
    except mysql.connection.Error as err:
        logger.error(f"Failed creating database {name}. Error: '{err}'")
        return "Failed creating database: {}".format(err)


@app.route('/drop_table/<name>')
def drptbl(name):
    """Deleting the table of a given name"""
    cur = mysql.connection.cursor()
    try:
        cur.execute('''DROP TABLE IF EXISTS ''' + name)
        mysql.connection.commit()
        logger.info(f"Database {name} was successfully dropped.")
        return f"Successfully dropped {name}"
    except mysql.connection.Error as err:
        logger.error(f"Failed dropping database. Error: '{err}'")
        return "Failed dropping database: {}".format(err)


@app.route('/tables')
def tbls():
    """Getting the list of available tables"""
    cur = mysql.connection.cursor()
    try:
        cur.execute("SHOW Tables")
        return str(cur.fetchall())
    except mysql.connection.Error as err:
        logger.error(f"Could not fetch all tables. Error: '{err}'")
        return f"Could not fetch all tables. Error: '{err}'"
