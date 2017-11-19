import MySQLdb
import graphlab
import pandas as pd

class Popularity_Recommender():
	def __init__(self, id):
		self.id = id

	def loadData(self):
		print('Loading Data')
		db = MySQLdb.connect(host="localhost",user="root",passwd="justgoogleit",db="movie_data_100k")
		users = graphlab.SFrame.from_sql(db, "Select * from users")
		ratings = graphlab.SFrame.from_sql(db, "Select * from ratings")
		movies = graphlab.SFrame.from_sql(db, "select * from movies")
		return (users)

	def trainTestData(self):
		print('Test Data')
		r_cols = ['user_id', 'movie_id', 'rating', 'unix_timestamp']
		ratings_base = pd.read_csv('/home/mukesh/Projects/Recommender-System/static/data/ua.base', sep='\t', names=r_cols, encoding='latin-1')
		ratings_test = pd.read_csv('/home/mukesh/Projects/Recommender-System/static/data/ua.test', sep='\t', names=r_cols, encoding='latin-1')
		print(ratings_base.shape)
		print(ratings_test.shape)
		train_data = graphlab.SFrame(ratings_base)
		test_data = graphlab.SFrame(ratings_test)
		return (train_data, test_data)

	def popularityModel(self, train_data, test_data):
		popularity_model = graphlab.popularity_recommender.create(train_data, user_id='user_id', item_id='movie_id', target='rating')
		popularity_recomm = popularity_model.recommend(users=[self.id],k=100)
		#print(popularity_recomm.print_rows(num_rows=15))
		#ratings_base.groupby(by='movie_id')['rating'].mean().sort_values(ascending=False).head(20)
		return popularity_recomm

	def itemSimilarityModel(self, train_data, test_data):
		item_sim_model = graphlab.item_similarity_recommender.create(train_data, user_id='user_id', item_id='movie_id', target='rating',similarity_type='pearson')
		item_sim_recomm = item_sim_model.recommend(users=[self.id],k=100)
		return item_sim_recomm