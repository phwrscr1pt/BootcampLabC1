#!/usr/bin/env python3
"""
LOCth Shop - Vulnerable Web Application for Cybersecurity Training
===================================================================
WARNING: This application contains intentional security vulnerabilities
for educational purposes only. DO NOT deploy in production!
"""

import time
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, make_response

app = Flask(__name__)
app.secret_key = 'locth-secret-key-2024'

# ============================================================
# WALLET - Initial Balance (stored in session)
# ============================================================
INITIAL_WALLET_BALANCE = 100.00


def get_wallet_balance():
    """Get current wallet balance from session, initialize if not exists."""
    if 'balance' not in session:
        session['balance'] = INITIAL_WALLET_BALANCE
        session.modified = True
    return session['balance']


@app.context_processor
def inject_globals():
    """Make cart count and wallet balance available to all templates."""
    cart_items = session.get('cart', [])
    return {
        'cart_count': len(cart_items),
        'wallet_balance': get_wallet_balance()
    }

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
    {"id": 4, "name": "Royal Crimson Rose", "price": 150.00, "image": "/static/images/flower_4.jpg",
     "description": "Our most exclusive arrangement - rare crimson roses imported from Ecuador."},
    {"id": 5, "name": "Golden Sunflower Bunch", "price": 55.00, "image": "/static/images/flower_5.jpg",
     "description": "Cheerful sunflowers that bring warmth to any room."},
    {"id": 6, "name": "Pink Peony Paradise", "price": 180.00, "image": "/static/images/flower_6.jpg",
     "description": "Luxurious pink peonies in full bloom."},
    {"id": 7, "name": "Lavender Dreams", "price": 85.00, "image": "/static/images/flower_7.jpg",
     "description": "Fragrant lavender stems for a calming atmosphere."},
    {"id": 8, "name": "White Rose Elegance", "price": 95.00, "image": "/static/images/flower_8.jpg",
     "description": "Pure white roses for weddings and special occasions."},
    {"id": 9, "name": "Mixed Floral Symphony", "price": 120.00, "image": "/static/images/flower_9.jpg",
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
    return render_template('shop.html', products=PRODUCTS, wallet_balance=get_wallet_balance())


# ============================================================
# LAB 2: Parameter Tampering Vulnerability (Direct Buy)
# ============================================================
@app.route('/buy', methods=['POST'])
def buy():
    """
    VULNERABLE: Trusts client-side price parameter.
    Wallet Logic:
    - User has session-based balance (starts at $100.00)
    - If price > balance: Insufficient funds (cannot buy)
    - If price <= balance: Transaction succeeds, balance deducted
      - If price < 10: Suspicious transaction detected, FLAG revealed
      - If 10 <= price <= balance: Normal purchase
    """
    product_name = request.form.get('product_name', 'Unknown Product')
    # VULNERABILITY: Trusting client-side price without validation
    try:
        price = float(request.form.get('price', 999))
    except (ValueError, TypeError):
        price = 999.0

    # Get current balance from session
    current_balance = get_wallet_balance()

    # Simulate payment gateway processing time (makes the attack more realistic)
    time.sleep(1.5)

    # Check if user has sufficient funds
    if price > current_balance:
        # Insufficient funds - transaction fails
        return render_template('purchase_result.html',
                               success=False,
                               product_name=product_name,
                               price=price,
                               balance=current_balance,
                               message=f"Transaction Failed: Insufficient Funds.",
                               flag=None)
    else:
        # Deduct from balance
        new_balance = current_balance - price
        session['balance'] = new_balance
        session.modified = True

        # Transaction succeeds - check for suspicious activity
        if price < 10:
            # Suspicious transaction - price tampered!
            return render_template('purchase_result.html',
                                   success=True,
                                   product_name=product_name,
                                   price=price,
                                   balance=current_balance,
                                   new_balance=new_balance,
                                   message=f"Payment Accepted for '{product_name}'!",
                                   suspicious=True,
                                   flag="FLAG{PARAM_TAMPERING_MASTER}")
        else:
            # Normal successful transaction
            return render_template('purchase_result.html',
                                   success=True,
                                   product_name=product_name,
                                   price=price,
                                   balance=current_balance,
                                   new_balance=new_balance,
                                   message=f"Purchase Successful! You bought '{product_name}' for ${price:.2f}.",
                                   suspicious=False,
                                   flag=None)


# ============================================================
# LAB 2 (Cart Version): Shopping Cart Tampering Vulnerability
# ============================================================
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    """
    VULNERABLE: Trusts client-side price parameter.
    Adds item to session cart with the price provided by the client.
    """
    product_name = request.form.get('product_name', 'Unknown Product')
    image_url = request.form.get('image_url', '/static/images/flower_1.jpg')

    # VULNERABILITY: Trusting client-side price without server-side validation
    try:
        price = float(request.form.get('price', 0))
    except (ValueError, TypeError):
        price = 0.0

    # Initialize cart if it doesn't exist
    if 'cart' not in session:
        session['cart'] = []

    # Add item to cart with client-provided price (VULNERABLE!)
    cart_item = {
        'name': product_name,
        'price': price,
        'image': image_url
    }
    session['cart'].append(cart_item)
    session.modified = True

    flash(f'"{product_name}" added to cart!', 'success')
    return redirect(url_for('cart'))


@app.route('/cart')
def cart():
    """Display shopping cart contents."""
    cart_items = session.get('cart', [])
    total = sum(item['price'] for item in cart_items)

    return render_template('cart.html',
                           cart_items=cart_items,
                           total=total,
                           wallet_balance=get_wallet_balance(),
                           item_count=len(cart_items))


@app.route('/checkout', methods=['POST'])
def checkout():
    """
    Process checkout - checks wallet balance against cart total.
    FLAG: If 'Royal Crimson Rose' is purchased AND total < $10, reveal flag.
    """
    cart_items = session.get('cart', [])

    if not cart_items:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('cart'))

    total = sum(item['price'] for item in cart_items)
    current_balance = get_wallet_balance()

    # Simulate payment processing
    time.sleep(1.5)

    # Check if user has sufficient funds
    if total > current_balance:
        return render_template('checkout_result.html',
                               success=False,
                               cart_items=cart_items,
                               total=total,
                               balance=current_balance,
                               message="Transaction Failed: Insufficient Funds.",
                               flag=None)

    # Deduct from balance
    new_balance = current_balance - total
    session['balance'] = new_balance
    session.modified = True

    # Check for the flag condition:
    # Royal Crimson Rose purchased AND total < $10 (price was tampered)
    has_royal_crimson = any(item['name'] == 'Royal Crimson Rose' for item in cart_items)

    if has_royal_crimson and total < 10:
        # Clear cart after successful (suspicious) purchase
        purchased_items = cart_items.copy()
        session['cart'] = []
        session.modified = True

        return render_template('checkout_result.html',
                               success=True,
                               cart_items=purchased_items,
                               total=total,
                               balance=current_balance,
                               new_balance=new_balance,
                               message="Payment Accepted!",
                               suspicious=True,
                               flag="FLAG{CART_TAMPERING_SUCCESS}")
    else:
        # Normal successful purchase
        purchased_items = cart_items.copy()
        session['cart'] = []
        session.modified = True

        return render_template('checkout_result.html',
                               success=True,
                               cart_items=purchased_items,
                               total=total,
                               balance=current_balance,
                               new_balance=new_balance,
                               message="Purchase Successful! Thank you for your order.",
                               suspicious=False,
                               flag=None)


