#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import copy
import shutil
import traceback
import bcrypt
import platform

from datetime import datetime
from dateutil.relativedelta import relativedelta

import pandas as pd

from p3lib.uio import UIO
from p3lib.helper import logTraceBack
from p3lib.pconfig import DotConfigManager
from p3lib.file_io import CryptFile

from p3lib.helper import getAbsFile, getProgramVersion

from nicegui import ui, app

import plotly.graph_objects as go


class Config(object):
    """@brief Responsible for loading and saving the app config."""
    BANK_ACCOUNTS_FILE = "bank_accounts.json"
    PENSIONS_FILE = "pensions.json"
    FUTURE_PLOT_ATTR_FILE = "future_plot_attr.json"
    MULTIPLE_FUTURE_PLOT_ATTR_FILE = "multiple_future_plot_attr.json"
    SELECTED_FUTURE_PLOT_NAME_ATTR_FILE = "selected_future_plot_name_attr.json"
    GLOBAL_CONFIGURATION_FILE = "global_configuration_parameters.json"
    MONTHLY_SPENDING_FILE = "monthly_spending.json"
    PASSWORD_HASH_FILE = "password_hash.txt"

    @staticmethod
    def GetConfigFolder(folder):
        """@brief Get the folder use to store files in.
           @param folder If defined and the folder exists it is used to store files.
           @return The folder where config files are stored.
           """
        if folder:
            if os.path.isdir(folder):
                cfg_folder = folder
            else:
                raise Exception("{folder} folder not found.")
        else:
            default_cfg_folder = DotConfigManager.GetDefaultConfigFolder()
            cfg_folder = os.path.join(default_cfg_folder, 'retirement_finances')

        if not os.path.isdir(cfg_folder):
            os.makedirs(cfg_folder)
        return cfg_folder

    def load_config(self, password):
        """@brief Load the encrypted config.
           @param password The password used to encrypt and decrypt the config files."""
        self._password = password
        self._global_configuration_name_crypt_file = CryptFile(filename=self._global_configuration_name_file, password=self._password)
        self.load_global_configuration()

        self._bank_account_crypt_file = CryptFile(filename=self._bank_accounts_file, password=self._password)
        self._load_bank_accounts()

        self._pensions_crypt_file = CryptFile(filename=self._pensions_file, password=self._password)
        self._load_pensions()

        self._future_plot_crypt_file = CryptFile(filename=self._future_plot_file, password=self._password)
        self._load_future_plot_attrs()

        self._multiple_future_plot_crypt_file = CryptFile(filename=self._multiple_future_plot_file, password=self._password)
        self._load_multiple_future_plot_attrs()

        self._selected_retirement_parameters_name_crypt_file = CryptFile(filename=self._selected_retirement_parameters_name_file, password=self._password)
        self._load_selected_retirement_parameters_name_attrs()

        self._monthly_spending_crypt_file = CryptFile(filename=self._monthly_spending_file, password=self._password)
        self._load_monthly_spending_dict()

    def __init__(self, folder, show_load_save_notifications=True):
        self._config_folder = Config.GetConfigFolder(folder)
        self._show_load_save_notifications = show_load_save_notifications

        self._global_configuration_name_file = self._getGlobalConfigurationFile()
        self._bank_accounts_file = self._getBankAccountListFile()
        self._pensions_file = self._getPensionsListFile()
        self._future_plot_file = self._getFuturePlotAttrFile()
        self._multiple_future_plot_file = self._getMultipleFuturePlotAttrFile()
        self._selected_retirement_parameters_name_file = self._getSelectedRequirementParametersNameFile()
        self._monthly_spending_file = self._getMonthlySpendingFile()

    def _getPasswordHashFile(self):
        """@return The file used to store the password hash."""
        return os.path.join(self._config_folder, Config.PASSWORD_HASH_FILE)

    def get_config_folder(self):
        """@return the folder used to store config files."""
        return self._config_folder

    def _getBankAccountListFile(self):
        """@return The file used to store bank account details."""
        return os.path.join(self._config_folder, Config.BANK_ACCOUNTS_FILE)

    def _getPensionsListFile(self):
        """@return The file used to store pension details."""
        return os.path.join(self._config_folder, Config.PENSIONS_FILE)

    def _getFuturePlotAttrFile(self):
        """@return The file used to store future plot details."""
        return os.path.join(self._config_folder, Config.FUTURE_PLOT_ATTR_FILE)

    def _getMultipleFuturePlotAttrFile(self):
        """@return The file used to store multiple future plot details."""
        return os.path.join(self._config_folder, Config.MULTIPLE_FUTURE_PLOT_ATTR_FILE)

    def _getSelectedRequirementParametersNameFile(self):
        """@return The file used to store the selected future plot name."""
        return os.path.join(self._config_folder, Config.SELECTED_FUTURE_PLOT_NAME_ATTR_FILE)

    def _getGlobalConfigurationFile(self):
        """@return The file used to store global configuration parameters."""
        return os.path.join(self._config_folder, Config.GLOBAL_CONFIGURATION_FILE)

    def _getMonthlySpendingFile(self):
        """@return The file used to store monthly spending details."""
        return os.path.join(self._config_folder, Config.MONTHLY_SPENDING_FILE)

    def hash_password(self, password: str) -> str:
        """@brief Create a hash from a password in order to validate a password in a secure manner.
           @param password The password to be hashed.
           @return The hashed password."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode(), salt)
        return hashed.decode()

    def get_stored_password_hash(self):
        """@brief Get the stored hashed password.
           @return The hashed password or None if no password found."""
        pw_hash = None
        pw_hash_file = self._getPasswordHashFile()
        if os.path.isfile(pw_hash_file):
            with open(pw_hash_file, 'r') as fd:
                pw_hash = fd.read()
        return pw_hash

    def store_password_hash(self, password):
        """@brief Store the hash of the password to the passwords file.
           @param pasword The password to store the hash of."""
        hashed_password = self.hash_password(password)
        pw_hash_file = self._getPasswordHashFile()
        if os.path.isfile(pw_hash_file):
            raise Exception(f"{pw_hash_file} password file already present.")
        else:
            with open(pw_hash_file, 'w') as fd:
                fd.write(hashed_password)

    # --- methods for bank accounts ---

    def _load_bank_accounts(self):
        """@brief Load bank accounts from file."""
        try:
            self._bank_accounts_dict_list = []
            self._bank_accounts_dict_list = self._bank_account_crypt_file.load()
            if self._show_load_save_notifications:
                ui.notify(f'Loaded from {self._bank_account_crypt_file.get_file()}', type='positive', position='center', duration=2)

        except Exception:
            ui.notify(f'{self._bank_account_crypt_file.get_file()} file not found.', type='negative')

    def save_bank_accounts(self):
        """@brief Save the bank accounts dict list persistently."""
        self._bank_account_crypt_file.save(self._bank_accounts_dict_list)
        if self._show_load_save_notifications:
            ui.notify(f'Saved {self._bank_account_crypt_file.get_file()}', type='positive', position='center', duration=2)

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
        try:
            self._pension_dict_list = []
            self._pension_dict_list = self._pensions_crypt_file.load()
            if self._show_load_save_notifications:
                ui.notify(f'Loaded from {self._pensions_crypt_file.get_file()}', type='positive', position='center', duration=2)

        except Exception:
            ui.notify(f'{self._pensions_crypt_file.get_file()} file not found.', type='negative')

    def save_pensions(self):
        """@brief Save the pension dict list persistently."""
        self._pensions_crypt_file.save(self._pension_dict_list)
        if self._show_load_save_notifications:
            ui.notify(f'Saved {self._pensions_crypt_file.get_file()}', type='positive', position='center', duration=2)

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
        try:
            self._future_plot_attr_dict = {}
            self._future_plot_attr_dict = self._future_plot_crypt_file.load()
            if self._show_load_save_notifications:
                ui.notify(f'Loaded from {self._future_plot_crypt_file.get_file()}', type='positive', position='center', duration=2)

        except Exception:
            ui.notify(f'{self._future_plot_crypt_file.get_file()} file not found.', type='negative')

    def save_future_plot_attrs(self):
        """@brief Save the future plot parameters persistently."""
        self._future_plot_crypt_file.save(self._future_plot_attr_dict)
        if self._show_load_save_notifications:
            ui.notify(f'Saved {self._future_plot_crypt_file.get_file()}', type='positive', position='center', duration=2)

    def get_future_plot_attrs_dict(self):
        """@brief Get the the future plot parameters dict."""
        return self._future_plot_attr_dict

    def replace_future_plot_attrs_dict(self, new_future_plot_attrs_dict):
        self._future_plot_attr_dict = new_future_plot_attrs_dict

    # --- methods for future plot parameters list ---

    def _load_multiple_future_plot_attrs(self):
        """@brief Load the multiple future plot parameters from file."""
        try:
            self._multiple_future_plot_attr_dict = {}
            self._multiple_future_plot_attr_dict = self._multiple_future_plot_crypt_file.load()
            if self._show_load_save_notifications:
                ui.notify(f'Loaded from {self._multiple_future_plot_crypt_file.get_file()}', type='positive', position='center', duration=2)

        except Exception:
            ui.notify(f'{self._multiple_future_plot_crypt_file.get_file()} file not found.', type='negative')

    def save_multiple_future_plot_attrs(self):
        """@brief Save the multiple_future plot parameters persistently."""
        self._multiple_future_plot_crypt_file.save(self._multiple_future_plot_attr_dict)
        if self._show_load_save_notifications:
            ui.notify(f'Saved {self._multiple_future_plot_crypt_file.get_file()}', type='positive', position='center', duration=2)

    def get_multiple_future_plot_attrs_dict(self):
        """@brief Get the future plot parameters dict."""
        return self._multiple_future_plot_attr_dict

    # --- methods for selected future plot parameters name ---

    def _load_selected_retirement_parameters_name_attrs(self):
        """@brief Load the selected retirement parameters name parameters from file."""
        try:
            self._selected_retirement_parameters_name_dict = {}
            self._selected_retirement_parameters_name_dict = self._selected_retirement_parameters_name_crypt_file.load()
            if self._show_load_save_notifications:
                ui.notify(f'Loaded from {self._selected_retirement_parameters_name_crypt_file.get_file()}', type='positive', position='center', duration=2)

        except Exception:
            ui.notify(f'{self._selected_retirement_parameters_name_crypt_file.get_file()} file not found.', type='negative')

    def _save_selected_retirement_parameters_name_attrs(self):
        """@brief Save the selected retirement parameters name parameters persistently."""
        self._selected_retirement_parameters_name_crypt_file.save(self._selected_retirement_parameters_name_dict)
        if self._show_load_save_notifications:
            ui.notify(f'Saved {self._selected_retirement_parameters_name_crypt_file.get_file()}', type='positive', position='center', duration=2)

    def get_selected_retirement_parameters_name_dict(self):
        """@brief Get the selected retirement parameters name parameters dict."""
        return self._selected_retirement_parameters_name_dict

    # --- methods for global configuration parameters ---

    def load_global_configuration(self):
        """@brief Load the global configuration parameters from file."""
        try:
            self._global_configuration_dict = {}
            self._global_configuration_dict = self._global_configuration_name_crypt_file.load()
            if self._show_load_save_notifications:
                ui.notify(f'Loaded from {self._global_configuration_name_crypt_file.get_file()}', type='positive', position='center', duration=2)

        except Exception:
            ui.notify(f'{self._global_configuration_name_crypt_file.get_file()} file not found.', type='negative')
            self.save_global_configuration()

    def save_global_configuration(self):
        """@brief Save the global configuration parameters persistently."""
        self._global_configuration_name_crypt_file.save(self._global_configuration_dict)
        if self._show_load_save_notifications:
            ui.notify(f'Saved {self._global_configuration_name_crypt_file.get_file()}', type='positive', position='center', duration=2)

    def get_global_configuration_dict(self):
        """@brief Get the global configuration parameters name parameters dict."""
        return self._global_configuration_dict

    # --- methods for holding the recording monthly spending values ---

    def _load_monthly_spending_dict(self):
        """@brief Load the monthly spending dict from a file."""
        try:
            self._monthly_spending_dict = {}
            self._monthly_spending_dict = self._monthly_spending_crypt_file.load()
            if self._show_load_save_notifications:
                ui.notify(f'Loaded from {self._monthly_spending_crypt_file.get_file()}', type='positive', position='center', duration=2)

        except Exception:
            ui.notify(f'{self._monthly_spending_crypt_file.get_file()} file not found.', type='negative')

    def _save_monthly_spending_dict(self):
        """@brief Save the monthly spending dict to a file."""
        self._monthly_spending_crypt_file.save(self._monthly_spending_dict)
        if self._show_load_save_notifications:
            ui.notify(f'Saved {self._monthly_spending_crypt_file.get_file()}', type='positive', position='center', duration=2)

    def get_monthly_spending_dict(self):
        """@brief Get the the monthly spending dict."""
        return self._monthly_spending_dict


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
                ui.icon('edit_calendar').on(
                    'click', menu.open).classes('cursor-pointer')
        date.tooltip("DD-MM-YYYY")
        return date

    @staticmethod
    def CheckValidDateString(date_str, field_name=None):
        """@brief Check for a valid date string. An exception is thrown if the date is invalid.
           @param date_str The dd-mm-yyyy format string.
           @param field_name The optional name of the field being checked.
           @return True if date is valid."""
        valid = False
        try:
            datetime.strptime(date_str, '%d-%m-%Y')
            valid = True
        except Exception:
            msg = f"The date '{date_str}' is not a valid date string (dd-mm-yyyy)"
            if field_name:
                msg = f"The '{field_name}' = '{date_str}' is not a valid date string (dd-mm-yyyy)"
            ui.notify(msg, type='negative')
        return valid

    @staticmethod
    def CheckGreaterThanZero(number, field_name=None):
        """@brief Check that the number is greater than 0.0.
           @param number The number to check.
           @param field_name The optional name of the field being checked.
           @return True if number is greater than 0."""
        if number is None:
            number = 0
        valid = False
        if number > 0.0:
            valid = True
        else:
            msg = f"The number entered ({number}) must be greater than zero."
            if field_name:
                msg = f"The '{field_name}' = ({number}) must be greater than zero."
            ui.notify(msg, type='negative')
        return valid

    def CheckZeroOrGreater(number, field_name=None):
        """@brief Check that the number is 0.0 or greater.
           @param number The number to check.
           @param field_name The optional name of the field being checked.
           @return True if number is 0 or greater."""
        if number is None:
            number = 0
        valid = False
        if number >= 0.0:
            valid = True
        else:
            msg = f"The number entered ({number}) must be zero or greater."
            if field_name:
                msg = f"The '{field_name}' = ({number}) must be zero or greater."
            ui.notify(msg, type='negative')
        return valid

    @staticmethod
    def CheckCommaSeparatedNumberList(comma_separated_number_str, field_name=None):
        """@brief Check that the string entered contains a comma separated number list.
           @param comma_separated_number_str The string to check.
           @param field_name The optional name of the field being checked.
           @return True if the string is a valid comma separated list of numbers."""
        valid = False
        try:
            elems = comma_separated_number_str.split(',')
            for elem in elems:
                float(elem)
            valid = True
        except ValueError:
            msg = f"'{comma_separated_number_str}' is not a valid comma separated number list."
            if field_name:
                msg = f"The '{field_name}' = '{comma_separated_number_str}' is not a valid comma separated number list."
            ui.notify(msg, type='negative')

        return valid

    @staticmethod
    def CheckDuplicateDate(table, date_str):
        """@brief check that the dateStr is not already present in the table.
           @param table A table in which the first column is the date (string format) in the form DD-HH-YYYY.
           @param date_str A date (string format) in the form DD-HH-YYYY."""
        # Check that the date entered is not already in the table
        valid = True
        for row in table:
            if row[0] == date_str:
                valid = False
                break

        if not valid:
            ui.notify(f"{date_str} is already present.", type='negative')

        return valid

    def __init__(self):
        """@brief Constructor"""
        pass


class Finances(GUIBase):

    GUI_TIMER_SECONDS = 0.1
    YES = "Yes"
    NO = "No"

    MY_NAME_FIELD = "My Name"
    PARTNER_NAME_FIELD = "Partner Name"

    def __init__(self, uio, password, folder):
        super().__init__()
        self._uio = uio
        self._password = password
        self._folder = folder
        self._bank_acount_table = None
        self._pension_table = None
        self._monthly_spend_table = None
        self._first_password = None
        self._authenticated_password = None
        self._config = Config(self._folder,
                              show_load_save_notifications=self._uio.isDebugEnabled())
        self._program_version = getProgramVersion()

    def _open_main_window(self):
        """@brief Called to allow the user to enter the password in order to access
                 the GUI."""
        # If the password has been setup
        if self._is_password_setup():
            self._authenticate_password()

        # If the password has yet to be setup
        else:
            self._setup_password()

    def _is_password_setup(self):
        """@return True if the password has been set."""
        password_set = False
        stored_password_hash = self._config.get_stored_password_hash()
        if stored_password_hash:
            password_set = True
        return password_set

    def _setup_password(self):
        """@brief Called if we have not saved a password hash in order to set one up."""
        # If the user has entered the password once.
        if self._first_password:
            second_password = self._password_input.value
            # If the first and second passwords match
            if self._first_password == second_password:
                self._config.store_password_hash(second_password)
                self._authenticate_password()

            else:
                self._first_password = None
                self._authenticated_password = None
                # Remove entered password
                self._password_input.value = ""
                ui.notify('First and second passwords do not match. Try again.', type='negative')

        else:
            error_message = self._valid_password(self._password_input.value)
            if error_message is None:
                self._first_password = self._password_input.value
                # Remove entered password
                self._password_input.value = ""
                ui.notify('Initialising valid password. Re-enter password to initialise all data.', type='positive')

            else:
                # Show the error message to the user and restart password setup.
                ui.notify(error_message)

    def _authenticate_password(self):
        """@brief Called when a password has been setup in order to authenticate it."""
        password_entered = self._password_input.value
        stored_password_hash = self._config.get_stored_password_hash()
        valid_password = bcrypt.checkpw(password_entered.encode(), stored_password_hash.encode())
        if valid_password:
            # Use the password entered from the GUI
            self._authenticated_password = password_entered
            self._config.load_config(self._authenticated_password)
            # Got to the
            ui.run_javascript("window.open('/authenticated', '_blank')")

        else:
            ui.notify('Incorrect password.', type='negative')
            # Remove entered password
            self._password_input.value = ""

    def initGUI(self,
                debugEnabled,
                reload=True,
                address='127.0.0.1',
                port=9090):
        self._address = address
        self._port = port
        self._reload = reload

        self._guiLogLevel = "warning"
        if debugEnabled:
            self._guiLogLevel = "debug"

        # If not allow the user to enter the app password.
        # main page (password must be entered to decrypt data/config files)
        @ui.page('/authenticated')
        def password_entered_page():
            if self._authenticated_password:
                self._init_top_level()
                # Called every time this page is displayed
                # i.e when the back button is selected
                self._show_bank_account_list()
                self._show_pension_list()
                self._show_monthly_spending_list()
            else:
                ui.notify('Password required to access this page.', type='negative')

        # We open the password entry page first
        with ui.row():
            ui.label("Retirement Finances").style('font-size: 32px; font-weight: bold;')
        with ui.row():
            ui.label('Password:')
        with ui.row():
            self._password_input = ui.input(password=True).props("autofocus").on("keydown.enter", lambda e: self._open_main_window())
            self._password_input.tooltip("The password must be at least 8 characters long. It must contain upper and lowercase characters with at least one number.")
            self._password_input.value = self._password
        with ui.row():
            ui.button('OK', on_click=self._open_main_window)

        self._show_config_location()

        ui.run(host=address,
               port=port,
               title="Retirement Finances",
               dark=True,
               uvicorn_logging_level=self._guiLogLevel,
               reload=reload)

    def _valid_password(self, password):
        """@brief Check if the password is valid. I.E meets the complexity criteria.
           @param password The password to check.
           @return None if valid password is entered, else it may return an error message."""
        if len(password) < 8:
            return "The password must be at least 8 characters long."
        has_upper = any(char.isupper() for char in password)
        has_lower = any(char.islower() for char in password)
        has_digit = any(char.isdigit() for char in password)

        if not has_upper:
            return "The password must contain at least one upper case character."

        if not has_lower:
            return "The password must contain at least one lower case character."

        if not has_digit:
            return "The password must contain at least one number."

        return None

    def _show_config_location(self, location='top'):
        """@brief Display a message for the user to show where the files are held."""
        msg = f'All files are stored in {self._config.get_config_folder()} folder.'
        with ui.footer().style('height: 60px;'):
            # Put label on left and button on the right.
            with ui.row().classes('w-full justify-between items-center'):
                ui.label(msg)
                with ui.row():
                    ui.label(f"Software Version: {self._program_version}")
                    ui.button('Quit', on_click=self.close).tooltip("Select to shutdown the Retirement Finances program.")

    def close(self):
        """@brief Close down the app server."""
        ui.notify("Server shutting down. Close browser window (click x on browser tab).")
        try:
            app.shutdown()
        except AttributeError:
            pass

    def _init_top_level(self):
        self._load_global_config()

        self._last_selected_bank_account_index = None
        self._last_selected_pension_index = None

        self._backup_data_files(self._config.get_config_folder())

        self._init_dialogs()

        tabNameList = ('Savings',
                       'Pensions',
                       'Monthly Spending',
                       'Reports',
                       'Configuration')
        # This must have the same number of elements as the above list
        tabMethodInitList = [self._init_bank_accounts_tab,
                             self._init_pensions_tab,
                             self._init_monthly_spend_tab,
                             self._init_reports_tab,
                             self._init_config_tab]

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

        self._update_gui_from_config()

        ui.timer(interval=Finances.GUI_TIMER_SECONDS, callback=self.gui_timer_callback)

        self._init_monthly_spending_dialog()

        self._show_config_location(location='bottom')

    def _load_global_config(self):
        self._global_configuration_dict = self._ensure_default_global_config_keys()

        self._savings_owner_list = []
        self._savings_owner_list.append(self._global_configuration_dict[Finances.MY_NAME_FIELD])
        self._savings_owner_list.append(self._global_configuration_dict[Finances.PARTNER_NAME_FIELD])
        self._savings_owner_list.append('Joint')

        self._pension_owner_list = []
        self._pension_owner_list.append(self._global_configuration_dict[Finances.MY_NAME_FIELD])
        self._pension_owner_list.append(self._global_configuration_dict[Finances.PARTNER_NAME_FIELD])

    def _backup_data_files(self, data_folder):
        """@brief Backup files in the data folder.
           @param data_folder The folder containing the data files created by this tool."""
        if os.path.isdir(data_folder):
            backup_folder = os.path.join(data_folder, 'backup')
            if not os.path.isdir(backup_folder):
                os.makedirs(backup_folder)
            timestamp_str = datetime.now().strftime("%Y-%m-%d-%H_%M_%S")
            this_backup_folder = os.path.join(backup_folder, timestamp_str)
            if not os.path.isdir(this_backup_folder):
                os.makedirs(this_backup_folder)
            # Copy the data files to the backup folder
            items = os.listdir(data_folder)
            file_list = [item for item in items if os.path.isfile(os.path.join(data_folder, item))]
            for _file in file_list:
                src_file = os.path.join(data_folder, _file)
                dest_file = os.path.join(this_backup_folder, _file)
                shutil.copy(src_file, dest_file)

        else:
            raise Exception(f"{data_folder} data folder not found.")

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
                       {'name': BankAccountGUI.BALANCE, 'label': BankAccountGUI.BALANCE, 'field': BankAccountGUI.BALANCE}
                       ]
            self._bank_acount_table = ui.table(columns=columns,
                                               rows=[],
                                               row_key=BankAccountGUI.ACCOUNT_NAME_LABEL,
                                               selection='single').style('text-align: left;')
            # .classes('h-96').props('virtual-scroll')

        with ui.row():
            ui.button('Add', on_click=lambda: self._add_bank_account()
                      ).tooltip('Add a bank/building society account')
            ui.button('Delete', on_click=lambda: self._delete_bank_account()).tooltip(
                'Delete a bank/building society account')
            ui.button('Edit', on_click=lambda: self._edit_bank_account()).tooltip(
                'Edit a bank/building society account')
            self._show_only_active_accounts_checkbox = ui.checkbox(
                "Show only active accounts", on_change=self.on_checkbox_change, value=True).tooltip("Deselect to show inactive accounts in the above list.")

        self._show_bank_account_list()

    def on_checkbox_change(self, event):
        show_only_active_accounts = event.value
        self._show_bank_account_list(show_only_active_accounts=show_only_active_accounts)

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
        self._config.remove_bank_account(
            self._last_selected_bank_account_index)
        self._show_bank_account_list()

    def _dialog2_no_button_press(self):
        """@brief Called when dialog 2 no button is selected."""
        self._dialog2.close()

    def _show_bank_account_list(self, show_only_active_accounts=True):
        """@brief Show a table of the configured bank accounts.
           @param show_only_active_accounts If True don't show inactive accounts."""
        if self._bank_acount_table:
            self._bank_acount_table.rows.clear()
            self._bank_acount_table.update()
            bank_accounts_dict_list = self._config.get_bank_accounts_dict_list()
            total = 0
            for bank_account_dict in bank_accounts_dict_list:
                owner = bank_account_dict[BankAccountGUI.ACCOUNT_OWNER]
                bank = bank_account_dict[BankAccountGUI.ACCOUNT_BANK_NAME_LABEL]
                account_name = bank_account_dict[BankAccountGUI.ACCOUNT_NAME_LABEL]
                active_account = bank_account_dict[BankAccountGUI.ACCOUNT_ACTIVE]
                balanceTable = bank_account_dict[BankAccountGUI.TABLE]
                balance = ""
                if active_account:
                    balance = 0
                    if len(balanceTable) > 0:
                        lastRow = balanceTable[-1]
                        if len(lastRow) == 2:
                            balance = float(lastRow[1])
                            total += balance
                show_account = True
                if show_only_active_accounts and not active_account:
                    show_account = False
                if show_account:
                    self._bank_acount_table.add_row({BankAccountGUI.ACCOUNT_OWNER: owner,
                                                     BankAccountGUI.BANK: bank,
                                                     BankAccountGUI.ACCOUNT_NAME_LABEL: account_name,
                                                     BankAccountGUI.BALANCE: f"{balance:.2f}"})
            # Add last empty row to show the totals
            self._bank_acount_table.add_row({BankAccountGUI.ACCOUNT_OWNER: "",
                                             BankAccountGUI.BANK: "",
                                             BankAccountGUI.ACCOUNT_NAME_LABEL: "Total",
                                             BankAccountGUI.BALANCE: f"{total:.2f}"})
            self._bank_acount_table.run_method(
                'scrollTo', len(self._bank_acount_table.rows)-1)

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
            selected_dict = selected_dict[0]
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
        if self._is_my_name_set():
            self._load_global_config()
            self._update_bank_account(True, {})

    def _edit_bank_account(self):
        """@brief Add a bank account."""
        if self._is_my_name_set():
            self._load_global_config()
            bank_account_dict = self._get_selected_bank_account_dict()
            if bank_account_dict:
                self._update_bank_account(False, bank_account_dict)
            else:
                ui.notify("Select a bank account to edit.")

    def _is_my_name_set(self):
        """@return True if my name is set in the global config."""
        set = False
        my_name = self._global_configuration_dict[Finances.MY_NAME_FIELD]
        if my_name and len(my_name) > 0:
            set = True

        if not set:
            ui.notify("Your name is unset in the configuration tab. Set your name, save it then try again.", type='negative')

        return set

    def _update_bank_account(self, add, bank_account_dict):
        """@brief edit bank account details.
           @param add If True then add to the list of available bank accounts.
           @param bank_account_dict A dict holding the bank account details."""
        if isinstance(bank_account_dict, dict):
            # Define a secondary page
            @ui.page('/bank_accounts_page')
            def bank_accounts_page():
                BankAccountGUI(add, bank_account_dict, self._config, self._savings_owner_list)
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
                       {'name': PensionGUI.VALUE, 'label': PensionGUI.VALUE, 'field': PensionGUI.VALUE}
                       ]
            self._pension_table = ui.table(columns=columns,
                                           rows=[],
                                           row_key='Description',
                                           selection='single').classes('h-96').props('virtual-scroll')
            self._show_pension_list()

        with ui.row():
            ui.button('Add', on_click=lambda: self._add_pension()
                      ).tooltip('Add a pension')
            ui.button('Delete', on_click=lambda: self._delete_pension()).tooltip(
                'Delete a pension')
            ui.button('Edit', on_click=lambda: self._edit_pension()
                      ).tooltip('Edit a pension')

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
        if self._pension_table:
            self._pension_table.rows.clear()
            self._pension_table.update()
            pension_dict_list = self._config.get_pension_dict_list()
            total = 0
            for pension_dict in pension_dict_list:
                provider = pension_dict[PensionGUI.PENSION_PROVIDER_LABEL]
                description = pension_dict[PensionGUI.PENSION_DESCRIPTION_LABEL]
                owner = pension_dict[PensionGUI.PENSION_OWNER_LABEL]
                statePension = pension_dict[PensionGUI.STATE_PENSION]
                value = ""
                if not statePension:
                    value = 0
                    # We assume the last row in the table is the most up to date
                    valueTable = pension_dict[PensionGUI.PENSION_TABLE]
                    if len(valueTable) > 0:
                        lastRow = valueTable[-1]
                        if len(lastRow) == 2:
                            value = lastRow[1]
                            total += value

                self._pension_table.add_row({PensionGUI.PENSION_PROVIDER_LABEL: provider,
                                             PensionGUI.PENSION_DESCRIPTION_LABEL: description,
                                             PensionGUI.PENSION_OWNER_LABEL: owner,
                                             PensionGUI.VALUE: value})

            # Add last empty row to show the totals
            self._pension_table.add_row({PensionGUI.PENSION_PROVIDER_LABEL: "",
                                         PensionGUI.PENSION_DESCRIPTION_LABEL: "",
                                         PensionGUI.PENSION_OWNER_LABEL: "Total",
                                         PensionGUI.VALUE: f"{total:.2f}"})

            self._pension_table.run_method(
                'scrollTo', len(self._bank_acount_table.rows)-1)

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
            selected_dict = selected_dict[0]
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
        if self._is_my_name_set():
            self._load_global_config()
            self._update_pension(True, {})

    def _edit_pension(self):
        """@brief Add a pension."""
        if self._is_my_name_set():
            self._load_global_config()
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
                PensionGUI(add, pension_dict, self._config, self._pension_owner_list)
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
                    row_dict[key] = value
                    column_index = column_index + 1
                self._table_dialog_table.add_row(row_dict)

            with ui.row():
                ui.button('OK', on_click=self._table_dialog_ok_button_selected)

    def _table_dialog_ok_button_selected(self):
        self._table_dialog.close()

    # methods associated with the monthly spending

    MONTHLY_SPEND_DATE = "Date"
    MONTHLY_SPEND_AMOUNT = "Amount"
    MONTHLY_SPENDING_TABLE = "MONTHLY_SPENDING_TABLE"
    MONTHLY_SPENDING_NOTES = "Notes"

    def _init_monthly_spend_tab(self):
        with ui.row():
            with ui.column().tooltip("Add the amounts you actually spend each month here for your reference to compare with your predictions."):
                columns = [{'name': Finances.MONTHLY_SPEND_DATE, 'label': Finances.MONTHLY_SPEND_DATE, 'field': Finances.MONTHLY_SPEND_DATE},
                           {'name': Finances.MONTHLY_SPEND_AMOUNT, 'label': Finances.MONTHLY_SPEND_AMOUNT, 'field': Finances.MONTHLY_SPEND_AMOUNT}]
                self._monthly_spend_table = ui.table(columns=columns,
                                                     rows=[],
                                                     row_key=Finances.MONTHLY_SPEND_DATE,
                                                     selection='single').classes('h-96').props('virtual-scroll')
                self._show_monthly_spending_list()

            monthly_spending_dict = self._get_monthly_spending_dict()

            self._information_field = ui.textarea(label=Finances.MONTHLY_SPENDING_NOTES,
                                                  value=monthly_spending_dict[Finances.MONTHLY_SPENDING_NOTES])
            self._information_field.on('keydown', self._monthly_spend_notes_keypress)
            self._information_field.style('width: 600px;')
            self._information_field.tooltip("Notes on monthly spending.")

        with ui.row():
            ui.button('Add', on_click=lambda: self._add_monthly_spending()
                      ).tooltip('Add to monthly spending table')
            ui.button('Delete', on_click=lambda: self._delete_monthly_spending()).tooltip(
                'Delete from monthly spending table')
            ui.button('Edit', on_click=lambda: self._edit_monthly_spending()
                      ).tooltip('Edit monthly spending table')

    def _monthly_spend_notes_keypress(self, event):
        """@brief Called every time the user presses a key in the notes field to
                  persistently save the contents of the nmotes field."""
        monthly_spending_dict = self._get_monthly_spending_dict()
        if Finances.MONTHLY_SPENDING_NOTES in monthly_spending_dict:
            monthly_spending_dict[Finances.MONTHLY_SPENDING_NOTES] = self._information_field.value + event.args.get('key')
            self._config._save_monthly_spending_dict()

    def _add_monthly_spending(self):
        """@brief Add to the monthly spending table."""
        self._add_to_monthly_spending_table = True
        self._add_monthly_spend_row_dialog.open()

    def _delete_monthly_spending(self):
        """@brief Delete from the monthly spending table."""
        selected_index = self._get_monthly_spending_index()
        monthly_spending_dict = self._get_monthly_spending_dict()
        if selected_index >= 0 and Finances.MONTHLY_SPENDING_TABLE in monthly_spending_dict:
            monthly_spending_table = monthly_spending_dict[Finances.MONTHLY_SPENDING_TABLE]
            if selected_index < len(monthly_spending_table):
                del monthly_spending_table[selected_index]
                self._config._save_monthly_spending_dict()
                self._show_monthly_spending_list()

    def _get_monthly_spending_index(self):
        selected_index = -1
        selected_dict = self._monthly_spend_table.selected
        if len(selected_dict) > 0:
            selected_dict = selected_dict[0]
            monthly_spending_dict = self._get_monthly_spending_dict()
            if Finances.MONTHLY_SPENDING_TABLE in monthly_spending_dict:
                monthly_spending_table = monthly_spending_dict[Finances.MONTHLY_SPENDING_TABLE]
                if selected_dict:
                    if Finances.MONTHLY_SPEND_DATE in selected_dict:
                        _date = selected_dict[Finances.MONTHLY_SPEND_DATE]
                        current_index = 0
                        for row in monthly_spending_table:
                            if len(row) == 2:
                                __date = row[0]
                                if _date == __date:
                                    selected_index = current_index
                                    break
                            current_index += 1

        return selected_index

    def _edit_monthly_spending(self):
        """@brief Edit the monthly spending table."""
        self._add_to_monthly_spending_table = False
        monthly_spending_dict = self._get_monthly_spending_dict()
        selected_index = self._get_monthly_spending_index()
        if selected_index >= 0 and Finances.MONTHLY_SPENDING_TABLE in monthly_spending_dict:
            monthly_spending_table = monthly_spending_dict[Finances.MONTHLY_SPENDING_TABLE]
            if selected_index < len(monthly_spending_table):
                row = monthly_spending_table[selected_index]
                self._monthly_spending_date_input_field.value = row[0]
                self._monthly_spending_amount_field.value = row[1]
                self._add_monthly_spend_row_dialog.open()

    def _show_monthly_spending_list(self):
        """@brief Display the monthly spending list."""
        if self._monthly_spend_table:
            self._monthly_spend_table.rows.clear()
            self._monthly_spend_table.update()
            monthly_spending_dict = self._get_monthly_spending_dict()
            if Finances.MONTHLY_SPENDING_TABLE in monthly_spending_dict:
                monthly_spending_table = monthly_spending_dict[Finances.MONTHLY_SPENDING_TABLE]
                for row in monthly_spending_table:
                    if len(row) >= 2:
                        _date = row[0]
                        _amount = row[1]
                        self._monthly_spend_table.add_row({Finances.MONTHLY_SPEND_DATE: _date,
                                                           Finances.MONTHLY_SPEND_AMOUNT: _amount})
            self._monthly_spend_table.run_method('scrollTo', len(self._monthly_spend_table.rows)-1)

    def _get_monthly_spending_dict(self):
        """@brief Get the dict that holds the monthly spending."""
        monthly_spending_dict = self._config.get_monthly_spending_dict()
        if Finances.MONTHLY_SPENDING_TABLE not in monthly_spending_dict:
            monthly_spending_dict[Finances.MONTHLY_SPENDING_TABLE] = []

        if Finances.MONTHLY_SPENDING_NOTES not in monthly_spending_dict:
            monthly_spending_dict[Finances.MONTHLY_SPENDING_NOTES] = ""

        return monthly_spending_dict

    def _init_monthly_spending_dialog(self):
        """@brief Create a dialog presented to the user to check that they wish to add a bank account."""
        with ui.dialog() as self._add_monthly_spend_row_dialog, ui.card().style('width: 400px;'):
            self._monthly_spending_date_input_field = GUIBase.GetInputDateField(Finances.MONTHLY_SPEND_DATE)
            self._monthly_spending_amount_field = ui.number(label="Amount (£)")
            with ui.row():
                ui.button("Ok", on_click=self._monthly_spending_ok_button_press)
                ui.button("Cancel", on_click=self._monthly_spending_cancel_button_press)

    def _monthly_spending_ok_button_press(self):
        """@brief Add the monthly spending amount to the table."""
        if Finances.CheckValidDateString(self._monthly_spending_date_input_field.value) and \
           self._monthly_spending_amount_field.value >= 0:
            monthly_spending_dict = self._config.get_monthly_spending_dict()
            if Finances.MONTHLY_SPENDING_TABLE in monthly_spending_dict:
                rows = monthly_spending_dict[Finances.MONTHLY_SPENDING_TABLE]
                if self._add_to_monthly_spending_table:
                    rows.append((self._monthly_spending_date_input_field.value, self._monthly_spending_amount_field.value))
                else:
                    selected_index = self._get_monthly_spending_index()
                    rows[selected_index] = (self._monthly_spending_date_input_field.value, self._monthly_spending_amount_field.value)

                # Ensure we store the table in ascending date order.
                sorted_rows = sorted(rows, key=lambda row: datetime.strptime(row[0], "%d-%m-%Y"))
                monthly_spending_dict[Finances.MONTHLY_SPENDING_TABLE] = sorted_rows
                self._config._save_monthly_spending_dict()

            self._show_monthly_spending_list()
        self._add_monthly_spend_row_dialog.close()

    def _monthly_spending_cancel_button_press(self):
        self._add_monthly_spend_row_dialog.close()

    # end of methods associated with the monthly spending

    def _init_reports_tab(self):
        with ui.row():
            ui.button('Totals', on_click=lambda: self._show_totals()).tooltip(
                'Show the current savings and pension totals.')
        with ui.row():
            ui.button('Drawdown Retirement Prediction', on_click=lambda: self._future_plot()).tooltip(
                'Show how your finances could increase/decrease in the future.')

    def _init_config_tab(self):
        self._my_name_field = ui.input(label=Finances.MY_NAME_FIELD).style('width: 300px;').tooltip('Enter your name here.')
        self._partner_name_field = ui.input(label=Finances.PARTNER_NAME_FIELD).style('width: 300px;').tooltip('If you have a partner you may enter their name here if you wish to combine your finances.')
        with ui.row():
            ui.button('Save', on_click=self._save_config_button_selected)

    def _save_config_button_selected(self):
        """@brief Save configuration."""
        self._update_config_from_gui()
        self._config.save_global_configuration()
        ui.notify('Saved Configuration.', type='positive', position='bottom')

    def _ensure_default_global_config_keys(self):
        self._config.load_global_configuration()
        global_configuration_dict = self._config.get_global_configuration_dict()
        if Finances.MY_NAME_FIELD not in global_configuration_dict:
            global_configuration_dict[Finances.MY_NAME_FIELD] = ""

        if Finances.PARTNER_NAME_FIELD not in global_configuration_dict:
            global_configuration_dict[Finances.PARTNER_NAME_FIELD] = ""

        return global_configuration_dict

    def _update_gui_from_config(self):
        """@brief Update GUI from the configuration."""
        self._my_name_field.value = self._global_configuration_dict[Finances.MY_NAME_FIELD]
        self._partner_name_field.value = self._global_configuration_dict[Finances.PARTNER_NAME_FIELD]

    def _update_config_from_gui(self):
        """@brief Update configuration from the GUI."""
        self._global_configuration_dict[Finances.MY_NAME_FIELD] = self._my_name_field.value
        self._global_configuration_dict[Finances.PARTNER_NAME_FIELD] = self._partner_name_field.value

    def _show_totals(self):
        """@brief Show details of the total savings and pensions."""
        bank_accounts_dict_list = self._config.get_bank_accounts_dict_list()
        pension_dict_list = self._config.get_pension_dict_list()

        savings_total = 0.0
        for bank_accounts_dict in bank_accounts_dict_list:
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

    def _future_plot(self):
        """@brief Plot our financial future based on given parameters."""
        # Define a secondary page
        @ui.page('/future_plot_page')
        def future_plot_page():
            FuturePlotGUI(self._config, self._pension_owner_list)
        # This will open in a separate browser window
        ui.run_javascript("window.open('/future_plot_page', '_blank')")


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

    def __init__(self, add, bank_account_dict, config, owner_list):
        """@brief Constructor.
           @param add If True then add to the list of available bank accounts.
           @param bank_account_dict A dict holding the bank account details.
           @param config A Config instance.
           @param owner_list A list of savings account owners."""
        self._add = add

        self._bank_account_dict = self._ensure_default_bank_account_keys(bank_account_dict)
        self._config = config
        self._owner_list = owner_list
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
        ui.label("Savings Account").style(
            'font-size: 32px; font-weight: bold;')
        with ui.row():
            bank_active_checkbox = ui.checkbox(
                BankAccountGUI.ACCOUNT_ACTIVE, value=True).tooltip("Deselect this if this account should not be included in retirement planning finances.")

        with ui.row():
            bank_account_bank_name_field = ui.input(
                label=BankAccountGUI.ACCOUNT_BANK_NAME_LABEL).style('width: 300px;').tooltip("The name of the institution where the account is held.")
            bank_account_name_field = ui.input(
                label=BankAccountGUI.ACCOUNT_NAME_LABEL).style('width: 300px;').tooltip("The name of the savings account.")
            bank_account_sort_code_field = ui.input(
                label=BankAccountGUI.ACCOUNT_SORT_CODE).style('width: 100px;').tooltip("The sort code of the savings account. Savings accounts may not have a sort code.")
            bank_account_number_field = ui.input(
                label=BankAccountGUI.ACCOUNT_NUMBER).style('width: 200px;').tooltip("The account number of the savings account.")

        with ui.row():
            bank_account_owner_select = ui.select(self._owner_list,
                                                  label=BankAccountGUI.ACCOUNT_OWNER,
                                                  value=self._owner_list[0]).style('width: 200px;').tooltip("The owner of the savings account.")

            bank_account_interest_rate_field = ui.number(
                label=BankAccountGUI.ACCOUNT_INTEREST_RATE, min=0, max=100).style('width: 150px;').tooltip("The rate of interest for this savings account when the account was opened. This is for your reference only and is not used in calculations.")
            bank_account_interest_type_field = ui.select(
                ['Fixed', 'Variable'], value='Fixed')
            bank_account_interest_type_field.tooltip(
                BankAccountGUI.ACCOUNT_INTEREST_RATE_TYPE)
            bank_account_open_date_field = Finances.GetInputDateField(
                BankAccountGUI.ACCOUNT_OPEN_DATE).tooltip("The date that the savings account was opened.")

        with ui.row():
            bank_notes_field = ui.textarea(
                label=BankAccountGUI.ACCOUNT_NOTES).style('width: 800px;').tooltip("Any notes you may wish to record regarding this savings acount.")

        with ui.card().style("height: 300px; overflow-y: auto;"):
            self._table = self._get_table_copy()
            with ui.row():
                columns = [{'name': BankAccountGUI.DATE, 'label': BankAccountGUI.DATE, 'field': BankAccountGUI.DATE},
                           {'name': BankAccountGUI.BALANCE, 'label': BankAccountGUI.BALANCE,
                               'field': BankAccountGUI.BALANCE},
                           ]
                self._bank_acount_table = ui.table(columns=columns,
                                                   rows=[],
                                                   row_key=BankAccountGUI.DATE,
                                                   selection='single')

                self._display_table_rows()

        with ui.row():
            ui.button("Add", on_click=self._add_button_handler).tooltip(
                'Add a row to the balance table.')
            ui.button("Delete", on_click=self._delete_button_handler).tooltip(
                'Delete a row from the balance table.')

        with ui.row():
            ui.button("Save", on_click=self._save_button_selected).tooltip("Save the account details.")
            ui.button("Back", on_click=lambda: ui.navigate.back()).tooltip("Go back to previous window.")

        self._bank_account_field_list = [bank_account_bank_name_field,
                                         bank_account_name_field,
                                         bank_account_sort_code_field,
                                         bank_account_number_field,
                                         bank_account_owner_select,
                                         bank_account_open_date_field,
                                         bank_account_interest_rate_field,
                                         bank_account_interest_type_field,
                                         bank_active_checkbox,
                                         bank_notes_field]

    def _save_button_selected(self):
        """@brief Called when the back button is selected."""
        if self._update_bank_account_from_gui():
            ui.notify('Saved savings account details.', type='positive', position='bottom')

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
        rows = self._bank_account_dict[BankAccountGUI.TABLE]
        rows.append(row)
        # Sort table in ascending date order
        sorted_rows = sorted(rows, key=lambda row: datetime.strptime(row[0], "%d-%m-%Y"))
        self._bank_account_dict[BankAccountGUI.TABLE] = sorted_rows

    def _init_add_row_dialog(self):
        """@brief Create a dialog presented to the user to check that they wish to add a bank account."""
        with ui.dialog() as self._add_row_dialog, ui.card().style('width: 400px;'):
            self._date_input_field = GUIBase.GetInputDateField(
                BankAccountGUI.DATE)
            self._amount_field = ui.number(label="Balance (£)")
            with ui.row():
                ui.button("Ok", on_click=self._add_row_dialog_ok_button_press)
                ui.button(
                    "Cancel", on_click=self._add_row_dialog_cancel_button_press)

    def _add_row_dialog_ok_button_press(self):
        self._add_row_dialog.close()
        if BankAccountGUI.CheckValidDateString(self._date_input_field.value,
                                               field_name=self._date_input_field.props['label']) and \
           BankAccountGUI.CheckGreaterThanZero(self._amount_field.value,
                                               field_name=self._amount_field.props['label']) and \
           BankAccountGUI.CheckDuplicateDate(self._bank_account_dict[BankAccountGUI.TABLE], self._date_input_field.value):
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
                found_field = False
                properties = input_field.props
                if 'label' in properties:
                    label = input_field.props['label']
                    if label == BankAccountGUI.ACCOUNT_OWNER:
                        input_field.value = self._bank_account_dict[BankAccountGUI.ACCOUNT_OWNER]
                        found_field = True

                # If not found we assume this is the interest rate type field as this is the only other ui.select
                # field in the bank account GUI.
                if not found_field:
                    input_field.value = self._bank_account_dict[BankAccountGUI.ACCOUNT_INTEREST_RATE_TYPE]

            elif isinstance(input_field, ui.checkbox):
                input_field.value = self._bank_account_dict[BankAccountGUI.ACCOUNT_ACTIVE]

            else:
                props = input_field._props
                key = props['label']
                input_field.value = self._bank_account_dict[key]

    def _update_bank_account_from_gui(self):
        """@brief Update the bank account dict. from the GUI fields.
           @return True if enough fields have been filled in to make the bank account valid."""
        valid = False
        # Do some checks on the values entered.
        if len(self._bank_account_field_list[0].value) == 0:
            ui.notify("Bank/Building society name must be entered.")

        elif len(self._bank_account_field_list[1].value) == 0:
            ui.notify("Account name must be entered.")

        elif BankAccountGUI.CheckValidDateString(self._bank_account_field_list[5].value,
                                                 field_name=self._bank_account_field_list[5].props['label']):
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
            valid = True

        return valid


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
    PENSION_OWNER = "Owner"
    VALUE = "Value (£)"

    def __init__(self, add, pension_dict, config, owner_list):
        """@brief Constructor.
           @param add If True then add to the list of available bank accounts.
           @param pension_dict A dict holding the pension details.
           @param config A Config instance.
           @param owner_list A list of pension owners."""
        self._add = add
        self._pension_dict = self._ensure_default_pension_keys(pension_dict)
        self._config = config
        self._owner_list = owner_list
        self._init_add_row_dialog()
        self._init_page()

    def _ensure_default_pension_keys(self, pension_dict):
        """@brief Ensure the pension dict has the required keys."""
        if PensionGUI.STATE_PENSION not in pension_dict:
            pension_dict[PensionGUI.STATE_PENSION] = False

        if PensionGUI.PENSION_PROVIDER_LABEL not in pension_dict:
            pension_dict[PensionGUI.PENSION_PROVIDER_LABEL] = ""

        if PensionGUI.PENSION_DESCRIPTION_LABEL not in pension_dict:
            pension_dict[PensionGUI.PENSION_DESCRIPTION_LABEL] = ""

        if PensionGUI.PENSION_OWNER_LABEL not in pension_dict:
            pension_dict[PensionGUI.PENSION_OWNER_LABEL] = ""

        if PensionGUI.STATE_PENSION_START_DATE not in pension_dict:
            pension_dict[PensionGUI.STATE_PENSION_START_DATE] = ""

        if PensionGUI.PENSION_TABLE not in pension_dict:
            pension_dict[PensionGUI.PENSION_TABLE] = []

        return pension_dict

    def _init_page(self):
        ui.label("Pension").style('font-size: 32px; font-weight: bold;')
        self._state_pension_checkbox = ui.checkbox(PensionGUI.STATE_PENSION, value=False).on(
            'click', self._state_pension_checkbox_callback).tooltip("This should be checked if this is a state pension. If not then this should be unchecked.")
        self._provider_field = ui.input(
            label=PensionGUI.PENSION_PROVIDER_LABEL, value="").tooltip("The name of the pension provider.")
        self._description_field = ui.input(
            label=PensionGUI.PENSION_DESCRIPTION_LABEL, value="").style('width: 400px;').tooltip("A description of the pension.")
        self._state_pension_state_date_field = GUIBase.GetInputDateField(
            PensionGUI.STATE_PENSION_START_DATE)
        self._pension_owner_field = ui.select(self._owner_list,
                                              label=PensionGUI.PENSION_OWNER,
                                              value=self._owner_list[0]).style('width: 200px;').tooltip("The name of the pension owner.")

        with ui.card().style("height: 300px; overflow-y: auto;").tooltip("If a state pension the amount should be the yearly expected state pension. If not a state pension, then the amount should be the pension fund value."):
            self._table = self._get_table_copy()
            with ui.row():
                columns = [{'name': PensionGUI.DATE, 'label': PensionGUI.DATE, 'field': PensionGUI.DATE},
                           {'name': PensionGUI.AMOUNT, 'label': PensionGUI.AMOUNT,
                               'field': PensionGUI.AMOUNT},
                           ]
                self._pension_table = ui.table(columns=columns,
                                               rows=[],
                                               row_key=PensionGUI.DATE,
                                               selection='single')

        self._update_gui_from_pension()

        with ui.row():
            ui.button("Add", on_click=self._add_button_handler).tooltip(
                'Add a row to the pension table.')
            ui.button("Delete", on_click=self._delete_button_handler).tooltip(
                'Delete a row from the pension table.')

        with ui.row():
            ui.button("Save", on_click=self._save_button_selected).tooltip("Save the pension details.")
            ui.button("Back", on_click=lambda: ui.navigate.back()).tooltip("Go back to previous window.")

    def _save_button_selected(self):
        """@brief Called when the back button is selected."""
        if self._update_pension_from_gui():
            ui.notify('Saved pension account details.', type='positive', position='bottom')

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
        # Ensure state pension field/s are enabled if checkbox is selected
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
            self._pension_table.add_row(
                {PensionGUI.DATE: row[0], PensionGUI.AMOUNT: row[1]})
        self._pension_table.run_method(
            'scrollTo', len(self._pension_table.rows)-1)

    def _init_add_row_dialog(self):
        """@brief Create a dialog presented to the user to check that they wish to add a pension value."""
        with ui.dialog() as self._add_row_dialog, ui.card().style('width: 400px;'):
            self._date_input_field = GUIBase.GetInputDateField(PensionGUI.DATE)
            self._amount_field = ui.number(label=PensionGUI.AMOUNT)
            with ui.row():
                ui.button("Ok", on_click=self._add_row_dialog_ok_button_press)
                ui.button(
                    "Cancel", on_click=self._add_row_dialog_cancel_button_press)

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
        rows = self._pension_dict[PensionGUI.PENSION_TABLE]
        rows.append(row)
        # Sort table in ascending date order
        sorted_rows = sorted(rows, key=lambda row: datetime.strptime(row[0], "%d-%m-%Y"))
        self._pension_dict[PensionGUI.PENSION_TABLE] = sorted_rows

    def _add_row_dialog_ok_button_press(self):
        self._add_row_dialog.close()
        if PensionGUI.CheckValidDateString(self._date_input_field.value,
                                           field_name=self._date_input_field.props['label']) and \
           PensionGUI.CheckGreaterThanZero(self._amount_field.value,
                                           field_name=self._amount_field.props['label']) and \
           PensionGUI.CheckDuplicateDate(self._pension_dict[PensionGUI.PENSION_TABLE], self._date_input_field.value):
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
        """@brief Update the pension dict from the GUI fields.
           @return True if required fields have been entered."""
        valid = False
        duplicate_description = False
        if self._add:
            pension_dict_list = self._config.get_pension_dict_list()
            for pension_dict in pension_dict_list:
                if PensionGUI.PENSION_DESCRIPTION_LABEL in pension_dict:
                    _descrip = pension_dict[PensionGUI.PENSION_DESCRIPTION_LABEL]
                    if _descrip == self._description_field.value:
                        duplicate_description = True

        self._state_pension_checkbox_callback()

        state_pension = self._state_pension_checkbox.value

        valid_pension_start_date = False
        if state_pension:
            valid_pension_start_date = BankAccountGUI.CheckValidDateString(self._state_pension_state_date_field.value,
                                                                           field_name=self._state_pension_state_date_field.props['label'])

        if len(self._description_field.value) == 0:
            ui.notify("No description entry.", type='negative')

        elif self._pension_owner_field.value is None:
            ui.notify("Owner field not set.", type='negative')

        elif duplicate_description:
            ui.notify(f"A pension with this description ('{_descrip}') is already present.", type='negative')

        elif state_pension and not valid_pension_start_date:
            # Error message already displayed
            pass

        else:

            self._pension_dict[PensionGUI.STATE_PENSION] = state_pension
            self._pension_dict[PensionGUI.PENSION_PROVIDER_LABEL] = self._provider_field.value
            self._pension_dict[PensionGUI.PENSION_DESCRIPTION_LABEL] = self._description_field.value
            self._pension_dict[PensionGUI.PENSION_OWNER_LABEL] = self._pension_owner_field.value
            self._pension_dict[PensionGUI.STATE_PENSION_START_DATE] = self._state_pension_state_date_field.value

            if self._add:
                self._config.add_pension(self._pension_dict)

            self._config.save_pensions()

            valid = True

        return valid


