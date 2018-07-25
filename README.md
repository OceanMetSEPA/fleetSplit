

## fleetSplit2EMIT.py ##
Creates a route type csv file of the type whose contents can be copied and
pasted in to EMIT to change the proportions of different vehicle categories
with a particular route type.

### Usage fleetSplit2EMIT.py ###
```text
usage: fleetSplit2EMIT.py [-h] [--saveloc [save location]] anprfile basefile

Creates a route type csv file of the type whose contents can be copied and
pasted in to EMIT to change the proportions of different vehicle categories
with a particular route type.

positional arguments:
  anprfile              The ANPR file to be processed. The ANPR file should be
                        a csv file listing all vehicles passing the ANPR
                        counter (including double counting of vehicles that
                        have passed more than once). There should be a column
                        each for vehicle class, euro class, weight class and
                        fuel.
  basefile              A file containing the base route type proportions.
                        This should be created by clicking 'copy' on the route
                        type window of EMIT, pasteing the results in to a
                        spreadsheet, and saving as a csv file.

optional arguments:
  -h, --help            show this help message and exit
  --saveloc [save location]
                        Path where the outpt csv file should be saved.
```


## fleetSplitFromANPR.py ##

### Usage fleetSplitFromANPR.py ###