@app.route('/clear_cart')
def clear_cart():
    """Clear all items from the shopping cart."""
    session['cart'] = []
    session.modified = True
    flash('Cart has been cleared.', 'info')
    return redirect(url_for('shop'))


@app.route('/reset_balance')
def reset_balance():
    """Reset wallet balance to initial value (for testing purposes)."""
    session['balance'] = INITIAL_WALLET_BALANCE
    session['cart'] = []
    session.modified = True
    flash(f'Wallet balance reset to ${INITIAL_WALLET_BALANCE:.2f} and cart cleared.', 'success')
    return redirect(url_for('shop'))


# ============================================================
# LAB 3: User-Agent Spoofing Vulnerability
# ============================================================
# Mock data for admin dashboard
ADMIN_STATS = {
    "revenue": 15204.50,
    "active_users": 1024,
    "pending_orders": 5,
    "total_orders": 342
}

RECENT_ORDERS = [
    {"id": "ORD-2026-0342", "customer": "Emily Watson", "product": "Pink Peony Paradise", "amount": 180.00, "status": "Delivered"},
    {"id": "ORD-2026-0341", "customer": "Michael Chen", "product": "Royal Crimson Rose", "amount": 150.00, "status": "Shipped"},
    {"id": "ORD-2026-0340", "customer": "Sarah Johnson", "product": "Elegant Rose Bouquet", "amount": 89.99, "status": "Processing"},
    {"id": "ORD-2026-0339", "customer": "David Kim", "product": "Exotic Orchid Collection", "amount": 200.00, "status": "Delivered"},
    {"id": "ORD-2026-0338", "customer": "Lisa Brown", "product": "Lavender Dreams", "amount": 85.00, "status": "Pending"},
]

@app.route('/admin')
def admin():
    """
    VULNERABLE: Checks User-Agent header for access control.
    If User-Agent contains 'iPhone', grants access to full admin dashboard.
    The flag is hidden in the System Settings tab as 'Server Environment Secret'.
    """
    user_agent = request.headers.get('User-Agent', '')

    if 'iPhone' in user_agent:
        # Access granted - render full admin dashboard with sensitive data
        return render_template('admin_dashboard.html',
                               stats=ADMIN_STATS,
                               recent_orders=RECENT_ORDERS,
                               api_key="sk_live_LOCth2026_xK9mP2vL8nQ4rT6wY",
                               flag="FLAG{USER_AGENT_SPOOFING_IS_EASY}")
    else:
        # Access denied - return 403 error page
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
# LAB 6: HTTP Method Discovery & Tampering
# ============================================================
# Mock news data for the API
NEWS_DATA = [
    {"id": 1, "title": "Welcome to LOCth Shop!", "content": "We're excited to launch our new floral boutique."},
    {"id": 2, "title": "Spring Sale - 20% Off!", "content": "Enjoy discounts on all arrangements this season."},
    {"id": 3, "title": "New Orchid Collection", "content": "Rare exotic orchids now available in store."},
]

