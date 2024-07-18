import os
from flask import Flask, render_template, url_for, flash, redirect, request, abort, send_from_directory
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, current_user, logout_user, login_required, UserMixin
from models import db, User, Song, Playlist, PlaylistSong
from forms import RegistrationForm, LoginForm
from config import Config

# Initialize Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Ensure the upload directory exists
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize SQLAlchemy
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Define the user_loader function required by Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Define routes

@app.route('/')
@app.route('/home')
def home():
    if current_user.is_authenticated:
        songs = Song.query.filter_by(user_id=current_user.id).all()
        playlists = Playlist.query.filter_by(user_id=current_user.id).all()
    else:
        songs = []
        playlists = []
    return render_template('index.html', songs=songs, playlists=playlists)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = form.password.data  # Hash the password before saving
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.password == form.password.data:
            login_user(user, remember=form.remember.data)
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in {'mp3'}:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            song = Song(title=request.form['title'], artist=request.form['artist'], filename=filename, user_id=current_user.id)
            db.session.add(song)
            db.session.commit()
            return redirect(url_for('home'))
    return render_template('upload.html')

@app.route('/playlist/<int:playlist_id>')
@login_required
def playlist(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    if playlist.owner != current_user:
        abort(403)
    songs = playlist.songs
    return render_template('playlist.html', playlist=playlist, songs=songs)

@app.route('/create_playlist', methods=['POST'])
@login_required
def create_playlist():
    playlist_name = request.form['name']
    if playlist_name:
        playlist = Playlist(name=playlist_name, user_id=current_user.id)
        db.session.add(playlist)
        db.session.commit()
    return redirect(url_for('home'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
