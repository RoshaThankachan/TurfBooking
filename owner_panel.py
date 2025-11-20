import base64
from datetime import timedelta, datetime
from flask import Blueprint, json, render_template, redirect, url_for, request, flash, session
from . import db
from sqlalchemy import text
from .models import Turf, TurfAmenity, TurfImage, TurfOwner, Category, Subcategory, Booking, Customer,Message, TurfPolicy
from werkzeug.utils import secure_filename

owner_bp = Blueprint('owner', __name__, url_prefix='/owner')

# Configuration for admin commission percentage
ADMIN_COMMISSION_PERCENTAGE = 10  # Admin takes 10% commission from each booking

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@owner_bp.route("/dashboard")
def dashboard():
    if session.get('login_type') != 'turf_owner':
        return redirect(url_for('main.login'))

    username = session.get('username')
    owner = TurfOwner.query.filter_by(username=username).first()
    turfs = Turf.query.filter_by(owner_id=owner.owner_id).all()

    # Fetch upcoming bookings
    upcoming_bookings = Booking.query\
        .join(Turf, Booking.turf_id == Turf.turf_id)\
        .join(Customer, Booking.cust_id == Customer.cust_id)\
        .filter(Turf.owner_id == owner.owner_id)\
        .filter(Booking.play_date >= datetime.now())\
        .order_by(Booking.play_date, Booking.start_time)\
        .all()

    booking_data = []
    for booking in upcoming_bookings:
        booking_data.append({
            'customer_name': f"{booking.customer.cust_fname} {booking.customer.cust_lname}",
            'turf_name': booking.turf.turf_name,
            'date': booking.play_date.strftime('%Y-%m-%d'),
            'start_time': booking.start_time.strftime('%H:%M'),
            'end_time': booking.end_time.strftime('%H:%M')
        })

    return render_template("owner_dashboard.html", owner=owner, turfs=turfs, upcoming_bookings=booking_data)




