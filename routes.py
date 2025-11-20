
from io import BytesIO
from flask import Blueprint, jsonify, render_template, redirect, send_file, url_for, request, flash, session
from sqlalchemy import func
from . import db
from .models import Category, Customer, Login, Refund, RefundPolicy, Review, TurfAmenity, TurfImage, TurfOwner, Turf, Booking, Payment, Card, TurfPolicy, UPI_Payment, NetBanking_Payment,Message,turf_category
from werkzeug.security import generate_password_hash, check_password_hash
import base64
from datetime import datetime
from sqlalchemy.orm import joinedload


bp = Blueprint("main", __name__)

@bp.route('/landing')
@bp.route('/')
def landing():
    # Render the landing page that will redirect to home after 10 seconds
    return render_template('landing.html')





@bp.route('/home')
def home():
    turfs = Turf.query.limit(3).all()
    categories = Category.query.all()
    locations = db.session.query(Turf.turf_dist).distinct().all()

    # Fetch number of customers
    customer_count = db.session.query(func.count(Login.id)).filter(Login.login_type == "customer").scalar()

    # Fetch number of turfs
    turf_count = db.session.query(func.count(Turf.turf_id)).scalar()

    # Fetch distinct district count
    district_count = db.session.query(func.count(func.distinct(Turf.turf_dist))).scalar()

    # Fetch number of sports available
    sports_count = db.session.query(func.count(Category.cat_id)).scalar()

    # Fetch images for each turf
    for turf in turfs:
        image = TurfImage.query.filter_by(turf_id=turf.turf_id).first()
        if image:
            turf.turf_image = base64.b64encode(image.image).decode('utf-8')  # Convert BLOB to base64
        else:
            turf.turf_image = None  # Handle missing images

    return render_template(
        'home.html', 
        turfs=turfs, 
        categories=categories, 
        locations=locations, 
        customer_count=customer_count, 
        turf_count=turf_count, 
        district_count=district_count,
        sports_count=sports_count
    )




@bp.route("/admin/dashboard")
def admin_dashboard():
    if session.get('login_type') != 'admin':
        return redirect(url_for('main.login'))

    total_customers = Customer.query.count()
    total_users = Login.query.count()

    return render_template("admin_dashboard.html", total_customers=total_customers, total_users=total_users)

@bp.route("/admin/users")
def admin_manage_users():
    if session.get('login_type') != 'admin':
        return redirect(url_for('main.login'))

    users = Login.query.all()
    return render_template("manage_users.html", users=users)

@bp.route("/admin/turfs")
def admin_manage_turfs():
    if session.get('login_type') != 'admin':
        return redirect(url_for('main.login'))

    turfs = Turf.query.all()
    return render_template("manage_turfs.html", turfs=turfs)

@bp.route("/admin/users/delete/<int:user_id>", methods=['POST'])
def admin_delete_user(user_id):
    if session.get('login_type') != 'admin':
        return redirect(url_for('main.login'))

    user = Login.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash("User deleted successfully.", "success")
    else:
        flash("User not found.", "error")

    return redirect(url_for('main.admin_manage_users'))

@bp.route("/admin/turfs/delete/<int:turf_id>", methods=['POST'])
def admin_delete_turf(turf_id):
    if session.get('login_type') != 'admin':
        return redirect(url_for('main.login'))

    turf = Turf.query.get(turf_id)
    if turf:
        db.session.delete(turf)
        db.session.commit()
        flash("Turf deleted successfully.", "success")
    else:
        flash("Turf not found.", "error")

    return redirect(url_for('main.admin_manage_turfs'))




@bp.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = Login.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["username"] = user.username
            session["login_type"] = user.login_type

            next_page = request.args.get('next')
            if next_page:
                return redirect(url_for(f'main.{next_page}'))
            if user.login_type == 'admin':
                return redirect(url_for('main.admin_dashboard'))
            elif user.login_type == 'turf_owner':
                return redirect(url_for('owner.dashboard'))
            else:
                return redirect(url_for('main.location'))

        flash("Invalid username or password", "error")
        return redirect(url_for('main.login'))

    return render_template("login.html")


import base64
from flask import Blueprint, render_template, request, redirect, url_for
from .models import db, Turf, TurfImage, Category

@bp.route("/search")
def search():
    query = request.args.get("query", "").strip()
    category = request.args.get("category", "").strip()
    location = request.args.get("location", "").strip()

    # Start query
    turfs = Turf.query

    if query:
        turfs = turfs.filter(Turf.turf_name.ilike(f"%{query}%"))
    
    if category:
        category_obj = Category.query.filter_by(cat_name=category).first()
        if category_obj:
            turfs = turfs.filter(Turf.categories.any(cat_id=category_obj.cat_id))

    if location:
        turfs = turfs.filter(Turf.turf_dist.ilike(f"%{location}%"))

    turfs = turfs.all()

    # Fetch images for each turf from turf_images table and convert them to base64
    turf_images = {}
    for turf in turfs:
        image_record = TurfImage.query.filter_by(turf_id=turf.turf_id).first()
        if image_record and image_record.image:
            # Convert BLOB to base64 string
            image_base64 = base64.b64encode(image_record.image).decode('utf-8')
            turf_images[turf.turf_id] = image_base64
        else:
            turf_images[turf.turf_id] = None  # No image available

    return render_template("search_results.html", turfs=turfs, turf_images=turf_images)




