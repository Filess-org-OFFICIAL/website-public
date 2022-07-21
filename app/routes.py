from httplib2 import Response
from app import app, db, stripe_keys
from app.models import User, Files, Plan
from flask import render_template, request, flash, redirect, url_for, jsonify, Response
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.utils import secure_filename
from werkzeug.urls import url_parse
from app.send_email import *

import boto3
import os
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import time
from PIL import Image
import re
import random
import string
import stripe

image_types = ['jpg', 'png', 'gif', 'webp', 'svg', 'jpeg']
video_types = ['mp4', 'mov', 'wmv', 'avi']
plan_size = {1: 100, 2: 500, 3: 5000, 4: 50000}
plan_tag = {1: 1, 2: 1, 3: 1, 4: 1}
plan_subdomain = {1: 0, 2: 0, 3: 1, 4: 1}
tier_translate = {199: 2, 699: 3, 1499: 4}  # first 3 digits for ease
beta = False


def datetime_filter(value):  # current timezone datetime
    now_timestamp = time.time()
    offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp)
    return value + offset


app.jinja_env.filters['datetime_filter'] = datetime_filter


def file_exists(filename, user_id):  # check if file exists for given user
    return len(Files.query.filter_by(fileName=filename, userId=user_id).all()) > 0


def bytes_convert(bytes):  # convert bytes to readable string
    if bytes < 1000:
        return str(bytes) + ' bytes'
    elif bytes < 1000000:
        return str(bytes // 1000) + ' KB'
    elif bytes < 1000000000:
        return str(bytes // 1000000) + ' MB'
    else:
        return str(round(bytes / 1000000000, 2)) + ' GB'


@app.before_request
def before_request():
    if not request.is_secure and 'stripe' not in request.url:
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)


@app.route('/', methods=('GET', 'POST'))
def landing_page():
    if request.method == 'POST':
        print('landing')
        file = request.files['file']  # get uploaded file
        filename = secure_filename(file.filename).replace(' ', '_')
        print(file)

        random_path = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(12))
        random_path += 'ep3E'
        url = f'https://filess.org/{random_path}/{filename}'
        filepath = 'app/static/uploaded_user_assets/' + random_path + '/'
        too_large = False

        if not os.path.exists(filepath):
            os.makedirs(filepath)
        file.save(filepath + filename)

        byte_size = int(os.path.getsize(filepath + filename))
        if byte_size > 25000000:    # 25mb size cap for non-account users
            too_large = True
            url = None

        # extra arguments for embedding
        file_type = filename.split('.')[-1].lower()
        extra_args = None
        if file_type in image_types:  # identify asset type
            img = Image.open(filepath + filename)
            img.close()
            extra_args = {'ContentType': "image/" + file_type}
        elif file_type in video_types:
            extra_args = {'ContentType': "video/" + file_type}

        # Upload to user-specific directory in S3
        s3 = boto3.client("s3")
        s3.upload_file(Filename=filepath + filename, Bucket="filessstorage",
                       Key=f'landing/{random_path}/{filename}', ExtraArgs=extra_args)

        # Remove from local
        os.remove(filepath + filename)

        return render_template('landing.html.j2', url=url, size=too_large)
    # return redirect(url_for('login'))
    return render_template('landing.html.j2')


# TODO: login with Google
@app.route('/login', methods=('GET', 'POST'))
def login():
    if current_user.is_authenticated:  # redirect to dashboard if already logged in
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Find a user with the given email
        user = User.query.filter_by(email=email).first()

        # Check if the credentials are invalid
        if user is None or not user.check_password(password):
            flash('Invalid e-mail or password', 'danger')
        else:
            print(user.check_password(password))
            login_user(user, remember=True)

            # If a user accesses a page protected by @login_required a parameter, 'next' will be passed
            # containing the redirect URL
            next_page = request.args.get('next')

            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('dashboard')
            return redirect(next_page)
    return render_template('login.html.j2')


