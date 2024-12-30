#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import json
import copy

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from p3lib.uio import UIO
from p3lib.helper import logTraceBack
from p3lib.pconfig import DotConfigManager

from nicegui import ui

import plotly.graph_objects as go

class Config(object):
    """@brief Responsible for loading and saving the app config."""
    BANK_ACCOUNTS_FILE = "bank_accounts.json"
    PENSIONS_FILE = "private_pensions.json"
    FUTURE_PLOT_ATTR_FILE = "future_plot_attr.json"

    @staticmethod
    def GetConfigFolder():
        """@return The folder where config files are stored."""
        cfg_filename = DotConfigManager.GetConfigFile(DotConfigManager.GetDefaultConfigFilename())
        cfg_folder = cfg_filename.replace(".cfg", "")
        if not os.path.isdir(cfg_folder):
            os.makedirs(cfg_folder)
        return cfg_folder

    @staticmethod
    def GetBankAccountListFile():
        """@return The file used to store bank account details."""
        config_path = Config.GetConfigFolder()
        return os.path.join(config_path, Config.BANK_ACCOUNTS_FILE)

    @staticmethod
    def GetPensionsListFile():
        """@return The file used to store pension details."""
        config_path = Config.GetConfigFolder()
        return os.path.join(config_path, Config.PENSIONS_FILE)

    def GetFuturePlotAttrFile():
        """@return The file used to store pension details."""
        config_path = Config.GetConfigFolder()
        return os.path.join(config_path, Config.FUTURE_PLOT_ATTR_FILE)

    def __init__(self):
        self._config_folder = Config.GetConfigFolder()
        # Notify user of config location on startup
        ui.notify(f"Config folder: {self._config_folder}")
        self._bank_accounts_file = Config.GetBankAccountListFile()
        self._load_bank_accounts()
        self._pensions_file = Config.GetPensionsListFile()
        self._load_pensions()
        self._future_plot_file = Config.GetFuturePlotAttrFile()
        self._load_future_plot_attrs()

    # --- methods for bank accounts ---

    def _load_bank_accounts(self):
        """@brief Load bank accounts from file."""
        self._bank_accounts_dict_list = []
        try:
            data = None
            with open(self._bank_accounts_file, 'r') as fd:
                data = fd.read()

            if data:
                self._bank_accounts_dict_list = json.loads(data)

        except:
            ui.notify(f'{self._bank_accounts_file} file not found.', type='negative')

    def save_bank_accounts(self):
        """@brief Save the bank accounts dict list persistently."""
        with open(self._bank_accounts_file, 'w') as fd:
            json.dump(self._bank_accounts_dict_list, fd, indent=4)
        ui.notify(f"Saved {self._bank_accounts_file}")

    def add_bank_account(self, bank_account_dict):
        """@brief Add bank account.
           @param bank_account_dict A bank account dict."""
        self._bank_accounts_dict_list.append(bank_account_dict)
        self.save_bank_accounts()

    def get_bank_accounts_dict_list(self):
        """@brief Get the current list of bank accounts."""
        return self._bank_accounts_dict_list

    def remove_bank_account(self, index):
        """@brief Remove a bank account from the list of bank accounts.
           @param index The 0 based index of the bank account to remove from the bank accounts list."""
        if index >= 0 and index < len(self._bank_accounts_dict_list):
            del self._bank_accounts_dict_list[index]
        self.save_bank_accounts()

    # --- methods for pensions ---

    def _load_pensions(self):
        """@brief Load pensions from file."""
        self._pension_dict_list = []
        try:
            data = None
            with open(self._pensions_file, 'r') as fd:
                data = fd.read()

            if data:
                self._pension_dict_list = json.loads(data)

        except:
            ui.notify(f'{self._pensions_file} file not found.', type='negative')

    def save_pensions(self):
        """@brief Save the pension dict list persistently."""
        with open(self._pensions_file, 'w') as fd:
            json.dump(self._pension_dict_list, fd, indent=4)
        ui.notify(f"Saved {self._pensions_file}")

    def add_pension(self, pension_dict):
        """@brief Add pension.bank account.
           @param pension_dict A pension dict."""
        self._pension_dict_list.append(pension_dict)
        self.save_pensions()

    def get_pension_dict_list(self):
        """@brief Get the current list of pensions."""
        return self._pension_dict_list

    def remove_pension(self, index):
        """@brief Remove a pension from the list of pensions.
           @param index The 0 based index of the pension to remove from the pension list."""
        if index >= 0 and index < len(self._pension_dict_list):
            del self._pension_dict_list[index]
        self.save_pensions()


    # --- methods for future plot parameters ---

    def _load_future_plot_attrs(self):
        """@brief Load future plot parameters from file."""
        self._future_plot_attr_dict = {}
        try:
            data = None
            with open(self._future_plot_file, 'r') as fd:
                data = fd.read()

            if data:
                self._future_plot_attr_dict = json.loads(data)

        except:
            ui.notify(f'{self._future_plot_file} file not found.', type='negative')

    def save_future_plot_attrs(self):
        """@brief Save the future plot parameters persistently."""
        with open(self._future_plot_file, 'w') as fd:
            json.dump(self._future_plot_attr_dict, fd, indent=4)
        ui.notify(f"Saved {self._future_plot_file}")

    def get_future_plot_attrs_dict(self):
        """@brief Get the the future plot parameters dict."""
        return self._future_plot_attr_dict


class GUIBase(object):
    DATE = "Date"

    @staticmethod
    def GetInputDateField(label):
        """@brief Add a control to allow the user to enter the date as an DD:MM:YYYY.
           @param label The label for the field.
           @return The input field containing the DD:MM:YYYY entered."""
        with ui.input(label) as date:
            with ui.menu().props('no-parent-event') as menu:
                with ui.date(mask='DD-MM-YYYY').bind_value(date):
                    with ui.row().classes('justify-end'):
                        ui.button('Close', on_click=menu.close).props('flat')
            with date.add_slot('append'):
                ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')
        date.tooltip("DD-MM-YYYY")
        return date


    def __init__(self):
        """@brief Constructor"""
        pass


