# app/admin_panel.py
from flask import Blueprint, render_template, redirect, url_for, session, request, flash
from sqlalchemy import func,extract, select
from .models import Category, Customer, Payment, Refund, RefundPolicy, Subcategory, Turf, Login, TurfOwner,Booking
from . import db
from datetime import datetime
admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin_panel')

@admin_bp.route("/dashboard")
def dashboard():
    # Check admin authentication
    if session.get('login_type') != 'admin':
        flash('Please login as admin to access this page', 'error')
        return redirect(url_for('main.login'))

    try:
        # Get total counts
        total_customers = db.session.query(func.count()).select_from(db.table('tbl_cust')).scalar() or 0
        total_turfs = db.session.query(func.count()).select_from(db.table('tbl_turf')).scalar() or 0
        total_bookings = db.session.query(func.count()).select_from(db.table('tbl_booking')).scalar() or 0
        total_revenue = db.session.query(func.coalesce(func.sum(db.table('tbl_booking').c.total_amount), 0)).scalar() or 0

        # Get monthly booking counts using the same approach as your reports function
        monthly_data = db.session.query(
            func.date_format(Booking.play_date, '%m').label('month'),
            func.count(Booking.booking_id).label('count')
        ).group_by('month').order_by('month').all()

        # Prepare data for the chart
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        # Create lists for the chart
        months_bookings = []
        counts_bookings = []
        
        for data in monthly_data:
            if data.month and data.count:
                # Convert month number (01-12) to index (0-11) for the month_names array
                month_index = int(data.month) - 1
                if 0 <= month_index < 12:
                    months_bookings.append(month_names[month_index])
                    counts_bookings.append(data.count)

        return render_template(
            "admin_dashboard.html",
            total_customers=total_customers,
            total_turfs=total_turfs,
            total_bookings=total_bookings,
            total_revenue=total_revenue,
            booking_labels=months_bookings,  # Match the variable names you used in your template
            booking_values=counts_bookings   # Match the variable names you used in your template
        )

    except Exception as e:
        print(f"Error in dashboard route: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('main.admin_dashboard'))


@admin_bp.route("/notifications")
def notifications():
    if session.get('login_type') != 'admin':
        return redirect(url_for('main.login'))
    return render_template("adnot.html")


@admin_bp.route("/customers")
def view_customers():
    # Debug print statements
    print(f"Login Type: {session.get('login_type')}")
    
    if session.get('login_type') != 'admin':
        print("Unauthorized access attempt")
        return redirect(url_for('main.login'))

    try:
        customers = Customer.query.all()
        print(f"Customers found: {len(customers)}")
        
        customer_list = [
            {
                'id': customer.cust_id, 
                'name': f"{customer.cust_fname} {customer.cust_lname}",
                'email': customer.username,
                'phone': customer.cust_phone,
                'address': f"{customer.cust_housename}, {customer.cust_street}, {customer.cust_dist}"
            } for customer in customers
        ]
        return render_template("adcustomers.html", customers=customer_list)
    
    except Exception as e:
        print(f"Error fetching customers: {e}")
        return "Error retrieving customers", 500
    
@admin_bp.route("/adto")
def view_turf_owners():
    print(f"Login Type: {session.get('login_type')}")
    
    if session.get('login_type') != 'admin':
        print("Unauthorized access attempt")
        return redirect(url_for('main.login'))

    # Fetching turf owners based on their approval status
    pending_owners = TurfOwner.query.filter_by(owner_status='pending').all()
    approved_owners = TurfOwner.query.filter_by(owner_status='approved').all()
    rejected_owners = TurfOwner.query.filter_by(owner_status='rejected').all()

    return render_template("adto.html", 
                           pending_owners=pending_owners, 
                           approved_owners=approved_owners, 
                           rejected_owners=rejected_owners)



@admin_bp.route("/approve_turf_owner/<int:owner_id>", methods=["POST"])
def approve_turf_owner(owner_id):
    if session.get('login_type') != 'admin':
        return redirect(url_for('main.login'))

    owner = TurfOwner.query.get(owner_id)
    if owner:
        owner.owner_status = "approved"
        db.session.commit()
        flash("Turf owner approved successfully!", "success")
    else:
        flash("Turf owner not found!", "danger")

    return redirect(url_for('admin_bp.view_turf_owners'))

@admin_bp.route("/reject_turf_owner/<int:owner_id>", methods=["POST"])
def reject_turf_owner(owner_id):
    if session.get('login_type') != 'admin':
        return redirect(url_for('main.login'))

    owner = TurfOwner.query.get(owner_id)
    if owner:
        owner.owner_status = "rejected"
        db.session.commit()
        flash("Turf owner rejected successfully!", "success")
    else:
        flash("Turf owner not found!", "danger")

    return redirect(url_for('admin_bp.view_turf_owners'))




@admin_bp.route("/turfs")
def list_turfs():
    if session.get('login_type') != 'admin':
        return redirect(url_for('main.login'))

    # Ensure that all turfs are fetched correctly with their related data
    turfs = db.session.query(
        Turf,
        TurfOwner,
        Category,
        Subcategory
    ).outerjoin(
        TurfOwner, Turf.owner_id == TurfOwner.owner_id
    ).outerjoin(
        Turf.categories
    ).outerjoin(
        Turf.subcategories
    ).all()

    turfs_list = [
        {
            'turf_id': turf.Turf.turf_id,
            'turf_name': turf.Turf.turf_name,
            'owner_name': f"{turf.TurfOwner.owner_fname} {turf.TurfOwner.owner_lname}" if turf.TurfOwner else "Unknown",
            'turf_phno': turf.Turf.turf_phno,
            'turf_address': turf.Turf.turf_address,
            'turf_street': turf.Turf.turf_street,
            'turf_dist': turf.Turf.turf_dist,
            'turf_pin': turf.Turf.turf_pin,
            'price_per_hour': float(turf.Turf.price_per_hour),
            'turf_desc': turf.Turf.turf_desc,
            'category_name': turf.Category.cat_name if turf.Category else "Uncategorized",
            'subcategory_name': turf.Subcategory.sub_name if turf.Subcategory else "Uncategorized",
            'status': True  # Assuming all turfs are active for simplicity
        } for turf in turfs
    ]
    
    return render_template("adturf.html", turfs=turfs_list) 


    





@admin_bp.route("/bookings")
def list_bookings():
    if session.get('login_type') != 'admin':
        return redirect(url_for('main.login'))

    bookings = Booking.query.all()
    bookings_list = [
        {
            'id': booking.booking_id,
            'customer_name': f"{booking.customer.cust_fname} {booking.customer.cust_lname}",
            'turf_name': booking.turf.turf_name,
            'booking_datetime': booking.booking_datetime.strftime('%Y-%m-%d'),
            'time_slot': f"{booking.start_time} - {booking.end_time}",
            'total_amount': booking.total_amount,
            'status': booking.booking_status
        } for booking in bookings
    ]
    return render_template("adbk.html", bookings=bookings_list)

@admin_bp.route("/categories")
def view_categories():
    if session.get('login_type') != 'admin':
        return redirect(url_for('main.login'))

    categories = Category.query.all()
    return render_template("adcat.html", categories=categories)







@admin_bp.route("/add_subcategory", methods=["POST"])
def add_subcategory():
    if session.get('login_type') != 'admin':
        return redirect(url_for('main.login'))

    cat_id = request.form.get('cat_id')
    sub_name = request.form.get('sub_name')
    sub_status = bool(int(request.form.get('sub_status')))

    new_subcategory = Subcategory(cat_id=cat_id, sub_name=sub_name, sub_status=sub_status)
    db.session.add(new_subcategory)
    db.session.commit()

    flash("Subcategory added successfully!")
    return redirect(url_for('admin_bp.view_subcategories'))



@admin_bp.route("/add_category", methods=["POST"])
def add_category():
    if session.get('login_type') != 'admin':
        return redirect(url_for('main.login'))

    # Debug prints
    print("Form data received:")
    print(request.form)

    cat_name = request.form.get('cat_name')
    cat_status = bool(int(request.form.get('cat_status')))

    # Ensure all required fields are received
    if not cat_name or not request.form.get('cat_status'):
        flash("Missing category name or status", "danger")
        return redirect(url_for('admin_bp.view_categories'))

    new_category = Category(cat_name=cat_name, cat_status=cat_status)
    
    try:
        db.session.add(new_category)
        db.session.commit()
        flash("Category added successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error adding category: {e}", "danger")
        print(f"Error adding category: {e}")

    return redirect(url_for('admin_bp.view_categories'))





@admin_bp.route("/inactivate_category/<int:cat_id>", methods=["POST"])
def inactivate_category(cat_id):
    if session.get('login_type') != 'admin':
        return redirect(url_for('main.login'))

    category = Category.query.get(cat_id)
    if category:
        category.cat_status = False
        db.session.commit()
        flash("Category inactivated successfully!", "success")
    else:
        flash("Category not found.", "danger")

    return redirect(url_for('admin_bp.view_categories'))


@admin_bp.route("/inactivate_subcategory/<int:sub_id>", methods=["POST"])
def inactivate_subcategory(sub_id):
    if session.get('login_type') != 'admin':
        return redirect(url_for('main.login'))

    subcategory = Subcategory.query.get(sub_id)
    if subcategory:
        subcategory.sub_status = False
        db.session.commit()
        flash("Subcategory inactivated successfully!", "success")
    else:
        flash("Subcategory not found.", "danger")

    return redirect(url_for('admin_bp.view_subcategories'))


@admin_bp.route("/subcategory/<int:sub_id>")
def view_subcategory(sub_id):
    if session.get('login_type') != 'admin':
        return redirect(url_for('main.login'))

    subcategory = Subcategory.query.get(sub_id)
    if not subcategory:
        flash("Subcategory not found.", "danger")
        return redirect(url_for('admin_bp.view_subcategories'))

    return render_template("view_subcategory.html", subcategory=subcategory)


@admin_bp.route("/toggle_subcategory_status/<int:sub_id>", methods=["POST"])
def toggle_subcategory_status(sub_id):
    if session.get('login_type') != 'admin':
        return redirect(url_for('main.login'))

    subcategory = Subcategory.query.get(sub_id)
    if subcategory:
        subcategory.sub_status = not subcategory.sub_status
        db.session.commit()
        flash(f"Subcategory status changed to {'Active' if subcategory.sub_status else 'Inactive'}!", "success")
    else:
        flash("Subcategory not found.", "danger")

    return redirect(url_for('admin_bp.view_subcategories'))


@admin_bp.route("/toggle_category_status/<int:cat_id>", methods=["POST"])
def toggle_category_status(cat_id):
    if session.get('login_type') != 'admin':
        return redirect(url_for('main.login'))

    category = Category.query.get(cat_id)
    if category:
        category.cat_status = not category.cat_status
        db.session.commit()
        flash(f"Category status changed to {'Active' if category.cat_status else 'Inactive'}!", "success")
    else:
        flash("Category not found.", "danger")

    return redirect(url_for('admin_bp.view_categories'))


@admin_bp.route("/category/<int:cat_id>")
def view_category(cat_id):
    if session.get('login_type') != 'admin':
        return redirect(url_for('main.login'))

    category = Category.query.get(cat_id)
    if not category:
        flash("Category not found.", "danger")
        return redirect(url_for('admin_bp.view_categories'))

    return render_template("view_category.html", category=category)


@admin_bp.route("/subcategories")
def view_subcategories():
    if session.get('login_type') != 'admin':
        return redirect(url_for('main.login'))

    subcategories = Subcategory.query.all()
    categories = Category.query.all()
    
    # Create a dictionary to map category IDs to category names
    category_dict = {category.cat_id: category.cat_name for category in categories}
    
    # Add category name to each subcategory
    subcategories_with_names = []
    for subcategory in subcategories:
        subcategory_dict = subcategory.__dict__
        subcategory_dict['cat_name'] = category_dict.get(subcategory.cat_id, 'Unknown')
        subcategories_with_names.append(subcategory_dict)

    return render_template("adsub.html", subcategories=subcategories_with_names, categories=categories)



@admin_bp.route("/messages")
def admin_messages():
    if session.get('login_type') != 'admin':
        return redirect(url_for('main.login'))
    
    # Add your messages logic here
    return render_template("admsg.html")  # You'll need to create this template


# In admin_panel.py
@admin_bp.route("/payments")
def view_payments():
    if session.get('login_type') != 'admin':
        return redirect(url_for('main.login'))

    try:
        # Modified query to handle possible NULL values and ensure proper joins
        payments = db.session.query(
            Payment,
            Customer,
            Booking,
            Turf
        ).join(
            Customer, Payment.cust_id == Customer.cust_id
        ).join(
            Booking, Payment.booking_id == Booking.booking_id
        ).join(
            Turf, Booking.turf_id == Turf.turf_id
        ).all()

        # Add debug print
        print(f"Number of payments found: {len(payments)}")

        payments_list = []
        for payment, customer, booking, turf in payments:
            payment_data = {
                'payment_id': payment.payment_id,
                'user': f"{customer.cust_fname} {customer.cust_lname}",
                'turf': turf.turf_name,
                'amount': float(payment.total_amount),
                'date': payment.payment_date.strftime('%Y-%m-%d %H:%M:%S') if payment.payment_date else 'N/A',
                'status': 'Completed' if payment.payment_status else 'Pending',
                'method': payment.payment_method or 'N/A'
            }
            payments_list.append(payment_data)
            # Debug print for each payment
            print(f"Processing payment: {payment_data}")

        return render_template("adpay.html", payments=payments_list)
    
    except Exception as e:
        print(f"Error in view_payments: {e}")
        flash("Error loading payments data", "error")
        return render_template("adpay.html", payments=[])


@admin_bp.route("/revenue")
def admin_revenue():
    if session.get('login_type') != 'admin':
        return redirect(url_for('main.login'))

    # Join the necessary tables to get complete booking information
    bookings = db.session.query(
        Booking,
        Turf,
        Customer,
        TurfOwner
    ).join(
        Turf, Booking.turf_id == Turf.turf_id
    ).join(
        Customer, Booking.cust_id == Customer.cust_id
    ).join(
        TurfOwner, Turf.owner_id == TurfOwner.owner_id
    ).all()

    bookings_list = []
    for booking, turf, customer, owner in bookings:
        # Calculate commission (assuming 10% for example)
        total_amount = float(booking.total_amount)
        admin_commission = total_amount * 0.10
        owner_revenue = total_amount - admin_commission

        booking_data = {
            'booking_id': booking.booking_id,
            'turf_name': turf.turf_name,
            'customer_name': f"{customer.cust_fname} {customer.cust_lname}",
            'date': booking.booking_datetime.strftime('%Y-%m-%d'),
            'time_slot': f"{booking.start_time} - {booking.end_time}",
            'total_amount': total_amount,
            'admin_commission': admin_commission,
            'owner_revenue': owner_revenue
        }
        bookings_list.append(booking_data)

    return render_template("adrevenue.html", bookings=bookings_list)



@admin_bp.route('/reports')
def reports():
    # Fetch monthly summary data
    monthly_data = db.session.query(
        func.date_format(Booking.play_date, '%Y-%m').label('month'),
        func.count(Booking.booking_id).label('total_bookings'),
        func.sum(Booking.total_amount).label('total_amount')
    ).group_by('month').all()

    monthly_bookings = [{'month': data.month, 'total_bookings': data.total_bookings, 'total_amount': data.total_amount} for data in monthly_data]

    # Calculate total bookings, total revenue, and average booking value
    total_bookings = sum(data.total_bookings for data in monthly_data)
    total_revenue = sum(data.total_amount for data in monthly_data)
    avg_booking_value = total_revenue / total_bookings if total_bookings else 0

    # Fetch detailed bookings for a selected month if provided
    selected_month = request.args.get('month')
    detailed_bookings = []
    if selected_month:
        detailed_bookings = Booking.query.filter(func.date_format(Booking.play_date, '%Y-%m') == selected_month).all()

    return render_template(
        'adreport.html',
        monthly_bookings=monthly_bookings,
        detailed_bookings=detailed_bookings,
        selected_month=selected_month,
        total_bookings=total_bookings,
        total_revenue=total_revenue,
        avg_booking_value=avg_booking_value
    )

@admin_bp.route('/turfs/<int:turf_id>')
def adtfull(turf_id):
    turf = Booking.query.filter_by(turf_id=turf_id).first_or_404()
    return render_template('adtfull.html', turf=turf)

if __name__ == '__main__':
    admin_bp.run(debug=True)

@admin_bp.route("/refunds", methods=["GET", "POST"])
def refunds():
    if session.get('login_type') != 'admin':
        flash("Access denied", "error")
        return redirect(url_for("main.login"))

    if request.method == "POST":
        policy_id = request.form.get("policy_id")
        cancellation_time_range = request.form.get("cancellation_time_range")
        refund_percentage = request.form.get("refund_percentage")
        processing_fee = request.form.get("processing_fee") or 0.00
        applies_to = request.form.get("applies_to")
        reason_allowed = request.form.get("reason_allowed")

        if policy_id:  # Edit existing policy
            policy = RefundPolicy.query.get(policy_id)
            if policy:
                policy.cancellation_time_range = cancellation_time_range
                policy.refund_percentage = refund_percentage
                policy.processing_fee = processing_fee
                policy.applies_to = applies_to
                policy.reason_allowed = reason_allowed
                flash("Refund policy updated successfully!", "success")
            else:
                flash("Policy not found!", "error")
        else:  # Add new policy
            new_policy = RefundPolicy(
                cancellation_time_range=cancellation_time_range,
                refund_percentage=refund_percentage,
                processing_fee=processing_fee,
                applies_to=applies_to,
                reason_allowed=reason_allowed
            )
            db.session.add(new_policy)
            flash("New refund policy added!", "success")

        db.session.commit()

    # Fetch all refund policies sorted by policy_id (ascending order)
    refund_policies = RefundPolicy.query.order_by(RefundPolicy.policy_id.asc()).all()

    return render_template("adrefund.html", refund_policies=refund_policies)

@admin_bp.route("/history")
def history():
    if session.get('login_type') != 'admin':
        flash("Access denied", "error")
        return redirect(url_for("main.login"))

    # Perform a JOIN between tbl_refund and tbl_cust to get customer names
    stmt = select(
        Refund.refund_id,
        Refund.payment_id,
        Refund.booking_id,
        Customer.cust_fname,  # Fetch First Name
        Customer.cust_lname,  # Fetch Last Name
        Refund.refund_amount,
        Refund.refund_reason,
        Refund.refund_date,
        Refund.refund_status,
        Refund.policy_id
    ).join(Customer, Refund.cust_id == Customer.cust_id)  # JOIN condition

    refunds = db.session.execute(stmt).fetchall()

    return render_template("adrefhis.html", refunds=refunds)