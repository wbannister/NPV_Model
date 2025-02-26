# src/main.py

import streamlit as st
import numpy as np

from npv_irr_calculations import calculate_npv_monthly, calculate_irr_monthly

def main():
    st.title("Commercial Real Estate NPV/IRR Model (Monthly)")

    st.subheader("Model Inputs")
    # Ask user for number of months in the investment
    months = st.number_input("Investment Duration (months)", min_value=1, value=60, step=1)

    # Ask user for an annual discount rate
    annual_discount_rate = st.number_input("Annual Discount Rate (decimal)", 
                                           min_value=0.0, value=0.10, step=0.01)

    st.write("Enter your monthly cashflows, starting with an initial outflow (Month 0).")

    # We can gather monthly cashflows in a loop or dynamically
    # For brevity, let's do a text_area or a loop. We'll do a simple approach:
    # Loop from 0 to months-1. If months is large, you might want a file upload or something more robust.

    cashflows = []
    for m in range(months):
        default_val = -100000.0 if m == 0 else 2000.0  # example defaults
        cf = st.number_input(f"Month {m} Cashflow", value=default_val, step=500.0, key=f"cf_{m}")
        cashflows.append(cf)

    if st.button("Calculate Monthly NPV & IRR"):
        # Calculate monthly NPV
        npv_value = calculate_npv_monthly(cashflows, annual_discount_rate)
        
        # Calculate monthly IRR
        monthly_irr = calculate_irr_monthly(cashflows)
        # Optionally convert monthly IRR to annual IRR:
        annual_irr = (1 + monthly_irr)**12 - 1 if monthly_irr is not None else None

        st.write(f"**NPV (Monthly):** {npv_value:,.2f}")
        
        if monthly_irr is not None:
            st.write(f"**Monthly IRR:** {monthly_irr * 100:,.2f}%")
            st.write(f"**Annualized IRR (from Monthly):** {annual_irr * 100:,.2f}%")
        else:
            st.write("IRR could not be calculated (check cashflow inputs)")

if __name__ == "__main__":
    main()