@bp.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        house_name = request.form.get('house_name')
        street = request.form.get('street')
        district = request.form.get('district')
        pin_code = request.form.get('pin_code')
        gender = request.form.get('gender')
        user_type = request.form.get('user_type')

        try:
            hashed_password = generate_password_hash(password)
            new_login = Login(
                username=username,
                password=hashed_password,
                login_type=user_type
            )
            db.session.add(new_login)
            db.session.commit()

            if user_type == 'customer':
                new_customer = Customer(
                    username=username,
                    cust_fname=first_name,
                    cust_lname=last_name,
                    cust_phone=phone,
                    cust_housename=house_name,
                    cust_street=street,
                    cust_dist=district,
                    cust_pin=pin_code,
                    cust_gender=gender,
                    cust_status=True
                )
                db.session.add(new_customer)
            elif user_type == 'turf_owner':
                new_owner = TurfOwner(
                    username=username,
                    owner_fname=first_name,
                    owner_lname=last_name,
                    owner_phno=phone,
                    owner_housename=house_name,
                    owner_street=street,
                    owner_dist=district,
                    owner_pin=pin_code,
                    owner_gender=gender,
                    owner_status=True
                )
                db.session.add(new_owner)

            db.session.commit()
            return redirect(url_for('main.login'))

        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {e}", "error")
            return redirect(url_for('main.signup'))

    return render_template("signup.html")

@bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out", "success")
    return redirect(url_for('main.login'))

@bp.route("/booking")
def booking():
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    # Fetch the customer record using the username from session
    customer = Customer.query.filter_by(username=session["username"]).first()
    if not customer:
        flash("Customer record not found", "error")
        return redirect(url_for('main.home'))

    # Fetch all bookings for the logged-in customer
    bookings = Booking.query.filter_by(cust_id=customer.cust_id).all()
    
    return render_template("booking.html", bookings=bookings)

@bp.route("/video/<filename>")
def serve_video(filename):
    return f"Serve the video file: {filename}"

@bp.route('/hturfs')
def turfs():
    # Using eager loading to avoid N+1 query problem
    all_turfs = Turf.query.options(
        db.joinedload(Turf.categories),
        db.joinedload(Turf.subcategories)
    ).all()
    return render_template('hturfs.html', turfs=all_turfs)

@bp.route("/location")
def location():
    return render_template("location.html")

@bp.route("/turfs/<district>")
def turfs_by_district(district):
    # Fetch turfs in the selected district
    turfs_in_district = Turf.query.filter_by(turf_dist=district.strip()).all()
    
    # Get all turf IDs in the selected district
    turf_ids = [turf.turf_id for turf in turfs_in_district]

    # Fetch unique category IDs linked to these turfs via turf_category
    category_ids = db.session.query(turf_category.c.cat_id).filter(turf_category.c.turf_id.in_(turf_ids)).distinct()

    # Fetch category names using the extracted category IDs
    district_categories = Category.query.filter(Category.cat_id.in_(category_ids)).all()

    return render_template(
        "turfs_by_district.html", 
        district=district, 
        turfs=turfs_in_district, 
        district_categories=district_categories
    )




@bp.route("/turf/<int:turf_id>")
def turf_details(turf_id):
    turf = Turf.query.get_or_404(turf_id)

    # Convert images to base64
    images_base64 = []
    if turf.images:
        for image_obj in turf.images:
            if image_obj.image:
                images_base64.append(base64.b64encode(image_obj.image).decode('utf-8'))

    # Fetch amenities for this turf
    amenities = TurfAmenity.query.filter_by(turf_id=turf_id).all()

    # Fetch Ground and Refund policies separately
    ground_policies = TurfPolicy.query.filter_by(turf_id=turf_id, policy_type="Ground").all()
    refund_policies = TurfPolicy.query.filter_by(turf_id=turf_id, policy_type="Refund").all()

    return render_template(
        "turf_details.html",
        turf=turf,
        images_base64=images_base64,
        turf_opening_time=turf.turf_opening_time,
        turf_closing_time=turf.turf_closing_time,
        amenities=amenities,
        ground_policies=ground_policies,
        refund_policies=refund_policies
    )





