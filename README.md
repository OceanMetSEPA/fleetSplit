Functions for creating fleet split breakdown files used by EMIT and other tools.

## fleetSplitFromANPR.py ##
Creates a vehFleetSplit file of the type used by shp2EFT using the contents of
an ANPR data file.

### Usage: fleetSplitFromANPR.py ###
```text
usage: fleetSplitFromANPR.py [-h] [--saveloc [save location]]
                             [--vehColumnName [vehicle class column name]]
                             [--weightColumnName [weight class column name]]
                             [--euroColumnName [euro class column name]]
                             [--fuelColumnName [fuel column name]]
                             [--yearColumnName [manufacture year column name]]
                             [--splitLoc]
                             [--siteColumnName [anpr site column name]]
                             [--directionColumnName [direction column name]]
                             [--keepTaxi] [--reassignEuro [Reassign Euro]]
                             anprfile

Creates a vehFleetSplit file of the type used by shp2EFT using the contents of
an ANPR data file.

positional arguments:
  anprfile              The ANPR file to be processed. The ANPR file should be
                        a csv file listing all vehicles passing the ANPR
                        counter (including double counting of vehicles that
                        have passed more than once). There should be a column
                        each for vehicle class, euro class, weight class and
                        fuel.

optional arguments:
  -h, --help            show this help message and exit
  --saveloc [save location]
                        Path where the outpt csv file should be saved.
  --vehColumnName [vehicle class column name]
                        The column name for the vehicle class.
  --weightColumnName [weight class column name]
                        The column name for the vehicle weight class.
  --euroColumnName [euro class column name]
                        The column name for the vehicle euro class.
  --fuelColumnName [fuel column name]
                        The column name for the vehicle fuel.
  --yearColumnName [manufacture year column name]
                        The column name for the vehicle manufacture year. Only
                        used if flag --reassignEuro is used.
  --splitLoc            If set, then different proportions will be found for
                        each monitoring site and direction. Default False.
  --siteColumnName [anpr site column name]
                        The column name for the ANPR monitoring site name.
                        Only used if flag --splitLoc is used.
  --directionColumnName [direction column name]
                        The column name for the ANPR monitoring site
                        direction. Only used if flag --splitLoc is used.
  --keepTaxi            If set, will keep taxis as a seperate category,
                        otherwise taxis will be incorporated in to cars.
  --reassignEuro [Reassign Euro]
                        If 0, euro values provided in the source ANPR file
                        will be ignored and will instead be based on the
                        manufacture date. If 1, then vehicles with either no
                        specified euro class, or an assigned euroclass of 0,
                        will be reassigned based on manufacture date. If 2,
                        then the euro class will not be adjusted. The
                        manufacture date is an imperfect proxy for euro class,
                        but can be better than no estimate if the euro class
                        is missing from many records. Default 2.
```

## fleetSplit2EMIT.py ##
Creates a route type csv file of the type whose contents can be copied and
pasted in to EMIT to change the proportions of different vehicle categories
with a particular route type.

### Usage: fleetSplit2EMIT.py ###
```text
usage: fleetSplit2EMIT.py [-h] [--saveloc [save location]] anprfile basefile

Creates a route type csv file of the type whose contents can be copied and
pasted in to EMIT to change the proportions of different vehicle categories
with a particular route type.

positional arguments:
  anprfile              The ANPR file to be processed. The ANPR file should be
                        a csv file created using fleetSplitFromANPR.
  basefile              A file containing the base route type proportions.
                        This should be created by clicking 'copy' on the route
                        type window of EMIT, pasteing the results in to a
                        spreadsheet, and saving as a csv file.

optional arguments:
  -h, --help            show this help message and exit
  --saveloc [save location]
                        Path where the outpt csv file should be saved.
```