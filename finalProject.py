from flask import flash
from flask import Flask
from flask import jsonify
from flask import render_template
from flask import request
from flask import redirect
from flask import session as login_session
from flask import url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem, User

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

import random
import string

app = Flask(__name__)

app.config.from_pyfile('config.py')

CLIENT_ID = json.loads(open('client_secrets.json','r').read())['web']['client_id']
APP_NAME = app.config['APPLICATION_NAME']


engine = create_engine(app.config['DATABASE'])
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()




@app.route('/gconnect', methods=['POST'])
def gconnect():

	# Validate state token
	if request.args.get('state') != login_session['state']:
	    response = make_response(json.dumps('Invalid state parameter.'), 401)
	    response.headers['Content-Type'] = 'application/json'
	    return response
	# Obtain authorization code
	code = request.data

	try:
	    # Upgrade the authorization code into a credentials object
	    oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
	    oauth_flow.redirect_uri = 'postmessage'
	    credentials = oauth_flow.step2_exchange(code)
	    print "\n\n\n TRY statement finished ok"
	except FlowExchangeError:
	    response = make_response(
	        json.dumps('Failed to upgrade the authorization code.'), 401)
	    response.headers['Content-Type'] = 'application/json'
	    return response

	# Check that the access token is valid.
	access_token = credentials.access_token
	url = ('https://www.googleapis.com/oauth2/v3/tokeninfo?access_token=%s'
	       % access_token)
	h = httplib2.Http()
	result = json.loads(h.request(url, 'GET')[1])
	print "\n\n\n %s \n\n\n" % result
	# If there was an error in the access token info, abort.
	if result.get('error') is not None:
		print "\nZOMG, AN ERROR!!\n"
		response = make_response(json.dumps(result.get('error')), 500)
		response.headers['Content-Type'] = 'application/json'

	# Verify that the access token is used for the intended user.
	gplus_id = credentials.id_token['sub']
	if result['sub'] != gplus_id:
	    response = make_response(
	        json.dumps("Token's user ID doesn't match given user ID."), 401)
	    response.headers['Content-Type'] = 'application/json'
	    return response

	# Verify that the access token is valid for this app.
	if result['azp'] != CLIENT_ID:
	    response = make_response(
	        json.dumps("Token's client ID does not match app's."), 401)
	    print "Token's client ID does not match app's."
	    response.headers['Content-Type'] = 'application/json'
	    return response

	stored_credentials = login_session.get('credentials')
	stored_gplus_id = login_session.get('gplus_id')
	if stored_credentials is not None and gplus_id == stored_gplus_id:
	    response = make_response(json.dumps('Current user is already connected.'),
	                             200)
	    response.headers['Content-Type'] = 'application/json'
	    return response

	# Store the access token in the session for later use.
	login_session['credentials'] = credentials.access_token
	login_session['gplus_id'] = gplus_id

	# Get user info
	userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
	params = {'access_token': credentials.access_token, 'alt': 'json'}
	answer = requests.get(userinfo_url, params=params)

	data = answer.json()

	print "\n\nData:%s\n\n" % data

	login_session['username'] = data['name']
	login_session['picture'] = data['picture']
	login_session['email'] = data['email']

	user_id = getUserID(login_session['email'])
	if not userID:
		userID = createUser(login_sessoin)
	login_session['user_id'] = user_id


	output = ''
	output += '<h1>Welcome, '
	output += login_session['username']
	output += '!</h1>'
	output += '<img src="'
	output += login_session['picture']
	output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
	flash("you are now logged in as %s" % login_session['username'])
	print "done!"
	return output

