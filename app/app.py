from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt # For password hashing
from flask_migrate import Migrate # For database migrations
from flask_sqlalchemy import SQLAlchemy # For database models
from secret_manager import SecretManagerDB # Your existing class (will be modified later)
import os # CRITICAL: os is imported here
import logging
import sqlite3 # Keep sqlite3 for IntegrityError handling
from sqlalchemy import or_ # For index route's filtering logic

# --- Define base_dir immediately after imports ---
# This must be here to be used by other parts of the app's initial setup.
base_dir = os.path.abspath(os.path.dirname(__file__))
# --- End base_dir definition ---
import paramiko
import tempfile
import os

# Récupérer les variables d'environnement SFTP
SFTP_HOST = os.environ.get('SFTP_HOST', 'localhost')
SFTP_PORT = int(os.environ.get('SFTP_PORT', 22))
SFTP_USER = os.environ.get('SFTP_USER', 'foo')
SFTP_PASS = os.environ.get('SFTP_PASS', 'pass123')

def sftp_connect():
    transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
    transport.connect(username=SFTP_USER, password=SFTP_PASS)
    sftp = paramiko.SFTPClient.from_transport(transport)
    return sftp, transport

def upload_file_to_sftp(local_path, remote_path):
    sftp, transport = sftp_connect()
    try:
        sftp.put(local_path, remote_path)
    finally:
        sftp.close()
        transport.close()

def download_file_from_sftp(remote_path, local_path):
    sftp, transport = sftp_connect()
    try:
        sftp.get(remote_path, local_path)
    finally:
        sftp.close()
        transport.close()


# --- Flask App Configuration ---
app = Flask(__name__)
app.secret_manager = SecretManagerDB()     

# Basic Flask configuration
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
if app.config['SECRET_KEY'] is None:
    app.config['SECRET_KEY'] = os.urandom(24)
    app.logger.warning("FLASK_SECRET_KEY environment variable not set. Using random key (not secure for production).")
else:
    app.logger.info("FLASK_SECRET_KEY loaded from environment variable.")

# Configure Cloud SQL database path for SQLAlchemy (using Private IP)
DB_USER = os.environ.get('DB_USER', 'Imed') # Your Cloud SQL username (Corrected to 'Imed' with capital 'I')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Eve123++') # Your Cloud SQL password
DB_NAME = os.environ.get('DB_NAME', 'secret-manager-prod') # Your Cloud SQL database name
DB_PRIVATE_IP = os.environ.get('DB_PRIVATE_IP', '10.46.160.3') # Your Cloud SQL instance's private IP

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(base_dir, 'secrets.db')}"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Suppress warning
app.logger.info("Connecting to Cloud SQL via private IP.")


# --- Logging Configuration (now base_dir is defined correctly) ---
log_dir = os.path.join(base_dir, 'logs')
os.makedirs(log_dir, exist_ok=True) # Ensure the logs directory exists

log_file_path = os.path.join(log_dir, 'secret_manager_app.log')
file_handler = logging.FileHandler(log_file_path)
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.DEBUG)


# --- Flask Extensions Initialization ---
db = SQLAlchemy(app) # Initialize SQLAlchemy with the app
bcrypt = Bcrypt(app) # Initialize Bcrypt with the app
login_manager = LoginManager(app) # Initialize Flask-Login with the app
login_manager.login_view = 'login' # Set the login view for Flask-Login (where to redirect unauthenticated users)

migrate = Migrate(app, db) # Initialize Flask-Migrate with the app and db


# --- User Model Definition ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False) # Hashed password
    secrets = db.relationship('Secret', backref='owner', lazy=True)

    def __repr__(self):
        return f"User('{self.username}')"

