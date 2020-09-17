from flask import Flask, request, url_for, render_template, redirect
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
    return render_template("index.html")


@app.route('/fetch')
def fetch():
    """Fetching data from request and storing it in the database"""
    db_name = "stories"
    r = requests.get(get_link())
    data = r.json()
    if data["completed"]:
        return render_template("results.html", results=add_data(db_name, data))
    else:
        return render_template("results.html", results="Nothing was added to the db  " + str(data))


@app.route('/story/<id>')
def by_story(id):
    """Prints title of the given record id"""
    cur = mysql.connection.cursor()
    try:
        cur.execute('''SELECT * FROM stories WHERE id = %s''', (id,))
        results = cur.fetchall()
        return str(results)
    except mysql.connection.Error as err:
        results = f"While fetching the story by id, '{id}' an error occurred: {err}"
        logger.error(results)
        return render_template("results.html", results=results)


@app.route('/user/<userId>')
def by_userid(userId):
    """All stories related to userId"""
    cur = mysql.connection.cursor()
    try:
        cur.execute('''SELECT title FROM stories WHERE userId = %s''', (userId,))
        results = cur.fetchall()
        return str(results)
    except mysql.connection.Error as err:
        results = f"While fetching the stories of the user '{userId}', an error occurred: {err}"
        logger.error(results)
        return render_template("results.html", results=results)


@app.route('/title/<word>')
def title_search(word):
    """Getting titles that include word"""
    cur = mysql.connection.cursor()
    try:
        cur.execute('''SELECT title FROM stories WHERE title LIKE %s ''', ('%' + word + '%',))
        results = cur.fetchall()
        return str(results)
    except mysql.connection.Error as err:
        results = f"While fetching the stories by word '{word}', an error occurred: {err}"
        logger.error(results)
        return render_template("results.html", results=results)


@app.route('/db/<name>')
def stor(name):
    """Viewing the values of a given table"""
    cur = mysql.connection.cursor()
    try:
        cur.execute('''SELECT * FROM ''' + name)
        results = cur.fetchall()
        return str(results)
    except mysql.connection.Error as err:
        results = f"An error occurred while trying to get data from '{name}': {err}"
        logger.error(results)
        return render_template("results.html", results=results)


@app.route('/create_table/<name>')
def crt(name):
    """Creating a table with a given name"""
    cur = mysql.connection.cursor()
    try:
        cur.execute('''CREATE TABLE ''' + name + ''' (id INTEGER UNIQUE, userId INTEGER, title VARCHAR(255))''')
        mysql.connection.commit()
        results = f"Table {name} created!"
        logger.info(results)
        return render_template("results.html", results=results)
    except mysql.connection.Error as err:
        results = f"Failed creating database {name}. Error: '{err}'"
        logger.error(results)
        return render_template("results.html", results=results)


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
        results = f"Could not fetch all tables. Error: '{err}'"
        logger.error(results)
        return render_template("results.html", results=results)


@app.route('/dispatch')
def dispatch():
    #destination = request.form.get('name')
    userid = request.args.get('str_by_usr')
    id = request.args.get('str_by_id')
    word = request.args.get('str_by_wrd')
    #value = request.form.get('value')

    if id:
        return redirect(url_for('by_story'), id)
    elif userid:
        return redirect(url_for('by_userid'), userid)
    elif word:
        return redirect(url_for('title_search'), word)

    #
    # if destination == "str_by_id":
    #     return redirect(url_for('by_story'), value)
    # elif destination == "str_by_usr":
    #     return redirect(url_for('by_userid'), value)
    # elif destination == "str_by_wrd":
    #     return redirect(url_for('title_search'), value)


@app.route('/logs')
def logz():
    """Showing the logs"""
    def lastNlines(fname, N):
        bufsize = 8192
        fsize = os.stat(fname).st_size
        iter = 0

        with open('app.log') as f:
            if bufsize > fsize:
                # adjusting buffer size according to size of file
                bufsize = fsize - 1
                # list to store last N lines
                fetched_lines = []
                # while loop to fetch last N lines
                while True:
                    iter += 1
                    # moving cursor to the last Nth line of file
                    f.seek(fsize - bufsize * iter)
                    # storing each line in list upto end of file
                    fetched_lines.extend(f.readlines())

                    # halting the program when size of list is equal or greater to the number of lines requested or
                    # when we reach end of file
                    if len(fetched_lines) >= N or f.tell() == 0:
                        return ''.join(fetched_lines[-N:])

    try:
        render_template("logs.html", logs=lastNlines('app.log', 20))
    except Exception as e:
        return render_template("results.html", results=f"No logs. An error occured: {e}")
