import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from streamlit_option_menu import option_menu

st.set_page_config(layout="wide")

# Initialize connection
conn = sqlite3.connect('inventory.db')
c = conn.cursor()

# Create or alter table to ensure the schema is correct
def create_or_update_table():
    # Ensure all necessary columns are present
    c.execute('''
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item TEXT,
        description TEXT,
        brand TEXT,
        quantity INTEGER,
        rate REAL,
        total REAL,
        date_added TEXT,
        type TEXT,
        added_by TEXT
    )
    ''')
    conn.commit()

    # Check existing columns in the inventory table
    c.execute('PRAGMA table_info(inventory)')
    columns = [col[1] for col in c.fetchall()]

    # Add missing columns if needed
    if 'type' not in columns:
        c.execute('ALTER TABLE inventory ADD COLUMN type TEXT')
    if 'added_by' not in columns:
        c.execute('ALTER TABLE inventory ADD COLUMN added_by TEXT')
    
    conn.commit()

create_or_update_table()

# Create table for storing bills
def create_bill_table():
    c.execute('''
    CREATE TABLE IF NOT EXISTS bills (
        bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT,
        customer_address TEXT,
        items TEXT,
        quantities TEXT,
        total_amount REAL,
        date_generated TEXT
    )
    ''')
    conn.commit()

create_bill_table()

# Functions for database operations
def add_item(item, description, brand, quantity, rate, item_type, added_by):
    total = quantity * rate
    date_added = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''
    INSERT INTO inventory (item, description, brand, quantity, rate, total, date_added, type, added_by)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (item, description, brand, quantity, rate, total, date_added, item_type, added_by))
    conn.commit()
    # Return the newly added item
    c.execute('SELECT * FROM inventory ORDER BY id DESC LIMIT 1')
    return c.fetchone()

def update_item(id, item, description, brand, quantity, rate, item_type, added_by):
    total = quantity * rate
    c.execute('''
    UPDATE inventory
    SET item=?, description=?, brand=?, quantity=?, rate=?, total=?, type=?, added_by=?
    WHERE id=?
    ''', (item, description, brand, quantity, rate, total, item_type, added_by, id))
    conn.commit()

def delete_item(id):
    c.execute('DELETE FROM inventory WHERE id=?', (id,))
    conn.commit()

def generate_bill(customer_name, customer_address, items, quantities, total_amount):
    date_generated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''
    INSERT INTO bills (customer_name, customer_address, items, quantities, total_amount, date_generated)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (customer_name, customer_address, ','.join(map(str, items)), ','.join(map(str, quantities)), total_amount, date_generated))
    conn.commit()
    # Return the newly generated bill
    c.execute('SELECT * FROM bills ORDER BY bill_id DESC LIMIT 1')
    return c.fetchone()

# Top navigation using streamlit_option_menu
selected = option_menu(
    menu_title=None,  # required
    options=["Add Item", "View Inventory", "Generate Bill", "Last Bills"],  # required
    icons=["plus-circle", "eye", "file-invoice", "history"],  # optional
    menu_icon="cast",  # optional
    default_index=0,  # optional
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "#fafafa"},
        "icon": {"color": "blue", "font-size": "25px"},
        "nav-link": {
            "font-size": "20px",
            "text-align": "left",
            "margin": "0px",
            "--hover-color": "#eee",
            "color": "black",
        },
        "nav-link-selected": {"background-color": "#4CAF50"},
    },
)

# Streamlit UI
st.title('Demeo/Simple Inventory Management System')

