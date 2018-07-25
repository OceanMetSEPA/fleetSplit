# -*- coding: utf-8 -*-
"""
Created on Fri Apr  6 14:49:52 2018

@author: edward.barratt
"""

import os
import argparse
import numpy as np
import pandas as pd
from fuzzywuzzy import process
#from datetime import datetime

#import EFT_Tools as tools
WeightClasses = {}


def writeChanges(changes, saveloc):

  print("Saving changes to '{}'.".format(saveloc))
  changes.to_csv(saveloc, index=False)
  #with open(saveloc, 'w') as f:
  #  f.write('Created Using, fleetSplitFromANPR, -\n')
  #  f.write('Created On, {}, -\n'.format(datetime.now()))
  #  f.write('Vehicle Class, Cell, Proportion\n')
  #  for vehClass, PropsAll in changes.items():
  #    for cell, Propsin in PropsAll.items():
  #      WStr = '{}, {}, {}\n'.format(vehClass, cell, Propsin)
  #      #print(WStr)
  #      f.write(WStr)

def mergeVDicts(D):
  # Merge by adding
  D_ = {}
  TotVehs = 0
  TotVehsAll = 0
  for Di in D:
    for key, value in Di.items():
      if key not in [-9, 'Unknown']:
        TotVehs += value['num']
      TotVehsAll += value['num']
      try :
        D_[key]['num'] += value['num']
      except KeyError:
        D_[key] = {'num': value['num']}
  for key, value in D_.items():
    if key not in [-9, 'Unknown']:
      vvv = D_[key]['num']/TotVehs
      D_[key]['normFract'] = vvv
    else:
      vvv = D_[key]['num']/TotVehsAll
      D_[key]['fraction'] = vvv
  return D_

def getchangesLGV(LGVD, veh, withCells=False):
  changes = pd.DataFrame(columns=['Vehicle Name', 'ProportionType', 'Value', 'Complication', 'Cell', 'Proportion'])
  # LGV fuel control was added in EFT v8.0. Just hardcode the cells in here for now.
  Cols = ['E', 'F', 'G']
  Rows= {'PETROL': 542, 'HEAVY OIL': 543, 'ELECTRICITY': 544}


  if withCells:
    for ColI, Col in enumerate(Cols):
      for Fuel, D in LGVD.items():
        if Fuel in Rows.keys():
          C = '{}{}'.format(Col, Rows[Fuel])
          change = pd.DataFrame([[veh, 'Fuel', Fuel, ColI+1, C, D['fraction']]],
                                 columns=['Vehicle Name', 'ProportionType', 'Value',
                                          'Complication', 'Cell', 'Proportion'])
          changes = changes.append(change)
    changes = changes.append(pd.DataFrame([[veh, 'Fuel', 'Other', 0, '---', LGVD['Other']['fraction']]],
                                 columns=['Vehicle Name', 'ProportionType', 'Value',
                                          'Complication', 'Cell', 'Proportion']))
    changes = changes.append(pd.DataFrame([[veh, 'Fuel', 'Unknown', 0, '---', LGVD['Unknown']['fraction']]],
                               columns=['Vehicle Name', 'ProportionType', 'Value',
                                        'Complication', 'Cell', 'Proportion']))
  else:
    for Fuel, D in LGVD.items():
      change = pd.DataFrame([[veh, 'Fuel', Fuel, 0, '---', D['fraction']]],
                             columns=['Vehicle Name', 'ProportionType', 'Value',
                                      'Complication', 'Cell', 'Proportion'])
      changes = changes.append(change)

  return changes

