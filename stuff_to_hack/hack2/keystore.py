#! /usr/bin/env python

import MySQLdb
from flask import Flask, request

app = Flask(__name__)
app.config['DEBUG'] = True

db = MySQLdb.connect('localhost', 'keystore', 'keystoreuserpass', 'keydb')

cursor = db.cursor()

@app.route('/store', methods=["POST"])
def store():
    assert 'key' in request.form
    assert 'value' in request.form
    new_sql = "INSERT INTO keyval (k, val) VALUES ('%s', '%s')" % (
            request.form['key'], request.form['value'])
    cursor.execute(new_sql)
    return "Success!"

@app.route('/retrieve', methods=["POST"])
def retrieve():
    assert 'key' in request.form
    new_sql = "SELECT val FROM keyval WHERE k LIKE '%%%s%%'" % request.form['key']
    cursor.execute(new_sql)
    retval = ""
    for row in cursor.fetchall():
        retval += str(row[0])
    return str(retval)

if __name__ == "__main__":
    cursor.execute("DROP TABLE IF EXISTS keyval")

    sql = """CREATE TABLE keyval (
            k VARCHAR(64),
            val VARCHAR(64)
            )"""

    cursor.execute(sql)
    app.run(port=8002, host='0.0.0.0')

    db.close()
