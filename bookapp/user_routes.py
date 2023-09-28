import random,string,os
import json,requests
from functools import wraps

from flask import render_template,request,abort,redirect,flash,make_response,url_for,session
from werkzeug.security import generate_password_hash,check_password_hash


#Local Imports
from bookapp import app, csrf,mail,Message
from bookapp.models import *
from bookapp.forms import *
from instance.config import USER_PROFILE_PATH




def login_required(f):
    @wraps(f)#this ensures that details(meta data) about the original function f, that is being decorated is still available
    def login_check(*args,**kwargs):
        if session.get("userloggedin") != None:
            return f(*args,**kwargs)
        else:
            flash("Access Denied")
            return redirect("/login")
    return login_check


def generate_string(howmany):#call this function as generate_string(10)
    x = random.sample(string.digits,howmany)
    return ''.join(x)


@app.route("/landing")
@login_required
def landing_page():
     refno = session.get('trxno')
     transaction_deets = db.session.query(Donation).filter(Donation.don_refno==refno).first()
     url="https://api.paystack.co/transaction/verify/"+transaction_deets.don_refno
     headers = {"Content-Type": "application/json","Authorization":"Bearer sk_test_c8d6c27640efff9fb2e0da94540f342a71ca1371"}
     response = requests.get(url,headers=headers)
     rspjson = json.loads(response.text)

     if rspjson['status'] == True:
        paystatus = rspjson['data']['gateway_response']
        transaction_deets.don_status = 'Paid'
        db.session.commit()
        return redirect("/dashboard")#paystack payment page will load
    
     else:        
        return redirect('Payment failed')
     

    
   



@app.route("/initialize/paystack/")
@login_required
def initialize_paystack():
    deets = User.query.get(session['userloggedin'])
    #transaction details
    refno = session.get('trxno')
    transaction_deets = db.session.query(Donation).filter(Donation.don_refno==refno).first()
    #make a curl request to the paystack endpoint
    
    url="https://api.paystack.co/transaction/initialize"
    
    headers = {"Content-Type": "application/json","Authorization":"Bearer sk_test_c8d6c27640efff9fb2e0da94540f342a71ca1371"}
    data={"email":deets.user_email, "amount":transaction_deets.don_amt,"reference":refno}
    response = requests.post(url,headers=headers,data=json.dumps(data))
    #extract json from the response coming from paystack
    rspjson = response.json()
    # return rspjson
    if rspjson['status'] == True:
        redirectURL = rspjson['data']['authorization_url']
        return redirect(redirectURL)#paystack payment page will load
    
    else:
        flash("Please complete the form again")
        return redirect('/donate/')



@app.route("/donate/",methods=["POST","GET"])
@login_required
def donation():
    dform = DonateForm()
    if request.method=="GET":

        deets = db.session.query(User).get(session['userloggedin'])
        return render_template("user/donation_form.html",dform=dform,deets=deets)

    else:
        if dform.validate_on_submit():
            #retrieve form data
            amt = float(dform.amt.data) * 100
            donor = dform.fullname.data
            email = dform.email.data
            #generate a transaction reference number
            ref = 'BW' + str(generate_string(8))

            #insert into db(save details of trx(transaction))
            donation = Donation(don_amt=amt,don_userid=session['userloggedin'],don_email=email,don_fullname=donor,don_status='pending',don_refno=ref)
            db.session.add(donation)
            db.session.commit()

            #save the reference no in session
            session['trxno'] = ref
            
            #redirect to a confirmation page
            return redirect("/confirm_donation")
        else:
            deets = db.session.query(User).get(session['userloggedin'])
            return render_template("user/donation_form.html",dform=dform,deets=deets)


