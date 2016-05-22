# Begin initial setup
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()
# End initial setup

class User(Base):
	__tablename__= 'users'

	id = Column(Integer, primary_key = True)
	email = Column(String(150), primary_key = True)
	name = Column(String(80), nullable = False)
	picture = Column(String(250), nullable = True)


class Restaurant(Base):
	__tablename__ = 'restaurants'

	name = Column(String(80), nullable = False)
	id = Column(Integer, primary_key = True)
	user_id = Column(Integer, ForeignKey('users.id'))
	admin = relationship(User, backref = 'restaurants')

	@property
	def serialize(self):
		return{
			'name': self.name,
			'id': self.id
			}


class MenuItem(Base):
	__tablename__ = 'menu_items'

	name = Column(String(80), nullable = False)
	id = Column(Integer, primary_key = True)
	course = Column(String(10))
	description = Column(String(250))
	price = Column(String(7))
	restaurant_id = Column(Integer, ForeignKey('restaurants.id'))
	restaurant = relationship(Restaurant, backref = 'menu_items')
	user_id = Column(Integer, ForeignKey('users.id'))
	admin = relationship(User, backref = 'menu_items')

	@property
	def serialize(self):
		return{
			'name': self.name,
			'description': self.description,
			'id': self.id,
			'price': self.price,
			'course': self.course
			}

#EOF
# engine = create_engine('sqlite:///restaurantmenuwithusers.db')
engine = create_engine('sqlite:///restaurantmenu.db')

Base.metadata.create_all(engine)