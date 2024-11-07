from app import db, User
from werkzeug.security import generate_password_hash, check_password_hash
# Create admin user
admin = User.query.filter_by(email='huyhoangt2201@gmail.com').first()
if not admin:
    admin = User(
        email='huyhoangt2201@gmail.com',
        name='Huy Hoàng',
        password=generate_password_hash('12345678', method='pbkdf2:sha256'),
        role='admin'
    )
    db.session.add(admin)
    db.session.commit()