class Finances(GUIBase):

    GUI_TIMER_SECONDS = 0.1
    YES = "Yes"
    NO = "No"

    def __init__(self):
        super().__init__()
        self._config = Config()
        self._last_selected_bank_account_index = None
        self._last_selected_pension_index = None

    def initGUI(self,
                uio,
                debugEnabled,
                reload=True,
                address='127.0.0.1',
                port=9090):
        self._uio = uio
        self._address = address
        self._port = port
        self._reload = reload

        self._init_dialogs()

        tabNameList = ('Savings',
                       'Pensions',
                       'Reports',
                       'Configuration')
        # This must have the same number of elements as the above list
        tabMethodInitList = [self._init_bank_accounts_tab,
                             self._init_pensions_tab,
                             self._init_reports_tab,
                             self._init_configuration_tab]

        tabObjList = []
        with ui.row():
            with ui.tabs().classes('w-full') as tabs:
                for tabName in tabNameList:
                    tabObj = ui.tab(tabName)
                    tabObjList.append(tabObj)

            with ui.tab_panels(tabs, value=tabObjList[0]).classes('w-full'):
                for tabObj in tabObjList:
                    with ui.tab_panel(tabObj):
                        tabIndex = tabObjList.index(tabObj)
                        tabMethodInitList[tabIndex]()

        self._guiLogLevel = "warning"
        if debugEnabled:
            self._guiLogLevel = "debug"

        ui.timer(interval=Finances.GUI_TIMER_SECONDS, callback=self.gui_timer_callback)
        ui.run(host=address,
               port=port,
               title="Austen Retirement Finances",
               dark=True,
               uvicorn_logging_level=self._guiLogLevel,
               reload=reload)

    def gui_timer_callback(self):
        """@brief Called periodically to update the GUI."""
        pass

    def _init_dialogs(self):
        """@brief Create the dialogs used by the app."""
        self._init_dialog2()
        self._init_dialog3()

    # methods associated with bank/building society accounts

    def _init_bank_accounts_tab(self):
        """@brief Create the bank accounts tab."""

        with ui.row():
            columns = [{'name': BankAccountGUI.ACCOUNT_OWNER, 'label': BankAccountGUI.ACCOUNT_OWNER, 'field': BankAccountGUI.ACCOUNT_OWNER},
                       {'name': BankAccountGUI.BANK, 'label': BankAccountGUI.BANK, 'field': BankAccountGUI.BANK},
                       {'name': BankAccountGUI.ACCOUNT_NAME_LABEL, 'label': BankAccountGUI.ACCOUNT_NAME_LABEL, 'field': BankAccountGUI.ACCOUNT_NAME_LABEL},
                      ]
            self._bank_acount_table = ui.table(columns=columns,
                                               rows=[],
                                               row_key=BankAccountGUI.ACCOUNT_NAME_LABEL,
                                               selection='single').style('text-align: left;')
            #.classes('h-96').props('virtual-scroll')
            self._show_bank_account_list()

        with ui.row():
            ui.button('Add', on_click=lambda: self._add_bank_account() ).tooltip('Add a bank/building society account')
            ui.button('Delete', on_click=lambda: self._delete_bank_account() ).tooltip('Delete a bank/building society account')
            ui.button('Edit', on_click=lambda: self._edit_bank_account() ).tooltip('Edit a bank/building society account')
            ui.button('Update', on_click=lambda: self._show_bank_account_list() ).tooltip('Update the list bank/building society accounts')

    def _init_dialog2(self):
        """@brief Create a dialog presented to the user to check that they wish to delete a bank account."""
        with ui.dialog() as self._dialog2, ui.card().style('width: 400px;'):
            ui.label("Are you sure you wish to delete the selected bank account.")
            with ui.row():
                ui.button("Yes", on_click=self._dialog2_yes_button_press)
                ui.button("No", on_click=self._dialog2_no_button_press)

    def _show_dialog2(self):
        """@brief Show dialog presented to the user to check that they wish to delete a bank account."""
        self._dialog2.open()

    def _dialog2_yes_button_press(self):
        """@brief Called when dialog 2 yes button is selected."""
        self._dialog2.close()
        self._config.remove_bank_account(self._last_selected_bank_account_index)
        self._show_bank_account_list()

    def _dialog2_no_button_press(self):
        """@brief Called when dialog 2 no button is selected."""
        self._dialog2.close()

    def _show_bank_account_list(self):
        """@brief Show a table of the configured bank accounts."""
        self._bank_acount_table.rows.clear()
        self._bank_acount_table.update()
        bank_accounts_dict_list = self._config.get_bank_accounts_dict_list()
        for bank_account_dict in bank_accounts_dict_list:
            owner = bank_account_dict[BankAccountGUI.ACCOUNT_OWNER]
            bank = bank_account_dict[BankAccountGUI.ACCOUNT_BANK_NAME_LABEL]
            account_name = bank_account_dict[BankAccountGUI.ACCOUNT_NAME_LABEL]
            self._bank_acount_table.add_row({BankAccountGUI.ACCOUNT_OWNER:owner, BankAccountGUI.BANK:bank, BankAccountGUI.ACCOUNT_NAME_LABEL: account_name})
        self._bank_acount_table.run_method('scrollTo', len(self._bank_acount_table.rows)-1)

    def _delete_bank_account(self):
        """@brief Delete the selected bank account."""
        self._last_selected_bank_account_index = self._get_selected_bank_account_index()
        if self._last_selected_bank_account_index < 0:
            ui.notify("Select a bank account to delete.")
        else:
            self._show_dialog2()

    def _get_selected_bank_account_index(self):
        selected_index = -1
        selected_dict = self._bank_acount_table.selected
        if len(selected_dict) > 0:
            selected_dict=selected_dict[0]
            if selected_dict:
                bank_name = selected_dict[BankAccountGUI.BANK]
                account_name = selected_dict[BankAccountGUI.ACCOUNT_NAME_LABEL]
                index = 0
                found = False
                for bank_account_dict in self._config.get_bank_accounts_dict_list():
                    _bank = bank_account_dict[BankAccountGUI.ACCOUNT_BANK_NAME_LABEL]
                    _account_name = bank_account_dict[BankAccountGUI.ACCOUNT_NAME_LABEL]
                    if _bank == bank_name and \
                        _account_name == account_name:
                        found = True
                        break
                    index = index + 1
                if found:
                    selected_index = index
        return selected_index

    def _get_selected_bank_account_dict(self):
        """@brief Get the selected bank account dict.
           @return The selected bank account dict or None if no bank account is selected."""
        bank_account_dict = None
        self._last_selected_bank_account_index = self._get_selected_bank_account_index()
        if self._last_selected_bank_account_index >= 0:
            bank_account_dict_list = self._config.get_bank_accounts_dict_list()
            bank_account_dict = bank_account_dict_list[self._last_selected_bank_account_index]
        return bank_account_dict

    def _add_bank_account(self):
        """@brief Add a bank account."""
        self._update_bank_account(True, {})

    def _edit_bank_account(self):
        """@brief Add a bank account."""
        bank_account_dict = self._get_selected_bank_account_dict()
        if bank_account_dict:
            self._update_bank_account(False, bank_account_dict)
        else:
            ui.notify("Select a bank account to edit.")

    def _update_bank_account(self, add, bank_account_dict):
        """@brief edit bank account details.
           @param add If True then add to the list of available bank accounts.
           @param bank_account_dict A dict holding the bank account details."""
        if isinstance(bank_account_dict, dict):
            # Define a secondary page
            @ui.page('/bank_accounts_page')
            def bank_accounts_page():
                BankAccountGUI(add, bank_account_dict, self._config)
            # This will open the new page in the same browser window
            ui.run_javascript("window.open('/bank_accounts_page', '_parent')")

        else:
            ui.notify("Select a bank account to view.")


    # methods associated with pensions

    def _init_pensions_tab(self):
        """@brief Create the bank accounts tab."""

        with ui.row():
            columns = [{'name': PensionGUI.PENSION_PROVIDER_LABEL, 'label': PensionGUI.PENSION_PROVIDER_LABEL, 'field': PensionGUI.PENSION_PROVIDER_LABEL},
                       {'name': PensionGUI.PENSION_DESCRIPTION_LABEL, 'label': PensionGUI.PENSION_DESCRIPTION_LABEL, 'field': PensionGUI.PENSION_DESCRIPTION_LABEL},
                       {'name': PensionGUI.PENSION_OWNER_LABEL, 'label': PensionGUI.PENSION_OWNER_LABEL, 'field': PensionGUI.PENSION_OWNER_LABEL},
                      ]
            self._pension_table = ui.table(columns=columns,
                                               rows=[],
                                               row_key='Description',
                                               selection='single').classes('h-96').props('virtual-scroll')
            self._show_pension_list()

        with ui.row():
            ui.button('Add', on_click=lambda: self._add_pension() ).tooltip('Add a pension')
            ui.button('Delete', on_click=lambda: self._delete_pension() ).tooltip('Delete a pension')
            ui.button('Edit', on_click=lambda: self._edit_pension() ).tooltip('Edit a pension')
            ui.button('Update', on_click=lambda: self._show_pension_list() ).tooltip('Update the list pensions')

    def _init_dialog3(self):
        """@brief Create a dialog presented to the user to check that they wish to delete a pension."""
        with ui.dialog() as self._dialog3, ui.card().style('width: 400px;'):
            ui.label("Are you sure you wish to delete the selected pension.")
            with ui.row():
                ui.button("Yes", on_click=self._dialog3_yes_button_press)
                ui.button("No", on_click=self._dialog3_no_button_press)

    def _show_dialog3(self):
        """@brief Show dialog presented to the user to check that they wish to delete a pension."""
        self._dialog3.open()

    def _dialog3_yes_button_press(self):
        """@brief Called when dialog 3 yes button is selected."""
        self._dialog3.close()
        self._config.remove_pension(self._last_selected_pension_index)
        self._show_pension_list()

    def _dialog3_no_button_press(self):
        """@brief Called when dialog 3 no button is selected."""
        self._dialog3.close()

    def _show_pension_list(self):
        """@brief Show a table of the configured pensions."""
        self._pension_table.rows.clear()
        self._pension_table.update()
        pension_dict_list = self._config.get_pension_dict_list()
        for pension_dict in pension_dict_list:
            provider = pension_dict[PensionGUI.PENSION_PROVIDER_LABEL]
            description = pension_dict[PensionGUI.PENSION_DESCRIPTION_LABEL]
            owner = pension_dict[PensionGUI.PENSION_OWNER_LABEL]
            self._pension_table.add_row({PensionGUI.PENSION_PROVIDER_LABEL:provider,
                                         PensionGUI.PENSION_DESCRIPTION_LABEL:description,
                                         PensionGUI.PENSION_OWNER_LABEL: owner})
        self._pension_table.run_method('scrollTo', len(self._bank_acount_table.rows)-1)

    def _delete_pension(self):
        """@brief Delete the pension."""
        self._last_selected_pension_index = self._get_selected_pension_index()
        if self._last_selected_pension_index < 0:
            ui.notify("Select a pension to delete.")
        else:
            self._show_dialog3()

    def _get_selected_pension_index(self):
        selected_index = -1
        selected_dict = self._pension_table.selected
        if len(selected_dict) > 0:
            selected_dict=selected_dict[0]
            if selected_dict:
                provider = selected_dict['Provider']
                description = selected_dict['Description']
                index = 0
                found = False
                for pension_dict in self._config.get_pension_dict_list():
                    _provider = pension_dict[PensionGUI.PENSION_PROVIDER_LABEL]
                    _description = pension_dict[PensionGUI.PENSION_DESCRIPTION_LABEL]
                    if _provider == provider and \
                        _description == description:
                        found = True
                        break
                    index = index + 1
                if found:
                    selected_index = index
        return selected_index

    def _get_selected_pension_dict(self):
        """@brief Get the selected pension dict.
           @return The selected pension dict or None if no pension is selected."""
        pension_dict = None
        self._last_selected_pension_index = self._get_selected_pension_index()
        if self._last_selected_pension_index >= 0:
            pension_dict_list = self._config.get_pension_dict_list()
            pension_dict = pension_dict_list[self._last_selected_pension_index]
        return pension_dict

    def _add_pension(self):
        """@brief Add a bank account."""
        self._update_pension(True, {})

    def _edit_pension(self):
        """@brief Add a pension."""
        pension_dict = self._get_selected_pension_dict()
        if pension_dict:
            self._update_pension(False, pension_dict)
        else:
            ui.notify("Select a pension to edit")

    def _update_pension(self, add, pension_dict):
        """@brief edit pension details.
           @param add If True then add to the list of available pensions.
           @param pension_dict A dict holding the pension details."""
        if isinstance(pension_dict, dict):
            # Define a secondary page
            @ui.page('/pensions_page')
            def pensions_page():
                PensionGUI(add, pension_dict, self._config)
            # This will open the new page in the same browser window
            ui.run_javascript("window.open('/pensions_page', '_parent')")

        else:
            ui.notify("Select a bank account to view.")



    def _init_table_dialog(self, table):
        with ui.dialog() as self._table_dialog, ui.card():
            columns = []
            index = 0
            for _ in table:
                row = {'name': f'c{index}', 'label': '', 'field': f'c{index}'}
                columns.append(row)
                index = index + 1
            self._table_dialog_table = ui.table(columns=columns, rows=[])

            for row in table:
                row_dict = {}
                column_index = 0
                for value in row:
                    key = f'c{column_index}'
                    row_dict[key]=value
                    column_index = column_index + 1
                self._table_dialog_table.add_row(row_dict)

            with ui.row():
                ui.button('OK', on_click=self._table_dialog_ok_button_selected)

    def _table_dialog_ok_button_selected(self):
        self._table_dialog.close()

    def _init_reports_tab(self):
        with ui.row():
            ui.button('Totals', on_click=lambda: self._show_totals() ).tooltip('Show total savings and pensions.')
            ui.button('Future Plot', on_click=lambda: self._future_plot() ).tooltip('Show net worth over time.')



    def _show_totals(self):
        """@brief Show details of the total savings and pensions."""
        bank_accounts_dict_list = self._config.get_bank_accounts_dict_list()
        pension_dict_list = self._config.get_pension_dict_list()

        savings_total = 0.0
        for bank_accounts_dict in bank_accounts_dict_list:
            account_name = bank_accounts_dict[BankAccountGUI.ACCOUNT_NAME_LABEL]
            active = bank_accounts_dict[BankAccountGUI.ACCOUNT_ACTIVE]
            # Only include active accounts.
            if active:
                last_row = bank_accounts_dict[BankAccountGUI.TABLE][-1]
                amount = float(last_row[1])
                savings_total = savings_total + amount

        pension_total = 0.0
        for pension_dict in pension_dict_list:
            if not pension_dict[PensionGUI.STATE_PENSION]:
                last_row = pension_dict[PensionGUI.PENSION_TABLE][-1]
                pension_total += float(last_row[1])

        total = pension_total + savings_total

        table = [['Savings',  f'£{savings_total:0.2f}'],
                 ['Pensions', f'£{pension_total:0.2f}'],
                 ['Total',    f'£{total:0.2f}'],
                ]
        self._init_table_dialog(table)
        self._table_dialog.open()
        # Plot this over time

    def _future_plot(self):
        """@brief Plot our financial future based on given parameters."""
        # Define a secondary page
        @ui.page('/future_plot_page')
        def future_plot_page():
            FuturePlotGUI(self._config)
        # This will open in a separate browser window
        ui.run_javascript("window.open('/future_plot_page', '_blank')")

    def _init_configuration_tab(self):
        pass


