from . import db  # Import the db instance from __init__.py
from datetime import datetime

# Association table for Turf and Category
turf_category = db.Table('turf_category',
    db.Column('turf_id', db.Integer, db.ForeignKey('tbl_turf.turf_id'), primary_key=True),
    db.Column('cat_id', db.Integer, db.ForeignKey('tbl_category.cat_id'), primary_key=True)
)

# Association table for Turf and Subcategory
turf_subcategory = db.Table('turf_subcategory',
    db.Column('turf_id', db.Integer, db.ForeignKey('tbl_turf.turf_id'), primary_key=True),
    db.Column('sub_id', db.Integer, db.ForeignKey('tbl_subcategory.sub_id'), primary_key=True)
)

# Login table model (authentication-related)
class Login(db.Model):
    __tablename__ = 'tbl_login'
    id = db.Column(db.Integer, autoincrement=True, nullable=False, unique=True, index=True)
    username = db.Column(db.String(150), primary_key=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    login_type = db.Column(db.String(50), nullable=False)  # Can be 'customer', 'turf_owner'

    def __repr__(self):
        return f"<Login {self.username}>"

# Customer table model
class Customer(db.Model):
    __tablename__ = 'tbl_cust'
    
    cust_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(150), db.ForeignKey('tbl_login.username'), nullable=False)
    cust_fname = db.Column(db.String(100), nullable=False)
    cust_lname = db.Column(db.String(100), nullable=False)
    cust_phone = db.Column(db.String(15), nullable=False)
    cust_housename = db.Column(db.String(100), nullable=False)
    cust_street = db.Column(db.String(100), nullable=False)
    cust_dist = db.Column(db.String(100), nullable=False)
    cust_pin = db.Column(db.String(6), nullable=False)
    cust_gender = db.Column(db.String(1), nullable=False)  # 'M', 'F', 'O'
    cust_status = db.Column(db.Boolean, default=True)  # True: Active, False: Inactive

    # Relationship with Login table
    login = db.relationship('Login', backref='customer', uselist=False)

    def __repr__(self):
        return f'<Customer {self.cust_fname} {self.cust_lname}>'


class Review(db.Model):
    __tablename__ = 'tbl_review'
    
    review_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('tbl_booking.booking_id'), nullable=False)
    cust_id = db.Column(db.Integer, db.ForeignKey('tbl_cust.cust_id'), nullable=False)
    turf_id = db.Column(db.Integer, db.ForeignKey('tbl_turf.turf_id'), nullable=False)
    rating = db.Column(db.Integer, nullable=True)  # Match DB schema (nullable=True)
    review_content = db.Column(db.Text, nullable=True)  # Already matches
    review_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships kept the sames
    
    # Relationships (use string-based references)
    customer = db.relationship('Customer', backref='reviews')
    turf = db.relationship('Turf', backref='reviews')
    booking = db.relationship('Booking', backref='review')

    def __repr__(self):
        return f'<Review {self.review_id} - Rating: {self.rating}>'



class TurfOwner(db.Model):
    __tablename__ = 'tbl_owner'
    
    owner_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    owner_fname = db.Column(db.String(100), nullable=False)
    owner_lname = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(150), db.ForeignKey('tbl_login.username'), nullable=False)
    owner_phno = db.Column(db.String(15), nullable=False)
    owner_street = db.Column(db.String(150), nullable=False)
    owner_dist = db.Column(db.String(150), nullable=False)
    owner_pin = db.Column(db.String(6), nullable=False)
    owner_status = db.Column(db.Boolean, default=True)
    owner_housename = db.Column(db.String(150), nullable=False)
    owner_gender = db.Column(db.String(1), nullable=False)  # 'M', 'F', 'O'

    # Relationship with Login table
    login = db.relationship('Login', backref='owner', uselist=False)

    def __repr__(self):
        return f'<TurfOwner {self.owner_fname} {self.owner_lname}>'
    
