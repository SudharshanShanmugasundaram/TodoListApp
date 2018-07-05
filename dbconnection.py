from flask_mysqldb import *
def connection():
    conn=MySQLdb.connect(host='localhost',user='root',passwd='sudharshan1999',db='flaskapp')
    c=conn.cursor()
    return c,conn
