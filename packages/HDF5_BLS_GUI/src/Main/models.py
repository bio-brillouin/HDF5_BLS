from PySide6.QtGui import QStandardItemModel
from PySide6.QtCore import QMimeData

class TreeviewItemModel(QStandardItemModel):
    def mimeData(self, indexes):
        mime_data = QMimeData()
        paths = []
        for index in indexes:
            if index.column() == 0:
                item = self.itemFromIndex(index)
                paths.append(self.get_item_path(item))
        mime_data.setText(",".join(paths))
        return mime_data

    def get_item_path(self, item):
        path = item.text()
        while item.parent():
            item = item.parent()
            path = item.text() + "/" + path
        return path