@app.route('/signup', methods=('GET', 'POST'))
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form['email']
        fname = request.form['fname']
        lname = request.form['lname']
        password = request.form['password']
        password2 = request.form['password2']
        print(email, fname, lname, password, password2)

        # email regex pattern
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

        if not email or not fname or not lname or not password or not password2:
            flash('Please enter the required fields', 'danger')
        if not re.fullmatch(regex, email):
            flash('Please use a valid email', 'danger')
        if any(not c.isalnum() for c in fname) or any(not c.isalnum() for c in lname):
            flash('Please enter your correct names in their respective fields', 'danger')
        elif password != password2:
            flash('Passwords do not match', 'danger')
        elif len(User.query.filter_by(email=email).all()) > 0:
            flash('Email already in use, if you own this account please sign in', 'danger')
        elif len(password) < 8 or not re.search(r'\d', password) or not any(c.isalnum() for c in password):
            flash('Please enter a stronger password. Passwords must be at least 8 characters with a number and special character', 'danger')
        # in Beta no new accounts can be created
        elif beta:
            flash('Account creation has been turned off during the beta state')
        else:
            code = random.randint(100000, 1000000)  # generate random 6 digit code
            encoded = code  # encoding removed from public repo for security reasons
            send(email, 'Your Filess verification code', 'Your code: ' + str(code))  # send code in email to user
            data = ' '.join([email, fname, lname, password, encoded])
            return render_template('verify.html.j2', data=data)

    return render_template('signup.html.j2')


@app.route('/api/verify', methods=['POST'])
def verify_code():
    data = request.data.split()
    # email, fname, lname, password, code, input_code = str(data[0])[2:-1], str(data[1])[2:-1], str(data[2])[2:-1], str(data[3])[2:-1], data[4], data[5]
    email, fname, lname, password, code, input_code = data[0].decode('utf-8'), data[1].decode('utf-8'), data[2].decode('utf-8'), data[3].decode('utf-8'), data[4], data[5]
    # verify code
    if int(code) != int(input_code):  # check code
        return jsonify({'error': 'Codes do not match'})  # TODO: get flash to work

    print('match!', email)
    # add new user to db
    db.session.add(User(email=email, firstName=fname, lastName=lname))
    db.session.commit()

    user = User.query.filter_by(email=email).first()
    user.set_password(password)
    db.session.commit()

    login_user(User.query.filter_by(email=email).first(), remember=True)

    # Tier 1 plan automatically
    db.session.add(Plan(planId=1, userId=current_user.userId, storageSize=plan_size[1], tags=plan_tag[1], subdomains=plan_subdomain[1], dateExpired=(date.today() + relativedelta(months=+1))))
    db.session.commit()
    print(Plan.query.filter_by(userId=current_user.userId).first().storageSize)

    return redirect(url_for('dashboard'))


@app.route('/dashboard')
@login_required
def dashboard():
    # check if plan expired
    plan = Plan.query.filter_by(userId=current_user.userId).first()
    if plan.dateExpired < datetime.utcnow():
        plan.planId, plan.storageSize, plan.tags, plan.subdomains = 1, plan_size[1], plan_tag[1], plan_subdomain[1]
        db.session.commit()
    # Get display variables
    assets = Files.query.filter_by(userId=current_user.userId).all()
    user = User.query.filter_by(userId=current_user.userId).first()

    return render_template('dashboard.html.j2', assets=assets, user=user, plan=plan, bytes_convert=bytes_convert)


@app.route('/logout')
def logout():  # logout
    logout_user()
    return redirect(url_for('login'))


# TODO: send reset password to email
# NOT SUPPORTED DURING BETA PHASE
@app.route('/reset', methods=["GET", "POST"])
def reset():  # forgot email or password, reset
    if request.method == "POST":
        email = request.data.decode("utf-8")
        if len(User.query.filter_by(email=email).all()) == 0:
            flash('Invalid email address', 'danger')
        else:
            print(email)
            user = User.query.filter_by(email=email).first()
            temp_pass = str(random.randint(1000000, 9999999))
            user.set_password(temp_pass)
            db.session.commit()
            send(email, 'Your reset password', 'Your reset password is: ' + temp_pass + '. You will be able to change this after login')
            flash('A reset password has been sent to your email')
            return redirect(url_for('login'))  # TODO: fix reload issue

    else:
        return render_template('reset.html.j2')


