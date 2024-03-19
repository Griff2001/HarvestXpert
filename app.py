import pytz
from flask import Flask, render_template, request, flash, redirect, url_for, session, jsonify
import numpy as np
from markupsafe import Markup
from flask_migrate import Migrate
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user, LoginManager, login_manager, UserMixin
from utils.fertilizer import fertilizer_dict
from flask_sqlalchemy import SQLAlchemy
import uuid
from datetime import datetime, timedelta
#from twilio.rest import Client  # Import the Twilio Client

# # Your Twilio credentials
# ACCOUNT_SID = 'AC862a2593d8664871712cda9b07333412'
# AUTH_TOKEN = 'b210f5faf3871055ab773a94460dabae'
# TWILIO_PHONE_NUMBER = '+12293608033'

# Setup Twilio client
# twilio_client = Client(ACCOUNT_SID, AUTH_TOKEN)

app = Flask(__name__)
app.secret_key = 'GrowFertile'  # for session encryption

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
Migrate(app, db, compare_type=True)
login_manager = LoginManager()
login_manager.login_view = 'index'
login_manager.init_app(app)



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(50), nullable=False)
   # phone = db.Column(db.String(20), nullable=True)  # Add phone number field


class Predictions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nitrogen = db.Column(db.Integer)
    potassium = db.Column(db.Integer)
    phosphorus = db.Column(db.Integer)
    user_id = db.Column(db.Integer)


class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_code = db.Column(db.String)
    user_id = db.Column(db.Integer)
    name = db.Column(db.String(50))