# ============================================================
# LAB 7: HTTP Methods - Announcements API
# ============================================================
# In-memory announcements list
announcements = [
    {"id": 1, "title": "Store Hours Update", "content": "We are now open from 9 AM to 9 PM daily."},
    {"id": 2, "title": "Secret Admin Note", "content": "SECRET_FLAG{HTTP_DELETE_METHOD_DISCOVERED}"},
    {"id": 3, "title": "Holiday Specials", "content": "Check out our holiday flower arrangements!"},
]


@app.route('/api/news', methods=['GET', 'POST', 'DELETE', 'OPTIONS'])
def api_news():
    """
    VULNERABLE: Hidden DELETE method accessible via HTTP method tampering.
    Students must use OPTIONS to discover available methods, then use DELETE to get the flag.
    """
    if request.method == 'OPTIONS':
        # The Recon Step: Reveal available methods in the Allow header
        response = make_response('', 200)
        response.headers['Allow'] = 'GET, POST, DELETE, OPTIONS'
        response.headers['Content-Type'] = 'text/plain'
        return response

    elif request.method == 'GET':
        # Normal operation: return news list
        return jsonify({"status": "success", "news": NEWS_DATA})

    elif request.method == 'POST':
        # Decoy: appears to allow posting but fails
        return jsonify({"status": "failed", "message": "Read-only mode. News posting is disabled."}), 403

    elif request.method == 'DELETE':
        # The Exploit Step: Hidden functionality reveals the flag
        return jsonify({
            "status": "success",
            "message": "All news deleted successfully.",
            "flag": "FLAG{HTTP_OPTIONS_METHOD_IS_USEFUL}"
        })


@app.route('/announcements', methods=['GET', 'POST'])
def handle_announcements():
    """
    LAB 7: Announcements endpoint with multiple HTTP methods.
    GET: Render announcements page.
    POST: Create a new announcement (VULNERABLE - no auth required).
    """
    if request.method == 'GET':
        return render_template('announcements.html', news=announcements)

    elif request.method == 'POST':
        # Create new announcement from JSON data
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No JSON data provided."}), 400

        # Auto-generate new ID
        new_id = max((a['id'] for a in announcements), default=0) + 1
        new_announcement = {
            "id": new_id,
            "title": data.get('title', 'Untitled'),
            "content": data.get('content', '')
        }
        announcements.append(new_announcement)

        return jsonify({
            "status": "success",
            "message": "Announcement created successfully.",
            "announcement": new_announcement
        }), 201


@app.route('/announcements/<int:announcement_id>', methods=['DELETE', 'PUT', 'PATCH'])
def modify_announcement(announcement_id):
    """
    LAB 7: Modify an announcement by ID.
    DELETE: Remove the announcement.
    PUT: Completely replace the announcement.
    PATCH: Partially update the announcement.
    VULNERABLE: No authentication required for any operation.
    """
    # Find the announcement
    announcement_index = None
    for i, announcement in enumerate(announcements):
        if announcement['id'] == announcement_id:
            announcement_index = i
            break

    if announcement_index is None:
        return jsonify({
            "status": "error",
            "message": f"Announcement with ID {announcement_id} not found."
        }), 404

    if request.method == 'DELETE':
        deleted = announcements.pop(announcement_index)
        return jsonify({
            "status": "success",
            "message": f"Announcement '{deleted['title']}' deleted successfully.",
            "deleted": deleted
        }), 200

    elif request.method == 'PUT':
        # Complete replacement
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No JSON data provided."}), 400

        announcements[announcement_index] = {
            "id": announcement_id,
            "title": data.get('title', 'Untitled'),
            "content": data.get('content', '')
        }
        return jsonify({
            "status": "success",
            "message": "Announcement replaced successfully.",
            "announcement": announcements[announcement_index]
        }), 200

    elif request.method == 'PATCH':
        # Partial update
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No JSON data provided."}), 400

        if 'title' in data:
            announcements[announcement_index]['title'] = data['title']
        if 'content' in data:
            announcements[announcement_index]['content'] = data['content']

        return jsonify({
            "status": "success",
            "message": "Announcement updated successfully.",
            "announcement": announcements[announcement_index]
        }), 200


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
    print("  - Lab 6: HTTP Method Tampering (/api/news)")
    print("  - Lab 7: HTTP Methods (/announcements)")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5000, debug=True)