@app.route('/<user_id>/<file_name>')  # url contains user id and filename
@app.route('/<user_id>/<tag>/<file_name>')  # if user has custom tag
def show_asset(user_id, file_name, tag=None):
    aws_pointer = 'https://filessstorage.s3.us-east-1.amazonaws.com/' + user_id + '/' + file_name  # public in S3
    try:
        asset = Files.query.filter_by(userId=int(user_id), fileName=file_name).first()
    except ValueError:
        asset = None

    if not asset:
        if user_id[-4:] == 'ep3E':
            aws_pointer = 'https://filessstorage.s3.us-east-1.amazonaws.com/landing/' + user_id + '/' + file_name
            return redirect(aws_pointer)
        return render_template('404.html'), 404

    file_type = asset.fileName.split('.')[-1].lower()
    if asset.fileType == 'image':
        return redirect(aws_pointer)
    elif asset.fileType == 'video':
        resp = Response(status=302, content_type='video/' + file_type)
        resp.headers.add('Accept-Ranges', 'bytes')
        resp.headers.add('Content-Length', asset.fileBytes)
        resp.headers.add('Content-Range', 'bytes {0}-{1}/{2}'.format(0, asset.fileBytes - 1, asset.fileBytes))
        resp.headers.add('Location', aws_pointer)
        return resp
    else:
        return redirect(aws_pointer)


@app.route('/updateAccountInformation', methods=('GET', 'POST'))
@login_required
def update_account():
    if request.method == 'POST':
        data = request.data.decode("utf-8").split(',')
        email = data[0]
        fname = data[1]
        lname = data[2]
        pass1 = data[3]
        pass2 = data[4]
        passIn = data[5]
        print(email, fname, lname, pass1, pass2, passIn)

        user = User.query.filter_by(userId=current_user.userId).first()
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

        # check invalid fields
        if not user.check_password(passIn):
            return jsonify({'error': 'Incorrect password'})
        elif pass1 != pass2:
            return jsonify({'error': 'New passwords do not match'})
        elif not re.fullmatch(regex, email) and user.email != email:
            return jsonify({'error': 'Please enter a valid email'})
        elif len(User.query.filter_by(email=email).all()) > 0 and user.email != email:
            return jsonify({'error': 'This email is already in use'})
        elif any(not c.isalnum() for c in fname) or any(not c.isalnum() for c in lname):
            return jsonify({'error': 'Please enter your real first and last name'})
        elif pass1 and (len(pass1) < 8 or not re.search(r'\d', pass1) or any(not c.isalnum() for c in pass1)):
            return jsonify({'error': 'Please enter a stronger password. Passwords must be at least 8 characters long, contain a number, and only alphanumeric characters'})

        if email: user.email = email
        if fname: user.firstName = fname
        if lname: user.lastName = lname
        if pass1: user.set_password(pass1)
        db.session.commit()

    return redirect(url_for('dashboard'))


@app.route('/deleteAccount')
@login_required
def delete_account():
    if beta:
        flash('You cannot delete Beta accounts')
        return redirect(url_for('dashboard'))

    user = User.query.filter_by(userId=current_user.userId)
    assets = Files.query.filter_by(userId=current_user.userId)
    plan = Plan.query.filter_by(userId=current_user.userId)
    user.delete()
    assets.delete()
    plan.delete()
    db.session.commit()

    s3 = boto3.resource('s3')
    bucket = s3.Bucket('filessstorage')
    bucket.objects.filter(Prefix=str(current_user.userId) + '/').delete()

    return redirect(url_for('login'))