@app.route("/confirm_donation")
@login_required
def confirm_donation():
    '''we want to display the details of the transaction saved from the previous page'''
    deets = db.session.query(User).get(session['userloggedin'])
    if session.get('trxno') == None:#means they are visiting here directly
        flash("Please Complete this form",category='error')
        return redirect("/donate")
    else:
        donation_deets = Donation.query.filter(Donation.don_refno==session['trxno']).first()
        return render_template("user/donation_confirmation.html",donation_deets=donation_deets,deets=deets)



@app.route("/sendmail/")
def send_email():
    file = open('requirements.txt')
    msg=Message(subject="Adding Heading to Email from BookWorm",sender="From BookWorm Website",recipients=["nancygrace92@gmail.com"])

    msg.html="""<h1>Welcome Home</h1>
    <img src='https://images.pexels.com/photos/18386361/pexels-photo-18386361/free-photo-of-fashion-love-people-woman.jpeg?auto=compress&cs=tinysrgb&w=600&lazy=load'><hr>"""

    msg.attach("saved_as.txt","application/text",file.read())
    mail.send(msg)
    return "done"

@app.route("/ajaxopt/",methods=["POST","GET"])
def ajax_options():
    cform = ContactForm()
    if request.method=="GET":

        return render_template("user/ajax_options.html",cform=cform)
    else:
        email = request.form.get('email')
        return f"Thank you, {email} has been submitted"

@app.route("/checkusername/")
def checkusername():
    user = request.args.get("m")
    user_mail = db.session.query(User).filter(User.user_email==user).first()
    if user_mail:
            return "Email taken"
    else:
        return "Email is okay, go ahead"


@app.route("/lga/<stateid>")
def load_lgas(stateid):
    records = db.session.query(Lga).filter(Lga.state_id==stateid).all()
    str2return = "<select class='form-control' name='lga'>"
    for r in records:
        optstr = f"<option value='{r.lga_id}'>" + r.lga_name+"</option>"
        str2return = str2return + optstr

    str2return=str2return+ "</select>"
    return str2return

@app.route("/dependent/")
def dependent_dropdown():
    states = db.session.query(State).all()
    return render_template("user/show_states.html",states=states)

@app.route("/contact/")
def ajax_contact():
    data = 'I am a string coming from the server' #may also be fetched from db
    return render_template("user/ajax_test.html",data=data)

@app.route("/submission/",methods=["POST","GET"])
def ajax_submission():
    """This route will ve visited by ajax silently"""
    # user = request.args.get('f')
    user = request.form.get('f')
    if user != "" and user != None:
        return f"Thank you {user} for completing the form"
    else:
        return "Please complete the form"
    

@app.route("/favourite")
def favourite_topics():
    bootcamp = {'name':'Olusegun','topics':['html','css','python']}
    cats = Category.query.all()
    # category = []
    # for c in cats:
    #     category.append(c.cat_name)

    category=[c.cat_name for c in cats]#list comprehension
    return json.dumps(category,indent=3)



@app.route("/profile/",methods = ["GET", "POST"])
@login_required
def edit_profile():
    id = session.get('userloggedin')
    userdeets = db.session.query(User).get(id)
    pform = ProfileForm()
    if request.method == "GET":
        return render_template("user/edit_profile.html",pform=pform,userdeets=userdeets)
    else:
        if pform.validate_on_submit():
            fullname = request.form.get('fullname')            
            userdeets.user_fullname = fullname
            db.session.commit()
            flash("Profile updated")
            return redirect(url_for('dashboard'))
        else:
            return render_template("user/changedp.html", pform=pform,userdeets=userdeets)

@app.route("/changedp/", methods=["GET","POST"])
@login_required
def changedp():
    id = session.get('userloggedin')
    userdeets = db.session.query(User).get(id)
    dpform = Dpform()   
    if request.method =="GET":
        return render_template("user/changedp.html",dpform=dpform,userdeets=userdeets)
    else:
        if dpform.validate_on_submit():
            pix = request.files.get('dp')
            filename = pix.filename
            pix.save(app.config['USER_PROFILE_PATH'] +filename)
            userdeets.user_pix = filename
            db.session.commit()
            flash("Profile picture updated")
            return redirect(url_for('dashboard'))
        else:
            return render_template("user/changedp.html", dpform=dpform,userdeets=userdeets)

