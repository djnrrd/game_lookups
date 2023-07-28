"""A Module for the main TK application
"""
import tkinter as tk
from tkinter import font as tk_font
from tkinter import scrolledtext, messagebox, DISABLED
from google.auth.exceptions import RefreshError
from game_lookup import text_includes as ti
from game_lookup.logger import setup_logger
from game_lookup.google import get_documents, get_credentials
from game_lookup.config import load_google_credentials, delete_google_credentials
from game_lookup.lookups import start_lookup_thread


class GameLookupApp(tk.Tk):
    """The main app window for Game Lookups

    :param debug: Switch logging to debug mode
    :param kwargs: List of keyword arguments for a Tk applications
    """
    def __init__(self, debug: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        # Main App Setup
        self.title(ti.DOCS_HEADER)
        self.title_font = tk_font.Font(family='Helvetica', size=18,
                                       weight='bold', slant='italic')
        self.geometry('800x360')
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        # Main frame setup
        self.main_frame = DocSelector(self)
        self.main_frame.grid(row=0, column=0, sticky='nsew')
        # Menu bar setup
        self.menu_bar = self._build_menu()
        self.config(menu=self.menu_bar)
        # Main widgets to reference setup
        doc_list_path = 'doc_selector.doc_list.doc_list_lbx'
        self.doc_list = self.nametowidget(doc_list_path)
        # The scrolling text widget creates a frame with a default name
        doc_log_path = 'doc_selector.doc_log.!frame.doc_log_txt'
        self.doc_log = self.nametowidget(doc_log_path)
        start_btn_path = 'doc_selector.doc_action.start_btn'
        self.start_btn = self.nametowidget(start_btn_path)
        # App specific setups
        self.logger = setup_logger(self, debug)
        self.google_credentials = None
        self.google_sheets = []

    def _build_menu(self) -> tk.Menu:
        """Build the main application menu

        :return: the application menu
        """
        menu_bar = tk.Menu(self)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)
        return menu_bar

    def load_doc_list(self) -> None:
        """Load a list of document titles into the scrolling listbox
        """
        self.logger.debug('Starting document load function')
        if self.google_credentials:
            self.logger.debug('Credentials in object, loading list of '
                              'Spreadsheets')
            self.doc_list.delete(0, 'end')
            try:
                self.google_sheets = get_documents(self.google_credentials,
                                                   self.logger)
                for sheet in self.google_sheets:
                    self.doc_list.insert('end', sheet)
            except RefreshError as err:
                self.logger.warning('Credentials have expired, deleting '
                                    'cached credentials.')
                self.google_credentials = None
                delete_google_credentials()
                self.load_doc_list()
        else:
            self.logger.debug('No credentials in object, attempting to load '
                              'from disc')
            self.google_credentials = load_google_credentials()
            if self.google_credentials:
                self.logger.debug('Credentials loaded from disc and added to '
                                  'object')
                self.load_doc_list()
            else:
                self.logger.info('No login credentials saved on disc, '
                                 'launching browser')
                messagebox.showinfo(ti.LOGIN_HEADING, ti.LOGIN_MSG)
                self.google_credentials = get_credentials(self.logger)
                if self.google_credentials:
                    self.logger.debug('Login credentials received from Google '
                                      'and added to object')
                    self.load_doc_list()

    def start_game_lookup(self) -> None:
        """Start looking up the game titles from the Google sheet in GameDB
        """
        idx = self.doc_list.curselection()
        if idx:
            sheet_id = self.google_sheets[idx[0]].id
            self.logger.debug(f"Looking up Sheet ID {sheet_id}")
            self.start_btn['state'] = DISABLED
            start_lookup_thread(sheet_id, self.google_credentials, self.logger)


class DocSelector(tk.Frame):
    """The main frame for selecting a google document and starting the lookups
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(name='doc_selector', *args, **kwargs)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=9)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=9)
        doc_list = DocList(self)
        doc_action = DocAction(self)
        doc_log = DocLog(self)
        doc_list.grid(column=0, rowspan=2, sticky='nsew')
        doc_action.grid(row=0, column=1, sticky='nsew')
        doc_log.grid(row=1, column=1, sticky='nsew')


class DocList(tk.Frame):
    """The frame containing the scrolling list box
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(name='doc_list', *args, **kwargs)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1)
        self._make_list_box()

    def _make_list_box(self) -> None:
        """Create the scrolling list ox
        """
        list_box = tk.Listbox(self, selectmode='single', name='doc_list_lbx')
        list_box.grid(row=0, column=0, sticky='nsew')
        scroll = tk.Scrollbar(self)
        scroll.grid(row=0, column=1, sticky='ns')
        scroll.config(command=list_box.yview)
        list_box.config(yscrollcommand=scroll.set)


class DocAction(tk.Frame):
    """The frame containing the action buttons
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(name='doc_action', *args, **kwargs)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._make_buttons()

    def _make_buttons(self) -> None:
        """Create the action buttons
        """
        start_btn = tk.Button(self, text=ti.START_BTN, name='start_btn',
                              state='normal',
                              command=self.master.master.start_game_lookup)
        start_btn.grid(row=0, column=0, sticky='', padx=5, pady=15)


class DocLog(tk.Frame):
    """The frame containing the log area
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(name='doc_log', *args, **kwargs)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._make_scrolled_txt()

    def _make_scrolled_txt(self) -> None:
        """Create the scrolled text area to be used for the log
        """
        st = scrolledtext.ScrolledText(self, state='disabled',
                                       name='doc_log_txt')
        st.configure(font='TkFixedFont')
        st.grid(column=0, row=0, sticky='nsew')
