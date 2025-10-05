from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret' # change for production
base_dir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'inventory.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class Product(db.Model):
    product_id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500))

    def __repr__(self):
        return f"<Product {self.product_id} - {self.name}>"

class Location(db.Model):
    location_id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(300))

    def __repr__(self):
        return f"<Location {self.location_id} - {self.name}>"

class ProductMovement(db.Model):
    movement_id = db.Column(db.String(50), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    from_location = db.Column(db.String(50), db.ForeignKey('location.location_id'), nullable=True)
    to_location = db.Column(db.String(50), db.ForeignKey('location.location_id'), nullable=True)
    product_id = db.Column(db.String(50), db.ForeignKey('product.product_id'), nullable=False)
    qty = db.Column(db.Integer, nullable=False)

    product = db.relationship('Product', foreign_keys=[product_id])
    from_loc = db.relationship('Location', foreign_keys=[from_location])
    to_loc = db.relationship('Location', foreign_keys=[to_location])

    def __repr__(self):
        return f"<Move {self.movement_id} {self.product_id} {self.qty}>"

# Helper: compute balances per product + location
def compute_balances():
    balances = {}
    moves = ProductMovement.query.order_by(ProductMovement.timestamp).all()
    for m in moves:
        # moving into to_location (from_location may be None)
        if m.to_location:
            key = (m.product_id, m.to_location)
            balances[key] = balances.get(key, 0) + m.qty
        # moving out from from_location
        if m.from_location:
            key = (m.product_id, m.from_location)
            balances[key] = balances.get(key, 0) - m.qty
    # convert to list of dict rows for template
    rows = []
    for (pid, lid), qty in balances.items():
        product = Product.query.get(pid)
        location = Location.query.get(lid)
        rows.append({
            'product_id': pid,
            'product_name': product.name if product else pid,
            'location_id': lid,
            'location_name': location.name if location else lid,
            'qty': qty
        })
    # sort for display
    rows.sort(key=lambda r: (r['product_name'], r['location_name']))
    return rows

# --- Dashboard / index ---
@app.route('/')
def index():
    products_count = Product.query.count()
    locations_count = Location.query.count()
    movements_count = ProductMovement.query.count()
    recent_moves = ProductMovement.query.order_by(ProductMovement.timestamp.desc()).limit(6).all()
    rows = compute_balances()
    return render_template('index.html',
                            products_count=products_count,
                            locations_count=locations_count,
                            movements_count=movements_count,
                            recent_moves=recent_moves,
                            rows=rows)

# --- INVENTORY BALANCE (The fix for the BuildError!) ---
@app.route('/balance')
def balance():
    """Renders the inventory balance/stock grid page."""
    # Use the existing helper function to get the data
    rows = compute_balances()
    # Get all products and locations to build the grid structure in the template
    products = Product.query.all()
    locations = Location.query.all()
    return render_template('balance.html', rows=rows, products=products, locations=locations)


# --- Products ---
@app.route('/products')
def products():
    items = Product.query.all()
    return render_template('products.html', products=items)

@app.route('/products/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        pid = request.form['product_id'].strip()
        name = request.form['name'].strip()
        desc = request.form.get('description', '').strip()
        if not pid or not name:
            flash('product id and name required', 'danger')
            return redirect(url_for('add_product'))
        if Product.query.get(pid):
            flash('product id already exists', 'danger')
            return redirect(url_for('add_product'))
        p = Product(product_id=pid, name=name, description=desc)
        db.session.add(p)
        db.session.commit()
        flash('product added', 'success')
        return redirect(url_for('products'))
    return render_template('product_form.html', product=None)

@app.route('/products/edit/<product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    p = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        p.name = request.form['name'].strip()
        p.description = request.form.get('description', '').strip()
        db.session.commit()
        flash('product updated', 'success')
        return redirect(url_for('products'))
    return render_template('product_form.html', product=p)

@app.route('/products/view/<product_id>')
def view_product(product_id):
    p = Product.query.get_or_404(product_id)
    return render_template('product_form.html', product=p, readonly=True)

# --- Locations ---
@app.route('/locations')
def locations():
    items = Location.query.all()
    return render_template('locations.html', locations=items)

@app.route('/locations/add', methods=['GET', 'POST'])
def add_location():
    if request.method == 'POST':
        lid = request.form['location_id'].strip()
        name = request.form['name'].strip()
        addr = request.form.get('address', '').strip()
        if not lid or not name:
            flash('location id and name required', 'danger')
            return redirect(url_for('add_location'))
        if Location.query.get(lid):
            flash('location id already exists', 'danger')
            return redirect(url_for('add_location'))
        l = Location(location_id=lid, name=name, address=addr)
        db.session.add(l)
        db.session.commit()
        flash('location added', 'success')
        return redirect(url_for('locations'))
    return render_template('location_form.html', location=None)

@app.route('/locations/edit/<location_id>', methods=['GET', 'POST'])
def edit_location(location_id):
    loc = Location.query.get_or_404(location_id)
    if request.method == 'POST':
        loc.name = request.form['name'].strip()
        loc.address = request.form.get('address', '').strip()
        db.session.commit()
        flash('location updated', 'success')
        return redirect(url_for('locations'))
    return render_template('location_form.html', location=loc)

@app.route('/locations/view/<location_id>')
def view_location(location_id):
    loc = Location.query.get_or_404(location_id)
    return render_template('location_form.html', location=loc, readonly=True)

# --- Product Movements ---
@app.route('/movements')
def movements():
    moves = ProductMovement.query.order_by(ProductMovement.timestamp.desc()).all()
    return render_template('movements.html', moves=moves)

@app.route('/movements/add', methods=['GET', 'POST'])
def add_movement():
    products = Product.query.all()
    locations = Location.query.all()
    if request.method == 'POST':
        mid = request.form['movement_id'].strip()
        pid = request.form['product_id']
        qty = int(request.form['qty'])
        from_loc = request.form.get('from_location') or None
        to_loc = request.form.get('to_location') or None
        ts_text = request.form.get('timestamp') or None
        if not mid or not pid or qty <= 0:
            flash('movement id, product and positive qty required', 'danger')
            return redirect(url_for('add_movement'))
        if ProductMovement.query.get(mid):
            flash('movement id already exists', 'danger')
            return redirect(url_for('add_movement'))
        if ts_text:
            try:
                ts = datetime.fromisoformat(ts_text)
            except Exception:
                ts = datetime.utcnow()
        else:
            ts = datetime.utcnow()
        m = ProductMovement(movement_id=mid, timestamp=ts, from_location=from_loc, to_location=to_loc, product_id=pid, qty=qty)
        db.session.add(m)
        db.session.commit()
        flash('movement recorded', 'success')
        return redirect(url_for('movements'))
    return render_template('movement_form.html', products=products, locations=locations, movement=None)

@app.route('/movements/view/<movement_id>')
def view_movement(movement_id):
    m = ProductMovement.query.get_or_404(movement_id)
    return render_template('movement_form.html', movement=m, readonly=True, products=Product.query.all(), locations=Location.query.all())

# --- Database init helper ---
@app.cli.command('initdb')
def initdb_command():
    """Initialize the database."""
    db.create_all()
    print('Initialized the database.')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
