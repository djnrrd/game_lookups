"""A module for setting up the logger and custom TK Scrolled Text log handler
"""
import logging
from tkinter import END, Text
from datetime import datetime


def setup_logger(app: 'GameLookupApp', debug: bool = False) -> logging.Logger:
    """Setup the logger for the application that uses the tkinter scrolling
    text box for the logs

    :param app: The tkinter application
    :param debug: If debug messages should be logged
    :return: A Logger object
    """
    # Create textLogger
    text_handler = TkTextHandler(app.doc_log)
    # Create a custom logger and add the Tk text handler
    logger = logging.getLogger('game_lookups')
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.addHandler(text_handler)
    return logger


class TkTextHandler(logging.Handler):
    """This class allows you to log to a Tkinter Text or ScrolledText widget
    Adapted from Moshe Kaplan:
    https://gist.github.com/moshekaplan/c425f861de7bbf28ef06

    :param tk_widget: Tkinter scrolled text widget to write to
    """

    def __init__(self, tk_widget: Text, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # Store a reference to the scrolled Text it will log to
        self.tk_widget = tk_widget

    def emit(self, record) -> None:
        """Override the normal Hanler emit method to write to a tkinter
        scrolled text widget

        :param record: The log record
        """
        def append() -> None:
            """Nested function to call in the program loop
            """
            self.tk_widget.configure(state='normal')
            if record.levelname in ('INFO', 'DEBUG'):
                self.tk_widget.insert(END, f"{record.levelname}", 'green_level')
            else:
                self.tk_widget.insert(END, f"{record.levelname}", 'red_level')
            self.tk_widget.insert(END, f" - "
                                       f"{datetime.now().strftime('%H:%M:%S')}"
                                       f" - ", 'time')
            self.tk_widget.insert(END, f"{record.msg}\n", 'message')

            self.tk_widget.tag_config('green_level', foreground='green')
            self.tk_widget.tag_config('red_level', foreground='red')
            self.tk_widget.configure(state='disabled')
            # Autoscroll to the bottom
            self.tk_widget.yview(END)
        # This is necessary because we can't modify the Text from other
        # threads, we have to add it to the loop
        self.tk_widget.after(0, append)
