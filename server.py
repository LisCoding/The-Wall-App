from flask import Flask, request, redirect, render_template, session, flash
from mysqlconnection import MySQLConnector
import md5 # imports the md5 module to generate a hash
from myemail import Email
from name import Name
from password import Password

app = Flask(__name__)
app.secret_key = 'KeepItSecretKeepItSafe'
mysql = MySQLConnector(app,'the_wall')

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/register', methods=["POST"])
def register_user():
    try:
        f_name = request.form["f_name"]
        l_name = request.form["l_name"]
        email = request.form["email"]
        Name(f_name, l_name)
        Email(email)
        pwd = request.form["pwd"]
        confi_pwd = request.form["confi_pwd"]
        Password(pwd,confi_pwd)
        pwd = md5.new(pwd).hexdigest();
        query = "INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VAlUES(:first_name, :last_name, :email, :password, NOW(), NOW())"
        data = {
            "first_name": f_name,
            "last_name": l_name,
            "email": email,
            "password": pwd
        }
        mysql.query_db(query, data)
        return redirect("/wall")
    except Exception as e:
        flash(str(e))
    return redirect("/")

@app.route('/login', methods=["POST"])
def login_user():
    email = request.form["email"]
    password = request.form["pwd"]
    user_query = "SELECT * FROM users WHERE users.email = :email LIMIT 1"
    query_data = {'email': email}
    user = mysql.query_db(user_query, query_data)

    if len(user) != 0:
        encrypted_password = md5.new(password).hexdigest();
        if user[0]["password"] == encrypted_password:
        # this means we have a successful login!
            session["user_id"] = user[0]["id"]
            return redirect("/wall")
        else:
            flash("******INVALID PASSWORD******")
            return redirect("/")
    else:
        flash("******INVALID EMAIL******")
        return redirect("/")

@app.route('/wall')
def home_page():

    user_query = """SELECT post_author.id, posts.id,
    CONCAT (post_author.first_name,' ' ,post_author.last_name)
    AS post_author_full_name,
    CONCAT (comment_author.first_name,' ' ,comment_author.last_name) AS comment_author_full_name,
    DATE_FORMAT(posts.created_at,'%M %d, %Y ') as date,
    DATE_FORMAT(comments.created_at,'%M %d, %Y ') as comment_date,
    posts.content AS post, comments.content AS response
    FROM posts
    LEFT JOIN comments ON posts.id = comments.post_id
    LEFT JOIN users AS post_author ON posts.user_id = post_author.id
    LEFT JOIN users AS comment_author ON comment_author.id = comments.user_id
    ORDER BY posts.created_at DESC, comments.created_at """
    posts = mysql.query_db(user_query)
    prev_post = None
    result = []
    # map array of comments into array of posts, where each post
    # has an array of comments:
    for post in posts:
        comment_data = {"body":post["response"],"author":post["comment_author_full_name"], "comment_date":post["comment_date"]}
        if prev_post == None or prev_post["id"] != post["id"]:
            if post["response"] != None:
                post["comment"] = [comment_data]
            else:
                post["comment"] = []
            result.append(post)
            prev_post = post
        else:
            if post["response"] != None:
                all_comments = prev_post["comment"]
                all_comments.append(comment_data)
                prev_post["comment"] = all_comments

    return render_template("wall.html", posts=result)

@app.route('/wall/message', methods=["POST"])
def post_message():
    content = request.form["content"]
    user_id = session['user_id']
    query = "INSERT INTO posts (content, created_at, updated_at, user_id) VAlUES(:content, NOW(), NOW(), :user_id)"
    data = {
        "content":content,
        "user_id":user_id,
    }
    user_id = mysql.query_db(query, data)
    return redirect("/wall")

@app.route('/wall/comment/<id>', methods=["POST"])
def post_comment(id):
    comment = request.form["content"]
    query = "INSERT INTO comments (content, user_id, post_id, created_at, updated_at) VAlUES(:content,:user_id, :post_id, NOW(), NOW())"
    data = {
        "content":comment,
        "post_id": id,
        "user_id":session['user_id'],
    }
    mysql.query_db(query, data)
    return redirect("/wall")
app.run(debug=True)
