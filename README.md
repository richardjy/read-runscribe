# read-runscribe
Read run data from RunScribe Dashboard and export to CSV format (using Python scripting). Also, analyzes data to identify active v. pause regions, so that active time and distance can be estimated.

###Python
1. Open source scripting language
2. Version used for development 3.5
3. Uses "requests" module - see for example https://pypi.python.org/pypi/requests/

###Script variables
1. rs_email and rs_password MUST be set to the email and password used to access the RunScribe Dashboard.
2. Other variables are described in the script - in particular 'min_delta' and 'min_step_rate' determine whether a data point is 'active' or 'pause'

###Running script - Script input
1. Enter run number (e.g. 98765 for data https://dashboard.runscribe.com/runs/98765)
2. Press to exit

###Script output:
Screen output - example
> 2015-12-10 11:45  
> left - Active: 5.69 mi 00:44:05 07:45 min/mi Pause: 00:03:37 Total: 5.98 mi 00:47:42 DistRatio: 1.052  
> right - Active: 5.67 mi 00:44:03 07:46 min/mi Pause: 00:03:39 Total: 6.00 mi 00:47:42 DistRatio: 1.059  

- First line shows data and time
- Active = distance, time, and pace for active section
- Pause = time for pause section
- Total = total distance and time (active + pause) - note the total time matches the Dashboard value, but the total distance is normally a little lower (I tried several ways to calculate the pause distance that the dashboard is including in the run, but still ended up with a difference)
- Dashboard distance also includes distance traveled during pauses (see earlier discussion in this thread), so even if stationary the starting (and/or stopping) pace is assumed for the time you stopped (e.g. if stop for 2mins and first datapoint when starting up again is 10min/mile, then the pause time will add 0.2 miles to the distance even though you didn't actually go anywhere).
- DistRatio - ratio of Total/active distance - purpose is to help calibrate runs to give active distance that matches your actual run - e.g. if actual should be 5miles and ratio is 1.1 then setting calibrated distance to 5.5miles should give more accurate paces etc. The discrepancy between the script's calculation of total distance and that displayed in the Dashboard means the ratio is currently not quite correct for accurate calibration. You can manually calculate Dashboard_dist/active_dist and use this as the ratio.

###Script output - log files (saved in same folder as the script)

1. Data files: creates 'run_98765left.csv' and/or 'run_98765right.csv' - overwrites any files with same name.
The data file includes 'time' in three ways - full date-time, elapsed time in seconds, and elapsed time in hh:mm:ss format
active_status is 1 for active sections, 0 for pauses
the other columns should be self explanatory

2. Log file: appends summary data about the run to end of 'runlog.csv'

###Error messages
1. If error message mentions 'requests' then you have not installed the 'requests' module (see above)
2. Entering an incorrect run number (you can only access your own runs) will prompt for number again
  * If see prompt and the number is correct then check email and password
  * If email/password OK then set 'read_tod' to False - there might be some difference in the web page layout causing the search for date and time to fail
3. Script will abort if CSV file is already open in Excel (or similar program that locks the opened file). Having a file open in Notepad is OK.

###SportTracks (Desktop version 3.1 - not tried with mobi version)
1. Setting 'sporttracks = True' (default) adds an extra line of header data that enables import of CSV into SportTracks
2. To import use 'WB CSV Importer' plugin for SportTracks
http://www.zonefivesoftware.com/sporttracks/plugins/?p=wb-csv-importer
3. By default 'step_rate' is imported into 'cadence' and 'pace' is imported into 'power'. Any of the other data sets can be imported by moving the position of 'power' to a different position in the header.
