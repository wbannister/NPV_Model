import numpy as np
import numpy_financial as npf
from datetime import date
from typing import Optional
import calendar
from datetime import timedelta
import pandas as pd
import itertools
from pyxirr import xirr, xnpv

def calculate_irr(dates, cashflows):
    """
    Uses the pyXIRR package to calculate the IRR of a series of cashflows
    with corresponding dates."""

    return xirr(dates,cashflows)

def calculate_npv(discount_rate, dates, cashflows):
    """
    Uses the pyXIRR package to calculate the NPV of a series of cashflows with corresponding dates."""
    
    return xnpv(discount_rate, dates, cashflows)

def add_months(d, months):
    # Simple function to add months to a date
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return d.replace(year=year, month=month, day=day)

def yrs_to_review(cashflow_start, review_date):
    '''function to calculate the years to review, whereby:
    - if the cashflow start date is after the review date, it's 0
    - if the cashflow start date is before the review date, it's the time from cashflow start until the review date'''
    
    if cashflow_start > review_date:
        yrs_to_review = 0
    else:
        yrs_to_review = (review_date - cashflow_start).days / 365.25
    return yrs_to_review

def yrs_to_reversion(cashflow_start, lease_termination, initial_void, initial_rf, end_void, relet_rf):
    '''function to calculate the years to reversion, whereby:
    - if the cashflow start date is after the lease_termination date, it's the time from cashflow start until the end of the initial void+rf period
    - if the cashflow start date is before the lease_termination date, it's the time from the lease_termination date + relet void+rf period from the cashflow start date'''
    
    if cashflow_start > lease_termination:
        yrs_reversion = (add_months(cashflow_start, int(initial_void + initial_rf)) - cashflow_start).days / 365.25
    else:
        yrs_reversion = (add_months(lease_termination, int(end_void + relet_rf)) - cashflow_start).days / 365.25
    return yrs_reversion


# print(yrs_to_review(date(2024, 12, 31), date(2029, 6, 7)))


def rent_yp(discount_rate, cashflow_start, review_date, lease_termination):
    '''function to calculate the rent years purchase, i.e. the amount to multiply the current rent by to get the PV of the remaining rent roll'''
    
    discount_factor = (1+discount_rate)
    
    yrs_review = yrs_to_review(cashflow_start, review_date)
        
    # code block to calculate the remaining term of the lease
    if cashflow_start > lease_termination:
        remaining_term = 0
    else:
        remaining_term = (lease_termination - cashflow_start).days / 365.25
        
    rent_yp = (1-(discount_factor)**(-min(yrs_review, remaining_term)))/discount_rate
    
    return rent_yp

#print(rent_yp(0.0705, date(2024, 12, 31), date(2029, 6, 7), date(2034, 5, 27)))


def rent_review_yp(discount_rate, cashflow_start, lease_start, review_date, lease_termination, initial_void, initial_rf, end_void, relet_rf):
    '''function to calculate the rent review years purchase, i.e. the amount to multiply any uplift from a rent review by to get the PV of the uplift in rent expected'''
    
    discount_factor = (1+discount_rate)
    
    yrs_reversion = yrs_to_reversion(cashflow_start, lease_termination, initial_void, initial_rf, end_void, relet_rf)
    remaining_term = (lease_termination - cashflow_start).days / 365.25
    yrs_review = yrs_to_review(cashflow_start, review_date)
    
    if review_date == lease_termination:
        rr_val = 0
    else:
        rr_val = ((1 - (1/discount_factor)**(remaining_term - yrs_review)) / discount_rate) * ((1/discount_factor)**yrs_review)
        
    rr_yp = max(0, rr_val)
    
    return rr_yp

# print(rent_review_yp(0.0705, date(2024, 12, 31), date(2019, 6, 7), date(2029, 6, 7), date(2034, 5, 27), 0, 0, 0, 12))
        
        
def reversion_yp(discount_rate, cashflow_start, lease_start, review_date, lease_termination, initial_void, initial_rf, end_void, relet_rf):
    '''function to calculate the reversion years purchase, i.e. the amount to multiply the reversionary rent by to get the PV of the ERV'''

    discount_factor = (1+discount_rate)
    rent_date = add_months(lease_start, initial_rf)
    
    reversion_rent_start = add_months(lease_termination, end_void+relet_rf)
    
    yrs_reversion = yrs_to_reversion(cashflow_start, lease_termination, initial_void, initial_rf, end_void, relet_rf)
    
    void_yp_rent_start = ((1-(discount_factor) ** -((lease_termination-rent_date).days / 365.25))/discount_rate) * (1/discount_factor) ** yrs_to_review(cashflow_start, rent_date)        
    void_yp_to_expiry = (1/discount_rate) * (1/discount_factor) ** ((reversion_rent_start-cashflow_start).days / 365.25)
    
    let_rev_yp = (1/discount_rate) * ((1/discount_factor) ** yrs_reversion)
    
    if lease_start > cashflow_start:
        return void_yp_rent_start + void_yp_to_expiry
    else:
        return let_rev_yp

