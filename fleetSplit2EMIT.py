# -*- coding: utf-8 -*-
"""
Created on Tue Jun 19 16:05:38 2018

@author: edward.barratt


"""

import os
import pandas as pd
import numpy as np
import argparse

vehcatDefault = os.path.normpath(('C:/Users/edward.barratt/Documents/Development/'
                                 'Python/extractfromeft/input/EMIT/'
                                 'VehCats.csv'))


# 'C:/Users/edward.barratt/Documents/Development/Python/extractfromeft/input/EMIT/E8.0NOx_11_ScoU17-tx.csv'
# 'C:/Users/edward.barratt/Documents/Modelling/CAFS/ANPRStuff/DundeeProportion_EuroUFromYear_taxis.csv'


def processSplit(anprfile, basefile, vehcatfile=vehcatDefault):
  """
  Creates a table of vehicle proportions that can be copied and pasted in to
  EMIT for the purpose of adjusting the route type, with proportions taken from
  an Automatic Number Plate Recognition (ANPR) data set.

  INPUTS:
      anprfile - string
                 The path to the ANPR data file. The ANPR file should be a csv
                 file created using fleetSplitFromANPR.
      basefile - string
                 The path to a base file upon which to base proportions. This
                 file should be a csv file created by clicking 'copy' on the
                 appropriate route type in emit, pasting the table into a
                 spreadsheet, and saving as a csv. The contents will be used to
                 distribute vehicles across vehicle types with the same properties.
                 For example, Euro 5 Rigid HGVs of 14-20 tonne gross weight could
                 be represented by one of 6 different wehicle sub-categories
                 (depending on fuel type and technology). Say 5% of Rigid HGVs
                 in the ANPR data are of that classification, then 5% will be
                 divided between the 6 sub-categorys, based on the proportions
                 that are already assigned to those sub-categories.
      vehcatfile - string OPTIONAL
                 The path to a file describing each sub-category of vehicle class
                 a default is provided by default but it may need to be updated
                 for future emission factors.



  """

  # Read the vehicle category file.
  v_df = pd.read_csv(vehcatfile)
  v_df = v_df.set_index('Vehicle sub-category')

  # Read the file with the data from EMIT.
  o_df = pd.read_csv(basefile)
  o_df = o_df.set_index('Vehicle sub-category')

  # Join those two...
  o_df = v_df.join(o_df)

  # Read the anpr data file.
  p_df = pd.read_csv(anprfile)

  # Add the columns we need.
  vehCols = ['Motorcycles', 'Cars', 'Taxis', 'LGVs', 'Buses and coaches',
             'Rigid HGVs 2 axles', 'Rigid HGVs 3 axles', 'Rigid HGVs 4+ axles',
             'Artic HGVs 3&4 axles', 'Artic HGVs 5 axles', 'Artic HGVs 6+ axles']
  outCols = []
  #dispCols = ['Vehicle sub-category', 'Vehicle sub-category description']
  dispCols = ['Vehicle sub-category description']
  dispCols.extend(vehCols)
  outRenames = {}
  for col in vehCols:
    outC = 'out - {}'.format(col)
    outCols.append(outC)
    outRenames[outC] = col
    o_df[outC] = 0

  # Remove rows that don't have a cell assigned to them; rows that don't have
  # an appropriate cell in the EFT are also not relavent in EMIT route types.
  # The exception are taxi rows, and cell for those rows is marked as '-+-'
  # rather than '---' by fleetSplitFromANPR.py.
  p_df = p_df[p_df['Cell'] != '---']

  # Deal with each vehicle in isolation.
  for veh, veh_g in p_df.groupby('Vehicle Name'):
    if veh in ['BusCoach', 'LGV']:
      # Skip, because 'Bus', 'Coach', 'Petrol LGV', and 'Diesel LGV' already exist.
      continue

    v_euros = veh_g[veh_g['ProportionType'] == 'Euro Class - NOx'].copy()
    v_euros['Value'] = pd.to_numeric(v_euros['Value'])
    v_weight = veh_g[veh_g['ProportionType'] == 'Weight Class'].copy()
    #v_fuel = veh_g[veh_g['ProportionType'] == 'Fuel'].copy()

    o_veh = o_df[o_df['Vehicle'] == veh]

    if len(o_veh.index) == 0:
      print(o_df['Vehicle'].unique())
      print(p_df['Vehicle Name'].unique())
      raise ValueError('{}: No data left.'.format(veh))

    for euro, euro_g in v_euros.groupby('Value'):
      o_euro = o_veh[o_veh['Euro Class'] == euro]
      if len(o_euro.index) == 0:
        print(euro)
        print(o_veh.head())
        raise ValueError('Euro {}: No data left.'.format(euro))

      for weight, weight_g in v_weight.groupby('Value'):
        o_weight = o_euro[o_euro['Weight'] == weight]


        if veh == 'Taxi':
          o_weight = o_euro

        if len(o_weight.index) == 0:
          if veh != 'Taxi':
            print(weight)
            print(o_euro[['Vehicle sub-category description', 'Weight']])
            print(o_euro['Weight'].unique())
            raise ValueError('Weight {}: No data left.'.format(weight))

        EuroProportion = euro_g['Proportion'].sum()
        WeightProportion = weight_g['Proportion'].sum()
        anpr_props_tot = EuroProportion * WeightProportion

        print('{} - Euro {}: {:.2g}% - Weight {}: {:.2g}% -- {:.6f}%'.format(veh, euro, 100*EuroProportion, weight, 100*WeightProportion, anpr_props_tot))

        # See if any of the matching vehicles in the EMIT data set are populated.
        orig_props = o_weight[vehCols]
        orig_props_matrix = orig_props.as_matrix()
        orig_props_tot = np.sum(orig_props_matrix)
        if orig_props_tot < 1e-6:
          # No proportion assigned to this veh type in original.
          if anpr_props_tot < 1e-6:
            # And none in anpr, so that's fine.
            pass
          else:
            uVehs = o_weight['Vehicle cat'].unique()
            #print(uVehs)
            if len(uVehs) > 1:
              raise ValueError('Mmmm, problem.')
            else:
              if uVehs[0] == 'Rigid HGV':
                outCol_ = ['out - Rigid HGVs 2 axles',
                           'out - Rigid HGVs 3 axles',
                           'out - Rigid HGVs 4+ axles']
              else:
                outCol_ = ['out - ' + uVehs[0]]
            # No preexisting values to guide us. Divide equally between the rows,
            # all in the most appropriate column.
            o_df.loc[o_weight.index, outCol_] += anpr_props_tot/len(o_weight.index)
        else:
          #print(o_weight[dispCols])
          orig_props_norm = anpr_props_tot * orig_props_matrix/orig_props_tot
          o_df.loc[o_weight.index, outCols] += orig_props_norm

  results = o_df[outCols].copy()

  # Now normalize all columns.
  #results_sums = results.sum()
  for col in outCols:
    results[col] = results[col].apply(abs)
    s = results[col].sum()
    if abs(s) <  0.00001:
      # None assigned. Probably Motorcycles or Taxis.
      results[col] = o_df[col[6:]]
    results[col] = 100*results[col]/results[col].sum()


  results = results.rename(columns=outRenames)