class Turf(db.Model):
    __tablename__ = 'tbl_turf'
    
    turf_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('tbl_owner.owner_id'), nullable=False)
    turf_name = db.Column(db.String(150), nullable=False)
    turf_phno = db.Column(db.String(15), nullable=False)
    turf_address = db.Column(db.String(150), nullable=False)
    turf_street = db.Column(db.String(150), nullable=False)
    turf_dist = db.Column(db.String(50), nullable=False)
    turf_pin = db.Column(db.String(6), nullable=False)
    price_per_hour = db.Column(db.Numeric(10, 2), nullable=False)
    turf_opening_time = db.Column(db.Time, nullable=False)
    turf_closing_time = db.Column(db.Time, nullable=False)
    turf_desc = db.Column(db.Text, nullable=True)
    
    # Relationships
    owner = db.relationship('TurfOwner', backref='turfs')
    categories = db.relationship('Category', secondary=turf_category, back_populates='turfs')
    subcategories = db.relationship('Subcategory', secondary=turf_subcategory, back_populates='turfs')
    bookings = db.relationship('Booking', backref='turf', lazy=True)
    images = db.relationship('TurfImage', backref='turf', cascade="all, delete-orphan")
    
    # Added Relationships
    policies = db.relationship('TurfPolicy', backref='turf', cascade="all, delete-orphan", lazy=True)
    amenities = db.relationship('TurfAmenity', backref='turf', cascade="all, delete-orphan", lazy=True)

    def __repr__(self):
        return f'<Turf {self.turf_name}>'


class TurfImage(db.Model):
    __tablename__ = 'turf_images'
    image_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    turf_id = db.Column(db.Integer, db.ForeignKey('tbl_turf.turf_id'), nullable=False)
    image = db.Column(db.LargeBinary, nullable=False)

    def __repr__(self):
        return f'<TurfImage {self.image_id}>'
class Booking(db.Model):
    __tablename__ = 'tbl_booking'
    
    booking_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cust_id = db.Column(db.Integer, db.ForeignKey('tbl_cust.cust_id'), nullable=False)
    turf_id = db.Column(db.Integer, db.ForeignKey('tbl_turf.turf_id'), nullable=False)
    booking_datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    play_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    total_hours = db.Column(db.Numeric(5, 2), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_status = db.Column(db.Boolean, nullable=False, default=False)
    booking_status = db.Column(db.String(10), nullable=False, default='Pending')
    special_requests = db.Column(db.Text, nullable=True)
    admin_commission = db.Column(db.Numeric(10, 2), nullable=True)  # Added column
    owner_revenue = db.Column(db.Numeric(10, 2), nullable=True)  # Added column
  
    # Relationships
    customer = db.relationship('Customer', backref='bookings')

    def __repr__(self):
        return f'<Booking {self.booking_id}>'

class Category(db.Model):
    __tablename__ = 'tbl_category'
    
    cat_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cat_name = db.Column(db.String(50), nullable=False)
    cat_status = db.Column(db.Boolean, nullable=False, default=True)
    

    # Relationships
    turfs = db.relationship('Turf', secondary=turf_category, back_populates='categories')
    subcategories = db.relationship('Subcategory', backref='category')

    def __repr__(self):
        return f'<Category {self.cat_name}>'
    
class Subcategory(db.Model):
    __tablename__ = 'tbl_subcategory'
    
    sub_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cat_id = db.Column(db.Integer, db.ForeignKey('tbl_category.cat_id'), nullable=False)
    sub_name = db.Column(db.String(50), nullable=False)
    sub_status = db.Column(db.Boolean, nullable=False, default=True)

    # Relationships
    turfs = db.relationship('Turf', secondary=turf_subcategory, back_populates='subcategories')

    def __repr__(self):
        return f'<Subcategory {self.sub_name}>'
    

class Payment(db.Model):
    __tablename__ = 'tbl_payment'
    
    payment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('tbl_booking.booking_id'), nullable=True)
    cust_id = db.Column(db.Integer, db.ForeignKey('tbl_cust.cust_id'), nullable=True)
    total_amount = db.Column(db.Numeric(9, 2), nullable=False)
    payment_status = db.Column(db.Boolean, nullable=False)
    payment_method = db.Column(db.Enum('debit_card', 'credit_card', 'upi', 'netbanking'), nullable=False)
    payment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<Payment {self.payment_id}>'
    



class Card(db.Model):
    __tablename__ = 'tbl_card'
    
    card_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cust_id = db.Column(db.Integer, db.ForeignKey('tbl_cust.cust_id'), nullable=True)
    card_holder_name = db.Column(db.String(20), nullable=False)
    card_no = db.Column(db.String(16), nullable=False)  # Changed to String
    bank_name = db.Column(db.String(20), nullable=False)
    card_type = db.Column(db.String(11), nullable=False)
    exp_date = db.Column(db.Date, nullable=False)
    card_status = db.Column(db.Boolean, nullable=False)

    def __repr__(self):
        return f'<Card {self.card_id}>'
    



