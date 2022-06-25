import json


class JsonFile:
    """
    Context for a JSON file operations
    """
    def __init__(self, filename, filemode):
        self.json_data = None
        self._file = None
        self.filename = filename
        self.filemode = filemode

    def __enter__(self):
        self._file = open(self.filename, self.filemode)
        return self

    def __exit__(self, type, value, traceback):
        self._file.close()

    def read(self):
        self.json_data = json.load(self._file)
        return self.json_data

    def _dump(self, data):
        self._file.seek(0)
        json.dump(data, self._file, indent=4, separators=(", ", ": "), sort_keys=True)
        self._file.truncate()

    def save(self):
        self._dump(self.json_data)

    def write(self, jdata):
        self._dump(jdata)
