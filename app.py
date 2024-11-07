### Import Package
## For main page
import os
from flask import Flask, render_template, request, url_for, redirect, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy.sql import func
import mysql.connector as connection
import matplotlib.pyplot as plt
import io
import base64
import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objects as go
import json
import seaborn as sns
from visualize import *

## For login function
from flask_login import LoginManager
from flask_login import UserMixin
from flask import Blueprint
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user
from flask_login import login_required, current_user

from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import utils
import time 
from flask_cors import CORS
from utils import * 
from sqlalchemy import create_engine
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
from pyngrok import ngrok

from functools import wraps
import datetime


app = Flask(__name__, static_folder='static')
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] =\
        ("mysql+mysqlconnector://root:2787853@127.0.0.1:3306/db2")
app.config['SECRET_KEY'] = 'secret-key-goes-here'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.app_context().push()

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

#=========import chatbot==============
# chatbot = pipeline("table-question-answering", model='google/tapas-large-finetuned-wtq')
model_path = "phamhai/Llama-3.2-1B-Instruct-Frog"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path)
chat_history = []


#=====================================

class UserRole:
    ADMIN ='admin'
    STANDARD = 'standard'

class User(UserMixin,db.Model): #for user information
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(10000))
    name = db.Column(db.String(1000))
    role = db.Column(db.String(20),default=UserRole.STANDARD)

    def is_admin(self):
        return self.role == UserRole.ADMIN
    
#Decorator for requiring admin role 
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash('You need to be an admin to access this page')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function 

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('You need to login to access this page')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function 


