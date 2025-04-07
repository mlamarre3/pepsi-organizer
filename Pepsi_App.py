#!/usr/bin/env python
# coding: utf-8

# In[4]:


# streamlit_app.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Pepsi Data Transformer", layout="wide")
st.title("Pepsi Forecast Transformer")
st.markdown("""
Upload the required files to generate a transformed Excel file for use in pivot tables.
""")

# File uploaders
cal_file = st.file_uploader("Upload Calendar CSV", type=["csv"])
main_file = st.file_uploader("Upload Pepsi Excel File", type=["xls", "xlsx"])
ref_file = st.file_uploader("Upload Conversion Excel File", type=["xls", "xlsx"])

if cal_file and main_file and ref_file:
    # Read uploaded files
    cal = pd.read_csv(cal_file)
    main = pd.read_excel(main_file)
    ref = pd.read_excel(ref_file)

    # Clean column names
    main.columns = main.columns.str.strip().str.replace('\xa0', '', regex=True)
    ref.columns = ref.columns.str.strip().str.replace('\xa0', '', regex=True)

    # Standardize key fields
    main['Item'] = main['Item'].astype(str).str.strip()
    ref['Pepsi Item# (RMID#)'] = ref['Pepsi Item# (RMID#)'].astype(str).str.strip()
    main['Plant Desc'] = main['Plant Desc'].astype(str).str.strip()
    ref['Pepsi Plant Desc'] = ref['Pepsi Plant Desc'].astype(str).str.strip()

    # Drop unnecessary columns
    main.drop(['Trademark','Cluster Qty','Container Size','Deposit','Wind','Design Style','Lane'], axis=1, inplace=True)

    # Merge
    merged = main.merge(ref, left_on=['Item', 'Plant Desc'], right_on=['Pepsi Item# (RMID#)', 'Pepsi Plant Desc'], how='left')
    merged.drop(['Supplier Desc','Pepsi Item Desc','Pepsi Plant Desc'], axis=1, inplace=True)

    # Melt operation
    melt = merged.melt(id_vars=[
        'Supplier','Item','SAP Item Number','Item Category', 'UOM','Plant', 'SAP Plant Number',
        'Plant Desc','QTY Open POs QTY with Supplier','Quantity Onhand','Scheduled Receipts',
        'Past Due Orders', 'Safety Stock','IM/LF', 'LF/LB','Special Record','Pepsi Item# (RMID#)',
        'Current J# w/Fcst','Berry Item Desc','Country','Item Desc'],
        var_name='Week', value_name='IM')

    # Conversion
    melt['IM'] = melt['IM'].replace(',', '', regex=True).astype(float)
    melt['LF'] = (melt['IM'] / melt['IM/LF']) / 1000
    melt['LB'] = melt['LF'] * melt['LF/LB']

    # Merge calendar
    melt['Week'] = pd.to_datetime(melt['Week'], format='%m/%d/%y', errors='coerce')
    cal['CalendarDate'] = pd.to_datetime(cal['CalendarDate'])
    final = melt.merge(cal, left_on='Week', right_on='CalendarDate', how='left')

    # Drop excess calendar columns
    dateDrop = ['DateSid', 'FiscalQuarter', 'PostingPeriod', 'CalendarDate', 'CalendarYear',
                'CalendarQuarter', 'CalendarMonth', 'CalendarWeek', 'CalendarDay',
                'CalendarWeekday', 'PostingPeriodStartDate', 'PostingPeriodEndDate', 'FiscalWeek',
                'WeekEndDatetime', 'WorkDay', 'PeriodTotalWorkDays', 'PeriodActualWorkDay',
                'PeriodTotalDays', 'WeeksinPeriod', 'WeekinPeriod', 'FiscalYearMonth',
                'FiscalYearQuarter', 'CalendarYearMonth', 'PeriodNameLong', 'CalendarWeekofMonth',
                'CalendarDayofWeek', 'FiscalDate', 'JulianDate', 'CalendarFiscalPeriod', 'SerialWeek',
                'SerialDay', 'SerialDayExcludingWeekends', 'SerialWorkingDay', 'DayofFiscalYear',
                'DayofPeriod', 'DaysInYear', 'CalendarMonthNameLong', 'CalendarMonthNameShort',
                'CalendarNameYear', 'InLastXFiscalYears', 'InLastXFiscalQuarters', 'InLastXPeriods',
                'InLastXWeeks', 'InLastXDays', 'JoinKey', 'FiscalPeriodSid', 'FiscalQuarterSid',
                'CalendarMonthSid', 'CalendarQuarterSid', 'CalendarQuarterAllSid',
                'InLastXCalendarYears', 'InLastXCalendarQuarters', 'InLastXMonths']
    final = final.drop(columns=[col for col in dateDrop if col in final.columns])

    # Output to Excel
    today = datetime.now().strftime('%Y-%m-%d')
    filename = f"Pepsi_{today}.xlsx"

    towrite = BytesIO()
    final.to_excel(towrite, index=False, engine='openpyxl')
    towrite.seek(0)

    st.success("Transformation complete! Download your file below.")
    st.download_button(label="📥 Download Transformed Excel",
                       data=towrite,
                       file_name=filename,
                       mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
else:
    st.warning("Please upload all required files.")