rentyp = rent_yp(0.0705, date(2024, 12, 31), date(2029, 6, 7), date(2034, 5, 27))
rr_yp = rent_review_yp(0.0705, date(2024, 12, 31), date(2019, 6, 7), date(2029, 6, 7), date(2034, 5, 27), 0, 0, 0, 12)
rev_yp = reversion_yp(0.0705, date(2024, 12, 31), date(2019, 6, 7), date(2029, 6, 7), date(2034, 5, 27), 0, 0, 0, 12)

def initial_yield_valuation(current_rent, net_initial_yield, purchasers_costs=0.068):
    '''function to calculate the valuation of a property based on the initial yield'''
    
    value = current_rent / net_initial_yield / (1 + purchasers_costs)
    return round(value, -4)


def valuation(current_rent, rent_yp, headline_erv, ner_discount, rent_review_yp, reversion_yp):
    
    rent_val = current_rent * rent_yp
    print(rent_val)
    net_effective_rent = headline_erv * ner_discount
    if current_rent > net_effective_rent:
        review_val = current_rent * rent_review_yp
    else:
        review_val = net_effective_rent * rent_review_yp
    
    print(review_val)
    reversion_val = headline_erv * reversion_yp
    
    print(reversion_val)
    return rent_val + review_val + reversion_val

print(valuation(220816, rentyp, 325286, 1, rr_yp, rev_yp))

### Valuation function works in this one unit example. Work needs to be done in making the calling of this function more efficient (i.e. done while inputting the rest of the stuff for the cashflow..).
### Can we make this valuation function work so that it get's applied on each cashflow month, showing value change over time. 


def create_cashflow(
    cashflow_start: date,
    cashflow_term: float,
    unit_area: float,
    lease_start: date,
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
    entry_price: float = 0.0,
    exit_price: float = 0.0,
    ):
    '''Input unit and lease details to calculate a cashflow for X inputted months,
    plus an initial entry price and a final exit price.
    
    Parameters:
        relet_rent: Optional; if not provided, defaults to None.
        review_date and lease_termination: Must be datetime.date objects.
        entry_price: Cashflow amount added at the start (a day before the first period).
        exit_price: Cashflow amount added at the end (a day after the final period).
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
            
        cashflows.append(row)
    
    # Convert the list of cashflows to a DataFrame
    cashflows_df = pd.DataFrame(cashflows)
    # Set up a month index starting at 0 for the computed cashflows
    cashflows_df['month'] = range(len(cashflows))
    
    # Calculate the total cashflow for each month
    cashflows_df['cashflow'] = cashflows_df.drop(columns=['month','category']).sum(axis=1)
    cashflows_df['period_start'] = cashflows_df['month'].apply(lambda m: add_months(cashflow_start, m))
    cashflows_df['period_end'] = cashflows_df['period_start'].apply(lambda d: d.replace(day=calendar.monthrange(d.year, d.month)[1]))
    
    # Incorporate entry_price and exit_price. Create an entry row one day before cashflow_start
    entry_row = pd.DataFrame({
        'month': [0],
        'cashflow': [-entry_price],
        'period_start': [cashflow_start - timedelta(days=1)],
        'period_end': [cashflow_start - timedelta(days=1)],
        'category': ['entry']
    })
    
    # Shift main cashflows by 1 month index so they come after the entry row
    cashflows_df['month'] = cashflows_df['month'] + 1
    
    # Create an exit row one day after the final period_end of the main cashflows
    exit_row = pd.DataFrame({
        'month': [cashflows_df['month'].max() + 1],
        'cashflow': [exit_price],
        'period_start': [cashflows_df.iloc[-1]['period_end'] + timedelta(days=1)],
        'period_end': [cashflows_df.iloc[-1]['period_end'] + timedelta(days=1)],
        'category': ['exit']
    })
    
    # Concatenate entry row, main cashflows, and exit row
    cashflows_df = pd.concat([entry_row, cashflows_df, exit_row], ignore_index=True)
    

    def compute_cashflow_line(row):
        if row['category'] == 'entry':
            return row['cashflow'] + entry_price
        elif row['category'] == 'exit':
            return row['cashflow'] - exit_price
        else:
            return row['cashflow']

    cashflows_df['cashflow_line'] = cashflows_df.apply(compute_cashflow_line, axis=1)
    # print(cashflows_df)    
    # Reorder columns if necessary
    return cashflows_df

# Test the function
if __name__ == "__main__":
    cashflow = create_cashflow(
        cashflow_start=date(2025, 1, 1),
        cashflow_term=60,
        unit_area=10000,
        lease_start=date(2020, 1, 1),
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
        vacant_sc=2,
        entry_price=1000000,
        exit_price=2000000)
    print(calculate_irr(cashflow['period_start'], cashflow['cashflow']))
    print(calculate_npv(0.1, cashflow['period_start'], cashflow['cashflow']))
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
    ax.plot(cashflow['month'], cashflow['cashflow_line'], color='black', linewidth=2, label='Cashflow')

    # Add a horizontal line at y=0 to clearly separate positive and negative cashflows
    ax.axhline(0, color='black', linewidth=1, linestyle='-')

    # Add labels and legend
    ax.set_xlabel('Month')
    ax.set_ylabel('Cashflow')
    ax.set_title('Cashflow Over Time with Full-Row Category Shading')
    ax.legend()

    # Show the plot
    plt.show()
