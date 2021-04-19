#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys
from models import db_config, Venue, Artist, Show
from utils.filters import format_datetime

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
db = db_config(app)
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
    data_venue = []
    venues = Venue.query.all()
    venue_places = set()

    for venue in venues:
        venue_places.add((venue.city, venue.state))

    for item in venue_places:
        data_venue.append({
            "city": item[0],
            "state": item[1],
            "venues": []
        })

    def number_upcoming_shows(venue):
        query = Show.query.\
            filter(
                Show.venue_id == venue.id,
                Show.start_time < datetime.now()
        ).count()
        return query

    for venue in venues:
        for element in data_venue:
            if venue.city == element['city'] and venue.state == element['state']:
                element['venues'].append({
                    "id": venue.id,
                    "name": venue.name,
                    "number_upcoming_shows": number_upcoming_shows(venue)
                })

    return render_template('pages/venues.html', areas=data_venue)


@app.route('/venues/search', methods=['POST'])
def search_venues():

    search = request.form.get('search_term', '')
    venues = Venue.query.filter(Venue.name.ilike("%" + search + "%")).all()
    data = []

    def number_upcoming_shows(venue):
        query = Show.query.\
            filter(
                Show.venue_id == venue.id,
                Show.start_time < datetime.now()
        ).count()
        return query

    for venue in venues:
        data.append({
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": number_upcoming_shows(venue),
        })

    response = {
        "count": len(venues),
        "data": data,
    }

    return render_template('pages/search_venues.html', results=response, search_term=search)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

    venue = Venue.query.filter_by(id=venue_id).first()
    if not venue:
        abort(400)

    upcoming_shows = []
    past_shows = []
    shows = Show.query.filter_by(venue_id=venue_id).all()

    for show in shows:
        if show.start_time > datetime.now():
            upcoming_shows.append({
                "artist_id": show.artist_id,
                "artist_name": show.artist.name,
                "artist_image_link": show.artist.image_link,
                "start_time": str(show.start_time)
            })

    for show in shows:
        if show.start_time < datetime.now():
            past_shows.append({
                "artist_id": show.artist_id,
                "artist_name": show.artist.name,
                "artist_image_link": show.artist.image_link,
                "start_time": str(show.start_time)
            })

    venue_info = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template('pages/show_venue.html', venue=venue_info)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

    error = False
    form = VenueForm()
    venue = Venue()
    try:
        venue.name = form.name.data
        venue.genres = form.genres.data
        venue.address = form.address.data
        venue.city = form.city.data
        venue.state = form.state.data
        venue.phone = form.phone.data
        venue.website = form.website_link.data
        venue.facebook_link = form.facebook_link.data
        venue.seeking_talent = form.seeking_talent.data
        venue.seeking_description = form.seeking_description.data
        venue.image_link = form.image_link.data

        db.session.add(venue)
        db.session.commit()
        db.session.close()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()
        if error:
            abort(400)
            flash('An error occured. Venue ' + name + ' could not be listed.')
            return redirect(url_for('index'))
        else:
            flash('Venue ' + request.form['name'] +
                  ' was successfully listed!')
            return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['POST'])
def delete_venue(venue_id):
   
    try:
        venue = Venue.query.filter_by(id=venue_id).first_or_404()
        db.session.delete(venue)
        db.session.commit()
        flash('The venue has been removed together with all of its shows.')
        return render_template('pages/home.html')
    except ValueError:
        flash('It was not possible to delete this Venue')
    return redirect(url_for('venues'))

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    data = []
    artists = Artist.query.all()
    for artist in artists:
        data.append({"id": artist.id, "name": artist.name})
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search = request.form.get('search_term', '')
    artists = Artist.query.filter(Artist.name.ilike("%" + search + "%")).all()
    data = []

    def number_upcoming_shows(artist):
        query = Show.query.\
            filter(
                Show.artist_id == artist.id,
                Show.start_time < datetime.now()
        ).count()
        return query

    for artist in artists:
        data.append({
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": number_upcoming_shows(artist),
        })

    response = {
        "count": len(artists),
        "data": data,
    }

    return render_template('pages/search_artists.html', results=response, search_term=search)



