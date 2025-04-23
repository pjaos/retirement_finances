# Retirement finances
I designed this tool to give me some idea if I had enough money to retire. Such tools
classically use Monte Carlo analysis to project a likelihood of success. I started
down this route but decided such an approach didn't serve my purpose.

I used spreadsheets to do some projections and these were useful but it appeared
it would be easier and more flexible to have the functionality included in a software package.

I wanted a tool that I could use to project various scenario's based on what I considered
possible parameters (E.G pension growth rates, savings interest rates etc). People with
much more knowledge of such predictions/guesses than I appear not to be able to make
remotely accurate predictions (particularly over longer timescales).
Therefore I wanted the tool to track the progression of my finances so that I can adjust
my spending as early as possible if required.

This tool must be used with care, the retirement choices you make are yours alone. You may wish to
consult a financial advisor to understand your options so that you make the best decisions
with regard to your retirement as mistakes could be very costly. The UK money and pensions
service (https://maps.org.uk/en) has useful information when considering retirement.

It is unclear to me if this tool will be useful to others given it was designed to my
requirements. It is offered as is, you can make the judgment on whether it is useful to you.


# Assumptions this tool makes
The assumptions made by this tool are shown below. These assumptions define the constraints I chose when designing this tool. They may not be directly applicable to your situation.

- Savings interest accrues daily but is added at the start of each year for the previous year.

- Pensions funds accrue (growth/drop) daily and are added daily.

- State pension changes (hopefully increases) in April for the new financial year. The first
  full month of the changed state pension will be in May.

- This tool does not take tax into account. Therefore you must be aware of the tax implications of your pension decisions.

- Money is taken from either savings or pensions to meet outgoings during retirement.

- This tool deals with draw down pensions only.

- If you die before age 75 then your personal pension (if you have one) will be available
  to your partner as a lump sum.


# Installing the software
The 'Retirement Finances' software can be installed on Linux and Windows platforms.

# Installing on Windows
Double click on the install.bat file. If python is not installed on your PC, then the first time you run this, you will be prompted to install python.

You can install python as shown below

- Open the Microsoft Store (suitcase in the Windows toolbar that has the Windows logo on the side).

- Enter [python](https://www.python.org/about/) into the 'Search apps, games, movies, and more' field at the top of the window.

- Select 'Python 3.12' option from the displayed list.

- Select the Get or Install button to install python onto your PC.

Once python is installed, double click the install.bat file again, to install the retirement finances application.

The installation may take several minutes to complete.

When complete double click on the create_launcher.bat file. This will create an icon on the desktop to allow you to launch the Retirement Finances application.

# Installing on Linux
To install onto a Linux PC ensure you have python 3.12 or greater installed. Details of how to do this can be found [here](https://docs.python-guide.org/starting/install3/linux/).
pipx must also be installed onto the Linux PC. Details of how to do this can be found [here](https://pipx.pypa.io/latest/installation/)

To install the 'Retirements Finances' application open a terminal windows in the installers folder and enter

```
pipx install retirement_finances-3.5-py3-none-any.whl
  installed package retirement-finances 3.5, installed using Python 3.12.3
  These apps are now globally available
    - retirement_finances
done! ✨ 🌟 ✨
```

# Using the software

## Overview
The software stores details of all your savings accounts and pensions. This information is only stored locally on your PC and all the files in which this information is stored are encrypted.

The capabilities are listed below.

- Enter your savings details.
- Enter your pension details.
- Enter details of your spending as time progresses.
- Make predictions of how long these will last you given details you enter.
- Check your expenditure as time progresses to see how you are doing against the above predictions.

As stated previously the predictions are based on your guesses regarding future growth of pension
funds, interest rates and spending. The first two of these are largely outside your control. Due
to the wide variations in these, this tool allows you to see as early as possible how this
is going sop that you can make changes if required.

# Starting the software

## On Windows
Type 'Retirement_Finances' into the windows search bar in the taskbar (normally at the bottom of the main windows screen) and select 'Retirement_Finances' under 'best match'. This opens a window indicating the the application ios starting up. Shortly afterwards (the time will depend how fast your PC is) A 'Retirement Finances' browser window should open asking you to enter a password.

## On Linux
Open a terminal window and enter retirement finances. After a delay a 'Retirement Finances' browser window should open asking you to enter a password.

Once started the software runs the same on Linux and Windows PC's. Therefore from here on, in this document, no distinction will be made when using
the software on different platforms.

## Entering your password
When you start the software you are asked to enter the password. This password is used to encrypt and decrypt the files in which data is stored. The first time you start the software you must setup this password. The password you enter must be

 - At least 16 characters long.
 - Include at least one uppercase character.
 - Include at least one lowercase character.
 - Include at least one numerical digit.

This password is used to encrypt all data stored.

Once entered you will be asked to enter the password again. If they match this is the password used to encrypt your data.

When you start the program a second time you will be asked to enter this password again.

```
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!! If you forget this password you will loose access to your data !!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
```

If you do forget your password you will need to delete the folder where all data is held. This folder is detailed in the blue bar at bottom of the password entry window.

## Initial Window
After entering the password a browser window is displayed with SAVINGS, PENSIONS, MONTHLY SPENDING, REPORTS and CONFIGURATION along the top.
Each of these is a separate Tab and when selected (using the mouse) the page below it will change.

## First Step
The first thing you should do is select the CONFIGURATION tab and enter your name into the 'My Name' field. If you hover the mouse over the field a tooltip message is displayed ('Enter your name here'). Tooltips are used to indicate what you should enter into fields.

If you have a partner and wish to combine finances for retirement purposes then you should enter your partners name into the field below this.

As you work out how to use the tool you may wish to, initially, enter dummy data (E.G John Doe). This can then be changed later if you wish.

Once you have entered data into this form select the SAVE button.


## SAVINGS Tab
The savings tab displays a list of your savings accounts. The ADD, DELETE and EDIT buttons allow add, delete and edit the savings accounts in this list.
Initially this list will be empty.

If you Select the ADD button you are presented with a different page. This contains the following fields.

- Active

  This should be selected if this account should be included in your retirement planning finances.

- Bank/Building Society Name

  The name of the organisation where the savings are held. This is a required field (I.E you must enter something) but again, initially, when getting used to how this program can be used you may wish to enter dummy data. You can repeat this foe all fields on all the forms presented if you wish.

- Account Name

  This field details the name of the account. This is also a required field.

- Sort code

  This is not a required field and may be left blank.

- Account Number

  This is not a required field and may be left blank.

- Owner

  You may select the owner of this account from the drop down list. This is either you or your partner.

- Interest rate

  The expected interest rate when the account was opened. This is not a required field and may be left at 0%. This value is not used in any calculations and is just for your reference.

- Fixed/Variable

  This is a dropdown list and indicates whether the interest is fixed rate or variable rate. This is not a required field and may be left at fixed. his value is not used in any calculations and is just for your reference.

- Open Date

  This should be the date when the account was opened. This is a required field as before this date the account should not have any money in it. The date format is DD-MM-YYYY.

- Notes

This is a free form text field that allows you to enter any information you wish about the savings account. This is optional and can be left blank.

- Date/Balalance Table.

  Initially this will be empty. Select the ADD button and enter a date and balance and then select the OK button to add a balance to the savings account. This value is used as part of your total savings when making predictions.


Once you have finished filling in this form select the OK button to save the savings account details.


## PENSIONS Tab
This is similar to the SAVINGS tab but allows you to add all your pensions (State and Private). The list of pensions will initially be empty. Select the ADD button to add details of a pension to the list.

In a similar fashion to the SAVINGS page you are presented with a different page. This contains the following fields.

- State Pension

  If checked then you are entering details of your expected state pension. If deselected then the page should hold details of a non state pension that you hold.

- Provider

  If the state pension field is selected then this field is fixed as GOV. If the state pension field is deselected then you may enter details of your pension provider in this field. This is not a required field.

- Description

  This allows you to enter a description of the pension if you wish. This is a required field.

- State Pension State Date

  If the state pension field is selected then you should enter the date at which your state pension is expected to start. If the state pension field is deselected then this field is greyed out. This is a required field for a state pension.

- Owner

  You may select the owner of this account from the drop down list. This is either you or your partner.

- Date/Amount table

If the state pension field is selected then you should enter your current state pension amount. This is the value that the HMRC say will be your yearly pension if you received it now.
If the state pension field is deselected then this should be the current value of your pension fund.

Select the ADD button and enter the date and the amount as detailed above.


## MONTHLY SPENDING
This table allows you to record the total amount you spend each month as time progresses. When predicting how long your savings and pensions will last thgis is used to plot over the prediction the actual amount you spent.

The table on the left details the date and the amount spent. Select the ADD button to add the date set to the 1'st of the month. The amount entered should be the total amount you spent in that month.

The Notes field is a  field to allow you to enter any information you wish about your monthly spending.


## REPORTS
This contains two buttons as detailed below.

### TOTALS
Simply gives the current total of all the latest entries in all the SAVINGS and PENSIONS amounts tables.

### DRAWDOWN RETIREMENT PREDICTION.
This is where you can check predictions and your progress against your predictions. Select this button and a new page is displayed with the following fields.

- My Date of Birth

  Enter your date of birth here.

- My max age

  This is the maximum age that you wish to plan for.

- Partner date of birth

  If you have included your partner in your finances then add their date of birth here.

- Partner max age

  This is the maximum age that you wish to plan for.

- Prediction state date

  The date you wish the prediction to start. This would typically be the date at which you wish to retire.

- Pension draw down start date

  The checkbox to the left of this field must be selected to allow you to enter this date. When entered the date defines the point at which you start regularly drawing down from your pension to fund your retirement. Before this date your savings are used to fund your retirement.

- Monthly budget/income

  This is the amount you expect to spend each month (on average) to live the life you wish to live during retirement.

- Monthly from other sources

  This is a fixed amount that you expect to receive each month from any source. This amount is deducted from the 'Monthly budget/income' to determine how much you need to take from savings or pensions each month.

- Yearly budget/income increase (%)
This is a list (comma separated) of yearly percentage increases in your 'Monthly budget/income' in order to allow you to keep pace with inflation. Each comma separated value is applied to each year from your Prediction start date. Enter your guesses here.

- Savings Interest rate (%)
This is a list (comma separated) of yearly savings rates to be applied to all your savings. Each comma separated value is applied to each year from your prediction start date. Enter your guesses here.

- Pension growth rate (%)
This is a list (comma separated) of yearly pension growth rates rates to be applied to all your pensions. Each comma separated value is applied to each year from your prediction start date. Enter your guesses here.

State pension yearly increase (%)
This is a list (comma separated) of yearly state pension increases to be applied to all state pensions (max of two, you and your partner). Each comma separated value is applied to each year from your prediction start date. Enter your guesses here.


To the right of the above fields two tables are displayed. 'Savings Withdrawals' and 'Pension Withdrawals'. These allow you to enter dates and amounts to deduct from savings or pensions. You may want to enter values here if you plan to spend a lump of savings or pensions. This could be to go on holiday from savings. Alternatively to draw down on your pensions at a level below your HMRC personal allowance so as to avoid paying tax. You may select the ADD button to add one or more deductions from either savings or pensions.


Near the bottom of the page a highlighted section allows you to save all the above parameters to different names. You may want to enter best case and worst case (probably more granular than this) scenarios to allow you to try out the effect of changing different values of, for example, savings interest rates or pension growth rates. A Default option is present and you may enter a name into the 'New name' field and select the save button to add to the pull down list. You may delete these using the DELETE button.

At the bottom of the following buttons exist.

#### SHOW PREDICTION

This will create a new page that displays plots. Four separate plots are displayed as detailed below.

Plot 1 -

A prediction of your savings and pensions value over time until the maximum of either you or your partners age. The total plot is the sum of the savings and pension values.

Plot 2 -

Your predicted Monthly budget/income, predicted total state pension (if you included yor partner this is the sum of both your state pensions) and your predicted spending.

Plot 3 -

Your predicted savings interest over time.

Plot 4 -

Your predicted savings withdrawals and your predicted pension withdrawals.


#### SHOW PROGRESS

This shows the same plots as when the SHOW PREDICTION button is selected and also plots the actual value of savings and pensions. These values come from the amounts entered over time into the savings and pensions tables. You can then compare the predicted savings and pensions values over time with the actual values.

The actual amount spent each month is also plotted (along with the average) this allows you to see how accurate your spending estimates/guesses were.

The actual value can only be plotted as time progresses and you update these tables with savings values, pension fund values and amount spent.

### Last year to plot
By default the plots continue up to max date. You can truncate this to view a shorter period of time by entering a year before the max year.

The plots allow you to zoom in on points of interest at any time but this field allows the plots to be truncated if required.