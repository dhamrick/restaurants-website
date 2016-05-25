# Begin initial setup
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()
# End initial setup

class User(Base):
	__tablename__= 'user'

	id = Column(Integer, primary_key = True)
	email = Column(String(150), nullable = False)
	name = Column(String(80), nullable = False)
	picture = Column(String(250))


class Restaurant(Base):
	__tablename__ = 'restaurant'

	name = Column(String(80), nullable = False)
	id = Column(Integer, primary_key = True)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)

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
	price = Column(String(8))
	restaurant_id = Column(Integer, ForeignKey('restaurant.id'))
	restaurant = relationship(Restaurant)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)

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
engine = create_engine('sqlite:///restaurantmenuwithusers.db')

Base.metadata.create_all(engine)