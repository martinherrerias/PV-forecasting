import numpy as np
import torch
import os
import math
import torch.nn as nn
import pandas as pd
import matplotlib.pyplot as plt
import LSTMModel
from sklearn.preprocessing import StandardScaler
from torch.autograd import Variable
from DataManagement import get_data, get_features, get_target_Pdc

# Trainings- /Test Set 1
"""data = get_data()
data_min = data

for Irr in ['GHI', 'DHI', 'gti30t187a', 'ENI']:
    data_min = data_min.drop(data_min.index[data_min[Irr]==0])

data_min = data_min.dropna(subset=['GHI', 'BNI', 'DHI', 'gti30t187a', 'ENI', 'Pdc_33'])

time = data_min.t
gti30t187a = data_min.gti30t187a
GHI = data_min.GHI
Ta = data_min.Ta
BNI = data_min.BNI
wdir = data_min.wdir
kt = data_min.kt
Pdc = data_min.Pdc_33
Pdcmean = data.iloc[:, 109:].mean(axis=1)

# Scaling trainings data: Normalization

BNI_norm = BNI/max(BNI)
Ta_norm = Ta/max(Ta)
Pdc_norm = Pdc/max(Pdc)
GHI_norm = GHI/max(GHI)"""


# Trainings- /Test Set 2

features = get_features()
target = get_target_Pdc() # includes Trainings and Test data of target
features.insert(features.shape[1], column="key", value = np.array(range(0,len(features))))
target.insert(target.shape[1], column="key", value = np.array(range(0,len(target))))
tar = target.drop('t', axis=1)

train_x = features[features["dataset"] == "Train"]
test_x = features[features["dataset"] == "Test"]
train_y = tar[tar["dataset"] == "Train"]
test_y = tar[tar["dataset"] == "Test"]

train_y = train_y.drop('dataset', axis=1)
test_y = test_y.drop('dataset', axis=1)

train = train_x.merge(train_y, on="key")
test = test_x.merge(test_y, on="key")

train = train.drop(train.index[train["El"] < 15])
test = test.drop(test.index[test["El"] < 15])

train = train.dropna()
test = test.dropna()

# Include Pdc in Trainingsset       # Normalisert?
Pdc_35_train = train.Pdc_33.shift(periods=7)
Pdc_35_train = Pdc_35_train[14:]
Pdc_35_test = test.Pdc_33.shift(periods=7)
Pdc_35_test = Pdc_35_test[14:]
train = train[0:(len(train)-14)]
test = test[0:(len(test)-14)]
train.insert(len(train.columns), column="Pdc_35", value=Pdc_35_train.values)
test.insert(len(test.columns), column="Pdc_35", value=Pdc_35_test.values)

feature_cols_G = features.filter(regex="GHI").columns.tolist()
feature_cols_B = features.filter(regex="BNI").columns.tolist()
feature_cols = feature_cols_G + feature_cols_B

train_X = train[feature_cols + ["Pdc_35"]].values #
test_X = test[feature_cols + ["Pdc_35"]].values #
train_Y = train[["Pdc_5min"] + ["Pdc_10min"] + ["Pdc_15min"] + ["Pdc_20min"] + ["Pdc_25min"]
            + ["Pdc_30min"] + ["Pdc_35min"] + ["Pdc_40min"] + ["Pdc_45min"] + ["Pdc_50min"]].values
test_Y = test[["Pdc_5min"] + ["Pdc_10min"] + ["Pdc_15min"] + ["Pdc_20min"] + ["Pdc_25min"]
            + ["Pdc_30min"] + ["Pdc_35min"] + ["Pdc_40min"] + ["Pdc_45min"] + ["Pdc_50min"]].values

# Scaler
scaler = StandardScaler()
scaler.fit(train_X)
train_X = scaler.transform(train_X)
test_X = scaler.transform(test_X)

# to torch
X_train = torch.from_numpy(train_X).float()
X_test = torch.from_numpy(test_X).float()
y_train = torch.from_numpy(train_Y).float()
y_test = torch.from_numpy(test_Y).float()
ENI_train = torch.from_numpy(train.ENI.values).float()
ENI_test = torch.from_numpy(test.ENI.values).float()

def initializeNewModel(input_dim, hidden_dim, layer_dim, output_dim):

    # Initializing LSTM
    # input_dim = number of features
    # hidden_dim = number of hidden layer
    # layer_dim = number of stacked LSTM's
    # output_dim = output horizon

    model = LSTMModel.LSTM(input_dim, hidden_dim, layer_dim, output_dim)

    return model

