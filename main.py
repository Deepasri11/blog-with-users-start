from flask import Flask, render_template, redirect, url_for, flash,request
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm,RegisterForm,LoginForm,CommentForm
from flask_gravatar import Gravatar
from functools import wraps
from flask import abort
from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base





Base = declarative_base()
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #If id is not 1 then return abort with 403 error
        if not current_user.is_authenticated or current_user.id != 1:
            return abort(403)
        #Otherwise continue with the route function
        return f(*args, **kwargs)
    return decorated_function



app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///basic.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

loginmanager=LoginManager()
loginmanager.init_app(app)


gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


##CONFIGURE TABLES
#
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))

    # This will act like a List of BlogPost objects attached to each User.
    # The "author" refers to the author property in the BlogPost class.
    posts = relationship("BlogPost", back_populates="author")
    comments=relationship("Comment",back_populates="comment_author")
# db.create_all()


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)

    # Create Foreign Key, "users.id" the users refers to the tablename of User.
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    # Create reference to the User object, the "posts" refers to the posts protperty in the User class.
    author = relationship("User", back_populates="posts")

    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    comments=relationship("Comment",back_populates="parent_post")


# db.create_all()
class Comment(db.Model):
    __tablename__="comments"
    id=db.Column(db.Integer,primary_key=True)
    author_id=db.Column(db.Integer,db.ForeignKey("users.id"))
    comment_author=relationship("User",back_populates="comments")
    post_id=db.Column(db.Integer,db.ForeignKey("blog_posts.id"))
    parent_post=relationship("BlogPost",back_populates="comments")
    text=db.Column(db.Text,nullable=False)
# db.create_all()
# class User(UserMixin, db.Model):
#     __tablename__ = "users"
#     id = db.Column(db.Integer, primary_key=True)
#     email = db.Column(db.String(100), unique=True)
#     password = db.Column(db.String(100))
#     name = db.Column(db.String(100))
#     posts = relationship("BlogPost", back_populates="author")
#     comments = relationship("Comment", back_populates="comment_author")
# db.create_all()
#
# class BlogPost(db.Model):
#     __tablename__ = "blog_posts"
#     id = db.Column(db.Integer, primary_key=True)
#     author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
#     author = relationship("User", back_populates="posts")
#     title = db.Column(db.String(250), unique=True, nullable=False)
#     subtitle = db.Column(db.String(250), nullable=False)
#     date = db.Column(db.String(250), nullable=False)
#     body = db.Column(db.Text, nullable=False)
#     img_url = db.Column(db.String(250), nullable=False)
#
#     # ***************Parent Relationship*************#
#     comments = relationship("Comment", back_populates="parent_post")
# db.create_all()
#
#
# class Comment(db.Model):
#     __tablename__ = "comments"
#     id = db.Column(db.Integer, primary_key=True)
#     author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
#     comment_author = relationship("User", back_populates="comments")
#
#     # ***************Child Relationship*************#
#     post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
#     parent_post = relationship("BlogPost", back_populates="comments")
#     text = db.Column(db.Text, nullable=False)
#
#
# db.create_all()

ADMIN=User.query.filter_by(id=1).first()
@loginmanager.user_loader
def load_user(user_id):
    return User.query.get(user_id)



@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    ADMIN = User.query.filter_by(id=1).first()
    is_admin=False
    if current_user==ADMIN:
        is_admin=True
    return render_template("index.html", all_posts=posts,logged_in=current_user.is_authenticated,is_admin=is_admin)


@app.route('/register',methods=["POST","GET"])
def register():

    registerform = RegisterForm()
    if request.method=="POST":
        if registerform.validate_on_submit():
            email = registerform.email.data
            name = registerform.name.data
            password = registerform.password.data
            user=User.query.filter_by(email=email).first()
            if not user:
                new_user=User(email=email,name=name,
                              password=generate_password_hash(password,method='pbkdf2:sha256',salt_length=8))
                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for('get_all_posts'))
            else:
                loginform = LoginForm()
                error = "User already exists in that email.Please try to login with that email!!"
                return render_template("login.html", form=loginform, error=error)


    return render_template("register.html",form=registerform)


@app.route('/login',methods=["POST","GET"])
def login():
    loginform=LoginForm()
    if request.method=="POST":
        if loginform.validate_on_submit():
            email=loginform.email.data
            password=loginform.password.data
            user=User.query.filter_by(email=email).first()
            if user:
                if check_password_hash(user.password,password):
                    login_user(user)
                    flash("Logged in successfully!")
                    return redirect(url_for('get_all_posts'))
                else:
                    error="Invalid password .please try again!"
                    return render_template("login.html",form=loginform,error=error)
            else:
                error = "The user not exists.Please provide valid credentials!"
                return render_template("login.html", form=loginform, error=error)

    return render_template("login.html",form=loginform)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>",methods=["POST","GET"])
def show_post(post_id):
    loginform = LoginForm()
    requested_post = BlogPost.query.get(post_id)
    commentform=CommentForm()
    is_admin=False
    if current_user==ADMIN:
        is_admin=True
    if request.method=="POST":
        if commentform.validate_on_submit():
            if current_user.is_authenticated:
                new_comment=Comment(text=commentform.comment.data,author_id=current_user.id,post_id=requested_post.id)
                db.session.add(new_comment)
                db.session.commit()
            else:
                error="You need to Login to add your comments."
                return render_template("login.html", form=loginform, error=error)


    return render_template("post.html", post=requested_post,is_admin=is_admin,logged_in=current_user.is_authenticated,form=commentform )


@app.route("/about")
def about():
    return render_template("about.html",logged_in=current_user.is_authenticated)


@app.route("/contact")
def contact():
    return render_template("contact.html",logged_in=current_user.is_authenticated)


@app.route("/new-post", methods=["GET", "POST"])
# Mark with decorator
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))

    return render_template("make-post.html", form=form, current_user=current_user)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=current_user,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form, is_edit=True, current_user=current_user)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(debug=True)