class BankAccountGUI(GUIBase):
    """@brief Responsible for allowing the user to add details of a bank/building society account or any other institution holding savings accounts"""

    ACCOUNT_ACTIVE = "Active"
    ACCOUNT_BANK_NAME_LABEL = "Bank/Building Society Name"
    ACCOUNT_NAME_LABEL = "Account Name"
    ACCOUNT_SORT_CODE = "Sort Code"
    ACCOUNT_NUMBER = "Account Number"
    ACCOUNT_OWNER = "Owner"
    ACCOUNT_INTEREST_RATE = "Interest Rate (%)"
    ACCOUNT_INTEREST_RATE_TYPE = "Interest Type"
    ACCOUNT_OPEN_DATE = "Open Date (DD-MM-YYYY)"
    ACCOUNT_NOTES = "Notes"
    TABLE = "table"
    BALANCE = 'Balance (£)'
    BANK = 'Bank'

    def __init__(self, add, bank_account_dict, config):
        """@brief Constructor.
           @param add If True then add to the list of available bank accounts.
           @param bank_account_dict A dict holding the bank account details.
           @param config A Config instance."""
        self._add = add
        self._bank_account_dict = self._ensure_default_bank_account_keys(bank_account_dict)
        self._config = config
        self._selected_row_index = -1
        self._init_page()
        self._init_add_row_dialog()
        self._update_gui_from_bank_account()

    def _ensure_default_bank_account_keys(self, bank_account_dict):
        """@brief Ensure the bank account dict has the required keys."""
        if BankAccountGUI.ACCOUNT_ACTIVE not in bank_account_dict:
            bank_account_dict[BankAccountGUI.ACCOUNT_ACTIVE] = True

        if BankAccountGUI.ACCOUNT_BANK_NAME_LABEL not in bank_account_dict:
            bank_account_dict[BankAccountGUI.ACCOUNT_BANK_NAME_LABEL] = ""

        if BankAccountGUI.ACCOUNT_NAME_LABEL not in bank_account_dict:
            bank_account_dict[BankAccountGUI.ACCOUNT_NAME_LABEL] = ""

        if BankAccountGUI.ACCOUNT_SORT_CODE not in bank_account_dict:
            bank_account_dict[BankAccountGUI.ACCOUNT_SORT_CODE] = ""

        if BankAccountGUI.ACCOUNT_NUMBER not in bank_account_dict:
            bank_account_dict[BankAccountGUI.ACCOUNT_NUMBER] = ""

        if BankAccountGUI.ACCOUNT_OWNER not in bank_account_dict:
            bank_account_dict[BankAccountGUI.ACCOUNT_OWNER] = ""

        if BankAccountGUI.ACCOUNT_INTEREST_RATE not in bank_account_dict:
            bank_account_dict[BankAccountGUI.ACCOUNT_INTEREST_RATE] = 0.0

        if BankAccountGUI.ACCOUNT_INTEREST_RATE_TYPE not in bank_account_dict:
            bank_account_dict[BankAccountGUI.ACCOUNT_INTEREST_RATE_TYPE] = "Fixed"

        if BankAccountGUI.ACCOUNT_OPEN_DATE not in bank_account_dict:
            bank_account_dict[BankAccountGUI.ACCOUNT_OPEN_DATE] = ""

        if BankAccountGUI.ACCOUNT_NOTES not in bank_account_dict:
            bank_account_dict[BankAccountGUI.ACCOUNT_NOTES] = ""

        if BankAccountGUI.TABLE not in bank_account_dict:
            bank_account_dict[BankAccountGUI.TABLE] = []

        return bank_account_dict

    def _init_page(self):
        ui.label("Savings Account").style('font-size: 32px; font-weight: bold;')
        with ui.row():
            bank_active_checkbox = ui.checkbox(BankAccountGUI.ACCOUNT_ACTIVE, value=True)

        with ui.row():
            bank_account_bank_name_field = ui.input(label=BankAccountGUI.ACCOUNT_BANK_NAME_LABEL).style('width: 300px;')
            bank_account_name_field = ui.input(label=BankAccountGUI.ACCOUNT_NAME_LABEL).style('width: 300px;')
            bank_account_sort_code_field = ui.input(label=BankAccountGUI.ACCOUNT_SORT_CODE).style('width: 100px;')
            bank_account_number_field = ui.input(label=BankAccountGUI.ACCOUNT_NUMBER).style('width: 200px;')

        with ui.row():
            bank_account_owner_field = ui.input(label=BankAccountGUI.ACCOUNT_OWNER).style('width: 300px;')
            bank_account_interest_rate_field = ui.number(label=BankAccountGUI.ACCOUNT_INTEREST_RATE, min=0, max=100).style('width: 150px;')
            bank_account_interest_type_field = ui.select(['Fixed', 'Variable'], value='Fixed')
            bank_account_interest_type_field.tooltip(BankAccountGUI.ACCOUNT_INTEREST_RATE_TYPE)
            bank_account_open_date_field = Finances.GetInputDateField(BankAccountGUI.ACCOUNT_OPEN_DATE)

        with ui.row():
            bank_notes_field = ui.textarea(label=BankAccountGUI.ACCOUNT_NOTES).style('width: 800px;')

        with ui.scroll_area():
            self._table = self._get_table_copy()
            with ui.row():
                columns = [{'name': BankAccountGUI.DATE, 'label': BankAccountGUI.DATE, 'field': BankAccountGUI.DATE},
                           {'name': BankAccountGUI.BALANCE, 'label': BankAccountGUI.BALANCE, 'field': BankAccountGUI.BALANCE},
                          ]
                self._bank_acount_table = ui.table(columns=columns,
                                                   rows=[],
                                                   row_key=BankAccountGUI.DATE,
                                                   selection='single')

                self._display_table_rows()


        with ui.row():
            ui.button("Back", on_click=lambda: ui.navigate.back())
            ui.button("Add", on_click=self._add_button_handler).tooltip('Add a row to the balance table.')
            ui.button("Delete", on_click=self._delete_button_handler).tooltip('Delete a row from the balance table.')
            if self._add:
                tooltip_msg = 'Add a new bank/building society account and save it.'
            else:
                tooltip_msg = 'Save the modified bank/building society account.'
            ui.button("Save", on_click=self._save_button_handler).tooltip(tooltip_msg)

        self._bank_account_field_list = [bank_account_bank_name_field,
                                            bank_account_name_field,
                                            bank_account_sort_code_field,
                                            bank_account_number_field,
                                            bank_account_owner_field,
                                            bank_account_open_date_field,
                                            bank_account_interest_rate_field,
                                            bank_account_interest_type_field,
                                            bank_active_checkbox,
                                            bank_notes_field]
    def _get_table_copy(self):
        """@brief Get a copy of the table from the dict that holds the balance table."""
        table = []
        if BankAccountGUI.TABLE in self._bank_account_dict:
            table = self._bank_account_dict[BankAccountGUI.TABLE]
        else:
            # If not present add an empty table to the dict
            self._bank_account_dict[BankAccountGUI.TABLE] = table
        # Return a copy of the table
        return copy.deepcopy(table)

    def _add_table_row(self, row):
        self._bank_account_dict[BankAccountGUI.TABLE].append(row)

    def _init_add_row_dialog(self):
        """@brief Create a dialog presented to the user to check that they wish to add a bank account."""
        with ui.dialog() as self._add_row_dialog, ui.card().style('width: 400px;'):
            self._date_input_field = GUIBase.GetInputDateField(BankAccountGUI.DATE)
            self._amount_field = ui.input(label="Balance (£)")
            with ui.row():
                ui.button("Ok", on_click=self._add_row_dialog_ok_button_press)
                ui.button("Cancel", on_click=self._add_row_dialog_cancel_button_press)

    def _add_row_dialog_ok_button_press(self):
        self._add_row_dialog.close()
        row = (self._date_input_field.value, self._amount_field.value)
        self._add_table_row(row)
        self._display_table_rows()

    def _display_table_rows(self):
        """@brief Show a table of the configured bank accounts."""
        self._bank_acount_table.rows.clear()
        self._bank_acount_table.update()
        table = self._bank_account_dict[BankAccountGUI.TABLE]
        for row in table:
            self._bank_acount_table.add_row({BankAccountGUI.DATE: row[0], BankAccountGUI.BALANCE: row[1]})
        self._bank_acount_table.run_method('scrollTo', len(self._bank_acount_table.rows)-1)

    def _add_row_dialog_cancel_button_press(self):
        self._add_row_dialog.close()

    def _save_button_handler(self):
        """@brief Handle save button selection events."""
        self._update_bank_account_from_gui()

    def _add_button_handler(self):
        """@brief Handle add button selection events."""
        self._add_row_dialog.open()

    def _delete_button_handler(self):
        """@brief Handle delete button selection events."""
        selected_dict = self._bank_acount_table.selected
        if selected_dict and BankAccountGUI.DATE in selected_dict[0]:
            del_date = selected_dict[0][BankAccountGUI.DATE]
            table = self._bank_account_dict[BankAccountGUI.TABLE]
            new_table = []
            for row in table:
                date = row[0]
                if date != del_date:
                    new_table.append(row)
            self._bank_account_dict[BankAccountGUI.TABLE] = new_table
        self._display_table_rows()
        self._config.save_bank_accounts()

    def _update_gui_from_bank_account(self):
        """@brief Update the contents of fields from the bank account entered."""
        for input_field in self._bank_account_field_list:
            if isinstance(input_field, ui.number):
                input_field.value = self._bank_account_dict[BankAccountGUI.ACCOUNT_INTEREST_RATE]

            elif isinstance(input_field, ui.select):
                input_field.value = self._bank_account_dict[BankAccountGUI.ACCOUNT_INTEREST_RATE_TYPE]

            elif isinstance(input_field, ui.checkbox):
                input_field.value = self._bank_account_dict[BankAccountGUI.ACCOUNT_ACTIVE]

            else:
                props = input_field._props
                key = props['label']
                input_field.value = self._bank_account_dict[key]

    def _update_bank_account_from_gui(self):
        """@brief Update the bank account dict. from the GUI fields."""
        # Do some checks on the values entered.
        if len(self._bank_account_field_list[0].value ) == 0:
            ui.notify("Bank/Building society name must be entered.")

        elif len(self._bank_account_field_list[1].value ) == 0:
            ui.notify("Account name must be entered.")

        else:
            # The table rows were updated previously
            self._bank_account_dict[BankAccountGUI.ACCOUNT_BANK_NAME_LABEL] = self._bank_account_field_list[0].value
            self._bank_account_dict[BankAccountGUI.ACCOUNT_NAME_LABEL] = self._bank_account_field_list[1].value
            self._bank_account_dict[BankAccountGUI.ACCOUNT_SORT_CODE] = self._bank_account_field_list[2].value
            self._bank_account_dict[BankAccountGUI.ACCOUNT_NUMBER] = self._bank_account_field_list[3].value
            self._bank_account_dict[BankAccountGUI.ACCOUNT_OWNER] = self._bank_account_field_list[4].value
            self._bank_account_dict[BankAccountGUI.ACCOUNT_OPEN_DATE] = self._bank_account_field_list[5].value
            self._bank_account_dict[BankAccountGUI.ACCOUNT_INTEREST_RATE] = self._bank_account_field_list[6].value
            self._bank_account_dict[BankAccountGUI.ACCOUNT_INTEREST_RATE_TYPE] = self._bank_account_field_list[7].value
            self._bank_account_dict[BankAccountGUI.ACCOUNT_ACTIVE] = self._bank_account_field_list[8].value
            self._bank_account_dict[BankAccountGUI.ACCOUNT_NOTES] = self._bank_account_field_list[9].value

            if self._add:
                self._config.add_bank_account(self._bank_account_dict)

            # If editing an account then the bank_account_dict has been modified and we just need to save it.
            self._config.save_bank_accounts()