class FuturePlotGUI(GUIBase):
    """@brief Responsible for allowing the user to plot predictions about the way the savings and pensions will fare during retirement."""
    DEFAULT_MALE_MAX_AGE = 90
    # The default initial monthly budget/income including any monthly income from other sources
    DEFAULT_MONTHLY_INCOME = 0
    DEFAULT_MONTHLY_AMOUNT_FROM_OTHER_SOURCES = 0
    # Default list of savings interest rates and pension growth rates.
    DEFAULT_RATE_LIST = ""
    DEFAULT_YEARLY_INCREASE_IN_INCOME = ""
    DEFAULT_STATE_PENSION_YEARLY_INCREASE = DEFAULT_YEARLY_INCREASE_IN_INCOME
    MY_MAX_AGE = "My max age"
    MY_DATE_OF_BIRTH = "My date of birth"
    PARTNER_MAX_AGE = "Partner max age"
    PARTNER_DATE_OF_BIRTH = "Partner date of birth"
    SAVINGS_INTEREST_RATE_LIST = "Savings interest rate (%)"
    PENSION_GROWTH_RATE_LIST = "Pension growth rate (%)"
    STATE_PENSION_YEARLY_INCREASE_LIST = "State pension yearly increase (%)"
    MONTHLY_AMOUNT_FROM_OTHER_SOURCES = "Monthly from other sources (£)"
    MONTHLY_INCOME = "Monthly budget/income (£)"
    YEARLY_INCREASE_IN_INCOME = "Yearly budget/income increase (%)"
    REPORT_START_DATE = "Prediction start date"
    ENABLE_PENSION_DRAWDOWN_START_DATE = "Enable pension drawdown start date"
    PENSION_DRAWDOWN_START_DATE = "Pension drawdown start date"

    DATE = BankAccountGUI.DATE
    AMOUNT = "Amount"

    SAVINGS_WITHDRAWAL_TABLE = "Savings withdrawal table"
    PENSION_WITHDRAWAL_TABLE = "Pensions withdrawal table"
    ADD_SAVINGS_WITHDRAWAL_BUTTON = "Add savings withdrawal"
    DEL_SAVINGS_WITHDRAWAL_BUTTON = "Delete savings withdrawal"
    ADD_PENSION_WITHDRAWAL_BUTTON = "Add pension withdrawal"
    DEL_PENSION_WITHDRAWAL_BUTTON = "Delete pension withdrawal"

    RETIREMENT_PREDICTION_SETTINGS_NAME = "Retirement prediction settings name"
    DEFAULT = "Default"

    YEARLY = 'Yearly'
    MONTHLY = 'Monthly'

    BY_MONTH = "By Month"
    BY_YEAR = "By Year"

    @staticmethod
    def GetDateTimeList(start_datetime, stop_datetime):
        """@brief Get a list of datetime instances (by month) starting from the start of the current month
                  for every month up to and including the stop_datetime.
           @param start_datetime The start datetime for the first datetime instance.
           @param stop_datetime The datetime instance for the last datetime."""
        current_date = start_datetime
        current_date = current_date.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0)
        date_list = []
        while current_date <= stop_datetime:
            date_list.append(current_date)
            current_date += relativedelta(months=+1)
        return date_list

    @staticmethod
    def Datetime2String(_datetime):
        return _datetime.strftime("%Y-%m-%d %H:%M:%S")

    def __init__(self, config, pension_owner_list):
        self._config = config
        self._pension_owner_list = pension_owner_list
        self._last_pp_year = None
        self._future_plot_attr_dict = self._ensure_keys_present()
        self._init_gui()
        self._init_add_row_dialog()
        self._init_ok_to_delete_dialog()
        self._report_start_date = None

    def _ensure_keys_present(self):
        """@brief Ensure the required keys are present in the config dict that relate to the future plot attrs."""
        future_plot_attr_dict = self._config.get_future_plot_attrs_dict()

        if FuturePlotGUI.MY_DATE_OF_BIRTH not in future_plot_attr_dict:
            future_plot_attr_dict[FuturePlotGUI.MY_DATE_OF_BIRTH] = ""

        if FuturePlotGUI.MY_MAX_AGE not in future_plot_attr_dict:
            future_plot_attr_dict[FuturePlotGUI.MY_MAX_AGE] = FuturePlotGUI.DEFAULT_MALE_MAX_AGE

        if FuturePlotGUI.PARTNER_DATE_OF_BIRTH not in future_plot_attr_dict:
            future_plot_attr_dict[FuturePlotGUI.PARTNER_DATE_OF_BIRTH] = ""

        if FuturePlotGUI.PARTNER_MAX_AGE not in future_plot_attr_dict:
            future_plot_attr_dict[FuturePlotGUI.PARTNER_MAX_AGE] = FuturePlotGUI.DEFAULT_MALE_MAX_AGE + 4

        if FuturePlotGUI.SAVINGS_INTEREST_RATE_LIST not in future_plot_attr_dict:
            future_plot_attr_dict[FuturePlotGUI.SAVINGS_INTEREST_RATE_LIST] = FuturePlotGUI.DEFAULT_RATE_LIST

        if FuturePlotGUI.PENSION_GROWTH_RATE_LIST not in future_plot_attr_dict:
            future_plot_attr_dict[FuturePlotGUI.PENSION_GROWTH_RATE_LIST] = FuturePlotGUI.DEFAULT_RATE_LIST

        if FuturePlotGUI.MONTHLY_AMOUNT_FROM_OTHER_SOURCES not in future_plot_attr_dict:
            future_plot_attr_dict[FuturePlotGUI.MONTHLY_AMOUNT_FROM_OTHER_SOURCES] = FuturePlotGUI.DEFAULT_MONTHLY_AMOUNT_FROM_OTHER_SOURCES

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

        if FuturePlotGUI.ENABLE_PENSION_DRAWDOWN_START_DATE not in future_plot_attr_dict:
            future_plot_attr_dict[FuturePlotGUI.ENABLE_PENSION_DRAWDOWN_START_DATE] = False

        if FuturePlotGUI.SAVINGS_WITHDRAWAL_TABLE not in future_plot_attr_dict:
            future_plot_attr_dict[FuturePlotGUI.SAVINGS_WITHDRAWAL_TABLE] = []

        if FuturePlotGUI.PENSION_WITHDRAWAL_TABLE not in future_plot_attr_dict:
            future_plot_attr_dict[FuturePlotGUI.PENSION_WITHDRAWAL_TABLE] = []

        return future_plot_attr_dict

    def _get_selected_retirement_predictions_settings_name(self):
        """@brief Get the name of the selected retirement predictions settings."""
        selected_retirement_parameters_name_dict = self._config.get_selected_retirement_parameters_name_dict()
        if FuturePlotGUI.RETIREMENT_PREDICTION_SETTINGS_NAME not in selected_retirement_parameters_name_dict:
            selected_retirement_parameters_name_dict[FuturePlotGUI.RETIREMENT_PREDICTION_SETTINGS_NAME] = FuturePlotGUI.DEFAULT
        return selected_retirement_parameters_name_dict[FuturePlotGUI.RETIREMENT_PREDICTION_SETTINGS_NAME]

    def _set_selected_retirement_predictions_settings_name(self, name):
        """@brief Set the name of the selected retirement prediction settings.
           @param name The name of the settings."""
        selected_retirement_parameters_name_dict = self._config.get_selected_retirement_parameters_name_dict()
        selected_retirement_parameters_name_dict[FuturePlotGUI.RETIREMENT_PREDICTION_SETTINGS_NAME] = name
        self._config._save_selected_retirement_parameters_name_attrs()

    def _enable_pension_drawdown_callback(self, checkbox):
        if checkbox.value:
            self._pension_drawdown_start_date_field.enable()
        else:
            self._pension_drawdown_start_date_field.disable()

    def _init_gui(self):
        with ui.row():
            ui.label("Drawdown Retirement Prediction").style('font-size: 32px; font-weight: bold;')
        with ui.row():
            ui.label(
                "The following parameters can be changed to alter your retirement prediction.")

        with ui.row():
            with ui.column():
                with ui.row():
                    self._my_dob_field = GUIBase.GetInputDateField(FuturePlotGUI.MY_DATE_OF_BIRTH)
                    my_dob = self._future_plot_attr_dict[FuturePlotGUI.MY_DATE_OF_BIRTH]
                    self._my_dob_field.value = my_dob
                    my_max_age = self._future_plot_attr_dict[FuturePlotGUI.MY_MAX_AGE]
                    self._my_max_age_field = ui.number(label=FuturePlotGUI.MY_MAX_AGE, value=my_max_age).tooltip("The maximum age to plan for.")

                    self._partner_dob_field = GUIBase.GetInputDateField(FuturePlotGUI.PARTNER_DATE_OF_BIRTH)
                    partner_dob = self._future_plot_attr_dict[FuturePlotGUI.PARTNER_DATE_OF_BIRTH]
                    self._partner_dob_field.value = partner_dob
                    partner_max_age = self._future_plot_attr_dict[FuturePlotGUI.PARTNER_MAX_AGE]
                    self._partner_max_age_field = ui.number(label=FuturePlotGUI.PARTNER_MAX_AGE, value=partner_max_age).tooltip("The maximum age to plan for.")

                with ui.row():
                    self._start_date_field = GUIBase.GetInputDateField(FuturePlotGUI.REPORT_START_DATE).tooltip('The first date to be plotted.').tooltip(
                        'The prediction start date is when you stop earning and live from your savings and pensions.')

                    tt = 'Enable/Disable the pension drawdown start date. When enabled monthly pension drawdown starts on this date to meet your budget/income.'
                    self._enable_pension_drawdown_start_date = ui.checkbox('', on_change=self._enable_pension_drawdown_callback).tooltip(tt)
                    self._pension_drawdown_start_date_field = GUIBase.GetInputDateField(FuturePlotGUI.PENSION_DRAWDOWN_START_DATE).style(
                        'width: 300px;').tooltip('The date at which we stop drawing out of savings and start regularly drawing money out of pensions '
                                                 'to cover monthly spending. You may add planned withdrawals from your pension/s before this date in '
                                                 'the Pension withdrawals table if you wish.')
                    self._pension_drawdown_start_date_field.disable()

                with ui.row():
                    monthly_income = self._future_plot_attr_dict[FuturePlotGUI.MONTHLY_INCOME]
                    self._monthly_income_field = ui.number(label=FuturePlotGUI.MONTHLY_INCOME, value=monthly_income).tooltip(
                        'The total monthly budget/income target amount including money from other sources. This is taken from savings prior to drawdown start date. Then from pension drawdown.'
                        ' If the pension runs out then money is taken from savings to cover this.')

                    monthly_amount_from_other_sources = self._future_plot_attr_dict[FuturePlotGUI.MONTHLY_AMOUNT_FROM_OTHER_SOURCES]
                    self._monthly_amount_from_other_sources_field = ui.number(label=FuturePlotGUI.MONTHLY_AMOUNT_FROM_OTHER_SOURCES, value=monthly_amount_from_other_sources, min=0).tooltip(
                        'A monthly amount from non savings/pension sources. E.G Part time jobs or adult children living at home contributing to household finances.')

                with ui.row():
                    yearly_increase_in_income = self._future_plot_attr_dict[
                        FuturePlotGUI.YEARLY_INCREASE_IN_INCOME]
                    self._yearly_increase_in_income_field = ui.input(label=FuturePlotGUI.YEARLY_INCREASE_IN_INCOME, value=yearly_increase_in_income).style(
                        'width: 800px;').tooltip('This may be a single value or a comma separated list (one value for each year). The last value in the list will be used for subsequent years.')

                with ui.row():
                    savings_interest_rate_list = self._future_plot_attr_dict[
                        FuturePlotGUI.SAVINGS_INTEREST_RATE_LIST]
                    self._savings_interest_rates_field = ui.input(label=FuturePlotGUI.SAVINGS_INTEREST_RATE_LIST, value=savings_interest_rate_list).style(
                        'width: 800px;').tooltip('This may be a single value or a comma separated list (one value for each year). The last value in the list will be used for subsequent years.')
                with ui.row():
                    pension_growth_rate_list = self._future_plot_attr_dict[
                        FuturePlotGUI.PENSION_GROWTH_RATE_LIST]
                    self._pension_growth_rate_list_field = ui.input(label=FuturePlotGUI.PENSION_GROWTH_RATE_LIST, value=pension_growth_rate_list).style(
                        'width: 800px;').tooltip('This may be a single value or a comma separated list (one value for each year). The last value in the list will be used for subsequent years.')
                with ui.row():
                    state_pension_growth_rate_list = self._future_plot_attr_dict[
                        FuturePlotGUI.STATE_PENSION_YEARLY_INCREASE_LIST]
                    self._state_pension_growth_rate_list_field = ui.input(label=FuturePlotGUI.STATE_PENSION_YEARLY_INCREASE_LIST, value=state_pension_growth_rate_list).style(
                        'width: 800px;').tooltip('This may be a single value or a comma separated list (one value for each year). The last value in the list will be used for subsequent years.')

            with ui.column():
                with ui.row():
                    columns = [{'name': FuturePlotGUI.DATE, 'label': FuturePlotGUI.DATE, 'field': FuturePlotGUI.DATE},
                               {'name': FuturePlotGUI.AMOUNT, 'label': FuturePlotGUI.AMOUNT,
                                   'field': FuturePlotGUI.AMOUNT},
                               ]
                    with ui.column():
                        with ui.card().style("height: 600px; overflow-y: auto;").tooltip("Add planned savings withdrawals here."):
                            ui.label("Savings withdrawals").style(
                                'font-weight: bold;')
                            self._savings_withdrawals_table = ui.table(columns=columns,
                                                                       rows=[],
                                                                       row_key=BankAccountGUI.DATE,
                                                                       selection='multiple')
                            with ui.row():
                                ui.button('Add', on_click=lambda: self._add_savings_withdrawal()).tooltip(
                                    'Add to the savings withdrawals table.')
                                ui.button('Delete', on_click=lambda: self._del_savings_withdrawal()).tooltip(
                                    'Delete a savings withdrawal from the table.')

                    with ui.column():
                        with ui.card().style("height: 600px; overflow-y: auto;").tooltip("Add planned pension withdrawals here."):
                            ui.label("Pension withdrawals").style(
                                'font-weight: bold;')
                            self._pension_withdrawals_table = ui.table(columns=columns,
                                                                       rows=[],
                                                                       row_key=BankAccountGUI.DATE,
                                                                       selection='multiple')
                            with ui.row():
                                ui.button('Add', on_click=lambda: self._add_pension_withdrawal()).tooltip(
                                    'Add to the pension withdrawals table.')
                                ui.button('Delete', on_click=lambda: self._del_pension_withdrawal()).tooltip(
                                    'Delete a pension withdrawal from the table.')

                    self._update_gui_tables()

        with ui.row():
            with ui.card():
                ui.label("Save/Load the above retirement prediction parameter set.")
                with ui.row():
                    self._settings_name_list = [FuturePlotGUI.DEFAULT] + self._get_settings_name_list()
                    retirement_predictions_settings_name = self._get_selected_retirement_predictions_settings_name()
                    self._settings_name_select = ui.select(self._settings_name_list,
                                                           label='Name',
                                                           on_change=lambda e: self._select_settings_name(
                                                               e.value),
                                                           value=retirement_predictions_settings_name).style('width: 400px;')
                    self._new_settings_name_input = ui.input(
                        label='New name').style('width: 400px;')

                with ui.row():
                    ui.button('Save', on_click=lambda: self._save()).tooltip(
                        'Save the above pension prediction parameters.')
                    ui.button('Delete', on_click=lambda: self._del_ret_pred_param_dialog.open()).tooltip(
                        'Delete the selected pension prediction parameters.')

        with ui.row():
            ui.button('Show prediction', on_click=lambda: self._calc()).tooltip(
                'Perform calculation and plot the results.')
            self._show_progress_button = ui.button('Show progress', on_click=lambda: self._show_progress()).tooltip(
                'Show your progress against a prediction.')
            self._last_year_to_plot_field = ui.input(label="Last year to plot", value="").style(
                        'width: 200px;').tooltip('The last year you wish to plot. Leave this blank to plot all years.')
            self._interval_radio = ui.radio([FuturePlotGUI.BY_MONTH, FuturePlotGUI.BY_YEAR], value=FuturePlotGUI.BY_MONTH).props('inline')

        self._update_gui_from_dict()
        self._load_settings(retirement_predictions_settings_name)

    def _init_ok_to_delete_dialog(self):
        """@brief Create a dialog presented to the user to check that they wish to delete a retirement prediction parameter set."""
        with ui.dialog() as self._del_ret_pred_param_dialog, ui.card().style('width: 400px;'):
            ui.label("Are you sure you wish to delete the selected retirement prediction parameter set ?")
            with ui.row():
                ui.button("Yes", on_click=self._delete)
                ui.button("No", on_click=self._cancel_del_ret_pred_param_dialog)

    def _cancel_del_ret_pred_param_dialog(self):
        self._del_ret_pred_param_dialog.close()

    def _get_settings_name_list(self):
        """@return a list of name of the saved future plot parameters."""
        multiple_future_plot_attrs_dict = self._config.get_multiple_future_plot_attrs_dict()
        return list(multiple_future_plot_attrs_dict.keys())

    def _select_settings_name(self, value):
        # Clear the new name field
        settings_name = self._get_settings_name()
        self._set_selected_retirement_predictions_settings_name(settings_name)
        self._new_settings_name_input.value = ""
        self._load_settings(settings_name)

    def _get_settings_name(self):
        """@brief Get the entered settings name."""
        use_input_field_name = False
        name = self._new_settings_name_input.value
        name = name.strip()
        if len(name) > 0:
            if name not in self._settings_name_list:
                self._settings_name_list.append(name)
                self._settings_name_select.update()
            self._settings_name_select.value = name
            use_input_field_name = True
        if not use_input_field_name:
            name = self._settings_name_select.value
        return name

    def _save(self):
        """@save the report parameters to persistent storage."""
        if self._update_dict_from_gui():
            self._config.save_future_plot_attrs()

            name = self._get_settings_name()
            multiple_future_plot_attrs_dict = self._config.get_multiple_future_plot_attrs_dict()
            if name and len(name) > 0:
                multiple_future_plot_attrs_dict[name] = copy.deepcopy(
                    self._config.get_future_plot_attrs_dict())
            self._config.save_multiple_future_plot_attrs()
            # Clear the new name field
            self._new_settings_name_input.value = ""

    def _load_settings(self, selected_settings_name):
        """@brief Load the prediction parameters.
           @param selected_settings_name The name of the settings to load."""
        name_list = self._get_settings_name_list()
        if selected_settings_name in name_list:
            # Load from the stored settings file
            self._config._load_multiple_future_plot_attrs()
            future_plot_attrs_dict = self._config.get_multiple_future_plot_attrs_dict()[selected_settings_name]
            self._config.replace_future_plot_attrs_dict(future_plot_attrs_dict)
            self._update_gui_from_dict()

    def _delete(self):
        self._del_ret_pred_param_dialog.close()
        name = self._settings_name_select.value
        if name == FuturePlotGUI.DEFAULT:
            ui.notify(
                f"{FuturePlotGUI.DEFAULT} cannot be deleted.", type='negative')
        else:
            # Remove the name from the dict
            multiple_future_plot_attrs_dict = self._config.get_multiple_future_plot_attrs_dict()
            if name in multiple_future_plot_attrs_dict:
                del multiple_future_plot_attrs_dict[name]
                self._config.save_multiple_future_plot_attrs()
                ui.notify(f"Deleted {name}.")
            # Remove the name from the displayed name list
            if name in self._settings_name_list:
                self._settings_name_list.remove(name)
            # If there are entries in the list
            if len(self._settings_name_list) > 0:
                # Select The first name
                self._settings_name_select.value = self._settings_name_list[0]

    def _init_add_row_dialog(self):
        """@brief Create a dialog presented to the user to add a withdrawal from the savings or pension tables."""
        with ui.dialog() as self._add_row_dialog, ui.card().style('width: 400px;'):
            self._date_input_field = GUIBase.GetInputDateField(
                FuturePlotGUI.DATE)
            self._amount_field = ui.number(label=FuturePlotGUI.AMOUNT)
            self._repeat_field = ui.select(
                [FuturePlotGUI.YEARLY, FuturePlotGUI.MONTHLY], value='Yearly')
            self._repeat_count_field = ui.number(
                label="Occurrences", value=1, min=1)
            with ui.row():
                ui.button("Ok", on_click=self._add_row_dialog_ok_button_press)
                ui.button(
                    "Cancel", on_click=self._add_row_dialog_cancel_button_press)

    def _update_gui_tables(self):
        self._display_table_rows(
            self._savings_withdrawals_table, self._get_savings_withdrawal_table_data())
        self._display_table_rows(
            self._pension_withdrawals_table, self._get_pension_withdrawal_table_data())

    def _get_savings_withdrawal_table_data(self):
        """@brief Get a table of the savings withdrawals."""
        return self._future_plot_attr_dict[FuturePlotGUI.SAVINGS_WITHDRAWAL_TABLE]

    def _get_pension_withdrawal_table_data(self):
        """@brief Get a table of the pension withdrawals."""
        return self._future_plot_attr_dict[FuturePlotGUI.PENSION_WITHDRAWAL_TABLE]

    def _display_table_rows(self, gui_table, table_data):
        """@brief Show a table of the configured bank accounts.
           @param gui_table The GUI table element.
           @param table_data The table date. Each row has two elements (DATE and AMOUNT)."""
        gui_table.rows.clear()
        gui_table.update()
        for row in table_data:
            gui_table.add_row(
                {FuturePlotGUI.DATE: row[0], FuturePlotGUI.AMOUNT: row[1]})
        gui_table.run_method('scrollTo', len(gui_table.rows)-1)

    def _add_savings_withdrawal(self):
        """@brief Called when the add a savings withdrawal button is selected."""
        self._button_selected = FuturePlotGUI.ADD_SAVINGS_WITHDRAWAL_BUTTON
        self._add_row_dialog.open()

    def _del_savings_withdrawal(self):
        """@brief Called when the delete a savings withdrawal button is selected."""
        selected_dict_list = self._savings_withdrawals_table.selected
        if selected_dict_list and len(selected_dict_list) > 0:
            for selected_dict in selected_dict_list:
                if FuturePlotGUI.DATE in selected_dict:
                    del_date = selected_dict[FuturePlotGUI.DATE]
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
        selected_dict_list = self._pension_withdrawals_table.selected
        if selected_dict_list and len(selected_dict_list) > 0:
            for selected_dict in selected_dict_list:
                if FuturePlotGUI.DATE in selected_dict:
                    del_date = selected_dict[FuturePlotGUI.DATE]
                    table = self._future_plot_attr_dict[FuturePlotGUI.PENSION_WITHDRAWAL_TABLE]
                    new_table = []
                    for row in table:
                        date = row[0]
                        if date != del_date:
                            new_table.append(row)
                    self._future_plot_attr_dict[FuturePlotGUI.PENSION_WITHDRAWAL_TABLE] = new_table
        self._update_gui_tables()

    def _add_row_dialog_ok_button_press(self):
        if FuturePlotGUI.CheckValidDateString(self._date_input_field.value,
                                              field_name=self._date_input_field.props['label']) and \
           FuturePlotGUI.CheckGreaterThanZero(self._repeat_count_field.value,
                                              field_name=self._repeat_count_field.props['label']):

            self._add_row_dialog.close()
            yearly = False
            monthly = False

            if self._repeat_field.value == FuturePlotGUI.YEARLY:
                yearly = True

            if self._repeat_field.value == FuturePlotGUI.MONTHLY:
                monthly = True

            occurrence_count = self._repeat_count_field.value
            the_date = self._date_input_field.value
            for _ in range(0, int(occurrence_count)):
                row = (the_date, self._amount_field.value)
                if self._button_selected == FuturePlotGUI.ADD_SAVINGS_WITHDRAWAL_BUTTON:
                    rows = self._future_plot_attr_dict[FuturePlotGUI.SAVINGS_WITHDRAWAL_TABLE]
                    if self._check_date_in_table(the_date, rows):
                        ui.notify(f"{the_date} is already in the table.", type='negative')
                        return

                    else:
                        rows.append(row)
                        # Sort table in ascending date order
                        sorted_rows = sorted(rows, key=lambda row: datetime.strptime(row[0], "%d-%m-%Y"))
                        self._future_plot_attr_dict[FuturePlotGUI.SAVINGS_WITHDRAWAL_TABLE] = sorted_rows

                elif self._button_selected == FuturePlotGUI.ADD_PENSION_WITHDRAWAL_BUTTON:
                    rows = self._future_plot_attr_dict[FuturePlotGUI.PENSION_WITHDRAWAL_TABLE]
                    if self._check_date_in_table(the_date, rows):
                        ui.notify(f"{the_date} is already in the table.", type='negative')
                        return

                    else:
                        rows.append(row)
                        # Sort table in ascending date order
                        sorted_rows = sorted(rows, key=lambda row: datetime.strptime(row[0], "%d-%m-%Y"))
                        self._future_plot_attr_dict[FuturePlotGUI.PENSION_WITHDRAWAL_TABLE] = sorted_rows

                else:
                    raise Exception("BUG: Neither the add savings or add pensions button was selected.")

                if yearly:
                    the_date = self._get_next_date_str(the_date, 12)
                if monthly:
                    the_date = self._get_next_date_str(the_date, 1)

            self._update_gui_tables()

    def _check_date_in_table(self, _date, table):
        """@brief Check if a date is in a table. Col 0 = date.
           @return True if it is."""
        return any(row[0] == _date for row in table)

    def _get_next_date_str(self, start_date_str, months):
        """@brief Get the start date + the number of months.
           @param start_date_str The from date string as dd-mm-yyyy.
           @param months The number of months to add to the start date."""
        start_date = datetime.strptime(start_date_str, '%d-%m-%Y')
        next_date = start_date + relativedelta(months=+months)
        return next_date.strftime('%d-%m-%Y')

    def _add_row_dialog_cancel_button_press(self):
        self._add_row_dialog.close()

    def _get_max_date(self):
        """@brief Get the maximum date we need to plan for.
           @return a datetime instance of the max year."""
        self._update_dict_from_gui()
        my_max_date = self._get_my_max_date()
        max_date = my_max_date

        partner_max_date = self._get_partner_max_date()
        if partner_max_date is not None and partner_max_date > my_max_date:
            max_date = partner_max_date

        return max_date

    def _get_my_max_date(self):
        """@return The maximum date I (for trhe purposes of this report) hope to be alive."""
        my_dob_str = self._future_plot_attr_dict[FuturePlotGUI.MY_DATE_OF_BIRTH]
        my_dob = datetime.strptime(my_dob_str, '%d-%m-%Y')
        my_max_age = int(self._future_plot_attr_dict[FuturePlotGUI.MY_MAX_AGE])
        my_max_date = my_dob + relativedelta(years=my_max_age)
        return my_max_date

    def _get_my_age(self, current_date):
        """@brief Get my age at the given date.
           @param current_date The date of interest.
           @return My age in years."""
        my_dob_str = self._future_plot_attr_dict[FuturePlotGUI.MY_DATE_OF_BIRTH]
        my_dob = datetime.strptime(my_dob_str, '%d-%m-%Y')
        timedelta = current_date - my_dob
        age_years = timedelta.days / 364.25
        return age_years

    def _get_partner_max_date(self):
        """@return The maximum date my partner (for the purposes of this report) hopes to be alive or None
                   if no partner details entered into the retirement prediction form."""
        partner_max_date = None
        partner_dob_str = self._future_plot_attr_dict[FuturePlotGUI.PARTNER_DATE_OF_BIRTH]
        if partner_dob_str and len(partner_dob_str) > 0:
            partner_dob = datetime.strptime(partner_dob_str, '%d-%m-%Y')
            partner_max_age = int(self._future_plot_attr_dict[FuturePlotGUI.PARTNER_MAX_AGE])
            partner_max_date = partner_dob + relativedelta(years=partner_max_age)
        return partner_max_date

    def _update_dict_from_gui(self):
        """@brief update the dict from the details entered into the GUI.
           @return True if all entries are valid."""
        valid = False
        if FuturePlotGUI.CheckValidDateString(self._start_date_field.value,
                                              field_name=self._start_date_field.props['label']):
            proceed = False
            # If the pension drawdown start date is enabled.
            if self._enable_pension_drawdown_start_date.value:
                # If enabled we need a valid date
                if FuturePlotGUI.CheckValidDateString(self._pension_drawdown_start_date_field.value, field_name=self._pension_drawdown_start_date_field.props['label']):
                    proceed = True
            # If not enabled we proceed with the rest of the checks.
            else:
                proceed = True

            if proceed and FuturePlotGUI.CheckValidDateString(self._my_dob_field.value,
                                                              field_name=self._my_dob_field.props['label']) and \
                BankAccountGUI.CheckGreaterThanZero(self._my_max_age_field.value,
                                                    field_name=self._my_max_age_field.props['label']) and \
                BankAccountGUI.CheckZeroOrGreater(self._monthly_income_field.value,
                                                  field_name=self._monthly_income_field.props['label']) and \
                BankAccountGUI.CheckCommaSeparatedNumberList(self._yearly_increase_in_income_field.value,
                                                             field_name=self._yearly_increase_in_income_field.props['label']) and \
                BankAccountGUI.CheckCommaSeparatedNumberList(self._savings_interest_rates_field.value,
                                                             field_name=self._savings_interest_rates_field.props['label']) and \
                BankAccountGUI.CheckCommaSeparatedNumberList(self._pension_growth_rate_list_field.value,
                                                             field_name=self._pension_growth_rate_list_field.props['label']) and \
                BankAccountGUI.CheckCommaSeparatedNumberList(self._state_pension_growth_rate_list_field.value,
                                                             field_name=self._state_pension_growth_rate_list_field.props['label']):

                self._future_plot_attr_dict[FuturePlotGUI.MY_DATE_OF_BIRTH] = self._my_dob_field.value
                self._future_plot_attr_dict[FuturePlotGUI.MY_MAX_AGE] = self._my_max_age_field.value
                self._future_plot_attr_dict[FuturePlotGUI.PARTNER_DATE_OF_BIRTH] = self._partner_dob_field.value
                self._future_plot_attr_dict[FuturePlotGUI.PARTNER_MAX_AGE] = self._partner_max_age_field.value
                self._future_plot_attr_dict[FuturePlotGUI.SAVINGS_INTEREST_RATE_LIST] = self._savings_interest_rates_field.value
                self._future_plot_attr_dict[FuturePlotGUI.PENSION_GROWTH_RATE_LIST] = self._pension_growth_rate_list_field.value
                self._future_plot_attr_dict[FuturePlotGUI.STATE_PENSION_YEARLY_INCREASE_LIST] = self._state_pension_growth_rate_list_field.value
                self._future_plot_attr_dict[FuturePlotGUI.MONTHLY_AMOUNT_FROM_OTHER_SOURCES] = self._monthly_amount_from_other_sources_field.value
                self._future_plot_attr_dict[FuturePlotGUI.MONTHLY_INCOME] = self._monthly_income_field.value
                self._future_plot_attr_dict[FuturePlotGUI.YEARLY_INCREASE_IN_INCOME] = self._yearly_increase_in_income_field.value
                self._future_plot_attr_dict[FuturePlotGUI.REPORT_START_DATE] = self._start_date_field.value
                self._future_plot_attr_dict[FuturePlotGUI.PENSION_DRAWDOWN_START_DATE] = self._pension_drawdown_start_date_field.value
                self._future_plot_attr_dict[FuturePlotGUI.ENABLE_PENSION_DRAWDOWN_START_DATE] = self._enable_pension_drawdown_start_date.value
                valid = True

        return valid

    def _update_gui_from_dict(self):
        """@brief Load config from persistent storage and display in GUI."""
        self._future_plot_attr_dict = self._config.get_future_plot_attrs_dict()
        self._my_dob_field.value = self._future_plot_attr_dict.get(
            FuturePlotGUI.MY_DATE_OF_BIRTH, "")
        self._my_max_age_field.value = self._future_plot_attr_dict.get(
            FuturePlotGUI.MY_MAX_AGE, FuturePlotGUI.DEFAULT_MALE_MAX_AGE)
        self._partner_dob_field.value = self._future_plot_attr_dict.get(
            FuturePlotGUI.PARTNER_DATE_OF_BIRTH, "")
        self._partner_max_age_field.value = self._future_plot_attr_dict.get(
            FuturePlotGUI.PARTNER_MAX_AGE, FuturePlotGUI.DEFAULT_MALE_MAX_AGE + 4)
        self._savings_interest_rates_field.value = self._future_plot_attr_dict.get(
            FuturePlotGUI.SAVINGS_INTEREST_RATE_LIST, FuturePlotGUI.DEFAULT_RATE_LIST)
        self._pension_growth_rate_list_field.value = self._future_plot_attr_dict.get(
            FuturePlotGUI.PENSION_GROWTH_RATE_LIST, FuturePlotGUI.DEFAULT_RATE_LIST)
        self._state_pension_growth_rate_list_field.value = self._future_plot_attr_dict.get(
            FuturePlotGUI.STATE_PENSION_YEARLY_INCREASE_LIST, FuturePlotGUI.DEFAULT_STATE_PENSION_YEARLY_INCREASE)
        self._monthly_amount_from_other_sources_field.value = self._future_plot_attr_dict.get(
            FuturePlotGUI.MONTHLY_AMOUNT_FROM_OTHER_SOURCES, FuturePlotGUI.DEFAULT_MONTHLY_AMOUNT_FROM_OTHER_SOURCES)
        self._monthly_income_field.value = self._future_plot_attr_dict.get(
            FuturePlotGUI.MONTHLY_INCOME, FuturePlotGUI.DEFAULT_MONTHLY_INCOME)
        self._yearly_increase_in_income_field.value = self._future_plot_attr_dict.get(
            FuturePlotGUI.YEARLY_INCREASE_IN_INCOME, FuturePlotGUI.DEFAULT_YEARLY_INCREASE_IN_INCOME)
        self._start_date_field.value = self._future_plot_attr_dict.get(FuturePlotGUI.REPORT_START_DATE, "")
        self._pension_drawdown_start_date_field.value = self._future_plot_attr_dict.get(FuturePlotGUI.PENSION_DRAWDOWN_START_DATE, '')
        self._enable_pension_drawdown_start_date.value = self._future_plot_attr_dict.get(FuturePlotGUI.ENABLE_PENSION_DRAWDOWN_START_DATE, False)
        if self._enable_pension_drawdown_start_date.value:
            self._pension_drawdown_start_date_field.enable()
        else:
            self._pension_drawdown_start_date_field.disable()

        self._update_gui_tables()

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

    def _show_progress(self):
        self._calc(overlay_real_performance=True)

    def _calc(self, overlay_real_performance=False):
        """@brief Perform calculation. This took ages to get right. I used the household_finances spreadsheet to validate the numbers it produces.
           @param overlay_real_performance If True then the plot shows the predictions overlaid with the real performance.

           !!! This method is to large, work needed !!!"""
        try:
            plot_table = []
            max_planning_date = self._get_max_date()
            report_start_date = datetime.strptime(
                self._future_plot_attr_dict[FuturePlotGUI.REPORT_START_DATE], '%d-%m-%Y')
            # Set parameter to be used later
            self._report_start_date = report_start_date
            # A list of the dates to be plotted (monthly)
            datetime_list = FuturePlotGUI.GetDateTimeList(
                report_start_date, max_planning_date)
            first_date = datetime_list[0]
            last_date = first_date
            # A table, each row of which index 0 = date and index 1 = the required monthly income
            monthly_budget_table = self._get_monthly_budget_table(
                datetime_list)
            monthly_savings_interest_list = []
            lump_sum_pension_withdrawals_table = self._convert_table(
                self._future_plot_attr_dict[FuturePlotGUI.PENSION_WITHDRAWAL_TABLE])
            pp_table = self._get_personal_pension_table()
            if self._future_plot_attr_dict[FuturePlotGUI.ENABLE_PENSION_DRAWDOWN_START_DATE]:
                pension_drawdown_start_date = datetime.strptime(self._future_plot_attr_dict[FuturePlotGUI.PENSION_DRAWDOWN_START_DATE], '%d-%m-%Y')
            else:
                pension_drawdown_start_date = None
            predicted_state_pension_table = self._get_predicted_state_pension(datetime_list, report_start_date)
            # DEBUG
            # print("PJA: predicted_state_pension_table")
            # for row in  predicted_state_pension_table:
            #    print(f"PJA: row = {row}")

            if predicted_state_pension_table is None:
                raise Exception('No state pension defined in the pension list.')
            monthly_from_other_sources = float(self._future_plot_attr_dict[FuturePlotGUI.MONTHLY_AMOUNT_FROM_OTHER_SOURCES])
            lump_sum_savings_withdrawals_table = self._convert_table(
                self._future_plot_attr_dict[FuturePlotGUI.SAVINGS_WITHDRAWAL_TABLE])

            # Get the initial value of our personal pension
            personal_pension_value = self._get_initial_value(pp_table, report_start_date)
            # DEBUG
            # print(f"PJA: INITIAL personal_pension_value={personal_pension_value}")
            savings_amount = self._get_savings_total(report_start_date)
            state_pension_this_month = self._get_state_pension_this_month(
                first_date, predicted_state_pension_table)
            savings_interest = 0.0
            total_savings_withdrawal = 0.0
            total_pension_withdrawal = 0.0
            pension_withdrawal_amount = 0.0
            lump_sum_pension_withdrawal = 0.0
            savings_withdrawal_amount = 0.0
            lump_sum_savings_withdrawal = 0.0
            year_index = 0
            total = savings_amount + personal_pension_value
            predicted_income_this_month = monthly_budget_table[0][1]
            state_pension_this_month = self._get_state_pension_this_month(first_date, predicted_state_pension_table)
            # DEBUG
            # print(f"PJA: state_pension_this_month={state_pension_this_month}")
            tax_free_pension_event = False
            money_ran_out = False
            # We assume our spending matches our income for the first month.
            spending_this_month = predicted_income_this_month

            # Add initial state
            plot_table.append((first_date,
                               total,
                               personal_pension_value,
                               savings_amount,
                               predicted_income_this_month,
                               state_pension_this_month,
                               savings_interest,
                               total_savings_withdrawal,
                               total_pension_withdrawal,
                               spending_this_month))

            # Assume that the account existed in the month prior to the report start date.
            # Therefore add the savings accrued during this month.
            increase_this_month = self._get_savings_increase_this_month(savings_amount, 0)
            # We assume savings interest accrues monthly but is added yearly. Therefore add to a list for use later.
            monthly_savings_interest_list.append(increase_this_month)

            # Calc the required parameters for each date
            for row in monthly_budget_table:
                this_date = row[0]
                # We ignore the first date as no time has passed. Therefore the state of the finances will be unchanged
                if this_date <= first_date:
                    continue

                # If the year has rolled over calculate the interest earned on any savings.
                if this_date.year != last_date.year:
                    year_index += 1
                    # Sum the interest we've added each month in the previous year
                    savings_interest = sum(monthly_savings_interest_list)
                    savings_amount += savings_interest
                    monthly_savings_interest_list = []
                    last_date = this_date

                # We assume savings account interest is once a year
                else:
                    savings_interest = 0

                # Get the predicted income this month
                predicted_income_this_month = row[1]
                # Remove any money we expect to receive.
                remaining_income_this_month = predicted_income_this_month - monthly_from_other_sources

                # Get the total state pension we expect to receive this month.
                state_pension_this_month = self._get_state_pension_this_month(this_date, predicted_state_pension_table)

                # Calc how much income we need after deducting state pension. We assume we need more than the state pension.
                # if remaining_income_this_month >= state_pension_this_month:
                remaining_income_this_month = remaining_income_this_month - state_pension_this_month

                # If we chose to draw a lump sum from savings
                savings_amount_before = savings_amount
                new_savings_amount = self._get_value_drop(this_date,
                                                          savings_amount,
                                                          lump_sum_savings_withdrawals_table)
                lump_sum_savings_withdrawal = savings_amount_before - new_savings_amount

                # Previously we used the lump sum savings withdrawal to reduce the required income.
                # However the savings withdrawal table should be used by the user to define savings withdrawals
                # on top of those required to meet the monthly income.
                # Therefore it should not be used so that, if set, it results in an increase in the monthly spending.
                # if lump_sum_savings_withdrawal > 0:
                #    # Note that this may result in more than the monthly budget.
                #    remaining_income_this_month = remaining_income_this_month - lump_sum_savings_withdrawal

                # If we want to draw lump sum/s from our pension.
                previous_personal_pension_value = personal_pension_value
                new_personal_pension_value = self._get_value_drop(this_date,
                                                                  personal_pension_value,
                                                                  lump_sum_pension_withdrawals_table)
                lump_sum_pension_withdrawal = previous_personal_pension_value - new_personal_pension_value
                if lump_sum_pension_withdrawal > 0:
                    # Note that this may result in more than the monthly budget.
                    remaining_income_this_month = remaining_income_this_month - lump_sum_pension_withdrawal

                if remaining_income_this_month > 0:
                    if pension_drawdown_start_date is not None and this_date >= pension_drawdown_start_date:
                        # If we are now regularly taking money from our personal pension to cover monthly income/budget
                        # we assume we are no longer regularly taking monthly money from our savings
                        if this_date >= pension_drawdown_start_date:
                            # Take the remainder from our pensions
                            pension_withdrawal_amount = remaining_income_this_month
                            # No savings drop now we are drawing down on pension.
                            savings_withdrawal_amount = 0

                    else:
                        # Take the remainder from our savings
                        savings_withdrawal_amount = remaining_income_this_month
                        # No pension drop as we are now we are drawing down on savings.
                        pension_withdrawal_amount = 0

                # Calc the withdrawal from savings and pension
                total_pension_withdrawal = pension_withdrawal_amount + lump_sum_pension_withdrawal

                total_savings_withdrawal = savings_withdrawal_amount + lump_sum_savings_withdrawal

                # Calc the new savings and pension amounts

                savings_amount = savings_amount - total_savings_withdrawal
                # Calc the increase/decrease on savings this month given the predicted interest rate.
                increase_this_month = self._get_savings_increase_this_month(savings_amount, year_index)
                # We assume savings interest accrues monthly but is added yearly. Therefore add to a list for use later.
                monthly_savings_interest_list.append(increase_this_month)

                personal_pension_value = personal_pension_value - total_pension_withdrawal
                # Calc increase/decrease of pension this month due to growth/decline. We assume this acru's monthly
                personal_pension_increase = self._get_pension_increase_this_month(personal_pension_value, year_index)
                personal_pension_value = personal_pension_value + personal_pension_increase

                # If we have no pension left but expect to withdraw from it
                if personal_pension_value <= 0 and total_pension_withdrawal > 0:
                    # Check to see if we can take what we need from savings.
                    if total_pension_withdrawal < savings_amount:
                        savings_amount = savings_amount - total_pension_withdrawal
                        total_savings_withdrawal += total_pension_withdrawal
                        total_pension_withdrawal = 0
                        personal_pension_value = 0

                    # We have no savings or pension left
                    else:
                        total_savings_withdrawal = 0
                        total_pension_withdrawal = 0
                        # Income drops to the state pension if we run out of money as this is the only other source.
                        predicted_income_this_month = state_pension_this_month
                        money_ran_out = True

                # If we have no savings left but expect to withdraw from it
                if savings_amount <= 0 and total_savings_withdrawal > 0:
                    # Check to see if we can take what we need from pensions.
                    if total_savings_withdrawal < personal_pension_value:
                        personal_pension_value = personal_pension_value - total_savings_withdrawal
                        total_pension_withdrawal += total_savings_withdrawal
                        total_savings_withdrawal = 0
                        savings_amount = 0

                    # We have no savings or pension left
                    else:
                        total_savings_withdrawal = 0
                        total_pension_withdrawal = 0
                        # Income drops to the state pension if we run out of money as this is the only other source.
                        predicted_income_this_month = state_pension_this_month
                        money_ran_out = True

                # Calc the total spending this month
                spending_this_month = total_savings_withdrawal + total_pension_withdrawal + state_pension_this_month + monthly_from_other_sources

                # Calc the total
                total = savings_amount + personal_pension_value

                # If an event has yet to occur that gives pension tax free
                if not tax_free_pension_event:
                    # Check to see if the prediction details my death before 75
                    if self._dead_before_75(this_date):
                        # Transfer all pension funds to savings tax free
                        savings_amount = savings_amount + personal_pension_value
                        personal_pension_value = 0
                        # As pension fund is now zero set this to None to
                        # stop any further pension fund withdrawals
                        pension_drawdown_start_date = None
                        tax_free_pension_event = True

                if total <= 0:
                    # Income drops to the state pension if we run out of money
                    predicted_income_this_month = state_pension_this_month
                    # We can't withdraw as savings and pensions have dropped to zero
                    total_savings_withdrawal = 0
                    total_pension_withdrawal = 0

                # Add to the data to be plotted
                plot_table.append((this_date,
                                   total,
                                   personal_pension_value,
                                   savings_amount,
                                   predicted_income_this_month,
                                   state_pension_this_month,
                                   savings_interest,
                                   total_savings_withdrawal,
                                   total_pension_withdrawal,
                                   spending_this_month))

                if total <= 0:
                    money_ran_out = True

            final_year = self._get_final_year()
            if overlay_real_performance:
                pp_table = self._get_personal_pension_table()
                savings_table = self._get_savings_table()
                total_table = self._get_total_table()
                monthly_spending_table = self._get_monthly_spending_table()
                # These tables hold values entered by the users that are real values, not predicted.
                reality_tables = [pp_table, savings_table, total_table, monthly_spending_table]

                self._do_plot(self._settings_name_select.value,
                              plot_table,
                              reality_tables=reality_tables,
                              money_ran_out=money_ran_out,
                              final_year=final_year)
            else:
                self._do_plot(self._settings_name_select.value,
                              plot_table,
                              money_ran_out=money_ran_out,
                              final_year=final_year)

        except Exception as ex:
            traceback.print_tb(ex.__traceback__)
            ui.notify(str(ex), type='negative')

    def _get_monthly_spending_table(self):
        monthly_spending_dict = self._config.get_monthly_spending_dict()
        monthly_spending_table = monthly_spending_dict[Finances.MONTHLY_SPENDING_TABLE]

        return monthly_spending_table

    def _get_final_year(self):
        """@brief Get the final year of the prediction.
           @return The year to end the plot or -1 if not end is defined"""
        final_year = -1
        try:
            if len(self._last_year_to_plot_field.value) > 0:
                final_year = int(self._last_year_to_plot_field.value)
                now = datetime.now()
                if final_year < now.year:
                    raise Exception(f"Invalid year. The last year to plot must be greater than or equal to {now.year}")

        except ValueError:
            raise Exception("Invalid last year to plot. This must be a year in the future.")
        return final_year

    def _dead_before_75(self, report_date):
        """@brief Check to see if dead before 75'th birthday.
           @param report_date The current date of the report."""
        died_before_75 = False
        death_date = self._get_my_max_date()
        age = self._get_my_age(report_date)
        if age < 75 and death_date < report_date:
            died_before_75 = True
        return died_before_75

    # PJA not used but may be useful for example code
    def _show_progress_against_prediction(self):
        """@brief Show the increase/decrease of savings and pension against a selected prediction."""
        pp_table = self._get_personal_pension_table()
        print('Pension table')
        for row in pp_table:
            print(row)

        savings_table = self._get_savings_table()
        print('Savings table')
        for row in savings_table:
            print(row)

        total_table = self._get_total_table()
        print('Total table')
        for row in total_table:
            print(row)

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
            if self.is_this_month(_date, this_date):
                value -= amount
        return value

    def is_this_month(self, this_date, date_to_check):
        return (this_date.year == date_to_check.year and this_date.month == date_to_check.month)

    def _do_plot(self,
                 name,
                 plot_table,
                 reality_tables=None,
                 final_year=-1,
                 money_ran_out=False):
        """@brief perform a plot of the data in the plot_table.
           @param name The name of the plot.
           @param plot_table Holds rows that comprise the following
                             0 = date
                             1 = total (savings + pension)
                             2 = pension total
                             3 = savings total
                             4 = monthly income
                             5 = monthly state pension total of both of us.
                             6 = savings_interest (yearly)
                             7 = savings withdrawal this month
                             8 = pension withdrawal this month.
                             9 = spending_this_month
            @param reality_tables If defined this is a list the following tables.
                                  Each row in each table has a 0:Date and 1:value column
                                  0 = personal_pension_table
                                  1 = savings table
                                  2 = total table
                                  3 = monthly spending table
           @param final_year The final year to plot.
                             This allows the caller to limit the length of the plot prediction.
                             If -1 entered then no limit is placed on the plot.
           @param money_ran_out If True the money ran out."""

        plot_by_year = False
        if self._interval_radio.value == FuturePlotGUI.BY_YEAR:
            plot_by_year = True

        # Define a secondary page
        @ui.page('/plot_1_page')
        def plot_1_page():
            Plot1GUI(name,
                     plot_table,
                     reality_tables,
                     final_year,
                     money_ran_out,
                     plot_by_year)
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
                account_amount = self._get_initial_value(date_value_table, initial_date=at_date)
                savings_total += account_amount
        return savings_total

    def _get_yearly_savings_increase(self, savings_amount, year_index):
        """@brief Get the value of our savings at the end of the month.
           @param savings_amount The current value of our savings.
           @param year_index An index from the start of the report to this year. Used to determine the predicted interest rate.
           @return As per the brief."""
        yearly_rate_list = self._future_plot_attr_dict[FuturePlotGUI.SAVINGS_INTEREST_RATE_LIST]
        yearly_rate = self._get_yearly_rate(yearly_rate_list, year_index)
        return savings_amount*(1 + (yearly_rate/100))

    def _get_savings_increase_this_month(self, savings_amount, year_index):
        """@brief Get the increase in the savings this month using the predicted interest rate.
           @param savings_amount The current value of our savings.
           @param year_index An index from the start of the report to this year. Used to determine the predicted interest rate.
           @return As per the brief."""
        yearly_rate_list = self._future_plot_attr_dict[FuturePlotGUI.SAVINGS_INTEREST_RATE_LIST]
        yearly_rate = self._get_yearly_rate(yearly_rate_list, year_index)
        yearly_increase = savings_amount * (yearly_rate/100)
        monthly_increase = yearly_increase / 12
        return monthly_increase

    def _get_monthly_growth(self, principal, annual_rate):
        """
            @brief Calculate the new balance after one month with daily compounding interest.
            @param principal: Initial amount (float)
            @param annual_rate: Annual interest rate as a decimal (e.g., 10% -> 0.10)
            @return: New balance after one month and increase.
        """
        days_in_year = 365  # May be 364 but this make only a small difference to calculations so we use 365
        days_in_month = 30.4167  # Average days in a month
        # Calculate the growth factor
        growth_factor = (1 + (annual_rate / days_in_year)) ** days_in_month
        # Calculate new balance
        new_balance = principal * growth_factor
        # Interest earned in one month
        interest_earned = new_balance - principal
        return new_balance, interest_earned

    def _get_pension_increase_this_month(self, personal_pension_value, year_index):
        """@brief Get the increase in the pension this month using the predicted growth rate.
                  This assumes that growth compounds daily.
           @param personal_pension_value The current value of our pensions.
           @param year_index An index from the start of the report to this year. Used to determine the predicted interest rate.
           @return The increase in the pension value."""
        yearly_rate_list = self._future_plot_attr_dict[FuturePlotGUI.PENSION_GROWTH_RATE_LIST]
        yearly_rate = self._get_yearly_rate(yearly_rate_list, year_index)
        yearly_rate = yearly_rate / 100
        _, monthly_increase = self._get_monthly_growth(personal_pension_value, yearly_rate)
        return monthly_increase

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
            raise Exception(f"_get_compound_growth_table(): datetime_list must have more than 1 element ({
                            len(datetime_list)})")
        compound_growth_table = []
        value = initial_value
        year_count = 0
        last_date = datetime_list[0]
        for _date in datetime_list:
            if _date.year != last_date.year:
                value = self._calc_new_account_value(
                    value, growth_rate_list, year_count)
                year_count += 1
                last_date = _date
            compound_growth_table.append((_date, value))
        return compound_growth_table

    def _get_personal_pension_table(self):
        """@return A table that contains the total amounts in all our personal pension
                   accounts over time. This is not predicted but comprises the total of all
                   savings accounts."""
        pp_dfl = self._get_personal_pension_pd_dfl()
        return self._get_amalgamated_table(pp_dfl)

    def _get_savings_table(self):
        """@param start_date The start date. Dates before this are ignored.
           @return A table that contains the total amounts in all our savings accounts
                   over time. This is not predicted but comprises the total of all
                   savings accounts."""
        savings_dfl = self._get_savings_pd_dfl()
        return self._get_amalgamated_table(savings_dfl)

    def _get_total_table(self):
        """@return A table that contains the total amounts in our personal
                   pension and saviings over time. This is not predicted but
                   comprises the total of all personal pension and savings accounts."""
        pp_dfl = self._get_personal_pension_pd_dfl()
        savings_dfl = self._get_savings_pd_dfl()
        return self._get_amalgamated_table(pp_dfl+savings_dfl)

    def _get_amalgamated_table(self, dataframe_list, return_total_table=True):
        """@brief Get an amalgamated table such that the total value of all input tables
                  can be seen over time. This was originally aimed at combining multiple
                  savings account tables into one so that the single table shows the
                  total amount of savings and how it changes over time as the user enters
                  the value in each savings account.
           @param dataframe_list A list of pandas dataframes. Each dataframe must have
                                 a 'Date' and a 'Value' column.
           @param return_total_table If True then the table returned just has two columns
                                     Date and Total.
                                     If False then the table returned has the same Date
                                     column but has separate columns for the total of
                                     each of the input tables."""
        table_index = 0
        for df in dataframe_list:
            # Convert 'Date' column to datetime
            df["Date"] = pd.to_datetime(df["Date"], format="%d-%m-%Y", errors="coerce")
            # Ensure Value column is a float
            df["Value"] = df["Value"].astype(float)
            # We need to ensure that the Value column is different in each table
            # So that they can be merged into one table without a column name clash.
            df.rename(columns={'Value': f'Value_{table_index}'}, inplace=True)
            # Inc the table index.
            table_index += 1

        if len(dataframe_list) > 0:
            # Merge all tables in the list
            merged_table = dataframe_list[0]
            for table in dataframe_list[1:]:
                merged_table = merged_table.merge(table, on='Date', how='outer').sort_values(by="Date")
            # Fill NaN values with previous row value if NaN
            # merged_table.fillna(method='ffill', inplace=True)
            merged_table.ffill(inplace=True)

            # Fall any NaN columns left over from above (no previous value in column) with 0
            merged_table.fillna(0.0, inplace=True)

            # Sum all the columns so that we know the total value each time it changes
            merged_table['Total'] = merged_table.drop(columns=['Date']).sum(axis=1)

            merged_table['Date'] = merged_table['Date'].apply(lambda x: x.to_pydatetime())

            if return_total_table:
                # Reset the Date index column so it is appears as any other table column
                table1 = merged_table.reset_index()
                # Only include the Date and Total columns on the returned table
                table2 = table1[['Date', 'Total']]
            else:
                # Return a table that has the date column and a separate column for
                # the total of each input table.
                table2 = merged_table

            return table2.values.tolist()

        else:
            return []

    def _get_personal_pension_pd_dfl(self):
        # Build a list of pandas dataframes
        pd_dataframe_list = []
        pension_dict_list = self._config.get_pension_dict_list()
        for pension_dict in pension_dict_list:
            state_pension = pension_dict[PensionGUI.STATE_PENSION]
            if not state_pension:
                data_dict = self._get_data_dict(pension_dict[PensionGUI.PENSION_TABLE], table_type="pensions")
                pd_dataframe = pd.DataFrame(data_dict)
                pd_dataframe_list.append(pd_dataframe)
        return pd_dataframe_list

    def _get_merged_dfl(self, pd_dataframe_list):
        """@brief Get a merged dataframe list.
           @param pd_dataframe_list Has a Date and a Value column in each.
           @return A table, a list of lists/rows, each row holding a date and value."""
        # Convert 'Date' column to datetime
        for df in pd_dataframe_list:
            df["Date"] = pd.to_datetime(df["Date"], format="%d-%m-%Y", errors="coerce")

        # Combine all DataFrames
        pd_dataframe_list_merged = pd.concat(pd_dataframe_list).sort_values(by="Date")

        # Compute cumulative sum
        full_date_range = pd.date_range(start=pd_dataframe_list_merged["Date"].min(), end=pd_dataframe_list_merged["Date"].max())
        final_pd_dataframe_list = (
            pd_dataframe_list_merged.set_index("Date")
            .reindex(full_date_range)
            .fillna({"Value": 0})
            .rename_axis("Date")
        )
        final_pd_dataframe_list["Value"] = final_pd_dataframe_list["Value"].astype(float)
        final_pd_dataframe_list["Cumulative Value"] = final_pd_dataframe_list["Value"].cumsum()
        table1 = final_pd_dataframe_list.reset_index()
        table2 = table1.drop(columns=["Value"])
        table2["Date"] = table2["Date"].dt.strftime("%d-%m-%Y")

        return self._convert_table(table2.values.tolist())

    def _get_data_dict(self, table, table_type=""):
        # We want to limit data in the table to dates on or after the report start date
        if self._report_start_date:
            # Filter based on parsed date
            filtered = [
                (date_str, value)
                for date_str, value in table
                if datetime.strptime(date_str, '%d-%m-%Y') >= self._report_start_date
            ]

            # Unpack results
            if filtered:
                new_dates, new_values = zip(*filtered)
            else:
                # If unable to select a date on or after the report start date use the latest data we have.
                dates, values = zip(*table)
                new_dates = dates[-1]
                new_values = values[-1]
            dates = new_dates
            values = new_values

        else:
            # If no report start date then use all the data we have
            # We should never really get here as a report start date is required.
            dates, values = zip(*table)

        if isinstance(dates, str):
            raise Exception(f"Insufficient {table_type} data. Check that you have at least two {table_type} values before the prediction start date.")

        return {"Date": dates, "Value": values}

    def _get_savings_pd_dfl(self):
        # Build a list of pandas dataframes
        pd_dataframe_list = []
        bank_accounts_dict_list = self._config.get_bank_accounts_dict_list()
        for bank_accounts_dict in bank_accounts_dict_list:
            active = bank_accounts_dict[BankAccountGUI.ACCOUNT_ACTIVE]
            if active:
                data_dict = self._get_data_dict(bank_accounts_dict[BankAccountGUI.TABLE], table_type="savings")
                pd_dataframe = pd.DataFrame(data_dict)
                pd_dataframe_list.append(pd_dataframe)
        return pd_dataframe_list

    def _get_predicted_state_pension(self, datetime_list, report_start_date):
        """ @param datetime_list A list of datetime instances
            @param report_start_date The date for the start of the future prediction report.
            @return A 2D table detailing the predicted state pension.
                   Row
                   0 = date
                   1 = The amount

                   of None if no state pensions found."""
        # Calculate the income from state pensions into the future
        consolidated_state_pension_income_table = []
        pension_dict_list = self._config.get_pension_dict_list()
        for pension_dict in pension_dict_list:
            state_pension_income_table = self._process_state_pension_table(pension_dict, datetime_list, report_start_date)
            # If a state pension was found
            if state_pension_income_table:

                if not consolidated_state_pension_income_table:
                    consolidated_state_pension_income_table = state_pension_income_table
                else:
                    # Add to current state pension table
                    for index in range(0, len(consolidated_state_pension_income_table)):
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
        owner = pension_dict[PensionGUI.PENSION_OWNER]
        if state_pension:
            future_table = []
            date_value_table = self._convert_table(
                pension_dict[PensionGUI.PENSION_TABLE])
            state_pension_start_date_str = pension_dict[PensionGUI.STATE_PENSION_START_DATE]
            state_pension_start_date = datetime.strptime(
                state_pension_start_date_str, '%d-%m-%Y')
            last_datetime = datetime_list[0]
            # Get the initial state pension amount based on the start date for the calc
            state_pension_amount = self._get_initial_value(date_value_table, initial_date=report_start_date)
            year_index = 0
            receiving_state_pension = False
            for this_datetime in datetime_list:
                # If the state pension changes, this occurs on 6 Apr for the new tax year.
                # We approximate this to the 1 may as we won't get a full months pension until then.
                # This means that the prediction will miss some of the first months state pension but
                # we accept this for purposes of this report.
                if this_datetime.month == 5 and year_index > 0:
                    state_pension_amount = self._calc_new_account_value(state_pension_amount,
                                                                        self._future_plot_attr_dict.get(FuturePlotGUI.STATE_PENSION_YEARLY_INCREASE_LIST),
                                                                        year_index)

                # Determine if the state pension has started yet
                if this_datetime >= state_pension_start_date:
                    receiving_state_pension = True
                else:
                    receiving_state_pension = False

                # We assume that if the owner is not alive they are not receiving state pension
                # We assume that the partner receives none of the state pension. This may not be
                # the case as pension rules prior to 2016 but for the purposes of this tool
                # this is the assumption.
                if not self._is_pension_owner_alive(owner, this_datetime):
                    receiving_state_pension = False

                # We assume that if your partner dies then their state pension stops. You may get some
                # money from the DWP but for purposes of this prediction we assume worst case.
                if not self._is_partner_alive(owner, this_datetime):
                    receiving_state_pension = False

                if receiving_state_pension:
                    future_table.append([this_datetime, state_pension_amount])
                else:
                    future_table.append([this_datetime, 0.0])

                # If the year has rolled over
                if this_datetime.year != last_datetime.year:
                    last_datetime = this_datetime
                    year_index = year_index + 1

        return future_table

    def _is_pension_owner_alive(self, owner, report_date):
        """@brief Determine if (for the purposes of this report) the pension owner is alive and this pension is owned by you.
           @return True if you are still alive."""
        alive = True
        me = self._pension_owner_list[0]
        partner = self._pension_owner_list[1]
        if owner not in self._pension_owner_list:
            raise Exception(f"{owner} is an unknown pension owner. Must be {me} or {partner}")

        if owner == me:
            me_max_date = self._get_my_max_date()
            if report_date > me_max_date:
                alive = False
        return alive

    def _is_partner_alive(self, owner, report_date):
        """@brief Determine if (for the purposes of this report) your partner is alive and this pension is owned by your partner.
           @return True if they are still alive."""
        alive = True
        me = self._pension_owner_list[0]
        partner = self._pension_owner_list[1]
        if partner not in self._pension_owner_list:
            raise Exception(f"{owner} is an unknown pension owner. Must be {me} or {partner}")

        if owner == partner:
            partner_max_date = self._get_partner_max_date()
            # If partner DOB exists
            if partner_max_date:
                # If partner has died
                if report_date > partner_max_date:
                    alive = False
            # If partner is not listed as having a DOB
            else:
                alive = False

        return alive

    def _get_state_pension_this_month(self, at_date, state_pension_table):
        if len(state_pension_table) == 0:
            return 0

        else:
            amount = state_pension_table[0][1]
            if len(state_pension_table) > 0:
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
        if len(date_value_table) == 0:
            return 0

        else:
            initial_value = None
            if initial_date:
                for row in date_value_table:
                    _date = row[0]
                    _value = row[1]
                    # DEBUG print(f"PJA: initial_date={initial_date}, _date={_date}, _value={_value}, previous_value={previous_value}")
                    # We could linterp this data to try and predict the value at the given initial date. However
                    # this may not be correct due to values not increasing in this fashion (I.E savings accounts
                    # interest paid on a date each year). Therefore as we may not have the data, we choose the
                    # closest value we have.
                    if _date >= initial_date:
                        initial_value = _value
                        break
                    else:
                        initial_value = _value

            if initial_value is None:
                raise Exception("Start date to early. Data is missing for this start date.")

            # DEBUG print(f"PJA: _get_initial_value(): initial_value={initial_value}")
            return initial_value

    def _get_monthly_budget_table(self, datetime_list):
        """@brief Get a table detailing how much we plan to spend each month from our savings and pension."""
        future_table = []
        last_datetime = datetime_list[0]
        monthly_income = float(
            self._future_plot_attr_dict[FuturePlotGUI.MONTHLY_INCOME])
        year_index = 0
        for this_datetime in datetime_list:
            if this_datetime.year == last_datetime.year:
                future_table.append([this_datetime, monthly_income])
            # We check for year rolling over as this is when we expect an increase in our income against inflation.
            else:
                monthly_income = self._calc_new_account_value(monthly_income, self._future_plot_attr_dict.get(
                    FuturePlotGUI.YEARLY_INCREASE_IN_INCOME), year_index)
                future_table.append([this_datetime, monthly_income])
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
            raise Exception(
                "Rate list error. The rate_list must have at least one element.")
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
        new_value = current_value * (1 + selected_rate / 100)
        return new_value


