#!/usr/bin/env python3
"""
LOCth Shop - Vulnerable Web Application for Cybersecurity Training
===================================================================
WARNING: This application contains intentional security vulnerabilities
for educational purposes only. DO NOT deploy in production!
"""

from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'locth-secret-key-2024'

# ============================================================
# PRODUCT DATA - Maps to local images in /static/images/
# ============================================================
PRODUCTS = [
    {"id": 1, "name": "Elegant Rose Bouquet", "price": 89.99, "image": "/static/images/flower_1.jpg",
     "description": "A stunning arrangement of premium red and pink roses."},
    {"id": 2, "name": "Pure White Lilies", "price": 75.00, "image": "/static/images/flower_2.jpg",
     "description": "Pristine white lilies symbolizing elegance and purity."},
    {"id": 3, "name": "Spring Tulip Collection", "price": 65.00, "image": "/static/images/flower_3.jpg",
     "description": "Vibrant tulips in assorted colors to brighten your day."},
    {"id": 4, "name": "Romantic Red Roses", "price": 120.00, "image": "/static/images/flower_4.jpg",
     "description": "Classic red roses for the perfect romantic gesture."},
    {"id": 5, "name": "Golden Sunflower Bunch", "price": 55.00, "image": "/static/images/flower_5.jpg",
     "description": "Cheerful sunflowers that bring warmth to any room."},
    {"id": 6, "name": "Pink Peony Paradise", "price": 150.00, "image": "/static/images/flower_6.jpg",
     "description": "Luxurious pink peonies in full bloom."},
    {"id": 7, "name": "Lavender Dreams", "price": 85.00, "image": "/static/images/flower_7.jpg",
     "description": "Fragrant lavender stems for a calming atmosphere."},
    {"id": 8, "name": "White Rose Elegance", "price": 95.00, "image": "/static/images/flower_8.jpg",
     "description": "Pure white roses for weddings and special occasions."},
    {"id": 9, "name": "Mixed Floral Symphony", "price": 110.00, "image": "/static/images/flower_9.jpg",
     "description": "A harmonious blend of seasonal flowers."},
    {"id": 10, "name": "Exotic Orchid Collection", "price": 200.00, "image": "/static/images/flower_10.jpg",
     "description": "Rare and exotic orchids for the discerning collector."},
]

# ============================================================
# MOCK USER DATABASE (for IDOR vulnerability)
# ============================================================
USERS_DB = {
    101: {"name": "Admin", "email": "admin@locthshop.com", "role": "Administrator",
          "secret": "FLAG{IDOR_BYPASSED_SUCCESS}"},
    102: {"name": "John Smith", "email": "john@example.com", "role": "Customer", "secret": "No special access"},
    103: {"name": "Jane Doe", "email": "jane@example.com", "role": "Customer", "secret": "No special access"},
    104: {"name": "Bob Wilson", "email": "bob@example.com", "role": "Customer", "secret": "No special access"},
    105: {"name": "Guest User", "email": "guest@locthshop.com", "role": "Guest", "secret": "You are just a guest"},
}


# ============================================================
# ROUTES
# ============================================================

@app.route('/')
def index():
    """Homepage with hero carousel and features."""
    # Get first 3 products for featured section
    featured = PRODUCTS[:3]
    return render_template('index.html', featured_products=featured)


@app.route('/shop')
def shop():
    """Shop page displaying all products."""
    return render_template('shop.html', products=PRODUCTS)


# ============================================================
# LAB 2: Parameter Tampering Vulnerability
# ============================================================
@app.route('/buy', methods=['POST'])
def buy():
    """
    VULNERABLE: Trusts client-side price parameter.
    If price < 10, returns the flag.
    """
    product_name = request.form.get('product_name', 'Unknown Product')
    # VULNERABILITY: Trusting client-side price without validation
    price = float(request.form.get('price', 999))

    if price < 10:
        return render_template('purchase_result.html',
                               success=True,
                               message=f"Congratulations! You purchased '{product_name}' for only ${price:.2f}!",
                               flag="FLAG{PARAM_TAMPERING_MASTER}")
    else:
        return render_template('purchase_result.html',
                               success=True,
                               message=f"Thank you for purchasing '{product_name}' for ${price:.2f}!",
                               flag=None)


# ============================================================
# LAB 3: User-Agent Spoofing Vulnerability
# ============================================================
@app.route('/admin')
def admin():
    """
    VULNERABLE: Checks User-Agent header for access control.
    If User-Agent contains 'iPhone', grants access and returns flag.
    """
    user_agent = request.headers.get('User-Agent', '')

    if 'iPhone' in user_agent:
        return render_template('admin.html',
                               access_granted=True,
                               flag="FLAG{USER_AGENT_SPOOFING_IS_EASY}")
    else:
        return render_template('admin.html',
                               access_granted=False,
                               flag=None), 403


# ============================================================
# LAB 4: Client-Side Bypass Vulnerability
# ============================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    VULNERABLE: Login form with disabled submit button (client-side only).
    Accepts any credentials and returns the flag.
    """
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        # VULNERABILITY: No real authentication, accepts anything
        if username and password:
            return render_template('login_result.html',
                                   success=True,
                                   username=username,
                                   flag="FLAG{HTML_DISABLED_BUTTON_BYPASS}")
        else:
            return render_template('login_result.html',
                                   success=False,
                                   message="Please provide both username and password.")

    return render_template('login.html')


# ============================================================
# LAB 5: IDOR (Insecure Direct Object Reference) Vulnerability
# ============================================================
@app.route('/profile')
def profile():
    """
    VULNERABLE: Accepts user ID parameter without authorization check.
    Default ID 105 (Guest), but ID 101 (Admin) contains the flag.
    """
    # VULNERABILITY: No authorization check, trusts user-provided ID
    user_id = request.args.get('id', 105, type=int)

    user = USERS_DB.get(user_id)

    if user:
        return render_template('profile.html', user=user, user_id=user_id)
    else:
        return render_template('profile.html', user=None, user_id=user_id)


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_code=404, message="Page not found"), 404


@app.errorhandler(500)
def internal_error(e):
    return render_template('error.html', error_code=500, message="Internal server error"), 500


# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    print("=" * 60)
    print("  LOCth Shop - Vulnerable Web Application")
    print("  For Cybersecurity Training Purposes Only!")
    print("=" * 60)
    print("\n  Starting server at http://localhost:5000")
    print("\n  Available Labs:")
    print("  - Lab 2: Parameter Tampering (/buy)")
    print("  - Lab 3: User-Agent Spoofing (/admin)")
    print("  - Lab 4: Client-Side Bypass (/login)")
    print("  - Lab 5: IDOR (/profile?id=XXX)")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5000, debug=True)