class PensionGUI(GUIBase):
    """@brief Responsible for allowing the user to add details of a bank account."""
    GOV = "GOV"
    AMOUNT = "Amount (£)"
    PENSION_PROVIDER_LABEL = "Provider"
    PENSION_DESCRIPTION_LABEL = "Description"
    STATE_PENSION = "State Pension"
    PENSION_OWNER_LABEL = "Owner"
    STATE_PENSION_START_DATE = "State Pension Start Date"
    PENSION_TABLE = "table"

    def __init__(self, add, pension_dict, config):
        """@brief Constructor.
           @param add If True then add to the list of available bank accounts.
           @param pension_dict A dict holding the pension details.
           @param config A Config instance."""
        self._add = add
        self._pension_dict = self._ensure_default_pension_keys(pension_dict)
        self._config = config
        self._init_add_row_dialog()
        self._init_page()

    def _ensure_default_pension_keys(self, pension_dict):
        """@brief Ensure the pension dict has the required keys."""
        if PensionGUI.STATE_PENSION not in pension_dict:
            pension_dict[PensionGUI.STATE_PENSION] = True

        if PensionGUI.PENSION_PROVIDER_LABEL not in pension_dict:
            pension_dict[PensionGUI.PENSION_PROVIDER_LABEL] = PensionGUI.GOV

        if PensionGUI.PENSION_DESCRIPTION_LABEL not in pension_dict:
            pension_dict[PensionGUI.PENSION_DESCRIPTION_LABEL] = PensionGUI.STATE_PENSION

        if PensionGUI.PENSION_OWNER_LABEL not in pension_dict:
            pension_dict[PensionGUI.PENSION_OWNER_LABEL] = ""

        if PensionGUI.STATE_PENSION_START_DATE not in pension_dict:
            pension_dict[PensionGUI.STATE_PENSION_START_DATE] = ""

        if PensionGUI.PENSION_TABLE not in pension_dict:
            pension_dict[PensionGUI.PENSION_TABLE] = []

        return pension_dict

    def _init_page(self):
        ui.label("Pension").style('font-size: 32px; font-weight: bold;')
        self._state_pension_checkbox = ui.checkbox(PensionGUI.STATE_PENSION, value=True).on('click', self._state_pension_checkbox_callback)
        self._provider_field = ui.input(label=PensionGUI.PENSION_PROVIDER_LABEL, value=PensionGUI.GOV)
        self._description_field = ui.input(label=PensionGUI.PENSION_DESCRIPTION_LABEL, value=PensionGUI.STATE_PENSION)
        self._state_pension_state_date_field = GUIBase.GetInputDateField(PensionGUI.STATE_PENSION_START_DATE)
        self._pension_owner_field = ui.input(label=PensionGUI.PENSION_OWNER_LABEL)

        with ui.scroll_area():
            self._table = self._get_table_copy()
            with ui.row():
                columns = [{'name': PensionGUI.DATE, 'label': PensionGUI.DATE, 'field': PensionGUI.DATE},
                          {'name': PensionGUI.AMOUNT, 'label': PensionGUI.AMOUNT, 'field': PensionGUI.AMOUNT},
                          ]
                self._pension_table = ui.table(columns=columns,
                                                   rows=[],
                                                   row_key=PensionGUI.DATE,
                                                   selection='single')

        self._update_gui_from_pension()

        with ui.row():
            ui.button("Back", on_click=lambda: ui.navigate.back())
            ui.button("Add", on_click=self._add_button_handler).tooltip('Add a row to the pension table.')
            ui.button("Delete", on_click=self._delete_button_handler).tooltip('Delete a row from the pension table.')
            if self._add:
                tooltip_msg = 'Add a new pension account and save it.'
            else:
                tooltip_msg = 'Save the modified pension.'
            ui.button("Save", on_click=self._save_button_handler).tooltip(tooltip_msg)

    def _get_table_copy(self):
        """@brief Get a copy of the table from the dict that holds the pension table."""
        table = []
        if PensionGUI.PENSION_TABLE in self._pension_dict:
            table = self._pension_dict[PensionGUI.PENSION_TABLE]
        else:
            # If not present add an empty table to the dict
            self._pension_dict[PensionGUI.PENSION_TABLE] = table
        # Return a copy of the table
        return copy.deepcopy(table)

    def _state_pension_checkbox_callback(self):
        #Ensure state pension field/s are enabled if checkbox is selected
        if self._state_pension_checkbox:
            if self._state_pension_checkbox.value:
                self._provider_field.value = PensionGUI.GOV
                self._state_pension_state_date_field.enabled = True
                self._provider_field.enabled = False

            else:
                self._state_pension_state_date_field.value = ""
                self._state_pension_state_date_field.enabled = False
                self._provider_field.enabled = True

    def _display_table_rows(self):
        """@brief Show a table of the configured bank accounts."""
        self._pension_table.rows.clear()
        self._pension_table.update()
        table = self._pension_dict[PensionGUI.PENSION_TABLE]
        for row in table:
            self._pension_table.add_row({PensionGUI.DATE: row[0], PensionGUI.AMOUNT: row[1]})
        self._pension_table.run_method('scrollTo', len(self._pension_table.rows)-1)

    def _init_add_row_dialog(self):
        """@brief Create a dialog presented to the user to check that they wish to add a pension value."""
        with ui.dialog() as self._add_row_dialog, ui.card().style('width: 400px;'):
            self._date_input_field = GUIBase.GetInputDateField(PensionGUI.DATE)
            self._amount_field = ui.input(label=PensionGUI.AMOUNT)
            with ui.row():
                ui.button("Ok", on_click=self._add_row_dialog_ok_button_press)
                ui.button("Cancel", on_click=self._add_row_dialog_cancel_button_press)

    def _add_button_handler(self):
        self._add_row_dialog.open()

    def _delete_button_handler(self):
        selected_dict = self._pension_table.selected
        if selected_dict and PensionGUI.DATE in selected_dict[0]:
            del_date = selected_dict[0][PensionGUI.DATE]
            table = self._pension_dict[PensionGUI.PENSION_TABLE]
            new_table = []
            for row in table:
                date = row[0]
                if date != del_date:
                    new_table.append(row)
            self._pension_dict[PensionGUI.PENSION_TABLE] = new_table
        self._display_table_rows()
        self._config.save_pensions()

    def _save_button_handler(self):
        self._update_pension_from_gui()

    def _add_table_row(self, row):
        if PensionGUI.PENSION_TABLE not in self._pension_dict:
            self._pension_dict[PensionGUI.PENSION_TABLE] = []
        self._pension_dict[PensionGUI.PENSION_TABLE].append(row)

    def _add_row_dialog_ok_button_press(self):
        self._add_row_dialog.close()
        row = (self._date_input_field.value, self._amount_field.value)
        self._add_table_row(row)
        self._display_table_rows()

    def _add_row_dialog_cancel_button_press(self):
        self._add_row_dialog.close()

    def _update_gui_from_pension(self):
        """@brief Update the contents of fields from the pension entered."""
        self._state_pension_checkbox.value = self._pension_dict[PensionGUI.STATE_PENSION]
        self._provider_field.value = self._pension_dict[PensionGUI.PENSION_PROVIDER_LABEL]
        self._description_field.value = self._pension_dict[PensionGUI.PENSION_DESCRIPTION_LABEL]
        self._pension_owner_field.value = self._pension_dict[PensionGUI.PENSION_OWNER_LABEL]
        self._state_pension_state_date_field.value = self._pension_dict[PensionGUI.STATE_PENSION_START_DATE]
        self._state_pension_checkbox_callback()
        self._display_table_rows()

    def _update_pension_from_gui(self):
        """@brief Update the pension dict from the GUI fields."""

        self._pension_dict[PensionGUI.STATE_PENSION] = self._state_pension_checkbox.value
        self._pension_dict[PensionGUI.PENSION_OWNER_LABEL] = self._pension_owner_field.value
        self._pension_dict[PensionGUI.STATE_PENSION_START_DATE] = self._state_pension_state_date_field.value
        self._pension_dict[PensionGUI.PENSION_PROVIDER_LABEL] = self._provider_field.value
        self._pension_dict[PensionGUI.PENSION_DESCRIPTION_LABEL] = self._description_field.value

        if self._add:
            self._config.add_pension(self._pension_dict)

        self._state_pension_checkbox_callback()

        self._config.save_pensions()