class Data(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nitrogen = db.Column(db.Integer)
    potassium = db.Column(db.Integer)
    phosphorus = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    device_id = db.Column(db.Integer)
    datetime = db.Column(db.DateTime, default=datetime.utcnow)



@app.route('/chart')
def chart():
    # Fetch data from the database
    device_id = request.args.get("device_id")
    # print(device_id)

    data = Data.query.filter_by(
        device_id=device_id).all()  # Assumes you have a 'Data' model with appropriate fields and SQLAlchemy configured

    # Parse data into a list of dictionaries

    nitrogen = {}
    phosphorus = {}
    potassium = {}
    for entry in data:
        # parsed_data["datetime"].append({entry.datetime.isoformat()})
        nitrogen[entry.datetime.strftime("%Y-%m-%d %H:%M:%S")] = entry.nitrogen
        potassium[entry.datetime.strftime("%Y-%m-%d %H:%M:%S")] = entry.potassium
        phosphorus[entry.datetime.strftime("%Y-%m-%d %H:%M:%S")] = entry.phosphorus

        # parsed_data["phosphorus"].append({entry.datetime.strftime("%Y-%m-%d"): entry.potassium})
        # parsed_data["potassium"].append({entry.datetime.strftime("%Y-%m-%d"): entry.potassium})
    parsed_data = {
        # "datetime": [],
        "nitrogen": nitrogen,
        "potassium": potassium,
        "phosphorus": phosphorus
    }
    # Return data as JSON
    return parsed_data


def datetimeformat(value, date_format='%A %d/%m/%Y %H:%M:%S'):
    if not value:
        return None

    local_timezone = pytz.timezone('Africa/Nairobi')
    local_time = value.replace(tzinfo=pytz.utc).astimezone(local_timezone)

    """Format a datetime object as a string."""
    return local_time.strftime(date_format)


app.jinja_env.filters['datetimeformat'] = datetimeformat


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/historic_data/<int:device_id>', methods=['GET'])
def historic_data(device_id):
    # Get the current page number and items per page from the query parameters
    page = request.args.get('page', 1, type=int)

    items_per_page = int(request.args.get('items_per_page', 10))

    # Query the database for data collected from the specified device ID
    data_list = Data.query.filter_by(device_id=device_id).order_by(Data.datetime.desc()).paginate(page=page,
                                                                                                  per_page=items_per_page)

    # Calculate the total number of pages
    pages = data_list.pages
    device_code = Device.query.get(device_id)

    return render_template('historic_data.html', device_id=device_id, page=page, device_code=device_code.device_code,
                           data_list=data_list, pages=pages, items_per_page=items_per_page)


@login_manager.user_loader
def load_user(user_id):
    # since the user_id is just the primary key of our user table, use it in the query for the user
    return User.query.get(int(user_id))


@app.route('/')
@app.route("/index.html")
def index():  # put application's code here
    # db.create_all()
    if current_user.is_authenticated:
        user_devices = Device.query.filter_by(user_id=current_user.id).all()
        return render_template('devices.html', devices=user_devices)

    return render_template("index.html")


def check_user_password(email, password):
    if not password or not email:
        return None
    user = User.query.filter_by(email=email).first()
    if not user:
        return None
    if check_password_hash(pwhash=user.password, password=password):
        return user


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if not password or not email:
            flash("Fill all required fields", "error")
            return redirect(url_for("index"))
        user = check_user_password(email=email, password=password)
        if not user:
            flash("Check your credentials and try again", "error")
            return redirect(url_for("index"))
            # Set session variables and redirect to homepage
        login_user(user=user, remember=True)
        flash('Logged in successfully!', 'success')
        user_devices = Device.query.filter_by(user_id=current_user.id).all()
        return render_template('devices.html', devices=user_devices)
        # return render_template("FertilizerRecommendation.html")
    return render_template("index.html")


@app.route("/signup", methods=["POST", "GET"])
def signup():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        # Process the signup data and save to database
        # Return a success message or redirect to another page
        if not name or not password or not email:
            flash("Fill all required fields", "error")
            return redirect(url_for("signup"))
        # Additional fields as necessary
        user = User.query.filter_by(email=email).first()
        if user:
            flash("Email already exists", "error")
            return redirect(url_for("signup"))
        hashed_password = generate_password_hash(password)
        new_user = User(email=email, password=hashed_password, name=name)
        db.session.add(new_user)
        db.session.commit()

        return render_template("index.html")
    return render_template("signup.html")


# /soil-data?device=080a3eaf-945c-4b14-8787-4f48cef3ed81&N=20&P=30&K=40
@app.route("/soil-data")
def soil_data():
    device_code = request.args.get("device")

    N = request.args.get("N")
    P = request.args.get("P")
    K = request.args.get("K")
    if not device_code and not N and not P and not K:
        return f"Provide all required data. Your data device_code: {device_code}, N: {N}, P: {P}, K: {K}"
    device_info = Device.query.filter_by(device_code=device_code).first()
    if not device_info:
        return f"Device id: {device_code} doesnt exists"
    new_data = Data(nitrogen=N, potassium=K, phosphorus=P, device_id=device_info.id, user_id=device_info.user_id)
    db.session.add(new_data)
    db.session.commit()
    return "OK"


@app.route('/create_device', methods=['POST'])
@login_required
def create_device():
    # Generate a UUID as the device ID
    device_id = str(uuid.uuid4())
    device_name = request.form.get("name")
    new_device = Device(device_code=device_id, user_id=current_user.id, name=device_name)
    db.session.add(new_device)
    db.session.commit()
    return render_template("FertilizerRecommendation.html", device_id=new_device.device_code)


# Flask route to display devices
@app.route('/devices')
@login_required
def devices():
    # Query devices from the database
    user_devices = Device.query.filter_by(user_id=current_user.id).all()
    return render_template('devices.html', devices=user_devices)


@app.route("/predictions")
def predictions():
    device_id = request.args.get("device_id")
    if not device_id:
        flash("Device not provided", "error")
    device_info = Device.query.get(device_id)
    if not device_info:
        flash("Device not found", "error")

    # Calculate datetime for one month ago from current datetime
    one_month_ago = datetime.utcnow() - timedelta(days=30)

    # Query data for the past one month for the given device_id
    data = Data.query.filter_by(device_id=device_id).filter(Data.datetime >= one_month_ago).all()
    if not data:
        flash("No data found for the device selected", "error")
        return redirect(request.referrer)

    # Calculate average of the values
    nitrogen_sum = 0
    potassium_sum = 0
    phosphorus_sum = 0
    count = 0
    for d in data:
        nitrogen_sum += d.nitrogen
        potassium_sum += d.potassium
        phosphorus_sum += d.phosphorus
        count += 1
    nitrogen_avg = nitrogen_sum / count if count > 0 else 0
    potassium_avg = potassium_sum / count if count > 0 else 0
    phosphorus_avg = phosphorus_sum / count if count > 0 else 0
    return redirect(url_for("fertilizer_recommend", cropname="maize", nitrogen=int(nitrogen_avg),
                            phosphorous=int(phosphorus_avg), potassium=int(potassium_avg)))
    # Render template with the average values
    # return render_template('predictions.html', device_id=device_id, nitrogen_avg=nitrogen_avg,
    #                        potassium_avg=potassium_avg, phosphorus_avg=phosphorus_avg)



@app.route('/PesticideRecommendation')
def PesticideRecommendation():
    return render_template('PesticideRecommendation.html')


@app.route("/recommend-fertilizer", methods=["POST", "GET"])
@app.route("/FertilizerRecommendation.html", methods=["POST", "GET"])
@app.route("/FertilizerRecommendation", methods=["POST", "GET"])
def fertilizer_recommend():
    print("fertilizer_recommend function accessed!")

    if request.method == "POST":
        crop_name = str(request.form['cropname'])
        N_filled = int(request.form['nitrogen'])
        P_filled = int(request.form['phosphorous'])
        K_filled = int(request.form['potassium'])
    else:
        crop_name = request.args.get('cropname')
        N_filled = request.args.get('nitrogen', type=int)
        P_filled = request.args.get('phosphorous', type=int)
        K_filled = request.args.get('potassium', type=int)

    if not crop_name or not N_filled or not P_filled or not K_filled:
        return render_template("FertilizerRecommendation.html")

    df = pd.read_csv('Data/Crop_NPK.csv')

    N_desired = df[df['Crop'] == crop_name]['N'].iloc[0]
    P_desired = df[df['Crop'] == crop_name]['P'].iloc[0]
    K_desired = df[df['Crop'] == crop_name]['K'].iloc[0]

    diff_n = N_desired - N_filled
    diff_p = P_desired - P_filled
    diff_k = K_desired - K_filled


    n = N_desired - N_filled
    p = P_desired - P_filled
    k = K_desired - K_filled

    if n < 0:
        key1 = "NHigh"
    elif n > 0:
        key1 = "Nlow"
    else:
        key1 = "NNo"

    if p < 0:
        key2 = "PHigh"
    elif p > 0:
        key2 = "Plow"
    else:
        key2 = "PNo"

    if k < 0:
        key3 = "KHigh"
    elif k > 0:
        key3 = "Klow"
    else:
        key3 = "KNo"

    abs_n = abs(n)
    abs_p = abs(p)
    abs_k = abs(k)

    response1 = Markup(str(fertilizer_dict[key1]))
    response2 = Markup(str(fertilizer_dict[key2]))
    response3 = Markup(str(fertilizer_dict[key3]))
    return render_template('Fertilizer-Result.html', recommendation1=response1,
                           recommendation2=response2, recommendation3=response3,
                           diff_n=abs_n, diff_p=abs_p, diff_k=abs_k)





    #recommendation1 = Markup(str(fertilizer_dict["NHigh" if diff_n < 0 else "Nlow" if diff_n > 0 else "NNo"]))
    #recommendation2 = Markup(str(fertilizer_dict["PHigh" if diff_p < 0 else "Plow" if diff_p > 0 else "PNo"]))
   # recommendation3 = Markup(str(fertilizer_dict["KHigh" if diff_k < 0 else "Klow" if diff_k > 0 else "KNo"]))

    # This will fetch the appropriate recommendation based on the differences.
    #sms_recommendation1 = Markup(str(sms_fertilizer_dict["NHigh" if diff_n < 0 else "Nlow" if diff_n > 0 else "NNo"]))
   # sms_recommendation2 = Markup(str(sms_fertilizer_dict["PHigh" if diff_p < 0 else "Plow" if diff_p > 0 else "PNo"]))
    #sms_recommendation3 = Markup(str(sms_fertilizer_dict["KHigh" if diff_k < 0 else "Klow" if diff_k > 0 else "KNo"]))


    # Generate the message based on the template data
   # message_text = f"""
    #**Difference between desired value of N and your farm's N value is {diff_n}
   # {sms_recommendation1}
   # **Difference between desired value of P and your farm's P value is {diff_p}  remove the two asteric before difference
   # {sms_recommendation2}
   # **Difference between desired value of K and your farm's K value is {diff_k}
   # {sms_recommendation3}
   # """

    # Send the message using Twilio
    #print(f"Sending SMS to +254704860552 with message: {message_text}")
    #account_sid = 'AC862a2593d8664871712cda9b07333412'  # replace with your actual SID
    #auth_token = 'b210f5faf3871055ab773a94460dabae'    # replace with your actual Auth Token
    #client = Client(account_sid, auth_token)
    #from_phone_number = '+12293608033'

    #try:
       # response = client.messages.create(
          #  body=message_text,
           # from_=from_phone_number,
           # to='+254740390420'
       # )
        #print(f"Twilio Response: {response.sid} - {response.status}")
    #except Exception as e:
        #print(f"Error sending SMS: {e}")

    # Render the template as usual
#return render_template('Fertilizer-Result.html', 
                           #diff_n=diff_n, recommendation1=recommendation1,
                           #diff_p=diff_p, recommendation2=recommendation2,
                           # diff_k=diff_k, recommendation3=recommendation3)

if __name__ == '__main__':
    app.run()
