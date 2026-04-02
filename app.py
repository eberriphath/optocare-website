from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# -------------------------
# HOME PAGE
# -------------------------
@app.route('/')
def home():
    return render_template('index.html')


# -------------------------
# SIGNUP PAGE
# -------------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Collect form data
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        store_name = request.form.get('store_name')
        location = request.form.get('location')
        phone = request.form.get('phone')
        services = request.form.get('services')
        document = request.files.get('document')

        # Temporary: print data to console (for testing)
        print("New Partner Application:")
        print(f"Name: {full_name}, Email: {email}, Store: {store_name}, Location: {location}, Phone: {phone}")
        print(f"Services: {services}, Document Filename: {document.filename if document else 'No file'}")

        # TODO: save to database or file system
        # For example, you could save document with:
        # document.save(f"uploads/{document.filename}")

        # Redirect to a thank-you page or home
        return redirect(url_for('home'))

    # GET request → show the signup form
    return render_template('signup.html')


# -------------------------
# LOGIN PAGE
# -------------------------
@app.route('/login')
def login():
    return render_template('login.html')


# -------------------------
# ADMIN DASHBOARD
# -------------------------
@app.route('/admin')
def admin():
    return render_template('admin-dashboard.html')


# -------------------------
# PARTNER DASHBOARD
# -------------------------
@app.route('/partner')
def partner():
    return render_template('partner-dashboard.html')


# -------------------------
# RUN SERVER
# -------------------------
if __name__ == '__main__':
    app.run(debug=True)