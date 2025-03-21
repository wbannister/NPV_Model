import streamlit as st
st.set_page_config(layout="wide")
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import itertools
from datetime import date

from npv_irr_calculations import *
from dateutil.relativedelta import relativedelta

def main():
    st.sidebar.title("Model Inputs")


    # Top-of-Page Inputs (Organized Across Columns)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        unit_area = st.number_input("Unit Area (sq ft)", value=10000)
        lease_start = st.date_input("Lease Start Date", value=date(2020, 6, 30))
    
        refurb_cost = st.number_input("Refurb Cost (£ psf)", value=20)
    
    with col2:
        current_rent = st.number_input("Current Rent (£ per month)", value=50000)
        review_date = st.date_input("Review Date", value=date(2025, 6, 30))
        refurb_duration = st.number_input("Refurb Duration (months)", value=3)
    
    with col3:
        headline_erv = st.number_input("Headline ERV (£ per sq ft)", value=20.00, step=0.25, format="%.2f")
        lease_termination = st.date_input("Lease Termination Date", value=date(2025, 12, 31))
        void_period = st.number_input("Addn. Void Period (months)", value=12)
    
    with col4:
        ner_discount = st.number_input("NER Discount (%)", value=50)
        relet_term = st.number_input("Relet Term (years)", value=5)
        rf = st.number_input("Rent Free Period (months)", value=3)
   

    # Sidebar Inputs
    st.sidebar.subheader("Default Model Assumptions")
    cashflow_start = st.sidebar.date_input("Cashflow Start Date", value=date(2025, 1, 1))
    cashflow_term = st.sidebar.number_input("Cashflow Term (months)", value=60)
    exit_date = cashflow_start + relativedelta(months=cashflow_term)
    st.sidebar.markdown(f"**Exit Date:** {exit_date}")
    
    st.sidebar.markdown("---")
    
    st.sidebar.subheader("Entry Pricing Assumptions")

    entry_initial_yield = st.sidebar.number_input("Entry Initial Yield (%)", value=10.00)
    purchasers_costs = st.sidebar.number_input("Purchasers Costs (%)", value=6.8)
    # current_rent is defined below; compute initial valuation once it’s available:
    initial_val = initial_yield_valuation(current_rent, entry_initial_yield / 100, purchasers_costs / 100) if 'current_rent' in locals() else 0
    st.sidebar.markdown(
        f"<div style='background-color:#f0f0f0; padding:10px; border-radius:5px; font-size:18px; font-weight:bold;'>Entry Valuation: £{initial_val:,.0f}</div>",
        unsafe_allow_html=True
    )
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Exit Pricing Assumptions")
    
    exit_initial_yield = st.sidebar.number_input("Exit Initial Yield (%)", value=12.00)
    
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
    vacant_rates_percent = st.sidebar.number_input("Vacant Rates Percent (%)", value=50)
    rates_relief = st.sidebar.number_input("Rates Relief (months)", value=3)
    vacant_sc = st.sidebar.number_input("Vacant Service Charge (£ per sq ft)", value=2)
    
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
