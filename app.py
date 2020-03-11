#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    genres = db.Column(db.String())
    address = db.Column(db.String())
    city = db.Column(db.String())
    state = db.Column(db.String())
    phone = db.Column(db.String())
    website = db.Column(db.String())
    image_link = db.Column(db.String())
    facebook_link = db.Column(db.String())
    seeking_talent = db.Column(db.Boolean(),default=False)
    seeking_description = db.Column(db.String())

    # build the venue to show relationship
    venue_shows = db.relationship('Show', cascade="all,delete", backref='venue', lazy=True)

    # implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    city = db.Column(db.String())
    state = db.Column(db.String())
    phone = db.Column(db.String())
    website = db.Column(db.String())
    genres = db.Column(db.String())
    image_link = db.Column(db.String())
    facebook_link = db.Column(db.String())
    seeking_venue = db.Column(db.Boolean(),default=False)
    seeking_description = db.Column(db.String())

    # build the artist to show relationship
    artist_shows = db.relationship('Show', cascade="all,delete", backref='artist', lazy=True)

    # implement any missing fields, as a database migration using Flask-Migrate

# Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

# build the show class with foreign keys on both artist and venue
class Show(db.Model):
    __tablename__ = 'show'
    id = db.Column('id', db.Integer, primary_key=True)
    artist_id = db.Column('artist_id', db.Integer, db.ForeignKey('artist.id'))
    venue_id = db.Column('venue_id', db.Integer, db.ForeignKey('venue.id'))
    start_time = db.Column('start_time', db.DateTime, nullable=False)

