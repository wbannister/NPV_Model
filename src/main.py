import streamlit as st
st.set_page_config(layout="wide")
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import itertools
from datetime import date

from npv_irr_calculations import *
from dateutil.relativedelta import relativedelta

import pyodbc
from dotenv import load_dotenv
import os


def extract_data(connection_string, query):
    # connect to the database
    with pyodbc.connect(connection_string) as conn:
        # execute the query and return the result as a pandas Dataframe
        df = pd.read_sql(query, conn)

    return df

# Build an absolute path to the .env file
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=env_path)

# Access the variables
server = os.getenv('SERVER')
house_db = os.getenv('HOUSE_DB')
user_id = os.getenv('USER_ID')
db_password = os.getenv('DB_PASSWORD')

# Connection string for the house database
connection_string_house = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={server};"
    f"DATABASE={house_db};"
    f"UID={user_id};"
    f"PWD={db_password};"
    f"Encrypt=yes;"
    f"TrustServerCertificate=no;"
    f"Connection Timeout=30;"
)

def get_connection():
        return pyodbc.connect(connection_string_house)

conn = get_connection()

@st.cache_data
def load_properties():
    query = "SELECT DISTINCT property FROM dbo.business_plans"
    df = pd.read_sql(query, conn)
    return df['property'].tolist()

@st.cache_data
def load_units(selected_property):
    # Query units for the selected property
    query = f"SELECT DISTINCT unit FROM dbo.business_plans WHERE property = '{selected_property}'"
    df = pd.read_sql(query, conn)
    return df['unit'].tolist()

@st.cache_data
def load_defaults(selected_property, selected_unit):
    # Query for default values based on property and unit selection
    query = f"""
        SELECT floor_area, refurb_psf, refurb_duration, rent_pa, review_date, lease_start,
               ERV_psf, break_date, lease_end, end_void, initial_void, NER_discount,
               term_yrs, initial_rent_free, relet_rent_free, rates_psf, Rates_Relief, sc_psf, exit_yield
        FROM dbo.business_plans
        WHERE property = '{selected_property}' AND unit = '{selected_unit}'
    """
    df = pd.read_sql(query, conn)
    return df.iloc[0] if not df.empty else None

# Helper function to safely convert to date
def safe_date(date_value, fallback):
    if date_value is None:
        return fallback
    try:
        return pd.to_datetime(date_value).date()
    except Exception:
        return fallback

