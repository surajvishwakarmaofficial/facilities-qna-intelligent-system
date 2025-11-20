
class FormFileWrapper:
    """Wrapper to make form file compatible with process_file"""
    def __init__(self, filename: str, content: bytes):
        self.name = filename
        self.filename = filename
        self._content = content
    
    def getbuffer(self):
        return self._content
    
    def seek(self, pos):
        pass

    