@owner_bp.route("/register_turf", methods=['GET', 'POST'])
def register_turf():
    if session.get('login_type') != 'turf_owner':
        return redirect(url_for('main.login'))
    
    # Get the owner information
    username = session.get('username')
    owner = TurfOwner.query.filter_by(username=username).first()
    if not owner:
        flash("Owner not found!", "error")
        return redirect(url_for('main.login'))

    categories = Category.query.all()
    subcategories = Subcategory.query.all()

    if request.method == 'POST':
        turf_name = request.form.get('turf_name')
        turf_phno = request.form.get('turf_phno')
        turf_address = request.form.get('turf_address')
        turf_street = request.form.get('turf_street')
        turf_dist = request.form.get('turf_dist')
        turf_pin = request.form.get('turf_pin')
        price_per_hour = request.form.get('price_per_hour')
        turf_desc = request.form.get('turf_desc')
        turf_opening_time = request.form.get('turf_opening_time')
        turf_closing_time = request.form.get('turf_closing_time')


        try:
            new_turf = Turf(
                owner_id=owner.owner_id,
                turf_name=turf_name,
                turf_phno=turf_phno,
                turf_address=turf_address,
                turf_street=turf_street,
                turf_dist=turf_dist,
                turf_pin=turf_pin,
                price_per_hour=price_per_hour,
                turf_desc=turf_desc,
                turf_opening_time=turf_opening_time,  # Added field
                turf_closing_time=turf_closing_time   # Added field
            )
            
            db.session.add(new_turf)
            db.session.flush()  # This will assign an ID to new_turf

            # Add categories
            cat_ids = request.form.getlist('cat_id[]')
            for cat_id in cat_ids:
                category = Category.query.get(cat_id)
                if category:
                    new_turf.categories.append(category)

            # Add subcategories
            for i in range(len(cat_ids)):
                sub_ids = request.form.getlist(f'sub_ids[{i}][]')
                for sub_id in sub_ids:
                    subcategory = Subcategory.query.get(sub_id)
                    if subcategory:
                        new_turf.subcategories.append(subcategory)

            db.session.flush()

            # Process multiple images
            if 'turf_images' in request.files:
                files = request.files.getlist('turf_images')
                for file in files:
                    if file and allowed_file(file.filename):
                        # Read image data
                        image_data = file.read()
                        if image_data:  # Ensure we got data
                            # Encode each image as base64 and store in a list
                            encoded_image = base64.b64encode(image_data).decode('utf-8')
                            new_image = TurfImage(
                                turf_id=new_turf.turf_id,
                                image=encoded_image
                            )
                            db.session.add(new_image)

            db.session.commit()
            flash("Turf registered successfully!", "success")
            return redirect(url_for('owner.dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {e}", "error")
            return redirect(url_for('owner.register_turf'))

    return render_template("register_turf.html", owner=owner, categories=categories, subcategories=subcategories)






ALLOWED_EXTENSIONS = {'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS





@owner_bp.route("/edit_turf/<int:turf_id>", methods=['GET', 'POST'])
def edit_turf(turf_id):
    turf = Turf.query.get_or_404(turf_id)
    categories = Category.query.all()
    subcategories = Subcategory.query.all()

    # Get existing images if any
    existing_images = TurfImage.query.filter_by(turf_id=turf_id).all()

    if request.method == 'POST':
        turf.turf_name = request.form.get('turf_name')
        turf.turf_phno = request.form.get('turf_phno')
        turf.turf_address = request.form.get('turf_address')
        turf.turf_street = request.form.get('turf_street')
        turf.turf_dist = request.form.get('turf_dist')
        turf.turf_pin = request.form.get('turf_pin')
        turf.price_per_hour = request.form.get('price_per_hour')
        turf.turf_desc = request.form.get('turf_desc')
        
        # Convert time strings to time objects
        opening_time_str = request.form.get('turf_opening_time')
        closing_time_str = request.form.get('turf_closing_time')
        
        # Parse time strings (assuming format like "08:00 AM")
        from datetime import datetime
        try:
            opening_time = datetime.strptime(opening_time_str, '%I:%M %p').time()
            closing_time = datetime.strptime(closing_time_str, '%I:%M %p').time()
            turf.turf_opening_time = opening_time
            turf.turf_closing_time = closing_time
        except ValueError as e:
            flash(f"Invalid time format: {e}", "error")
            return render_template("edit_turf.html", turf=turf, categories=categories, 
                                  subcategories=subcategories, existing_images=existing_images)

        # Update categories
        cat_ids = request.form.getlist('cat_id[]')
        turf.categories = []
        for cat_id in cat_ids:
            category = Category.query.get(cat_id)
            if category:
                turf.categories.append(category)

        # Update subcategories
        sub_ids = request.form.getlist('sub_id[]')
        turf.subcategories = []
        for sub_id in sub_ids:
            subcategory = Subcategory.query.get(sub_id)
            if subcategory:
                turf.subcategories.append(subcategory)

        # Handle image uploads
        if 'turf_images' in request.files:
            files = request.files.getlist('turf_images')
            
            # Check if we need to delete existing images
            if not request.form.get('keep_existing_images', False):
                for image in existing_images:
                    db.session.delete(image)
            
            # Process each uploaded file
            for file in files:
                if file and file.filename:  # Check if file is actually provided
                    # Define allowed_file if not already defined
                    def allowed_file(filename):
                        return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png'}
                    
                    if allowed_file(file.filename):
                        image_data = file.read()
                        if image_data:  # Ensure there's actual data
                            try:
                                new_image = TurfImage(
                                    turf_id=turf.turf_id,
                                    image=image_data
                                )
                                db.session.add(new_image)
                            except Exception as e:
                                flash(f"Error saving image: {e}", "error")
                    else:
                        flash(f"File {file.filename} is not an allowed type. Use jpg, jpeg, or png.", "error")

        try:
            db.session.commit()
            flash("Turf updated successfully!", "success")
            return redirect(url_for('owner.view_turfs'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating turf: {e}", "error")
    
    return render_template("edit_turf.html", turf=turf, categories=categories, 
                          subcategories=subcategories, existing_images=existing_images)

@owner_bp.route("/view_turfs")
def view_turfs():
    if session.get('login_type') != 'turf_owner':
        return redirect(url_for('main.login'))
    
    username = session.get('username')
    owner = TurfOwner.query.filter_by(username=username).first()
    if not owner:
        flash("Owner not found!", "error")
        return redirect(url_for('main.login'))
    
    turfs = db.session.query(Turf).filter_by(owner_id=owner.owner_id).all()
    
    turf_data = []
    for turf in turfs:
        categories = [(cat.cat_id, cat.cat_name) for cat in turf.categories]
        subcategories = [(sub.sub_id, sub.sub_name) for sub in turf.subcategories]
        images = TurfImage.query.filter_by(turf_id=turf.turf_id).all()

        # Convert string to datetime and format it properly
        try:
            opening_time = turf.turf_opening_time.strftime('%I:%M %p') if turf.turf_opening_time else "N/A"
        except ValueError:
            opening_time = "Invalid Time"

        try:
            closing_time = turf.turf_closing_time.strftime('%I:%M %p') if turf.turf_closing_time else "N/A"
        except ValueError:
            closing_time = "Invalid Time"

        turf_data.append({
            'turf_id': turf.turf_id,
            'turf_name': turf.turf_name,
            'turf_address': turf.turf_address,
            'turf_street': turf.turf_street,
            'turf_dist': turf.turf_dist,
            'turf_pin': turf.turf_pin,
            'turf_phno': turf.turf_phno,
            'price_per_hour': turf.price_per_hour,
            'turf_desc': turf.turf_desc,
            'images': [base64.b64encode(image.image).decode('utf-8') for image in images],
            'categories': categories,
            'subcategories': subcategories,
            'turf_opening_time': opening_time,
            'turf_closing_time': closing_time
        })
    
    return render_template("view_turfs.html", owner=owner, turfs=turf_data)





@owner_bp.route("/bookings")
def owner_bookings():
    if session.get('login_type') != 'turf_owner':
        return redirect(url_for('main.login'))

    username = session.get('username')
    owner = TurfOwner.query.filter_by(username=username).first()
    if not owner:
        flash("Please login to view bookings", "error")
        return redirect(url_for('main.login'))

    query = text("""
        SELECT 
            b.booking_id,
            b.play_date,
            b.start_time,
            b.end_time,
            b.total_amount,
            b.booking_status,
            b.special_requests,
            t.turf_name,
            c.cust_fname,
            c.cust_lname
        FROM tbl_booking b
        JOIN tbl_turf t ON b.turf_id = t.turf_id
        JOIN tbl_cust c ON b.cust_id = c.cust_id
        WHERE t.owner_id = :owner_id
        ORDER BY b.play_date DESC, b.start_time ASC
    """)

    bookings = db.session.execute(query, {'owner_id': owner.owner_id}).fetchall()
    booking_data = []

    for row in bookings:
        # Safely handle time formatting
        def format_time(time_obj):
            if isinstance(time_obj, timedelta):
                # Convert timedelta to hours and minutes
                total_minutes = int(time_obj.total_seconds() / 60)
                hours, minutes = divmod(total_minutes, 60)
                return f"{hours:02d}:{minutes:02d}"
            else:
                return time_obj.strftime('%I:%M %p')

        booking_data.append({
            'booking_id': row.booking_id,
            'turf_name': row.turf_name,
            'customer_name': f"{row.cust_fname} {row.cust_lname}",
            'date': row.play_date.strftime('%d-%m-%Y'),
            'time_slot': f"{format_time(row.start_time)} - {format_time(row.end_time)}",
            'amount': float(row.total_amount),
            'status': row.booking_status,
            'special_requests': row.special_requests if row.special_requests else 'None'
        })

    return render_template("cbook.html", owner=owner, bookings=booking_data)


@owner_bp.route("/revenue")
def owner_revenue():
    if session.get('login_type') != 'turf_owner':
        return redirect(url_for('main.login'))

    username = session.get('username')
    owner = TurfOwner.query.filter_by(username=username).first()
    if not owner:
        flash("Owner not found!", "error")
        return redirect(url_for('main.login'))

    query = text("""
        SELECT 
            b.booking_id,
            b.play_date,
            b.start_time,
            b.end_time,
            b.total_amount,
            t.turf_name,
            c.cust_fname,
            c.cust_lname
        FROM tbl_booking b
        JOIN tbl_turf t ON b.turf_id = t.turf_id
        JOIN tbl_cust c ON b.cust_id = c.cust_id
        WHERE t.owner_id = :owner_id
        ORDER BY b.play_date DESC, b.start_time ASC
    """)

    bookings = db.session.execute(query, {'owner_id': owner.owner_id}).fetchall()
    booking_data = []

    def format_time(time_obj):
        if isinstance(time_obj, timedelta):
            total_minutes = int(time_obj.total_seconds() / 60)
            hours, minutes = divmod(total_minutes, 60)
            return f"{hours:02d}:{minutes:02d}"
        else:
            return time_obj.strftime('%I:%M %p')

    total_revenue = 0
    total_commission = 0
    total_owner_revenue = 0

    for row in bookings:
        admin_commission = row.total_amount * ADMIN_COMMISSION_PERCENTAGE / 100
        owner_revenue = row.total_amount - admin_commission

        total_revenue += float(row.total_amount)
        total_commission += admin_commission
        total_owner_revenue += owner_revenue

        booking_data.append({
            'booking_id': row.booking_id,
            'turf_name': row.turf_name,
            'customer_name': f"{row.cust_fname} {row.cust_lname}",
            'date': row.play_date.strftime('%d-%m-%Y'),
            'time_slot': f"{format_time(row.start_time)} - {format_time(row.end_time)}",
            'amount': float(row.total_amount),
            'admin_commission': admin_commission,
            'owner_revenue': owner_revenue
        })

    summary = {
        'total_revenue': total_revenue,
        'total_commission': total_commission,
        'total_owner_revenue': total_owner_revenue
    }

    return render_template("revenue.html", 
                         owner=owner, 
                         bookings=booking_data, 
                         summary=summary,
                         commission_percentage=ADMIN_COMMISSION_PERCENTAGE)
@owner_bp.route("/messages")
def owner_messages():
    if session.get('login_type') != 'turf_owner':
        return redirect(url_for('main.login'))
    
    username = session.get('username')
    owner = TurfOwner.query.filter_by(username=username).first()
    
    if not owner:
        flash("Owner not found!", "error")
        return redirect(url_for('main.login'))

    # Fetch messages where the recipient matches the owner's username
    messages = Message.query.filter_by(recipient=username).order_by(Message.created_at.desc()).all()

    return render_template("messages.html", owner=owner, messages=messages)


@owner_bp.route("/tprofile")
def owner_profile():
    if session.get('login_type') != 'turf_owner':
        return redirect(url_for('main.login'))
    
    owner = TurfOwner.query.filter_by(username=session.get('username')).first()
    return render_template("tprofile.html", owner=owner)

@owner_bp.route("/edit_tprofile", methods=['GET', 'POST'])
def edit_profile():
    if session.get('login_type') != 'turf_owner':
        return redirect(url_for('main.login'))
    
    owner = TurfOwner.query.filter_by(username=session.get('username')).first()
    
    if request.method == 'POST':
        owner.owner_fname = request.form.get('first_name')
        owner.owner_lname = request.form.get('last_name')
        owner.owner_phno = request.form.get('phone')
        owner.owner_housename = request.form.get('house_name')
        owner.owner_street = request.form.get('street')
        owner.owner_dist = request.form.get('district')
        owner.owner_pin = request.form.get('pin_code')
        owner.owner_gender = request.form.get('gender')
        
        try:
            db.session.commit()
            flash("Profile updated successfully!", "success")
            return redirect(url_for('owner.owner_profile'))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {e}", "error")
    
    return render_template("edit_tprofile.html", owner=owner)

@owner_bp.route("/delete_turf/<int:turf_id>", methods=['GET'])
def delete_turf(turf_id):
    turf = Turf.query.get_or_404(turf_id)
    db.session.delete(turf)
    db.session.commit()
    flash("Turf deleted successfully!", "success")
    return redirect(url_for('owner.view_turfs'))


@owner_bp.route("/weather")
def weather():
    if session.get('login_type') != 'turf_owner':
        return redirect(url_for('main.login'))
    
    username = session.get('username')
    owner = TurfOwner.query.filter_by(username=username).first()
    
    return render_template("tweather.html", owner=owner)


@owner_bp.route("/inventory")
def inventory():
    if session.get('login_type') != 'turf_owner':
        return redirect(url_for('main.login'))
    
    username = session.get('username')
    owner = TurfOwner.query.filter_by(username=username).first()
    
    return render_template("tinventory.html", owner=owner)

@owner_bp.route("/promotions")
def promotions():
    if session.get('login_type') != 'turf_owner':
        return redirect(url_for('main.login'))
    
    username = session.get('username')
    owner = TurfOwner.query.filter_by(username=username).first()
    
    return render_template("tpromotions.html", owner=owner)


@owner_bp.route("/messages/reply", methods=["POST"])
def reply_message():
    if session.get('login_type') != 'turf_owner':
        return redirect(url_for('main.login'))

    recipient = request.form.get("recipient")
    subject = request.form.get("subject")
    reply_content = request.form.get("reply_content")
    sender_email = session.get('email')  # Assuming the email is stored in session

    if not sender_email:
        flash("Your email is missing. Please update your profile.", "error")
        return redirect(url_for('owner.owner_messages'))


    if not recipient or not reply_content:
        flash("Missing recipient or message content", "error")
        return redirect(url_for('owner.owner_messages'))

    # Create a new reply message
    new_reply = Message(
        sender_name="Turf Owner",
        sender_email=sender_email,
        recipient=recipient,
        subject=subject,
        content=reply_content
    )

    db.session.add(new_reply)
    db.session.commit()

    flash("Reply sent successfully!", "success")
    return redirect(url_for('owner.owner_messages'))


@owner_bp.route('/turf/<int:turf_id>/amenity', methods=['GET', 'POST'])
def add_amenity(turf_id):
    # Fetch the turf name from tbl_turf using turf_id
    turf = db.session.execute(db.select(Turf).filter_by(turf_id=turf_id)).scalar_one_or_none()
    
    if not turf:
        flash('Turf not found!', 'error')
        return redirect(url_for('owner.dashboard'))  # Redirect to a relevant page

    if request.method == 'POST':
        amenity_name = request.form.get('amenity_name')
        
        if amenity_name:
            new_amenity = TurfAmenity(turf_id=turf_id, amenity_name=amenity_name)
            db.session.add(new_amenity)
            db.session.commit()
            flash('Amenity added successfully!', 'success')
        
        return redirect(url_for('owner.add_amenity', turf_id=turf_id))

    amenities = TurfAmenity.query.filter_by(turf_id=turf_id).all()
    return render_template('amenpol.html', turf_name=turf.turf_name, amenities=amenities, turf_id=turf_id)



@owner_bp.route('/turf/<int:turf_id>/policy', methods=['GET', 'POST'])
def add_policy(turf_id):
    # Fetch the turf details
    turf = db.session.execute(db.select(Turf).filter_by(turf_id=turf_id)).scalar_one_or_none()

    if not turf:
        flash('Turf not found!', 'error')
        return redirect(url_for('owner.dashboard'))

    if request.method == 'POST':
        policy_type = request.form.get('policy_type')  # Get selected policy type
        policy_text = request.form.get('policy_text')

        if policy_type and policy_text:
            new_policy = TurfPolicy(turf_id=turf_id, policy_type=policy_type, policy_text=policy_text)
            db.session.add(new_policy)
            db.session.commit()
            flash('Policy added successfully!', 'success')

        return redirect(url_for('owner.add_policy', turf_id=turf_id))

    # Fetch existing policies for this turf
    policies = TurfPolicy.query.filter_by(turf_id=turf_id).all()

    return render_template('policy.html', turf_name=turf.turf_name, policies=policies, turf_id=turf_id)









@owner_bp.route("/reviews")
def reviews():
    if session.get('login_type') != 'turf_owner':
        return redirect(url_for('main.login'))
    
    username = session.get('username')
    owner = TurfOwner.query.filter_by(username=username).first()
    
    return render_template("treview.html", owner=owner)