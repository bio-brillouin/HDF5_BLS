from PySide6.QtWidgets import QTextBrowser

class LogWidget(QTextBrowser):
    def __init__(self, config, parent=None):
        """Initializes the log text browser.
        """
        super().__init__(parent)
        self.setMaximumHeight(self.fontMetrics().height() * config["Log"].getint("Height"))
