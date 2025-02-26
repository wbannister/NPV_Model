import numpy as np
import numpy_financial as npf
from datetime import date
from typing import Optional
import calendar
from datetime import timedelta
import pandas as pd
import itertools

def calculate_npv_monthly(cashflows, annual_discount_rate):
    """
    Calculate the NPV of a series of monthly cashflows, given 
    an ANNUAL discount rate (as a decimal, e.g. 0.10 for 10%).
    
    cashflows: list or array of monthly CFs, 
               where cashflows[0] is Month 0, cashflows[1] is Month 1, etc.
    annual_discount_rate: decimal (e.g. 0.10 for 10%).
    
    Returns: The NPV as a float.
    """
    # Convert annual discount rate to monthly rate
    monthly_rate = (1 + annual_discount_rate) ** (1/12) - 1
    
    npv = 0.0
    for i, cf in enumerate(cashflows):
        npv += cf / ((1 + monthly_rate) ** i)
    return npv


def calculate_irr_monthly(cashflows):
    """
    Calculate the monthly IRR from a list of monthly cashflows 
    using numpy's IRR. 
    This returns the *monthly* IRR (per period = per month).
    
    If you want the annual IRR, you can convert it by:
        annual_irr = (1 + monthly_irr)**12 - 1
    """
    monthly_irr = npf.irr(cashflows)  # per-month IRR
    return monthly_irr

def add_months(d, months):
    # Simple function to add months to a date
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return d.replace(year=year, month=month, day=day)


def create_cashflow(
    cashflow_start: date,
    cashflow_term: float,
    unit_area: float,
    current_rent: float,
    review_date: date,
    lease_termination: date,
    headline_erv: float,
    ner_discount: float,
    refurb_cost: float,
    refurb_duration: float,
    void_period: float,
    rf: float,
    relet_term: float,
    exit_cap: float,
    vacant_rates_percent: float,
    rates_relief: float,
    vacant_sc: float,
    relet_rent: Optional[float] = None,
    ):
    '''Input unit and lease details to calculate a cashflow for X inputted months.
    
    Parameters:
        relet_rent: Optional; if not provided, defaults to None.
        review_date and lease_termination: Must be datetime.date objects.
    '''
    if not isinstance(review_date, date):
        raise TypeError("review_date must be a datetime.date instance")
    if not isinstance(lease_termination, date):
        raise TypeError("lease_termination must be a datetime.date instance")
    
    cashflows = []
    # Define the distinct categories you want cashflow series for
    categories = [
        "contracted_rent",
        "reviewed_rent",
        "refurbishment_period",
        "void_period",
        "rf_period",
        "relet_rent"
    ]
    # Calculate relet_date as lease_termination plus refurb_duration and void_period (in months)
    relet_months = int(refurb_duration + void_period)
    relet_date = add_months(lease_termination, relet_months)
    print(relet_date)

    # Monthly refurb cost per month (as a negative cashflow)
    monthly_refurb_cost = -(refurb_cost * unit_area) / refurb_duration

    for i in range(int(cashflow_term)):
        # Initialize a row with zero for each category
        row = {cat: 0.0 for cat in categories}

        period_start = add_months(cashflow_start, i)
        period_end = add_months(cashflow_start, i + 1)
        days_in_period = (period_end - period_start).days

        rent_amount = 0.0
        category = None

        # Rental income from current rent until lease termination
        if period_start < lease_termination:
            # current_rent is annual; convert to monthly
            monthly_rent = current_rent / 12
            rent_amount = monthly_rent
            category = "contracted_rent"
            if review_date < lease_termination and period_start >= review_date and ((headline_erv * unit_area) * ner_discount) > current_rent:
                reviewed_monthly_rent = ((headline_erv * unit_area) * ner_discount) / 12
                rent_amount = reviewed_monthly_rent
                category = "reviewed_rent"

        refurb_cost_amount = 0.0
        refurb_end = add_months(lease_termination, int(refurb_duration))
        # Refurbishment costs apply for the refurb period (starting at lease_termination)
        if lease_termination <= period_start < refurb_end:
            refurb_cost_amount = monthly_refurb_cost
            category = "refurbishment_period"

        void_end = add_months(refurb_end, int(void_period))
        # Void period after refurbishment and before relet
        if refurb_end <= period_start < void_end:
            category = "void_period"
            # Calculate vacant service charge
            vacant_sc_amount = -(unit_area * vacant_sc / 12)
            rent_amount = vacant_sc_amount

            # Calculate vacant rates if beyond rates relief period
            void_month = (period_start - refurb_end).days // 30 + 1
            if void_month > rates_relief:
                vacant_rates_amount = -(vacant_rates_percent * (headline_erv * unit_area) / 12)
                rent_amount = vacant_sc_amount + vacant_rates_amount

        rf_end = add_months(void_end, int(rf))
        annual_new_rent = relet_rent if relet_rent is not None else headline_erv * unit_area
        monthly_new_rent = annual_new_rent / 12
        if void_end <= period_start < rf_end:
            rent_amount = -monthly_new_rent
            category = "rf_period"
        elif period_start >= relet_date:
            rent_amount = monthly_new_rent
            category = "relet_rent"

        # Assign the computed cashflow to the corresponding category series
        if category:
            row[category] = rent_amount + refurb_cost_amount
            row["category"] = category

        # If rf_period is less than 0, update the relet_rent value in that row to be the inverse of the rf_period value
        if row.get("rf_period", 0) < 0:
            row["relet_rent"] = -row["rf_period"]
            

        # print(row)
        cashflows.append(row)
    
    # Convert the list of cashflows to a DataFrame
    cashflows_df = pd.DataFrame(cashflows)
    cashflows_df['month'] = range(len(cashflows))
    
    # Calculate the total cashflow for each month
    cashflows_df['cashflow'] = cashflows_df.drop(columns=['month','category']).sum(axis=1)
    cashflows_df['period_start'] = cashflows_df['month'].apply(lambda m: add_months(cashflow_start, m))
    cashflows_df['period_end'] = cashflows_df['period_start'].apply(lambda d: d.replace(day=calendar.monthrange(d.year, d.month)[1]))

    # print(cashflows_df)
    return cashflows_df