class FuturePlotGUI(GUIBase):
    """@brief Responsible for allowing the user to plot predictions about the way the savings and pensions will fare during retirement."""
    DEFAULT_MALE_MAX_AGE = 90
    DEFAULT_MONTHLY_INCOME = 2850                     # The  initial monthly budget @ Dec 2024 including sarah pays towards household bills
    DEFAULT_MONTHLY_AMOUNT_FROM_SARAH = 250           # The amount sarah pays towards household bills @ Dec 2024
    DEFAULT_RATE_LIST = "4, 3.5, 3.2, 3, 3, 3, 3"     # Default list of savings interest rates and pension growth rates.
    DEFAULT_YEARLY_INCREASE_IN_INCOME = "2.5, 2.5, 2.5, 2.5, 2.5, 2.5"
    DEFAULT_STATE_PENSION_YEARLY_INCREASE = DEFAULT_YEARLY_INCREASE_IN_INCOME
    PAUL_MAX_AGE = "Paul max age"
    PAUL_DATE_OF_BIRTH = "Paul date of birth"
    KAREN_MAX_AGE = "Karen max age"
    KAREN_DATE_OF_BIRTH = "Karen date of birth"
    SAVINGS_INTEREST_RATE_LIST = "Predicted savings interest rate list (%)"
    PENSION_GROWTH_RATE_LIST = "Predicted pension growth rate list (%)"
    STATE_PENSION_YEARLY_INCREASE_LIST = "Predicted state pension yearly increase (%)"
    MONTHLY_AMOUNT_FROM_SARAH = "Monthly from Sarah (£)"
    MONTHLY_INCOME = "Monthly budget/income (£)"
    YEARLY_INCREASE_IN_INCOME = "Yearly budget/income increase (%)"
    REPORT_START_DATE = "Plot start date"
    PENSION_DRAWDOWN_START_DATE = "Pension drawdown start date"

    DATE = BankAccountGUI.DATE
    AMOUNT = "Amount"

    SAVINGS_WITHDRAWAL_TABLE = "Savings withdrawal table"
    PENSION_WITHDRAWAL_TABLE = "Pensions withdrawal table"
    ADD_SAVINGS_WITHDRAWAL_BUTTON = "Add savings withdrawal"
    DEL_SAVINGS_WITHDRAWAL_BUTTON = "Delete savings withdrawal"
    ADD_PENSION_WITHDRAWAL_BUTTON = "Add pension withdrawal"
    DEL_PENSION_WITHDRAWAL_BUTTON = "Delete pension withdrawal"

    @staticmethod
    def GetDateTimeList(start_datetime, stop_datetime):
        """@brief Get a list of datetime instances (by month) starting from the start of the current month
                  for every month up to and including the stop_datetime.
           @param start_datetime The start datetime for the first datetime instance.
           @param stop_datetime The datetime instance for the last datetime."""
        current_date = start_datetime
        current_date = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        date_list = []
        while current_date <= stop_datetime:
            date_list.append(current_date)
            current_date += relativedelta(months=+1)
        return date_list

    @staticmethod
    def Datetime2String(_datetime):
        return _datetime.strftime("%Y-%m-%d %H:%M:%S")

    def __init__(self, config):
        self._config = config
        self._last_pp_year = None
        self._future_plot_attr_dict = self._ensure_keys_present()
        self._init_gui()
        self._init_add_row_dialog()

    def _ensure_keys_present(self):
        """@brief Ensure the required keys are present in the config dict that relate to the future plot attrs."""
        future_plot_attr_dict = self._config.get_future_plot_attrs_dict()

        if FuturePlotGUI.PAUL_DATE_OF_BIRTH not in future_plot_attr_dict:
            future_plot_attr_dict[FuturePlotGUI.PAUL_DATE_OF_BIRTH] = ""

        if FuturePlotGUI.PAUL_MAX_AGE not in future_plot_attr_dict:
            future_plot_attr_dict[FuturePlotGUI.PAUL_MAX_AGE] = FuturePlotGUI.DEFAULT_MALE_MAX_AGE

        if FuturePlotGUI.KAREN_DATE_OF_BIRTH not in future_plot_attr_dict:
            future_plot_attr_dict[FuturePlotGUI.KAREN_DATE_OF_BIRTH] = ""

        if FuturePlotGUI.KAREN_MAX_AGE not in future_plot_attr_dict:
            future_plot_attr_dict[FuturePlotGUI.KAREN_MAX_AGE] = FuturePlotGUI.DEFAULT_MALE_MAX_AGE + 4

        if FuturePlotGUI.SAVINGS_INTEREST_RATE_LIST not in future_plot_attr_dict:
            future_plot_attr_dict[FuturePlotGUI.SAVINGS_INTEREST_RATE_LIST] = FuturePlotGUI.DEFAULT_RATE_LIST

        if FuturePlotGUI.PENSION_GROWTH_RATE_LIST not in future_plot_attr_dict:
            future_plot_attr_dict[FuturePlotGUI.PENSION_GROWTH_RATE_LIST] = FuturePlotGUI.DEFAULT_RATE_LIST

        if FuturePlotGUI.MONTHLY_AMOUNT_FROM_SARAH not in future_plot_attr_dict:
            future_plot_attr_dict[FuturePlotGUI.MONTHLY_AMOUNT_FROM_SARAH] = FuturePlotGUI.DEFAULT_MONTHLY_AMOUNT_FROM_SARAH

        if FuturePlotGUI.MONTHLY_INCOME not in future_plot_attr_dict:
            future_plot_attr_dict[FuturePlotGUI.MONTHLY_INCOME] = FuturePlotGUI.DEFAULT_MONTHLY_INCOME

        if FuturePlotGUI.YEARLY_INCREASE_IN_INCOME not in future_plot_attr_dict:
            future_plot_attr_dict[FuturePlotGUI.YEARLY_INCREASE_IN_INCOME] = FuturePlotGUI.DEFAULT_YEARLY_INCREASE_IN_INCOME

        if FuturePlotGUI.STATE_PENSION_YEARLY_INCREASE_LIST not in future_plot_attr_dict:
            future_plot_attr_dict[FuturePlotGUI.STATE_PENSION_YEARLY_INCREASE_LIST] = FuturePlotGUI.DEFAULT_STATE_PENSION_YEARLY_INCREASE

        if FuturePlotGUI.REPORT_START_DATE not in future_plot_attr_dict:
            future_plot_attr_dict[FuturePlotGUI.REPORT_START_DATE] = ""

        if FuturePlotGUI.PENSION_DRAWDOWN_START_DATE not in future_plot_attr_dict:
            future_plot_attr_dict[FuturePlotGUI.PENSION_DRAWDOWN_START_DATE] = ""

        if FuturePlotGUI.SAVINGS_WITHDRAWAL_TABLE not in future_plot_attr_dict:
            future_plot_attr_dict[FuturePlotGUI.SAVINGS_WITHDRAWAL_TABLE] = []

        if FuturePlotGUI.PENSION_WITHDRAWAL_TABLE not in future_plot_attr_dict:
            future_plot_attr_dict[FuturePlotGUI.PENSION_WITHDRAWAL_TABLE] = []

        return future_plot_attr_dict

    def _init_gui(self):
        with ui.row():
            ui.label("Future Plot").style('font-size: 32px; font-weight: bold;')
        with ui.row():
            ui.label("The following parameters can be adjusted when generating a future plot.")

        with ui.row():
            self._start_date_field = GUIBase.GetInputDateField(FuturePlotGUI.REPORT_START_DATE).tooltip('The first date to be plotted.')

        with ui.row():
            self._paul_dob_field = GUIBase.GetInputDateField(FuturePlotGUI.PAUL_DATE_OF_BIRTH)
            paul_dob = self._future_plot_attr_dict[FuturePlotGUI.PAUL_DATE_OF_BIRTH]
            self._paul_dob_field.value = paul_dob
            paul_max_age = self._future_plot_attr_dict[FuturePlotGUI.PAUL_MAX_AGE]
            self._paul_max_age_field = ui.number(label=FuturePlotGUI.PAUL_MAX_AGE, value=paul_max_age)

            self._karen_dob_field = GUIBase.GetInputDateField(FuturePlotGUI.KAREN_DATE_OF_BIRTH)
            karen_dob = self._future_plot_attr_dict[FuturePlotGUI.KAREN_DATE_OF_BIRTH]
            self._karen_dob_field.value = karen_dob
            karen_max_age = self._future_plot_attr_dict[FuturePlotGUI.KAREN_MAX_AGE]
            self._karen_max_age_field = ui.number(label=FuturePlotGUI.KAREN_MAX_AGE, value=karen_max_age)

        with ui.row():
            monthly_amount_from_sarah = self._future_plot_attr_dict[FuturePlotGUI.MONTHLY_AMOUNT_FROM_SARAH]
            self._monthly_amount_from_sarah_field = ui.number(label=FuturePlotGUI.MONTHLY_AMOUNT_FROM_SARAH, value=monthly_amount_from_sarah).tooltip('Sarah gives us this amount each month for food etc.')

            monthly_income = self._future_plot_attr_dict[FuturePlotGUI.MONTHLY_INCOME]
            self._monthly_income_field = ui.number(label=FuturePlotGUI.MONTHLY_INCOME, value=monthly_income).tooltip('The total amount we use each month including the money from Sarah.')

            yearly_increase_in_income = self._future_plot_attr_dict[FuturePlotGUI.YEARLY_INCREASE_IN_INCOME]
            self._yearly_increase_in_income_field = ui.input(label=FuturePlotGUI.YEARLY_INCREASE_IN_INCOME, value=yearly_increase_in_income).style('width: 450px;').tooltip('A comma separated list of the predicted increase in yearly income as a %.')

        with ui.row():
            savings_interest_rate_list = self._future_plot_attr_dict[FuturePlotGUI.SAVINGS_INTEREST_RATE_LIST]
            self._savings_interest_rates_field = ui.input(label=FuturePlotGUI.SAVINGS_INTEREST_RATE_LIST, value=savings_interest_rate_list).style('width: 250px;').tooltip('A comma separated list of savings interest rate (%) predictions for this year, next year and so on.')
            pension_growth_rate_list = self._future_plot_attr_dict[FuturePlotGUI.PENSION_GROWTH_RATE_LIST]
            self._pension_growth_rate_list_field = ui.input(label=FuturePlotGUI.PENSION_GROWTH_RATE_LIST, value=pension_growth_rate_list).style('width: 250px;').tooltip('A comma separated list of the predicted yearly non state pension growth rate (%).')
            state_pension_growth_rate_list = self._future_plot_attr_dict[FuturePlotGUI.STATE_PENSION_YEARLY_INCREASE_LIST]
            self._state_pension_growth_rate_list_field = ui.input(label=FuturePlotGUI.STATE_PENSION_YEARLY_INCREASE_LIST, value=state_pension_growth_rate_list).style('width: 250px;').tooltip('A comma separated list of the predicted yearly state pension increase (%).')

        with ui.row():
            self._pension_drawdown_start_date_field = GUIBase.GetInputDateField(FuturePlotGUI.PENSION_DRAWDOWN_START_DATE).tooltip('The date at which we stop drawing out of savings and draw out of our pension to cover monthly income.')

        with ui.row():
            columns = [{'name': FuturePlotGUI.DATE, 'label': FuturePlotGUI.DATE, 'field': FuturePlotGUI.DATE},
                       {'name': FuturePlotGUI.AMOUNT, 'label': FuturePlotGUI.AMOUNT, 'field': FuturePlotGUI.AMOUNT},
                      ]
            with ui.column():
                ui.label("Savings withdrawals").style('font-weight: bold;')
                self._savings_withdrawals_table = ui.table(columns=columns,
                                        rows=[],
                                        row_key=BankAccountGUI.DATE,
                                        selection='single')
                with ui.row():
                    ui.button('Add', on_click=lambda: self._add_savings_withdrawal() ).tooltip('Add to the savings withdrawals table.')
                    ui.button('Delete', on_click=lambda: self._del_savings_withdrawal() ).tooltip('Delete a savings withdrawal from the table.')

            with ui.column():
                ui.label("Pension withdrawals").style('font-weight: bold;')
                self._pension_withdrawals_table = ui.table(columns=columns,
                                        rows=[],
                                        row_key=BankAccountGUI.DATE,
                                        selection='single')
                with ui.row():
                    ui.button('Add', on_click=lambda: self._add_pension_withdrawal() ).tooltip('Add to the pension withdrawals table.')
                    ui.button('Delete', on_click=lambda: self._del_pension_withdrawal() ).tooltip('Delete a pension withdrawal from the table.')

            self._update_gui_tables()

        with ui.row():
            ui.button('Calculate', on_click=lambda: self._calc() ).tooltip('Perform calculation and plot the results.')
            ui.button('Save', on_click=lambda: self._save() ).tooltip('Save the above report parameters.')
        self._load()

    def _init_add_row_dialog(self):
        """@brief Create a dialog presented to the user to add a withdrawal from the savings or pension tables."""
        with ui.dialog() as self._add_row_dialog, ui.card().style('width: 400px;'):
            self._date_input_field = GUIBase.GetInputDateField(FuturePlotGUI.DATE)
            self._amount_field = ui.input(label=FuturePlotGUI.AMOUNT)
            with ui.row():
                ui.button("Ok", on_click=self._add_row_dialog_ok_button_press)
                ui.button("Cancel", on_click=self._add_row_dialog_cancel_button_press)

    def _update_gui_tables(self):
        self._display_table_rows(self._savings_withdrawals_table, self._get_savings_withdrawal_table_data())
        self._display_table_rows(self._pension_withdrawals_table, self._get_pension_withdrawal_table_data())

    def _get_savings_withdrawal_table_data(self):
        """@brief Get a table of the savings withdrawals."""
        return self._future_plot_attr_dict[FuturePlotGUI.SAVINGS_WITHDRAWAL_TABLE]
        # PJA IS the deepcopy NEEDED
