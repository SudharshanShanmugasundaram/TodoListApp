from flask import Flask,render_template,request,url_for,redirect,flash,session
from flask_mysqldb import MySQL
from dbconnection import connection
from wtforms import Form,BooleanField,TextField,PasswordField,validators
from passlib.hash import sha256_crypt
from MySQLdb import escape_string as thwart
from functools import wraps

import gc

app=Flask(__name__)

app.config['SECRET_KEY']='flaskapp'

@app.route('/')
def index():
    return render_template('homepage.html')

def login_required(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if 'logged_in' in session:
            return f(*args,**kwargs)
        else:
            flash("You need to login first")
            return redirect(url_for('login_page'))
    return wrap

@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been successfully logged out ")
    gc.collect()
    return redirect(url_for('index'))


class RegistrationForm(Form):
    username=TextField('Username',[validators.Length(min=4,max=20)])
    email=TextField('Email Address',[validators.Length(min=10,max=50)])
    password=PasswordField('Password',[validators.Required(),validators.EqualTo('confirm',message="Passwords must match.")])
    confirm=PasswordField('Repeat Password')
    accept_tos=BooleanField('I accept to all The Terms and Conditions',[validators.Required()])

@app.route('/register',methods=['GET','POST'])
def register():
    try:
        form=RegistrationForm(request.form)
        if request.method=='POST' and form.validate():
            username=form.username.data
            email=form.email.data
            password=sha256_crypt.encrypt((str(form.password.data)))
            c,conn=connection()
            x=c.execute("SELECT * from users where username=(%s)",[thwart(username)])
            if int(x)>0:
                flash("That username is already taken.Please choose another")
                return render_template('register.html',form=form)
            else:
                c.execute("INSERT INTO users (username,password,email) VALUES (%s,%s,%s)",(thwart(username),thwart(password),thwart(email)))
                conn.commit()
                flash("Thanks for registering!!!")
                c.close()
                conn.close()
                gc.collect()
                return redirect('/')

        return render_template('register.html',form=form)
    except Exception as e:
        return (str(e))

@app.route("/login",methods=["GET","POST"])
def login_page():
    error=None
    try:
        if request.method =='POST':
            c,conn=connection()
            username=c.execute("SELECT * FROM users WHERE username=(%s)",(thwart(request.form['username']),))
            if username==0:
                #error=" Username doesn't exist"
                flash("Username doesn't exist")
                return render_template('login.html',error=error)

            data=c.fetchone()[2]

            if sha256_crypt.verify(request.form['password'],data):
                session['logged_in']=True
                session['username']=request.form['username']
                return redirect(url_for('dashboard'))
            else:
                # error=" Incorrect Password"
                flash("Incorrect Password")
                return render_template('login.html',error=error)
            c.close()
            conn.close()
        gc.collect()
        return render_template('login.html',error=error)
    except Exception as e:
        return render_template("login.html",error=e)

@app.route('/dashboard')
@login_required
def dashboard():
    c,conn=connection()
    result=c.execute("SELECT * FROM todolist where username=(%s)",(thwart(session['username']),))
    tasks=c.fetchall()
    if result>0:
        return render_template('dashboard.html',tasks=tasks)
    else:
        flash("No tasks left ")
    c.close()
    conn.close()
    return render_template('dashboard.html')


@app.route('/add',methods=['GET','POST'])
@login_required
def add():
    if request.method=='POST':
        task=request.form['todolist']
        c,conn=connection()
        c.execute("INSERT INTO todolist (username,task) VALUES (%s,%s)",(thwart(session['username']),thwart(task)))
        conn.commit()
        c.close()
        conn.close()
        flash("Added successfully!!!")
        return redirect(url_for('dashboard'))
    return render_template('dashboard.html')

@app.route('/delete/<string:id>',methods=['POST','GET'])
@login_required
def delete(id):
    c,conn=connection()
    c.execute("DELETE FROM todolist WHERE id=(%s)",(thwart(id),))
    conn.commit()
    c.close()
    conn.close()
    flash("Task deleted!!!")
    return redirect(url_for('dashboard'))

@app.route("/todolistitems")
@login_required
def todolist():
    c,conn=connection()
    result=c.execute("SELECT * FROM todolist where username=(%s)",(thwart(session['username']),))
    tasks=c.fetchall()
    if result>0:
        return render_template('todolist.html',tasks=tasks)
    else:
        flash("No tasks left ")
    c.close()
    conn.close()
    return render_template('todolist.html')

if __name__=='__main__':
    app.run(debug=True)
