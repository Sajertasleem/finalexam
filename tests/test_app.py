"""
Comprehensive test suite for Flask CRUD Application

Tests cover:
- Database model functionality
- All CRUD operations (Create, Read, Update, Delete)
- Search functionality
- Form validation
- Error handling
- Route accessibility
"""

import pytest
import os
import sys
from datetime import datetime

# Add parent directory to path to import app
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from app import app, db, User


@pytest.fixture
def client():
    """Create a test client for the Flask application"""
    # Use in-memory SQLite database for testing
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()


@pytest.fixture
def sample_user():
    """Create a sample user for testing"""
    return {
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john.doe@example.com',
        'age': 30,
        'city': 'New York'
    }


@pytest.fixture
def created_user(client, sample_user):
    """Create and return a user in the database"""
    user = User(**sample_user)
    db.session.add(user)
    db.session.commit()
    return user


class TestUserModel:
    """Test User database model"""
    
    def test_user_creation(self, client, sample_user):
        """Test creating a user in the database"""
        user = User(**sample_user)
        db.session.add(user)
        db.session.commit()
        
        assert user.id is not None
        assert user.first_name == sample_user['first_name']
        assert user.last_name == sample_user['last_name']
        assert user.email == sample_user['email']
        assert user.age == sample_user['age']
        assert user.city == sample_user['city']
        assert user.created_at is not None
    
    def test_user_repr(self, client, sample_user):
        """Test user string representation"""
        user = User(**sample_user)
        db.session.add(user)
        db.session.commit()
        
        assert str(user) == f"<User {user.id}: {user.first_name} {user.last_name}>"
    
    def test_user_to_dict(self, client, sample_user):
        """Test user to_dict method"""
        user = User(**sample_user)
        db.session.add(user)
        db.session.commit()
        
        user_dict = user.to_dict()
        assert user_dict['id'] == user.id
        assert user_dict['first_name'] == user.first_name
        assert user_dict['last_name'] == user.last_name
        assert user_dict['email'] == user.email
        assert user_dict['age'] == user.age
        assert user_dict['city'] == user.city
    
    def test_user_email_uniqueness(self, client, sample_user):
        """Test that email must be unique"""
        user1 = User(**sample_user)
        db.session.add(user1)
        db.session.commit()
        
        # Try to create another user with same email
        user2 = User(**sample_user)
        db.session.add(user2)
        
        with pytest.raises(Exception):  # Should raise IntegrityError
            db.session.commit()


class TestIndexRoute:
    """Test index/home route"""
    
    def test_index_route_get(self, client):
        """Test accessing the home page"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'User Management' in response.data or b'All Users' in response.data
    
    def test_index_with_no_users(self, client):
        """Test index page with no users"""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_index_with_users(self, client, created_user):
        """Test index page with users"""
        response = client.get('/')
        assert response.status_code == 200
        assert created_user.first_name.encode() in response.data
        assert created_user.last_name.encode() in response.data


class TestAddUserRoute:
    """Test add user route"""
    
    def test_add_user_get(self, client):
        """Test GET request to add user page"""
        response = client.get('/add')
        assert response.status_code == 200
        assert b'Add' in response.data or b'New User' in response.data
    
    def test_add_user_post_valid(self, client, sample_user):
        """Test POST request with valid data"""
        response = client.post('/add', data=sample_user, follow_redirects=True)
        assert response.status_code == 200
        
        # Check if user was created
        user = User.query.filter_by(email=sample_user['email']).first()
        assert user is not None
        assert user.first_name == sample_user['first_name']
    
    def test_add_user_post_missing_fields(self, client):
        """Test POST request with missing fields"""
        response = client.post('/add', data={'first_name': 'John'}, follow_redirects=True)
        assert response.status_code == 200
        assert b'required' in response.data.lower()
    
    def test_add_user_post_duplicate_email(self, client, sample_user, created_user):
        """Test POST request with duplicate email"""
        response = client.post('/add', data=sample_user, follow_redirects=True)
        assert response.status_code == 200
        assert b'already exists' in response.data.lower() or b'duplicate' in response.data.lower()
    
    def test_add_user_post_invalid_age(self, client, sample_user):
        """Test POST request with invalid age"""
        sample_user['age'] = 'invalid'
        response = client.post('/add', data=sample_user, follow_redirects=True)
        assert response.status_code == 200
        assert b'valid number' in response.data.lower() or b'age' in response.data.lower()
    
    def test_add_user_post_age_out_of_range(self, client, sample_user):
        """Test POST request with age out of range"""
        sample_user['age'] = '200'
        response = client.post('/add', data=sample_user, follow_redirects=True)
        assert response.status_code == 200
        assert b'valid age' in response.data.lower() or b'1-150' in response.data.lower()
    
    def test_add_user_post_negative_age(self, client, sample_user):
        """Test POST request with negative age"""
        sample_user['age'] = '-5'
        response = client.post('/add', data=sample_user, follow_redirects=True)
        assert response.status_code == 200
        assert b'valid age' in response.data.lower()


class TestViewUserRoute:
    """Test view user route"""
    
    def test_view_user_existing(self, client, created_user):
        """Test viewing an existing user"""
        response = client.get(f'/view/{created_user.id}')
        assert response.status_code == 200
        assert created_user.first_name.encode() in response.data
        assert created_user.email.encode() in response.data
    
    def test_view_user_nonexistent(self, client):
        """Test viewing a non-existent user"""
        response = client.get('/view/99999')
        assert response.status_code == 404


class TestUpdateUserRoute:
    """Test update user route"""
    
    def test_update_user_get(self, client, created_user):
        """Test GET request to update user page"""
        response = client.get(f'/update/{created_user.id}')
        assert response.status_code == 200
        assert created_user.first_name.encode() in response.data
    
    def test_update_user_post_valid(self, client, created_user):
        """Test POST request with valid update data"""
        update_data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane.smith@example.com',
            'age': '25',
            'city': 'Los Angeles'
        }
        response = client.post(f'/update/{created_user.id}', data=update_data, follow_redirects=True)
        assert response.status_code == 200
        
        # Check if user was updated
        updated_user = User.query.get(created_user.id)
        assert updated_user.first_name == 'Jane'
        assert updated_user.last_name == 'Smith'
        assert updated_user.email == 'jane.smith@example.com'
    
    def test_update_user_post_same_email(self, client, created_user):
        """Test updating user with same email (should be allowed)"""
        update_data = {
            'first_name': 'John Updated',
            'last_name': created_user.last_name,
            'email': created_user.email,  # Same email
            'age': str(created_user.age),
            'city': created_user.city
        }
        response = client.post(f'/update/{created_user.id}', data=update_data, follow_redirects=True)
        assert response.status_code == 200
        
        updated_user = User.query.get(created_user.id)
        assert updated_user.first_name == 'John Updated'
    
    def test_update_user_post_duplicate_email(self, client, created_user):
        """Test updating user with another user's email"""
        # Create another user
        user2 = User(
            first_name='Jane',
            last_name='Doe',
            email='jane.doe@example.com',
            age=25,
            city='Boston'
        )
        db.session.add(user2)
        db.session.commit()
        
        # Try to update first user with second user's email
        update_data = {
            'first_name': created_user.first_name,
            'last_name': created_user.last_name,
            'email': user2.email,  # Duplicate email
            'age': str(created_user.age),
            'city': created_user.city
        }
        response = client.post(f'/update/{created_user.id}', data=update_data, follow_redirects=True)
        assert response.status_code == 200
        assert b'already exists' in response.data.lower()
    
    def test_update_user_nonexistent(self, client):
        """Test updating a non-existent user"""
        response = client.get('/update/99999')
        assert response.status_code == 404


