import bcrypt
from uuid import uuid4
from .db_service import get_connection
from .jwt_service import create_token


def register_user(first_name, last_name, email, password):

    conn = get_connection()
    cursor = conn.cursor()

    password_hash = bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()

    try:

        cursor.execute("""
        INSERT INTO users (id, first_name, last_name, email, password_hash)
        VALUES (%s,%s,%s,%s,%s)
        RETURNING id
        """, (
            str(uuid4()),
            first_name,
            last_name,
            email,
            password_hash
        ))

        user_id = cursor.fetchone()[0]

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise e

    finally:
        cursor.close()
        conn.close()

    return user_id


def login_user(email, password):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, password_hash
        FROM users
        WHERE email=%s
    """, (email,))

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    # user not found
    if user is None:
        return None

    user_id, password_hash = user

    # convert to bytes if needed
    if isinstance(password_hash, str):
        password_hash = password_hash.encode("utf-8")

    if not bcrypt.checkpw(password.encode("utf-8"), password_hash):
        return None

    # generate JWT
    token = create_token(str(user_id), email)

    return token

def update_user_profile(user_id: str, first_name: str = None, last_name: str = None, email: str = None, password: str = None) -> bool:
    """Updates the user profile. Returns True if relogin is required (email or password changed), False otherwise."""
    conn = get_connection()
    cursor = conn.cursor()

    relogin_required = False
    updates = []
    params = []

    if first_name is not None:
        updates.append("first_name = %s")
        params.append(first_name)
    if last_name is not None:
        updates.append("last_name = %s")
        params.append(last_name)
    if email is not None:
        # Check if email is already taken by someone else
        cursor.execute("SELECT id FROM users WHERE email = %s AND id != %s", (email, user_id))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            raise Exception("Email already exists")
        updates.append("email = %s")
        params.append(email)
        relogin_required = True
    if password is not None:
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        updates.append("password_hash = %s")
        params.append(password_hash)
        relogin_required = True

    if not updates:
        cursor.close()
        conn.close()
        return False

    params.append(user_id)
    param_tuple = tuple(params)
    
    query = f"UPDATE users SET {', '.join(updates)} WHERE id = %s"

    try:
        cursor.execute(query, param_tuple)
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

    return relogin_required