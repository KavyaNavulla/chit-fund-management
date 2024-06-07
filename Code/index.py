from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from flask_mail import Mail, Message

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
app.config['MAIL_SERVER']= 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'gitty695@gmail.com'
app.config['MAIL_PASSWORD'] = 'sncc qwfd tbxo lxop'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=False, nullable=False)
    password = db.Column(db.String(50), nullable=False)

# Scheme model
class Scheme(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name_of_scheme = db.Column(db.String(100), nullable=False)
    principal_amount = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    monthly_amount = db.Column(db.Float, nullable=False)
    commission = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    def calculate_statistics(self):
        total_members = len(self.members)
        total_monthly_contributions = sum(member.scheme.monthly_amount for member in self.members)
        total_commission_earned = sum(member.scheme.monthly_amount * self.commission for member in self.members)
        return {
            'total_members': total_members,
            'total_monthly_contributions': total_monthly_contributions,
            'total_commission_earned': total_commission_earned,
             'principal_amount': self.principal_amount,
            'monthly_amount': self.monthly_amount,
            'duration': self.duration
        }
# Member model (example structure, adjust as needed)
class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    address = db.Column(db.String(200), nullable=True)
    join_date = db.Column(db.DateTime, default=datetime.utcnow)
    scheme_id = db.Column(db.Integer, db.ForeignKey('scheme.id'), nullable=False)
    scheme = db.relationship('Scheme', backref=db.backref('members', lazy=True))

class PaymentStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    member_name = db.Column(db.String(100), nullable=False)  # Adding member's name
    month = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    member = db.relationship('Member', backref=db.backref('payment_statuses', lazy=True))


def create_tables():
    with app.app_context():
        db.create_all()

create_tables()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        existing_user = User.query.filter_by(username=username).first()
        
        if existing_user:
            return "Username already exists! Please choose a different username."
        
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for('index'))
    else:
        return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            print(username)
            return redirect(url_for('home', username=username))
        else:
            return "Invalid username or password. Please try again."

@app.route('/send_remainder')
def send_remainder():
    # msg = Message(subject="helloo", sender='gitty695@gmail.com', recipients=['suraj963719@gmail.com'])
    # msg.body = "heyyyy"
    # mail.send(msg)
    schemes = Scheme.query.all()
    return render_template('send_remainder.html',schemes=schemes)

@app.route('/send_reminder_email', methods=['POST'])
def send_reminder_email():
    data = request.get_json()
    scheme_id = data['scheme_id']
    
    scheme = Scheme.query.get(scheme_id)
    if not scheme:
        return jsonify({'success': False, 'error': 'Scheme not found'}), 404
    
    members = Member.query.filter_by(scheme_id=scheme_id).all()
    if not members:
        return jsonify({'success': False, 'error': 'No members found for this scheme'}), 404

    try:
        for member in members:
            msg = Message(
                subject=f"Payment Reminder for {scheme.name_of_scheme}",
                sender='gitty695@gmail.com',
                recipients=[member.email]
            )
            # msg.body = f"Dear {member.name},\n\nThis is a reminder to pay your fee for the scheme {scheme.name_of_scheme}.\n\nThank you."
            msg.body = f"Dear {member.name},\n\nThis is a gentle reminder for those who haven't yet submitted their monthly contribution to the chit fund named {scheme.name_of_scheme}. If you've already paid, please ignore this message.\n\nThank you for your prompt attention."
            mail.send(msg)
        
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
@app.route('/dashboard')
def dashboard():
    schemes = Scheme.query.all()
    scheme_statistics = {}
    for scheme in schemes:
        scheme_statistics[scheme.name_of_scheme] = scheme.calculate_statistics()
    return render_template('dashboard.html', scheme_statistics=scheme_statistics)

@app.route('/add_schemes', methods=['GET', 'POST'])
def add_schemes():
    if request.method == 'POST':
        name_of_scheme = request.form['name_of_scheme']
        principal_amount = float(request.form['principal_amount'])
        duration = int(request.form['duration'])
        monthly_amount = float(request.form['monthly_amount'])
        commission = float(request.form['commission'])
        
        new_scheme = Scheme(
            name_of_scheme=name_of_scheme,
            principal_amount=principal_amount,
            duration=duration,
            monthly_amount=monthly_amount,
            commission=commission
        )
        db.session.add(new_scheme)
        db.session.commit()
        
        return redirect(url_for('add_schemes'))
    return render_template('add_schemes.html')


@app.route('/add_member', methods=['GET', 'POST'])
def add_member():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone_number = request.form['phone_number']
        address = request.form['address']
        scheme_id = request.form['scheme_id']
        
        new_member = Member(
            name=name,
            email=email,
            phone_number=phone_number,
            address=address,
            scheme_id=scheme_id
        )
        
        db.session.add(new_member)
        db.session.commit()
        
        return redirect(url_for('add_member'))
    
    # Fetch all schemes to display in the dropdown
    schemes = Scheme.query.all()
    return render_template('add_member.html', schemes=schemes)


@app.route('/update_payments', methods=['GET'])
def update_payments():
    schemes = Scheme.query.all()
    return render_template('update_payments.html', schemes=schemes)


@app.route('/scheme_members/<int:scheme_id>', methods=['GET'])
def scheme_members(scheme_id):
    scheme = Scheme.query.get_or_404(scheme_id)
    members = Member.query.filter_by(scheme_id=scheme_id).all()
    return render_template('scheme_members.html', scheme=scheme, members=members)


@app.route('/update_payments_status', methods=['POST'])
def update_payments_status():
    try:
        print("Form data received:", request.form)
        for key, value in request.form.items():
            if key.startswith('payment_status_'):
                parts = key.split('_')
                if len(parts) == 4:
                    _, _, member_id, month = parts
                    member_id = int(member_id)
                    month = int(month)
                    status = value
                    current_status_key = f"current_status_{member_id}_{month}"
                    current_status = request.form.get(current_status_key)

                    if current_status != status:
                        member = Member.query.get(member_id)  # Get the member object
                        member_name = member.name  # Extract the member's name
                        
                        payment_status = PaymentStatus.query.filter_by(member_id=member_id, month=month).first()
                        if payment_status:
                            payment_status.status = status
                            payment_status.member_name = member_name  # Update member's name
                            print(f"Updating existing payment status for Member ID = {member_id}, Month = {month}")
                        else:
                            payment_status = PaymentStatus(member_id=member_id, month=month, status=status, member_name=member_name)
                            db.session.add(payment_status)
                            print(f"Adding new payment status for Member ID = {member_id}, Month = {month}")

        db.session.commit()
        print("Database commit successful")
        return redirect(url_for('home'))
    except Exception as e:
        print(f"Error processing payment status update: {e}")
        return "An error occurred while updating payment statuses. Please try again.", 500


@app.route('/generate_receipt')
def generate_receipt():
    return render_template('generate_receipt.html')

@app.route('/home')
def home():
    username = request.args.get('username')
    return render_template('home.html', username=username)

@app.route('/delete_expired_schemes')
def delete_expired_schemes():
    current_time = datetime.utcnow()
    schemes = Scheme.query.all()
    
    for scheme in schemes:
        expiry_date = scheme.start_date + timedelta(days=scheme.duration * 30)
        if current_time >= expiry_date:
            # Delete associated members first
            members = Member.query.filter_by(scheme_id=scheme.id).all()
            for member in members:
                db.session.delete(member)
            
            # Delete the scheme
            db.session.delete(scheme)
    
    db.session.commit()
    return "Expired schemes and associated members deleted."

if __name__ == '__main__':
    app.run(debug=True)