def getchanges(ED, WD, eftE_veh, eftW_veh, verbose=False, vehName=''):
  changes = pd.DataFrame(columns=['Vehicle Name', 'ProportionType', 'Value', 'Complication', 'Cell', 'Proportion'])
  if verbose:
    print('')
    if vehName:
      print(vehName)
      print('-'*len(vehName))

  if isinstance(ED, list):
    # Add all the numbers together.
    ED = mergeVDicts(ED)
    if verbose:
      for euro, EDD in ED.items():
        if euro == -9:
          print('Unknown Euro               : {:6d} vehs, {:9.6f}%'.format(
            EDD['num'], 100.*EDD['fraction']))
        else:
          print('Euro   {:20.0f}: {:6d} vehs, {:9.6f}%'.format(
            euro, EDD['num'], 100.*EDD['normFract']))

  if isinstance(WD, list):
    # Add all the numbers together.
    WD = mergeVDicts(WD)
    if verbose:
      for weight, WDD in WD.items():
        if weight == 'Unknown':
          print('Unknown Weight             : {:6d} vehs, {:9.6f}%.'.format(
              WDD['num'], 100.*WDD['fraction']))
        else:
          print('Weight {:>20s}: {:6d} vehs, {:9.6f}%.'.format(
              weight, WDD['num'], 100.*WDD['normFract']))

  # Add unknown euro proportions.
  if -9 in ED.keys():
    vvvv = round(ED[-9]['fraction'], 8)
  else:
    vvvv = 0.0
  for polI, polType in enumerate(EFTPolTypes):
    change = pd.DataFrame([[vehName, 'Euro Class - {}'.format(polType), -9, 0, '---', vvvv]],
                          columns=['Vehicle Name', 'ProportionType', 'Value', 'Complication', 'Cell', 'Proportion'])
    changes = changes.append(change)
  # And unknown weight.
  if 'Unknown' in WD.keys():
    vvvv = round(WD['Unknown']['fraction'], 8)
  else:
    vvvv = 0.0
  change = pd.DataFrame([[vehName, 'Weight Class', 'Unknown', 0, '---', vvvv]],
                          columns=['Vehicle Name', 'ProportionType', 'Value', 'Complication', 'Cell', 'Proportion'])
  changes = changes.append(change)

  propTot = np.zeros_like(EFTPolTypes)
  lastLocation = np.zeros_like(EFTPolTypes)
  for Euro in range(7):
    if Euro in ED.keys():
      V = ED[Euro]
    else:
      V = {'normFract': 0.0}

    eft_veh_euro = eftE_veh[eftE_veh['euroclass']==Euro]
    for polI, polType in enumerate(EFTPolTypes):
      # Get the correct values and cells for the given pollutant type'
      eft_veh_euro_p = eft_veh_euro[eft_veh_euro['poltype']==polType]
      eft_props = np.array(eft_veh_euro_p['proportion'])
      eft_cells = list(eft_veh_euro_p['userCell'])
      if len(eft_cells) == 1:
        # Just one value to fill.
        vvvv = round(V['normFract'], 8)
        change = pd.DataFrame([[vehName, 'Euro Class - {}'.format(polType), Euro, 0, eft_cells[0], vvvv]],
                              columns=['Vehicle Name', 'ProportionType', 'Value', 'Complication', 'Cell', 'Proportion'])
        changes = changes.append(change)
        #changes[eft_cells[0]] = vvvv
        propTot[polI] += vvvv
        lastLocation[polI] = changes.tail(1).index.item()
      else:
        # A few cells to fill, so split the proportion we have between these
        # cells, weighted by the default split.
        if sum(eft_props) == 0:
          # All zeros, split evenly.
          eft_props_norm = np.ones_like(eft_props) / len(eft_props)
        else:
          eft_props_norm = eft_props / sum(eft_props)
        for ei, ec in enumerate(eft_cells):
          vvvv = round(eft_props_norm[ei] * V['normFract'], 8)
          change = pd.DataFrame([[vehName, 'Euro Class - {}'.format(polType), Euro, ei+1, ec, vvvv]],
                                 columns=['Vehicle Name', 'ProportionType', 'Value', 'Complication', 'Cell', 'Proportion'])
          changes = changes.append(change)
          propTot[polI] += vvvv
          lastLocation[polI] = changes.tail(1).index.item()
  # Adjust the values to ensure they sum to 1.
  for pi, pt in enumerate(propTot):
    if pt == 0.0:
      # No 'known' weights.
      continue
    diff = 1.0 - pt

    if abs(diff) > 1e-15:
      if abs(diff) > 1e-7:
        print(pt)
        raise ValueError("Doesn't sum to 1!")
      print('Adjusting Euro Nums')
      changes.loc[lastLocation[pi], 'Proportion'] = round(changes.loc[lastLocation[pi], 'Proportion'] + diff, 8)


  # Weight
  EFTWeights = eftW_veh['weightclass'].unique()
  Weights = list(WD.keys())
  WeightsGot = dict.fromkeys(Weights, False)
  propTot = 0.0
  lastLocation = 0
  for EFTWeight in EFTWeights:
    # Get the default values from the EFT.
    eft_veh_weight = eftW_veh[eftW_veh['weightclass'] == EFTWeight]
    eft_props = np.array(eft_veh_weight['proportion'])
    eft_cells = list(eft_veh_weight['userCell'])

    # Assume 0 initially.
    #for eft_cell in eft_cells:
    #changes[eft_cells[0]] = 0.0
    # Now add the values from the ANPR.
    if EFTWeight in Weights:
      V = WD[EFTWeight]
      # Just one value to fill for all weight classes.
      vvvv = round(V['normFract'], 8)
      change = pd.DataFrame([[vehName, 'Weight Class', EFTWeight, 0, eft_cells[0], vvvv]],
                             columns=['Vehicle Name', 'ProportionType', 'Value', 'Complication', 'Cell', 'Proportion'])
      changes = changes.append(change)
      lastLocation = changes.tail(1).index.item()
      propTot += vvvv
      WeightsGot[EFTWeight] = True

  for W, B in WeightsGot.items():
    if (not B) and (W != 'Unknown'):
      raise ValueError("No value assigned for weight '{}'.".format(W))

  diff = 1.0 - propTot
  if (diff != 1.0) and (abs(diff) > 1e-15):
    if abs(diff) > 1e-7:
      print(propTot)
      raise ValueError("Doesn't sum to 1!")
    print('Adjusting Weight Nums')
    changes.loc[lastLocation, 'Proportion'] = round(changes.loc[lastLocation, 'Proportion'] + diff, 8)
    #changes[lastCellName] = round(changes[lastCellName] + diff, 8)
    #print(changes[lastCellName])
  #print(changes)
  return changes


