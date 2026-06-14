# models/news.py — News data model

class News:
    def __init__(self, id=None, title=''):
        self.id = id
        self.title = title
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title
        }
