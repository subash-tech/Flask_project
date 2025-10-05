from app import app, db, Product, Location, ProductMovement
from datetime import datetime, timedelta
import random

def seed():
    with app.app_context():  # ← add this
        db.create_all()
        ProductMovement.query.delete()
        Product.query.delete()
        Location.query.delete()
        db.session.commit()

        # now all the rest of your seeding logic inside this block ↓
        products = [
            Product(product_id='P001', name='Widget A', description='Small blue widget'),
            Product(product_id='P002', name='Widget B', description='Large red widget'),
            Product(product_id='P003', name='Gadget X', description='Electronic gadget'),
            Product(product_id='P004', name='Gadget Y', description='Accessory for Gadget X'),
        ]
        for p in products:
            db.session.add(p)

        locations = [
            Location(location_id='L001', name='Warehouse North', address='North street 12'),
            Location(location_id='L002', name='Warehouse East', address='East road 5'),
            Location(location_id='L003', name='Storefront Main', address='Market lane'),
        ]
        for l in locations:
            db.session.add(l)
        db.session.commit()

        # your add_move() and movements logic here as before...
        print("sample data created")

if __name__ == '__main__':
    seed()
