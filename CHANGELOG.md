1/22/2016
Various bug fixes

###Cross-correlate R and L data
Use cross-correlation of L and R data to measure time offset between data streams. Also measure time scaling factor between the data sets. Uses Python graphing to display results. 'crosscorr = True' used to switch on capability. Other variables documented in code. 


12/30/2015

###Adding extra dummy datapoints
For pauses more than some amount (default = 5s) the script can add dummy datapoints that force the step rate to 0 etc during the pause. In first version two datapoints were added. An improvement is to add extra datapoints every approx 1.2s (equivalent of 100 steps per min). Code adapts the exact time gap to fit in a whole number of datapoints.

###Separate Email/password file
Users can edit their runscribe email and password in the script. However, this makes working with GitHub more complicated as need to make sure actual email/pwd are not uploaded into the repository. Instead create 'userdata.config' to hold this data. This file can be excluded from uploads to GitHub. Users can still edit email/pwd in main script for their local use, or else include info in userdata.config (based on userdata.config.example included in GitHub.

###Intervals (split) support added
A summary of each active/pause region is logged in 'runlog.csv'. Pace and average step rate for the interval is calculated along with average values for the other metrics. See example file.