# --- Secret Model Definition (Updated for User Ownership) ---
class Secret(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    encrypted_value = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # --- ADD THIS LINE ---
    # This relationship links secrets to the SharedSecret association table
    # It allows querying secrets by who they are shared with.
    shared_with_users = db.relationship('SharedSecret', backref='shared_secret_obj', lazy=True)
    # --- END ADDITION
    __table_args__ = (db.UniqueConstraint('user_id', 'name', name='_user_secret_name_uc'),)

    def __repr__(self):
        return f"Secret('{self.name}', user_id={self.user_id})"

# --- SharedSecret Model Definition ---
class SharedSecret(db.Model):
    __tablename__ = 'shared_secret'
    id = db.Column(db.Integer, primary_key=True)
    secret_id = db.Column(db.Integer, db.ForeignKey('secret.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    __table_args__ = (db.UniqueConstraint('secret_id', 'user_id', name='_shared_secret_uc'),)

    def __repr__(self):
        return f"<SharedSecret secret_id={self.secret_id} user_id={self.user_id}>"


# --- Flask-Login User Loader ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --- Flask Routes (Updated for Authentication & Ownership) ---

@app.route('/')
@login_required
def index():
    app.logger.info(f'User {current_user.username} accessed the index page.')
    
    # Ensure 'from sqlalchemy import or_' is at the top of app.py
    # This import is already included at the top now in this suggested version.
    from sqlalchemy import or_ # Adding here as a reminder to ensure it's at the top

    search_query = request.args.get('query', '').strip()
    
    base_query = Secret.query.filter(
        or_(
            Secret.user_id == current_user.id,
            Secret.shared_with_users.any(user_id=current_user.id)
        )
    )
    
    if search_query:
        secrets = base_query.filter(Secret.name.ilike(f'%{search_query}%')).all()
        app.logger.info(f"User {current_user.username} searched for secrets matching '{search_query}'.")
    else:
        secrets = base_query.all()
        app.logger.info(f"User {current_user.username} viewed all owned/shared secrets.")
        
    for secret in secrets:
        try:
            secret.decrypted_value = app.secret_manager.decrypt(secret.encrypted_value)
        except Exception as e:
            secret.decrypted_value = "[DECRYPTION ERROR]"
            app.logger.error(f"Error decrypting secret ID {secret.id} for user {current_user.username}: {e}", exc_info=True)
            
    return render_template('index.html', secrets=secrets)


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_secret():
    if request.method == 'POST':
        name = request.form['name']
        value = request.form['value']
        if not name or not value:
            flash("Name and value cannot be empty!", 'danger')
            app.logger.warning(f"User {current_user.username} attempted to add secret with empty name or value.")
        else:
            try:
                encrypted_value = app.secret_manager.encrypt(value)

                secret = Secret(name=name, encrypted_value=encrypted_value, user_id=current_user.id)
                db.session.add(secret)
                db.session.commit()
                flash(f"Secret '{name}' added successfully!", 'success')
                app.logger.info(f"Secret '{name}' added by user {current_user.username}.")
                return redirect(url_for('index'))
            except sqlite3.IntegrityError:
                db.session.rollback()
                flash(f"Secret name '{name}' already exists for your account. Please choose a different name.", 'danger')
                app.logger.warning(f"User {current_user.username} attempted to add duplicate secret name '{name}'.")
            except Exception as e:
                db.session.rollback()
                flash(f'An error occurred while adding secret: {e}', 'danger')
                app.logger.error(f"Error while adding secret for user {current_user.username}: {e}", exc_info=True)
    return render_template('add_secret.html')


@app.route('/delete/<int:secret_id>')
@login_required
def delete_secret(secret_id):
    secret = Secret.query.filter_by(id=secret_id, user_id=current_user.id).first_or_404()
    
    try:
        db.session.delete(secret)
        db.session.commit()
        flash(f"Secret '{secret.name}' deleted successfully!", 'info')
        app.logger.info(f"Secret '{secret.name}' (ID: {secret_id}) deleted by user {current_user.username}.")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while deleting secret: {e}", 'danger')
        app.logger.error(f"Error deleting secret (ID: {secret_id}) for user {current_user.username}: {e}", exc_info=True)
        
    return redirect(url_for('index'))


@app.route('/about')
def about():
    app.logger.info('Accessed the about page.')
    return render_template('about.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        flash('You are already logged in!', 'info')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if not username or not password:
            flash('Username and password cannot be empty.', 'danger')
            return render_template('register.html')
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        user = User(username=username, password=hashed_password)
        try:
            db.session.add(user)
            db.session.commit()
            flash('Your account has been created! You are now able to log in', 'success')
            app.logger.info(f"New user registered: {username}")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            db.session.rollback()
            flash('That username is already taken. Please choose a different one.', 'danger')
            app.logger.warning(f"Registration attempt for duplicate username: {username}")
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during registration: {e}', 'danger')
            app.logger.error(f"Error during registration for username {username}: {e}", exc_info=True)

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('You are already logged in!', 'info')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('You have been logged in!', 'success')
            app.logger.info(f"User {username} logged in successfully.")
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
            app.logger.warning(f"Failed login attempt for username: {username}")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    app.logger.info(f"User {current_user.username} logged out.")
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.errorhandler(404)
def page_not_found(e):
    app.logger.warning(f"404 Not Found: {request.url}")
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    app.logger.error(f"500 Internal Server Error: {e}", exc_info=True)
    return render_template('500.html'), 500

@app.route('/edit/<int:secret_id>', methods=['GET', 'POST'])
@login_required
def edit_secret(secret_id):
    secret = Secret.query.filter_by(id=secret_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        new_name = request.form['name']
        new_value = request.form['value']

        if not new_name or not new_value:
            flash("Name and value cannot be empty!", "danger")
            return render_template('edit_secret.html', secret=secret)

        try:
            # Vérifier si le nouveau nom est déjà pris par un autre secret du même utilisateur
            existing = Secret.query.filter(Secret.user_id == current_user.id, Secret.name == new_name, Secret.id != secret.id).first()
            if existing:
                flash(f"Secret name '{new_name}' already exists. Please choose a different name.", "danger")
                return render_template('edit_secret.html', secret=secret)

            # Met à jour les valeurs
            secret.name = new_name
            secret.encrypted_value = app.secret_manager.encrypt(new_value)
            db.session.commit()
            flash(f"Secret '{new_name}' updated successfully!", "success")
            app.logger.info(f"Secret '{new_name}' (ID: {secret_id}) updated by user {current_user.username}.")
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred while updating secret: {e}", "danger")
            app.logger.error(f"Error updating secret (ID: {secret_id}) for user {current_user.username}: {e}", exc_info=True)
            return render_template('edit_secret.html', secret=secret)

    # GET request: afficher le formulaire avec les données actuelles
    try:
        secret.decrypted_value = app.secret_manager.decrypt(secret.encrypted_value)
    except Exception as e:
        secret.decrypted_value = "[DECRYPTION ERROR]"
        app.logger.error(f"Error decrypting secret ID {secret.id} for user {current_user.username}: {e}", exc_info=True)
    
    return render_template('edit_secret.html', secret=secret)

from flask import send_file

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash("No file part in the request", 'danger')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash("No file selected", 'danger')
            return redirect(request.url)
        if file:
            # Sauvegarde temporaire
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, file.filename)
            file.save(temp_path)
            try:
                # Upload sur le serveur SFTP, dans le dossier 'upload'
                remote_path = f'/upload/{file.filename}'
                upload_file_to_sftp(temp_path, remote_path)
                flash(f"File '{file.filename}' uploaded successfully to SFTP server.", 'success')
            except Exception as e:
                flash(f"Error uploading file to SFTP: {e}", 'danger')
                app.logger.error(f"Upload error: {e}", exc_info=True)
            finally:
                os.remove(temp_path)
            return redirect(url_for('index'))
    return render_template('upload.html')
@app.route('/files')
@login_required
def list_files():
    try:
        sftp, transport = sftp_connect()
        files = sftp.listdir('/upload')
        sftp.close()
        transport.close()
    except Exception as e:
        files = []
        flash(f"Could not list files on SFTP: {e}", 'danger')
        app.logger.error(f"List files error: {e}", exc_info=True)
    return render_template('files.html', files=files)

@app.route('/download/<filename>')
@login_required
def download_file(filename):
    try:
        sftp, transport = sftp_connect()
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, filename)
        sftp.get(f'/upload/{filename}', temp_path)
        sftp.close()
        transport.close()
        return send_file(temp_path, as_attachment=True)
    except Exception as e:
        flash(f"Error downloading file: {e}", 'danger')
        app.logger.error(f"Download error: {e}", exc_info=True)
        return redirect(url_for('list_files'))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)