def getFromEFT(year, area, euroProportionsFile='default', weightProportionsFile='default'):
  """
  Returns the default proportions from the EFT. The

  """

  defaultDir = 'input'
  defaultDir = os.path.abspath(defaultDir)
  defaultEPF = os.path.join(defaultDir, 'AllCombined_AllEuroProportions.csv')
  defaultWPF = os.path.join(defaultDir, 'AllCombined_WeightProportions.csv')
  if euroProportionsFile == 'default':
    euroProportionsFile = defaultEPF
  if weightProportionsFile == 'default':
    weightProportionsFile = defaultWPF

  EData = pd.read_csv(euroProportionsFile)
  EData = EData[EData.area == area]
  EData = EData[EData.year == year]

  WData = pd.read_csv(weightProportionsFile)
  WData = WData[WData.area == area]
  WData = WData[WData.year == year]

  return EData, WData

def getFuelBreakdown(data, colF, verbose=False, vehName='', allowedFuels=['HEAVY OIL', 'PETROL', 'ELECTRICITY']):

  if verbose:
    print('')
    if vehName:
      print(vehName)
      print('-'*len(vehName))

  #removeFuels = [x for x in data[colF].unique() if x not in allowedFuels]
  #for rf in removeFuels:
  #  data = data[data[colF] != rf]
  data = data.copy()
  data[colF].fillna('Unknown', inplace=True)
  numTot = len(data.index)
  numAllow = 0
  for aF in allowedFuels:
    numAllow += len(data[data[colF] == aF].index)

  numUnknown = len(data[data[colF] == 'Unknown'].index)
  numOther = len(data.index) - (numAllow + numUnknown)
  D = {}
  UKF = round(numUnknown/numTot, 8)
  D['Unknown'] = {'num': numUnknown, 'fraction': UKF}
  OF = round(numOther/numTot, 8)
  D['Other'] = {'num': numOther, 'fraction': OF}
  if verbose:
    print('Unknown Fuel               : {:6d} vehs, {:9.6f}%'.format(numUnknown, 100.*UKF))
    print('Other Fuel                 : {:6d} vehs, {:9.6f}%'.format(numOther, 100.*OF))

  dataFuels = data.groupby([colF])
  propTot = 0.0
  for Fuel, group in dataFuels:
    if Fuel in allowedFuels:
      Fuel_ = Fuel
      numvehs = len(group.index)
      fraction = round(numvehs/numAllow, 8)
      propTot += fraction
      D[Fuel] = {'num': numvehs, 'fraction': fraction}
      if verbose:
        print('Fuel   {:>20s}: {:6d} vehs, {:9.6f}%'.format(Fuel, D[Fuel]['num'], 100.*D[Fuel]['fraction']))

  diff = 1.0 - propTot
  if abs(diff) > 1e-15:
    if abs(diff) > 1e-7:
      print(propTot)
      raise ValueError("Doesn't sum to 1!")
    print('Adjusting Fuel Nums')
    print(D)
    D[Fuel_]['fraction'] = round(D[Fuel_]['fraction'] + diff, 8)

  for aF in allowedFuels:
    if aF not in D.keys():
      D[aF] = {'num': 0, 'fraction': 0}

  return D