def getArgs():
  """
  Organise command line arguments when run as __main__.
  """
  ProgDesc = ("Creates a route type csv file of the type whose contents can be "
              "copied and pasted in to EMIT to change the proportions of "
              "different vehicle categories with a particular route type.")
  ANPRDesc = ("The ANPR file should be a csv file listing all vehicles "
              "passing the ANPR counter (including double counting of vehicles "
              "that have passed more than once). There should be a column each "
              "for vehicle class, euro class, weight class and fuel.")
  parser = argparse.ArgumentParser(description=ProgDesc)
  parser.add_argument('anprfile', type=str,
                      help="The ANPR file to be processed. "+ANPRDesc)
  parser.add_argument('basefile', type=str,
                      help=("A file containing the base route type proportions. "
                            "This should be created by clicking 'copy' on the "
                            "route type window of EMIT, pasteing the results in "
                            "to a spreadsheet, and saving as a csv file."))
  parser.add_argument('--saveloc', metavar='save location',
                      type=str, nargs='?', default='Auto',
                      help="Path where the outpt csv file should be saved.")


  args = parser.parse_args()
  return args

if __name__ == '__main__':

  args = getArgs()
  anprfile = args.anprfile
  basefile = args.basefile
  saveloc = args.saveloc
  if args.saveloc == 'Auto':
    p, x = os.path.splitext(anprfile)
    saveloc = p + '_4EMIT.csv'

  results = processSplit(anprfile, basefile)
  results.to_csv(saveloc)
  print('Results saved to {}.'.format(saveloc))