def trainModel(model):

    optimizer = torch.optim.SGD(model.parameters(), lr=1e-4)

    # adjust length to packet size
    batch_size = 200
    seq_dim = 1
    epochs = 10
    iter = 0

    train_loss = []
    test_rmse = []
    test_mae = []
    test_mbe = []

    results = pd.DataFrame()
    metric = pd.DataFrame()

    for epoch in range(epochs):
        for step in range(0, int(len(X_train)/batch_size -1)):

            train_load = Variable(X_train[step * batch_size:(step+1) * batch_size, :]).view(-1, seq_dim, X_train.shape[1])
            y = Variable(y_train[step * batch_size:(step+1) * batch_size])

            optimizer.zero_grad()  # clears old gradients (w, r, t)

            y_pred = model(train_load)

            # Denormalize
            train_ENI = Variable(ENI_train[step * batch_size:(step + 1) * batch_size])
            train_pred = torch.zeros(size=(y_pred.shape))
            observ = torch.zeros(size=(y_pred.shape))

            for i in range(0, batch_size):
                train_pred[i] = y_pred[i, :] * train_ENI[i]
                observ[i] = y[i, :] * ENI_train[i]

            # compute loss: criterion RMSE
            RMSE = model.loss(train_pred, observ)

            train_loss.append(RMSE.data)
            """test_batch_rmse = list()
            test_batch_mae = list()
            test_batch_mbe = list()"""
            P_observ = torch.Tensor()
            P_pred = torch.Tensor()

            if iter % 10 == 9:
                 for step in range(0, int(len(X_test)/batch_size - 1)):

                    test_batch_rmse = list()
                    test_batch_mae = list()
                    test_batch_mbe = list()

                    test_load = Variable(X_test[step * batch_size:(step + 1) * batch_size, :]).view(-1, seq_dim, X_test.shape[1])
                    y = Variable(y_test[step * batch_size:(step + 1) * batch_size])

                    y_pred = model(test_load)

                    # Denormalize
                    test_ENI = Variable(ENI_test[step * batch_size:(step + 1) * batch_size])
                    test_pred = torch.zeros(size=(y_pred.shape))
                    observ = torch.zeros(size=(y_pred.shape))

                    for i in range(0, batch_size):
                        test_pred[i] = y_pred[i, :] * test_ENI[i]       # (P_pred)test_pred[:, 0] is Pdc_+5min
                        observ[i] = y[i, :] * ENI_test[i]

                    P_observ = torch.cat((P_observ, observ), 0)
                    P_pred = torch.cat((P_pred, test_pred), 0)

                    # compute Metrics
                    error = observ.data.numpy() - test_pred.data.numpy().squeeze()
                    """mae = np.nanmean(np.nanmean(np.abs(error), axis=0))
                    mbe = np.nanmean(np.nanmean(error, axis=0))
                    rmse = np.nanmean(np.sqrt(np.nanmean(error ** 2, axis=0)))"""

                    test_batch_rmse = np.sqrt(np.mean(error ** 2, axis=0))
                    test_batch_mae = np.nanmean(np.abs(error), axis=0)
                    test_batch_mbe = np.nanmean(error, axis=0)
                    test_rmse.append(np.mean(test_batch_rmse))
                    test_mae.append(np.mean(test_batch_mae))
                    test_mbe.append(np.mean(test_batch_mbe))

                    print('Epoch: {}, Iteration: {}, Train_RMSE: {}, Test_RMSE: {}, MAE: {}, MBE: {}'
                          .format(epoch, iter, RMSE.data, np.mean(test_rmse), np.mean(test_mae),
                                  np.mean(test_mbe)))

            RMSE.backward()  # computes derivative of loss
            optimizer.step()  # next step based on gradient
            iter += 1

    # save results of one epoch and Model
    results.insert(results.shape[1], "P_{}_observ".format(epochs), value=P_observ)
    results.insert(results.shape[1], "P_{}_pred".format(epochs), value=P_pred.detach())

    metric.insert(metric.shape[1], "MAE_{}".format(epochs), value=test_mae)
    metric.insert(metric.shape[1], "MBE_{}".format(epochs), value=test_mbe)
    metric.insert(metric.shape[1], "RMSE_{}".format(epochs), value=test_rmse)

    results.to_csv("LSTM_results/resultsLSTM_Epoch_{}.csv".format(epochs))
    metric.to_csv("LSTM_results/metricLSTM_Epoch_{}.csv".format(epochs))
    torch.save(model, PATH_save)

    print('loss: ', RMSE.item())

    return metric, results

# define which Model to load or name Model to be initialized
Model = 1

PATH_load = 'LSTM_Models/LSTM_{}'.format(Model)
PATH_save = 'LSTM_Models/LSTM_{}'.format(Model)

# True = load existing Model
# False = initialize new Model !insert number to not overwrite existing Model!
load_model = True

if load_model == False:
    # initialise Model and train IT
    model = initializeNewModel(input_dim=X_train.shape[1], hidden_dim=100, layer_dim=1, output_dim=10)
    test_loss, results = trainModel(model)
else:
    # load Model and train it
    model = torch.load(PATH_load)
    print("Model loaded")
    test_loss, results = trainModel(model)
    print("finished training")


