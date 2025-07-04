# app.py
from flask import Flask, render_template, request, redirect, url_for, Response
from flask_sqlalchemy import SQLAlchemy
import re
import csv
from io import StringIO

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secretkey'

db = SQLAlchemy(app)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    blood_group = db.Column(db.String(5), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    course = db.Column(db.String(100), nullable=False)
    addresses = db.relationship('Address', backref='student', cascade="all, delete-orphan")

class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    block = db.Column(db.String(100))
    street = db.Column(db.String(100), nullable=False)
    area = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    district = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.String(6), nullable=False)

@app.route('/')
def index():
    students = Student.query.all()
    return render_template('index.html', students=students)

@app.route('/add', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        blood_group = request.form['blood_group']
        age = request.form['age']
        course = request.form['course']

        if not re.match(r"^[A-Za-z\s]+$", name):
            return "<h3>❌ Invalid name: Only letters and spaces allowed.</h3><a href='/add'>Go back</a>"
        if not re.match(r"^\d{10}$", phone):
            return "<h3>❌ Invalid phone number: Must be 10 digits.</h3><a href='/add'>Go back</a>"

        blocks = request.form.getlist('block')
        streets = request.form.getlist('street')
        areas = request.form.getlist('area')
        cities = request.form.getlist('city')
        districts = request.form.getlist('district')
        states = request.form.getlist('state')
        pincodes = request.form.getlist('pincode')

        for pin in pincodes:
            if not re.match(r"^\d{6}$", pin):
                return "<h3>❌ Invalid pincode: Must be 6 digits.</h3><a href='/add'>Go back</a>"

        student = Student(name=name, email=email, phone=phone, blood_group=blood_group, age=age, course=course)
        db.session.add(student)
        db.session.flush()

        for i in range(len(streets)):
            db.session.add(Address(
                student_id=student.id,
                block=blocks[i],
                street=streets[i],
                area=areas[i],
                city=cities[i],
                district=districts[i],
                state=states[i],
                pincode=pincodes[i]
            ))

        db.session.commit()
        return redirect(url_for('index'))

    return render_template('form.html', student=None)

@app.route('/edit/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    if request.method == 'POST':
        student.name = request.form['name']
        student.email = request.form['email']
        student.phone = request.form['phone']
        student.blood_group = request.form['blood_group']
        student.age = request.form['age']
        student.course = request.form['course']

        if not re.match(r"^[A-Za-z\s]+$", student.name):
            return "<h3>❌ Invalid name: Only letters and spaces allowed.</h3><a href='/edit/{}'>Go back</a>".format(student_id)
        if not re.match(r"^\d{10}$", student.phone):
            return "<h3>❌ Invalid phone number: Must be 10 digits.</h3><a href='/edit/{}'>Go back</a>".format(student_id)

        blocks = request.form.getlist('block')
        streets = request.form.getlist('street')
        areas = request.form.getlist('area')
        cities = request.form.getlist('city')
        districts = request.form.getlist('district')
        states = request.form.getlist('state')
        pincodes = request.form.getlist('pincode')

        for pin in pincodes:
            if not re.match(r"^\d{6}$", pin):
                return "<h3>❌ Enter valid details.</h3><a href='/edit/{}'>Go back</a>".format(student_id)

        Address.query.filter_by(student_id=student.id).delete()

        for i in range(len(streets)):
            db.session.add(Address(
                student_id=student.id,
                block=blocks[i],
                street=streets[i],
                area=areas[i],
                city=cities[i],
                district=districts[i],
                state=states[i],
                pincode=pincodes[i]
            ))

        db.session.commit()
        return redirect(url_for('index'))

    return render_template('form.html', student=student)

@app.route('/delete/<int:student_id>')
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/download_csv')
def download_csv():
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Student ID', 'Name', 'Email', 'Phone', 'Blood Group', 'Age', 'Course', 'Block', 'Street', 'Area', 'City', 'District', 'State', 'Pincode'])
    students = Student.query.all()
    for student in students:
        for addr in student.addresses:
            writer.writerow([
                student.id, student.name, student.email, student.phone, student.blood_group,
                student.age, student.course,
                addr.block or '', addr.street, addr.area, addr.city,
                addr.district, addr.state, addr.pincode
            ])
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=students.csv'
    return response

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