# Test the function
if __name__ == "__main__":
    cashflow = create_cashflow(
        cashflow_start=date(2025, 1, 1),
        cashflow_term=60,
        unit_area=10000,
        current_rent=50000,
        review_date=date(2025, 6, 30),
        lease_termination=date(2025, 12, 31),
        headline_erv=20,
        ner_discount=0.50,
        refurb_cost=20,
        refurb_duration=3,
        void_period=12,
        rf=3,
        relet_term=6,
        exit_cap=0.06,
        vacant_rates_percent=0.5,
        rates_relief=3,
        vacant_sc=2)
    import matplotlib.pyplot as plt

    # Plot the cashflows
    fig, ax = plt.subplots(figsize=(10, 6))

    # Define colors for each category
    colors = {
        "contracted_rent": "green",
        "reviewed_rent": "lightgreen",
        "refurbishment_period": "orange",
        "void_period": "red",
        "rf_period": "yellow",
        "relet_rent": "blue"
    }

    # Plot background shading as full rectangles for each contiguous period in each category.
    for category, color in colors.items():
        cat_months = cashflow[cashflow['category'] == category]['month'].tolist()
        if not cat_months:
            continue

        # Identify contiguous segments
        segs = []
        for k, g in itertools.groupby(enumerate(cat_months), key=lambda ix: ix[1] - ix[0]):
            group = list(g)
            start = group[0][1]
            end = group[-1][1]  # end month of the segment
            segs.append((start, end))

        # Only add label on the first segment for legend clarity
        first = True
        for start, end in segs:
            # Extend the shading to the full chart height (from bottom to top).
            # end+1 used to cover the full month span.
            if first:
                ax.axvspan(start, end + 1, facecolor=color, alpha=0.3, label=category)
                first = False
            else:
                ax.axvspan(start, end + 1, facecolor=color, alpha=0.3)

    # Plot the cashflow line over the shaded backgrounds
    ax.plot(cashflow['month'], cashflow['cashflow'], color='black', linewidth=2, label='Cashflow')

    # Add a horizontal line at y=0 to clearly separate positive and negative cashflows
    ax.axhline(0, color='black', linewidth=1, linestyle='-')

    # Add labels and legend
    ax.set_xlabel('Month')
    ax.set_ylabel('Cashflow')
    ax.set_title('Cashflow Over Time with Full-Row Category Shading')
    ax.legend()

    # Show the plot
    plt.show()
