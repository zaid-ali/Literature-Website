from flask import Flask, render_template, request, jsonify, flash, session, url_for
import sqlite3
from sqlite3 import Error
import hashlib
import os
from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField,BooleanField,DateTimeField,RadioField,SelectField,TextField, TextAreaField
from wtforms.validators import DataRequired


app = Flask(__name__)
app.secret_key = b'\xed"\xdc\xe2\x8c\x1c~>\x8b\xcb\x99p,\xb4\xf9J5fx\x9ag_\x9a\xb2'
app.config['DEBUG'] = True  # 开启 debug

# class Session(dict, SessionMixin):
#     pass

# Connect to the SQL database; source: https://realpython.com/python-sql-libraries/
def create_connection(path):
    connection = None
    try:
        connection = sqlite3.connect(path)
        print("Connection to SQLite DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")
    return connection

#for creating new post form
class NewPost(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    body = TextAreaField("Body", validators=[DataRequired()])
    formoflit = RadioField("What is the form of literature for this Lit Byte? ", choices =[("prose", "Prose")\
    , ("poetry", "Poetry"), ("drama", "Drama")], validators=[DataRequired()])
    genre = RadioField("What is the genre for this Lit Byte?", choices=[("action", "Action"), ("mystery",\
     "Mystery"), ("scifi", "Science Fiction"), ("fantasy", "Fantasy"), ("horror", "Horror"), \
     ("romance", "Romance") ], validators=[DataRequired()])
    post = SubmitField("Post")



@app.route("/")
def index():
    # logconn = create_connection("databases/database.sqlite")
    # currentCursor = logconn.cursor()
    # sqlSelect = "DROP TABLE userPosts"
    # currentCursor.execute(sqlSelect)

    return render_template("cover.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/logout")
def logout():
    session['userid']=""
    return render_template("login.html")

@app.route("/loggedin", methods=['GET','POST'])
def loggedin():
    usern=request.form['inputUsername']
    passw=request.form['inputPassword']
    logconn=create_connection("databases/database.sqlite")
    currentCursor=logconn.cursor()
    sqlSelect="SELECT * FROM credentials WHERE username=?"
    currentCursor.execute(sqlSelect, (usern,))
    row=currentCursor.fetchall()
    if row==[]:
        error="Username not found"
        return render_template("login.html", error=error)
    creds=row[0]
    salt=creds[2] #Pull the salt from the row
    hashedPassw=creds[1] #Pull the hashed password
    salt=salt.encode('latin1') #Change it back from string to the original bytes
    passHash=hashlib.pbkdf2_hmac("sha512",passw.encode('utf-8'),salt,100000)
    if hashedPassw!=passHash.hex(): #passhash.hex() returns the string representation
        error="Incorrect password"
        return render_template("login.html", error=error)
    session['userid'] = creds[0] #Should set the userid cookie to the user's username
    return home()

@app.route("/signup")
def signup():
    return render_template("signup.html")

# Learned python password hashing from https://nitratine.net/blog/post/how-to-hash-passwords-in-python/
@app.route("/signedup", methods=['GET','POST'])
def signedup():
    usern=request.form['inputUsername']
    passw=request.form['inputPassword']
    logconn=create_connection("databases/database.sqlite")
    currentCursor=logconn.cursor()
    sqlCreateTable="""CREATE TABLE IF NOT EXISTS credentials (
                        username text PRIMARY KEY,
                        password text NOT NULL,
                        salt text NOT NULL
                    ); """
    currentCursor.execute(sqlCreateTable)
    salt=os.urandom(32)
    passHash=hashlib.pbkdf2_hmac("sha512",passw.encode('utf-8'),salt,100000)
    #Have to decode the salt with latin1 to make a string that I can revert back to the proper bytes
    credTuple=(usern,passHash.hex(),salt.decode('latin1')) #passhash.hex() returns a string representation
    sqlInsert="""INSERT INTO credentials(username, password, salt)
                VALUES(?,?,?)""" # The ?'s should act as placeholders for the credTuple indexs to insert into
    try:
        currentCursor.execute(sqlInsert,credTuple) # Perform the insert
        logconn.commit()
    except Error as e:
        print(f"The error '{e}' occurred")
        return render_template("signup.html", error="Username is taken")
    return render_template("login.html")

@app.route("/home")
def home():
    if session['userid']=="":
        return login()
    logconn=create_connection("databases/database.sqlite")
    currentCursor=logconn.cursor()
    sqlSelect="SELECT * FROM userPosts"
    try:
        currentCursor.execute(sqlSelect)
        rows=currentCursor.fetchall()
    except:
        return render_template("home.html")
    postList=[]
    for post in rows:
        # post is a tuple representing a row from the userPosts table
        tempDict={"id":post[0], "title":post[2], "author":post[1], "body":post[3], "formOfLit":post[4], "genre":post[5], "likes":post[6], "likedBy":post[7]}
        postList.append(tempDict)
    postList.reverse()
    return render_template("home.html", my_list=postList)

@app.route("/featured")
def featured():
    if session['userid']=="":
        return login()
    logconn=create_connection("databases/database.sqlite")
    currentCursor=logconn.cursor()
    sqlSelect="SELECT * FROM userPosts"
    try:
        currentCursor.execute(sqlSelect)
        rows=currentCursor.fetchall()
    except:
        return render_template("featured.html")
    postList=[]
    for post in rows:
        # post is a tuple representing a row from the userPosts table
        tempDict={ "id":post[0], "title":post[2], "author":post[1], "body":post[3], "formOfLit":post[4], "genre":post[5], "likes":post[6], "likedBy":post[7]}
        postList.append(tempDict)
    postList=sorted(postList, key=lambda i: i["likes"], reverse=True)
    return render_template("featured.html", my_list=postList)

@app.route("/newest")
def newest():
    return render_template("featured.html")

@app.route("/create")
def create():
    form = NewPost()
    return render_template("create.html", form=form)

@app.route("/posted", methods=['GET','POST'])
def posted():
    title = request.form['title']
    body = request.form['body']
    formoflit = request.form['formoflit']
    genre = request.form['genre']
    logconn=create_connection("databases/database.sqlite")
    currentCursor=logconn.cursor()
    sqlCreateTable="""CREATE TABLE IF NOT EXISTS userPosts (
                        postID INTEGER PRIMARY KEY AUTOINCREMENT,
                        userID text NOT NULL,
                        title text NOT NULL,
                        body text NOT NULL,
                        formoflit text NOT NULL,
                        genre text NOT NULL,
                        likes integer NOT NULL,
                        likedBy text NOT NULL
                    ); """
    currentCursor.execute(sqlCreateTable)
    logconn.commit()
    sqlInsert="""INSERT INTO userPosts(userID, title, body, formoflit, genre, likes, likedBy)
                VALUES(?,?,?,?,?,0,"")"""
    userID=session['userid'] # Should pull the user's id from the session cookie
    postTuple=(userID,title,body,formoflit,genre)
    try:
        currentCursor.execute(sqlInsert,postTuple) # Perform the insert
        logconn.commit()
    except Error as e:
        print(f"The error '{e}' occurred")
    return home()


@app.route("/like/<id>")
def like(id):
    logconn = create_connection("databases/database.sqlite")
    currentCursor = logconn.cursor()
    sqlSelect = "SELECT * FROM userPosts WHERE postID = ?"
    try:
        currentCursor.execute(sqlSelect,id)
        rows = currentCursor.fetchall()
    except:
        return featured()
    if rows[0][7].find(session['userid']+",")!=-1:
        return home()
    new_likes = int(rows[0][6]) + 1
    likeTuple = (new_likes,id)
    likedTuple=(rows[0][7]+session['userid']+",",id)
    sqlInsertOne = """ UPDATE userPosts SET likes = ? WHERE postID = ? """
    sqlInsertTwo=""" UPDATE userPosts SET likedBy = ? WHERE postID = ? """
    try:
        currentCursor.execute(sqlInsertOne, likeTuple)
        currentCursor.execute(sqlInsertTwo, likedTuple)
        logconn.commit()
    except Exception as e:
        print(e)
        return featured()
    return home()

@app.route("/unlike/<id>")
def unlike(id):
    logconn = create_connection("databases/database.sqlite")
    currentCursor = logconn.cursor()
    sqlSelect = "SELECT * FROM userPosts WHERE postID = ?"
    try:
        currentCursor.execute(sqlSelect,id)
        rows = currentCursor.fetchall()
    except:
        return featured()
    new_likes = int(rows[0][6]) - 1
    likeTuple = (new_likes,id)
    newLikedList=rows[0][7]
    posOfUnliker=newLikedList.find(session['userid'])
    newLikedList=newLikedList[:posOfUnliker]+newLikedList[posOfUnliker+len(session['userid']+","):]
    likedTuple=(newLikedList,id)
    sqlInsertOne = """ UPDATE userPosts SET likes = ? WHERE postID = ? """
    sqlInsertTwo=""" UPDATE userPosts SET likedBy = ? WHERE postID = ? """
    try:
        currentCursor.execute(sqlInsertOne, likeTuple)
        currentCursor.execute(sqlInsertTwo, likedTuple)
        logconn.commit()
    except:
        print(new_likes,id)
        return featured()
    return home()


if __name__ == '__main__':
    app.run(debug=True)
