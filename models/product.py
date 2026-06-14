# models/product.py — Product data model

class Product:
    def __init__(self, id=None, name='', price=0.0, compare_price=None, 
                 description='', image_file='', category='', is_new=False):
        self.id = id
        self.name = name
        self.price = price
        self.compare_price = compare_price
        self.description = description
        self.image_file = image_file
        self.category = category
        self.is_new = is_new
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'compare_price': self.compare_price,
            'description': self.description,
            'image_file': self.image_file,
            'category': self.category,
            'is_new': self.is_new
        }
