import MySQLdb
import requests

db = MySQLdb.connect(host="localhost",user="root",passwd="justgoogleit",db="movie_data_100k")
cur = db.cursor()

def push(poster,id):
	try:
	    cur.execute('''UPDATE movies SET poster=%s where movie_id=%s''',(poster, id))
	   # cursor.execute('''INSERT into students (roll_no,name,cgpi) values (%s,%s,%s)''',(rollno,name,cgpi))
	    db.commit()
	except:
	    print db.rollback()
	    print ("MKK")

def posterMovies():
	query = "SELECT * from movies"
	cur.execute(query)
	res = cur.fetchall()
	for i in range(len(res)):
		j = i + 638
		print(res[j][1].split('(')[0].split(',')[0])
		
		
		payload = {'apikey': "Your Key", 't': res[j][1].split('(')[0].split(',')[0]}
		r = requests.get('http://www.omdbapi.com', params = payload)
		print(j)
		json_data = r.json()
		print(json_data)
		if(json_data['Response'] != 'False'):
			push(json_data['Poster'], res[j][0])

posterMovies()
