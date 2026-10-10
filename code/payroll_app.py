"""
payroll_app.py — the weekly payroll, for someone who has never opened a terminal.

Every Friday the office manager at Salt City Coffee exports the week's timesheet
from the point-of-sale system. This page turns it into a paycheck table and the
CSV the online payroll provider imports — without the manager touching pandas.

The app is mostly *assembly*: the roster is loaded from data/, the upload comes
from the page, and one call to `build_payroll` does all the work. What the page
adds is what a manager needs to trust the numbers: totals, a loud warning about
anything the pipeline could not match, the full lineage table, and the download.

Run it:  Run and Debug -> "Streamlit Run: Current File"   (see README Reference #1)
Test it: pytest tests/test_pipeline.py -k app
"""

import streamlit as st

from payroll import build_payroll, load_employees, load_timesheet, payroll_export

st.title("Salt City Coffee — Weekly Payroll")
st.write("Upload this week's timesheet CSV from the point-of-sale system.")

# roster comes from HR's file, only the timesheet gets uploaded
employees = load_employees()
uploaded = st.file_uploader("Timesheet CSV", type="csv", key="timesheet")

# nothing shows up until they pick a file
if uploaded is not None:
    timesheet = load_timesheet(uploaded)
    payroll = build_payroll(timesheet, employees)  # does all the work

    # pay period at the top
    payroll_date = payroll["payroll_date"].iloc[0]
    st.subheader(f"Pay period: {payroll_date}")

    # boolean index to split rows up, then len() to count them
    unmatched = payroll[payroll["pay_type"] == "unmatched"]
    overtime = payroll[payroll["pay_type"] == "overtime"]
    paid = payroll[payroll["pay_type"] != "unmatched"]

    # totals with .sum()
    total_hours = payroll["hours_worked"].sum()
    total_pay = payroll["gross_pay"].sum()

    # four metrics in a row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Employees paid", len(paid))
    c2.metric("Total hours", f"{total_hours:,.2f}")
    c3.metric("Total gross pay", f"${total_pay:,.2f}")
    c4.metric("Overtime weeks", len(overtime))

    # warn if anyone wasn't on the roster, otherwise show success
    if len(unmatched) > 0:
        bad_ids = ", ".join(unmatched["employee_id"])
        st.warning(f"Unmatched employee_ids (not on the roster): {bad_ids}")
    else:
        st.success("Every employee_id matched the roster.")

    # whole table, raw columns and computed ones together
    st.dataframe(payroll)

    # file for the payroll provider (unmatched rows already left out)
    export = payroll_export(payroll)
    st.download_button(
        "Download payroll CSV for the provider",
        data=export.to_csv(index=False),
        file_name=f"payroll_{payroll_date}.csv",
        mime="text/csv",
        key="download",
    )
