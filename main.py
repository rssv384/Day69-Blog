from datetime import date
from functools import wraps

from flask import (Flask, abort, flash, redirect, render_template, request,
                   url_for)
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import (LoginManager, UserMixin, current_user, login_user,
                         logout_user)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from werkzeug.security import check_password_hash, generate_password_hash

from forms import NewPostForm, RegisterForm, LoginForm, CommentForm

# SETUP FLASK APP
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)
ckeditor = CKEditor()
ckeditor.init_app(app)

# CONFIGURE FLASK-LOGIN
login_manager = LoginManager()
login_manager.init_app(app)

# CONFIG GRAVATAR
# Source: https://flask-gravatar.readthedocs.io/en/latest/#usage
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


# Create user_loader callback
@login_manager.user_loader
def load_user(user_id: int):
    return db.get_or_404(User, user_id)


# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
db = SQLAlchemy()
db.init_app(app)


# CONFIGURE TABLES
# User table
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(254), unique=True)
    password = db.Column(db.String())
    name = db.Column(db.String(100))

    # === Parent 1:N Relationship ===
    comments = relationship("Comment", back_populates="comment_author")


# BlogPost table
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    # === Parent 1:N Relationship ===
    comments = relationship("Comment", back_populates="parent_post")


# Comment table
class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)

    # === Child 1:N Relationship (User -> Comment) ===
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")

    # === Child 1:N Relationship (BlogPost -> Comment)===
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")


# CREATE TABLE SCHEMAS IN DB. COMMENT OUT AFTER FIRST RUN
with app.app_context():
    db.create_all()


# Decorator function to allow only admin to create and delete posts
def admin_only(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        # If current user is not admin or authenticated, abort with 403 error
        if not current_user.is_authenticated or current_user.id != 1:
            return abort(code=403)
        # Otherwise, call route function
        return function(*args, **kwargs)
    return decorated_function


# APP ROUTES
# Homepage
@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template('index.html', all_posts=posts)


# New user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        # Check that the email isn't already in the DB
        result = db.session.execute(
            db.select(User).where(User.email == register_form.email.data))
        user = result.scalar()
        if user:
            flash('E-mail has already been registered.')
            return redirect(url_for('login'))
        # Hash password
        password_hash = generate_password_hash(
            password=register_form.password.data,
            method='pbkdf2:sha256', salt_length=8
        )
        new_user = User(
            email=register_form.email.data,
            name=register_form.name.data,
            password=password_hash
        )
        db.session.add(new_user)
        db.session.commit()

        # Login user after registration
        login_user(new_user)
        # Redirect to homepage
        return redirect(url_for('get_all_posts'))
    return render_template('register.html', form=register_form)


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        email = login_form.email.data
        password = login_form.password.data
        # Get user by email
        result = db.session.execute(
            db.select(User).where(User.email == email))
        user = result.scalar()
        # Check for e-mail not in DB or incorrect password, else login
        if user is None:
            flash("E-mail doesn't exist. Please, try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Incorrect password. Please, try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('get_all_posts'))

    return render_template('login.html', form=login_form)


# Logout
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


# TODO: Allow logged-in users to comment on posts
@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        # If user isn't logged in, redirect to login page
        if not current_user.is_authenticated:
            flash('You must login in order to submit comments.')
            return redirect(url_for('login'))
        # Otherwise, add comment to DB
        new_comment = Comment(
            text=comment_form.text.data,
            comment_author=current_user,
            parent_post=requested_post
        )
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('show_post', post_id=post_id))
    return render_template('post.html', post=requested_post, form=comment_form)


# Use a decorator so only an admin user can create a new post
@app.route('/new-post', methods=['GET', 'POST'])
@admin_only
def add_new_post():
    add_form = NewPostForm()
    if add_form.validate_on_submit():
        new_post = BlogPost(
            title=add_form.title.data,
            subtitle=add_form.subtitle.data,
            date=date.today().strftime('%B %d, %Y'),
            body=add_form.body.data,
            author=add_form.author.data,
            img_url=add_form.img_url.data
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('get_all_posts'))
    return render_template('make-post.html', form=add_form)


# Use a decorator so only an admin user can edit a post
@app.route('/edit-post/<int:post_id>', methods=['GET', 'POST'])
@admin_only
def edit_post(post_id: int):
    # Get post to edit
    post = db.get_or_404(
        BlogPost, post_id, description='Sorry, we could not find that post.')
    # Create edit form by populating the post creation form
    edit_form = NewPostForm(
        title=post.title,
        subtitle=post.subtitle,
        author=post.author,
        img_url=post.img_url,
        body=post.body
    )
    # On POST, update all fields except the date
    if edit_form.validate():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.body = edit_form.body.data
        post.author = edit_form.author.data
        post.img_url = edit_form.img_url.data
        db.session.commit()
        # Redirect to post page
        return redirect(url_for('show_post', post_id=post.id))
    return render_template('make-post.html', form=edit_form, is_editing=True)


# Use a decorator so only an admin user can delete a post
@admin_only
@app.route('/delete/<int:post_id>')
def delete_post(post_id: int):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


# About page
@app.route('/about')
def about():
    return render_template('about.html')


# Contact page
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        return render_template('contact.html', message_sent=True)
    return render_template('contact.html', message_sent=False)


if __name__ == '__main__':
    app.run(debug=True, port=5002)
