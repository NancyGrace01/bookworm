from flask import Flask

from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_mail import Mail,Message


csrf=CSRFProtect()

#Instatiating an object of flask so that it can be easily imported by other modules in the package


 # This protects all our (POST) from csrf attacks whether we are using Flaskform or not..
mail=Mail()

def create_app():
   """Keep all imports that may cause conflict within this function so that anytime we write from bookapp..import .. none of these statements will be executed"""
   from bookapp.models import db
   app = Flask(__name__,instance_relative_config=True)
   
   app.config.from_pyfile("config.py",silent=True)
   db.init_app(app)
   migrate = Migrate(app,db)
   csrf.init_app(app)
   mail.init_app(app)
   return app

app = create_app()

#Loading the routes
from bookapp import admin_routes, user_routes
from bookapp.forms import *