class Plot1GUI(GUIBase):
    """@brief Responsible for plotting the data of the predicted changes in the savings as we draw out money."""

    def __init__(self,
                 name,
                 plot_table,
                 reality_tables=None,
                 final_year=-1,
                 money_ran_out=False,
                 plot_by_year=False):
        """@param name The name of the plot.
           @param plot_table Holds rows that comprise the following
                             0 = date
                             1 = total (savings + pension)
                             2 = pension total
                             3 = savings total
                             4 = monthly income
                             5 = monthly state pension total of both of us.
                             6 = savings_interest (yearly)
                             7 = savings withdrawal this month
                             8 = pension withdrawal this month.
                             9 = spending_this_month
            @param reality_tables If defined this is a list the following tables.
                                  Each row in each table has a 0:Date and 1:value column
                                  0 = personal_pension_table
                                  1 = savings table
                                  2 = total table
                                  3 = monthly spending table
           @param final_year The final year to plot.
                             This allows the caller to limit the length of the plot prediction.
                             If -1 entered then no limit is placed on the plot.
           @param money_ran_out If True the money ran out.
           @param plot_by_year If True the yearly rather than month changes are plotted.
                             """
        self._name = name
        self._plot_table = plot_table
        self._reality_tables = reality_tables
        self._final_year = final_year
        self._money_ran_out = money_ran_out
        self._plot_by_year = plot_by_year

        # If plotting by year make changes to the tables.
        if self._plot_by_year:
            self._plot_table, self._reality_tables = self._group_by_year(self._plot_table, self._reality_tables)

        self._init_gui()

    def _group_plot_table_by_year(self, plot_table):
        """@brief group the values in the plot_table by year and return the resultant table.
           @param plot_table A 2D table (list of rows) containing the predictions.
           @return plot_table The resultant plot table."""
        # First we convert the plot_table to sum the columns excluding the date, total, pension total and savings total columns.
        # The last value for each year is returned in the total, pension total and savings total columns.

        # Convert to DataFrame
        df = pd.DataFrame(plot_table, columns=[
            'date',
            'total',
            'pension total',
            'savings total',
            'monthly income',
            'monthly state pension total of both of us.',
            'savings_interest (yearly)',
            'savings withdrawal this month',
            'pension withdrawal this month',
            'spending_this_month'
        ])

        # Extract year
        df['year'] = df['date'].dt.year

        last_cols = ['total',
                     'pension total',
                     'savings total']

        # Set which columns to sum and which to take last value
        sum_cols = ['monthly income',
                    'monthly state pension total of both of us.',
                    'savings_interest (yearly)',
                    'savings withdrawal this month',
                    'pension withdrawal this month',
                    'spending_this_month']

        # Step 1: Get the last value per year (based on latest date)
        last_vals = df.sort_values('date').groupby('year').last()[last_cols]

        # Step 1: Get the last value per year (based on latest date)
        last_vals = df.sort_values('date').groupby('year').last()[last_cols]

        # Step 2: Sum the remaining columns per year
        sum_vals = df.groupby('year')[sum_cols].sum()

        # Step 3: Combine
        yearly_summary = pd.concat([last_vals, sum_vals], axis=1)

        # convert to list of rows (tuples)
        rows = [(year, *row) for year, row in yearly_summary.iterrows()]

        return rows

    def _update_reality_plot_tables_per_year(self, reality_tables):
        """@brief Modify the reality (historical data) tables to show results per year.
           @param reality_tables A list of four tables.
                  Each row in each table has a 0:Date and 1:value column.
            0 = personal_pension_table
            1 = savings table
            2 = total table
            3 = monthly spending table
            """
        table = reality_tables[3]

        # Load into a DataFrame
        df = pd.DataFrame(table, columns=['date', 'value'])

        # Convert 'date' to datetime
        df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y')

        # Extract year
        df['year'] = df['date'].dt.year

        # Group by year and sum
        yearly_sum = df.groupby('year')['value'].sum()

        # Convert to list of (year, sum) tuples
        output_table = list(yearly_sum.items())

        # Update the monthly spending table with a single value that is the real amount spent each year
        # Initially all years are 0 as they are in the future. As time progresses we have the data to fill in the values.
        # Note that if you are part of the way through the current year the value is the total spent to date.
        reality_tables[3] = output_table

    def _group_by_year(self, plot_table, reality_tables):
        """@brief Table two tables that have dates in them, sum all the columns by year and return the resultant tables.
           @param plot_table A 2D table (list of rows) containing the predictions.
           @param reality_tables A list of tables"""

        plot_table = self._group_plot_table_by_year(plot_table)
        # reality_tables will be None if the show progress button was not selected.
        # Only calculate if set
        if reality_tables:
            self._update_reality_plot_tables_per_year(reality_tables)

        # Currently we don't process reality tables
        return (plot_table, reality_tables)

    def _overlay_reality(self):
        """@return True if the plot shows predicted and real values overlaid."""
        overlay_reality = False
        if self._reality_tables:
            overlay_reality = True
        return overlay_reality

    def _init_gui(self):
        """@brief plot the data in the plot table."""
        with ui.row():
            ui.label(self._name).style('font-size: 32px; font-weight: bold;')

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

        plot_names = ['Total', 'Personal Pension', 'Savings']
        plot_dict = {plot_names[0]: [],
                     plot_names[1]: [],
                     plot_names[2]: []}

        for row in self._plot_table:
            _date = row[0]
            total = row[1]
            personal_pension = row[2]
            savings = row[3]

            plot_dict[plot_names[0]].append((_date, total))
            plot_dict[plot_names[1]].append((_date, personal_pension))
            plot_dict[plot_names[2]].append((_date, savings))

        reality_tables = None
        if self._reality_tables and len(self._reality_tables) == 4:
            reality_tables = self._reality_tables[:3]

        bar_chart = False
        if self._plot_by_year:
            bar_chart = True

        self._do_plot(plot_panel_1,
                      plot_dict,
                      bar_chart=bar_chart,
                      reality_tables=reality_tables,
                      final_year=self._final_year)

        plot_names = ['Monthly budget/income', 'Total state pension', 'Predicted Spending']
        plot_dict = {plot_names[0]: [],
                     plot_names[1]: [],
                     plot_names[2]: []}

        for row in self._plot_table:
            _date = row[0]
            monthly_income = row[4]
            monthly_state_pension = row[5]
            monthly_spending = row[9]

            plot_dict[plot_names[0]].append((_date, monthly_income))
            plot_dict[plot_names[1]].append((_date, monthly_state_pension))
            plot_dict[plot_names[2]].append((_date, monthly_spending))

        monthly_spending_table = None
        if self._reality_tables and len(self._reality_tables) == 4:
            monthly_spending_table = self._reality_tables[3]

        self._do_plot(plot_panel_2,
                      plot_dict,
                      bar_chart=bar_chart,
                      final_year=self._final_year,
                      monthly_spending_table=monthly_spending_table)

        plot_names = ['Savings Interest']
        plot_dict = {plot_names[0]: []}

        for row in self._plot_table:
            _date = row[0]
            savings_interest = row[6]

            plot_dict[plot_names[0]].append((_date, savings_interest))

        self._do_plot(plot_panel_3,
                      plot_dict,
                      bar_chart=True,
                      final_year=self._final_year)

        plot_names = ['Savings withdrawal', 'Pension withdrawal']
        plot_dict = {plot_names[0]: [],
                     plot_names[1]: []}

        for row in self._plot_table:
            _date = row[0]
            savings_withdrawal = row[7]
            pensions_withdrawal = row[8]

            plot_dict[plot_names[0]].append((_date, savings_withdrawal))
            plot_dict[plot_names[1]].append((_date, pensions_withdrawal))

        self._do_plot(plot_panel_4,
                      plot_dict,
                      bar_chart=True,
                      final_year=self._final_year)

    def _get_year(self, obj):
        """@brief Get the year from an object.
           @param obj The obj may be a datetime instance or an int.
           @return The year as an int value."""
        if isinstance(obj, datetime):
            year = obj.year
        elif isinstance(obj, int):
            year = obj
        else:
            raise Exception(f"{obj} is not a datetime or an int object")
        return year

    def _do_plot(self,
                 plot_pane,
                 plot_dict,
                 bar_chart=False,
                 reality_tables=None,
                 final_year=-1,
                 monthly_spending_table=None):
        """@brief Perform a plot of the data in the plot_dict on the plot_pane.
           @param plot_pane The area to plot data on.
           @param plot_dict The dict containing data to be plotted.
                            Each key in the dict is the name of the plot.
                            Each value is a row in the table
                            0 = The date.
                            1 = The value.
           @param bar_chart If True show a bar chart.
            @param reality_tables If defined this is a list the following tables.
                                  Each row in each table has a 0:Date and 1:value column
                                  0 = personal_pension_table
                                  1 = savings table
                                  2 = total table
           @param final_year The final year to plot.
                             This allows the caller to limit the length of the plot prediction.
                             If -1 entered then no limit is placed on the plot.
           @param monthly_spending_table The monthly spending table."""
        fig = go.Figure()

        if reality_tables:

            totals_table = reality_tables[2]
            if len(totals_table) > 0:
                x, y = zip(*totals_table)
                # Convert from Timestamp instances to datetime instances
                datetimes = [ts.to_pydatetime() for ts in x]
                fig.add_trace(go.Scatter(name='Total (reality)',
                                         x=datetimes,
                                         y=y,
                                         mode='lines',
                                         line=dict(dash='solid')))

            pension_table = reality_tables[0]
            if len(pension_table) > 0:
                x, y = zip(*pension_table)
                # Convert from Timestamp instances to datetime instances
                datetimes = [ts.to_pydatetime() for ts in x]
                fig.add_trace(go.Scatter(name='Personal Pension (reality)',
                                         x=datetimes,
                                         y=y,
                                         mode='lines',
                                         line=dict(dash='solid')))

            savings_table = reality_tables[1]
            if len(savings_table) > 0:
                x, y = zip(*savings_table)
                # Convert from Timestamp instances to datetime instances
                datetimes = [ts.to_pydatetime() for ts in x]
                fig.add_trace(go.Scatter(name='Savings (reality)',
                                         x=datetimes,
                                         y=y,
                                         mode='lines',
                                         line=dict(dash='solid')))

        if monthly_spending_table:
            x, y = zip(*monthly_spending_table)
            try:
                # Convert date string list to datetime instances
                datetimes = [datetime.strptime(date, "%d-%m-%Y") for date in x]
            except TypeError:
                years = [int(s) for s in x]
                datetimes = years

            # If the caller wants to limit the number of years we plot over.
            if final_year > 0:
                value_count = 0
                for _date in datetimes:
                    year = self._get_year(_date)
                    if year > final_year:
                        break

                    value_count += 1
                if value_count < len(datetimes):
                    datetimes = datetimes[:value_count]
                    y = y[:value_count]

            # Calculate the average
            if y and len(y) > 0:
                average_monthly_spending_table = sum(y) / len(y)
            else:
                average_monthly_spending_table = 0
            if self._plot_by_year:
                # When plotting yuearly results we sum the monthly spending per year
                # and display this and we don't display the average.
                fig.add_trace(go.Bar(name='Yearly Spending (reality)',
                                     x=datetimes,
                                     y=y))

            else:
                fig.add_trace(go.Scatter(name='Monthly Spending (reality)',
                                         x=datetimes,
                                         y=y,
                                         mode='lines',
                                         line=dict(dash='solid')))
                avgList = [average_monthly_spending_table,]*len(datetimes)
                fig.add_trace(go.Scatter(name='Average monthly Spending (reality)',
                                         x=datetimes,
                                         y=avgList,
                                         mode='lines',
                                         line=dict(dash='solid', width=5)))

        # Prediction traces are always dotted lines
        # as this tends to indicate their unclear nature.
        line_dict = dict(dash='dot')

        max_y = 0
        for plot_name in plot_dict:
            # Skip the monthly budget/income trace as it's the same as the Predicted Spending plot
            if plot_name == 'Monthly budget/income':
                continue
            plot_table = plot_dict[plot_name]
            x, y = zip(*plot_table)
            # If the caller wants to limit the number of years we plot over.
            if final_year > 0:
                value_count = 0
                for _date in x:
                    year = self._get_year(_date)
                    if year > final_year:
                        break
                    value_count += 1
                if value_count < len(x):
                    x = x[:value_count]
                    y = y[:value_count]

            my = max(y)
            if my > max_y:
                max_y = my
            if bar_chart:
                fig.add_trace(go.Bar(name=plot_name, x=x, y=y))
            else:
                # option mode='lines+markers'
                fig.add_trace(go.Scatter(
                    name=plot_name, x=x, y=y, mode='lines', line=line_dict))

        max_y = int(max_y * 1.1)
        fig.update_layout(margin=dict(l=40, r=40, t=40, b=40),
                          showlegend=True,
                          plot_bgcolor="black",       # Background for the plot area
                          paper_bgcolor="black",      # Background for the entire figure
                          # Font color for labels and title
                          font=dict(color="yellow"),
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

        # Let the user know this prediction ran out of money before you, and your partner (if you have one) passed away.
        if self._money_ran_out:
            ui.notify("You ran out of money", type='negative')


class WindowsApp():

    def __init__(self, uio=None):
        self._uio = uio

    def info(self, msg):
        """@brief Show an info level message to the user.
           @param msg The msessage text."""
        if self._uio:
            self._uio.info(msg)

    def _get_startup_file(self):
        """@return Get the abs name of the program first started."""
        return os.path.abspath(sys.argv[0])

    def _get_app_name(self):
        """@return The name of the running program without the .py extension."""
        app_name = self._get_startup_file()
        app_name = os.path.basename(app_name)
        return app_name.replace(".py", "")

    def _get_shortcut_folder(self):
        temp_dir = os.path.join(os.getenv("TEMP"), "my_temp_shortcuts")
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir

    def _get_shortcut(self):
        package_name = self._get_app_name()
        desktop = os.path.join(os.getenv("USERPROFILE"), "Desktop")
        shortcut_path = os.path.join(desktop, f"{package_name}.lnk")
        return shortcut_path

    def create(self, icon_filename=None):
        """@brief Create a start menu item to launch a program.
           @param package_name The name of the package.
           @param icon_filename The name of the icon file."""
        from win32com.client import Dispatch
        package_name = self._get_app_name()
        exe_name = f"{package_name}.exe"

        # Locate the pipx-installed executable
        pipx_venv_path = os.path.expanduser(f"~\\.local\\bin\\{exe_name}")
        if not os.path.isfile(pipx_venv_path):
            raise Exception(f"{pipx_venv_path} file not found.")

        icon_path = None
        if icon_filename:
            icon_path = getAbsFile(icon_filename)
        if icon_path:
            if os.path.isfile(icon_path):
                self.info(f"{icon_path} icon file found.")
            else:
                raise Exception(f"{icon_path} file not found.")

        shortcut_path = self._get_shortcut()

        # Create the shortcut
        shell = Dispatch("WScript.Shell")
        shortcut = shell.CreateShortcut(shortcut_path)
        shortcut.TargetPath = pipx_venv_path  # Path to your executable or script
        shortcut.WorkingDirectory = os.path.dirname(pipx_venv_path)
        shortcut.IconLocation = icon_path  # Optional: Set an icon
        shortcut.Save()

        if not os.path.isfile(shortcut_path):
            raise Exception(f"{shortcut_path} shortcut file missing after creation.")

        self.info(f"{shortcut_path} shortcut created.")

    def delete(self):
        shortcut_path = self._get_shortcut()

        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)
            self.info(f"Removed '{shortcut_path}' shortcut.")
        else:
            raise Exception(f"{shortcut_path} file not found.")


