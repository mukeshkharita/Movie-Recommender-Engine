import numpy as np
import random
import MySQLdb
import scipy.spatial
import scipy.stats
import pickle
from sklearn.cross_validation import KFold
from math import sqrt
import sys
from sklearn.metrics import mean_squared_error

db = MySQLdb.connect(host="localhost",user="root",passwd="YOUR_DB_PASSWORD",db="DB_NAME")
cur = db.cursor()
users = 945
items = 1682

def readingData():
	data = []
	query = "SELECT * from ratings"
	cur.execute(query)
	for row in cur.fetchall():
		r = [int(row[0]), int(row[1]), int(row[2])]
		data.append(r)
	dataMatrix = np.zeros((users,items))
	for e in data:
		dataMatrix[e[0]-1][e[1]-1] = e[2]
	return (data, dataMatrix)

def similarity_item(data):

	item_similarity_cosine = np.zeros((items,items))
	item_similarity_jaccard = np.zeros((items,items))
	item_similarity_pearson = np.zeros((items,items))
	for item1 in range(items):
		for item2 in range(items):
			print(item1, item2)
			if np.count_nonzero(data[:, item1]) and np.count_nonzero(data[:, item2]):
				item_similarity_cosine[item1][item2] = 1-scipy.spatial.distance.cosine(data[:,item1],data[:,item2])
				item_similarity_jaccard[item1][item2] = 1-scipy.spatial.distance.jaccard(data[:,item1],data[:,item2])
				try:
					if not math.isnan(scipy.stats.pearsonr(data[:,item1],data[:,item2])[0]):
						item_similarity_pearson[item1][item2] = scipy.stats.pearsonr(data[:,item1],data[:,item2])[0]
					else:
						item_similarity_pearson[item1][item2] = 0
				except:
					item_similarity_pearson[item1][item2] = 0

	print(item_similarity_cosine, item_similarity_jaccard, item_similarity_pearson)
	pickle.dump( item_similarity_cosine, open( "save.p", "wb" ) )
	pickle.dump( item_similarity_jaccard, open( "save1.p", "wb" ) )
	pickle.dump( item_similarity_pearson, open( "save2.p", "wb" ) )

	return item_similarity_cosine, item_similarity_jaccard, item_similarity_pearson

def cross_validation(data):
	k_fold = KFold(n=len(data), n_folds=10)

	Mat = np.zeros((users,items))
	for e in data:
		Mat[e[0]-1][e[1]-1] = e[2]

	sim_item_cosine, sim_item_jaccard, sim_item_pearson = similarity_item(Mat)

	rmse_cosine = []
	rmse_jaccard = []
	rmse_pearson = []

	for train_indices, test_indices in k_fold:
		train = [data[i] for i in train_indices]
		test = [data[i] for i in test_indices]

		M = np.zeros((users,items))

		for e in train:
			M[e[0]-1][e[1]-1] = e[2]

		true_rate = []
		pred_rate_cosine = []
		pred_rate_jaccard = []
		pred_rate_pearson = []

		for e in test:
			user = e[0]
			item = e[1]
			true_rate.append(e[2])

			pred_cosine = 3.0
			pred_jaccard = 3.0
			pred_pearson = 3.0


			if np.count_nonzero(M[:,item-1]):
				sim_cosine = sim_item_cosine[item-1]
				sim_jaccard = sim_item_jaccard[item-1]
				sim_pearson = sim_item_pearson[item-1]

				ind = (M[user-1] > 0)

				normal_cosine = np.sum(np.absolute(sim_cosine[ind]))
				normal_jaccard = np.sum(np.absolute(sim_jaccard[ind]))
				normal_pearson = np.sum(np.absolute(sim_pearson[ind]))

				if normal_cosine > 0:
					pred_cosine = np.dot(sim_cosine,M[user-1])/normal_cosine

				if normal_jaccard > 0:
					pred_jaccard = np.dot(sim_jaccard,M[user-1])/normal_jaccard

				if normal_pearson > 0:
					pred_pearson = np.dot(sim_pearson,M[user-1])/normal_pearson
			if pred_cosine < 0:
				pred_cosine = 0

			if pred_cosine > 5:
				pred_cosine = 5

			if pred_jaccard < 0:
				pred_jaccard = 0

			if pred_jaccard > 5:
				pred_jaccard = 5

			if pred_pearson < 0:
				pred_pearson = 0

			if pred_pearson > 5:
				pred_pearson = 5

			pred_rate_cosine.append(pred_cosine)
			pred_rate_jaccard.append(pred_jaccard)
			pred_rate_pearson.append(pred_pearson)

		rmse_cosine.append(sqrt(mean_squared_error(true_rate, pred_rate_cosine)))
		rmse_jaccard.append(sqrt(mean_squared_error(true_rate, pred_rate_jaccard)))
		rmse_pearson.append(sqrt(mean_squared_error(true_rate, pred_rate_pearson)))


	rmse_cosine = sum(rmse_cosine) / float(len(rmse_cosine))
	rmse_pearson = sum(rmse_pearson) / float(len(rmse_pearson))
	rmse_jaccard = sum(rmse_jaccard) / float(len(rmse_jaccard))

	
	f_rmse = open("rmse_item.txt","w")
	f_rmse.write(str(rmse_cosine) + "\t" + str(rmse_jaccard) + "\t" + str(rmse_pearson) + "\n")

	rmse = [rmse_cosine, rmse_jaccard, rmse_pearson]
	req_sim = rmse.index(min(rmse))

	print req_sim
	f_rmse.write(str(req_sim))
	f_rmse.close()

	if req_sim == 0:
		sim_mat_item = sim_item_cosine

	if req_sim == 1:
		sim_mat_item = sim_item_jaccard

	if req_sim == 2:
		sim_mat_item = sim_item_pearson

	return Mat, sim_mat_item

def predict_rating(data):

	M, sim_item = cross_validation(data)

	toBeRated = {"user":[], "item":[]}
	for i in range(items-1):
		toBeRated["item"].append(int(i+1))
		toBeRated["user"].append(int(1))

	pred_rate = []

	fw_w = open('result2.csv','w')

	l = len(toBeRated["user"])
	for e in range(l):
		user = toBeRated["user"][e]
		item = toBeRated["item"][e]

		pred = 3.0

		if np.count_nonzero(M[:,item-1]):
			sim = sim_item[item-1]
			ind = (M[user-1] > 0)
			normal = np.sum(np.absolute(sim[ind]))
			if normal > 0:
				pred = np.dot(sim,M[user-1])/normal

		if pred < 0:
			pred = 0

		if pred > 5:
			pred = 5

		pred_rate.append(pred)
		print str(user) + "," + str(item) + "," + str(pred)
		fw_w.write(str(pred) + "\n")

	fw_w.close()

data, dataMatrix = readingData()
predict_rating(data)