def getBreakdown(data, colE, colW, verbose=False, vehName=''):
  """
  Returns the vehicle fleet breakdown for euro class and weight class from the
  data frame.
  """
  if verbose:
    print('')
    if vehName:
      print(vehName)
      print('-'*len(vehName))


  numTot = len(data.index)

  # Catch nans
  data = data.copy()
  data[colE].fillna(-9, inplace=True)
  #print(data.head())
  # Groupby Euro class.
  eurogroups = data.groupby([colE])
  euroDict = {}
  fractions = np.array([])
  for euro, group in eurogroups:
    numvehs = len(group.index)
    fraction = numvehs/numTot
    euroDict[euro] = {'num': numvehs, 'fraction': fraction}
    if euro != -9:
      fractions = np.append(fractions, [fraction])
    else:
      if verbose:
        print('Unknown Euro               : {:6d} vehs, {:9.6f}%'.format(numvehs, 100.*fraction))
  fractionsS = sum(fractions)
  for ei, euro in enumerate(euroDict.keys()):
    if euro == -9:
      continue
    ED = euroDict[euro]
    normFrac = np.round(ED['fraction']/fractionsS, 8)
    ED['normFract'] = normFrac
    if verbose:
      print('Euro   {:20.0f}: {:6d} vehs, {:9.6f}%, normalized to {:9.6f}%'.format(
            euro, ED['num'], 100.*ED['fraction'], 100.*ED['normFract']))

  # Groupby weight class.
  weightgroups = data.groupby([colW])
  weightDict = {}
  fractions = np.array([])
  for weight, group in weightgroups:
    numvehs = len(group.index)
    fraction = numvehs/numTot
    weightDict[weight] = {'num': numvehs, 'fraction': fraction}
    if weight != 'Unknown':
      fractions = np.append(fractions, [fraction])
    else:
      if verbose:
        print('Unknown Weight             : {:6d} vehs, {:9.6f}%.'.format(numvehs, 100.*fraction))
  fractionsS = sum(fractions)
  for weight in weightDict.keys():
    if weight == 'Unknown':
      continue
    WD = weightDict[weight]
    WD['normFract'] = WD['fraction']/fractionsS
    if verbose:
      print('Weight {:>20s}: {:6d} vehs, {:9.6f}%, normalized to {:9.6f}%.'.format(
          weight, WD['num'], 100.*WD['fraction'], 100.*WD['normFract']))
  return euroDict, weightDict

def assignEuro(euro, year, notAll):
  if notAll:
    if euro in [1,2,3,4,5,6]:
      return euro
    else:
      return euroFromYear(year)
  else:
    return euroFromYear(year)

def euroFromYear(year):
  try:
    if year >= 2014:
      return 6
    elif year >= 2008:
      return 5
    elif year >= 2005:
      return 4
    elif year >= 2000:
      return 3
    elif year >= 1996:
      return 2
    elif year >= 1992:
      return 1
    else:
      return 0
  except TypeError as E:
    print(year)
    print(type(year))
    raise E


