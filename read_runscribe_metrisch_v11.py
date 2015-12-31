# reads data from RunScribe account
# exports CSV file(s) in form viewable in Excel etc
# CSV importable into Sporttracks 3.1 desktop (using "WB CSV importer" plugin)
# assumes US settings, including yards and miles. Not tested with metres and km.
# Richard Young - December 2015 

try:   #generic error trapping 
    import sys, traceback, locale
    import requests  # not part of the default python install - see http://docs.python-requests.org/en/latest/
    import re
    from datetime import datetime, timedelta

    #input is datetime format - allows formating with rounded numbers
    def showHMS(dt): #output is string for H:M:S rounded to nearest second (e.g. for run time)
        dt = dt + timedelta(seconds=0.5)
        return dt.strftime('%H:%M:%S')

    def showMS(dt): #output is string for M:S rounded to nearest second (e.g. for pace)
        dt = dt + timedelta(seconds=0.5)
        return dt.strftime('%M:%S')

    def showMSd(dt): #output is string for M:S.d rounded to nearest tenth (e.g. for interval)
        dt = dt + timedelta(seconds=0.05)
        return dt.strftime('%M:%S,%f')[:-5]

    def getjson(url, p): # get json data using payload 'p' as authentication
        r = s.get(url, params=p)
        return r.json()

    # Main code
    # start of input variables
    #login and password for RunScribe.com account - needed to access data
    rs_email = 'email'
    rs_password = 'password'    

    # analysis values
    #   if delta is more than min_delta (in ms) or step_rate less than min_step_rate then
    #   treat as a pause rather than active
    min_delta=3500
    min_step_rate = 120

    # try to read time of day and date from web page
    #(may be unreliable in other countries?)
    # if set to false then date set to april 1, 2015
    read_tod = True

    # sporttracks = True add extra header line for WB CSV plugin
    # WB CSV plugin only recognizes fields in second line, so just uses these
    # plugin only supports time, cadence, but can import pace (or other parameter) as power 
    sporttracks = False

    # forcing pauses to have step rate of zero - improves look of graphs
    # if delta > gap_delta then add blank section into trace (+/- 700ms) 
    gap_on = False      # whether to add gaps, set to True to add gaps
    gap_delta = 10000    # if longer than 5s then add gap data
    gap_step_rate = 0
    gap_stride_pace = 500  # arbitary. Larger value might be more realistic
    gap_stride_length = 0
    gap_contact_time = 1000 #arbitrarily set to 1 second
    gap_braking_gs = 0
    gap_impact_gs = 0
    gap_footstrike_type = 0
    gap_max_pronation_velocity =  0
    gap_pronation_excursion_fs_mp =  0
    gap_pronation_excursion_mp_to =  0
    gap_stance_excursion_fs_mp =  0
    gap_stance_excursion_mp_to =  0  
    # end of input variables
    
    #runscribe dashboard
    url_login = 'https://dashboard.runscribe.com/login'

    # get login info - fetch the login page
    s = requests.session()
    r = s.get(url_login)

    # get authentication info - find string from login page
    matchme = 'authenticity_token" value="(.*)" /><div'
    csrf = re.search(matchme,str(r.text))

    # set up data to login  
    payload = {'authenticity_token': csrf.group(1), 'email': rs_email, 'password': rs_password}
       
    # post to the login form
    (s.post(url_login, params=payload))

    while True:
        #make sure US format for first part so that date format from web site is parsed correctly
        locale.setlocale(locale.LC_ALL, 'US')         
        # input run number
        data = input('\nRun index (<Enter> to exit): ')
        if data == '' : break #end the loop
        try:
            run_index = int(data)
        except ValueError:
            print('Not an integer')
            continue
    
        url_runs = 'https://dashboard.runscribe.com/runs/' + str(run_index)
        url_metric = url_runs + '/metric/'

        run_tod = '12:00 AM' #set default value
        run_date = '1 Apr 2015'
        if (read_tod == True) :
            # get date and time for run from web page
            matchme = 'day, (.*)\n\|\n(.*PM|.*AM)$' 
            r = s.get(url_runs) # no need for payload
            tod_str = re.search(matchme,str(r.text), re.MULTILINE)
            if (tod_str != None) : 
                run_date = tod_str.group(1)
                run_tod = tod_str.group(2)
            else :
                print('Invalid run number, or cannot read date-time data')
                continue
        locale.setlocale(locale.LC_ALL, 'US') 
        run_tod = datetime.strptime(run_date + ' ' + run_tod, '%d %b %Y %I:%M %p')

        #locale.setlocale(locale.LC_ALL, '') # set to user's locale - 
        # force to be german for testing        
        locale.setlocale(locale.LC_ALL, 'DE')
        dec_pt_chr = locale.localeconv()['decimal_point']
        if dec_pt_chr == "." : # delim not currently used
            delim = ','
        else:
            delim = ';'

        # append summary data to general logfile
        log_file = open('runlog.csv', 'a')
        logstr = 'Run: ' + str(run_index) + '   ' + run_tod.strftime('%Y-%m-%d %H:%M')
        print (run_tod.strftime('%Y-%m-%d %H:%M')) 
        log_file.write('\n\nRun; ' + str(run_index) + ';' + run_tod.strftime('%Y-%m-%d %H:%M') + '\n')
        log_file.write('min_delta; ' + str(min_delta) + '; min_step_rate; ' + str(min_step_rate) + '\n')
        log_file.write('\nShoe; Active time; Active dist (km); Active pace (min/km); Pause time; Total distance (km); Total time; Distance ratio\n')
        
        # get metric data for step rate etc
        step_rate = getjson(url_metric + 'step_rate', payload)
        stride_pace = getjson(url_metric + 'stride_pace', payload)
        stride_length = getjson(url_metric + 'stride_length', payload)
        contact_time = getjson(url_metric + 'contact_time', payload)
        braking_gs = getjson(url_metric + 'braking_gs', payload)
        impact_gs = getjson(url_metric + 'impact_gs', payload)
        footstrike_type = getjson(url_metric + 'footstrike_type', payload)
        max_pronation_velocity = getjson(url_metric + 'max_pronation_velocity', payload)
        pronation_excursion_fs_mp = getjson(url_metric + 'pronation_excursion_fs_mp', payload)
        pronation_excursion_mp_to = getjson(url_metric + 'pronation_excursion_mp_to', payload)
        stance_excursion_fs_mp = getjson(url_metric + 'stance_excursion_fs_mp', payload)
        stance_excursion_mp_to = getjson(url_metric + 'stance_excursion_mp_to', payload)

        # is there one or two data sets?
        no_feet=(len(step_rate['mountings']))

        for shoe in range(0, no_feet):
            foot = (step_rate['mountings'][shoe]['foot'])

            # initialize pause, active time
            status_active = ["1"]
            pause = [0] # these are accumulated values through the run
            active = [0]
            pause_dist = [0]
            active_dist = [0]
            active_flag = 1
            interval = 1  # these are per interval - interval 0 is accumulated value
            ipause = [0]  # interval code not added yet
            iactive = [0]
            ipause_dist = [0]
            iactive_dist = [0]
            no_pts = (len(step_rate['mountings'][shoe]['values']))

            #initial point - don't add extra points here
            delta_time = (step_rate['mountings'][shoe]['timestamps'][0])
            pt_step_rate = (step_rate['mountings'][shoe]['values'][0])
            pt_stride_length = (stride_length['mountings'][shoe]['values'][0])
            pt_dist = (delta_time/60000)*(pt_step_rate/2)*pt_stride_length
            if (delta_time > min_delta) or (pt_step_rate < min_step_rate) :
                ipause[0] = delta_time
                ipause_dist[0] = pt_dist
                pause[0] = ipause[0]
                pause_dist[0] = ipause_dist[0]          
                status_active[0] = "0"
            else :
                iactive[0] = delta_time
                iactive_dist[0] = pt_dist
                active[0] = iactive[0]
                active_dist[0] = iactive_dist[0]
                status_active[0] = "1"

            # look at the rest of the points - add extra points in long pauses
            pt = 1
            while pt < len(step_rate['mountings'][shoe]['values']) :
                delta_time=(step_rate['mountings'][shoe]['timestamps'][pt]) - (step_rate['mountings'][shoe]['timestamps'][pt-1])
                pt_step_rate = (step_rate['mountings'][shoe]['values'][pt])
                pt_step_rate0 = (step_rate['mountings'][shoe]['values'][pt-1]) #-1
                pt_stride_length = (stride_length['mountings'][shoe]['values'][pt])
                pt_stride_length0 = (stride_length['mountings'][shoe]['values'][pt-1]) #-1
                pt_dist = (delta_time/60000)*((pt_step_rate0/2*pt_stride_length0 + pt_step_rate/2*pt_stride_length)/2) #use both ends of period
                if (delta_time > min_delta) or (pt_step_rate < min_step_rate):
                    ipause[0] += delta_time
                    ipause_dist[0] += pt_dist
                    status_active.append("0")
                    if (delta_time > gap_delta) and (gap_on == True) :  #add gaps to data
                        gap_start = step_rate['mountings'][shoe]['timestamps'][pt-1] + 700
                        gap_end = step_rate['mountings'][shoe]['timestamps'][pt] - 700
                        #note should really change all data timestamps, but OK if only use those from step_rate
                        step_rate['mountings'][shoe]['timestamps'].insert(pt, gap_start)  
                        step_rate['mountings'][shoe]['timestamps'].insert(pt+1, gap_end)
                        step_rate['mountings'][shoe]['values'].insert(pt, gap_step_rate)
                        step_rate['mountings'][shoe]['values'].insert(pt+1, gap_step_rate)
                        stride_pace['mountings'][shoe]['values'].insert(pt, gap_stride_pace)
                        stride_pace['mountings'][shoe]['values'].insert(pt+1, gap_stride_pace)
                        stride_length['mountings'][shoe]['values'].insert(pt, gap_stride_length)
                        stride_length['mountings'][shoe]['values'].insert(pt+1, gap_stride_length)
                        contact_time['mountings'][shoe]['values'].insert(pt, gap_contact_time)
                        contact_time['mountings'][shoe]['values'].insert(pt+1, gap_contact_time)
                        braking_gs['mountings'][shoe]['values'].insert(pt, gap_braking_gs)
                        braking_gs['mountings'][shoe]['values'].insert(pt+1, gap_braking_gs)
                        impact_gs['mountings'][shoe]['values'].insert(pt, gap_impact_gs)
                        impact_gs['mountings'][shoe]['values'].insert(pt+1, gap_impact_gs)
                        footstrike_type['mountings'][shoe]['values'].insert(pt, gap_footstrike_type)
                        footstrike_type['mountings'][shoe]['values'].insert(pt+1, gap_footstrike_type)
                        max_pronation_velocity['mountings'][shoe]['values'].insert(pt, gap_max_pronation_velocity)
                        max_pronation_velocity['mountings'][shoe]['values'].insert(pt+1, gap_max_pronation_velocity)
                        pronation_excursion_fs_mp['mountings'][shoe]['values'].insert(pt, gap_pronation_excursion_fs_mp)
                        pronation_excursion_fs_mp['mountings'][shoe]['values'].insert(pt+1, gap_pronation_excursion_fs_mp)
                        pronation_excursion_mp_to['mountings'][shoe]['values'].insert(pt, gap_pronation_excursion_mp_to)
                        pronation_excursion_mp_to['mountings'][shoe]['values'].insert(pt+1, gap_pronation_excursion_mp_to)
                        stance_excursion_fs_mp['mountings'][shoe]['values'].insert(pt, gap_stance_excursion_fs_mp)
                        stance_excursion_fs_mp['mountings'][shoe]['values'].insert(pt+1, gap_stance_excursion_fs_mp)
                        stance_excursion_mp_to['mountings'][shoe]['values'].insert(pt, gap_stance_excursion_mp_to)
                        stance_excursion_mp_to['mountings'][shoe]['values'].insert(pt+1, gap_stance_excursion_mp_to)
                        #handle extra data sets
                        pause.append(pause[pt-1] + 700)
                        pause.append(ipause[0] - 700)
                        pause_dist.append(pause_dist[pt-1])
                        pause_dist.append(ipause_dist[0])
                        active.append(iactive[0])
                        active.append(iactive[0])
                        active_dist.append(iactive_dist[0])
                        active_dist.append(iactive_dist[0])
                        status_active.append("0")
                        status_active.append("0")
                        pt+=2
                else :
                    iactive[0] += delta_time
                    iactive_dist[0] += pt_dist
                    status_active.append("1")
                pause.append(ipause[0])
                pause_dist.append(ipause_dist[0])
                active.append(iactive[0])
                active_dist.append(iactive_dist[0])
                pt+=1
            # update number of points
            no_pts = (len(step_rate['mountings'][shoe]['values']))
                
            # distance in miles, times in datetime format
            active_kilometer = iactive_dist[0]/1000
            active_pace = datetime.min + timedelta(seconds=(iactive[0]/(1000*active_kilometer)))
            pause_kilometer = ipause_dist[0]/1000
            total_kilometer = active_kilometer + pause_kilometer
            distance_ratio = total_kilometer/active_kilometer #can be used to enter calibration value for run that includes pauses
            active_time = datetime.min + timedelta(seconds=iactive[0]/1000)
            pause_time = datetime.min + timedelta(seconds=ipause[0]/1000)
            total_time = active_time + timedelta(seconds=ipause[0]/1000)

            print(foot+ ' -' + '\tActive: {0:.2f}'.format(active_kilometer) + ' km ' + showHMS(active_time) \
                  + ' ' + showMS(active_pace) + ' min/km  Pause: ' + showHMS(pause_time) \
                  + '  Total: {0:.2f}'.format(total_kilometer) + ' km ' + showHMS(total_time) \
                  + ' DistRatio: {0:.3f}'.format(distance_ratio))

            # append summary data to general logfile
            log_file.write(foot + '; ' + showHMS(active_time) + '; {0:.2f}'.format(active_kilometer) + '; ' \
                  + showMS(active_pace) + '; ' +  showHMS(pause_time) + '; {0:.2f}'.format(total_kilometer) + '; ' \
                  + showHMS(total_time) + '; {0:.3f}'.format(distance_ratio) + '\n')

            # save to logfile along with other key data (overwite old file) name format 'run_XXXXXfoot.cvs'
            csv_file = open('run_' + str(run_index) + foot + '_metric_v1''.csv', 'w')
            csv_file.write('datetime; time_s; time_h_m_s; active_status; active_dist_km; active_time_s; pause_time_s; ' \
                           + 'stride_pace_min/km; step_rate_steps/min; stride_length_cm; contact_time_ms; braking_gs; impact_gs; ' \
                           + 'footstrike_type; max_pronation_vel; pronation_fs_mp; pronation_mp_to;' \
                           + 'stance_fs_mp; stance_mp_to \n')

            if sporttracks == True :  # add headers just for sporttracks WBS CSV plugin - use power as input for one of RunScribe values
                csv_file.write('datetime, , , , , , , ' \
                           + 'power, cadence, , , , , , , , , , , \n') #import pace as power
            for pt in range(0, no_pts):
                time_sec = (step_rate['mountings'][shoe]['timestamps'][pt])/1000
                pt_tod = run_tod + timedelta(seconds=time_sec)
                pt_time = datetime.min + timedelta(seconds=time_sec)
                csv_file.write(pt_tod.strftime('%Y-%m-%d %H:%M:%S'+ dec_pt_chr + '%f')[:-3] + "; " #show millisecs not microsecs \  
                               + locale.str(time_sec) + '; ' \
                               + pt_time.strftime('%H:%M:%S'+ dec_pt_chr + '%f')[:-3] + '; ' \
                               + str(status_active[pt]) + '; ' \
                               + locale.format_string('%.3f',(active_dist[pt]/1000))  + '; ' \
                               + locale.format_string('%.1f', (active[pt]/1000))  + '; ' \
                               + locale.format_string('%.1f', (pause[pt]/1000))  + '; ' \
                               + locale.str(stride_pace['mountings'][shoe]['values'][pt]) + '; ' \
                               + locale.str(step_rate['mountings'][shoe]['values'][pt]) + '; ' \
                               + locale.str(stride_length['mountings'][shoe]['values'][pt]) + '; ' \
                               + locale.str(contact_time['mountings'][shoe]['values'][pt]) + '; ' \
                               + locale.str(braking_gs['mountings'][shoe]['values'][pt]) + '; ' \
                               + locale.str(impact_gs['mountings'][shoe]['values'][pt]) + '; ' \
                               + locale.str(footstrike_type['mountings'][shoe]['values'][pt]) + '; ' \
                               + locale.str(max_pronation_velocity['mountings'][shoe]['values'][pt]) + '; ' \
                               + locale.str(pronation_excursion_fs_mp['mountings'][shoe]['values'][pt]) + '; ' \
                               + locale.str(pronation_excursion_mp_to['mountings'][shoe]['values'][pt]) + '; ' \
                               + locale.str(stance_excursion_fs_mp['mountings'][shoe]['values'][pt]) + '; ' \
                               + locale.str(stance_excursion_mp_to['mountings'][shoe]['values'][pt]) + '\n')
            csv_file.close()
            del status_active[:]   #get rid of the lists so can reuse
            del active_dist[:]
            del active[:]
            del pause_dist[:]
            del pause[:]
        log_file.close()

except: # called on all errors - needs better trapping!
    print("\nThere was an error:")
    exc_type, exc_value, exc_traceback = sys.exc_info()
    traceback.print_exception(exc_type, exc_value, exc_traceback, \
                              limit=2, file=sys.stdout)
    
    input("\nPress <Enter> to Exit")
