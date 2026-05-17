from flask import Flask, render_template, request, redirect, jsonify, session, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Flower


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'super-secret-key'


db.init_app(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def home():
    search = request.args.get('search', '')

    if search:
        flowers = Flower.query.filter(
            Flower.name.ilike(f'%{search}%')
        ).all()
    else:
        flowers = Flower.query.all()

    return render_template('index.html', flowers=flowers)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash('Username already exists')
            return redirect('/register')

        hashed_password = generate_password_hash(password)

        user = User(
            username=username,
            password=hashed_password
        )

        db.session.add(user)
        db.session.commit()

        flash('Registration successful')
        return redirect('/login')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful')
            return redirect('/')

        flash('Invalid credentials')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully')
    return redirect('/')


@app.route('/add_to_cart/<int:flower_id>')
def add_to_cart(flower_id):
    cart = session.get('cart', {})

    flower_id = str(flower_id)

    if flower_id in cart:
        cart[flower_id] += 1
    else:
        cart[flower_id] = 1

    session['cart'] = cart

    flash('Item added to cart')
    return redirect('/')


@app.route('/cart')
def cart():
    cart = session.get('cart', {})

    cart_items = []
    total = 0

    for flower_id, quantity in cart.items():
        flower = Flower.query.get(int(flower_id))

        subtotal = flower.price * quantity
        total += subtotal

        cart_items.append({
            'flower': flower,
            'quantity': quantity,
            'subtotal': subtotal
        })

    return render_template(
        'cart.html',
        cart_items=cart_items,
        total=total
    )


@app.route('/update_cart/<int:flower_id>', methods=['POST'])
def update_cart(flower_id):
    quantity = int(request.form['quantity'])

    cart = session.get('cart', {})

    if quantity <= 0:
        cart.pop(str(flower_id), None)
    else:
        cart[str(flower_id)] = quantity

    session['cart'] = cart

    return redirect('/cart')


@app.route('/remove_from_cart/<int:flower_id>')
def remove_from_cart(flower_id):
    cart = session.get('cart', {})

    cart.pop(str(flower_id), None)

    session['cart'] = cart

    flash('Item removed')

    return redirect('/cart')


@app.route('/pay')
def pay():
    session['cart'] = {}

    return render_template('payment_success.html')


# ---------------- API ENDPOINTS ----------------

@app.route('/api/products')
def api_products():
    flowers = Flower.query.all()

    data = []

    for flower in flowers:
        data.append({
            'id': flower.id,
            'name': flower.name,
            'description': flower.description,
            'price': flower.price
        })

    return jsonify(data)


@app.route('/api/search')
def api_search():
    search = request.args.get('q', '')

    flowers = Flower.query.filter(
        Flower.name.ilike(f'%{search}%')
    ).all()

    data = []

    for flower in flowers:
        data.append({
            'id': flower.id,
            'name': flower.name,
            'price': flower.price
        })

    return jsonify(data)


@app.route('/api/cart/add', methods=['POST'])
def api_add_to_cart():
    data = request.json

    flower_id = str(data['flower_id'])

    cart = session.get('cart', {})

    if flower_id in cart:
        cart[flower_id] += 1
    else:
        cart[flower_id] = 1

    session['cart'] = cart

    return jsonify({
        'message': 'Item added to cart'
    })


@app.route('/api/cart')
def api_cart():
    cart = session.get('cart', {})

    return jsonify(cart)


@app.route('/api/pay', methods=['POST'])
def api_pay():
    session['cart'] = {}

    return jsonify({
        'message': 'Payment successful'
    })


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        if Flower.query.count() == 0:
            flowers = [
                Flower(
                    name='Red Rose',
                    description='Beautiful red roses',
                    price=10,
                    image='rose.jpg'
                ),
                Flower(
                    name='Pink Lily',
                    description='Elegant pink lilies',
                    price=12,
                    image='lily.jpg'
                ),
                Flower(
                    name='Sunflower',
                    description='Bright yellow sunflower',
                    price=9,
                    image='sunflower.jpg'
                ),
                Flower(
                    name='Tulip',
                    description='Colorful tulips',
                    price=20,
                    image='tulip.jpg'
                ),
                Flower(
                    name='Orchid Basket',
                    description='Premium orchid basket',
                    price=25,
                    image='orchid.jpg'
                ),
                Flower(
                    name='Lavender Bundle',
                    description='Fresh lavender flowers',
                    price=15,
                    image='lavender.jpg'
                ),
                Flower(
                    name='Cherry Blossom',
                    description='Delicate pink cherry blossoms',
                    price=22,
                    image='cherry_blossom.jpg'
                ),
                Flower(
                    name='Blue Hydrangea',
                    description='Beautiful blue hydrangea bouquet',
                    price=19,
                    image='hydrangea.jpg'
                ),
                Flower(
                    name='Daisy Mix',
                    description='Mixed daisy flowers',
                    price=11,
                    image='daisy.jpg'
                )
            ]

            db.session.bulk_save_objects(flowers)
            db.session.commit()

    app.run(debug=True)
