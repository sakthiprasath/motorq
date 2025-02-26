import asyncpg
import bcrypt
from flask import Flask, request, jsonify
import jwt
from datetime import datetime, timedelta
from flask_smorest import Blueprint
import os
from functools import wraps
auth_route = Blueprint('auth-service', __name__, url_prefix='/api/auth')

def get_secret_key():
    from server import app
    app.secret_key = 'your_secret_key'
    return app.secret_key


# Database connection setup
async def get_db_connection():
    DB_CONFIG = {
        'database': os.getenv('DB_NAME', 'test_db'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres'),
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432))
    }
    return await asyncpg.connect(**DB_CONFIG)


# Generate hashed password
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


# Check hashed password
def check_password(hashed_password, password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


# Generate token with 2 min expiration
def generate_token(user_id):
    secret_key = get_secret_key()
    payload = {
        'user_id': user_id,
        # Expires in 5 minutes (300s)
        'exp': datetime.utcnow() + timedelta(seconds=300)
    }
    token = jwt.encode(payload, secret_key, algorithm='HS256')
    return token


# Validate token
# def validate_token(token):
#     s = Serializer(get_secret_key())
#     try:
#         data = s.loads(token)
#         return data['user_id']
#     except Exception:
#         return None

async def validate_token_and_get_user_id(token):
    conn = await get_db_connection()
    try:
        # Check if token exists and is not expired
        result = await conn.fetchrow(
            "SELECT user_id, expires_at FROM tokens WHERE token = $1", token
        )

        if result:
            expires_at = result['expires_at']
            if expires_at > datetime.utcnow():
                user_id = result['user_id']
                return user_id
            else:
                return None  # Token is expired
        else:
            return None  # Invalid token
    finally:
        await conn.close()

# Create a decorator function
def token_required(f):
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing.'}), 401

        user_id = await validate_token_and_get_user_id(token)
        if user_id is None:
            return jsonify({'error': 'Invalid or expired token.'}), 401

        return await f(*args, **kwargs, user_id=user_id)  # Pass user_id to the route

    return decorated_function

# Register user
@auth_route.route('/register', methods=['POST'])
async def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    hashed_password = hash_password(password)
    conn = await get_db_connection()
    try:
        # Insert user
        async with conn.transaction():
            result = await conn.fetchrow(
                "INSERT INTO users_new (username, password) VALUES ($1, $2) RETURNING id",
                username, hashed_password
            )
            user_id = result['id']
            # Insert user into users table
            # Insert user into users table with dummy email and timestamps
            email = "test@email.com"
            result = await conn.fetchrow(
                """INSERT INTO users (user_id, name, email, created_at, updated_at) 
                   VALUES ($1, $2, $3, NOW(), NOW()) RETURNING user_id""",
                user_id, username, email  # Pass user_id, username, and email to the query
            )
            user_id = result['user_id']


            # Generate token
            token = generate_token(user_id)

            # Insert token with 2-minute expiration
            expires_at = datetime.now() + timedelta(minutes=5)
            await conn.execute(
                "INSERT INTO tokens (user_id, token, expires_at) VALUES ($1, $2, $3)",
                user_id, token, expires_at
            )

        return jsonify({'message': 'User registered', 'token': token})
    except asyncpg.UniqueViolationError:
        return jsonify({'error': 'Username already exists'}), 400
    finally:
        await conn.close()


@auth_route.route('token/generate', methods=['POST'])
async def generate_token_for_details():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Missing username or password'}), 400

    username = data['username']
    password = data['password']

    conn = await get_db_connection()
    try:
        # Fetch user
        result = await conn.fetchrow(
            "SELECT id, password FROM users_new WHERE username = $1",
            username
        )
        if not result:
            # If there's no such user
            return jsonify({'error': 'Invalid credentials'}), 403

        # Here, instead of hashing the password and comparing it,
        # directly compare using bcrypt as it handles the comparison itself
        if bcrypt.checkpw(password.encode('utf-8'), result['password'].encode('utf-8')):
            user_id = result['id']

            # Generate token
            token = generate_token(user_id)

            # Insert token with 2-minute expiration
            expires_at = datetime.utcnow() + timedelta(minutes=5)
            await conn.execute(
                "INSERT INTO tokens (user_id, token, expires_at) VALUES ($1, $2, $3)",
                user_id, token, expires_at
            )
            return jsonify({'token': token}), 201
        else:
            # Passwords do not match
            return jsonify({'error': 'Invalid credentials'}), 403

    # It's uncommon for this scenario to throw a UniqueViolationError unless under rare race conditions.
    # If needed, additional checks or logic should be applied where users or tokens are being uniquely created.
    except asyncpg.UniqueViolationError as e:
        return jsonify({'error': 'A unique constraint was violated', 'details': str(e)}), 400
    finally:
        # Ensure the connection is always closed
        await conn.close()


@auth_route.route('/validate', methods=['POST'])
async def validate():
    data = request.get_json()
    token = data.get('token')
    user_id = await validate_token_and_get_user_id(token)
    if user_id:
        return jsonify({'message': 'Token is valid', 'user_id': user_id})
    else:
        return jsonify({'error': 'Invalid token'}), 401