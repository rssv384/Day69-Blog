from flask_wtf import FlaskForm
from flask_ckeditor import CKEditorField
from wtforms import StringField, SubmitField
from wtforms.validators import URL, DataRequired


class NewPostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    subtitle = StringField('Subtitle', validators=[DataRequired()])
    author = StringField('Author', validators=[DataRequired()])
    img_url = StringField('Background Image URL',
                          validators=[DataRequired(), URL()])
    body = CKEditorField('Post Content', validators=[DataRequired()])
    submit = SubmitField('Submit Post')


# TODO: Create a RegisterForm to register new users


# TODO: Create a LoginForm to login existing users


# TODO: Create a CommentForm so users can leave comments below posts