db.create_all()

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.

  # pain in the butt to figure out, but this query gets me the 'headers' for each city state breakdown to start our data up
  query = db.session.query(Venue.city, Venue.state).distinct().order_by(Venue.city).order_by(Venue.state)

  # lets start our new data array
  data = []
  # loop through combos of city state
  for city_state_combo in query:

    # set city state to variable for readibility in next query
    distinct_city = city_state_combo.city
    distinct_state = city_state_combo.state

    # query venue table WHERE city and state match previous result
    query2 = db.session.query(Venue).filter(Venue.city == distinct_city, Venue.state == distinct_state).all()

    # start new empty venue object
    venues = []

    # loop through venues only found in city state match
    for venue in query2:
      # build new venue object and append to root venues object
      venue = {
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": 0
      }
      venues.append(venue)

    # now we can build the root venue object using the city, state, and venues object we built previously
    root_venue_object = {
      "city": distinct_city,
      "state": distinct_state,
      "venues": venues
    }
    
    # add each root object to the root data being passed to the template
    data.append(root_venue_object)

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  # build query using generic like - using ilike for insensitive case
  venues = db.session.query(Venue).filter(Venue.name.ilike('%' + request.form.get('search_term') + '%')).all()
  # get count of query for returned number
  search_count = db.session.query(Venue).filter(Venue.name.ilike('%' + request.form.get('search_term') + '%')).count()
  # build response object template is expecting
  response={
    "count": search_count,
    "data": venues
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # replace with real venue data from the venues table, using venue_id
  # get venue by venue_id
  venue = db.session.query(Venue).get(venue_id)
  # query Show table using venue id and < current time to get past shows
  past_shows = db.session.query(Show).filter(Show.venue_id == venue_id, Show.start_time < datetime.now()).all()
  # query Show table using venue id and > current time to get upcoming shows
  upcoming_shows = db.session.query(Show).filter(Show.venue_id == venue_id, Show.start_time > datetime.now()).all()
  # query show table using venue id and < current time to get past show count
  past_shows_count = db.session.query(Show).filter(Show.venue_id == venue_id, Show.start_time < datetime.now()).count()
  # query show table using venue id and > current time to get upcoming show count
  upcoming_shows_count = db.session.query(Show).filter(Show.venue_id == venue_id, Show.start_time > datetime.now()).count()
  # do some string operations to clean the genres data stored to match the formatting of the demo data
  convert_genres = str(venue.genres).replace("{",'').replace("}","").split(",")

  # assemble the new data object using the above queries
  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": convert_genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": [],
    "upcoming_shows": [],
    "past_shows_count": past_shows_count,
    "upcoming_shows_count": upcoming_shows_count
  }

  # loop through past shows and cast the timestamps as strings
  for past_show in past_shows:
    past_show.start_time = str(past_show.start_time)
    past_show.artist_image_link = db.session.query(Artist).get(past_show.artist_id).image_link
    data['past_shows'].append(past_show)

  # loop through upcoming shows and cast the timestamps as strings
  for upcoming_show in upcoming_shows:
    upcoming_show.start_time = str(upcoming_show.start_time)
    upcoming_show.artist_image_link = db.session.query(Artist).get(upcoming_show.artist_id).image_link
    data['upcoming_shows'].append(upcoming_show)

  #sys.stdout.flush()   
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

  try:
    # insert form data as a new Venue record in the db, instead
    name = request.form.get('name')
    genres = request.form.getlist('genres')
    address = request.form.get('address')
    city = request.form.get('city')
    state = request.form.get('state')
    phone = request.form.get('phone')
    website = request.form.get('website')
    image_link = request.form.get('image_link')
    facebook_link = request.form.get('facebook_link')
    seeking_talent = request.form.get('seeking_talent')
    seeking_description = request.form.get('seeking_description')

    # boolean check based on form input to set boolean value to true or false (db does have this default to false)
    if seeking_talent == 'y':
      seeking_talent = True
    else:
      seeking_talent = False

    # build the actual venue item and commit it
    venue = Venue(name=name, address=address, city=city, state=state, phone=phone, seeking_talent=seeking_talent, seeking_description=seeking_description, website=website, facebook_link=facebook_link, image_link=image_link, genres=genres)
    db.session.add(venue)
    db.session.commit()
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
     # on unsuccessful db insert, flash an error instead.
    flash('Venue ' + request.form['name'] + ' was NOT listed!')
    db.session.rollback()
  finally:
    db.session.close()
  # modify data to be the data object returned from db insertion
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # replace with real data returned from querying the database
  artists = Artist.query.all()

  return render_template('pages/artists.html', artists=artists)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  # build query using generic like - using ilike for insensitive case
  artists = db.session.query(Artist).filter(Artist.name.ilike('%' + request.form.get('search_term') + '%')).all()
  # get count of query for returned number
  search_count = db.session.query(Artist).filter(Artist.name.ilike('%' + request.form.get('search_term') + '%')).count()
  # build response object template is expecting
  response={
    "count": search_count,
    "data": artists
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # insert form data as a new Venue record in the db, instead
  try:
    name = request.form.get('name')
    city = request.form.get('city')
    state = request.form.get('state')
    phone = request.form.get('phone')
    genres = request.form.getlist('genres')
    facebook_link = request.form.get('facebook_link')
    image_link = request.form.get('image_link')
    website = request.form.get('website')
    seeking_venue = request.form.get('seeking_venue')
    seeking_description = request.form.get('seeking_description')

    if seeking_venue == 'y':
      seeking_venue = True
    else:
      seeking_venue = False

    artist = Artist(name=name, city=city, state=state, phone=phone, facebook_link=facebook_link, image_link=image_link, genres=genres, website=website, seeking_venue=seeking_venue, seeking_description=seeking_description)
    db.session.add(artist)
    db.session.commit()
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    # on unsuccessful db insert, flash an error instead.
    flash('Artist ' + request.form['name'] + ' was NOT listed!')
    
    db.session.rollback()
  finally:
    db.session.close()
  # modify data to be the data object returned from db insertion
  return render_template('pages/home.html')



@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  # shows the artist page with the given artist_id
  # replace with real artist data from the artist table, using artist_id
  # get artist by artist_id
  artist = db.session.query(Artist).get(artist_id)
  # query Show table using artist id and < current time to get past shows
  past_shows = db.session.query(Show).filter(Show.artist_id == artist_id, Show.start_time < datetime.now()).all()
  # query Show table using artist id and > current time to get upcoming shows
  upcoming_shows = db.session.query(Show).filter(Show.artist_id == artist_id, Show.start_time > datetime.now()).all()
  # query show table using artist id and < current time to get past show count
  past_shows_count = db.session.query(Show).filter(Show.artist_id == artist_id, Show.start_time < datetime.now()).count()
  # query show table using artist id and > current time to get upcoming show count
  upcoming_shows_count = db.session.query(Show).filter(Show.artist_id == artist_id, Show.start_time > datetime.now()).count()
  # do some string operations to clean the genres data stored to match the formatting of the demo data
  convert_genres = str(artist.genres).replace("{",'').replace("}","").split(",")

  # assemble the new data object using the above queries
  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": convert_genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": [],
    "upcoming_shows": [],
    "past_shows_count": past_shows_count,
    "upcoming_shows_count": upcoming_shows_count
  }

  # loop through past shows and cast the timestamps as strings
  for past_show in past_shows:
    past_show.start_time = str(past_show.start_time)
    past_show.venue_image_link = db.session.query(Venue).get(past_show.venue_id).image_link
    data['past_shows'].append(past_show)

  # loop through upcoming shows and cast the timestamps as strings
  for upcoming_show in upcoming_shows:
    upcoming_show.start_time = str(upcoming_show.start_time)
    upcoming_show.venue_image_link = db.session.query(Venue).get(upcoming_show.venue_id).image_link
    data['upcoming_shows'].append(upcoming_show)

  #sys.stdout.flush()   
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()

  artist = db.session.query(Artist).get(artist_id)

  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()

  venue = db.session.query(Venue).get(venue_id)
  
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))



#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  query=Show.query.all()

  # loop through to build new data array

  data = []

  for show in query:
    show = {
      "venue_id": show.venue_id,
      "venue_name": db.session.query(Venue).get(show.venue_id).name,
      "artist_id": show.artist_id,
      "artist_name": db.session.query(Artist).get(show.artist_id).name,
      "artist_image_link": db.session.query(Artist).get(show.artist_id).image_link,
      "start_time": str(show.start_time)
    }
    data.append(show)

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  artist_id = request.form.get('artist_id')
  venue_id = request.form.get('venue_id')
  start_time = request.form.get('start_time')


  show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)

  db.session.add(show)
  db.session.commit()



  # on successful db insert, flash success
  flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