@app.route("/viewall/")
@login_required
def viewall():
    books = db.session.query(Book).filter(Book.book_status=="1").all()
    return render_template("user/viewall.html",books=books)


@app.route("/logout")
def logout():
    if session.get('userloggedin') !=None:
        session.pop('userloggedin',None)
    return redirect("/")


@app.route("/dashboard")
@login_required
def dashboard():
    
        id = session.get('userloggedin')
        userdeets = User.query.get(id)
        return render_template("user/dashboard.html",userdeets=userdeets)
    

@app.route("/login",methods=["POST","GET"])
def login():
    if request.method=='GET':
        return render_template('user/loginpage.html')
    
    else:
        email = request.form.get('email')
        pwd = request.form.get('pwd')
        deets = db.session.query(User).filter(User.user_email==email).first()
        if deets != None:
            hashed_pwd = deets.user_pwd
            if check_password_hash(hashed_pwd, pwd) == True:
                session['userloggedin'] = deets.user_id
                return redirect("/dashboard")
                
            else:
                flash("Invalid credentials, try again")
                return redirect("/login")
        else:

            flash("Invalid credentials, try again")
            return redirect("/login")
    

@app.route("/register/",methods=['GET','POST'])
def register():
    regform=RegForm()
    if request.method=="GET":
        return render_template("user/signup.html",regform=regform)

    else:
        if regform.validate_on_submit():
            #retrieve the form data and insert to user table
            fullname = request.values.get("fullname") #or regform.fullname.data      
            email = request.form.get("email")
            pwd = request.form.get("pwd")  
            hashed_pwd = generate_password_hash(pwd)      
            users = User(user_fullname=fullname,user_email=email,user_pwd=hashed_pwd)
            db.session.add(users)
            db.session.commit()
            flash("An account has been created for you. Please login")
            return redirect('/login')
        else:
            return render_template("user/signup.html",regform=regform)
            
@app.route("/submit_review/",methods=["POST"])
@login_required
def submit_review():
     title = request.form.get('title')  
     content = request.form.get('content')
     userid = session['userloggedin']
     book = request.form.get('book')
     br = Reviews(rev_title=title,rev_text=content,rev_userid=userid,rev_bookid=book)
     db.session.add(br)
     db.session.commit()

     retstr = f"""<article class="blog-post">
            <h5 class="blog-post-title">{title}</h5>
            <p class="blog-post-meta">Reviewed just now by <a href="#">{br.reviewby.user_fullname}</a></p>
            <p>{content}</p>
            <hr>
            </article>"""
     return retstr


@app.route("/myreviews/")
@login_required
def myreviews():
    id = session['userloggedin']
    userdeets = db.session.query(User).get(id)
    return render_template("user/myreviews.html",userdeets=userdeets)

@app.route("/books/details/<id>")

def book_details(id):
    book = Book.query.get_or_404(id)
    return render_template("user/reviews.html",book=book)

@app.route("/")
def home_page():
    books = db.session.query(Book).filter(Book.book_status=='1').limit(4).all()
    #connect to the endpoint http://127.0.0.1:5000/api/v1.0/listall to collect data of books
    #pass it to the template and display on the template
    try:
        response = requests.get('http://127.0.0.1:5000/api/v1.0/listall')
        rsp = json.loads(response.text)
    except:
        rsp = None #if the server is unreachable...
   
    return render_template("user/home_page.html",books=books,rsp=rsp)


@app.after_request
def after_request(response):
   #To solve the problem of loggedout user's details being cached in the browser
   response.headers["Cache-Control"]="no-cache, no-store, must-revalidate"
   return response