def processThroughAll(data, changes, Site, keepTaxi=False):

  totRows = len(data.index)

  # Catch unknown vehicles.
  data_unknown = data[data[colV] == 'Unknown']
  num_veh = len(data_unknown.index)
  changes = changes.append(pd.DataFrame([['Unknown', 'Vehicle Type', 'Unknown', 0, '---', round(num_veh/totRows, 8)]],
                        columns=['Vehicle Name', 'ProportionType', 'Value', 'Complication', 'Cell', 'Proportion']))

  data_unknown = data[data[colV] == 'Other HGV']
  num_veh = len(data_unknown.index)
  changes = changes.append(pd.DataFrame([['Other HGV', 'Vehicle Type', 'Unknown', 0, '---', round(num_veh/totRows, 8)]],
                        columns=['Vehicle Name', 'ProportionType', 'Value', 'Complication', 'Cell', 'Proportion']))


  # Taxi
  if keepTaxi:
    vehName = 'Taxi'
    data_veh = data[data[colV] == '3. TAXI']
    num_veh = len(data_veh.index)
    changes = changes.append(pd.DataFrame([[vehName, 'Vehicle Type', vehName, 0, '---', round(num_veh/totRows, 8)]],
                            columns=['Vehicle Name', 'ProportionType', 'Value', 'Complication', 'Cell', 'Proportion']))#print(data_veh)
    ED, WD = getBreakdown(data_veh, colE, colW, verbose=True, vehName=vehName)
    for euro, vs in ED.items():
      changes = changes.append(pd.DataFrame([['Taxi', 'Euro Class - NOx', euro, 0, '-+-', round(vs['fraction'], 8)]],
                                            columns=['Vehicle Name', 'ProportionType', 'Value', 'Complication', 'Cell', 'Proportion']))
      changes = changes.append(pd.DataFrame([['Taxi', 'Euro Class - PM10', euro, 0, '-+-', round(vs['fraction'], 8)]],
                                            columns=['Vehicle Name', 'ProportionType', 'Value', 'Complication', 'Cell', 'Proportion']))
    for weight, vs in WD.items():
      changes = changes.append(pd.DataFrame([['Taxi', 'Weight Class', weight, 0, '-+-', round(vs['fraction'], 8)]],
                                            columns=['Vehicle Name', 'ProportionType', 'Value', 'Complication', 'Cell', 'Proportion']))

  else:
    print('Taxis assigned to cars.')
    data.loc[data[colV] == '3. TAXI', colV] = '2. CAR'


  # Cars
  data_cars = data[data[colV] == '2. CAR']
  num_veh = len(data_cars.index)
  changes = changes.append(pd.DataFrame([['Car', 'Vehicle Type', 'Car', 0, '---', round(num_veh/totRows, 8)]],
                        columns=['Vehicle Name', 'ProportionType', 'Value', 'Complication', 'Cell', 'Proportion']))
  # Get the proportion of Cars by fuel type.
  vehName = 'Car Fuel Type'
  LGVD = getFuelBreakdown(data_cars, colF, verbose=True, vehName=vehName)
  changes = changes.append(getchangesLGV(LGVD, 'Car'))

  # Diesel Cars
  vehName = 'Diesel Car'
  data_veh = data_cars[data_cars[colF] == 'HEAVY OIL']
  num_veh = len(data_veh.index)

  changes = changes.append(pd.DataFrame([[vehName, 'Vehicle Type', vehName, 0, '---', round(num_veh/totRows, 8)]],
                        columns=['Vehicle Name', 'ProportionType', 'Value', 'Complication', 'Cell', 'Proportion']))
  eftE_veh = EFTEuroDefault[EFTEuroDefault['vehicle'] == vehName]
  eftW_veh = EFTWeightDefault[EFTWeightDefault['vehicle'] == vehName]
  ED, WD = getBreakdown(data_veh, colE, colW, verbose=True, vehName=vehName)
  changes = changes.append(getchanges(ED, WD, eftE_veh, eftW_veh, vehName=vehName))

  # Petrol Cars
  vehName = 'Petrol Car'
  vehNameW = 'Petrol car'
  data_veh = data_cars[data_cars[colF] == 'PETROL']
  num_veh = len(data_veh.index)
  changes = changes.append(pd.DataFrame([[vehName, 'Vehicle Type', vehName, 0, '---', round(num_veh/totRows, 8)]],
                        columns=['Vehicle Name', 'ProportionType', 'Value', 'Complication', 'Cell', 'Proportion']))
  eftE_veh = EFTEuroDefault[EFTEuroDefault['vehicle'] == vehName]
  eftW_veh = EFTWeightDefault[EFTWeightDefault['vehicle'] == vehNameW]
  ED, WD = getBreakdown(data_veh, colE, colW, verbose=True, vehName=vehName)
  changes = changes.append(getchanges(ED, WD, eftE_veh, eftW_veh, vehName=vehName))


  # LGVs
  data_lgvs = data[data[colV] == '4. LGV']
  num_veh = len(data_lgvs.index)
  changes = changes.append(pd.DataFrame([['LGV', 'Vehicle Type', 'LGV', 0, '---', round(num_veh/totRows, 8)]],
                        columns=['Vehicle Name', 'ProportionType', 'Value', 'Complication', 'Cell', 'Proportion']))
  # Get the proportion of LGVs by fuel type.
  vehName = 'LGV Fuel Type'
  LGVD = getFuelBreakdown(data_lgvs, colF, verbose=True, vehName=vehName)
  changes = changes.append(getchangesLGV(LGVD, 'LGV', withCells=True))

  # Diesel LGVs
  vehName='Diesel LGV'
  data_veh = data_lgvs[data_lgvs[colF] == 'HEAVY OIL']
  num_veh = len(data_veh.index)
  changes = changes.append(pd.DataFrame([[vehName, 'Vehicle Type', vehName, 0, '---', round(num_veh/totRows, 8)]],
                        columns=['Vehicle Name', 'ProportionType', 'Value', 'Complication', 'Cell', 'Proportion']))
  eftE_veh = EFTEuroDefault[EFTEuroDefault['vehicle'] == vehName]
  eftW_veh = EFTWeightDefault[EFTWeightDefault['vehicle'] == vehName]
  ED, WD = getBreakdown(data_veh, colE, colW, verbose=True, vehName=vehName)
  changes = changes.append(getchanges(ED, WD, eftE_veh, eftW_veh, vehName=vehName))

  # Petrol LGVs
  vehName='Petrol LGV'
  data_veh = data_lgvs[data_lgvs[colF] == 'PETROL']
  num_veh = len(data_veh.index)
  if num_veh > 0:
    changes = changes.append(pd.DataFrame([[vehName, 'Vehicle Type', vehName, 0, '---', round(num_veh/totRows, 8)]],
                          columns=['Vehicle Name', 'ProportionType', 'Value', 'Complication', 'Cell', 'Proportion']))
    eftE_veh = EFTEuroDefault[EFTEuroDefault['vehicle'] == vehName]
    eftW_veh = EFTWeightDefault[EFTWeightDefault['vehicle'] == vehName]
    ED, WD = getBreakdown(data_veh, colE, colW, verbose=True, vehName=vehName)
    changes = changes.append(getchanges(ED, WD, eftE_veh, eftW_veh, vehName=vehName))

  # Bus Vs Coach
  busName = '5b. BUS'
  data_bus = data[data[colV] == busName]
  nb = len(data_bus.index)
  if nb == 0:
    busName = '5. BUS'
    data_bus = data[data[colV] == busName]
    nb = len(data_bus.index)
  data_coach = data[data[colV] == '5c. COACH']
  nc = len(data_coach.index)
  bus_r = round(nb/(nb+nc), 8)
  coach_r = 1.0 - bus_r
  changes = changes.append(pd.DataFrame([['BusCoach', 'Bus Or Coach', 'Bus', 0, 'D429', bus_r]],
                        columns=['Vehicle Name', 'ProportionType', 'Value', 'Complication', 'Cell', 'Proportion']))
  changes = changes.append(pd.DataFrame([['BusCoach', 'Bus Or Coach', 'Bus', 0, 'E429', bus_r]],
                        columns=['Vehicle Name', 'ProportionType', 'Value', 'Complication', 'Cell', 'Proportion']))
  changes = changes.append(pd.DataFrame([['BusCoach', 'Bus Or Coach', 'Coach', 0, 'D430', coach_r]],
                        columns=['Vehicle Name', 'ProportionType', 'Value', 'Complication', 'Cell', 'Proportion']))
  changes = changes.append(pd.DataFrame([['BusCoach', 'Bus Or Coach', 'Coach', 0, 'E430', coach_r]],
                        columns=['Vehicle Name', 'ProportionType', 'Value', 'Complication', 'Cell', 'Proportion']))

  # Buses
  vehName='Bus'
  vehName2 = 'Buses'
  data_veh = data[data[colV] == busName]
  num_veh = len(data_veh.index)
  changes = changes.append(pd.DataFrame([[vehName, 'Vehicle Type', vehName, 0, '---', round(num_veh/totRows, 8)]],
                        columns=['Vehicle Name', 'ProportionType', 'Value', 'Complication', 'Cell', 'Proportion']))#print(data_veh)
  eftE_veh = EFTEuroDefault[EFTEuroDefault['vehicle'] == vehName2]
  eftW_veh = EFTWeightDefault[EFTWeightDefault['vehicle'] == vehName2]
  ED, WD = getBreakdown(data_veh, colE, colW, verbose=True, vehName=vehName)
  changes = changes.append(getchanges(ED, WD, eftE_veh, eftW_veh, vehName=vehName))

  # Coaches
  vehName='Coach'
  vehName2 = 'Coaches'
  data_veh = data[data[colV] == '5c. COACH']
  num_veh = len(data_veh.index)
  if num_veh > 0:
    changes = changes.append(pd.DataFrame([[vehName, 'Vehicle Type', vehName, 0, '---', round(num_veh/totRows, 8)]],
                          columns=['Vehicle Name', 'ProportionType', 'Value', 'Complication', 'Cell', 'Proportion']))#print(data_veh)
    eftE_veh = EFTEuroDefault[EFTEuroDefault['vehicle'] == vehName2]
    eftW_veh = EFTWeightDefault[EFTWeightDefault['vehicle'] == vehName2]
    ED, WD = getBreakdown(data_veh, colE, colW, verbose=True, vehName=vehName)
    changes = changes.append(getchanges(ED, WD, eftE_veh, eftW_veh, vehName=vehName))

  # RHGV 2X
  vehName='Rigid HGV 2 Axle'
  data_veh = data[data[colV] == '6a. RHGV_2X']
  num_veh = len(data_veh.index)
  changes = changes.append(pd.DataFrame([[vehName, 'Vehicle Type', vehName, 0, '---', round(num_veh/totRows, 8)]],
                        columns=['Vehicle Name', 'ProportionType', 'Value', 'Complication', 'Cell', 'Proportion']))#print(data_veh)
  ED2, WD2 = getBreakdown(data_veh, colE, colW, verbose=True, vehName=vehName)

  # RHGV 3X
  vehName='Rigid HGV 3 Axle'
  data_veh = data[data[colV] == '6b. RHGV_3X']
  num_veh = len(data_veh.index)
  changes = changes.append(pd.DataFrame([[vehName, 'Vehicle Type', vehName, 0, '---', round(num_veh/totRows, 8)]],
                        columns=['Vehicle Name', 'ProportionType', 'Value', 'Complication', 'Cell', 'Proportion']))#print(data_veh)
  ED3, WD3 = getBreakdown(data_veh, colE, colW, verbose=True, vehName=vehName)

  # RHGV 4X
  vehName='Rigid HGV 4 Axle'
  data_veh = data[data[colV] == '6c. RHGV_4X']
  num_veh = len(data_veh.index)
  changes = changes.append(pd.DataFrame([[vehName, 'Vehicle Type', vehName, 0, '---', round(num_veh/totRows, 8)]],
                        columns=['Vehicle Name', 'ProportionType', 'Value', 'Complication', 'Cell', 'Proportion']))#print(data_veh)
  ED4, WD4 = getBreakdown(data_veh, colE, colW, verbose=True, vehName=vehName)

  # Get changes for Rigid HGVs
  vehName2 = 'Rigid HGV'
  eftE_veh = EFTEuroDefault[EFTEuroDefault['vehicle'] == vehName2]
  eftW_veh = EFTWeightDefault[EFTWeightDefault['vehicle'] == vehName2]
  changes = changes.append(getchanges([ED2, ED3, ED4], [WD2, WD3, WD4], eftE_veh, eftW_veh,
                                verbose=True, vehName=vehName2))

  # AHGV 34X
  vehName='Artic HGV 3&4 Axle'
  data_veh = data[data[colV] == '7a. AHGV_34X']
  num_veh = len(data_veh.index)
  numAHGV = num_veh
  changes = changes.append(pd.DataFrame([[vehName, 'Vehicle Type', vehName, 0, '---', round(num_veh/totRows, 8)]],
                        columns=['Vehicle Name', 'ProportionType', 'Value', 'Complication', 'Cell', 'Proportion']))#print(data_veh)
  ED3, WD3 = getBreakdown(data_veh, colE, colW, verbose=True, vehName=vehName)

  # AHGV 5X
  vehName='Artic HGV 5 Axle'
  data_veh = data[data[colV] == '7b. AHGV_5X']
  num_veh = len(data_veh.index)
  numAHGV += num_veh
  changes = changes.append(pd.DataFrame([[vehName, 'Vehicle Type', vehName, 0, '---', round(num_veh/totRows, 8)]],
                        columns=['Vehicle Name', 'ProportionType', 'Value', 'Complication', 'Cell', 'Proportion']))#print(data_veh)
  ED5, WD5 = getBreakdown(data_veh, colE, colW, verbose=True, vehName=vehName)

  # AHGV 6X
  vehName='Artic HGV 6 Axle'
  data_veh = data[data[colV] == '7c. AHGV_6X']
  num_veh = len(data_veh.index)
  numAHGV += num_veh
  changes = changes.append(pd.DataFrame([[vehName, 'Vehicle Type', vehName, 0, '---', round(num_veh/totRows, 8)]],
                        columns=['Vehicle Name', 'ProportionType', 'Value', 'Complication', 'Cell', 'Proportion']))#print(data_veh)
  ED6, WD6 = getBreakdown(data_veh, colE, colW, verbose=True, vehName=vehName)

  # Get changes for Artic HGVs
  vehName2 = 'Artic HGV'
  if numAHGV > 0:
    eftE_veh = EFTEuroDefault[EFTEuroDefault['vehicle'] == vehName2]
    eftW_veh = EFTWeightDefault[EFTWeightDefault['vehicle'] == vehName2]
    changes = changes.append(getchanges([ED3, ED5, ED6], [WD3, WD5, WD6], eftE_veh, eftW_veh,
                                  verbose=True, vehName=vehName2))

  changes['Site'] = Site
  return changes