@bp.route("/book_turf/<int:turf_id>", methods=['POST'])
def book_turf(turf_id):
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    # First get the customer record using the username from session
    customer = Customer.query.filter_by(username=session["username"]).first()
    if not customer:
        flash("Customer record not found", "error")
        return redirect(url_for('main.turf_details', turf_id=turf_id))

    # Get form data
    category_id = request.form.get("category")
    subcategory_id = request.form.get("subcategory")
    booking_date = request.form.get("booking_date")
    start_time = request.form.get("start_time")
    end_time = request.form.get("end_time")
    special_requests = request.form.get("special_requests")

    try:
        # Validate if the slot is already booked
        existing_booking = Booking.query.filter_by(
            turf_id=turf_id,
            play_date=datetime.strptime(booking_date, "%Y-%m-%d").date(),
            booking_status="Confirmed"
        ).first()

        if existing_booking:
            # Check if time slots overlap
            new_start = datetime.strptime(start_time, "%H:%M").time()
            new_end = datetime.strptime(end_time, "%H:%M").time()
            if (new_start >= existing_booking.start_time and new_start < existing_booking.end_time) or \
               (new_end > existing_booking.start_time and new_end <= existing_booking.end_time):
                flash("This time slot is already booked. Please choose a different time.", "error")
                return redirect(url_for('main.turf_details', turf_id=turf_id))

        # Calculate total amount
        start_dt = datetime.strptime(start_time, "%H:%M")
        end_dt = datetime.strptime(end_time, "%H:%M")
        diff_in_hours = (end_dt - start_dt).seconds / 3600
        
        # Validate booking duration
        if (diff_in_hours <= 0):
            flash("Invalid time selection. End time must be after start time.", "error")
            return redirect(url_for('main.turf_details', turf_id=turf_id))

        turf = Turf.query.get_or_404(turf_id)
        total_amount = float(diff_in_hours) * float(turf.price_per_hour)

        # Create a booking record in the database
        new_booking = Booking(
            cust_id=customer.cust_id,
            turf_id=turf_id,
            booking_datetime=datetime.utcnow(),
            play_date=datetime.strptime(booking_date, "%Y-%m-%d").date(),
            start_time=start_dt.time(),
            end_time=end_dt.time(),
            total_hours=diff_in_hours,
            total_amount=total_amount,
            payment_status=False,
            booking_status="Pending",
            special_requests=special_requests
        )

        db.session.add(new_booking)
        db.session.commit()

        # Redirect to payment page with the new booking ID
        return redirect(url_for('main.payment', booking_id=new_booking.booking_id))
        
    except ValueError as ve:
        db.session.rollback()
        flash(f"Invalid date or time format: {str(ve)}", "error")
        return redirect(url_for('main.turf_details', turf_id=turf_id))
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('main.turf_details', turf_id=turf_id))

@bp.route("/payment/<int:booking_id>")
def payment(booking_id):
    if "user_id" not in session:
        return redirect(url_for("main.login"))
        
    # Get booking details
    booking = Booking.query.get_or_404(booking_id)
    turf = Turf.query.get(booking.turf_id)
    
    # Verify that the booking belongs to the logged-in user
    customer = Customer.query.filter_by(username=session["username"]).first()
    if booking.cust_id != customer.cust_id:
        flash("Unauthorized access", "error")
        return redirect(url_for("main.booking"))
        
    return render_template(
        "payment.html",
        booking=booking,
        turf=turf,
        customer=customer
    )


