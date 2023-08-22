from flask_ckeditor import CKEditorField
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import URL, DataRequired, Email, Length


class NewPostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    subtitle = StringField('Subtitle', validators=[DataRequired()])
    author = StringField('Author', validators=[DataRequired()])
    img_url = StringField('Background Image URL',
                          validators=[DataRequired(), URL()])
    body = CKEditorField('Post Content', validators=[DataRequired()])
    submit = SubmitField('Submit Post')


# TODO: Create a RegisterForm to register new users
class RegisterForm(FlaskForm):
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    name = StringField('Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[
                             DataRequired(), Length(min=8)])
    submit = SubmitField('Register')


# TODO: Create a LoginForm to login existing users


# TODO: Create a CommentForm so users can leave comments below posts
