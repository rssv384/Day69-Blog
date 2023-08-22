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

# Import your forms from the forms.py
from forms import NewPostForm

# SETUP FLASK APP
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)
ckeditor = CKEditor()
ckeditor.init_app(app)

# TODO: Configure Flask-Login


# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy()
db.init_app(app)


# CONFIGURE TABLES
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)


# TODO: Create a User table for all your registered users.


# CREATE TABLE SCHEMAS IN DB. COMMENT OUT AFTER FIRST RUN
# with app.app_context():
#     db.create_all()


# TODO: Use Werkzeug to hash the user's password when creating a new user.
@app.route('/register')
def register():
    return render_template("register.html")


# TODO: Retrieve a user from the database based on their email.
@app.route('/login')
def login():
    return render_template("login.html")


@app.route('/logout')
def logout():
    return redirect(url_for('get_all_posts'))


@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts)


# TODO: Allow logged-in users to comment on posts
@app.route("/post/<int:post_id>")
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    return render_template("post.html", post=requested_post)


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


if __name__ == "__main__":
    app.run(debug=True, port=5002)
