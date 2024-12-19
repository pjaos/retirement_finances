# Austen retirement finances
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

Tab 3
State Pension fields.

Due Date
Current date
Current amount
Estimated yearly increase

For Paul and Karen. The state pension should increase over time. The Current date and amount should track this.

Tax thresholds

Date
Amount

Tab 4
Reports

- Plot predictions over time
  Enter years into future
    Plot and save predictions
- Compare data with predictions


Store data in CSV files un ~/.config/retirement_finances
