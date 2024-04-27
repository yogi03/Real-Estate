from flask import Flask, render_template, request, redirect, url_for , session , flash
from flask_sqlalchemy import SQLAlchemy
import os
import secrets
import string
from sqlalchemy import func
from werkzeug.utils import secure_filename
from datetime import datetime
from datetime import time
from flask_mail import Mail, Message
import secrets
from flask import jsonify

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///real_estate.db'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)

UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['MAIL_SERVER'] = 'smtp.gmail.com'  
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'yogendrachaurasiya30@gmail.com'  
app.config['MAIL_PASSWORD'] = 'oizzrkharzmoltmv'  

mail = Mail(app)
app.jinja_env.globals['getattr'] = getattr

# Define models
class Client(db.Model):
    id = db.Column(db.String(6), primary_key=True, default=lambda: ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6)))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(10), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    photo = db.Column(db.String(200))

class Owner(db.Model):
    id = db.Column(db.String(6), primary_key=True, default=lambda: ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6)))
    owner_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(10), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    photo = db.Column(db.String(200))

class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_name = db.Column(db.String(100), db.ForeignKey('owner.owner_name'), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    property_name = db.Column(db.String(100), nullable=False)
    property_description = db.Column(db.Text, nullable=False)  
    property_size = db.Column(db.String(20), nullable=False)
    property_type = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image1 = db.Column(db.String(200))
    image2 = db.Column(db.String(200))
    image3 = db.Column(db.String(200))
    image4 = db.Column(db.String(200))
    image5 = db.Column(db.String(200))
    image6 = db.Column(db.String(200))
    
class Appointment(db.Model):
    id = db.Column(db.String(6), primary_key=True, default=lambda: ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6)))
    client_id = db.Column(db.String(6),nullable=False)
    client_name = db.Column(db.String(100), nullable=False)
    client_email = db.Column(db.String(100), nullable=False)
    client_phone = db.Column(db.String(10), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    property_address = db.Column(db.String(200), nullable=False)
    owner_name = db.Column(db.String(100), nullable=False)

class PropertyBooked(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pid = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    cid = db.Column(db.String(6), db.ForeignKey('client.id'), nullable=False)
    booked_date = db.Column(db.Date, nullable=False)


class Transaction(db.Model):
    transaction_id = db.Column(db.String(10), primary_key=True, default=lambda: ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(10)))
    prop_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


    
# Define routes
@app.route('/')
def index():
    # Get filter parameters from the query string
    property_type = request.args.get('property_type')
    property_size_min = request.args.get('property_size_min')
    property_size_max = request.args.get('property_size_max')
    price_min = request.args.get('price_min')
    price_max = request.args.get('price_max')
    address = request.args.get('address')

    # Filter properties based on the parameters
    properties = Property.query

    if property_type:
        properties = properties.filter(Property.property_type == property_type)
    if property_size_min and property_size_max:
        properties = properties.filter(Property.property_size.between(property_size_min, property_size_max))
    if price_min and price_max:
        properties = properties.filter(Property.price.between(price_min, price_max))
    if address:
        properties = properties.filter(Property.address.ilike(f'%{address}%'))

    properties = properties.all()

    return render_template('index.html', properties=properties)

@app.route('/property/<int:id>')
def property_details(id):
    property = Property.query.get_or_404(id)
    return render_template('property_details.html', property=property, id=id, owner_name=property.owner_name)

@app.route('/properties')
def properties():
    # Fetch properties data as needed
    properties = Property.query.all()
    return render_template('properties.html', properties=properties)

@app.route('/list_property', methods=['POST'])
def list_property():
    if 'owner_id' not in session:
        return redirect(url_for('owner_login'))  
    
    if request.method == 'POST':
        owner_id = session['owner_id']
        owner = Owner.query.get(owner_id)
        if owner:
            property_name = request.form['property_name']
            property_description = request.form['property_description']
            address = request.form['address']
            property_size = request.form['property_size']
            property_type = request.form['property_type']
            price = request.form['price']

            # Initialize an empty list to store file paths
            property_images = []

            # Process file uploads
            for i in range(1, 5):
                file_key = 'property_image{}'.format(i)
                if file_key in request.files:
                    file = request.files[file_key]
                    if file.filename != '':
                        # Save the file to the uploads folder
                        filename = secure_filename(file.filename)
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(file_path)
                        property_images.append(file_path)

            # Create a new property with the logged-in owner's owner_name
            new_property = Property(owner_name=owner.owner_name, property_name=property_name, 
                                    property_description=property_description, address=address, 
                                    property_size=property_size, property_type=property_type, price=price)
            db.session.add(new_property)
            db.session.commit()

            # Save property images to the database
            for i in range(len(property_images)):
                setattr(new_property, f"image{i+1}", property_images[i])
            db.session.commit()

            return redirect(url_for('index'))
        else:
            return "Owner not found!"
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search_properties():
    query = request.form.get('query')
    # Search for properties that match the query
    properties = Property.query.filter(
        (Property.property_name.ilike(f'%{query}%')) |
        (Property.owner_name.ilike(f'%{query}%')) |
        (Property.address.ilike(f'%{query}%')) |
        (Property.property_type.ilike(f'%{query}%')) |
        (Property.property_size.ilike(f'%{query}%')) |
        (Property.price.ilike(f'%{query}%'))
    ).all()
    # Render a template with the search results
    return render_template('property_list.html', properties=properties)

# Add two different routes for client and owner signup
@app.route('/client_signup', methods=['GET', 'POST'])
def client_signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        
        # Validate password
        if not (
            len(password) >= 8 and
            any(char.islower() for char in password) and
            any(char.isupper() for char in password) and
            any(char.isdigit() for char in password) and
            any(char in string.punctuation for char in password)
        ):
            flash("Password must be at least 8 characters long and contain at least 1 lowercase alphabet, 1 uppercase alphabet, 1 special character, and 1 numeric value.")
            return redirect(url_for('client_signup'))
        
        # Check if the email is already registered
        existing_user = Client.query.filter_by(email=email).first()
        if existing_user:
            # User already exists, redirect to login page
            return redirect(url_for('client_login'))
        else:
            # Process photo upload
            if 'photo' in request.files:
                photo = request.files['photo']
                photo_path = 'static/images/' + photo.filename
                photo.save(photo_path)
            else:
                photo_path = None
            
            # Create a new client user
            new_client = Client(name=name, email=email, phone=phone, password=password, photo=photo_path)
            db.session.add(new_client)
            db.session.commit()
            # Store user_id in session after successful signup
            session['user_id'] = new_client.id
            # Redirect to index page after successful signup
            return redirect(url_for('index'))
    return render_template('client_signup.html')

@app.route('/owner_signup', methods=['GET', 'POST'])
def owner_signup():
    if request.method == 'POST':
        owner_name = request.form['owner_name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        
        # Validate password
        if not (
            len(password) >= 8 and
            any(char.islower() for char in password) and
            any(char.isupper() for char in password) and
            any(char.isdigit() for char in password) and
            any(char in string.punctuation for char in password)
        ):
            flash("Password must be at least 8 characters long and contain at least 1 lowercase alphabet, 1 uppercase alphabet, 1 special character, and 1 numeric value.")
            return redirect(url_for('owner_signup'))
        
        # Check if the email is already registered
        existing_owner = Owner.query.filter_by(email=email).first()
        if existing_owner:
            # Owner already exists, redirect to owner login page
            return redirect(url_for('owner_login'))
        else:
            new_owner = Owner(owner_name=owner_name, email=email, password=password, phone=phone)
            db.session.add(new_owner)
            db.session.commit()
            # Store owner_id in session after successful signup
            session['owner_id'] = new_owner.id
            # Redirect to index page after successful signup
            return redirect(url_for('sell_property'))
    return render_template('owner_signup.html')

# Add routes for client and owner login
@app.route('/client_login', methods=['GET', 'POST'])
def client_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        # Check if the client exists in the database
        client = Client.query.filter_by(email=email).first()
        if client:
            # Verify password
            if client.password == password:
                # Client exists and password matches, store user_id in session and redirect to index page
                session['user_id'] = client.id
                return redirect(url_for('index'))
            else:
                flash("Incorrect email or password.")
                return redirect(url_for('client_login'))
        else:
            # Client does not exist, redirect to client signup page
            return redirect(url_for('client_signup'))
    return render_template('client_login.html')

@app.route('/owner_login', methods=['GET', 'POST'])
def owner_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        # Check if the owner exists in the database
        owner = Owner.query.filter_by(email=email).first()
        if owner:
            # Verify password
            if owner.password == password:
                # Owner exists and password matches, store owner_id in session and redirect to index page
                session['owner_id'] = owner.id
                return redirect(url_for('sell_property'))
            else:
                flash("Incorrect email or password.")
                return redirect(url_for('owner_login'))
        else:
            # Owner does not exist, redirect to owner signup page
            return redirect(url_for('owner_signup'))
    return render_template('owner_login.html')

@app.route('/logout')
def logout():
    # Remove user_id from session if present
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/sell_property', methods=['GET', 'POST'])
def sell_property():
    if 'owner_id' not in session:
        return redirect(url_for('owner_login'))  # Redirect to login page if user is not logged in
    
    if request.method == 'POST':
        # Handle property listing form submission
        # Add property listing logic here
        return redirect(url_for('index'))
    return render_template('sell_property.html')

# Define a function to send email to client
def send_appointment_email(client_email, property_details):
    msg = Message('Appointment Scheduled', sender='yogendrachaurasiya30@example.com', recipients=[client_email])
    msg.body = f"Hello,\n\nYour property booking appointment for property located at {property_details['property_address']} has been scheduled.\n\nAppointment Date: {property_details['appointment_date']}\nAppointment Time: {property_details['appointment_time']}\n\nRegards,\nReal Estate Team"
    mail.send(msg)
    
# Define a function to send appointment notification email to property owner
def send_owner_appointment_email(owner_email, appointment_data):
    msg = Message('New Appointment Scheduled', sender='yogendrachaurasiya30@example.com', recipients=[owner_email])
    msg.body = f"Hello,\n\nA new appointment has been scheduled by {appointment_data['client_name']} for your property located at {appointment_data['property_address']}.\n\nAppointment Date: {appointment_data['appointment_date']}\nAppointment Time: {appointment_data['appointment_time']}\n\nClient Phone: {appointment_data['client_phone']}\n\nRegards,\nReal Estate Team"
    mail.send(msg)

# schedule_appointment route to send emails to both client and owner
@app.route('/schedule_appointment', methods=['POST'])
def schedule_appointment():
    if 'user_id' not in session:
        return redirect(url_for('client_login'))
    
    if request.method == 'POST':
        client_id = session['user_id']
        client = Client.query.get(client_id)
        if client:
            appointment_date = datetime.strptime(request.form['appointment_date'], '%Y-%m-%d').date()
            appointment_time_str = request.form.get('appointment_time')
            hour, minute = map(int, appointment_time_str.split(':'))
            appointment_time = time(hour, minute)
            property_id = request.args.get('id')  
            property_owner_name = request.args.get('owner_name')  # Fetch owner name from request
            
            # Fetch owner's email address based on the owner's name
            property_owner = Owner.query.filter_by(owner_name=property_owner_name).first()
            if property_owner:
                property_owner_email = property_owner.email
                
                property_address = Property.query.get(property_id).address
                
                # Create a new appointment instance
                new_appointment = Appointment(client_id=client_id, client_name=client.name, client_email=client.email,
                                              client_phone=client.phone, appointment_date=appointment_date,
                                              appointment_time=appointment_time, property_id=property_id,
                                              property_address=property_address, owner_name=property_owner_name)
                
                # Add the appointment to the database
                db.session.add(new_appointment)
                db.session.commit()
                
                # Send appointment confirmation email to the client
                client_email_data = {
                    'property_address': new_appointment.property_address,
                    'appointment_date': new_appointment.appointment_date,
                    'appointment_time': new_appointment.appointment_time
                }
                send_appointment_email(client.email, client_email_data)
                
                # Send appointment notification email to the property owner
                owner_email_data = {
                    'client_name': client.name,
                    'client_phone': client.phone,
                    'appointment_date': new_appointment.appointment_date,
                    'appointment_time': new_appointment.appointment_time,
                    'property_address': new_appointment.property_address
                }
                send_owner_appointment_email(property_owner_email, owner_email_data)
                
                # Redirect to property details page after scheduling appointment
                return redirect(url_for('property_details', id=property_id))
            else:
                return "Property owner not found!"
        else:
            return "Client not found!"
    return render_template('property_details.html')



@app.route('/book_property', methods=['GET', 'POST'])
def book_property():
    if 'user_id' not in session:
        return redirect(url_for('client_login'))

    if request.method == 'POST':
        pid = request.args.get('pid')
        cid = session.get('user_id')  # Assuming the user is logged in and session contains user_id
        booked_date_str = request.form.get('booked_date')
        
        # Convert the string representation of the date to a Python date object
        booked_date = datetime.strptime(booked_date_str, '%Y-%m-%d').date()

        # Create a new PropertyBooked instance
        new_booking = PropertyBooked(pid=pid, cid=cid, booked_date=booked_date)
        db.session.add(new_booking)
        db.session.commit()

        # Redirect to home page after booking
        return redirect(url_for('index'))

    else:
       pid = request.args.get('pid')
       appointment_date = request.args.get('appointment_date')  # Get appointment date from query parameter
    return render_template('book_property.html', pid=pid, appointment_date=appointment_date)


@app.route('/down_payment', methods=['GET', 'POST'])
def down_payment():
    if 'user_id' not in session:
        return redirect(url_for('client_login'))

    if request.method == 'POST':
        
        client_id = session.get('user_id')
        prop_id = request.args.get('prop_id')
        

        # Check if the client has scheduled an appointment for the property
        appointment_exists = Appointment.query.filter_by(client_id=client_id, property_id=prop_id).first()
        if not appointment_exists:
            # Client has not scheduled an appointment, redirect to property_details.html
            flash("Please schedule an appointment before making a down payment. if already scheduled please ignore it")
            return redirect(url_for('property_details', id=prop_id))

        amount = 10000
        
        # Create a new Transaction instance
        new_transaction = Transaction(prop_id=prop_id, client_id=client_id, amount=amount)
        db.session.add(new_transaction)
        db.session.commit()

        return redirect(url_for('index'))
    
    return render_template('down_payment.html')


# Add a new route to handle the query 1
@app.route('/booked_properties')
def get_booked_properties():
    
    booked_properties = db.session.query(PropertyBooked, Property).join(Property).all()

    # Check if there are no booked properties
    no_properties_booked = not bool(booked_properties)
    return render_template('booked_properties.html', booked_properties=booked_properties , no_properties_booked=no_properties_booked)

# Add this route to count appointment Flask
@app.route('/appointment_count')
def appointment_count():
    # Query to count the total number of appointments scheduled for each property
    appointment_counts = db.session.query(Property.id, Property.address, db.func.count(Appointment.id).label('appointment_count')) \
                        .outerjoin(Appointment, Property.id == Appointment.property_id) \
                        .group_by(Property.id, Property.address) \
                        .all()
    return render_template('appointment_count.html', appointment_counts=appointment_counts)



# Route to display the form to input appointment date
@app.route('/appointment_date_form')
def appointment_date_form():
    return render_template('appointment_date_form.html')

# Route to display appointments count for properties on the specified date
@app.route('/appointment_by_date', methods=['GET'])
def appointment_by_date():
    # Get the appointment date from the query parameters
    appointment_date = request.args.get('appointment_date')
    
    # Convert the date string to a Python date object
    try:
        target_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()
    except ValueError:
        return "Invalid date format. Please use YYYY-MM-DD format."

    # Query to retrieve appointments scheduled for properties on the specified date
    appointment_scheduled = db.session.query(Property.id, Property.address, Appointment.appointment_date , Appointment.client_name) \
                        .join(Appointment, Property.id == Appointment.property_id) \
                        .filter(Appointment.appointment_date == target_date) \
                        .all()

    return render_template('appointment_by_date.html', appointment_scheduled=appointment_scheduled, target_date=target_date)


# Route to find properties not booked yet
@app.route('/unbooked_properties')
def unbooked_properties():
    unbooked_props = Property.query.filter(~Property.id.in_(PropertyBooked.query.with_entities(PropertyBooked.pid))).all()
    if not unbooked_props:
        message = "All properties are booked."
    else:
        message = None
    return render_template('unbooked_properties.html', unbooked_props=unbooked_props, message=message)


# Modify the route to fetch all properties for each owner with more than one property
@app.route('/owners_with_multiple_properties')
def owners_with_multiple_properties():
    # Query to retrieve properties listed by owners who have more than 1 property
    owners_properties = db.session.query(Owner.owner_name, Property.id, Property.address) \
                        .join(Owner, Property.owner_name == Owner.owner_name) \
                        .group_by(Owner.owner_name) \
                        .having(db.func.count(Property.id) >= 2) \
                        .all()
    
    # Fetch all properties for each owner with more than one property
    owners_properties_with_all = []
    for owner_property in owners_properties:
        owner_name, _, _ = owner_property
        properties = Property.query.filter_by(owner_name=owner_name).all()
        owners_properties_with_all.append((owner_name, properties))
    
    # Render the retrieved data in an HTML file
    return render_template('owners_with_multiple_properties.html', owners_properties=owners_properties_with_all)


# query to display clients who booked more than one property 
@app.route('/clients_with_multiple_bookings')
def clients_with_multiple_bookings():
    clients = db.session.query(Client).join(PropertyBooked, Client.id == PropertyBooked.cid).group_by(Client.id).having(func.count(PropertyBooked.id) > 1).all()
    return render_template('clients_with_multiple_bookings.html', clients=clients)



#query for client who have not booked any property yet
@app.route('/clients_without_bookings')
def clients_without_bookings():
    clients = db.session.query(Client).outerjoin(PropertyBooked, Client.id == PropertyBooked.cid).filter(PropertyBooked.id == None).all()
    return render_template('clients_without_bookings.html', clients=clients)

#query for listing the property inw which price is > 100000
@app.route('/expensive_properties')
def expensive_properties():
    properties = db.session.query(Property).filter(Property.price > 20000000).all()
    return render_template('expensive_properties.html', properties=properties)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