@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

    artist = Artist.query.filter_by(id=artist_id).first()
    if not artist:
        abort(400)

    upcoming_shows = []
    past_shows = []
    shows = Show.query.filter_by(artist_id=artist_id).all()

    for show in shows:
        if show.start_time > datetime.now():
            upcoming_shows.append({
                "venue_id": show.venue_id,
                "venue_name": show.venue.name,
                "venue_image_link": show.venue.image_link,
                "start_time": str(show.start_time)
            })

    for show in shows:
        if show.start_time < datetime.now():
            past_shows.append({
                "venue_id": show.venue_id,
                "venue_name": show.venue.name,
                "venue_image_link": show.venue.image_link,
                "start_time": str(show.start_time)
            })

    artist_info = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template('pages/show_artist.html', artist=artist_info)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    if artist:
        form.name.data = artist.name 
        form.genres.data = artist.genres 
        form.city.data = artist.city 
        form.state.data = artist.state 
        form.phone.data = artist.phone 
        form.website_link.data = artist.website 
        form.facebook_link.data = artist.facebook_link 
        form.seeking_venue.data = artist.seeking_venue 
        form.seeking_description.data = artist.seeking_description 
        form.image_link.data = artist.image_link 
      
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
        error = False
        form = ArtistForm()
        artist = Artist.query.get(artist_id)
        try:
            artist.name = form.name.data
            artist.genres = form.genres.data
            artist.city = form.city.data
            artist.state = form.state.data
            artist.phone = form.phone.data
            artist.website = form.website_link.data
            artist.facebook_link = form.facebook_link.data
            artist.seeking_venue = form.seeking_venue.data
            artist.seeking_description = form.seeking_description.data
            artist.image_link = form.image_link.data

            db.session.commit()
        except:
            error = True
            db.session.rollback()
            print(sys.exc_info())
        finally:
            flash('Artist ' + request.form['name'] + ' was successfully updated!')
            db.session.close()
        if error:
            flash('An error occurred. Artist ' +
            request.form['name'] + ' could not be updated.')
            abort(400)
        else:
            return redirect(url_for('show_artist', artist_id=artist_id))
    # # TODO: take values from the form submitted, and update existing
    # # artist record with ID <artist_id> using the new attributes

    # return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    if venue:
        form.name.data = venue.name 
        form.genres.data = venue.genres 
        form.address.data = venue.address 
        form.city.data = venue.city 
        form.state.data = venue.state 
        form.phone.data = venue.phone 
        form.website_link.data = venue.website 
        form.facebook_link.data = venue.facebook_link 
        form.seeking_talent.data = venue.seeking_talent 
        form.seeking_description.data = venue.seeking_description 
        form.image_link.data = venue.image_link 
      
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    error = False
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    try:
        venue.name = form.name.data
        venue.genres = form.genres.data
        venue.address = form.address.data
        venue.city = form.city.data
        venue.state = form.state.data
        venue.phone = form.phone.data
        venue.website = form.website_link.data
        venue.facebook_link = form.facebook_link.data
        venue.seeking_talent = form.seeking_talent.data
        venue.seeking_description = form.seeking_description.data
        venue.image_link = form.image_link.data

        db.session.commit()
        db.session.close()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()
        if error:
            abort(400)
            flash('An error occured. Venue ' + name + ' could not be updated.')
            return redirect(url_for('show_venue', venue_id=venue_id))
        else:
            flash('Venue ' + request.form['name'] +
                  ' was successfully updated!')
            return render_template('pages/home.html')

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    error = False
    form = ArtistForm()
    artist = Artist()
    try:
        artist.name = form.name.data
        artist.genres = form.genres.data
        artist.city = form.city.data
        artist.state = form.state.data
        artist.phone = form.phone.data
        artist.website = form.website_link.data
        artist.facebook_link = form.facebook_link.data
        artist.seeking_venue = form.seeking_venue.data
        artist.seeking_description = form.seeking_description.data
        artist.image_link = form.image_link.data

        db.session.add(artist)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
        db.session.close()
    if error:
        flash('An error occurred. Artist ' +
              request.form['name'] + ' could not be listed.')
        abort(400)
    else:
        return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    shows = db.session.query(Show).join(Artist).join(Venue).all()
    data = []
    for show in shows:
        data.append({
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": format_datetime(str(show.start_time))
        })
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    error = False
    show = Show()
    form = ShowForm()
    try:
        show.start_time = form.start_time.data
        show.artist_id = form.artist_id.data
        show.venue_id = form.venue_id.data

        db.session.add(show)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()
    if error:
        abort(400)
        flash('An error occurred. Show could not be listed.')
        return redirect(url_for('index'))
    else:
        flash('Show was successfully listed!')
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
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
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