if selected == "Add Item":
    st.header('Add New Item')
    with st.form('Add Item'):
        col1, col2, col3 = st.columns(3)
        with col1:
            item = st.text_input('Item', placeholder='Enter the item name')
            quantity = st.number_input('Quantity', min_value=0, step=1, placeholder='Enter quantity' , key = "01")
            item_type = st.text_input('Type', placeholder='Enter the type of item')
        with col2:
            description = st.text_input('Description', placeholder='Enter description')
            rate = st.number_input('Rate', min_value=1.0, step=0.1, placeholder='Enter rate per unit')
        with col3:
            brand = st.text_input('Brand', placeholder='Enter brand name')
            added_by = st.text_input('Added By', placeholder='Enter your name')

        submitted = st.form_submit_button('Add Item')
        
        if submitted:
            new_item = add_item(item, description, brand, quantity, rate, item_type, added_by)
            st.success('Item added successfully!')
            
            # Show the newly added item
            st.write('**Newly Added Item:**')
            st.write(pd.DataFrame([new_item], columns=['ID', 'Item', 'Description', 'Brand', 'Quantity', 'Rate', 'Total', 'Date Added', 'Type', 'Added By']), width=100000)

elif selected == "View Inventory":
    st.header('Current Inventory')
    inventory_df = pd.read_sql('SELECT * FROM inventory', conn)
    
    st.dataframe(inventory_df, width=100000)

    
    st.subheader('Edit or Delete Items')
    id_to_edit = st.number_input('Enter ID of item to edit/delete', min_value=1, step=1, placeholder='Enter item ID')
    action = st.selectbox('Action', ['Edit', 'Delete'])

    if action == 'Edit':
        with st.form('Edit Item'):
            col1, col2, col3 = st.columns(3)
            with col1:
                item = st.text_input('Item', placeholder='Enter new item name')
                quantity = st.number_input('Quantity', min_value=0, step=1, placeholder='Enter new quantity')
                item_type = st.text_input('Type', placeholder='Enter new type of item')
            with col2:
                description = st.text_input('Description', placeholder='Enter new description')
                rate = st.number_input('Rate', min_value=1.0, step=0.1, placeholder='Enter new rate per unit')
            with col3:
                brand = st.text_input('Brand', placeholder='Enter new brand name')
                added_by = st.text_input('Added By', placeholder='Enter your name')
            
            update_submitted = st.form_submit_button('Update Item')
            if update_submitted:
                update_item(id_to_edit, item, description, brand, quantity, rate, item_type, added_by)
                st.success('Item updated successfully!')

    elif action == 'Delete':
        if st.button('Delete Item'):
            delete_item(id_to_edit)
            st.success('Item deleted successfully!')

elif selected == "Generate Bill":
    st.header('Generate Invoice')
    
    with st.form('Generate Invoice'):
        col1, col2 = st.columns(2)
        with col1:
            customer_name = st.text_input('Customer Name', placeholder='Enter customer name')
            customer_address = st.text_input('Customer Address', placeholder='Enter customer address')
        with col2:
            inventory_df = pd.read_sql('SELECT * FROM inventory', conn)
            selected_items = st.multiselect('Select Items', inventory_df['item'])
        
        generate_invoice_submitted = st.form_submit_button('Generate Invoice')

        if generate_invoice_submitted:
            if not selected_items:
                st.error('Please select at least one item.')
            else:
                selected_quantities = []
                total_amount = 0

                for item in selected_items:
                    quantity = st.number_input(f'Quantity for {item}', min_value=1, step=1)
                    selected_quantities.append(quantity)
                    item_rate = inventory_df[inventory_df['item'] == item]['rate'].values[0]
                    total_amount += item_rate * quantity

                generated_bill = generate_bill(customer_name, customer_address, selected_items, selected_quantities, total_amount)
                st.success('Invoice generated successfully!')

                # Show the generated bill
                st.write('**Generated Invoice:**')
                st.write(pd.DataFrame([generated_bill], columns=['Bill ID', 'Customer Name', 'Customer Address', 'Items', 'Quantities', 'Total Amount', 'Date Generated']), width=100000)

elif selected == "Last Bills":
    st.header('Previous Bills')
    bills_df = pd.read_sql('SELECT * FROM bills ORDER BY date_generated DESC LIMIT 10', conn)
    st.dataframe(bills_df, width=100000)
