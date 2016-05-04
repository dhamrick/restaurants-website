from flask import flash
from flask import Flask
from flask import jsonify
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem

app = Flask(__name__)

engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/')
@app.route('/restaurants/')
def displayRestaurants():
	"""Returns the list of all of the restaurants in the database"""
	# return ("This will list all of the restaurants!")
	# restaurants = session.query(Restaurant).filter_by(id = 10000).all()
	restaurants = session.query(Restaurant).all()

	if not restaurants:
		flash("There are no restaurants!")
	return render_template('restaurants.html', restaurants = restaurants)

@app.route('/restaurant/new/', methods = ['GET', 'POST'])
def newRestaurant():
	"""Returns an HTML form for creating a new restaurant."""
	# return ("This will create a new restaurant!")
	if request.method == 'GET':
		return render_template('newrestaurant.html')
	elif request.method == 'POST':
		newRestaurant = Restaurant(
		                           name = request.form['newRestaurant']
		                           )
		session.add(newRestaurant)
		session.commit()
		flash("The restaurant %s was added!" % newRestaurant.name)
		return redirect(url_for("displayRestaurants"))

@app.route('/restaurant/<int:restaurant_id>/edit/', methods = ['GET', 'POST'])
def editRestaurant(restaurant_id):
	"""Returns an HTML form for editing a restaurant """
	# return ("This will edit restaurant %s's name!" %restaurant_id)
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	if request.method == 'GET':
		return render_template('editrestaurant.html', restaurant = restaurant)
	elif request.method == 'POST':
		oldRestaurantName = restaurant.name
		restaurant.name = request.form['newRestaurantName']
		session.add(restaurant)
		session.commit()
		flash("%s's name changed to %s!" %(oldRestaurantName, restaurant.name))
		return redirect(url_for("displayRestaurants"))

@app.route('/restaurant/<int:restaurant_id>/delete/', methods = ['GET', 'POST'])
def deleteRestaurant(restaurant_id):
	"""Returns an HTML form for deleting the restaurant"""
	# return ("This will delete restaurant %s!" %restaurant_id)
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	if request.method == 'GET':
		return render_template('deleterestaurant.html', restaurant = restaurant)
	elif request.method == 'POST':
		session.delete(restaurant)
		session.commit()
		flash("Restaurant %s was deleted!" %restaurant.name)
		return redirect(url_for("displayRestaurants"))

@app.route('/restaurant/<int:restaurant_id>/')
@app.route('/restaurant/<int:restaurant_id>/menu/')
def displayRestaurantMenu(restaurant_id):
	"""Display's the restaurant's menu"""
	# return ("This will list restaurant %s's menu!" %restaurant_id)
	menuItems = session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
	# menuItems = session.query(MenuItem).filter_by(restaurant_id = 100000).all()
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	if not menuItems:
		flash("There are no menu items for this restaurant!")
	return render_template('menu.html', restaurant = restaurant, items = menuItems)

@app.route('/restaurant/<int:restaurant_id>/menu/new/', methods = ['GET', 'POST'])
def newMenuItem(restaurant_id):
	"""Returns an HTML form for creating a new menu item for the restaurant"""
	# return ("This will create a new menu item for restaurant %s!" %restaurant_id)
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	if request.method == 'GET':
		return (render_template('newmenuitem.html', restaurant = restaurant))
	elif request.method == 'POST':
		newMenuItem = MenuItem(
		                       name = request.form['newMenuItemName'],
		                       price = request.form['newMenuItemPrice'],
		                       description = request.form['newMenuItemDesc'],
		                       course = request.form['newMenuItemCourse'],
		                       restaurant_id = restaurant_id
		                       )
		session.add(newMenuItem)
		session.commit()
		flash("%s successfully added to %s's restaurant!" %(newMenuItem.name, restaurant.name))
		return (redirect(url_for('displayRestaurantMenu', restaurant_id = restaurant.id)))

@app.route('/restaurant/<int:restaurant_id>/menu/<int:menuItem_id>/edit/', methods = ['GET', 'POST'])
def editMenuItem(restaurant_id, menuItem_id):
	"""Returns an HTML form for editing the selecting menu item"""
	# return ("This will edit menu item %s from restaurant %s!" %(menuItem_id, restaurant_id))
	menuItem = session.query(MenuItem).filter_by(id = menuItem_id).one()

	if request.method == 'GET':
		restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
		return render_template('editmenuitem.html', restaurant = restaurant, item = menuItem)

	elif request.method == 'POST':
		empty = True
		if request.form['newMenuItemName']:
			menuItem.name = request.form['newMenuItemName']
			empty = False
		if request.form['newMenuItemPrice']:
			menuItem.price = request.form['newMenuItemPrice']
			empty = False
      	if request.form['newMenuItemDesc']:
      		menuItem.description = request.form['newMenuItemDesc']
      		empty = False
      	if request.form['newMenuItemCourse']:
      		menuItem.course = request.form['newMenuItemCourse']
      		empty = False

      	if empty == True:
      		flash('No changes were made!')
      		return redirect(url_for('displayRestaurantMenu', restaurant_id = restaurant_id))

      	session.add(menuItem)
      	session.commit()
      	flash("Item successfully edited!")
      	return redirect(url_for('displayRestaurantMenu', restaurant_id = restaurant_id))


@app.route('/restaurant/<int:restaurant_id>/menu/<int:menuItem_id>/delete/', methods = ['GET', 'POST'])
def deleteMenuItem(restaurant_id, menuItem_id):
	"""Returns an HTML form for deleting the selected menu item"""
	# return ("This will delete menu item %s from restaurant %s!" %(menuItem_id, restaurant_id))
	menuItem = session.query(MenuItem).filter_by(id = menuItem_id).one()
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	if request.method == 'GET':
		return render_template('deletemenuitem.html', restaurant = restaurant, item = menuItem)
	elif request.method == 'POST':
		session.delete(menuItem)
		session.commit()
		flash("Item successfully deleted!")
		return redirect(url_for('displayRestaurantMenu', restaurant_id = restaurant.id))

@app.route('/retaurants/JSON/')
def restaurantsAPI():
	"""Returns list of restaurants in JSON to API request"""
	# return 'This will display the restuarants JSON output!'
	restaurants = session.query(Restaurant).all()
	return jsonify(restaurants = [restaurant.serialize for restaurant in restaurants])

@app.route ('/restautant/<int:restaurant_id>/menu/JSON/')
def restaurantMenuAPI(restaurant_id):
	"""Returns the restaurant's menu in JSON to API request"""
	menuItems = session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
	return jsonify(menuItems = [(menuItem.name, menuItem.price) for menuItem in menuItems])

@app.route ('/restautant/<int:restaurant_id>/menu/<int:menuItem_id>/JSON/')
def restaurantMenuItemAPI(restaurant_id, menuItem_id):
	"""Returns the restaurant menu item's info. as JSON to API request"""
	# return "This will display the menu item's JSON!"
	menuItem = session.query(MenuItem).filter_by(id = menuItem_id).one()
	return jsonify(menuItem.serialize)

if __name__ == '__main__':
	app.secret_key = 'super_secret_key'
	app.debug = True
	app.run(host = '0.0.0.0', port = 5000)