#        copy.deepcopy(self._future_plot_attr_dict[FuturePlotGUI.SAVINGS_WITHDRAWAL_TABLE].split(','))

    def _get_pension_withdrawal_table_data(self):
        """@brief Get a table of the pension withdrawals."""
        return self._future_plot_attr_dict[FuturePlotGUI.PENSION_WITHDRAWAL_TABLE]
        # PJA IS the deepcopy NEEDED
#        copy.deepcopy(self._future_plot_attr_dict[FuturePlotGUI.PENSION_WITHDRAWAL_TABLE].split(','))

    def _display_table_rows(self, gui_table, table_data):
        """@brief Show a table of the configured bank accounts.
           @param gui_table The GUI table element.
           @param table_data The table date. Each row has two elements (DATE and AMOUNT)."""
        gui_table.rows.clear()
        gui_table.update()
        for row in table_data:
            gui_table.add_row({FuturePlotGUI.DATE: row[0], FuturePlotGUI.AMOUNT: row[1]})
        gui_table.run_method('scrollTo', len(gui_table.rows)-1)

    def _add_savings_withdrawal(self):
        """@brief Called when the add a savings withdrawal button is selected."""
        self._button_selected = FuturePlotGUI.ADD_SAVINGS_WITHDRAWAL_BUTTON
        self._add_row_dialog.open()

    def _del_savings_withdrawal(self):
        """@brief Called when the delete a savings withdrawal button is selected."""
        selected_dict = self._savings_withdrawals_table.selected
        if selected_dict and FuturePlotGUI.DATE in selected_dict[0]:
            del_date = selected_dict[0][FuturePlotGUI.DATE]
            table = self._future_plot_attr_dict[FuturePlotGUI.SAVINGS_WITHDRAWAL_TABLE]
            new_table = []
            for row in table:
                date = row[0]
                if date != del_date:
                    new_table.append(row)
            self._future_plot_attr_dict[FuturePlotGUI.SAVINGS_WITHDRAWAL_TABLE] = new_table
        self._update_gui_tables()

    def _add_pension_withdrawal(self):
        """@brief Called when the add a savings withdrawal button is selected."""
        self._button_selected = FuturePlotGUI.ADD_PENSION_WITHDRAWAL_BUTTON
        self._add_row_dialog.open()

    def _del_pension_withdrawal(self):
        """@brief Called when the delete a pension withdrawal button is selected."""
        selected_dict = self._pension_withdrawals_table.selected
        if selected_dict and FuturePlotGUI.DATE in selected_dict[0]:
            del_date = selected_dict[0][FuturePlotGUI.DATE]
            table = self._future_plot_attr_dict[FuturePlotGUI.PENSION_WITHDRAWAL_TABLE]
            new_table = []
            for row in table:
                date = row[0]
                if date != del_date:
                    new_table.append(row)
            self._future_plot_attr_dict[FuturePlotGUI.PENSION_WITHDRAWAL_TABLE] = new_table
        self._update_gui_tables()

    def _add_row_dialog_ok_button_press(self):
        self._add_row_dialog.close()
        row = (self._date_input_field.value, self._amount_field.value)
        if self._button_selected == FuturePlotGUI.ADD_SAVINGS_WITHDRAWAL_BUTTON:
            self._future_plot_attr_dict[FuturePlotGUI.SAVINGS_WITHDRAWAL_TABLE].append(row)

        elif self._button_selected == FuturePlotGUI.ADD_PENSION_WITHDRAWAL_BUTTON:
            self._future_plot_attr_dict[FuturePlotGUI.PENSION_WITHDRAWAL_TABLE].append(row)

        else:
            raise Exception("BUG: Neither the add savings or add pensions button was selected.")
        self._update_gui_tables()

    def _add_row_dialog_cancel_button_press(self):
        self._add_row_dialog.close()

    def _get_max_date(self):
        """@brief Get the maximum date we need to plan for.
           @return a datetime instance of the max year."""
        self._update_dict_from_gui()
        paul_dab_str = self._future_plot_attr_dict[FuturePlotGUI.PAUL_DATE_OF_BIRTH]
        paul_dob = datetime.strptime(paul_dab_str, '%d-%m-%Y')
        paul_max_age = int(self._future_plot_attr_dict[FuturePlotGUI.PAUL_MAX_AGE])
        paul_max_date = paul_dob + relativedelta(years=paul_max_age)

        karen_dab_str = self._future_plot_attr_dict[FuturePlotGUI.KAREN_DATE_OF_BIRTH]
        karen_dob = datetime.strptime(karen_dab_str, '%d-%m-%Y')
        karen_max_age = int(self._future_plot_attr_dict[FuturePlotGUI.KAREN_MAX_AGE])
        karen_max_date = karen_dob + relativedelta(years=karen_max_age)
        max_date = paul_max_date
        if karen_max_date > paul_max_date:
            max_date = karen_max_date
        return max_date

    def _update_dict_from_gui(self):
        """@brief update the dict from the details entered into the GUI."""
        self._future_plot_attr_dict[FuturePlotGUI.PAUL_DATE_OF_BIRTH] = self._paul_dob_field.value
        self._future_plot_attr_dict[FuturePlotGUI.PAUL_MAX_AGE] = self._paul_max_age_field.value
        self._future_plot_attr_dict[FuturePlotGUI.KAREN_DATE_OF_BIRTH] = self._karen_dob_field.value
        self._future_plot_attr_dict[FuturePlotGUI.KAREN_MAX_AGE] = self._karen_max_age_field.value
        self._future_plot_attr_dict[FuturePlotGUI.SAVINGS_INTEREST_RATE_LIST] = self._savings_interest_rates_field.value
        self._future_plot_attr_dict[FuturePlotGUI.PENSION_GROWTH_RATE_LIST] = self._pension_growth_rate_list_field.value
        self._future_plot_attr_dict[FuturePlotGUI.STATE_PENSION_YEARLY_INCREASE_LIST] = self._state_pension_growth_rate_list_field.value
        self._future_plot_attr_dict[FuturePlotGUI.MONTHLY_AMOUNT_FROM_SARAH] = self._monthly_amount_from_sarah_field.value
        self._future_plot_attr_dict[FuturePlotGUI.MONTHLY_INCOME] = self._monthly_income_field.value
        self._future_plot_attr_dict[FuturePlotGUI.YEARLY_INCREASE_IN_INCOME] = self._yearly_increase_in_income_field.value
        # PJA add error if either start date is before 21/12/2024
        self._future_plot_attr_dict[FuturePlotGUI.REPORT_START_DATE] = self._start_date_field.value
        self._future_plot_attr_dict[FuturePlotGUI.PENSION_DRAWDOWN_START_DATE] = self._pension_drawdown_start_date_field.value

    def _save(self):
        """@save the report parameters to persistent storage."""
        self._update_dict_from_gui()
        # PJA add check that each rate list contains at least on number

        # If editing an account then the bank_account_dict has been modified and we just need to save it.
        self._config.save_future_plot_attrs()

    def _load(self):
        """@brief Load config from persistent storage and display in GUI."""
        self._future_plot_attr_dict = self._config.get_future_plot_attrs_dict()
        self._paul_dob_field.value = self._future_plot_attr_dict.get(FuturePlotGUI.PAUL_DATE_OF_BIRTH, "")
        self._paul_max_age_field.value = self._future_plot_attr_dict.get(FuturePlotGUI.PAUL_MAX_AGE, FuturePlotGUI.DEFAULT_MALE_MAX_AGE)
        self._karen_dob_field.value = self._future_plot_attr_dict.get(FuturePlotGUI.KAREN_DATE_OF_BIRTH, "")
        self._karen_max_age_field.value = self._future_plot_attr_dict.get(FuturePlotGUI.KAREN_MAX_AGE, FuturePlotGUI.DEFAULT_MALE_MAX_AGE + 4)
        self._savings_interest_rates_field.value = self._future_plot_attr_dict.get(FuturePlotGUI.SAVINGS_INTEREST_RATE_LIST, FuturePlotGUI.DEFAULT_RATE_LIST)
        self._pension_growth_rate_list_field.value = self._future_plot_attr_dict.get(FuturePlotGUI.PENSION_GROWTH_RATE_LIST, FuturePlotGUI.DEFAULT_RATE_LIST)
        self._state_pension_growth_rate_list_field.value = self._future_plot_attr_dict.get(FuturePlotGUI.STATE_PENSION_YEARLY_INCREASE_LIST, FuturePlotGUI.DEFAULT_STATE_PENSION_YEARLY_INCREASE)
        self._monthly_amount_from_sarah_field.value = self._future_plot_attr_dict.get(FuturePlotGUI.MONTHLY_AMOUNT_FROM_SARAH, FuturePlotGUI.DEFAULT_MONTHLY_AMOUNT_FROM_SARAH)
        self._monthly_income_field.value = self._future_plot_attr_dict.get(FuturePlotGUI.MONTHLY_INCOME, FuturePlotGUI.DEFAULT_MONTHLY_INCOME)
        self._yearly_increase_in_income_field.value = self._future_plot_attr_dict.get(FuturePlotGUI.YEARLY_INCREASE_IN_INCOME, FuturePlotGUI.DEFAULT_YEARLY_INCREASE_IN_INCOME)
        self._start_date_field.value = self._future_plot_attr_dict[FuturePlotGUI.REPORT_START_DATE]
        self._pension_drawdown_start_date_field.value = self._future_plot_attr_dict[FuturePlotGUI.PENSION_DRAWDOWN_START_DATE]

    def _convert_table(self, date_value_table):
        """@brief Convert a table of rows = <date str>,<value str> to a table of rows = <datetime>,<float>
            @param date_value_table A list of tuples where each tuple contains a date string and a value string.
            @return A list of tuples where each tuple contains a datetime object and a float value."""
        converted_table = []
        for date_str, value_str in date_value_table:
            date_obj = datetime.strptime(date_str, '%d-%m-%Y')
            value_float = float(value_str)
            converted_table.append((date_obj, value_float))
        return converted_table

    def _calc(self):
        """@brief Perform calculation.
                  This calculation involves
                  - For each savings account calculate the increase in the value based on the predicted interest rate for each year.
                    For years beyond those predicted the last predicted interest rate is used.
                  - For each pension check how much it will increase over time.

                  - Sum all the above to produce a predicted increase with no expenditure.
                  - Subtract the monthly expenditure (and it's increase) from the above.
                  - Plot the resulting graph."""
        try:
            plot_table = []
            max_planning_date = self._get_max_date()
            report_start_date = datetime.strptime(self._future_plot_attr_dict[FuturePlotGUI.REPORT_START_DATE], '%d-%m-%Y')
            datetime_list = FuturePlotGUI.GetDateTimeList(report_start_date, max_planning_date)
            pension_drawdown_start_date = datetime.strptime(self._future_plot_attr_dict[FuturePlotGUI.PENSION_DRAWDOWN_START_DATE], '%d-%m-%Y')
            lump_sum_savings_withdrawals_table = self._convert_table(self._future_plot_attr_dict[FuturePlotGUI.SAVINGS_WITHDRAWAL_TABLE])
            lump_sum_pension_withdrawals_table = self._convert_table(self._future_plot_attr_dict[FuturePlotGUI.PENSION_WITHDRAWAL_TABLE])
            pension_growth_rate_list = self._future_plot_attr_dict[FuturePlotGUI.PENSION_GROWTH_RATE_LIST]
            monthly_from_sarah = float(self._future_plot_attr_dict[FuturePlotGUI.MONTHLY_AMOUNT_FROM_SARAH])

            # Get the initial value of our personal pension
            pp_table = self._get_personal_pension_table()
            personal_pension_value = self._get_initial_value(pp_table, report_start_date)
            print(f'PJA: personal_pension_value={personal_pension_value}')

            # Best guess on our monthly outgoings based on the parameters entered.
            monthly_budget_table = self._get_monthly_budget_table(datetime_list)
            predicted_state_pension_table = self._get_predicted_state_pension(datetime_list, report_start_date)
            savings_amount = self._get_savings_total(report_start_date)

            print(f"PJA: initial_savings_amount={savings_amount}")
            last_date = datetime_list[0]
            year_index = 0
            savings_withdrawal_amount = 0
            pension_withdrawal_amount = 0
            lump_sum_savings_withdrawal = 0
            lump_sum_pension_withdrawal = 0
            # Calc the drop in savings up until we start
            for row in monthly_budget_table:
                this_date = row[0]
                income_this_month = row[1]
                state_pension_this_month = self._get_state_pension_this_month(this_date, predicted_state_pension_table)

                # If we are taking money from our personal pension we assume we are no longer taking money from our savings
                if this_date >= pension_drawdown_start_date:
                    pension_withdrawal_amount = income_this_month - state_pension_this_month - monthly_from_sarah
                    personal_pension_value -= pension_withdrawal_amount
                    print(f'PJA: personal_pension_value=£{personal_pension_value}, pension_withdrawal_amount=£{pension_withdrawal_amount}')
                    # No savings drop now we are drawing down on pension.
                    savings_withdrawal_amount = 0

                else:
                    # Deduct our joint state pension amount from the monthly outgoings
                    savings_withdrawal_amount = income_this_month - state_pension_this_month - monthly_from_sarah
                    # No pension drop as we are now we are drawing down on savings.
                    pension_withdrawal_amount = 0

                # Calc the new savings amount
                savings_amount = savings_amount - savings_withdrawal_amount
