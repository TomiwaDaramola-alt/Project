# models/admin.py — Admin data model

class Admin:
    def __init__(self, id=None, username='', password=''):
        self.id = id
        self.username = username
        self.password = password
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username
        }
