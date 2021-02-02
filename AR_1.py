import numpy as np
import matplotlib.pyplot as plt
import csv
import pandas as pa
import sklearn as sk
import statsmodels as stat
from sklearn import datasets, linear_model
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.impute import SimpleImputer
from pandas.plotting import autocorrelation_plot, lag_plot
from statsmodels.tsa.ar_model import AutoReg

def replace_NaN(var): 
# Input var has to be of the class list. Replace with minimum value 
    for i in range(0,len(var)):
      if var[i] == 'NaN':
        var.remove('NaN')
        var.insert(i,0.01)
    return var

def replace_NaN_n(var): 
# Input var has to be of the class list. Replace with minimum value 
    for i in range(0,len(var)):
      if var[i] == 'NaN\n':
        var.remove('NaN\n')
        var.insert(i,0.01)
    return var

def replace_NaN_NN(var):
    # Input var has to be of the class list.    
    for i in range(0,len(var)):
      if (var[0] == 'NaN') and (i < len(var)):
        var.remove('NaN')
        while var[i] == 'NaN':
              continue
        var.insert(i,var[i+1])
      elif (var[i] == 'NaN') and (i <= len(var)):
        var.remove('NaN')
        var.insert(i,var[i-1])
    return var

def replace_NaN_n_NN(var):
    # Input var has to be of the class list.    
    for i in range(0,len(var)):
      if (var[0] == 'NaN\n') and (i < len(var)):
        var.remove('NaN\n')
        while var[i] == 'NaN\n':
              continue
        var.insert(i,var[i+1])
      elif (var[i] == 'NaN\n') and (i <= len(var)):
        var.remove('NaN\n')
        var.insert(i,var[i-1])
    return var

data = open (r'Daten/PVAMM_201911-202011_PT5M_merged.csv', 'r')
d = data.readlines()

time = []
gti30t187a = []
GHI = []
Ta = []
BNI = []
Pdc = []
Pdcmean = []
summe = 0.0
Pdcall = []
Indata_nlist = []

for n in range(1,113185):
  linie = d[n]
  D = linie.split(",")
  time.append(D[0])
  gti30t187a.append(D[9])
  GHI.append(D[8])
  Ta.append(D[5])
  BNI.append(D[23])
  Pdc.append(D[32])
  for m in range (32,72):
        summe += float(D[m])
  Pdcmean = summe/m
  Pdcall.append(Pdcmean)


# datatype list

Pdc = replace_NaN(Pdc)
gti30t187a = replace_NaN(gti30t187a)
GHI = replace_NaN(GHI)
Ta = replace_NaN(Ta)

Pdc_float = np.array(Pdc, dtype=np.float16)
gti30t187a_float = np.array(gti30t187a, dtype=float)
GHI_float = np.array(GHI, dtype=float)
Ta_float = np.array(Ta, dtype=float)

print(type(Pdc_float.size))

# Scaling trainings data: Normalization

Pdc_norm = Pdc_float/max(Pdc_float)
gti30t187a_norm = gti30t187a_float/max(gti30t187a_float)    
GHI_norm = GHI_float/max(GHI_float)
Ta_norm = Ta_float/max(Ta_float)

# Input

for m in range(0,len(Pdc)):
    Indata_nlist.append([gti30t187a_norm[m], Pdc_norm[m]])

Indata_array = np.array(Indata_nlist, dtype=float)

# Trainingsdata Split

Indata_array_train, Indata_array_test = train_test_split(Indata_array)
Pdc_train, Pdc_test = Pdc_norm[1:len(Pdc)-24], Pdc[len(Pdc)-24:len(Pdc)]

# Autoregression fixed Model

model = AutoReg(Pdc_train, lags=1000)
model_fit = model.fit()
print('Coefficients: %s' % model_fit.params)

# pred = model_fit.predict(start=len(Pdc_train), end=len(Pdc_train)+len(Pdc_test)-1, dynamic=False)
# for i in range(len(pred)):
#     print('predicted=%f, expected=%f' % (pred[i], Pdc_test[i]))
# rmse = np.sqrt(mean_squared_error(Pdc_test, pred))
# print('Test RMSE: %.3f' % rmse)
# plt.plot(Pdc_test)
# plt.plot(pred, color='red')
# plt.show()

# Autoregression rolling Model

window = 1000
hist = Pdc_train[len(Pdc_train)-window:len(Pdc_train)]
hist = [hist[i] for i in range(len(hist))]
pred = list()
for t in range(len(Pdc_test)):
      length = len(hist)
      lag = [hist[i] for i in range(length-window, length)]
      Pdc_pred = model_fit.params[0]
      for d in range(window):
            Pdc_pred += model_fit.params[d+1] * lag[window-d-1]
      obs = Pdc_test[t]
      pred.append(Pdc_pred)
      hist.append(obs)
      print('predicted=%f, expected=%f' % (Pdc_pred, obs))
rmse = np.sqrt(mean_squared_error(Pdc_test, pred))
print('Test RMSE: %.3f' % rmse)
plt.plot(Pdc_test)
plt.plot(pred, color='red')
plt.show()