@bp.route("/process_upi_payment/<int:booking_id>", methods=['POST'])
def process_upi_payment(booking_id):
    if "user_id" not in session:
        return redirect(url_for("main.login"))
        
    upi_id = request.form.get('upi_id')
    booking = Booking.query.get_or_404(booking_id)
    
    try:
        # Here, you would integrate with your payment gateway to process the UPI payment.
        # For this example, we'll assume the payment is successful.
        
        # Create a payment record
        new_payment = Payment(
            booking_id=booking_id,
            cust_id=booking.cust_id,
            total_amount=booking.total_amount,
            payment_status=True,
            payment_method='upi',
            payment_date=datetime.utcnow()
        )
        db.session.add(new_payment)
        db.session.commit()

        # Create a UPI record
        new_upi = UPI_Payment(
            payment_id=new_payment.payment_id,
            cust_id=booking.cust_id,
            upi_id=upi_id
        )
        db.session.add(new_upi)
        db.session.commit()

        # Update booking payment status
        booking.payment_status = True
        booking.booking_status = "Confirmed"
        db.session.commit()
        
        # Redirect to the confirmation page
        return redirect(url_for('main.payment_confirmation', booking_id=booking_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f"UPI Payment failed: {str(e)}", "error")
        return redirect(url_for('main.upi_payment', booking_id=booking_id))

@bp.route("/payment_confirmation/<int:booking_id>")
def payment_confirmation(booking_id):
    if "user_id" not in session:
        return redirect(url_for("main.login"))
        
    booking = Booking.query.get_or_404(booking_id)
    return render_template("payment_confirmation.html", booking=booking)

@bp.route("/process_payment/<int:booking_id>", methods=['POST'])
def process_payment(booking_id):
    if "user_id" not in session:
        return redirect(url_for("main.login"))
        
    payment_method = request.form.get('payment_method')
    booking = Booking.query.get_or_404(booking_id)
    
    try:
        # Update booking payment status
        booking.payment_status = True
        booking.booking_status = "Confirmed"
        db.session.commit()
        
        flash("Payment successful! Your booking is confirmed.", "success")
        return redirect(url_for('main.booking'))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Payment failed: {str(e)}", "error")
        return redirect(url_for('main.payment', booking_id=booking_id))


@bp.route("/upi_payment/<int:booking_id>")
def upi_payment(booking_id):
    if "user_id" not in session:
        return redirect(url_for("main.login"))
    
    return render_template("upi_payment.html", booking_id=booking_id)


@bp.route("/gpay/<int:booking_id>")
def gpay(booking_id):
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    # Fetch booking and customer details
    booking = Booking.query.get_or_404(booking_id)
    customer = Customer.query.get_or_404(booking.cust_id)

    # Extract first letter from first name
    first_letter = customer.cust_fname[0].upper()

    # Mask phone number (Show first 2 & last 2 digits)
    masked_phone = customer.cust_phone[:2] + "*****" + customer.cust_phone[-2:]

    # Ensure `booking_id` is explicitly passed
    return render_template("gpay.html", 
                           first_letter=first_letter, 
                           full_name=f"{customer.cust_fname} {customer.cust_lname}", 
                           masked_phone=masked_phone, 
                           amount=booking.total_amount,
                           booking_id=booking_id)  # Ensure booking_id is passed






@bp.route("/process_gpay_payment/<int:booking_id>", methods=['POST'])
def process_gpay_payment(booking_id):
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    # Fetch booking details
    booking = Booking.query.get_or_404(booking_id)

    try:
        # Create a payment record
        new_payment = Payment(
            booking_id=booking_id,
            cust_id=booking.cust_id,
            total_amount=booking.total_amount,
            payment_status=True,
            payment_method='upi',
            payment_date=datetime.utcnow()
        )
        db.session.add(new_payment)
        db.session.commit()

        # Insert into UPI Payment table with "gpay" as upi_id
        new_upi_payment = UPI_Payment(
            payment_id=new_payment.payment_id,
            cust_id=booking.cust_id,
            upi_id="gpay"  # Fixed UPI ID as "gpay"
        )
        db.session.add(new_upi_payment)
        db.session.commit()

        # Update booking payment status
        booking.payment_status = True
        booking.booking_status = "Confirmed"
        db.session.commit()

        flash("Payment successful via GPay!", "success")
        return redirect(url_for('main.payment_confirmation', booking_id=booking_id))

    except Exception as e:
        db.session.rollback()
        flash(f"GPay Payment failed: {str(e)}", "error")
        return redirect(url_for('main.gpay', booking_id=booking_id))





@bp.route("/phonepe/<int:booking_id>")
def phonepe(booking_id):
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    # Fetch booking and customer details
    booking = Booking.query.get_or_404(booking_id)
    customer = Customer.query.get_or_404(booking.cust_id)

    # Extract first letter from first name
    first_letter = customer.cust_fname[0].upper()

    # Mask phone number (Show first 2 & last 2 digits)
    masked_phone = customer.cust_phone[:2] + "*****" + customer.cust_phone[-2:]

    # Ensure `booking_id` is explicitly passed
    return render_template("phonepe.html", 
                           first_letter=first_letter, 
                           full_name=f"{customer.cust_fname} {customer.cust_lname}", 
                           masked_phone=masked_phone, 
                           amount=booking.total_amount,
                           booking_id=booking_id)  # Ensure booking_id is passed




@bp.route("/process_phonepe_payment/<int:booking_id>", methods=['POST'])
def process_phonepe_payment(booking_id):
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    # Fetch booking details
    booking = Booking.query.get_or_404(booking_id)

    try:
        # Create a payment record
        new_payment = Payment(
            booking_id=booking_id,
            cust_id=booking.cust_id,
            total_amount=booking.total_amount,
            payment_status=True,
            payment_method='upi',
            payment_date=datetime.utcnow()
        )
        db.session.add(new_payment)
        db.session.commit()

        # Insert into UPI Payment table with "phonepe" as upi_id
        new_upi_payment = UPI_Payment(
            payment_id=new_payment.payment_id,
            cust_id=booking.cust_id,
            upi_id="phonepe"  # Fixed UPI ID as "phonepe"
        )
        db.session.add(new_upi_payment)
        db.session.commit()

        # Update booking payment status
        booking.payment_status = True
        booking.booking_status = "Confirmed"
        db.session.commit()

        flash("Payment successful via PhonePe!", "success")
        return redirect(url_for('main.payment_confirmation', booking_id=booking_id))

    except Exception as e:
        db.session.rollback()
        flash(f"PhonePe Payment failed: {str(e)}", "error")
        return redirect(url_for('main.phonepe', booking_id=booking_id))




@bp.route("/paytm/<int:booking_id>")
def paytm(booking_id):
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    # Fetch booking and customer details
    booking = Booking.query.get_or_404(booking_id)
    customer = Customer.query.get_or_404(booking.cust_id)

    # Extract first letter from first name
    first_letter = customer.cust_fname[0].upper()

    # Mask phone number (Show first 2 & last 2 digits)
    masked_phone = customer.cust_phone[:2] + "*****" + customer.cust_phone[-2:]

    # Ensure `booking_id` is explicitly passed
    return render_template("paytm.html", 
                           first_letter=first_letter, 
                           full_name=f"{customer.cust_fname} {customer.cust_lname}", 
                           masked_phone=masked_phone, 
                           amount=booking.total_amount,
                           booking_id=booking_id)  # Ensure booking_id is passed



@bp.route("/process_paytm_payment/<int:booking_id>", methods=['POST'])
def process_paytm_payment(booking_id):
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    # Fetch booking details
    booking = Booking.query.get_or_404(booking_id)

    try:
        # Create a payment record
        new_payment = Payment(
            booking_id=booking_id,
            cust_id=booking.cust_id,
            total_amount=booking.total_amount,
            payment_status=True,
            payment_method='upi',
            payment_date=datetime.utcnow()
        )
        db.session.add(new_payment)
        db.session.commit()

        # Insert into UPI Payment table with "paytm" as upi_id
        new_upi_payment = UPI_Payment(
            payment_id=new_payment.payment_id,
            cust_id=booking.cust_id,
            upi_id="paytm"  # Fixed UPI ID as "paytm"
        )
        db.session.add(new_upi_payment)
        db.session.commit()

        # Update booking payment status
        booking.payment_status = True
        booking.booking_status = "Confirmed"
        db.session.commit()

        flash("Payment successful via Paytm!", "success")
        return redirect(url_for('main.payment_confirmation', booking_id=booking_id))

    except Exception as e:
        db.session.rollback()
        flash(f"Paytm Payment failed: {str(e)}", "error")
        return redirect(url_for('main.paytm', booking_id=booking_id))






@bp.route("/bhim/<int:booking_id>")
def bhim(booking_id):
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    # Fetch booking and customer details
    booking = Booking.query.get_or_404(booking_id)
    customer = Customer.query.get_or_404(booking.cust_id)

    # Extract first letter from first name
    first_letter = customer.cust_fname[0].upper()

    # Mask phone number (Show first 2 & last 2 digits)
    masked_phone = customer.cust_phone[:2] + "*****" + customer.cust_phone[-2:]

    # Ensure `booking_id` is explicitly passed
    return render_template("bhim.html", 
                           first_letter=first_letter, 
                           full_name=f"{customer.cust_fname} {customer.cust_lname}", 
                           masked_phone=masked_phone, 
                           amount=booking.total_amount,
                           booking_id=booking_id)  # Ensure booking_id is passed



@bp.route("/process_bhim_payment/<int:booking_id>", methods=['POST'])
def process_bhim_payment(booking_id):
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    # Fetch booking details
    booking = Booking.query.get_or_404(booking_id)

    try:
        # Create a payment record
        new_payment = Payment(
            booking_id=booking_id,
            cust_id=booking.cust_id,
            total_amount=booking.total_amount,
            payment_status=True,
            payment_method='upi',
            payment_date=datetime.utcnow()
        )
        db.session.add(new_payment)
        db.session.commit()

        # Insert into UPI Payment table with "bhim" as upi_id
        new_upi_payment = UPI_Payment(
            payment_id=new_payment.payment_id,
            cust_id=booking.cust_id,
            upi_id="bhim"  # Fixed UPI ID as "bhim"
        )
        db.session.add(new_upi_payment)
        db.session.commit()

        # Update booking payment status
        booking.payment_status = True
        booking.booking_status = "Confirmed"
        db.session.commit()

        flash("Payment successful via BHIM!", "success")
        return redirect(url_for('main.payment_confirmation', booking_id=booking_id))

    except Exception as e:
        db.session.rollback()
        flash(f"BHIM Payment failed: {str(e)}", "error")
        return redirect(url_for('main.bhim', booking_id=booking_id))




@bp.route("/card_payment/<int:booking_id>")
def card_payment(booking_id):
    if "user_id" not in session:
        return redirect(url_for("main.login"))
    
    return render_template("card_payment.html", booking_id=booking_id)

@bp.route("/netbanking_payment/<int:booking_id>")
def netbanking_payment(booking_id):
    if "user_id" not in session:
        return redirect(url_for("main.login"))
    
    return render_template("netbanking_payment.html", booking_id=booking_id)



@bp.route("/process_card_payment/<int:booking_id>", methods=['POST'])
def process_card_payment(booking_id):
    if "user_id" not in session:
        return redirect(url_for("main.login"))
    
    try:
        # Print all form data for debugging
        print("Form Data:")
        print("Card Holder Name:", request.form.get('card_holder_name'))
        print("Card Number:", request.form.get('card_number'))
        print("Expiry Date:", request.form.get('expiry_date'))
        print("Bank Name:", request.form.get('bank_name'))
        print("Card Type:", request.form.get('card_type'))
        
        # Get booking
        booking = Booking.query.get_or_404(booking_id)
        print("Booking ID:", booking_id)
        print("Customer ID:", booking.cust_id)
        
        # Parse form data
        card_holder_name = request.form.get('card_holder_name')
        card_number = request.form.get('card_number')
        expiry_date = request.form.get('expiry_date')
        bank_name = request.form.get('bank_name')
        card_type = request.form.get('card_type')
        
        # Parse expiry date
        month, year = expiry_date.split('/')
        exp_date = datetime(2000 + int(year), int(month), 1)
        print("Parsed Expiry Date:", exp_date)
        
        # Create new card record
        new_card = Card(
            cust_id=booking.cust_id,
            card_holder_name=card_holder_name,
            card_no=card_number.replace(' ', ''),
            bank_name=bank_name,
            card_type=card_type,
            exp_date=exp_date,
            card_status=True
        )
        
        print("Created Card Object:", vars(new_card))
        
        # Add and flush card
        db.session.add(new_card)
        db.session.flush()
        print("Card ID after flush:", new_card.card_id)
        
        # Create payment record
        new_payment = Payment(
            booking_id=booking_id,
            cust_id=booking.cust_id,
            total_amount=booking.total_amount,
            payment_status=True,
            payment_method='credit_card' if card_type == 'credit' else 'debit_card',
            payment_date=datetime.utcnow()
        )
        
        print("Created Payment Object:", vars(new_payment))
        
        # Add payment and update booking
        db.session.add(new_payment)
        booking.payment_status = True
        booking.booking_status = "Confirmed"
        
        # Commit all changes
        print("Attempting to commit...")
        db.session.commit()
        print("Commit successful!")
        
        flash("Payment processed successfully!", "success")
        return redirect(url_for('main.payment_confirmation', booking_id=booking_id))
        
    except ValueError as e:
        db.session.rollback()
        print("ValueError occurred:", str(e))
        flash(f"Invalid card details: {str(e)}", "error")
        return redirect(url_for('main.card_payment', booking_id=booking_id))
    except Exception as e:
        db.session.rollback()
        print("Exception occurred:", str(e))
        print("Exception type:", type(e))
        flash(f"Card Payment failed: {str(e)}", "error")
        return redirect(url_for('main.card_payment', booking_id=booking_id))
    


@bp.route("/process_netbanking_payment/<int:booking_id>", methods=['POST'])
def process_netbanking_payment(booking_id):
    if "user_id" not in session:
        return redirect(url_for("main.login"))
        
    bank_name = request.form.get('bank_name')
    account_number = request.form.get('account_number')
    ifsc_code = request.form.get('ifsc_code')
    booking = Booking.query.get_or_404(booking_id)
    
    try:
        # Here, you would integrate with your payment gateway to process the net banking payment.
        # For this example, we'll assume the payment is successful.
        
        # Create a payment record
        new_payment = Payment(
            booking_id=booking_id,
            cust_id=booking.cust_id,
            total_amount=booking.total_amount,
            payment_status=True,
            payment_method='netbanking',
            payment_date=datetime.utcnow()
        )
        db.session.add(new_payment)
        db.session.commit()

        # Create a net banking record
        new_netbanking = NetBanking_Payment(
            payment_id=new_payment.payment_id,
            cust_id=booking.cust_id,
            bank_name=bank_name,
            account_number=account_number,
            ifsc_code=ifsc_code
        )
        db.session.add(new_netbanking)
        db.session.commit()

        # Update booking payment status
        booking.payment_status = True
        booking.booking_status = "Confirmed"
        db.session.commit()
        
        # Redirect to the confirmation page
        return redirect(url_for('main.payment_confirmation', booking_id=booking_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Net Banking Payment failed: {str(e)}", "error")
        return redirect(url_for('main.netbanking_payment', booking_id=booking_id))
    

@bp.route("/admin/messages", methods=["GET", "POST"])
def admin_messages():
    if session.get('login_type') != 'admin':
        return redirect(url_for('main.login'))
    
    if request.method == "POST":
        sender_name = request.form.get("sender_name")
        sender_email = request.form.get("sender_email")
        recipient = request.form.get("recipient")
        subject = request.form.get("subject")
        content = request.form.get("content")
        
        new_message = Message(sender_name=sender_name, sender_email=sender_email, recipient=recipient, subject=subject, content=content)
        db.session.add(new_message)
        db.session.commit()
        flash("Message sent successfully!", "success")
        return redirect(url_for('main.admin_messages'))
    
    messages = Message.query.all()
    return render_template("admsg.html", messages=messages)


@bp.route("/turf/<int:turf_id>/review", methods=['POST'])
def post_review(turf_id):
    if "user_id" not in session:
        flash("Please log in to post a review.", "error")
        return redirect(url_for("main.login"))

    customer = Customer.query.filter_by(username=session["username"]).first()
    if not customer:
        flash("Customer record not found", "error")
        return redirect(url_for('main.turf_details', turf_id=turf_id))

    rating = request.form.get('rating')
    review_text = request.form.get('review_text')

    try:
        # Validate rating
        if not rating or not rating.isdigit() or int(rating) < 1 or int(rating) > 5:
            flash("Please provide a valid rating between 1 and 5.", "error")
            return redirect(url_for('main.turf_details', turf_id=turf_id))

        # Create new review record
        new_review = Review(
            cust_id=customer.cust_id,
            turf_id=turf_id,
            rating=int(rating),
            review_text=review_text
        )
        db.session.add(new_review)
        db.session.commit()

        flash("Review posted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "error")

    return redirect(url_for('main.turf_details', turf_id=turf_id))




@bp.route("/submit_review", methods=['POST'])
def submit_review():
    if "user_id" not in session:
        flash("Please login to submit a review", "error")
        return redirect(url_for("main.login"))
    
    try:
        # Extract form data
        booking_id = request.form.get('booking_id')
        turf_id = request.form.get('turf_id')
        rating = request.form.get('rating')
        review_content = request.form.get('review_content')
        
        # Log the received data for debugging
        print(f"Received data: booking_id={booking_id}, turf_id={turf_id}, rating={rating}, content={review_content}")
        
        # Validate data
        if not all([booking_id, turf_id, rating, review_content]):
            flash("All fields are required", "error")
            return redirect(url_for("main.profile"))
        
        # Check if review already exists for this booking
        existing_review = Review.query.filter_by(booking_id=booking_id).first()
        if existing_review:
            flash("You have already submitted a review for this booking", "error")
            return redirect(url_for("main.profile"))
        
        # Verify the associated booking exists and belongs to this customer
        booking = Booking.query.get(booking_id)
        if not booking or booking.cust_id != int(session["user_id"]):
            flash("Invalid booking selected", "error")
            return redirect(url_for("main.profile"))
            
        # Create new review with explicit type conversion
        new_review = Review(
            booking_id=int(booking_id),
            cust_id=int(session["user_id"]),
            turf_id=int(turf_id),
            rating=int(rating),
            review_content=review_content,
            review_date=datetime.utcnow()
        )
        
        # Debug: Print the review object
        print(f"Review object created: {new_review}")
        
        # Add and commit with explicit transaction management
        db.session.add(new_review)
        db.session.flush()  # Flush to get the new review_id
        print(f"Review ID after flush: {new_review.review_id}")
        db.session.commit()
        print("Review committed successfully")
        
        flash("Review submitted successfully!", "success")
        return redirect(url_for("main.profile"))
        
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"Exception: {str(e)}")
        print(traceback.format_exc())
        flash(f"Error submitting review: {str(e)}", "error")
        return redirect(url_for("main.profile"))






@bp.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session or session.get("login_type") != "customer":
        return redirect(url_for("main.login"))

    customer = Customer.query.filter_by(username=session["username"]).first()
    if not customer:
        flash("Customer record not found", "error")
        return redirect(url_for('main.home'))

    # Handle profile update form submission
    message, message_class, message_icon = None, None, None
    if request.method == "POST" and request.form.get("action") == "update_profile":
        try:
            customer.cust_fname = request.form.get("cust_fname")
            customer.cust_lname = request.form.get("cust_lname")
            customer.cust_phone = request.form.get("cust_phone")
            customer.cust_housename = request.form.get("cust_housename")
            customer.cust_street = request.form.get("cust_street")
            customer.cust_dist = request.form.get("cust_dist")
            customer.cust_pin = request.form.get("cust_pin")
            
            db.session.commit()
            
            message = "Profile updated successfully!"
            message_class = "alert-success"
            message_icon = "fas fa-check-circle"
        except Exception as e:
            db.session.rollback()
            message = f"Error updating profile: {str(e)}"
            message_class = "alert-error"
            message_icon = "fas fa-exclamation-circle"

    # Fetch all bookings for the logged-in customer with eager loading
    bookings = Booking.query.filter_by(cust_id=customer.cust_id).options(
        joinedload(Booking.review),
        joinedload(Booking.turf)
    ).all()

    # Fetch refunds and store in a dictionary for quick lookup
    refund_records = Refund.query.filter(Refund.booking_id.in_([b.booking_id for b in bookings])).all()
    refunds = {r.booking_id: r.refund_amount for r in refund_records}

    # Log fetched refunds for debugging
    print(f"Refunds fetched: {refunds}")

    # Categorize bookings based on play_date and status
    current_date = datetime.now().date()
    upcoming_bookings, completed_bookings, cancelled_bookings = [], [], []

    for booking in bookings:
        play_date = booking.play_date if not isinstance(booking.play_date, datetime) else booking.play_date.date()
        
        if booking.booking_status.lower() == 'cancelled':
            cancelled_bookings.append(booking)
        elif play_date >= current_date:
            upcoming_bookings.append(booking)
        else:
            completed_bookings.append(booking)

    # Sort bookings
    upcoming_bookings.sort(key=lambda x: x.play_date)
    completed_bookings.sort(key=lambda x: x.play_date, reverse=True)
    cancelled_bookings.sort(key=lambda x: x.play_date, reverse=True)

    return render_template(
        "cprofile.html", 
        customer=customer, 
        bookings=bookings,  
        upcoming_bookings=upcoming_bookings,
        completed_bookings=completed_bookings,
        cancelled_bookings=cancelled_bookings,
        refunds=refunds,  # ✅ Pass refund data to template
        message=message,
        message_class=message_class,
        message_icon=message_icon
    )




@bp.route("/cancel_booking", methods=["POST"])
def cancel_booking():
    if "user_id" not in session or session.get("login_type") != "customer":
        return jsonify({"success": False, "message": "Unauthorized access"}), 403

    try:
        data = request.get_json()
        booking_id = data.get("booking_id")

        if not booking_id:
            return jsonify({"success": False, "message": "No booking ID provided"}), 400

        # Fetch booking details
        booking = Booking.query.get(booking_id)
        if not booking:
            return jsonify({"success": False, "message": "Booking not found"}), 404

        # Ensure the logged-in user owns the booking
        customer = Customer.query.filter_by(username=session["username"]).first()
        if booking.cust_id != customer.cust_id:
            return jsonify({"success": False, "message": "Permission denied"}), 403

        # Fetch payment_id from tbl_payment
        payment = Payment.query.filter_by(booking_id=booking.booking_id).first()
        payment_id = payment.payment_id if payment else None  # Handle missing payment case

        # Corrected: Consider both play date and time
        play_datetime = datetime.combine(booking.play_date, booking.start_time)
        current_time = datetime.now()
        hours_before_play = (play_datetime - current_time).total_seconds() / 3600

        print(f"Booking ID: {booking_id}, Hours Before Play: {hours_before_play}")  # Debugging

        # Select refund policy based on cancellation time
        if hours_before_play >= 24:
            refund_policy = RefundPolicy.query.filter_by(cancellation_time_range="More than 24 hours before").first()
        elif 6 <= hours_before_play < 24:
            refund_policy = RefundPolicy.query.filter_by(cancellation_time_range="6 to 24 hours before").first()
        else:
            refund_policy = RefundPolicy.query.filter_by(cancellation_time_range="Less than 6 hours before").first()

        if not refund_policy:
            return jsonify({"success": False, "message": "No applicable refund policy found"}), 400

        print(f"Refund Policy ID: {refund_policy.policy_id}, Refund %: {refund_policy.refund_percentage}, Processing Fee: {refund_policy.processing_fee}")  # Debugging

        # Correct refund calculation
        refund_amount = (booking.total_amount * (refund_policy.refund_percentage / 100)) - refund_policy.processing_fee

        # Ensure refund is not negative
        refund_amount = max(round(refund_amount, 2), 0)

        print(f"Calculated Refund Amount: {refund_amount}")  # Debugging

        # Update booking status
        booking.booking_status = "Cancelled"
        db.session.commit()

        refund_status = 1 if refund_amount > 0 else 0  # 1 = processed, 0 = no refund

        # Insert refund record with payment_id
        new_refund = Refund(
            payment_id=payment_id,
            booking_id=booking.booking_id,
            cust_id=booking.cust_id,
            refund_amount=refund_amount,
            refund_reason="Customer cancelled the booking",
            refund_date=datetime.today(),
            refund_status=refund_status,
            policy_id=refund_policy.policy_id
        )

        db.session.add(new_refund)
        db.session.commit()

        return jsonify({"success": True, "message": "Booking cancelled and refund processed", "refund_amount": refund_amount})

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500









@bp.route('/turf_image/<int:image_id>')
def get_turf_image(image_id):
    image = TurfImage.query.get_or_404(image_id)
    return send_file(BytesIO(image.image), mimetype='image/jpeg')