#                print(f"PJA: Updated savings amount before interest =£{savings_amount}")
                # Interest is generally added to savings accounts yearly we assume jan
                savings_interest = 0
                if this_date.year != last_date.year:
                    # Add on the interest for the next month
                    previous_savings_amount = savings_amount
                    savings_amount = self._get_yearly_savings_increase(savings_amount, year_index)
                    savings_interest = savings_amount - previous_savings_amount
                    year_index += 1
                    last_date = this_date
#                    print(f"PJA: Updated savings amount after interest =£{savings_amount}")

                # Calc increase/decrease of pension this month.
                before = personal_pension_value
                print(f'PJA: CALC PENSION INCREASE: before = £{before}')
                personal_pension_value = self._calc_new_account_value(personal_pension_value, pension_growth_rate_list, year_index, rate_divisor=12)
                print(f'PJA: CALC PENSION INCREASE: after = £{personal_pension_value}, INCREASED BY: £{personal_pension_value-before}')

                # If we drew lump sum/s from savings in the last month
                savings_amount_before = savings_amount
                savings_amount = self._get_value_drop(this_date, savings_amount, lump_sum_savings_withdrawals_table)
                lump_sum_savings_withdrawal = savings_amount_before - savings_amount

                # If we want to draw lump sum/s from our pension in the next month.
                previous_personal_pension_value = personal_pension_value
                personal_pension_value = self._get_value_drop(this_date, personal_pension_value, lump_sum_pension_withdrawals_table)
                print(f"PJA ----> previous_personal_pension_value={previous_personal_pension_value}, personal_pension_value={personal_pension_value}")
                if personal_pension_value < previous_personal_pension_value:
                    lump_sum_pension_withdrawal = previous_personal_pension_value - personal_pension_value
                    print(f"PJA: ----> WITHDREW £{lump_sum_pension_withdrawal} from pension and added it to savings.")
                    # Add the value to our savings
                    savings_amount += lump_sum_pension_withdrawal
                else:
                    lump_sum_pension_withdrawal = 0

                total = savings_amount + personal_pension_value
                print(f"PJA: ----> this_date={this_date}, lump_sum_pension_withdrawal=£{lump_sum_pension_withdrawal}")
#                print(f"PJA: ----> this_date={this_date}, savings_amount=£{savings_amount}, state_pension_this_month=£{state_pension_this_month}, savings_withdrawal_amount=£{savings_withdrawal_amount}")

                total_savings_withdrawal = savings_withdrawal_amount + lump_sum_savings_withdrawal
                total_pension_withdrawal = pension_withdrawal_amount + lump_sum_pension_withdrawal
                plot_table.append( (this_date, total, personal_pension_value, savings_amount, income_this_month, state_pension_this_month, savings_interest, total_savings_withdrawal, total_pension_withdrawal) )

            self._do_plot(plot_table)

        except Exception as ex:
            # PJA DEL
            raise
#            ui.notify(str(ex), type='negative')

    def _get_value_drop(self, this_date, value, withdrawals_table):
        """@brief Determine how much a value drops given the withdrawal table amounts.
                  The withdrawals_table contains dates and amounts on each row. If a date falls
                  within the next month (from this_date) then the amount is deducted from the value.
           @param this_date The date to check for.
           @param value The current value.
           @param withdrawals_table The table (date, amount on each row) that details each value drop.
           @return The new or unchanged value."""
        for row in withdrawals_table:
            _date = row[0]
            amount = row[1]
            if self._in_next_month(_date, this_date):
                value -= amount
        return value

    def _in_next_month(self, this_date, date_to_check):
        """@brief Check if this_date falls in the next month after that_date.
           @param this_date A datetime instance.
           @param that_date A datetime instance.
           @return True if this_date falls in the month previous to that_date."""
        # Calculate next month and year
        next_month = this_date.month % 12 + 1
        next_year = this_date.year + (1 if this_date.month == 12 else 0)

        # Check if the date's month and year match the next month and year
        return date_to_check.year == next_year and date_to_check.month == next_month

    def _do_plot(self, plot_table):
        """@brief perform a plot of the data in the plot_table.
           @param plot_table Holds rows that comprise the following
                             0 = date
                             1 = savings total
                             2 = pension total
                             3 = total of both the above
                             4 = monthly income
                             5 = monthly state pension total of both of us."""
        # Define a secondary page
        @ui.page('/plot_1_page')
        def plot_1_page():
            Plot1GUI(plot_table)
        # This will open in a separate browser window
        ui.run_javascript("window.open('/plot_1_page', '_blank')")

    def _get_savings_total(self, at_date):
        """@brief Calculate the total savings.
           @param at_date The date to predict the value of the savings."""
        savings_total = 0.0
        bank_account_dict_list = self._config.get_bank_accounts_dict_list()
        for bank_account_dict in bank_account_dict_list:
            active = bank_account_dict[BankAccountGUI.ACCOUNT_ACTIVE]
            if active:
                date_value_table = self._convert_table(bank_account_dict[BankAccountGUI.TABLE])
                savings_total += self._get_initial_value(date_value_table, initial_date=at_date)
        return savings_total

    def _get_yearly_savings_increase(self, savings_amount, year_index):
        """@brief Get the value of our savings at the end of the month.
           @param savings_amount The current value of our savings.
           @param year_index An index from the start of the report to this year. Used to determine the predicted interest rate.
           @return As per the brief."""
        yearly_rate_list = self._future_plot_attr_dict[FuturePlotGUI.SAVINGS_INTEREST_RATE_LIST]
        yearly_rate = self._get_yearly_rate(yearly_rate_list, year_index)
        print(f"PJA: yearly_rate={yearly_rate}")
        return savings_amount*(1 + (yearly_rate/100))

    def _get_compound_growth_table(self, initial_value, growth_rate_list, datetime_list):
        """@brief Get a table that details the compound growth of a value. We assume that
                  growth is added yearly.
           @param initial_value The starting value.
           @param growth_rate_list A list of rates of growth for each year.
           @param datetime_list A list of the dates that we wish for the output table.
           @return A table
                   0 = The date.
                   1 = The value."""
        if len(datetime_list) < 2:
            raise Exception(f"_get_compound_growth_table(): datetime_list must have more than 1 element ({len(datetime_list)})")
        compound_growth_table = []
        value = initial_value
        year_count = 0
        last_date = datetime_list[0]
        for _date in datetime_list:
            if _date.year != last_date.year:
                value = self._calc_new_account_value(value, growth_rate_list, year_count)
                year_count += 1
                last_date = _date
            compound_growth_table.append( (_date, value) )
        return compound_growth_table

    def _get_personal_pension_table(self):
        # PJA ADD DOC
        pension_dict_list = self._config.get_pension_dict_list()
        for pension_dict in pension_dict_list:
            state_pension = pension_dict[PensionGUI.STATE_PENSION]
            if not state_pension:
                return self._convert_table(pension_dict[PensionGUI.PENSION_TABLE])

        raise Exception("No personal pension found.")

    def _get_predicted_state_pension(self, datetime_list, report_start_date):
        """ @param datetime_list A list of datetime instances
            @param report_start_date The date for the start of the future prediction report.
            @return A 2D table detailing the predicted state pension.
                   Row
                   0 = date
                   1 = The amount

                   of None if no state pensions found."""
        # Calculate the income from state pensions into the future
        consolidated_state_pension_income_table = None
        pension_dict_list = self._config.get_pension_dict_list()
        for pension_dict in pension_dict_list:
            state_pension_income_table = self._process_state_pension_table(pension_dict, datetime_list, report_start_date)
            # If a state pension was found
            if state_pension_income_table:
                if not consolidated_state_pension_income_table:
                    consolidated_state_pension_income_table = state_pension_income_table
                else:
                    # Add to current state pension table
                    for index in range(0,len(consolidated_state_pension_income_table)):
                        consolidated_state_pension_income_table[index][1] += state_pension_income_table[index][1]

        return consolidated_state_pension_income_table

    def _process_state_pension_table(self, pension_dict, datetime_list, report_start_date):
        """@brief Process a state pension.
           @param pension_dict A dict holding the pension details.
           @param datetime_list A list of monthly datetime instances.
           @return A 2D table each row containing
                   0 = Date
                   1 = The monthly amount from the pension.

                   Or None if the this pension is not a state pension."""
        future_table = None
        state_pension = pension_dict[PensionGUI.STATE_PENSION]
        if state_pension:
            future_table = []
            print(f'PJA: pension_dict={pension_dict}')
            date_value_table = self._convert_table(pension_dict[PensionGUI.PENSION_TABLE])
            state_pension_start_date_str = pension_dict[PensionGUI.STATE_PENSION_START_DATE]
            state_pension_start_date = datetime.strptime(state_pension_start_date_str, '%d-%m-%Y')
            last_datetime = datetime_list[0]
            # Get the initial state pension amount based on the start date for the calc
            state_pension_amount = self._get_initial_value(date_value_table, initial_date=report_start_date)
            year_index = 0
            for this_datetime in datetime_list:
                # If the year hasn't changed
                if this_datetime.year == last_datetime.year:
                    if this_datetime >= state_pension_start_date:
                        future_table.append( [this_datetime, state_pension_amount] )
                    else:
                        future_table.append( [this_datetime, 0.0] )

                # If the year has rolled over
                else:
                    state_pension_amount = self._calc_new_account_value(state_pension_amount, self._future_plot_attr_dict.get(FuturePlotGUI.STATE_PENSION_YEARLY_INCREASE_LIST), year_index)
                    if this_datetime >= state_pension_start_date:
                        future_table.append( [this_datetime, state_pension_amount] )
                    else:
                        future_table.append( [this_datetime, 0.0] )
                    last_datetime = this_datetime
                    year_index = year_index + 1

        return future_table

    def _get_state_pension_this_month(self, at_date, state_pension_table):
        # PJA add check that we have at least one row in the table.
        amount = state_pension_table[0][1]
        for row in state_pension_table:
            _date = row[0]
            amount = row[1]
            if at_date <= _date:
                break
        return amount/12

    def _get_initial_value(self, date_value_table, initial_date=None):
        """@brief Get the first value to be used from the table (date,value rows)
           @param date_value_table A 2 D table of date and value rows.
           @param initial_date If None then we use the first value in the table.
                               If a datetime is provided then we check the date_value_table
                               for the initial_date and use the date before or equal to this
                               for the value we're after."""
        initial_value = date_value_table[0][1]
        if initial_date:
            for row in date_value_table:
                _date = row[0]
                _value = row[1]
                if _date >= initial_date:
                    initial_value = _value
                    break
        return initial_value

    def _get_monthly_budget_table(self, datetime_list):
        """@brief Get a table detailing how much we plan to spend each month from our savings and pension."""
        future_table = []
        last_datetime = datetime_list[0]
        monthly_income = float(self._future_plot_attr_dict[FuturePlotGUI.MONTHLY_INCOME])
        year_index = 0
        print(f"PJA: monthly_income={monthly_income}")
        for this_datetime in datetime_list:
            if this_datetime.year == last_datetime.year:
                future_table.append( [this_datetime, monthly_income] )
            # We check for year rolling over as this is when we expect an increase in our income against inflation.
            else:
                monthly_income = self._calc_new_account_value(monthly_income, self._future_plot_attr_dict.get(FuturePlotGUI.YEARLY_INCREASE_IN_INCOME), year_index)
                future_table.append( [this_datetime, monthly_income] )
                last_datetime = this_datetime
                year_index += 1

        return future_table

    def _get_yearly_rate(self,
                         rate_list,
                         year_index):
        """@brief Get the interest/growth rate for the year.
           @param rate_list A list detailing the predicted interest/growth rates in future years (0=this year, 1=next year and so on). This may also be a comma separated string.
           @param The index to the above list of rates. If the index is greater than the number of elements in the ate_list then the last rate is used."""
        if len(rate_list) < 1:
            raise Exception("Rate list error. The rate_list must have at least one element.")
        if isinstance(rate_list, str):
            rate_list = rate_list.split(',')
        selected_rate = rate_list[0]
        if year_index >= 0 and year_index < len(rate_list):
            selected_rate = rate_list[year_index]
        else:
            selected_rate = rate_list[-1]
        selected_rate = float(selected_rate)
        return selected_rate

    def _calc_new_account_value(self,
                                current_value,
                                rate_list,
                                year_index,
                                rate_divisor=1):
        """@brief Calculate the new value of an account.
           @param current_value The current value of the account.
           @param rate_list A list of (strings) detailing the predicted rates in future years (0=this year, 1=next year and so on).
           @param The index to the above list of rates. If the index is greater than the number of elements in the ate_list then the last rate is used.
           @param rate_divisor If 1 then the yearly % is used. If 12 then the monthly % is used."""
        selected_rate = self._get_yearly_rate(rate_list, year_index)
        selected_rate = selected_rate / rate_divisor
        print(f"PJA: >>>> selected_rate={selected_rate}")
        new_value = current_value * (1 + selected_rate / 100)
        return new_value

