# src/main.py

import streamlit as st

def main():
    st.title("Commercial Real Estate NPV/IRR Model")
    st.write("Welcome! In this app, you can load, update, and analyze the cashflows.")
    
    # For now, just a simple input to demonstrate
    discount_rate = st.number_input("Discount Rate (%)", min_value=0.0, value=10.0, step=0.5)

    st.write(f"You entered a discount rate of: {discount_rate}%")

if __name__ == "__main__":
    main()
