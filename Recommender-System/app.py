from __future__ import print_function
from flask import Flask, flash, Response, redirect, url_for, request, session, abort, render_template, send_file
import requests
import json
import MySQLdb
import hashlib
import Recommender.popularity_recommender as recommender

db = MySQLdb.connect(host="localhost",user="root",passwd="justgoogleit",db="movie_data_100k")
cur = db.cursor()

app = Flask(__name__)

app.config.update(
    DEBUG = True,
    SECRET_KEY = 'secret_xxx'
)

@app.route('/')
def index():
	if 'id' in session:
		name = session['name']
		return render_template('index.html', name=name)
	else:
		return render_template('index.html')


@app.route("/login", methods=["GET", "POST"])
def login():
	if 'id' in session:
		return redirect('/')
	else:
		if request.method == 'POST':
			username = request.form['username']
			password = request.form['password']
			query = "SELECT * from users where username='%s' and password='%s'" %(username, hashlib.md5(password).hexdigest())
			cur.execute(query)
			res = cur.fetchall()
			print(cur.rowcount)    
			if cur.rowcount != 0:
				session['id'] = res[0][0]
				session['name'] = res[0][5]
				return redirect('/')
			else:
				flash('Wrong username or password')
				return render_template('register.html')
		else:
		    return render_template('register.html')

@app.route("/register", methods=["GET", "POST"])
def register():
	if 'id' in session:
		return redirect('/')
	else:
		if request.method == 'POST':
			name = request.form['name']
			username = request.form['username']
			email = request.form['email']
			password = request.form['password']
			query_id = "select max(user_id) from users"
			cur.execute(query_id)
			id = int(cur.fetchall()[0][0]) + 1
			query = "insert into users(user_id, name, username, email, password) values ('%s', '%s', '%s', '%s', '%s' )" %(id, name, username, email, hashlib.md5(password).hexdigest())
			cur.execute(query)
			db.commit()
			if cur.rowcount:
				session['id'] = id
				session['name'] = name
				return redirect('/')
			else:
				flash('Failed to signup')
				render_template('register.html')
		else:
			return render_template('register.html')

@app.route('/recommendation', methods=["GET", "POST"])
def recommendation():
	if 'id' in session:
		x = recommender.Popularity_Recommender(session['id'])
		train_data, test_data = x.trainTestData()
		popularity_recomm = x.popularityModel(train_data, test_data)
		results = list(popularity_recomm)
		res = []
		for i in range(len(results)):
			query = ""
			if request.method == "POST":
				genre = request.form.get('genre')
				print(genre)
				query = "SELECT movie_title, poster from movies where movie_id=%s and %s = 1" %(results[i]['movie_id'], genre)
				print(query)
			else:
				query = "SELECT movie_title, poster from movies where movie_id=%s" %(results[i]['movie_id'])
			cur.execute(query)
			queryresult = cur.fetchall()
			if cur.rowcount != 0:
				x = dict();
				x['title'] = queryresult[0][0].split('(')[0].split(',')[0]
				x['poster'] = queryresult[0][1]
				x['movie_id'] = results[i]['movie_id']
				res.append(x)
		print(res)
		return render_template('recommendation.html', results = res, name=session['name'])
	else:
		flash('Login before recommendation')
		return render_template('register.html')

@app.route('/item_recommendation', methods=["GET", "POST"])
def recommendation_item():
	if 'id' in session:
		x = recommender.Popularity_Recommender(session['id'])
		train_data, test_data = x.trainTestData()
		popularity_recomm = x.itemSimilarityModel(train_data, test_data)
		results = list(popularity_recomm)
		res = []
		for i in range(len(results)):
			query = ""
			if request.method == "POST":
				genre = request.form.get('genre')
				print(genre)
				query = "SELECT movie_title, poster from movies where movie_id=%s and %s = 1" %(results[i]['movie_id'], genre)
				print(query)
			else:
				query = "SELECT movie_title, poster from movies where movie_id=%s" %(results[i]['movie_id'])
			cur.execute(query)
			queryresult = cur.fetchall()
			if cur.rowcount != 0:
				x = dict();
				x['title'] = queryresult[0][0].split('(')[0].split(',')[0]
				x['poster'] = queryresult[0][1]
				x['movie_id'] = results[i]['movie_id']
				res.append(x)
		print(res)
		return render_template('recommendation.html', results = res, name=session['name'])
	else:
		flash('Login before recommendation')
		return render_template('register.html') 


@app.route("/logout")
def logout():
	session.pop('id', None)
	session.pop('name', None)
	return render_template('index.html')


# handle login failed
@app.errorhandler(401)
def page_not_found(e):
    return Response('<p>Login failed</p>')

@app.route('/posterMovies')
def posterMovies():
	query = "SELECT * from movies"
	cur.execute(query)
	res = cur.fetchall()
	for i in range(len(res)):
		print(res[i][1].split('(')[0].split(',')[0])
		payload = {
            'apikey': "Your Key",
            't': res[i][1].split('(')[0].split(',')[0],
        }
		r = requests.get('http://www.omdbapi.com', params = payload)
        json_data = r.json()
        print(json_data['Poster'])
        query2 = "update movies set poster='%s' where movie_id='%s'" %(json_data['Poster'], res[i][0])
        print(query2)
        cur.execute(query2)
        db.commit()
	return redirect('/')

@app.route('/search', methods=["GET", "POST"])
def search():
	if 'id' in session:
		if request.method == "POST":
			title = request.form['movie_title']
			query = "SELECT movie_title, poster, movie_id from movies where movie_title like '%s'" %('%' + title + '%')
			print(query)
			res = []
			cur.execute(query)
			result = cur.fetchall()
			for i in range(len(result)):
				query2 = "SELECT rating from ratings where item_id = '%s' and user_id = '%s'" %(result[i][2], session['id'])
				cur.execute(query2)

				x = dict()
				x['title'] = result[i][0].split('(')[0].split(',')[0]
				x['poster'] = result[i][1]
				x['movie_id'] = result[i][2]
				if(cur.rowcount == 0):
					x['rating'] = 0
				else:
					res_rating = cur.fetchall()
					x['rating'] = res_rating[0][0]
				res.append(x)
			print(res)
			return render_template('search.html', res = res, name=session['name'])
		else:
			return render_template('search.html', res = [], name=session['name'])

	else:
		flash('Login Required')
		return render_template('/')

@app.route('/rating', methods=["POST"])
def rating():
	if 'id' in session:
		movie_id = request.form['movie_id']
		rating = request.form['rating']
		user_id = session['id']
		print(rating)
		query = "select * from ratings where item_id = %s and user_id = %s" %(movie_id, user_id)
		cur.execute(query)
		if cur.rowcount == 0:
			query2 = "insert into ratings (user_id, item_id, rating) values ('%s', '%s', '%s')" %(user_id, movie_id, rating)
			print(query2)
			cur.execute(query2)
			db.commit()
		else:
			print('Here')
			query2 = "update ratings set rating='%s' where user_id='%s' AND item_id='%s'" %(rating, user_id, movie_id)
			print(query2)
			cur.execute(query2)
			db.commit()
		return redirect('/recommendation')
	else:
		flash('Login Required')
		return render_template('/')

if __name__ == "__main__":
	app.run(host="0.0.0.0")
