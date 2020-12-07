#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel ,sqlite3
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import jinja2
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import ast
from sqlalchemy import update , create_engine
from sqlalchemy.orm import  Session
from flask import Flask
from models import app, db, Venue, Artist, Show

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app.config.from_object('config')
moment = Moment(app)
db.init_app(app)

#db.create_all()

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
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data = []
  venues = Venue.query.all()
  for place in Venue.query.distinct(Venue.city, Venue.state).all():
    data.append({
      "city": place.city ,
      "state": place.state ,
      "venues": [{
      "id": venue.id ,
      "name": venue.name ,
    } for venue in venues if
    venue.city == place.city and venue.state == place.state] 
  })
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

  venueSearch = Venue.query.filter(Venue.name.like('%' + request.form['search_term'] + '%')).all()
  countVenueSearch = Venue.query.filter(Venue.name.like('%' + request.form['search_term'] + '%')).count()

  response={
    "count": countVenueSearch,
    "data": venueSearch
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id

  past_shows = db.session.query(Artist, Show).join(Show).join(Venue).filter(
      Show.venue_id == venue_id,
      Show.artist_id == Artist.id,
      Show.start_time < datetime.now()
    ).all()

  uncoming_shows = db.session.query(Artist, Show).Join(Show).join(Venue).filter(
      Show.venue_id == venue_id,
      Show.artist_id == Artist.id,
      Show.start_time > datetime.now()
    ).all()

  venue = Venue.query.filter_by(venue_id).first_or_404()

  data={
    "id": venue.id,
    "name": venue.name,
    "genres": [venue.genres],
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_show":[{
      "artist_id": artist.id,
      "artist_name": artist.name,
      "artisy_image_link": artist.image_link,
      "start_time": Show.start_time.strftime("%m/%d/%Y, %H:%M")
    } for artist, Show in past_shows],
    "uncoming_shows": [{
      "artist_id": artist.id,
      "artist_name": artist.name,
      "artist_image:linl": artist.image_link,
      "start_time": Show.start_time.strftime("%m/%d/%Y, %H:%M")
    } for artist, Show in uncoming_shows],
    "past_shows_count": len(past_show),
    "uncoming_shows_count": len(uncoming_shows)

}

  #data = list(filter(lambda d: d['id'] == venue_id, [data1, data2, data3]))[0]
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  
  form =VenueForm(request.form, meta={'csrf': False})

  name = request.form['name']
  city = request.form['city']
  state = request.form['state']
  address = request.form['address']
  genres = request.form['genres']
  phone = request.form['phone']
  facebook_link = request.form['facebook_link']
  website = request.form['website']
  image_link = request.form['image_link']
  seeking_talent= request.form['seeking_talent']
  seeking_description= request.form['seeking_description']
  if form.validate():
    try:
      createVenue = Venue(name=name,
                          seeking_description=seeking_description,
                          seeking_talent=seeking_talent,
                          image_link=image_link,
                          website=website,
                          city=city,
                          state=state,
                          address=address, 
                          genres=genres,
                          phone=phone,
                          facebook_link=facebook_link
                          )
      form.populate_obj(createVenue)
      db.session.add(createVenue)
      db.session.commit()
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except ValueError as e:
      print(e)
      flash('An error occurred. Venue ' + request.form['name'] + ' Could not be listed.')
      db.session.rollback()
    finally:
      db.session.close()
  else:
    message = []
    for field, err in form.errors.items():
      message.append(field + ' ' + '|'.join(err))
      flash('Errors ' + str(message))

  return render_template('pages/home.html')

  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  try:
    venue = Venue.query.filter_by(id = venue_id).first_or_404()
    db.session.delete(venue)
    db.session.commit()
    flash('The venuse has been removed togther with all its shows')
    return render_template('pages/home.html')
  except ValueError:
    flash('Iy was not possible to delte this Venue')
  
  return redirect(url_for('venues'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database

  artist = Artist.query.group_by(Artist.id).all()
  data=[]
  for artis in artist:
      data.append({
      "id": artis.id,
      "name": artis.name
      })
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

  artistSearch = Artist.query.filter(Artist.name.ilike('%' + request.form['search_term'] + '%')).all()
  countArtistSearch = Artist.query.filter(Artist.name.ilike('%'+ request.form['search_term'] + '%')).count()


  response={
    "count": countArtistSearch,
    "data": artistSearch
    }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  past_show =db.session.query(Artist, Show).join(Show).join(Venue).filter(
    Show.venue_id == Venue.id,
    Show.artist_id == artist_id,
    Show.start_time < datetime.now()
  ).all()

  uncoming_shows = db.session.query(Artist, Show).join(Show).join(Venue).filter(
    Show.venue_id == Venue.id,
    Show.artist_id == artist_id,
    Shoe.start_time > datetime.now()
  ).all()

  artist = Artist.query.filter_by(id=artist_id).first_or_404()
  data={
    "id": artist.id,
    "name": artist.name,
    "genres": [artist.genres],
    "city": artist.city,
    "state": artist.state,
    "phone": artist,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    'past_show':[{
      "artist_id":artist.id,
      "artist_name":artist.name,
      "artist_image_link":artist.image_link,
      "start_time": Show.start_time.strftime('%m/%d/%Y, %H:%M')
    } for artist, Show in uncoming_shows],
    "past_shows_count": len(past_show),
    "uncoming_shows_count": len(uncoming_shows)
}
 # data = list(filter(lambda d: d['id'] == artist_id, [data1, data2, data3]))[0]
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.filter_by(id=artist_id).first_or_404()
  form = ArtistForm(obj=artist)

  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  form=ArtistForm(request.form, meta={'csrf':False})

  artist = Artist.query.get(artist_id)

  artist.name = request.form['name']
  artist.city = request.form['city']
  artist.state = request.form['state']
  artist.phone = request.form['phone']
  artist.genres = request.form['genres']
  artist.facebook_link = request.form['facebook_link']
  artist.image_link = request.form['image_link']
  artist.seeking_venue = request.form['seeking_venue']
  artist.seeking_description = request.form['seeking_desctription']
  db.session.commit()
  db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue.query.filter_by(id=venue_id).first_or-404()
  form = VenueForm(obj=artist)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  venue = Venue.query.get(venue_id)

  venue.name = request.form['name']
  venue.city = request.form['city']
  venue.state = request.form['state']
  venue.phone = request.form['phone']
  venue.genres = request.form['genres']
  venue.facebook_link = request.fom['facebook_link']
  venue.image_link = request.form['image_link']
  venue.seeking_talent = request.form['seeking_talent']
  venue.seeking_description = request.form['seeking_description']

  db.session.commit()
  db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

  form = ArtistForm(request.form, meta={'csrf': False})

 
  name = request.form['name']
  city = request.form['city']
  genres = request.form['genres']
  phone = request.form['phone']
  facebook_link = request.form['facebook_link']
  image_link = request.form['image_link']
  seeking_venue = request.form['seeking_venue']
  seeking_description = request.form['seeking_description']

  if form.validate():
    try:
      createArtist = Artist(
                            name=name,
                            city=city,
                            genres=genres,
                            phone=phone,
                            facebook_link=facebook_link,
                            seeking_venue=seeking_venue,
                            seeking_description=seeking_description,
                            image_link=image_link
                            )
      form.populate_obj(createArtist)
      db.session.add(createArtist)
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully listed')
    except ValueError as e:
      print(e)
      flash('An error occurred. Artist ' + request.form['name']+ ' could not be listed.')
      db.session.rollback()
    finally:
      db.session.close()
  else:
     message =[]
     for field, err in form.errors.items():
       message.append(field + ' ' + '|'.join(err))
       flash('Errors' + str(message))

  return render_template('pages/home.html')

  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------
@app.route('/shows')
def shows():
  
  data= []
  shows = db.session.query(Show).join(Artist).join(Venue).all()
  for show in shows:
    data.extend=([{
      "venue_id" : show.venue.id,
      "venue_name" : show.venue.name,
      "artist_id" : show.artist.id,
      "artist_name": show.artist.name,
      "artist_image_link" : show.artist.image_link,
      "start_time" : show.start_time.strftime("%m/%d/%Y, %H:%M")
    }])


  return render_template('pages/shows.html',shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead

  form = ShowForm(request.form, meta={'csrf': False})
  artist_id = request.form['artist_id']
  venue_id = request.form['venue_id']
  start_time = request.form['start_time']
  try:

    addShow = Show(
      artist_id=artist_id,
      venue_id=venue_id,
      start_time=start_time
    )
    form.populate_obj(addShow)
    db.session.add(addShow)
    db.session.commit()
    flash('Show was successfully listed!')
  except ValueError as e:
    print(e)
    flash('Ane error occured, Show could not be listed')
    db.session.rollback()
  finally:
    db.session.close()

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