def main():
    st.sidebar.title("Model Inputs")

    # Initial Inputs (Organized Across Columns)
    col7, col8 = st.columns(2)


    # 2. Cascading Dropdowns for Property and Unit Selection
    property_list = load_properties()
    with col7:
        selected_property = st.selectbox("Select Property", property_list)

    with col8:
    # Only load units if a property is selected
        if selected_property:
            unit_list = load_units(selected_property)
            selected_unit = st.selectbox("Select Unit", unit_list)
        else:
            selected_unit = None

    # 3. Load Default Values if both selections have been made
    defaults = None
    if selected_property and selected_unit:
        defaults = load_defaults(selected_property, selected_unit)
        if defaults is None:
            st.error("No default values found for this property and unit selection.")

    # 4. Main Inputs: use the default values from the DB if available; otherwise, use your hard-coded defaults.
    if defaults is not None:
        default_unit_area      = defaults['floor_area']
        default_refurb_cost    = defaults['refurb_psf']
        default_refurb_duration = defaults['refurb_duration']
        # Convert annual rent (rent_pa) to monthly rent
        default_current_rent   = defaults['rent_pa']
        default_review_date = safe_date(defaults['review_date'], date(2025, 6, 30))
        default_lease_start = safe_date(defaults['lease_start'], date(2020, 6, 30))
        default_headline_erv   = defaults['ERV_psf']
        default_lease_termination = safe_date(defaults['lease_end'], date(2025, 12, 31))
        default_void_period    = defaults['end_void']
        default_ner_discount   = defaults['NER_discount']
        default_relet_term     = defaults['term_yrs']
        default_rf             = defaults['initial_rent_free']
        default_rates_percent = defaults['rates_psf'] / defaults['ERV_psf'] * 100
        # Optionally, if you want to update sidebar inputs as well:
        default_rates_relief   = defaults['Rates_Relief']
        default_vacant_sc      = defaults['sc_psf']
        default_exit_yield     = defaults['exit_yield'] * 100
    else:
        default_unit_area      = 10000
        default_refurb_cost    = 20
        default_current_rent   = 50000
        default_review_date    = date(2025, 6, 30)
        default_lease_start    = date(2020, 6, 30)
        default_headline_erv   = 20.00
        default_lease_termination = date(2025, 12, 31)
        default_void_period    = 12
        default_ner_discount   = 50
        default_relet_term     = 5
        default_rf             = 3
        default_rates_relief   = 3
        default_vacant_sc      = 2
        default_exit_yield     = 12.00

    st.markdown("---")

    # Top-of-Page Inputs (Organized Across Columns)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        unit_area = st.number_input("Unit Area (sq ft)", value=default_unit_area)
        lease_start = st.date_input("Lease Start Date", value=default_lease_start)

        refurb_cost = st.number_input("Refurb Cost (£ psf)", value=default_refurb_cost)

    with col2:
        current_rent = st.number_input("Current Rent (£ per month)", value=default_current_rent)
        review_date = st.date_input("Review Date", value=default_review_date)
        refurb_duration = st.number_input("Refurb Duration (months)", value=default_refurb_duration, step=1.0)

    with col3:
        headline_erv = st.number_input("Headline ERV (£ per sq ft)", value=default_headline_erv, step=0.25, format="%.2f")
        lease_termination = st.date_input("Lease Termination Date", value=default_lease_termination)
        void_period = st.number_input("Addn. Void Period (months)", value=default_void_period, step=1.0)

    with col4:
        ner_discount = st.number_input("NER Discount (%)", value=default_ner_discount)
        relet_term = st.number_input("Relet Term (years)", value=default_relet_term)
        rf = st.number_input("Rent Free Period (months)", value=default_rf, step=1.0)


    # Sidebar Inputs
    st.sidebar.subheader("Default Model Assumptions")
    cashflow_start = st.sidebar.date_input("Cashflow Start Date", value=date(2025, 1, 1))
    cashflow_term = st.sidebar.number_input("Cashflow Term (months)", value=60)
    exit_date = cashflow_start + relativedelta(months=cashflow_term)
    st.sidebar.markdown(f"**Exit Date:** {exit_date}")

    st.sidebar.markdown("---")

    st.sidebar.subheader("Entry Pricing Assumptions")

    entry_initial_yield = st.sidebar.number_input("Entry Initial Yield (%)", value=default_exit_yield)
    purchasers_costs = st.sidebar.number_input("Purchasers Costs (%)", value=6.8)
    # current_rent is defined below; compute initial valuation once it’s available:
    initial_val = initial_yield_valuation(current_rent, entry_initial_yield / 100, purchasers_costs / 100) if 'current_rent' in locals() else 0
    st.sidebar.markdown(
        f"<div style='background-color:#f0f0f0; padding:10px; border-radius:5px; font-size:18px; font-weight:bold;'>Entry Valuation: £{initial_val:,.0f}</div>",
        unsafe_allow_html=True
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("Exit Pricing Assumptions")

    exit_initial_yield = st.sidebar.number_input("Exit Initial Yield (%)", value=default_exit_yield)

    # Initialize with default values
    exit_rent = 0
    exit_price = 2000000  # default until cashflow is generated

    # Create a placeholder for the exit rent display
    exit_rent_placeholder = st.sidebar.empty()
    # Create a placeholder for the exit price display
    exit_price_placeholder = st.sidebar.empty()

    # if "cashflow" in st.session_state and st.session_state["cashflow"] is not None:
    #     # Use the second-to-last row of the cashflow table
    #     second_last_row = st.session_state["cashflow"].iloc[-2]
    #     # Extract rents from the different rent option columns and determine the maximum
    #     max_rent = max(
    #         second_last_row["contracted_rent"],
    #         second_last_row["reviewed_rent"],
    #         second_last_row["relet_rent"]
    #     )
    #     # Annualise the maximum rent to get exit rent
    #     exit_rent = max_rent * 12
    #     # Compute exit price using the initial yield valuation formula
    #     exit_price = initial_yield_valuation(exit_rent, exit_initial_yield / 100, purchasers_costs / 100)

    # # Update the placeholders with current values
    # exit_rent_placeholder.write(f"Exit Rent (Annualised): £{exit_rent:,.2f}" if exit_rent > 0 else "Computed Exit Rent will appear here once cashflow is generated.")
    # exit_price_placeholder.markdown(
    #     f"<div style='background-color:#f0f0f0; padding:10px; border-radius:5px; font-size:18px; font-weight:bold;'>Exit Valuation: £{exit_price:,.0f}</div>" if exit_rent > 0 else "Computed Exit Price will appear here once cashflow is generated.",
    #     unsafe_allow_html=True
    # )

    st.sidebar.markdown("---")
    st.sidebar.subheader("Misc Assumptions")
    vacant_rates_percent = st.sidebar.number_input("Vacant Rates Percent (%)", value=default_rates_percent, step = 1.0)
    rates_relief = st.sidebar.number_input("Rates Relief (months)", value=default_rates_relief, step=1.0)
    vacant_sc = st.sidebar.number_input("Vacant Service Charge (£ per sq ft)", value=default_vacant_sc, step=0.25)

    exit_price = st.session_state.get("exit_price", initial_val)  # default to initial valuation for exit price
    # if st.button("Calculate Cashflow"):
    cashflow = create_cashflow(
        cashflow_start=cashflow_start,
        cashflow_term=cashflow_term,
        unit_area=unit_area,
        lease_start=lease_start,
        current_rent=current_rent,
        review_date=review_date,
        lease_termination=lease_termination,
        headline_erv=headline_erv,
        ner_discount=ner_discount/100,
        refurb_cost=refurb_cost,
        refurb_duration=refurb_duration,
        void_period=void_period,
        rf=rf,
        relet_term=relet_term,
        exit_cap=exit_initial_yield/100,
        vacant_rates_percent=vacant_rates_percent/100,
        rates_relief=rates_relief,
        vacant_sc=vacant_sc,
        entry_price=initial_val,
        exit_price=exit_price
    )
    st.session_state["cashflow"] = cashflow


    # Use the second-to-last row of the cashflow table
    second_last_row = st.session_state["cashflow"].iloc[-2]
    # Extract rents from the different rent option columns and determine the maximum
    max_rent = max(
        second_last_row["contracted_rent"],
        second_last_row["reviewed_rent"],
        second_last_row["relet_rent"]
    )
    # Annualise the maximum rent to get exit rent
    exit_rent = max_rent * 12
    # Compute exit price using the initial yield valuation formula
    exit_price_new = initial_yield_valuation(exit_rent, exit_initial_yield / 100, purchasers_costs / 100)

    st.session_state["exit_price"] = exit_price_new

    # Update the placeholders with current values
    exit_rent_placeholder.write(f"Exit Rent (Annualised): £{exit_rent:,.2f}" if exit_rent > 0 else "Computed Exit Rent will appear here once cashflow is generated.")
    exit_price_placeholder.markdown(
        f"<div style='background-color:#f0f0f0; padding:10px; border-radius:5px; font-size:18px; font-weight:bold;'>Exit Valuation: £{exit_price_new:,.0f}</div>" if exit_rent > 0 else "Computed Exit Price will appear here once cashflow is generated.",
        unsafe_allow_html=True
    )

    # If cashflow exists, display results and allow dynamic discount rate updates
    if st.session_state["cashflow"] is not None:
        st.subheader("Cashflow Outputs")

        discount_rate_input = st.number_input("Discount Rate %", value=10.00, key="discount_rate", min_value=0.00, max_value=100.00, step=0.25)
        col4, col5 = st.columns(2)
        with col4:
            irr = calculate_irr(st.session_state["cashflow"]['period_start'], st.session_state["cashflow"]['cashflow'])
            st.write(f"IRR (Monthly): {irr * 100:.2f}%")

        with col5:
            npv = calculate_npv(discount_rate_input/100, st.session_state["cashflow"]['period_start'], st.session_state["cashflow"]['cashflow'])
            st.write(f"NPV: £{npv:,.2f}")


        # Old chart format
        # Plot the cashflows without clearing the previous output
        import plotly.graph_objects as go
        chart_data = st.session_state["cashflow"].iloc[1:-1]
        fig = go.Figure()

        colors = {
            "contracted_rent": "green",
            "reviewed_rent": "lightgreen",
            "refurbishment_period": "orange",
            "void_period": "red",
            "rf_period": "yellow",
            "relet_rent": "blue"
        }
        for category, color in colors.items():
            cat_months = chart_data[chart_data["category"] == category]["month"].tolist()
            if not cat_months:
                continue

            segs = []
            for k, g in itertools.groupby(enumerate(cat_months), key=lambda ix: ix[1] - ix[0]):
                group = list(g)
                segs.append((group[0][1], group[-1][1]))

            for start, end in segs:
                fig.add_shape(
                    type="rect",
                    x0=start,
                    x1=end + 1,
                    y0=chart_data["cashflow_line"].min(),
                    y1=chart_data["cashflow_line"].max(),
                    fillcolor=color,
                    opacity=0.3,
                    layer="below",
                    line_width=0,
                )
            fig.add_trace(
                {
                    "type": "scatter",
                    "x": [None],
                    "y": [None],
                    "mode": "markers",
                    "marker": {"size": 10, "color": color},
                    "name": category,
                    "showlegend": True,
                }
            )

        fig.add_trace(
            go.Scatter(
                x=chart_data["month"],
                y=chart_data["cashflow_line"],
                mode="lines",
                line=dict(color="black", width=2),
                name="Cashflow",
            )
        )

        fig.update_layout(
            title="Cashflow Over Time with Full-Row Category Shading",
            xaxis_title="Month",
            yaxis_title="Cashflow",
            showlegend=True,
        )

        # st.plotly_chart(fig)



        import plotly.express as px

        # Present the rent components over time using a multi-line chart
        if "cashflow" in st.session_state and st.session_state["cashflow"] is not None:
            df = st.session_state["cashflow"]
            fig2 = go.Figure()

            fig2.add_trace(go.Scatter(
            x=df["period_start"],
            y=df["contracted_rent"],
            mode="lines+markers",
            name="Contracted Rent",
            line=dict(color="green")
            ))

            fig2.add_trace(go.Scatter(
            x=df["period_start"],
            y=df["reviewed_rent"],
            mode="lines+markers",
            name="Reviewed Rent",
            line=dict(color="lightgreen")
            ))

            fig2.add_trace(go.Scatter(
            x=df["period_start"],
            y=df["rf_period"],
            mode="lines+markers",
            name="Rent Free Period",
            line=dict(color="orange")
            ))

            fig2.add_trace(go.Scatter(
            x=df["period_start"],
            y=df["relet_rent"],
            mode="lines+markers",
            name="Relet Rent",
            line=dict(color="blue")
            ))

            fig2.add_trace(go.Scatter(
            x=df["period_start"],
            y=df["void_period"],
            mode="lines+markers",
            name="Void Costs",
            line=dict(color="red")
            ))

            fig2.update_layout(
            title="Income Components over Time",
            xaxis_title="Period Start",
            yaxis_title="Rent (£)"
            )
            # st.plotly_chart(fig2)


            fig3 = go.Figure(
                go.Scatter(
                    x=df["period_start"],
                    y=df["refurbishment_period"],
                    name="Refurbishment Period",
                    mode="lines",
                    line=dict(color="red"),
                    fill="tozeroy"
                )
            )
            fig3.update_layout(
                title="Refurbishment Period Over Time",
                xaxis_title="Period Start",
                yaxis_title="Refurbishment Period"
            )
            # st.plotly_chart(fig3)
            col1, col2 = st.columns(2)

            with col1:
                st.plotly_chart(fig2, use_container_width=True)
            with col2:
                st.plotly_chart(fig3, use_container_width=True)

        display_df = st.session_state["cashflow"].copy().drop(columns=["cashflow_line", "month"])
        currency_fmt = lambda x: f"£{x:,.2f}" if isinstance(x, (int, float)) else x
        format_dict = {col: currency_fmt for col in display_df.columns}

        st.subheader("Cashflow Data Table")
        st.dataframe(
            display_df.style.format(format_dict)
        )

if __name__ == "__main__":
    main()
