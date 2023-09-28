from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, SubmitField, TextAreaField, PasswordField
from wtforms.validators import Email, DataRequired, EqualTo, Length

class RegForm(FlaskForm):
   fullname = StringField("Fullname",validators=[DataRequired(message="The firstname is a must")])   
   email = StringField("Email",validators=[Email(message="Invalid Email Format"),DataRequired(message="Email must be supplied")])
   pwd = PasswordField("Enter Password",validators=[DataRequired()])
   confirmpwd = PasswordField("Confirm Password",validators=[EqualTo('pwd',message="Let the two password match")])  
   btnsubmit = SubmitField("Register!")


class Dpform(FlaskForm):
   dp = FileField("Upload a picture",validators=[FileRequired(),FileAllowed(['jpg','png','jpeg'])])
   btnupload = SubmitField("Upload Picture")

class ProfileForm(FlaskForm):
   fullname = StringField("Fullname",validators=[DataRequired(message="Fullname is a must")])   
   btnsubmit = SubmitField("Update Profile")

class ContactForm(FlaskForm):
   email = StringField("Email",validators=[Email(message="Invalid Email Format"),DataRequired(message="Email must be supplied")])
   btnsubmit = SubmitField("Subscribe...")

class DonateForm(FlaskForm):
   fullname = StringField("Fullname",validators=[DataRequired()])
   email = StringField("Email",validators=[Email(message="Invalid Email Format"),DataRequired()])
   amt = StringField("Amount",validators=[DataRequired()])
   btnsubmit = SubmitField("Continue")