@app.route('/Admin')
@login_required
def admin_page():  # info on all users, users' files, total storage and files, while preserving integrity
    if current_user.userId == 8:  # if user is logged in as Admin
        files = []
        total_storage = 0
        total_files = 0

        users = [user for user in User.query.all()]
        for i, user in enumerate(users):
            files.append([])
            for file in Files.query.filter_by(userId=user.userId).all():
                files[i].append(file)
                total_storage += file.fileBytes
                total_files += 1

        return render_template('admin_page.html.j2', data=zip(reversed(users), reversed(files)),
                               files=total_files, storage=total_storage)
    else:
        return render_template('404.html'), 404


# API ROUTES
@app.route('/api/upload', methods=['POST'])
@login_required
def asset_upload():
    try:
        if request.method == "POST":
            file = request.files['file']  # get uploaded file
            filename = secure_filename(file.filename).replace(' ', '_')
            print(filename)

            if len(re.findall(r'\.', filename)) > 1 or '/' in filename:
                return jsonify({'error': 'Invalid filename. Filenames cannot contain "." or "/"'})
            if file_exists(file.filename, current_user.userId):
                return jsonify({'error': 'File with same name already exists.'})

            # Download uploaded file
            filepath = 'app/static/uploaded_user_assets/' + str(current_user.userId) + '/'
            if not os.path.exists(filepath):
                os.makedirs(filepath)
            file.save(filepath + filename)

            byte_size = int(os.path.getsize(filepath + filename))  # get size in bytes, convert to readable form
            user = User.query.filter_by(userId=current_user.userId).first()
            plan = Plan.query.filter_by(userId=current_user.userId).first()

            if int(user.totalSize) + byte_size > plan.storageSize * 1000000:
                return jsonify({'error': 'You have exceeded the maximum storage for your tier. Upgrade your tier or delete some files to continue.'})

            file_type = filename.split('.')[-1].lower()
            width, height = 0, 0
            extra_args = None
            if file_type in image_types:  # identify asset type
                img = Image.open(filepath + filename)
                width, height = img.size  # store image dimensions for display
                width, height = width // 2.5, height // 2.5
                img.close()
                extra_args = {'ContentType': "image/" + file_type}
                file_type = "image"
            elif file_type in video_types:
                extra_args = {'ContentType': "video/" + file_type}
                file_type = "video"
            else:
                file_type = "unidentified"

            # Upload to user-specific directory in S3
            s3 = boto3.client("s3")
            s3.upload_file(Filename=filepath + filename, Bucket="filessstorage", Key=str(current_user.userId) + '/' + filename, ExtraArgs=extra_args)

            # Remove from local
            os.remove(filepath + filename)

            # Create new entry with uploaded file details to Files db
            db.session.add(Files(userId=current_user.userId, fileName=filename, fileBytes=byte_size, fileType=file_type,
                                fileWidth=width, fileHeight=height))
            db.session.commit()  # commit changes

            # Update total byte size storage
            if not user.totalSize:
                user.totalSize = byte_size
            else:
                user.totalSize += byte_size

            print("Current user's total storage in bytes:", user.totalSize)
            db.session.commit()

        return redirect(url_for('dashboard'))

    except Exception as e:
        print(str(e))
        return jsonify({'error' : str(e)})


@app.route('/api/delete/<file_name>', methods=["DELETE"])
@login_required
def delete_asset(file_name):
    print(file_name)
    record = Files.query.filter_by(userId=current_user.userId, fileName=file_name)
    file = record.first()
    bytes_ = file.fileBytes

    record.delete()
    db.session.commit()

    s3 = boto3.client('s3')
    s3.delete_object(Bucket='filessstorage', Key=str(current_user.userId) + '/' + file_name)  # delete from s3

    # Update total byte size storage
    user = User.query.filter_by(userId=current_user.userId).first()
    user.totalSize -= bytes_
    print("Current user's total storage in bytes:", user.totalSize)
    db.session.commit()

    return redirect(url_for('dashboard'))