class TestDeleteUserRoute:
    """Test delete user route"""
    
    def test_delete_user_existing(self, client, created_user):
        """Test deleting an existing user"""
        user_id = created_user.id
        response = client.get(f'/delete/{user_id}', follow_redirects=True)
        assert response.status_code == 200
        
        # Check if user was deleted
        deleted_user = User.query.get(user_id)
        assert deleted_user is None
    
    def test_delete_user_nonexistent(self, client):
        """Test deleting a non-existent user"""
        response = client.get('/delete/99999')
        assert response.status_code == 404


class TestSearchRoute:
    """Test search route"""
    
    def test_search_no_query(self, client):
        """Test search with no query"""
        response = client.get('/search')
        assert response.status_code == 200
    
    def test_search_by_first_name(self, client, created_user):
        """Test searching by first name"""
        response = client.get(f'/search?query={created_user.first_name}')
        assert response.status_code == 200
        assert created_user.first_name.encode() in response.data
    
    def test_search_by_last_name(self, client, created_user):
        """Test searching by last name"""
        response = client.get(f'/search?query={created_user.last_name}')
        assert response.status_code == 200
        assert created_user.last_name.encode() in response.data
    
    def test_search_by_city(self, client, created_user):
        """Test searching by city"""
        response = client.get(f'/search?query={created_user.city}')
        assert response.status_code == 200
        assert created_user.city.encode() in response.data
    
    def test_search_case_insensitive(self, client, created_user):
        """Test that search is case insensitive"""
        query = created_user.first_name.upper()
        response = client.get(f'/search?query={query}')
        assert response.status_code == 200
        assert created_user.first_name.encode() in response.data
    
    def test_search_no_results(self, client):
        """Test search with no results"""
        response = client.get('/search?query=nonexistentuser12345')
        assert response.status_code == 200


class TestErrorHandlers:
    """Test error handlers"""
    
    def test_404_error(self, client):
        """Test 404 error handler"""
        response = client.get('/nonexistent-route')
        assert response.status_code == 404


class TestFormValidation:
    """Test form validation"""
    
    def test_name_length_validation(self, client, sample_user):
        """Test name length validation"""
        # Test first name too short
        sample_user['first_name'] = 'A'
        response = client.post('/add', data=sample_user, follow_redirects=True)
        assert response.status_code == 200
        assert b'2 and 50' in response.data.lower() or b'characters' in response.data.lower()
        
        # Test first name too long
        sample_user['first_name'] = 'A' * 51
        response = client.post('/add', data=sample_user, follow_redirects=True)
        assert response.status_code == 200
    
    def test_city_length_validation(self, client, sample_user):
        """Test city length validation"""
        # Test city too short
        sample_user['city'] = 'A'
        response = client.post('/add', data=sample_user, follow_redirects=True)
        assert response.status_code == 200
    
    def test_empty_string_validation(self, client, sample_user):
        """Test that empty strings are rejected"""
        sample_user['first_name'] = '   '  # Only whitespace
        response = client.post('/add', data=sample_user, follow_redirects=True)
        assert response.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

