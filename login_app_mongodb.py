import streamlit as st
import re
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
import calendar
from datetime import datetime

from pymongo import MongoClient
from passlib.hash import pbkdf2_sha256

# Connect to your MongoDB instance.
# Replace the connection URL with your own.
client = MongoClient("mongodb+srv://Kevcar98:QKlGirVW2q6lYuuc@cluster0.bg2grjx.mongodb.net/")
db = client["your_db_name"]  # Replace with your database name
users_collection = db["users"]  # Replace with your collection name

def LogOut():
    col1, col2, col3 = st.columns([0.26, 0.3, 0.1])
    with col1:
        pass
    with col2:
        pass        
    with col3:
        if st.button("Log Out"):
            st.experimental_set_query_params(logged_in="false")

def create_user(username, password, is_admin=False):
    # Hash the user's password before storing it in the database.
    hashed_password = pbkdf2_sha256.hash(password)
    user_data = {"username": username, "password": hashed_password, "is_admin": is_admin}
    users_collection.insert_one(user_data)

def verify_user(username, password):
    user_data = users_collection.find_one({"username": username})
    if user_data and pbkdf2_sha256.verify(password, user_data["password"]):
        return user_data
    return None

def get_admin_count():
    admin_count = 0
    for user in users_collection.find({"is_admin": True}):
        admin_count += 1
    return admin_count

def update_user(username, new_password, is_admin):
    # Find the user by the username
    user_data = users_collection.find_one({"username": username})
    Success=True
    if user_data:
        if new_password:
            # Hash and update the new password if provided
            hashed_password = pbkdf2_sha256.hash(new_password)
            user_data["password"] = hashed_password

        # If the user is attempting to remove admin privileges, check if there will be at least one admin left
        if not is_admin and get_admin_count() == 1 and user_data["is_admin"]:
            st.error("Update Failed: There needs to be at least one admin.")
            Success=False
        else:
            user_data["is_admin"] = is_admin
            # Update the user's data in the database
            users_collection.update_one({"username": username}, {"$set": user_data})
    return Success

def login_and_register():
    st.title("Login or Register")

    option = st.selectbox("Select an option:", ["Login", "Register"])

    if option == "Login":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            user_data = verify_user(username, password)
            if user_data:
                st.experimental_set_query_params(logged_in="true", username=username, is_admin=user_data.get("is_admin", False))
            else:
                st.error("Login failed. Please check your credentials.")

    elif option == "Register":
        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        is_admin = st.checkbox("Is Admin")

        if st.button("Register"):
            if not users_collection.find_one({"username": new_username}):
                create_user(new_username, new_password, is_admin)
                st.success("Registration successful!")
                st.write(f"Account for {new_username} has been created.")
            else:
                st.error("Registration failed. Username already exists.")

def admin_page():
    LogOut()    
    st.title("Admin Page") 
    users_data = users_collection.find()
    user_list = list(users_data)

    if user_list:
        st.write("User Database:")
        table = st.table(user_list)
    else:
        st.write("No user data found.")

    st.write("Update user:")
    username_to_modify = st.text_input("Enter Username")

    new_password = st.text_input("New Password", type="password")
    is_admin_checkbox = st.checkbox("Is Admin")

    if st.button("Update User"):
        Success=update_user(username_to_modify, new_password, is_admin_checkbox)
        if Success:
            st.success(f"{username_to_modify} has been updated!")

        # Retrieve the updated user data
        users_data = users_collection.find()
        user_list = list(users_data)
        if user_list:
            table.table(user_list)
        else:
            st.write("No user data found.")

def home(username):
    LogOut()
    susername = re.sub(r'[\[\]\']', '', str(username))#removes square brackets and single quotations
    st.title(f"Home Page - Welcome, {susername}!")
    st.write("You can put your content here.")
    
    selectedCurrency = option_menu(
        menu_title= None,
        options=["GBP","Euro","USD"],
        icons=["1","2","3"],
        orientation= "horizontal",)





def main():
    params = st.experimental_get_query_params()
    if "logged_in" in params and params["logged_in"] == ["true"]:
        username = params.get('username')
        is_admin = params.get('is_admin')        

        if is_admin == ['True']:
            admin_page()
        elif is_admin == ['False']:
            home(username)
    else:
        login_and_register()

if __name__ == "__main__":
    main()