class jidouka(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    innovation_name = db.Column(db.String(100), nullable=False)
    task_type = db.Column(db.String(20), nullable=False)
    tool = db.Column(db.String(50), nullable=False)
    describe_innovation = db.Column(db.Text)
    software = db.Column(db.String(50))
    product = db.Column(db.String(50))
    pic = db.Column(db.String(30))
    dc = db.Column(db.String(10))
    num_tasks = db.Column(db.Integer)
    saved_hours = db.Column(db.Integer)
    created_at = db.Column(db.DateTime(timezone=True),
                           server_default=func.now())
    information = db.Column(db.Text)

class definition(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    tool = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

class QuestionAndAnswer(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    requester = db.Column(db.String(50), nullable=False)
    task_type = db.Column(db.String(20), nullable=False)
    task = db.Column(db.Text)
    problem = db.Column(db.Text)
    frequency = db.Column(db.String(20))
    num_hours = db.Column(db.Integer)
    deadline_to_feedback = db.Column(db.String(20))

    content = db.Column(db.Text)
    time = db.Column(db.DateTime(timezone=True), server_default=func.now())
    result = db.Column(db.String(50))
    feedback = db.Column(db.Text)


#data for chatbot
mydb = connection.connect(host="127.0.0.1", database = 'db2',user="root", passwd="2787853")
cursor = mydb.cursor()
query = "Select * from jidouka;"
df = pd.read_sql(query,mydb)
df.rename(columns={'pic':'contributor'}, inplace=True)

chatbot_df = utils.format_table_for_chatbot(df)
# prompt_template=""" Bạn là một trợ lí ảo thông minh
#                     ###Nhiệm vụ: trả lời câu hỏi của người dùng dựa vào bảng cho dưới đây. Nếu câu hỏi không liên quan đến bảng, hãy bắt đầu bằng: "Tôi không thể tìm được dữ kiện trong bảng bạn cần tìm".
#                     ###Bảng:
#                     {table}
#                 """

prompt_template=""" Bạn là một trợ lí Tiếng Việt nhiệt tình và trung thực. Dựa vào thông tin có trong bảng dưới, hãy luôn trả lời một cách hữu ích nhất có thể, đồng thời giữ an toàn.
Nếu một câu hỏi không có ý nghĩa hoặc không hợp lý về mặt thông tin, hãy giải thích tại sao thay vì trả lời một điều gì đó không chính xác, vui lòng không chia sẻ thông tin sai lệch.
                    Nhiệm vụ: trả lời câu hỏi của người dùng dựa vào bảng cho dưới đây. Nếu câu hỏi không liên quan đến bảng, hãy bắt đầu bằng: "Tôi không thể tìm được dữ kiện trong bảng bạn cần tìm".
                    Bảng:
                    {table}
                """
system_prompt = prompt_template.format(table=chatbot_df)
@login_manager.user_loader
def load_user(user_id):
    # since the user_id is just the primary key of our user table, use it in the query for the user
    return User.query.get(int(user_id))

main = Blueprint('main', __name__)

@main.route('/index')
@login_required
def index():
    jidoukaa = jidouka.query.all()

    return render_template('index.html', jidouka=jidoukaa)

# @main.route('/chat', methods=['POST'])
# @login_required
# def chat():
#     df_copy = df.copy()
#     df_copy = df_copy.astype(str)
#     data = request.json
#     message = data.get('message', '')
    
#     # Add your chatbot logic here
#     response = chatbot(table=df_copy, query = message)['answer'] # Replace with actual chatbot response
#     response = utils.format_result_tapas(response)
#     response = str(response)

#     return jsonify({'response': response})

@main.route('/chat_page')
def chat_page():
    chat_history = []
    return render_template('chat_page.html', history=chat_history)

@main.route('/chat', methods=['POST'])
def chat():
    user_message = request.json['message']
    
    # Append user message to chat history
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    chat_history.append({'timestamp': timestamp, 'user': user_message})

    # Generate a response
    # input_text = user_message  # Modify this as needed for your model's input
    # inputs = tokenizer(input_text, return_tensors='pt')
    # outputs = model.generate(**inputs, max_new_tokens=128)
    # bot_response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    messages = [
        {'role':'system',
         'content': system_prompt}
         ,{ 'role': 'user',
             'content': user_message
         }
    ]
    tokenized_chat = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_tensors='pt')
    outputs = model.generate(tokenized_chat, max_new_tokens=256)
    bot_response = tokenizer.decode(outputs[0])
    bot_response = bot_response.split('<|start_header_id|>assistant<|end_header_id|>')
    bot_response = bot_response[1].strip()[:-10]
    # Append bot response to chat history
    chat_history.append({'timestamp': timestamp, 'bot': bot_response})
    
    return jsonify({'timestamp': timestamp, 'response': bot_response})

@main.route('/clear', methods=['POST'])
def clear():
    global chat_history
    chat_history = []  # Clear chat history
    return jsonify(success=True)


@main.route('/<int:jidou_id>/')
@login_required
def Jidouka(jidou_id):
    jidoukaa = jidouka.query.get_or_404(jidou_id)
    return render_template('jidouka.html', jidouka=jidoukaa)

@main.route('/chart')
@login_required
def chart():
    # mydb = connection.connect(host="127.0.0.1", database = 'db2',user="root", passwd="2787853")
    # cursor = mydb.cursor()
    # query = "Select * from jidouka;"
    # df = pd.read_sql(query,mydb)

    barchart = bar_chart(df)
    linechart = line_chart(df)
    piechart = pie_chart(df)


    # Convert the plots to JSON for embedding in HTML
    charts = {
        'bar_chart': json.dumps(barchart, cls=plotly.utils.PlotlyJSONEncoder),
        'line_chart': json.dumps(linechart, cls=plotly.utils.PlotlyJSONEncoder),
        'pie_chart': json.dumps(piechart, cls=plotly.utils.PlotlyJSONEncoder)
    }

    return render_template('chart.html', charts=charts)

@main.route('/qna')
@login_required
def qna():
    qa = QuestionAndAnswer.query.all()
    return render_template('qna.html',qa = qa )

@main.route('/create_qa', methods=('GET','POST'))
@login_required
def create_qa():
    if request.method == 'POST':
        requester = request.form['requester']
        task_type = request.form['task_type']
        task = request.form['task']
        problem = request.form['problem']
        frequency = request.form['frequency']
        num_hours = request.form['num_hours']
        deadline_to_feedback = request.form['deadline_to_feedback']
        qa = QuestionAndAnswer(
            requester = requester,
            task_type = task_type,
            task = task,
            problem = problem,
            frequency = frequency, 
            num_hours = num_hours, 
            deadline_to_feedback = deadline_to_feedback,
        )
        db.session.add(qa)
        db.session.commit()

        return redirect(url_for('main.qna'))
    return render_template('create_qa.html')

@main.route('/<int:qa_id>/edit_qa',methods=('GET','POST'))
@login_required
def edit_qa(qa_id):
    qa = QuestionAndAnswer.query.get_or_404(qa_id)

    if request.method == 'POST':
        requester = request.form['requester']
        task_type = request.form['task_type']
        task = request.form['task']
        problem = request.form['problem']
        frequency = request.form['frequency']
        num_hours = request.form['num_hours']
        deadline_to_feedback = request.form['deadline_to_feedback']

        qa.requester = str(requester)
        qa.task_type = str(task_type)
        qa.task = str(task)
        qa.problem = str(problem)
        qa.frequency = str(frequency)
        qa.num_hours = num_hours 
        qa.deadline_to_feedback = str(deadline_to_feedback)

        db.session.add(qa)
        db.session.commit()
        
        return redirect(url_for('main.qna'))
    return render_template('edit_qa.html', qa=qa)

@main.route('/<int:qa_id>/create_response',methods=('GET','POST'))
@login_required
@admin_required
def create_response(qa_id):
    qa = QuestionAndAnswer.query.get_or_404(qa_id)

    if request.method == 'POST':
        content = request.form['content']
        result = request.form['result']
        feedback = request.form['feedback']

        qa.content = str(content)
        qa.result = str(result)
        qa.feedback = str(feedback)

        db.session.add(qa)
        db.session.commit()

        return redirect(url_for('main.qna'))
    return render_template('create_response.html',qa=qa)

@main.route('/<int:qa_id>/edit_response',methods=('GET','POST'))
@login_required
@admin_required
def edit_response(qa_id):
    qa = QuestionAndAnswer.query.get_or_404(qa_id)

    if request.method == 'POST':
        content = request.form['content']
        result = request.form['result']
        feedback = request.form['feedback']

        qa.content = str(content)
        qa.result = str(result)
        qa.feedback = str(feedback)

        db.session.add(qa)
        db.session.commit()

        return redirect(url_for('main.qna'))
    return render_template('edit_response.html',qa=qa)

@main.route('/definition')
@login_required
def Definition():
    define= definition.query.all()
    return render_template('definition.html',define=define)

@main.route('/definition/<int:define_id>/')
@login_required
def tool(define_id):
    define = definition.query.get_or_404(define_id)
    return render_template('tool.html', definition=define)

@main.route('/<int:define_id>/edit_tool/', methods=('GET', 'POST'))
@login_required
@admin_required
def edit_tool(define_id):
    define = definition.query.get_or_404(define_id)

    if request.method =='POST':
        tool = request.form['tool']
        description = request.form['description']

        define.tool = str(tool)
        define.information=str(description)

        db.session.add(define)
        db.session.commit()

        return redirect(url_for('main.Definition'))
    return render_template('edit_tool.html', define = define)

@main.route('/create_tool', methods=('GET', 'POST'))
@login_required
@admin_required
def create_tool():
    if request.method == 'POST':
        tool = request.form['tool']
        description = request.form['description']
        define = definition(
                    tool = tool,
                    description=description)
        db.session.add(define)
        db.session.commit()

        return redirect(url_for('main.Definition'))
    return render_template('create_tool.html')


@main.route('/create', methods=('GET', 'POST'))
@login_required
@admin_required
def create():
    if request.method == 'POST':
        innovation_name = request.form['innovation_name']
        task_type = request.form['task_type']
        tool = request.form['tool']
        describe_innovation = request.form['describe_innovation']
        software = request.form['software']
        product = request.form['product']
        pic = request.form['pic']
        dc = request.form['dc']
        num_tasks = request.form['num_tasks']
        saved_hours = request.form['saved_hours']
        description = request.form['description']
        jidou = jidouka(innovation_name = innovation_name,
                    task_type = task_type,
                    tool = tool,
                    describe_innovation = describe_innovation,
                    software = software,
                    product = product,
                    pic = pic,
                    dc = dc, 
                    num_tasks = num_tasks,
                    saved_hours = saved_hours,
                    information=description)
        db.session.add(jidou)
        db.session.commit()

        return redirect(url_for('main.index'))
    return render_template('create.html')

@main.route('/<int:jidou_id>/edit/', methods=('GET', 'POST'))
@login_required
@admin_required
def edit(jidou_id):
    jidou = jidouka.query.get_or_404(jidou_id)

    if request.method =='POST':
        innovation_name = request.form['innovation_name']
        task_type = request.form['task_type']
        tool = request.form['tool']
        describe_innovation = request.form['describe_innovation']
        software = request.form['software']
        product = request.form['product']
        pic = request.form['pic']
        dc = request.form['dc']
        num_tasks = request.form['num_tasks']
        saved_hours = request.form['saved_hours']
        description = request.form['description']

        jidou.innovation_name = str(innovation_name)
        jidou.task_type = str(task_type)
        jidou.tool = str(tool)
        jidou.describe_innovation = str(describe_innovation)
        jidou.software = str(software)
        jidou.product = str(product)
        jidou.pic = str(pic)
        jidou.dc = str(dc)
        jidou.num_tasks = num_tasks
        jidou.saved_hours = saved_hours
        jidou.information=str(description)

        db.session.add(jidou)
        db.session.commit()

        return redirect(url_for('main.index'))
    return render_template('edit.html', jidou = jidou)

@main.post('/<int:jidou_id>/delete/')
@login_required
@admin_required
def delete(jidou_id):
    jidou = jidouka.query.get_or_404(jidou_id)
    db.session.delete(jidou)
    db.session.commit()
    return redirect(url_for('main.index'))
@main.post('/<int:define_id>/delete_tool/')
@login_required
@admin_required
def delete_tool(define_id):
    define = definition.query.get_or_404(define_id)
    db.session.delete(define)
    db.session.commit()
    return redirect(url_for('main.Definition'))
@main.post('/<int:qa_id>/delete_qa/')
@login_required
def delete_qa(qa_id):
    qa = QuestionAndAnswer.query.get_or_404(qa_id)
    db.session.delete(qa)
    db.session.commit()
    return redirect(url_for('main.qna'))
@main.post('/<int:qa_id>/delete_response/')
@login_required
@admin_required
def delete_response(qa_id):
    qa = QuestionAndAnswer.query.get_or_404(qa_id)
    qa.content = ""
    qa.result = ""
    qa.feedback = ""
    db.session.add(qa)
    db.session.commit()
    return redirect(url_for('main.qna'))

auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    return render_template('login.html')

@auth.route('/login', methods=['POST'])
def login_post():
    # login code goes here
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=email).first()

    # check if the user actually exists
    # take the user-supplied password, hash it, and compare it to the hashed password in the database
    if not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again.')
        return redirect(url_for('auth.login')) 
    login_user(user, remember=remember)
    return redirect(url_for('main.index'))

@auth.route('/signup')
def signup():
    return render_template('signup.html')

@auth.route('/signup', methods=['POST'])
def signup_post():
    # code to validate and add user to database goes here
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database

    if user: # if a user is found, we want to redirect back to signup page so user can try again
        flash('Email address already exists')
        return redirect(url_for('auth.signup'))

    # create a new user with the form data. Hash the password so the plaintext version isn't saved.
    new_user = User(email=email, name=name, password=generate_password_hash(password, method='pbkdf2:sha256')
                    ,role=UserRole.STANDARD)

    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('auth.login'))

# New route to manage user roles (admin only)
@main.route('/manage_users')
@login_required
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('manage_users.html', users=users)

# Route to update user role
@main.route('/update_user_role/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def update_user_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')
    
    if new_role in [UserRole.ADMIN, UserRole.STANDARD]:
        user.role = new_role
        db.session.commit()
        flash(f'Role updated for user {user.email}')
    else:
        flash('Invalid role specified')
    
    return redirect(url_for('main.manage_users'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('log.before_login'))

log = Blueprint('log', __name__)

@log.route('/')
def before_login():
    return render_template('before_login.html')

@log.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.name)


if __name__ == "__main__":
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(log)
    app.run(host='0.0.0.0', port=7860)  