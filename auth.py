import streamlit as st
from db_config import get_db_connection

def verify_login(staff_id, password):
    """Checks the STAFF table for valid credentials."""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Directly querying your STAFF table from image_702ab3.png
            query = "SELECT ROLE, FULLNAME FROM STAFF WHERE STAFF_ID = :1 AND PASSWORD = :2"
            cursor.execute(query, (staff_id, password))
            result = cursor.fetchone()
            if result:
                return {"role": result[0], "name": result[1]}
            return None
        except Exception as e:
            st.error(f"Login Error: {e}")
            return None
        finally:
            conn.close()
    return None

def logout():
    """Clears the session and reloads the app."""
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()
    