def main():
    """@brief Program entry point"""
    uio = UIO()
    options = None
    try:
        parser = argparse.ArgumentParser(description="A program to attempt to predict and track your finances in retirement.",
                                         formatter_class=argparse.RawDescriptionHelpFormatter)
        parser.add_argument("-d", "--debug",  action='store_true', help="Enable debugging.")
        parser.add_argument("-enable_syslog", action='store_true', help="Enable syslog.")
        parser.add_argument("-p", "--password", help="Password use for encrypting savings and pension details.")
        parser.add_argument("-f", "--folder",   help="The folder to store the retirement finances files in.")
        parser.add_argument("--port", type=int, help="The TCP IP port to serve the GUI on (default = 9090).", default=9090)
        parser.add_argument("--reload",  action='store_true', help="Set nicegui reload = True.")
        if platform.system() == 'Linux':
            parser.add_argument("-a", "--add_gnome_desktop_launcher",  action='store_true', help="Add a Linux gnome desktop launcher.")
            parser.add_argument("-r", "--remove_gnome_desktop_launcher",  action='store_true', help="Remove a Linux gnome desktop launcher.")
        if platform.system() == 'Windows':
            parser.add_argument("-a", "--add_startup_icon",  action='store_true', help="Add a startup icon to the Windows start button.")
            parser.add_argument("-r", "--remove_startup_icon",  action='store_true', help="Remove a startup icon from the Windows start button.")

        options = parser.parse_args()
        uio.enableDebug(options.debug)
        uio.logAll(True)
        uio.enableSyslog(options.enable_syslog, programName="ngt")
        if options.enable_syslog:
            uio.info("Syslog enabled")

        setup_launcher = False
        if platform.system() == 'Linux':
            from p3lib.gnome_desktop_app import GnomeDesktopApp
            if options.add_gnome_desktop_launcher:
                gda = GnomeDesktopApp('savings.png')
                gda.create()
                uio.info("Created gnome desktop application launcher")
                setup_launcher = True

            elif options.remove_gnome_desktop_launcher:
                gda = GnomeDesktopApp('savings.png')
                if gda.delete():
                    uio.info("Deleted gnome desktop application launcher")
                else:
                    uio.info("No gnome desktop application launcher was found to delete.")
                setup_launcher = True

        if platform.system() == 'Windows':
            if options.add_startup_icon:
                windowsApp = WindowsApp(uio=uio)
                windowsApp.create("savings.ico")
                setup_launcher = True

            if options.remove_startup_icon:
                windowsApp = WindowsApp(uio=uio)
                windowsApp.delete()
                setup_launcher = True

        if not setup_launcher:
            uio.info("Starting up, please wait...")
            finances = Finances(uio, options.password, options.folder)
            finances.initGUI(options.debug, port=options.port, reload=options.reload)

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
