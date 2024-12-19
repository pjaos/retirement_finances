#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import json
import copy

from p3lib.uio import UIO
from p3lib.helper import logTraceBack
from p3lib.pconfig import DotConfigManager
from p3lib.ngt import TabbedNiceGui, YesNoDialog

from nicegui import ui

class GUIBase(object):

    @staticmethod
    def GetInputDateField(label):
        """@brief Add a control to allow the user to enter the date as an DD:MM:YYYY.
           @param label The label for the field.
           @return The input field containing the DD:MM:YYYY entered."""
        date_input = ui.input(label=label).style("width: 230px;")
        with date_input as _date:
            with ui.menu().props('no-parent-event') as menu:
                with ui.date(mask='DD-MM-YYYY').bind_value(_date):
                    ui.button('Close', on_click=menu.close).props('flat')
            with _date.add_slot('append'):
                ui.icon('access_calendar_today').on('click', menu.open).classes('cursor-pointer')
        return date_input

    def __init__(self):
        """@brief Constructor"""
        pass

class Config(object):
    """@brief Responsible for loading and saving the app config."""
    BANK_ACCOUNTS_FILE = "bank_accounts.json"

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

    def __init__(self):
        self._config_folder = Config.GetConfigFolder()
        # Notify user of config location on startup
        ui.notify(f"Config folder: {self._config_folder}")
        self._bank_accounts_file = Config.GetBankAccountListFile()
        self._load_bank_accounts()

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
           @param input_field_list A bank account dict."""
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

class Finances(GUIBase):

    GUI_TIMER_SECONDS = 0.1
    YES = "Yes"
    NO = "No"

    ADD_ACCOUNT_BUTTON = 1
    DELETE_ACCOUNT_BUTTON = 2
    EDIT_ACCOUNT_BUTTON = 3
    VIEW_ACCOUNT_BUTTON = 4

    def __init__(self):
        super().__init__()
        self._config = Config()

    def initGUI(self,
                uio,
                debugEnabled,
                reload=True,
                address='0.0.0.0',
                port=9090):
        self._uio = uio
        self._address = address
        self._port = port
        self._reload = reload

        self._init_dialogs()
        self._bank_account_action_button = None

        tabNameList = ('Bank/Building Society accounts',
                       'Private Pensions',
                       'State Pensions',
                       'Reports')
        # This must have the same number of elements as the above list
        tabMethodInitList = [self._init_bank_accounts_tab,
                             self._private_pensions_tab,
                             self._state_pensions_tab,
                             self._reports_tab]

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

    def _init_bank_accounts_tab(self):
        """@brief Create the bank accounts tab."""

        with ui.row():
            columns = [{'name': 'Bank', 'label': 'Bank', 'field': 'Bank'},
                       {'name': 'Account Name', 'label': 'Account Name', 'field': 'Account Name'},
                      ]
            self._bank_acount_table = ui.table(columns=columns,
                                               rows=[],
                                               row_key='Account Name',
                                               selection='single').classes('h-96').props('virtual-scroll')
            self._show_bank_account_list()

        with ui.row():
            ui.button('Add', on_click=lambda: self._add_bank_account() ).tooltip('Add a bank/building society account')
            ui.button('Delete', on_click=lambda: self._delete_bank_account_dialog() ).tooltip('Delete a bank/building society account')
            ui.button('Edit', on_click=lambda: self._edit_bank_account() ).tooltip('Edit a bank/building society account')
            ui.button('Update', on_click=lambda: self._show_bank_account_list() ).tooltip('Update the list bank/building society accounts')

    def _private_pensions_tab(self):
        pass

    def _state_pensions_tab(self):
        pass

    def _reports_tab(self):
        pass

    def _init_dialogs(self):
        """@brief Create the dialogs used by the app."""
        self._init_dialog2()

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
        self._config.remove_bank_account(self._last_selected_index)
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
            bank = bank_account_dict[BankAccountGUI.ACCOUNT_BANK_NAME_LABEL]
            account_name = bank_account_dict[BankAccountGUI.ACCOUNT_NAME_LABEL]
            self._bank_acount_table.add_row({'Bank':bank, 'Account Name': account_name})
        self._bank_acount_table.run_method('scrollTo', len(self._bank_acount_table.rows)-1)

    def _delete_bank_account_dialog(self):
        """@brief Delete the selected bank account."""
        self._bank_account_action_button = Finances.DELETE_ACCOUNT_BUTTON
        self._last_selected_index = self._get_selected_bank_account_index()
        if self._last_selected_index < 0:
            ui.notify("Select a bank account to delete.")
        else:
            self._show_dialog2()

    def _get_selected_bank_account_index(self):
        selected_index = -1
        selected_dict = self._bank_acount_table.selected
        if len(selected_dict) > 0:
            selected_dict=selected_dict[0]
            if selected_dict:
                bank_name = selected_dict['Bank']
                account_name = selected_dict['Account Name']
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
           return The selected bank account dict or None if no bank account is selected."""
        bank_account_dict = None
        self._last_selected_index = self._get_selected_bank_account_index()
        if self._last_selected_index >= 0:
            bank_account_dict_list = self._config.get_bank_accounts_dict_list()
            bank_account_dict = bank_account_dict_list[self._last_selected_index]
        return bank_account_dict

    def _add_bank_account(self):
        """@brief Add a bank account."""
        self._update_bank_account(True, {})

    def _edit_bank_account(self):
        """@brief Add a bank account."""
        bank_account_dict = self._get_selected_bank_account_dict()
        if bank_account_dict:
            self._update_bank_account(False, bank_account_dict)

    def _update_bank_account(self, add, bank_account_dict):
        """@brief edit bank account details.
           @param add If True then add to the list of available bank accounts.
           @param bank_account_dict A dict holding the bank account details."""
        if isinstance(bank_account_dict, dict):
            # Define a secondary page
            @ui.page('/bank_account_page')
            def bank_account_page():
                BankAccountGUI(add, bank_account_dict, self._config)
