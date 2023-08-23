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

from forms import NewPostForm, RegisterForm, LoginForm

# SETUP FLASK APP
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)
ckeditor = CKEditor()
ckeditor.init_app(app)

# CONFIGURE FLASK-LOGIN
login_manager = LoginManager()
login_manager.init_app(app)


# Create user_loader callback
@login_manager.user_loader
def load_user(user_email: int):
    return db.get_or_404(User, user_email)


# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy()
db.init_app(app)


# CONFIGURE TABLES
class BlogPost(db.Model):
    __tablename__ = 'blog_posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)


# Create a User table with UserMixin.
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    email = db.Column(db.String(250), primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    password = db.Column(db.String(250), nullable=False)

    # Override UserMixin get_id() method to return the User email
    # instead when login_user() is called.
    def get_id(self):
        return self.email


# CREATE TABLE SCHEMAS IN DB. COMMENT OUT AFTER FIRST RUN
# with app.app_context():
#     db.create_all()


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
@app.route('/post/<int:post_id>')
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    return render_template('post.html', post=requested_post)


# TODO: Use a decorator so only an admin user can create a new post
@app.route('/new-post', methods=['GET', 'POST'])
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


# TODO: Use a decorator so only an admin user can edit a post
@app.route('/edit-post/<int:post_id>', methods=['GET', 'POST'])
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


# TODO: Use a decorator so only an admin user can delete a post
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
