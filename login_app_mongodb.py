import streamlit as st
import re
import plotly.graph_objects as go
import plotly.express as px
from streamlit_option_menu import option_menu
import calendar
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

from pymongo import MongoClient
from passlib.hash import pbkdf2_sha256

# Connect to your MongoDB instance.
# Replace the connection URL with your own.
client = MongoClient("mongodb+srv://Kevcar98:QKlGirVW2q6lYuuc@cluster0.bg2grjx.mongodb.net/")
db = client["your_db_name"]  # Replace with your database name
users_collection = db["users"]  # Replace with your collection name
DataEntrys=db["DataEntry"]

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

    selected = option_menu(
    menu_title= None,
    options=["Data Entry","Data Visualization"],
    icons=["pencil-fill","bar-chart-fill"],
    orientation= "horizontal",
)
    if selected == "Data Entry":
        DataEntry(selectedCurrency,susername)
    elif selected == "Data Visualization":
        DataViz(susername)  



def DataEntry(currency,username):

    st.header(f"Data Entry in {currency}")
    years = [datetime.today().year, datetime.today().year + 1]
    months = list(calendar.month_name[1:])
    incomes = ["Salary","Blog","Other Income"]
    expenses = ["Rent","Utilities","Groceries","Car","Saving"]
    comments=""
    periods=""

    with st.form("Entry_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            col1.selectbox("Select Month:", months, key= "month")
            col2.selectbox("Select Year:", years, key="year")          

            with st.expander("Income"):
                for income in incomes:
                    st.number_input(f"{income}:",min_value=0, format="%i", step=10,key=income)
            with st.expander("Expenses"):
                for expense in expenses:
                    st.number_input(f"{expense}:", min_value=0,format="%i",step=10,key=expense)
            with st.expander("Comment"):
                comment = st.text_area("", placeholder="Enter a comment here ...")

            submitted = st.form_submit_button("Save Data")
            if submitted:
                period = str(st.session_state["year"]) + " " + str(st.session_state["month"])
                incomes = {income: st.session_state[income] for income in incomes}
                expenses = {expense: st.session_state[expense] for expense in expenses}
                data_entry = {"user":username,"period": period, "incomes": incomes,"expenses":expenses,"comments":comment}
                DataEntrys.insert_one(data_entry)
                st.success("Data Saved!")

def get_all_periods():
    items = db.fetch_all_periods()
    periods = [item["key"] for item in items]
    return periods

def DataViz(username):
    user=""
    st.header("Data Visualization")
    years = [datetime.today().year, datetime.today().year + 1]
    months = list(calendar.month_name[1:])
    incomes = ["Salary","Blog","Other Income"]
    expenses = ["Rent","Utilities","Groceries","Car","Saving"]

    data = DataEntrys.find_one({"user": "user"})
    incomes = data.get("incomes", {})
    expenses = data.get("expenses", {})

# Create a DataFrame for easier manipulation
    dfExpenses = pd.DataFrame({
        'Category': list(expenses.keys()),
        'Amount': list(expenses.values())
    })

    dfincome = pd.DataFrame({
        'Category': list(incomes.keys()),
        'Amount': list(incomes.values())
    })

# Create a pie chart using Plotly Express
    figIncome = px.pie(dfincome, values='Amount', names='Category', title='Income Breakdown')
    figExpense = px.pie(dfExpenses, values='Amount', names='Category', title='Expenses Breakdown')
# Display the pie chart using Streamlit
    st.plotly_chart(figIncome)
    st.plotly_chart(figExpense)


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