#            ui.run_javascript("window.open('/bank_account_page', '_blank')")
            ui.run_javascript("window.open('/bank_account_page', '_parent')")

        else:
            ui.notify("Select a bank account to view.")


class BankAccountGUI(object):
    """@brief Responsible for allowing the user to add details (date and amount of a bank account)."""

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

    def __init__(self, add, bank_account, config):
        """@brief Constructor.
           @param add If True then add to the list of available bank accounts.
           @param bank_account_dict A dict holding the bank account details.
           @param config A Config instance."""
        self._add = add
        self._bank_account = bank_account
        self._config = config
        self._selected_row_index = -1
        self.init_page()
        self._init_add_row_dialog()
        self._update_gui_from_bank_account()

    def init_page(self):
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
                columns = [{'name': 'Date', 'label': 'Date', 'field': 'Date'},
                        {'name': 'Balance (£)', 'label': 'Balance (£)', 'field': 'Balance (£)'},
                        ]
                self._bank_acount_table = ui.table(columns=columns,
                                                   rows=[],
                                                   row_key='Date',
                                                   selection='single')

                self._display_table_rows()


        with ui.row():
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
        """@brief Get the table from the dict that holds the balance table."""
        table = []
        if 'table' in self._bank_account:
            table = copy.deepcopy(self._bank_account['table'])
        else:
            self._bank_account['table'] = table
        return table

    def _add_table_row(self, row):
        self._bank_account['table'].append(row)

    def _init_add_row_dialog(self):
        """@brief Create a dialog presented to the user to check that they wish to delete a bank account."""
        with ui.dialog() as self._add_row_dialog, ui.card().style('width: 400px;'):
            self._date_input_field = GUIBase.GetInputDateField('Date')
            self._amount_field = ui.input(label="Balance (£)")
            with ui.row():
                ui.button("Ok", on_click=self._add_row_dialog_ok_button_press)
                ui.button("Cancel", on_click=self._add_row_dialog_cancel_button_press)

    def _add_row_dialog_ok_button_press(self):
        self._add_row_dialog.close()
        row = (self._date_input_field.value, self._amount_field.value)
        self._add_table_row(row)
        self._display_table_rows()
        self._config.save_bank_accounts()

    def _display_table_rows(self):
        """@brief Show a table of the configured bank accounts."""
        self._bank_acount_table.rows.clear()
        self._bank_acount_table.update()
        table = self._bank_account['table']
        for row in table:
            self._bank_acount_table.add_row({'Date': row[0], 'Balance (£)': row[1]})
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
        if selected_dict and 'Date' in selected_dict[0]:
            del_date = selected_dict[0]['Date']
            table = self._bank_account['table']
            new_table = []
            for row in table:
                date = row[0]
                if date != del_date:
                    new_table.append(row)
            self._bank_account['table'] = new_table
        self._display_table_rows()
        self._config.save_bank_accounts()

    def _update_gui_from_bank_account(self):
        """@brief Update the contents of fields from the bank account entered."""
        input_field_list = self._bank_account_field_list
        bank_account_dict = self._bank_account

        for input_field in input_field_list:
            if isinstance(input_field, ui.number):
                if BankAccountGUI.ACCOUNT_INTEREST_RATE in bank_account_dict:
                    input_field.value = bank_account_dict[BankAccountGUI.ACCOUNT_INTEREST_RATE]
                else:
                    # If not present in dict create empty value
                    input_field.value = 0
                    bank_account_dict[BankAccountGUI.ACCOUNT_INTEREST_RATE] = input_field.value

            elif isinstance(input_field, ui.select):
                if BankAccountGUI.ACCOUNT_INTEREST_RATE_TYPE in bank_account_dict:
                    input_field.value = bank_account_dict[BankAccountGUI.ACCOUNT_INTEREST_RATE_TYPE]
                else:
                    # If not present in dict create empty value
                    input_field.value = 'Fixed'
                    bank_account_dict[BankAccountGUI.ACCOUNT_INTEREST_RATE_TYPE] = input_field.value

            elif isinstance(input_field, ui.checkbox):
                if BankAccountGUI.ACCOUNT_ACTIVE in bank_account_dict:
                    input_field.value = bank_account_dict[BankAccountGUI.ACCOUNT_ACTIVE]
                else:
                     # If not present in dict create empty value
                    input_field.value = True
                    bank_account_dict[BankAccountGUI.ACCOUNT_ACTIVE] = input_field.value

            else:
                props = input_field._props
                key = props['label']
                if key in bank_account_dict:
                    value = bank_account_dict[key]
                else:
                    # If not present in dict create empty value
                    value = ""
                    bank_account_dict[key] = value
                input_field.value = value

    def _update_bank_account_from_gui(self):
        """@brief Update the bank account dict. from the GUI fields."""
        # Do some checks on the values entered.
        if len(self._bank_account_field_list[0].value ) == 0:
            ui.notify("Bank/Building society name must be entered.")

        elif len(self._bank_account_field_list[1].value ) == 0:
            ui.notify("Account name must be entered.")

        else:
            input_field_list = self._bank_account_field_list
            if self._add:
                bank_account_dict = {}
                self._bank_account = bank_account_dict
            else:
                bank_account_dict = self._bank_account
            for input_field in input_field_list:
                props = input_field._props
                if isinstance(input_field, ui.number):
                    key = props['label']
                    value = input_field.value

                elif isinstance(input_field, ui.select):
                    key = "interest type"
                    entry_dict = props['model-value']
                    value = entry_dict['label']

                elif isinstance(input_field, ui.checkbox):
                    key = "active"
                    value = props['model-value']

                elif 'label' in props and 'value' in props:
                    key = props['label']
                    value = props['value']

                else:
                    raise Exception(f"Unable to add bank account: input_field={input_field}")

                bank_account_dict[key]=value

            if self._add:
                self._config.add_bank_account(bank_account_dict)

            else:
                # If editing an account then the bank_account_dict has been modified and we just need to save it.
                self._config.save_bank_accounts()


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
