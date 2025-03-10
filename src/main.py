import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import itertools
from datetime import date

from npv_irr_calculations import create_cashflow, calculate_npv, calculate_irr

def main():
    st.sidebar.title("Model Inputs")

    entry_price = st.sidebar.number_input("Entry Price (£)", value=1000000)
    exit_price = st.sidebar.number_input("Exit Price (£)", value=2000000)
    cashflow_start = st.sidebar.date_input("Cashflow Start Date", value=date(2025, 1, 1))
    cashflow_term = st.sidebar.number_input("Cashflow Term (months)", value=60)
    unit_area = st.sidebar.number_input("Unit Area (sq ft)", value=10000)
    lease_start = st.sidebar.date_input("Lease Start Date", value=date(2020, 6, 30))
    current_rent = st.sidebar.number_input("Current Rent (£ per month)", value=50000)
    review_date = st.sidebar.date_input("Review Date", value=date(2025, 6, 30))
    lease_termination = st.sidebar.date_input("Lease Termination Date", value=date(2025, 12, 31))
    headline_erv = st.sidebar.number_input("Headline ERV (£ per sq ft)", value=20)
    ner_discount = st.sidebar.number_input("NER Discount (%)", value=50)
    refurb_cost = st.sidebar.number_input("Refurbishment Cost (£ per sq ft)", value=20)
    refurb_duration = st.sidebar.number_input("Refurbishment Duration (months)", value=3)
    void_period = st.sidebar.number_input("Void Period (months)", value=12)
    rf = st.sidebar.number_input("Rent Free Period (months)", value=3)
    relet_term = st.sidebar.number_input("Relet Term (months)", value=6)
    exit_cap = st.sidebar.number_input("Exit Cap Rate (%)", value=6)
    vacant_rates_percent = st.sidebar.number_input("Vacant Rates Percent (%)", value=50)
    rates_relief = st.sidebar.number_input("Rates Relief (months)", value=3)
    vacant_sc = st.sidebar.number_input("Vacant Service Charge (£ per sq ft)", value=2)
        
    if st.button("Calculate Cashflow"):
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
            exit_cap=exit_cap/100,
            vacant_rates_percent=vacant_rates_percent/100,
            rates_relief=rates_relief,
            vacant_sc=vacant_sc,
            entry_price=entry_price,
            exit_price=exit_price
        )
        st.session_state["cashflow"] = cashflow
        # st.write("Session State Contents:", st.session_state)
                    
    # If cashflow exists, display results and allow dynamic discount rate updates
    if st.session_state["cashflow"] is not None:
        st.subheader("Cashflow Data")
        st.dataframe(st.session_state["cashflow"])

        discount_rate_input = st.number_input("Discount Rate %", value=10.00, key="discount_rate", min_value=0.00, max_value=100.00, step=0.25)
        irr = calculate_irr(st.session_state["cashflow"]['period_start'], st.session_state["cashflow"]['cashflow'])
        npv = calculate_npv(discount_rate_input/100, st.session_state["cashflow"]['period_start'], st.session_state["cashflow"]['cashflow'])
        st.write(f"IRR (Monthly): {irr * 100:.2f}%")
        st.write(f"NPV: £{npv:.2f}")


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
                y=chart_data["cashflow"],
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
        
        st.plotly_chart(fig)
        # st.subheader("Cashflow Data")
        # st.dataframe(cashflow)
        
        # discount_rate_input = st.number_input("Discount Rate", value=0.1)
        
        # irr = calculate_irr(cashflow['period_start'], cashflow['cashflow'])
        # npv = calculate_npv(discount_rate_input, cashflow['period_start'], cashflow['cashflow'])
        # st.write(f"IRR (Monthly): {irr * 100:.2f}%")
        # st.write(f"NPV: £{npv:.2f}")
        
        # cashflow = cashflow.iloc[1:-1]
        # # Plot the cashflows
        # fig, ax = plt.subplots(figsize=(10, 6))

        # # Define colors for each category
        # colors = {
        #     "contracted_rent": "green",
        #     "reviewed_rent": "lightgreen",
        #     "refurbishment_period": "orange",
        #     "void_period": "red",
        #     "rf_period": "yellow",
        #     "relet_rent": "blue"
        # }
        # import plotly.graph_objects as go

        # # Create an interactive Plotly figure
        # fig = go.Figure()

        # # Add shapes for each contiguous category period
        # for category, color in colors.items():
        #     cat_months = cashflow[cashflow["category"] == category]["month"].tolist()
        #     if not cat_months:
        #         continue

        #     # Identify contiguous segments
        #     segs = []
        #     for k, g in itertools.groupby(enumerate(cat_months), key=lambda ix: ix[1] - ix[0]):
        #         group = list(g)
        #         start = group[0][1]
        #         end = group[-1][1]
        #         segs.append((start, end))

        #     for start, end in segs:
        #         fig.add_shape(
        #             type="rect",
        #             x0=start,
        #             x1=end + 1,
        #             y0=cashflow["cashflow_line"].min(),
        #             y1=cashflow["cashflow_line"].max(),
        #             fillcolor=color,
        #             opacity=0.3,
        #             layer="below",
        #             line_width=0,
        #         )
                
        #     # Add a transparent scatter trace for the legend entry
        #     fig.add_trace(
        #         {
        #             "type": "scatter",
        #             "x": [None],
        #             "y": [None],
        #             "mode": "markers",
        #             "marker": {"size": 10, "color": color},
        #             "name": category,
        #             "showlegend": True,
        #         }
        #     )

        # # Add the cashflow line over the shaded background
        # fig.add_trace(
        #     go.Scatter(
        #         x=cashflow["month"],
        #         y=cashflow["cashflow"],
        #         mode="lines",
        #         line=dict(color="black", width=2),
        #         name="Cashflow",
        #     )
        # )

        # # Update layout for titles and axis labels
        # fig.update_layout(
        #     title="Cashflow Over Time with Full-Row Category Shading",
        #     xaxis_title="Month",
        #     yaxis_title="Cashflow",
        #     showlegend=True,
        # )

        # # Render the Plotly chart in Streamlit
        # st.plotly_chart(fig)

if __name__ == "__main__":
    main()