class UPI_Payment(db.Model):
    __tablename__ = 'tbl_upi_payment'
    
    upi_payment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('tbl_payment.payment_id'), nullable=False)
    cust_id = db.Column(db.Integer, db.ForeignKey('tbl_cust.cust_id'), nullable=True)
    upi_id = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f'<UPI_Payment {self.upi_payment_id}>'

class NetBanking_Payment(db.Model):
    __tablename__ = 'tbl_netbanking_payment'
    
    netbanking_payment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('tbl_payment.payment_id'), nullable=False)
    cust_id = db.Column(db.Integer, db.ForeignKey('tbl_cust.cust_id'), nullable=True)
    bank_name = db.Column(db.String(50), nullable=False)
    account_number = db.Column(db.String(20), nullable=False)
    ifsc_code = db.Column(db.String(11), nullable=False)

    def __repr__(self):
        return f'<NetBanking_Payment {self.netbanking_payment_id}>'
    


class Message(db.Model):
    __tablename__ = 'tbl_msg'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    sender_name = db.Column(db.String(100), nullable=False)
    sender_email = db.Column(db.String(100), nullable=False)
    recipient = db.Column(db.String(100), nullable=False)  # Ensure recipient column exists
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_unread = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # New date column

    def __init__(self, sender_name, sender_email, recipient, subject, content, is_unread=True):
        self.sender_name = sender_name
        self.sender_email = sender_email
        self.recipient = recipient
        self.subject = subject
        self.content = content
        self.is_unread = is_unread
        self.created_at = datetime.utcnow()  # Auto-assign the current timestamp


class TurfPolicy(db.Model):
    __tablename__ = 'turf_policies'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    turf_id = db.Column(db.Integer, db.ForeignKey('tbl_turf.turf_id', ondelete="CASCADE"), nullable=False, index=True)
    policy_type = db.Column(db.Enum('Ground', 'Refund'), nullable=False)
    policy_text = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<TurfPolicy {self.policy_type} - Turf ID {self.turf_id}>"


class TurfAmenity(db.Model):
    __tablename__ = 'turf_amenities'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    turf_id = db.Column(db.Integer, db.ForeignKey('tbl_turf.turf_id', ondelete="CASCADE"), nullable=False, index=True)
    amenity_name = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<TurfAmenity {self.amenity_name} - Turf ID {self.turf_id}>"



class RefundPolicy(db.Model):
    __tablename__ = 'refund_policy'

    policy_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cancellation_time_range = db.Column(db.String(50), nullable=False)
    refund_percentage = db.Column(db.Numeric(5, 2), nullable=False)
    processing_fee = db.Column(db.Numeric(5, 2), nullable=True, default=0.00)
    applies_to = db.Column(db.Enum('Customer', 'Admin', 'Both'), nullable=False, default='Customer')
    reason_allowed = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<RefundPolicy {self.policy_id} - {self.cancellation_time_range}>"



class Refund(db.Model):
    __tablename__ = 'tbl_refund'

    refund_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('tbl_payment.payment_id', ondelete="SET NULL"), nullable=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('tbl_booking.booking_id', ondelete="CASCADE"), nullable=True)
    cust_id = db.Column(db.Integer, db.ForeignKey('tbl_cust.cust_id', ondelete="CASCADE"), nullable=False)
    refund_amount = db.Column(db.Numeric(10, 2), nullable=False)
    refund_reason = db.Column(db.Text, nullable=False)
    refund_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    refund_status = db.Column(db.Boolean, nullable=False, default=False)  # False = Pending, True = Processed
    policy_id = db.Column(db.Integer, db.ForeignKey('refund_policy.policy_id', ondelete="CASCADE"), nullable=False)

    # Relationships with correct table name
    payment = db.relationship('Payment', backref=db.backref('refunds', lazy=True))
    booking = db.relationship('Booking', backref=db.backref('refunds', lazy=True, cascade="all, delete-orphan"))
    customer = db.relationship('Customer', primaryjoin="Refund.cust_id == Customer.cust_id", backref=db.backref('refunds', lazy=True, cascade="all, delete-orphan"))
    policy = db.relationship('RefundPolicy', backref=db.backref('refunds', lazy=True, cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<Refund {self.refund_id} - Booking {self.booking_id} - ₹{self.refund_amount}>"




class Reply(db.Model):
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    sender_name = db.Column(db.String(100), nullable=False)
    sender_email = db.Column(db.String(100), nullable=True)
    recipient = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
