from flask import Flask, render_template, url_for, redirect, flash, request, session #sessions - to generate ids for sessions
from flask_session import Session #Session - create security layer for session
import mysql.connector
from otp import genotp
from cmail import sendmail
import re
from datetime import datetime
from datetime import date

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app) #creates security layer
# Secret Key is required for using flash messages
app.secret_key = 'secret word'
#db = mysql.connector.connect(host='localhost',user='root',password='tejeshtanishka',database='payroll')
with mysql.connector.connect(host=host,password=password,db=db,user=user,port=port) as conn:
    cursor=conn.cursor()
    cursor.execute("CREATE TABLE if not exists admin(email varchar(50) DEFAULT NULL,password varchar(50) DEFAULT NULL,passcode varchar(50) DEFAULT NULL) ")
    cursor.execute("CREATE TABLE if not exists  emp_records (emp_id varchar(20) DEFAULT NULL,username varchar(100) DEFAULT NULL,date date DEFAULT NULL,checkin_time time DEFAULT NULL,checkout_time time DEFAULT NULL)")
    cursor.execute("CREATE TABLE if not exists emp_registration (emp_id varchar(20) NOT NULL,firstname varchar(50) DEFAULT NULL,lastname varchar(100) DEFAULT NULL,designation varchar(20) NOT NULL,gender enum('male','female','others') DEFAULT NULL,phone_number bigint DEFAULT NULL,email varchar(50) NOT NULL,password varchar(20) NOT NULL,address textdepartment varchar(30) NOT NULL,salary int unsigned NOT NULL,PRIMARY KEY (emp_id),UNIQUE KEY email (email)) ")
    cursor.execute("CREATE TABLE if not exists  otp_rec (otp_id int NOT NULL AUTO_INCREMENT,email varchar(50) DEFAULT NULL,otp varchar(10) DEFAULT NULL,PRIMARY KEY (otp_id)) ")
    cursor.execute("CREATE TABLE if not exists  work_status ( emp_id varchar(20) NOT NULL,datetime datetime DEFAULT CURRENT_TIMESTAMP,workstatus text,KEY emp_id (emp_id),CONSTRAINT work_status_ibfk_1 FOREIGN KEY (emp_id) REFERENCES emp_registration (emp_id)) ")
mydb=mysql.connector.connect(host=host,user=user,password=password,db=db,port=port)
@app.route('/cd')
def home():
    return render_template('welcome.html')