@app.route('/gdisconnect')
def gdisconnect():
	if 'username' not in login_session:
		flash('No user is logged in!')
		return redirect('/login')
	access_token = login_session['credentials']
	print 'In gdisconnect access token is %s' % access_token
	print 'User name is: %s' % login_session['username']
	if access_token is None:
		print 'Access Token is None'
		response = make_response(json.dumps('Current user not connected.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
	h = httplib2.Http()
	result = h.request(url, 'GET')[0]
	print 'result is '
	print result
	if result['status'] == '200':
		del login_session['credentials']
		del login_session['gplus_id']
		del login_session['username']
		del login_session['email']
		del login_session['picture']
		response = make_response(json.dumps('Successfully disconnected.'), 200)
		response.headers['Content-Type'] = 'application/json'
		return response
	else:
		response = make_response(json.dumps('Failed to revoke token for given user.', 400))
		response.headers['Content-Type'] = 'application/json'
		return response


# Create anti-forgery state token
@app.route('/')
@app.route('/login/')
def showLogin():
	state = ''.join(random.choice(string.ascii_uppercase + string.digits)
	                for x in xrange(64))
	login_session['state'] = state
	return render_template('login.htm.j2', STATE = state, clientID = CLIENT_ID)
	# return "The current session state is %s" %login_session['state']

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
	if 'username' not in login_session:
		flash('You need to login to create a new restaurant!')
		return redirect('/login')
	if request.method == 'GET':
		return render_template('newrestaurant.html')
	elif request.method == 'POST':
		newRestaurant = Restaurant(
		                           name = request.form['newRestaurant'],
		                           user_id = login_session['user_id']
		                           )
		session.add(newRestaurant)
		session.commit()
		flash("The restaurant %s was added!" % newRestaurant.name)
		return redirect(url_for("displayRestaurants"))

@app.route('/restaurant/<int:restaurant_id>/edit/', methods = ['GET', 'POST'])
def editRestaurant(restaurant_id):
	"""Edit the name of a restaurant"""
	if 'username' not in login_session:
		flash('You need to login to edit a restaurant!')
		return redirect('/login')
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
	"""Handles GET and POST requests for deleting a restaurant

	GET: Returns an HTML form for deleting the restaurant.
	POST: Deletes the restaurant from the database and the restaurant's menu items.
	"""
	if 'username' not in login_session:
		flash('You need to login to delete a restaurant!')
		return redirect('/login')
	# return ("This will delete restaurant %s!" %restaurant_id)
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	if request.method == 'GET':
		return render_template('deleterestaurant.html', restaurant = restaurant)
	elif request.method == 'POST':
		session.query(MenuItem).filter_by(restaurant_id = restaurant_id).delete()
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
	"""Handles the GET and POST requests for creating a new menu item.

		GET: Returns an HTML form with fields for the information
		POST: Creates new item without verifying all data present
	"""
	if 'username' not in login_session:
		flash('You need to login to create a new menu item!')
		return redirect('/login')
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
		                       restaurant_id = restaurant_id,
		                       user_id = restaurant.user_id
		                       )
		session.add(newMenuItem)
		session.commit()
		flash("%s successfully added to %s's restaurant!" %(newMenuItem.name, restaurant.name))
		return (redirect(url_for('displayRestaurantMenu', restaurant_id = restaurant.id)))

@app.route('/restaurant/<int:restaurant_id>/menu/<int:menuItem_id>/edit/', methods = ['GET', 'POST'])
def editMenuItem(restaurant_id, menuItem_id):
	"""Handles the GET and POST requests for editing menu item

		GET: Returns an HTML form for editing the menu item
		POST: Checks for changes and commits them to database
	"""
	if 'username' not in login_session:
		flash('You need to login to edit menu item!')
		return redirect('/login')
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
	"""Handles the GET and POST requests for deleting a menu item.

		GET: Returns an HTML form for deleting the selected menu item'
		POST: Deletes the menu item from the database
	"""
	if 'username' not in login_session:
		flash('You need to login to delete a menu item!')
		return redirect('/login')
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

def createUser(login_sessoin):
	newUser = User(name = login_session['username'],
	               email = login_session['email'],
	               picture = login_session['picture'])
	session.add(newUser)
	session.commit()
	user = session.query(User).filter_by(email = login_session['email']).one()
	return user.id

def getUserInfo(user_id):
	user = session.query(User).filter_by(id = user_id).one()
	return user

def getUserID(email):
	try:
		user = session.query(User).filter_by(email = email).one()
		return user.id
	except:
		return None

# BEGIN API BLOCK
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
# END API BLOCK


if __name__ == '__main__':
	app.secret_key = app.config['SECRET_KEY']
	app.debug = app.config['DEBUG']
	app.run(host = '0.0.0.0', port = 5000)