if __name__ == '__main__':
  ProgDesc = ("Creates a vehFleetSplit file of the type used by shp2EFT using "
              "the contents of an ANPR data file.")
  ANPRDesc = ("The ANPR file should be a csv file listing all vehicles "
              "passing the ANPR counter (including double counting of vehicles "
              "that have passed more than once). There should be a column each "
              "for vehicle class, euro class, weight class and fuel.")
  parser = argparse.ArgumentParser(description=ProgDesc)
  parser.add_argument('anprfile', type=str,
                      help="The ANPR file to be processed. "+ANPRDesc)
  parser.add_argument('--saveloc', metavar='save location',
                      type=str, nargs='?',
                      help="Path where the outpt csv file should be saved.")
  parser.add_argument('--vehColumnName', metavar='vehicle class column name',
                      type=str, nargs='?', default='Vehicle11Split',
                      help="The column name for the vehicle class.")
  parser.add_argument('--weightColumnName', metavar='weight class column name',
                      type=str, nargs='?', default='WeightClassEFT',
                      help="The column name for the vehicle weight class.")
  parser.add_argument('--euroColumnName', metavar='euro class column name',
                      type=str, nargs='?', default='Euro Class',
                      help="The column name for the vehicle euro class.")
  parser.add_argument('--fuelColumnName', metavar='fuel column name',
                      type=str, nargs='?', default='Fuel',
                      help="The column name for the vehicle fuel.")
  parser.add_argument('--yearColumnName', metavar='manufacture year column name',
                      type=str, nargs='?', default='Manufacture Year',
                      help=("The column name for the vehicle manufacture year. "
                            "Only used if flag --reassignEuro is used."))
  parser.add_argument('--splitLoc', action='store_true',
                      help=("If set, then different proportions will be found "
                            "for each monitoring site and direction. Default False."))
  parser.add_argument('--siteColumnName', metavar='anpr site column name',
                      type=str, nargs='?', default='Site Name',
                      help=("The column name for the ANPR monitoring site name. "
                            "Only used if flag --splitLoc is used."))
  parser.add_argument('--directionColumnName', metavar='direction column name',
                      type=str, nargs='?', default='Direction',
                      help=("The column name for the ANPR monitoring site direction. "
                            "Only used if flag --splitLoc is used."))
  parser.add_argument('--keepTaxi',
                      action='store_true',
                      help=("If set, will keep taxis as a seperate category, "
                            "otherwise taxis will be incorporated in to cars."))
  parser.add_argument('--reassignEuro', metavar='Reassign Euro',
                      type=int, nargs='?', default=2,
                      help=("If 0, euro values provided in the source ANPR file "
                            "will be ignored and will instead be based on the "
                            "manufacture date. If 1, then vehicles with either "
                            "no specified euro class, or an assigned euroclass "
                            "of 0, will be reassigned based on manufacture date. "
                            "If 2, then the euro class will not be adjusted. "
                            "The manufacture date is an imperfect proxy "
                            "for euro class, but can be better than no estimate "
                            "if the euro class is missing from many records. Default 2."))

  args = parser.parse_args()
  anprfile = args.anprfile
  splitLoc = args.splitLoc
  colV = args.vehColumnName
  colW = args.weightColumnName
  colE = args.euroColumnName
  colF = args.fuelColumnName
  colY = args.yearColumnName
  colS = args.siteColumnName
  colD = args.directionColumnName
  keepTaxi = args.keepTaxi
  reassignEuro = args.reassignEuro
  saveloc = args.saveloc
  reqColNames = ['--vehColumnName', '--weightColumnName', '--euroColumnName', '--fuelColumnName']
  reqCols = [colV, colW, colE, colF]
  if reassignEuro != 2:
    reqColNames.append('--yearColumnName')
    reqCols.append(colY)
  if splitLoc:
    reqColNames.extend(['--siteColumnName', '--directionColumnName'])
    reqCols.extend([colS, colD])

  # Check that the anpr file exists.
  if not os.path.exists(anprfile):
    raise ValueError('File {} does not exist.'.format(anprfile))

  # Get the default proportions.
  EFTEuroDefault, EFTWeightDefault = getFromEFT(2018, 'Scotland')
  EFTPolTypes = EFTEuroDefault['poltype'].unique()

  # Read the file into pandas.
  data = pd.read_csv(anprfile, encoding="ISO-8859-1")

  print()
  print(list(data))
  print()

  # Check various things.
  colnames = list(data)
  for qi, q in enumerate(reqCols):
    if q not in colnames:
      bestOptions = process.extract(q, colnames, limit=5)
      posNames = '", "'.join([x[0] for x in bestOptions])
      raise ValueError(('Column {} does not exist in file, specify another '
                        'column using the {} flag. Perhaps one of the following is '
                        'appropriate: "{}".').format(q, reqColNames[qi], posNames))


  for col in colnames:
    if col not in reqCols:
      data = data.drop(col, 1)

  if reassignEuro != 2:
    data[colY] = pd.to_numeric(data[colY])
    data[colE] = data.apply(lambda row: assignEuro(row[colE], row[colY], reassignEuro), axis=1)

  print('Unique vehicle names:')
  print(', '.join(data[colV].unique()))
  print('Unique euro classes:')
  print(', '.join([str(x) for x in data[colE].unique()]))
  print('Unique weight classes:')
  print(', '.join(data[colW].unique()))

  # Start the changes dataframe.
  changes = pd.DataFrame(columns=['Vehicle Name', 'ProportionType', 'Value', 'Complication', 'Cell', 'Proportion', 'Site'])

  if splitLoc:
    changes_ = changes.copy()
    for a, b in data.groupby([colS, colD]):
      Site = '{}_{}'.format(*a).replace(' ', '')
      changesS = processThroughAll(b, changes, Site=Site)
      changes_ = changes_.append(changesS)
    changes = changes_
  else:
    changes = processThroughAll(data, changes, Site='All', keepTaxi=keepTaxi)


  print()
  if saveloc is None:
    saveloc = anprfile.replace('.csv', '_EFTProportionChanges.csv')
  writeChanges(changes, saveloc)