@app.route('/cd/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        # Get data from the form
        email = request.form.get('email')
        password = request.form.get('password')
        passcode = request.form.get('passcode')

        # Validate form input
        if not email or not password or not passcode:
            flash("All fields (Email, Password, and Passcode) are required.", "error")
            return render_template('admin_login.html')  # Show the form again with the error

        # Check if the email exists in the admin table
        cursor = db.cursor(dictionary=True) 
        cursor.execute("SELECT * FROM admin WHERE email = %s", (email,))
        admin_record = cursor.fetchone()
        cursor.close()

        if admin_record:
            # Email exists, now validate password and passcode
            if admin_record['password'] == password and admin_record['passcode'] == passcode:
                # Valid credentials
                return redirect(url_for('admin_dashboard'))
            else:
                # Invalid password or passcode
                flash("Invalid password or passcode. Please try again.", "error")
        else:
            # Email does not exist
            flash("Invalid email. Please enter a valid email.", "error")

        # If invalid, render the login form again with a flash message
        return render_template('admin_login.html')

    # Render the admin login form for GET requests
    return render_template('admin_login.html')

@app.route('/cd/admin_dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/cd/emp_signup', methods=['GET', 'POST'])
def emp_signup():
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        email = request.form['email']
        # emp_id_prefix = f'EMP_{emp_id}'
        cursor = db.cursor(buffered=True, dictionary=True)
        cursor.execute('SELECT * FROM emp_registration WHERE email = %s', (email,))
        emp_exist = cursor.fetchone()

        if emp_exist:
            flash('You Are Already Registered.Please Login With Valid Credentials.','success')
            # return redirect(url_for('emp_login'))
            return render_template('emp_login.html')
        else:
            # Collect data from the form
            emp_id = request.form['emp_id']
            firstname = request.form['firstname']
            lastname = request.form['lastname']
            designation = request.form['designation']
            gender = request.form['gender']
            phone_number = request.form['phone_number']
            email = request.form['email']
            password = request.form['password']
            address = request.form['address']
            department = request.form['department']
            salary = request.form['salary']
            print(request.form)
            fullname = f'{firstname} {lastname}'
            # emp_id_prefix = f"EMP_{emp_id}"
            # Insert data into emp_reg table
            cursor.execute('INSERT INTO emp_registration(emp_id, firstname, lastname,designation, gender,phone_number, email, password, address, department, salary) VALUES (concat("EMP00",%s), %s,  %s, %s, %s, %s, %s, %s, %s,%s,%s)', (emp_id,firstname,lastname, designation, gender, phone_number,email, password, address, department, salary))

            # Commit the changes
            db.commit()
            cursor.close()
            subject = 'Emp_Reg Verification'
            body = f"Dear {firstname} {lastname},\n\n\tWe are delighted to inform you that your registration has been successfully completed!🎉 \n\tThank you for taking this important step. You are now officially registered in our system, and we're excited to have you as part of the family.\n\nWarm Regards,\nFrom Payroll Management System😍."
            sendmail(to=email,subject=subject,body=body)
            # Flash success message and redirect to the login page
            flash('Registration is successful.','success')
        return render_template('emp_login.html')  # Redirect to the login page after successful signup

    # If it's a GET request, just render the signup form
    return render_template('emp_signup.html')
@app.route('/cd/emp_list')
def emp_list():
    cursor = db.cursor(buffered=True,dictionary=True)
    cursor.execute('select * from emp_registration')
    data = cursor.fetchall()
    cursor.close()
    # print("Fetched Data:", data)  
    return render_template('emp_list.html',emp_data = data)

@app.route('/cd/view_details/<emp_id>')
def view_details(emp_id):
    print(emp_id)
    cursor = db.cursor(buffered=True)
    cursor.execute('select * from emp_records where emp_id = %s',(emp_id,))
    view_data = cursor.fetchall()
    cursor.close()
    print(view_data)
     # Check if no records are found
    if not view_data:
        message = "User has not checked in yet."
        cursor = db.cursor(buffered=True)
        cursor.execute('select firstname, lastname from emp_registration where emp_id = %s',(emp_id,))
        data = cursor.fetchone()
        username = f'{data[0]} {data[1]}'
        print(username)
        cursor.close()
        # view_data = [{'emp_id': emp_id, 'username':username , 'date': 'Not Checkin', 'checkin_time': 'Not Checked In', 'checkout_time': 'Not Checked Out'}]
        view_data = [(emp_id, username, 'Not Check In', 'Not Checked In', 'Not Checked Out')] 
        print(view_data)
        return render_template('view_details.html', message=message,view_data = view_data)
        
    return render_template('view_details.html',view_data = view_data)


@app.route('/cd/emp_login',methods = ['GET','POST'])
def emp_login():
    if 'email' in session:
        return redirect(url_for('emp_dashboard'))
    else:
        if request.method == 'POST':
        # Get data from the form
            email = request.form.get('email')
            password = request.form.get('password')
            # Validate form input
            if not email or not password:
                flash("All fields (Email, Password) are required.", "error")
                return render_template('emp_login.html')  # Show the form again with the error
            # Check if the email exists in the emp_reg table
            cursor = db.cursor(dictionary=True,buffered=True)
            cursor.execute("SELECT * FROM emp_registration WHERE email = %s", (email,))
            emp_record = cursor.fetchone()
            cursor.close()
            print(emp_record)
            # print(emp_record.values())
            if emp_record:
                # Email exists, now validate password
                if emp_record['password'] == password : 
                    # Valid credentials
                    session['email'] = email #creating session
                    return redirect(url_for('emp_dashboard'))
                else:
                    # Invalid password 
                    flash("Invalid password. Please try again.", "error")
            else:
                # Email does not exist
                # flash("Invalid email. Please enter a valid email.", "error")
                flash('Email Is Not Registered. Please Contact Your Admin to Register.','error')
                # If invalid, render the login form again with a flash message
                # return render_template('emp_login.html')
                return redirect(url_for('home'))
        # Render the admin login form for GET requests
    return render_template('emp_login.html')
# return redirect(url_for('emp_dashboard.html'))

@app.route('/cd/emp_dashboard')
def emp_dashboard():
    if session.get('email'):
        email = session.get('email')
        #Fetching The Username In The Database
        cursor = db.cursor(buffered=True)
        cursor.execute('select firstname, lastname from emp_registration where email=%s',(email,))
        username = cursor.fetchone()
        # print(username)
        
        if username:
            fullname = f'{username[0]} {username[1]}'
            cursor.close()
            return render_template('emp_dashboard.html',username = fullname)

        else:
            flash('Username Not Found In Database..! update your Profile')
            # return redirect(url_for('emp_login'))
    else:
        flash('You are not logged in.')
        return redirect(url_for('emp_login'))
    return render_template('emp_dashboard.html',username = fullname)#to del if error 

@app.route('/cd/update_profile',methods=['GET','POST'])
def update_profile():
    if session.get('email'):
        # Check if user is logged in (session email exists)
        email = session.get('email')
        if not email:
            # If no email in session, redirect to login page
            flash("You must be logged in to update your profile.", "error")
            return redirect(url_for('emp_login'))
        # Get updated data from the form0
            
        if request.method == 'POST':
            emp_id = request.form.get('emp_id')
            firstname = request.form.get('firstname')
            lastname = request.form.get('lastname')
            designation = request.form.get('designation')
            # gender = request.form.get('gender')
            # password = request.form.get('password')
            phone_number = request.form['phonenumber']
            email1 = request.form['email']
            address = request.form.get('address')
            department = request.form.get('department')
            salary = request.form.get('salary')
        # Connect to the database
            cursor = db.cursor()
            fullname = f'{firstname} {lastname}'
            print(fullname)
            cursor.execute('update emp_registration set emp_id = %s, firstname = %s, lastname = %s, designation=%s, phone_number = %s, email = %s, address=%s, department=%s, salary=%s where email=%s',(emp_id,firstname,lastname,designation,phone_number,email1,address,department,salary,email))
            db.commit()
            cursor.close() 
        # Redirect to login page with a success message
            flash("Your profile has been updated successfully. Please login with updated credentials.", "success")
            return redirect(url_for('emp_login'))  # Assuming 'login' is the name of your login route

        cursor = db.cursor(buffered=True)
        cursor.execute('select * from emp_registration where email = %s',(email,))
        emp_data = cursor.fetchone()
        cursor.close()
        if emp_data:
            return render_template('update_profile.html', emp_data=emp_data)
        else:
            flash("No profile data found for the current user.", "error")
            return redirect(url_for('emp_login'))


@app.route('/cd/checkin', methods=['GET', 'POST'])
def checkin():
    if session.get('email'):
        email = session.get('email')
        # Get Employee Details
        cursor = db.cursor(buffered=True)
        cursor.execute('SELECT emp_id, firstname, lastname FROM emp_registration WHERE email = %s', (email,))
        result = cursor.fetchone()
        if not result:
            flash('Employee not found', 'error')
            return redirect(url_for('emp_login'))
        emp_id = result[0]
        username = result[1] + result[2]
        cursor.close()

        if request.method == 'POST':
            date = request.form['date']
            current_date = datetime.now().strftime('%Y-%m-%d')

            # Date Validation
            if not date:
                flash('Please Select the Date', 'error')
                return redirect(url_for('checkin'))

            if date != current_date:
                flash(f'Please checkin with valid DATE __: {current_date}', 'error')
                return redirect(url_for('checkin'))

            # Insert Check-in Record
            else:
                cursor = db.cursor(buffered=True)
                try:
                    cursor.execute('INSERT INTO emp_records (emp_id, username, date, checkin_time) VALUES (%s, %s, %s, CURTIME())', (emp_id, username, date))
                    db.commit()
                    flash('Check-in successful!', 'success')
                except Exception as e:
                    print(f'Error during check-in: {e}', 'error')
                    db.rollback()
                finally:
                    cursor.close()
                return redirect(url_for('checkin_details', emp_id=emp_id))
        # Render the Employee Dashboard
        return render_template('emp_dashboard.html', username=username)
    else:
        flash('You Are Not Logged In', 'error')
        return redirect(url_for('emp_login'))

@app.route('/cd/checkin_details/<emp_id>')
def checkin_details(emp_id):
    if 'email' in session:
        email = session.get('email')
        print(emp_id)
        cursor = db.cursor(buffered=True,dictionary=True)
        cursor.execute('select * from emp_records where emp_id = %s and date = CURDATE()',(emp_id,))
        checkin_data = cursor.fetchall()
        cursor.close()
        print("checkin_data:",checkin_data)
        if checkin_data:
            # Render the template with the check-in details
            return render_template('checkin_details.html', checkin_data = checkin_data)                           
        else:
            flash('No check-in records found', 'error')
            return redirect(url_for('emp_dashboard'))  # If no check-in found
    else:
        flash('User not found', 'error')
        return redirect(url_for('emp_login'))  # If user not 


@app.route('/cd/checkout/',methods=['GET','POST'])
def checkout():
    if session.get('email'):
        email = session.get('email')
        cursor = db.cursor(buffered=True)
        cursor.execute('select emp_id,firstname,lastname from emp_registration where email = %s',(email,))
        result = cursor.fetchone()
        emp_id = result[0]
        username = f'{result[1]} {result[2]}'
        cursor.close()
        if request.method == 'POST':
            # checkin = request.form['checkin']
            # checkin = current
            cursor = db.cursor(buffered=True)
            # cursor.execute('insert into emp_records(checkout_time) values(CURTIME())')
            cursor.execute("UPDATE emp_records SET checkout_time = CURTIME() WHERE emp_id = %s and date = CURDATE() and checkout_time is NULL",(emp_id,))

            db.commit()
            cursor.close()
            flash('Check Out Successful.')
            # return render_template('emp_dashboard.html')# Redirect to the dashboard with emp_id
            return redirect(url_for('checkout_details',emp_id = emp_id))
        return render_template('emp_dashboard.html')# Render the dashboard if not POST
    else:
        flash('You Are Not Logged In')
        return redirect(url_for('emp_login'))# Redirect to login if session does not exist


# from datetime import datetime
@app.route('/cd/checkout_details/<emp_id>')
def checkout_details(emp_id):
    if 'email' in session:
        email = session.get('email')
        cursor = db.cursor(buffered=True)
        # cursor.execute('select emp_id from emp_registration where email = %s',(email,))
        # emp_id = cursor.fetchone()[0]

        # Fetch the first check-in record for today
        cursor.execute('SELECT * FROM emp_records WHERE emp_id = %s AND date = CURDATE() ORDER BY checkin_time ASC LIMIT 1',(emp_id,))
        checkin_data = cursor.fetchone()  # Get the first record
        print("checkin_data:", checkin_data)

        if checkin_data:
            # Check-in record exists, proceed to update check-out time
            checkin_time = checkin_data[3]  # Assuming 4th column is `checkin_time`
            # checkout_time = datetime.now().strftime('%H:%M:%S')  # Get current time

            # Update the record with the check-out time
            cursor.execute('UPDATE emp_records SET checkout_time = CURTIME() WHERE emp_id = %s AND date = CURDATE() AND checkin_time = %s',(emp_id, checkin_time))
            db.commit()
            # cursor.close()
            # Fetch the updated record to display
            # cursor = db.cursor(buffered=True)
            cursor.execute('SELECT * FROM emp_records WHERE emp_id = %s AND date = CURDATE() ORDER BY checkin_time ASC LIMIT 1',(emp_id,))
            updated_record = cursor.fetchone()
            cursor.close()

            # Render the template with the updated check-out details
            return render_template('checkout_details.html', checkin_data=updated_record)
        else:
            # No check-in records found
            flash('No check-in records found', 'error')
            cursor.close()
            return redirect(url_for('emp_dashboard'))
    else:
        # User not logged in
        flash('User not found', 'error')
        return redirect(url_for('emp_login'))

@app.route('/cd/work_status',methods=['GET','POST'])
def work_status():
    if 'email' not in session:
        flash("You need to be logged in to submit work status.")
        return redirect(url_for('emp_login'))  # Redirect to login page if not logged in
    else:
        email = session.get('email')
        cursor = db.cursor(buffered=True)
        cursor.execute('select emp_id from emp_registration where email = %s',(email,))
        emp_id = cursor.fetchone()[0]

        today = date.today().strftime('%Y-%m-%d')  # Get today's date in 'YYYY-MM-DD' format
        cursor.execute('SELECT * FROM emp_records WHERE emp_id = %s AND date = %s', (emp_id, today))
        checkin_record = cursor.fetchone()
        
        if not checkin_record:
            flash("You must check in first before submitting your work status.",'error')
            return redirect(url_for('emp_dashboard'))  # Redirect to dashboard if no check-in today
        if request.method == 'POST':
            work_status = request.form['work_status']
            cursor = db.cursor(buffered=True)
            cursor.execute('insert into work_status(emp_id,workstatus) values(%s,%s)',(emp_id,work_status))
            db.commit()
            cursor.close()
            flash(f'Work Status Submitted Successfully.','success')
            return redirect(url_for('emp_dashboard'))

@app.route('/cd/forget_password', methods=['GET', 'POST'])
def forget_password():
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash('Please enter an email.', 'error')
            return render_template('forget_password.html')  
        # Check if the email exists in the emp_reg table
        cursor = db.cursor(buffered=True)
        cursor.execute("SELECT count(email) FROM emp_registration WHERE email = %s", (email,))
        emp_record = cursor.fetchone()[0]
        print('*'*30,emp_record)
        cursor.close()
            
        if emp_record:
            # Generate OTP and send email
            otp = genotp()
            # firstname = emp_record.get('firstname', 'User')  # Use default if firstname is not in the record
            # lastname = emp_record.get('lastname', '')        # Use default empty if lastname is not in the record
            cursor = db.cursor(dictionary=True)
            cursor.execute('insert into otp_rec(email,otp) values(%s,%s)',(email,otp))
            db.commit()
            cursor.close()
            subject = 'Emp_OTP Verification'
            body = f"Dear,\n\n\tYour OTP for validation is: {otp}"
        # Send email
            sendmail(to=email, subject=subject, body=body)
            flash('OTP has been sent to your email. Please check it.', 'success')
            return redirect(url_for('otp_verify'))
        else:
            flash('Email not found. Please try again or contact support.', 'error')
            return render_template('forget_password.html')

    # Render the forget password form (for GET requests)
    return render_template('forget_password.html')

@app.route('/cd/otp_verify',methods=['GET','POST'])
def otp_verify():
    if request.method == 'POST':
        otp1 = request.form['otp1']
        print(f"OTP provided by user: {otp1}")
        cursor = db.cursor(buffered=True)
        cursor.execute("SELECT otp FROM otp_rec order by(otp_id) desc limit 1")
        db_otp = cursor.fetchone()[0]
        print(db_otp)
        if db_otp == otp1:
            return redirect(url_for('new_pwd'))
        else:
            flash("Invalid Otp. Please Try Again.")
            return redirect(url_for('otp_verify'))
    return render_template('otp.html')

#take new route to enter registred mail id 
@app.route('/cd/new_pwd',methods=['GET','POST'])
def new_pwd():
    if request.method == 'POST':
        email = request.form['email']
        print(f"Redirecting to update_password with email: {email}")
        if not email:
            flash("Email is required.", "error")
            return render_template('new_pwd.html')
        return redirect(url_for('update_password', email=email))
    return render_template('new_pwd.html')

@app.route('/cd/update_password/<email>',methods=['GET','POST'])
def update_password(email):
    print(f"Email received in update_password: {email}")

    if request.method == 'POST':
        new_pwd = request.form['new_password']
        cnfrm_pwd = request.form['confirm_password']
        if not new_pwd or not cnfrm_pwd:
            flash("Both fields are required.", "error")
            return render_template('update_password.html', email=email)

        print("New Password = ",new_pwd,"\nConfirm password =",cnfrm_pwd)
        if new_pwd == cnfrm_pwd:
            cursor = db.cursor()
            #cursor.execute('update emp_reg set password = %s where email = %s',(new_pwd,email))
            cursor.execute('update emp_registration set password=%s where email=%s',(new_pwd,email))
            db.commit()
            cursor.close()
            # print(email)
            flash('Your Password Updated Successfully.')
            return redirect(url_for('emp_login'))
        else:
            flash("The New Password and Confirm Password Are Not Matching.Try Again.")
            return redirect(url_for('update_password',email=email))

    return render_template('update_password.html',email=email)

@app.route('/cd/salary_details/<emp_id>')
def salary_details(emp_id):
    cursor = db.cursor(buffered=True)
    # Step 1: Fetch the employee's monthly salary from emp_registration table
    cursor.execute('SELECT firstname, lastname, salary FROM emp_registration WHERE emp_id = %s', (emp_id,))
    emp_data = cursor.fetchone()
    if not emp_data:
        return "Employee not found", 404  # Handle case where employee is not found
    firstname, lastname, salary = emp_data
    username = f"{firstname} {lastname}"
    # Step 2: Count distinct working days from emp_records for the employee
    cursor.execute('SELECT COUNT(DISTINCT date) FROM emp_records WHERE emp_id = %s', (emp_id,))
    num_working_days = cursor.fetchone()[0]  # Get the count of distinct dates
    cursor.close()
    company_working_days = 26
    # Step 3: Calculate daily salary
    # Assuming 30 days in a month for simplicity (adjust if needed based on actual working days)
    daily_salary = salary / 26

    # Step 4: Calculate the total salary for the working days
    total_salary = daily_salary * num_working_days

    # Step 5: Render the template with the data
    return render_template('salary_details.html',emp_data=[{'emp_id': emp_id, 'username': username}],company_working_days=company_working_days, num_working_days=num_working_days, total_salary=round(total_salary, 2))
  

@app.route('/cd/logout')
def logout():
    # Clear the user session
    session.pop('email', None)  # Remove the 'email' from the session
    flash('Logged Out Successfully.','success')
    return redirect(url_for('home'))  # Redirect to the login page

@app.route('/cd/search',methods=['GET','POST'])
def search():
    query = ""  # Ensure query is always defined
    results = []  # Default to an empty list of results
    if request.method == 'POST':
        query = request.form.get("search", "").strip() 
        cursor = db.cursor(buffered = True,dictionary=True)
        # Check if the query is not empty
        if query:  # Check if the query is not empty (ignoring whitespace)
        # SQL query to search the database
            search_query = "SELECT emp_id, firstname,lastname, designation, email, department FROM emp_registration WHERE emp_id LIKE %s OR firstname LIKE %s OR lastname LIKE %s OR designation LIKE %s OR email LIKE %s OR department LIKE %s"
            cursor.execute(search_query, (f"%{query}%", f"%{query}%",f"%{query}%",f"%{query}%",f"%{query}%", f"%{query}%"))
            results = cursor.fetchall()  # Fetch all matching rows
    # else:
    #     results = []  # Empty list for no results or no query

    # Pass the query and results to the template
    return render_template("search_results.html", query=query, results=results)

app.run(debug=True)