@app.route('/api/update/<file_name>', methods=["POST"])
@login_required
def update_file_name(file_name):
    try:
        if request.method == 'POST':
            filename = request.data.decode("utf-8")
            print(filename)
            filename = filename.replace(' ', '_')

            if file_name == filename:
                return jsonify({'error': 'Please exit the editor to cancel editing'})
            elif len(filename.split('.')[0]) < 1:
                return jsonify({'error': 'Please enter a filename'})
            elif any(not c.isalnum() for c in filename.split('.')[0].replace('_', '')):
                return jsonify({'error': 'Filenames may only contain alpha numeric characters or _'})
            elif file_exists(filename, current_user.userId):
                return jsonify({'error': 'File with same name already exists.'})
            elif filename in ['', ' ', None, '/']:
                return jsonify({'error': 'Invalid filename'})

            files = Files.query.filter_by(userId=current_user.userId, fileName=file_name).first()
            files.fileName = filename  # rename file in db
            db.session.commit()

            s3 = boto3.resource('s3')  # rename in s3
            s3.Object('filessstorage', str(current_user.userId) + '/' + filename).copy_from(CopySource={'Bucket': 'filessstorage', 'Key': str(current_user.userId) + '/' + file_name})
            s3.Object('filessstorage', str(current_user.userId) + '/' + file_name).delete()

        return redirect(url_for('dashboard'))

    except Exception as e:
        print(str(e))
        return jsonify({'error': str(e)})



@app.route('/api/updateSubdomain', methods=["POST"])
@login_required
def update_custom_subdomain():
    try:
        if request.method == 'POST':
            subdomain = request.data.decode("utf-8")
            subdomain = subdomain.replace(' ', '_').lower()
            plan = Plan.query.filter_by(userId=current_user.userId).first()

            if any(not c.isalnum() for c in subdomain.replace('_', '')):
                return jsonify({'error': 'Custom subdomains may only contain alpha numeric characters or _'})
            elif len(User.query.filter_by(subdomain=subdomain).all()) >= 1 and subdomain != '':
                return jsonify({'error': 'Custom subdomain already taken'})
            elif plan.subdomains == 0 and subdomain != '':
                stripe.api_key = stripe_keys["secret_key"]
                domain_url = "https://filess.org/dashboard/"
                checkout_session = stripe.checkout.Session.create(
                    client_reference_id=current_user.userId if current_user.is_authenticated else None,
                    metadata={"subdomain": subdomain},
                    success_url=domain_url + "success?session_id={CHECKOUT_SESSION_ID}",
                    cancel_url=domain_url + "cancelled",
                    payment_method_types=["card"],
                    mode="payment",
                    line_items=[
                        {
                            "name": "Subdomain: " + subdomain,
                            "quantity": 1,
                            "currency": "usd",
                            "amount": "069",
                        }
                    ]
                )

                # stripe_checkout_url = 'https://checkout.stripe.com/pay/' + checkout_session["id"]
                # print(stripe_checkout_url)
                # return redirect("https://monkeytype.com")
                return jsonify({"sessionId": checkout_session["id"]})

            user = User.query.filter_by(userId=current_user.userId).first()
            user.subdomain = subdomain
            db.session.commit()
        return redirect(url_for('dashboard'))

    except Exception as e:
        print(str(e))
        return jsonify({'error': str(e)})


@app.route('/api/updateCustomTag/<filename>', methods=['POST'])
@login_required
def update_custom_tag(filename):
    if request.method == 'POST':
        tag = request.data.decode("utf-8")
        tag = tag.replace(' ', '_')
        print(tag)
        if any(not c.isalnum() for c in tag.replace('_', '')):
            return jsonify({'error': 'Custom tags may only contain alpha numeric characters or _'})

        file = Files.query.filter_by(userId=current_user.userId, fileName=filename).first()
        file.tag = tag
        db.session.commit()
    return redirect(url_for('dashboard'))


@app.route("/api/config")
@login_required
def get_publishable_key():
    stripe_config = {"publicKey": stripe_keys["publishable_key"]}
    return jsonify(stripe_config)