class Plot1GUI(GUIBase):
    """@brief Responsible for plotting the data of the predicted changes in the savings as we draw out money."""

    def __init__(self, plot_table):
        """@param plot_table Holds rows that comprise the following
                             0 = date
                             1 = total (savings + pension)
                             2 = pension total
                             3 = savings total
                             4 = monthly income
                             5 = monthly state pension total of both of us.
                             6 = savings_interest (yearly)
                             7 = savings withdrawal this month
                             8 = pension withdrawal this month.
                             """
        self._plot_table = plot_table
        self._init_gui()

    def _init_gui(self):
        """@brief plot the data in the plot table."""
        with ui.column().style('width: 100%; margin: 0 auto;'):
            # A plot of energy costs is added to this container when the users requests it
            plot_panel_1 = ui.element('div').style('width: 100%;')

        with ui.column().style('width: 100%; margin: 0 auto;'):
            # A plot of energy costs is added to this container when the users requests it
            plot_panel_2 = ui.element('div').style('width: 100%;')

        with ui.column().style('width: 100%; margin: 0 auto;'):
            # A plot of energy costs is added to this container when the users requests it
            plot_panel_3 = ui.element('div').style('width: 100%;')

        with ui.column().style('width: 100%; margin: 0 auto;'):
            # A plot of energy costs is added to this container when the users requests it
            plot_panel_4 = ui.element('div').style('width: 100%;')

        plot_names = ['Total','Personal Pension','Savings']
        plot_dict = {plot_names[0]:[],
                     plot_names[1]:[],
                     plot_names[2]:[]}

        for row in self._plot_table:
            _date = row[0]
            total = row[1]
            personal_pension = row[2]
            savings = row[3]

            plot_dict[plot_names[0]].append( (_date, total) )
            plot_dict[plot_names[1]].append( (_date, personal_pension) )
            plot_dict[plot_names[2]].append( (_date, savings) )

        self._do_plot(plot_panel_1, plot_dict)


        plot_names = ['Monthly budget/income', 'Total state pension']
        plot_dict = {plot_names[0]:[],
                     plot_names[1]:[]}

        for row in self._plot_table:
            _date = row[0]
            monthly_income = row[4]
            monthly_state_pension = row[5]

            plot_dict[plot_names[0]].append( (_date, monthly_income) )
            plot_dict[plot_names[1]].append( (_date, monthly_state_pension) )

        self._do_plot(plot_panel_2, plot_dict)

        plot_names = ['Savings Interest']
        plot_dict = {plot_names[0]:[]}

        for row in self._plot_table:
            _date = row[0]
            savings_interest = row[6]

            plot_dict[plot_names[0]].append( (_date, savings_interest) )

        self._do_plot(plot_panel_3, plot_dict, bar_chart=True)

        plot_names = ['Savings withdrawal', 'Pension withdrawal']
        plot_dict = {plot_names[0]:[],
                     plot_names[1]:[]}

        for row in self._plot_table:
            _date = row[0]
            savings_withdrawal = row[7]
            pensions_withdrawal = row[8]

            plot_dict[plot_names[0]].append( (_date, savings_withdrawal) )
            plot_dict[plot_names[1]].append( (_date, pensions_withdrawal) )

        self._do_plot(plot_panel_4, plot_dict, bar_chart=True)

    def _do_plot(self, plot_pane, plot_dict, bar_chart=False):
        """@brief Perform a plot of the data in the plot_dict on the plot_pane.
           @param plot_pane The area to plot data on.
           @param plot_dict The dict containing date to be plotted.
                            Each key in the dict is the name of the plot.
                            Each value is a row in the table
                            0 = The date.
                            1 = The value.
           @param bar_chart If True show a bar chart."""
        fig = go.Figure()

        max_y = 0
        for plot_name in plot_dict:
            plot_table= plot_dict[plot_name]
            print(f"PJA: plot_name={plot_name}")
            x, y = zip(*plot_table)
            my = max(y)
            if my > max_y:
                max_y = my
            if bar_chart:
                fig.add_trace(go.Bar(name=plot_name, x=x, y=y))
            else:
                fig.add_trace(go.Scatter(name=plot_name, x=x, y=y, mode='lines+markers'))

        max_y = int(max_y * 1.1)
        fig.update_layout(margin=dict(l=40, r=40, t=40, b=40),
                          showlegend=True,
                          plot_bgcolor="black",       # Background for the plot area
                          paper_bgcolor="black",      # Background for the entire figure
                          font=dict(color="yellow"),  # Font color for labels and title
                          xaxis=dict(
                              title='Date',
                              tickformat='%d-%m-%Y',  # Format as day-month-year
                              color="yellow",         # Axis label color
                              gridcolor="gray",       # Gridline color
                              zerolinecolor="gray"    # Zero line color
                          ),
                          yaxis=dict(
                              title="£",
                              color="yellow",         # Axis label color
                              gridcolor="gray",       # Gridline color
                              zerolinecolor="gray",   # Zero line color
                              range=[0, max_y]    # Ensure 0 is on Y axis
                          ),)

        if plot_pane:
            plot_pane.clear()
            with plot_pane:
                ui.plotly(fig).style('width: 100%; height: 100%;')

def main():
    """@brief Program entry point"""
    uio = UIO()
    options = None

    try:
        parser = argparse.ArgumentParser(description="ngt examples.",
                                         formatter_class=argparse.RawDescriptionHelpFormatter)
        parser.add_argument("-d", "--debug",  action='store_true', help="Enable debugging.")
        parser.add_argument("-enable_syslog", action='store_true', help="Enable syslog.")

        options = parser.parse_args()
        uio.enableDebug(options.debug)
        uio.logAll(True)
        uio.enableSyslog(options.enable_syslog, programName="ngt")
        if options.enable_syslog:
            uio.info("Syslog enabled")

        finances = Finances()
        finances.initGUI(uio, options.debug)

    # If the program throws a system exit exception
    except SystemExit:
        pass
    # Don't print error information if CTRL C pressed
    except KeyboardInterrupt:
        pass
    except Exception as ex:
        logTraceBack(uio)

        if not options or options.debug:
            raise
        else:
            uio.error(str(ex))


# Note __mp_main__ is used by the nicegui module
if __name__ in {"__main__", "__mp_main__"}:
    main()
