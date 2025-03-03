# Retirement finances
I designed this tool to see if I had enough money to retire. Such tools
classically use mote carlo analysis to project a likelyhood of success. I started
down this route but decided such an approach didn't serve my purpose , E.G a percentage
of success.

I used spreadsheets to do some projections and these were useful but it appeared
it would be easier and more flexible to have the functionality included in a SW package.

I wanted a tool that I could use to project various scenario's based on what I considered
possible parameters (E.G pension growth rates, savings interest rates etc). People with
much more knowledge of such predictions/guesses appear to have little ability to get close
and they are usually wrong (often very wrong) so I wanted the tool to track the progression
of my finances so that I can adjust my spending as early as possible so I don't get into
sticky situations.

This tool must be used with care, the choices you make are yours alone. You may wish to
consult a financial advisor to understand your options so that you make the best decisions
with regard to your retirement as mistakes could be very costly. The UK money and pensions
service (https://maps.org.uk/en) has information and I found this very useful.


# Assumptions this tool makes

- Savings interest is added at the start of each year for the previous year.
- Pensions funds grow/fall in value daily.
- State pension will change in April for the new financial year. The first full month of the changed
  state pension will be in May.
- This tool does not take your tax situation into account. You'll need to understand this to make any
  decisions with regard to your pensions.
- Generally we either take money from savings or pensions to meet our outgoings during retirement.
- This tool deals with a drawdown approach to pensions.

# Installing the software

# Installing on Windows

# Installing on Linux

# Starting the software

# On Windows

# On Linux


# Using the software








I would like a program that allows me to see how my retirement finances are going.

As a top level requirement statement

The app should allow me to enter details of all our

- Bank accounts
- Building society accounts
- Pension/s. Both state and private.

The app should allow me to update the state of each of these accounts as needed and to easily produce
plots that show projections of how long our money will last.

- A monthly amount taken out. this may change over time and the ability to plot this through changes is important.
- We may take lump sum's out on occasion and the ability to plot this through changes is important.

For each bank/building society account

- Set active/inactive
- Add date an amount in account
- checkbox to hide inactive ones.


GUI

TAB 1 - Bank/Building society accounts
Add bank/building society account should have these fields.

Bank/Building Society Name:
Name of account:
Sort code:
Account number:
Type: 1 year fixed interest, Variable interest
Initial interest rate (%):
Aniversary date:
Notes:
Checkbox to include in Net Worth - This allows accounts that may be given to children to be excluded

TAB 2
Private pensions
Add Pensions

Fields

Provider
Date
Amount
Estimated increase in % if no funds removed
Start date for drawdown inclusion in income for tax purposes

Tab 3
State Pension fields.

Due Date
Current date
Current amount
Estimated yearly increase

For Paul and Karen. The state pension should increase over time. The Current date and amount should track this.

Tab 4
Reports

- Plot predictions over time
  Enter years into future
    Plot and save predictions
- Compare data with predictions


Store data in CSV files un ~/.config/retirement_finances


Tax income thresholds

Date
Amount