@app.route("/create-checkout-session/<tier>")
@login_required
def create_checkout_session(tier):
    print(tier)
    domain_url = "https://filess.org/dashboard/"
    stripe.api_key = stripe_keys["secret_key"]

    try:
        # Create new Checkout Session for the order
        # Other optional params include:
        # [billing_address_collection] - to display billing address details on the page
        # [customer] - if you have an existing Stripe Customer ID
        # [payment_intent_data] - capture the payment later
        # [customer_email] - prefill the email input in the form
        # For full details see https://stripe.com/docs/api/checkout/sessions/create

        # ?session_id={CHECKOUT_SESSION_ID} means the redirect will have the session ID set as a query param
        if tier == "tier2":
            checkout_session = stripe.checkout.Session.create(
                client_reference_id=current_user.userId if current_user.is_authenticated else None,
                success_url=domain_url + "success?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=domain_url + "cancelled",
                payment_method_types=["card"],
                mode="payment",
                line_items=[
                    {
                        "name": "Tier 2",
                        "quantity": 1,
                        "currency": "usd",
                        "amount": "099",
                    }
                ]
            )
        elif tier == "tier3":
            checkout_session = stripe.checkout.Session.create(
                client_reference_id=current_user.userId if current_user.is_authenticated else None,
                success_url=domain_url + "success?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=domain_url + "cancelled",
                payment_method_types=["card"],
                mode="payment",
                line_items=[
                    {
                        "name": "Tier 3",
                        "quantity": 1,
                        "currency": "usd",
                        "amount": "399",
                    }
                ]
            )
        elif tier == "tier4":
            checkout_session = stripe.checkout.Session.create(
                client_reference_id=current_user.userId if current_user.is_authenticated else None,
                success_url=domain_url + "success?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=domain_url + "cancelled",
                payment_method_types=["card"],
                mode="payment",
                line_items=[
                    {
                        "name": "Tier 4",
                        "quantity": 1,
                        "currency": "usd",
                        "amount": "699",
                    }
                ]
            )
        return jsonify({"sessionId": checkout_session["id"]})
    except Exception as e:
        return jsonify(error=str(e)), 403


@app.route("/dashboard/success")
@login_required
def success():
    return render_template("success.html.j2")


@app.route("/dashboard/cancelled")
@login_required
def cancelled():
    return render_template("cancelled.html.j2")


# connect to Stripe to verify purchase
@app.route("/api/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe_keys["endpoint_secret"]
        )

    except ValueError as e:
        # Invalid payload
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return "Invalid signature", 400

    # Handle the checkout.session.completed event
    if event["type"] == "checkout.session.completed":
        print("Payment was successful.")
        data = request.data.decode("utf-8")
        print(data)
        cost = int(re.findall(r'"amount_subtotal": .+,', data)[0].split()[-1][:-1])
        user_id = int(re.findall(r'"client_reference_id": ".+"', data)[0].split()[-1][1:-1])
        print(cost, user_id)

        if cost == 99:
            user = User.query.filter_by(userId=user_id).first()
            user.subdomain = re.findall(r'"subdomain": ".+"', data)[0].split()[-1][1:-1]
            db.session.commit()
        else:
            paid_tier = tier_translate[cost]
            plan = Plan.query.filter_by(userId=user_id).first()

            plan.planId, plan.storageSize, plan.tags, plan.subdomains = paid_tier, plan_size[paid_tier], plan_tag[paid_tier], plan_subdomain[paid_tier]
            db.session.commit()

    return "Success", 200


@app.errorhandler(404)
def page_not_found(e):  # 404 page error handler
    return render_template('404.html'), 404


@app.errorhandler(403)
def page_not_found(e):  # 404 page error handler
    return render_template('403.html'), 403


@app.errorhandler(400)
def page_not_found(e):  # 404 page error handler
    return render_template('400.html'), 400


@app.errorhandler(500)
def page_not_found(e):  # 404 page error handler
    return render_template('500.html'), 500


# Any and all testing, feel free to use
@app.route('/DELETEALLROWSINFILESTABLE')  # deletes all user's assets
def test():
    Files.query.filter_by(userId=current_user.userId).delete()
    db.session.commit()
    user = User.query.filter_by(userId=current_user.userId).first()
    user.totalSize = 0
    db.session.commit()
    return redirect(url_for('dashboard'))
