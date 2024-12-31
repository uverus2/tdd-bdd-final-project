# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    def test_deserialize_not_bool_available(self):
        """It should throw exception if available is wrong value"""
        product = ProductFactory()
        product.create()

        # prepare data
        data = product.serialize()
        data['available'] = 'error'

        # assert
        with self.assertRaises(Exception) as context: 
            product.deserialize(data)
        self.assertIn(str(context.exception), "Invalid type for boolean [available]: <class 'str'>")

    def test_deserialize_wrong_category(self):
        """It should throw exception if category is wrong value"""
        product = ProductFactory()
        product.create()
        
        # prepare data
        data = product.serialize()
        data['category'] = 'INVALID_CATEGORY'

        # assert
        with self.assertRaises(Exception) as context: 
            product.deserialize(data)
        self.assertIn(str(context.exception), "Invalid attribute: INVALID_CATEGORY")     

    def test_deserialize_wrong_body(self):
        """It should throw exception if body is wrong"""
        product = ProductFactory()
        product.create()
        
        # prepare data
        data = []

        # assert
        with self.assertRaises(Exception) as context: 
            product.deserialize(data)
        self.assertIn(str(context.exception), "Invalid product: body of request contained bad or no data list indices must be integers or slices, not str")     
        
    def test_read_a_product(self):
        """It should find the product in the DB"""
        product = ProductFactory()
        product.id = None
        product.create()
        found_product = product.find(product.id)

        # assertions
        self.assertIsNotNone(product.id)
        self.assertEqual(found_product.id, product.id)
        self.assertEqual(found_product.name, product.name)
        self.assertEqual(found_product.description, product.description)
        self.assertEqual(found_product.price, product.price)
        self.assertEqual(found_product.available, product.available)
        self.assertEqual(found_product.category, product.category)

    def test_update_a_product(self):
        """It should Update a Product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        product.description = "Updated"
        product.name = "Hat"
        product.price = 10.00
        original_id = product.id
        product.update()
        self.assertEqual(product.id, original_id)
        self.assertEqual(product.description, "Updated")
        self.assertEqual(product.name, "Hat")
        self.assertEqual(product.price, 10.00)
        products = Product.all()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].id, original_id)
        self.assertEqual(products[0].name, "Hat")
        self.assertEqual(products[0].description, "Updated")
        self.assertEqual(products[0].price, 10.00)

    def test_update_a_product_with_empty_id(self):
        """It should throw exception"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        
        # update product
        product.id = None
        with self.assertRaises(Exception) as context: 
            product.update()
        self.assertEqual(str(context.exception), "Update called with empty ID field")    
        
    def test_delete_a_product(self):
        """It should Delete a Product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        self.assertEqual(len(Product.all()), 1)
        product.delete()
        self.assertEqual(len(Product.all()), 0)

    def test_list_all_products(self):
        """It should List all Products in the database"""
        products = Product.all()
        self.assertEqual(len(Product.all()), 0)
        self.assertEqual(products, [])
        for index in range(5):
            product = ProductFactory()
            product.create()
        self.assertEqual(len(Product.all()), 5)

    def test_find_by_name(self):
        """It should Find a Product by Name"""
        products = ProductFactory.create_batch(5)
        for product in products:
            product.create()
        first_product = Product.all()[0]
        count = len([product for product in products if product.name == first_product.name])
        found_product = Product.find_by_name(first_product.name)
        self.assertEqual(found_product.count(), count)
        for product in found_product:
            self.assertEqual(product.name, first_product.name)

    def test_find_by_availability(self):
        """It should Find Products by Availability"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        first_product = Product.all()[0]
        count = len([product for product in products if product.available == first_product.available])
        available_products = Product.find_by_availability(first_product.available)
        self.assertEqual(available_products.count(), count)
        for product in available_products:
            self.assertEqual(product.available, first_product.available)

    def test_find_by_category(self):
        """It should Find Products by Category"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        first_product = Product.all()[0]
        count = len([product for product in products if product.category == first_product.category])
        products_by_category = Product.find_by_category(first_product.category)
        self.assertEqual(products_by_category.count(), count)
        for product in products_by_category:
            self.assertEqual(product.category, first_product.category)

    def test_find_by_price(self):
        """It should Find Products by Price"""
        products = ProductFactory.create_batch(5)
        for product in products:
            product.create()

        # get product info  
        first_product = Product.all()[0]
        count = len([product for product in products if product.price == first_product.price])
        products_by_price = Product.find_by_price(first_product.price)

        # carry out assertions  
        self.assertEqual(products_by_price.count(), count)
        for product in products_by_price:
            self.assertEqual(product.price, first_product.price)      

    def test_find_by_price_string(self):
        products = ProductFactory.create_batch(5)
        for product in products:
            product.create()

        # update product
        first_product = Product.all()[0]
        first_product.price = "10"
        first_product.update()

        # get product by price
        count = len([product for product in products if product.price == first_product.price])
        products_by_price = Product.find_by_price("10")

        # carry out assertions  
        self.assertEqual(products_by_price.count(), count)
        for product in products_by_price:
            self.assertEqual(product.price, first_product.price)

                
