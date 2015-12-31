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
    from configparser import ConfigParser

    #input is datetime format - allows formating with rounded numbers
    def showHMS(dt): #output is string for H:M:S rounded to nearest second (e.g. for run time)
        dt = dt + timedelta(seconds=0.5)
        return dt.strftime('%H:%M:%S')

    def showMS(dt): #output is string for M:S rounded to nearest second (e.g. for pace)
        dt = dt + timedelta(seconds=0.5)
        return dt.strftime('%M:%S')

    def showMSd(dt): #output is string for M:S.d rounded to nearest tenth (e.g. for interval)
        dt = dt + timedelta(seconds=0.05)
        return dt.strftime('%M:%S.%f')[:-5]
        
    def showHMSd(dt): #output is string for H:M:S.d rounded to nearest tenth (e.g. for interval)
        dt = dt + timedelta(seconds=0.05)
        return dt.strftime('%H:%M:%S.%f')[:-5]

    def getjson(url, p): # get json data using payload 'p' as authentication
        r = s.get(url, params=p)
        return r.json()
        
    def addactiveinterval():
        # set index value        
        iactive_index[shoe].append(pt-1) 
        
        #store interval values
        last_index = iactive_index[shoe][interval-1]        
        iactive_time[shoe].append(iactive_time[shoe][0] - (last_index>-1)*active_time[shoe][last_index])                           
        iactive_dist[shoe].append(iactive_dist[shoe][0] - (last_index>-1)*active_dist[shoe][last_index])
        iactive_step[shoe].append(iactive_step[shoe][0] - (last_index>-1)*sum(iactive_step[shoe][1:(interval)]))
        # calculate average metrics, assuming there is some data        
        if some_activity == True:         
            iactive_pace[shoe].append(iactive_time[shoe][interval]/(60000*iactive_dist[shoe][interval]))        
            iactive_step_rate[shoe].append(iactive_step[shoe][interval]*60000/iactive_time[shoe][interval])
        else:
            iactive_pace[shoe].append(0)
            iactive_step_rate[shoe].append(0)
            
        # ranges for summed averages                
        start_pt = ipause_index[shoe][interval-1] + 1  
        end_pt = pt #one past end
        range_pt = end_pt-start_pt
        if range_pt == 0: range_pt = 1
        iactive_contact[shoe].append(sum(contact_time['mountings'][shoe]['values'][start_pt:end_pt])/range_pt)
        iactive_stride_length[shoe].append(sum(stride_length['mountings'][shoe]['values'][start_pt:end_pt])/range_pt)
        iactive_braking_gs[shoe].append(sum(braking_gs['mountings'][shoe]['values'][start_pt:end_pt])/range_pt)
        iactive_impact_gs[shoe].append(sum(impact_gs['mountings'][shoe]['values'][start_pt:end_pt])/range_pt)
        iactive_footstrike[shoe].append(sum(footstrike_type['mountings'][shoe]['values'][start_pt:end_pt])/range_pt)
        iactive_max_pronation_vel[shoe].append(sum(max_pronation_velocity['mountings'][shoe]['values'][start_pt:end_pt])/range_pt)
        iactive_pro_fs_mp[shoe].append(sum(pronation_excursion_fs_mp['mountings'][shoe]['values'][start_pt:end_pt])/range_pt)
        iactive_pro_mp_to[shoe].append(sum(pronation_excursion_mp_to['mountings'][shoe]['values'][start_pt:end_pt])/range_pt)
        iactive_stance_fs_mp[shoe].append(sum(stance_excursion_fs_mp['mountings'][shoe]['values'][start_pt:end_pt])/range_pt)
        iactive_stance_mp_to[shoe].append(sum(stance_excursion_mp_to['mountings'][shoe]['values'][start_pt:end_pt])/range_pt)
        return True

    def summaryactiveinterval():
        #store summary interval values
        iactive_pace[shoe][0] = iactive_time[shoe][0]/(60000*iactive_dist[shoe][0])
        iactive_step_rate[shoe][0] = iactive_step[shoe][0]*60000/iactive_time[shoe][0]
        # count which points are active
        range_pt = len([(contact_time['mountings'][shoe]['values'][i]) for i,j in enumerate(status_active[shoe]) if j !=0])
        # find average for all points
        iactive_contact[shoe][0] = (sum([(contact_time['mountings'][shoe]['values'][i]) for i,j in enumerate(status_active[shoe]) if j !=0])/range_pt)
        iactive_stride_length[shoe][0] = (sum([(stride_length['mountings'][shoe]['values'][i]) for i,j in enumerate(status_active[shoe]) if j !=0])/range_pt)
        iactive_braking_gs[shoe][0] = (sum([(braking_gs['mountings'][shoe]['values'][i]) for i,j in enumerate(status_active[shoe]) if j !=0])/range_pt)
        iactive_impact_gs[shoe][0] = (sum([(stride_length['mountings'][shoe]['values'][i]) for i,j in enumerate(status_active[shoe]) if j !=0])/range_pt)
        iactive_footstrike[shoe][0] = (sum([(footstrike_type['mountings'][shoe]['values'][i]) for i,j in enumerate(status_active[shoe]) if j !=0])/range_pt)
        iactive_max_pronation_vel[shoe][0] = (sum([(max_pronation_velocity['mountings'][shoe]['values'][i]) for i,j in enumerate(status_active[shoe]) if j !=0])/range_pt)
        iactive_pro_fs_mp[shoe][0] = (sum([(pronation_excursion_fs_mp['mountings'][shoe]['values'][i]) for i,j in enumerate(status_active[shoe]) if j !=0])/range_pt)
        iactive_pro_mp_to[shoe][0]= (sum([(pronation_excursion_mp_to['mountings'][shoe]['values'][i]) for i,j in enumerate(status_active[shoe]) if j !=0])/range_pt)
        iactive_stance_fs_mp[shoe][0] = (sum([(stance_excursion_fs_mp['mountings'][shoe]['values'][i]) for i,j in enumerate(status_active[shoe]) if j !=0])/range_pt)
        iactive_stance_mp_to[shoe][0] = (sum([(stance_excursion_mp_to['mountings'][shoe]['values'][i]) for i,j in enumerate(status_active[shoe]) if j !=0])/range_pt)
        return True

    # Main code

    # start of input variables
    #login and password for RunScribe.com account - needed to access data
    try: #try to read 'userdata.config' file (see example version)
        parser = ConfigParser()
        parser.read('userdata.config')
        rs_email = parser.get('runscribe', 'email')
        rs_password = parser.get('runscribe', 'password')
    except: # otherwise can use these hardcoaded values (if userdata.config exists then don't need to edit hardcoded values)
        rs_email = 'user@email.com'
        rs_password = 'password'  

    # analysis values
    #  if delta is more than min_delta (in ms) or step_rate less than min_step_rate then
    #  treat as a pause rather than active
    min_delta=3500
    min_step_rate = 50

    # try to read time of day and date from web page
    #  (may be unreliable in other countries?)
    #  if set to false then date set to april 1, 2015
    read_tod = True

    # sporttracks = True add extra header line for WB CSV plugin
    #   WB CSV plugin only recognizes fields in second line, so just uses these
    #   plugin only supports time, cadence, but can import pace (or other parameter) as power 
    sporttracks = True

    # forcing pauses to have step rate of zero - improves look of graphs
    #   if delta > gap_delta then add blank section into trace (+/- 700ms) 
    gap_on = False      # whether to add gaps, set to True to add gaps
    gap_delta = 5000    # if longer than 5s then add gap data
    gap_step_rate = 0
    gap_stride_pace = 100  # arbitary
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

        run_tod = datetime.strptime(run_date + ' ' + run_tod, '%d %b %Y %I:%M %p')
        # miles or km? also set updelimter
        stride2dist = 1/5280 #convert stride in ft into miles, factor for cm and km is 1E5 


        # append summary data to general logfile
        log_file = open('runlog.csv', 'a')
        logstr = 'Run: ' + str(run_index) + '   ' + run_tod.strftime('%Y-%m-%d %H:%M')
        print (run_tod.strftime('%Y-%m-%d %H:%M')) 
        log_file.write('\n\nRun, ' + str(run_index) + ',' + run_tod.strftime('%Y-%m-%d %H:%M') + '\n')
        log_file.write('min_delta, ' + str(min_delta) + ', min_step_rate, ' + str(min_step_rate) + '\n')
        log_file.write('\nShoe, Active time, Active dist (mi), Active pace (mi/min), Pause time, Total distance (mi), Total time, Distance ratio\n')
        
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

        # initialize pause, active time
        # these are accumulated values through the run (could be added to JSON structure)
        status_active = [[0],[0]]       # pause = 0, active = interval index
        pause_time = [[0],[0]]          # in milliseconds
        active_time = [[0],[0]]              
        pause_dist = [[0],[0]]          # in miles / km (depending on setup)
        active_dist = [[0],[0]]
        
        # interval settings - interval 0 is accumulated value       
        ipause_time = [[0],[0]]
        iactive_time = [[0],[0]]
        ipause_dist = [[0],[0]]
        iactive_dist = [[0],[0]]
        ipause_index = [[0],[0]]
        iactive_index = [[0],[0]]
        iactive_pace = [[0],[0]]        # in min/mi, digital rather than mm:ss
        iactive_step = [[0],[0]]        # step count
        iactive_step_rate = [[0],[0]]   # active step rate
        iactive_stride_length = [[0],[0]]       
        iactive_contact = [[0],[0]]      # average contact time  
        iactive_braking_gs = [[0],[0]]  
        iactive_impact_gs = [[0],[0]]  
        iactive_footstrike = [[0],[0]]  
        iactive_max_pronation_vel = [[0],[0]]  
        iactive_pro_fs_mp = [[0],[0]]  
        iactive_pro_mp_to = [[0],[0]]  
        iactive_stance_fs_mp = [[0],[0]]  
        iactive_stance_mp_to = [[0],[0]]  
        
        # are there one or two data sets?
        no_feet=(len(step_rate['mountings']))
        for shoe in range(0, no_feet):
            foot = (step_rate['mountings'][shoe]['foot'])
            interval = 1
            iactive_index[shoe][0] = -1
            ipause_index[shoe][0] = -1 #i.e. starting active section is index=0
           # ipause_time[shoe][0] = 0
           # ipause_dist[shoe][0] = 0            
            
            # look at the rest of the points - add extra points in long pauses
            some_activity = False 
            current_status = "active"
            pt = 0
            while pt < (len(step_rate['mountings'][shoe]['values'])-1) : 
                # delta time = T(n+1) - T(n)   cadence = 120/DT   rate (min/mi)= DT.5280/(60.Stride_length) 
                delta_time=(step_rate['mountings'][shoe]['timestamps'][pt+1]) - (step_rate['mountings'][shoe]['timestamps'][pt])
                pt_step_rate = (step_rate['mountings'][shoe]['values'][pt])
                pt_step_count = delta_time*pt_step_rate/60000 #normally = 2, 2 steps = 1 stride length
                if pt>0 : # special for first point
                    pt_stride_lengthneg1 = (stride_length['mountings'][shoe]['values'][pt-1])
                else: pt_stride_lengthneg1 = (stride_length['mountings'][shoe]['values'][pt])
                pt_stride_length0 = (stride_length['mountings'][shoe]['values'][pt])
                pt_stride_length1 = (stride_length['mountings'][shoe]['values'][pt+1])
                pt_distneg1 = stride2dist*pt_stride_lengthneg1*pt_step_count/2    # use stride length of previous period  
                pt_dist0 = stride2dist*pt_stride_length0*pt_step_count/2    # use stride length at beginning of period             
                pt_dist1 = stride2dist*pt_stride_length1*pt_step_count/2    # use stride length at end of period
                # several ways to possibly combine these values - none give same answer as DashBoard                
                pt_dist01 = (pt_dist0 + pt_dist1)/2  # average                 
                pt_distn01 = (pt_distneg1 + pt_dist0 + pt_dist1)/3  # average 
                pt_dist = pt_dist01 #use this one for distance
                
                if (delta_time > min_delta) or (pt_step_rate < min_step_rate): # pause period
                    ipause_time[shoe][0] += delta_time
                    ipause_dist[shoe][0] += pt_dist
                    
                    if (current_status == "active"): #end of an active period 
                        addactiveinterval()
                        current_status = "pause"
                    if (delta_time > gap_delta) and (gap_on == True) and (pt != 0):
                        # fill in data in the gap - starting 700ms after last point and ending 700ms before next
                        gap_start = step_rate['mountings'][shoe]['timestamps'][pt-1] + 700
                        gap_end = step_rate['mountings'][shoe]['timestamps'][pt] - 700                        
                        #add a point roughtly every 1.2 seconds in the gap 
                        num2add = int(round((gap_end - gap_start)/1200, 0))  
                        gap_time = (gap_end - gap_start)/num2add 
                        pause_start =  pause_time[shoe][pt-1] + 700                       
                        for n in range(0, num2add+1) :
                            #note should really change all data timestamps, but OK if only use those from step_rate                            
                            step_rate['mountings'][shoe]['timestamps'].insert(pt, gap_start + n*gap_time)  
                            step_rate['mountings'][shoe]['values'].insert(pt, gap_step_rate)
                            stride_pace['mountings'][shoe]['values'].insert(pt, gap_stride_pace)
                            stride_length['mountings'][shoe]['values'].insert(pt, gap_stride_length)
                            contact_time['mountings'][shoe]['values'].insert(pt, gap_contact_time)
                            braking_gs['mountings'][shoe]['values'].insert(pt, gap_braking_gs)
                            impact_gs['mountings'][shoe]['values'].insert(pt, gap_impact_gs)
                            footstrike_type['mountings'][shoe]['values'].insert(pt, gap_footstrike_type)
                            max_pronation_velocity['mountings'][shoe]['values'].insert(pt, gap_max_pronation_velocity)
                            pronation_excursion_fs_mp['mountings'][shoe]['values'].insert(pt, gap_pronation_excursion_fs_mp)
                            pronation_excursion_mp_to['mountings'][shoe]['values'].insert(pt, gap_pronation_excursion_mp_to)
                            stance_excursion_fs_mp['mountings'][shoe]['values'].insert(pt, gap_stance_excursion_fs_mp)
                            stance_excursion_mp_to['mountings'][shoe]['values'].insert(pt, gap_stance_excursion_mp_to)
                            #handle extra data sets
                            pause_time[shoe].append(pause_start + n*gap_time)
                            pause_dist[shoe].append(pause_dist[shoe][pt-1])
                            active_time[shoe].append(iactive_time[shoe][0])
                            active_dist[shoe].append(iactive_dist[shoe][0])
                            status_active[shoe].append(0)
                            pt+=1
                else : # active period
                    some_activity = True                    
                    if (current_status == "pause"): #start of an active period, log pause info
                        last_index = ipause_index[shoe][interval-1] #if last_index = -1 then first interval                          
                        ipause_time[shoe].append(ipause_time[shoe][0] - (last_index>-1)*pause_time[shoe][last_index])                           
                        ipause_dist[shoe].append(ipause_dist[shoe][0] - (last_index>-1)*pause_dist[shoe][last_index])                          
                        ipause_index[shoe].append(pt-1)
                        current_status = "active"                        
                        interval+=1
                    iactive_time[shoe][0] += delta_time
                    iactive_dist[shoe][0] += pt_dist
                    iactive_step[shoe][0] += pt_step_count 
                # first data point
                if (pt == 0): 
                    pause_time[shoe][0] = ipause_time[shoe][0]
                    pause_dist[shoe][0] = ipause_dist[shoe][0]
                    active_time[shoe][0] = iactive_time[shoe][0]
                    active_dist[shoe][0] = iactive_dist[shoe][0] 
                    status_active[shoe][0] = interval*(current_status == "active")
                else:
                    pause_time[shoe].append(ipause_time[shoe][0])
                    pause_dist[shoe].append(ipause_dist[shoe][0])
                    active_time[shoe].append(iactive_time[shoe][0])
                    active_dist[shoe].append(iactive_dist[shoe][0])
                    status_active[shoe].append(interval*(current_status == "active"))
                pt+=1
            
            # log one last set of interval data - assume stame staus as previous point
            pt_step_rate = (step_rate['mountings'][shoe]['values'][pt])
            pt_step_count = 2 #no more points so assume 2 steps
            delta_time =  120/pt_step_rate
            pt_stride_length0 = (stride_length['mountings'][shoe]['values'][pt])
            pt_dist = stride2dist*pt_stride_length0 # use stride length at beginning of period             

            if (current_status == "active"): #end of an active period            
                iactive_time[shoe][0] += delta_time
                iactive_dist[shoe][0] += pt_dist
                iactive_step[shoe][0] += pt_step_count 
                status_active[shoe].append(interval)
                
                # end of active period                
                addactiveinterval()                  

              # add data for non-existant pause                
                ipause_time[shoe].append(0)
                ipause_dist[shoe].append(0)
                ipause_index[shoe].append(pt-1)
            else:
                last_index = ipause_index[shoe][interval-1]                          
                ipause_time[shoe].append(ipause_time[shoe][0] - (last_index>-1)*pause_time[shoe][last_index])                           
                ipause_dist[shoe].append(ipause_dist[shoe][0] - (last_index>-1)*pause_dist[shoe][last_index])
                ipause_index[shoe].append(pt-1) 
                status_active[shoe].append(0)
            
            pause_time[shoe].append(ipause_time[shoe][0])
            pause_dist[shoe].append(ipause_dist[shoe][0])
            active_time[shoe].append(iactive_time[shoe][0])
            active_dist[shoe].append(iactive_dist[shoe][0])
            interval+=1            
            

            # update number of points
            no_pts = (len(step_rate['mountings'][shoe]['values']))
            
            summaryactiveinterval()    
            # distance in miles/km, times in datetime format
            total_dist = iactive_dist[shoe][0] + ipause_dist[shoe][0]
            distance_ratio = total_dist/iactive_dist[shoe][0] #can be used to enter calibration value for run that includes pauses
            
            # format in mm:ss style
            total_active_time = datetime.min + timedelta(seconds=iactive_time[shoe][0]/1000)
            total_pause_time = datetime.min + timedelta(seconds=ipause_time[shoe][0]/1000)
            total_time = total_active_time + timedelta(seconds=ipause_time[shoe][0]/1000)
            active_pace_time =  datetime.min + timedelta(seconds=iactive_pace[shoe][0]*60)

            print(foot+ ' -' + '\tActive: {0:.2f}'.format(iactive_dist[shoe][0]) + ' mi ' + showHMS(total_active_time) \
                  + ' ' + showMS(active_pace_time) + ' min/mi  Pause: ' + showHMS(total_pause_time) \
                  + '  Total: {0:.2f}'.format(total_dist) + ' mi ' + showHMS(total_time) \
                  + ' DistRatio: {0:.3f}'.format(distance_ratio))

            # append summary data to general logfile
            log_file.write(foot + ', ' + showHMS(total_active_time) + ', {0:.2f}'.format(iactive_dist[shoe][0]) + ', ' \
                  + showMS(active_pace_time) + ', ' +  showHMS(total_pause_time) + ', {0:.2f}'.format(total_dist) + ', ' \
                  + showHMS(total_time) + ', {0:.3f}'.format(distance_ratio) + '\n')

            # save to logfile along with other key data (overwite old file) name format 'run_XXXXXfoot.cvs'
            csv_file = open('run_' + str(run_index) + foot + '.csv', 'w')
            csv_file.write('datetime, time (s), time (hms), active_status, active_dist (mi), active_time (s), pause_time (s), ' \
                           + 'stride_pace (mi/min), step_rate (s/min), stride_length (ft), contact_time (ms), braking_gs, impact_gs, ' \
                           + 'footstrike_type, max_pronation_vel, pronation_fs_mp, pronation_mp_to,' \
                           + 'stance_fs_mp, stance_mp_to \n')

            if sporttracks == True :  # add headers just for sporttracks WBS CSV plugin - use power as input for one of RunScribe values
                csv_file.write('datetime, , , , , , , ' \
                           + 'power, cadence, , , , , , , , , , , \n') #import pace as power
            for pt in range(0, no_pts):
                time_sec = (step_rate['mountings'][shoe]['timestamps'][pt])/1000
                pt_tod = run_tod + timedelta(seconds=time_sec)
                pt_time = datetime.min + timedelta(seconds=time_sec)
                csv_file.write(pt_tod.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] + ', ' #show millisecs not microsecs \  
                               + str(time_sec) + ', ' \
                               + pt_time.strftime('%H:%M:%S.%f')[:-3] + ', ' \
                               + str(status_active[shoe][pt]) + ', ' \
                               + '{number:.{digits}f}, '.format(number=(active_dist[shoe][pt]), digits=4) \
                               + '{number:.{digits}f}, '.format(number=(active_time[shoe][pt]/1000), digits=1) \
                               + '{number:.{digits}f}, '.format(number=(pause_time[shoe][pt]/1000), digits=1) \
                               + str(stride_pace['mountings'][shoe]['values'][pt]) + ', ' \
                               + str(step_rate['mountings'][shoe]['values'][pt]) + ', ' \
                               + str(stride_length['mountings'][shoe]['values'][pt]) + ', ' \
                               + str(contact_time['mountings'][shoe]['values'][pt]) + ', ' \
                               + str(braking_gs['mountings'][shoe]['values'][pt]) + ', ' \
                               + str(impact_gs['mountings'][shoe]['values'][pt]) + ', ' \
                               + str(footstrike_type['mountings'][shoe]['values'][pt]) + ', ' \
                               + str(max_pronation_velocity['mountings'][shoe]['values'][pt]) + ', ' \
                               + str(pronation_excursion_fs_mp['mountings'][shoe]['values'][pt]) + ', ' \
                               + str(pronation_excursion_mp_to['mountings'][shoe]['values'][pt]) + ', ' \
                               + str(stance_excursion_fs_mp['mountings'][shoe]['values'][pt]) + ', ' \
                               + str(stance_excursion_mp_to['mountings'][shoe]['values'][pt]) + '\n')
            csv_file.close()
        # print interval data to log file
        log_file.write('\nshoe, interval#, time of day, time(s), time(hms), active_time, active_dist,  active_pace, pause_time, ' \
                                + 'step_rate (s/min), stride_length (ft), contact_time (ms), braking_gs, impact_gs, ' \
                                + 'footstrike_type, max_pronation_vel, pronation_fs_mp, pronation_mp_to,' \
                                + 'stance_fs_mp, stance_mp_to, active_index, pause_index, pause_dist, active steps \n')   
        for shoe in range(0, no_feet):
            foot = (step_rate['mountings'][shoe]['foot'])  
            no_ints = (len(iactive_index[shoe]))
            for i in range(0, no_ints):
                start_pt = ipause_index[shoe][i]                
                time_sec = (step_rate['mountings'][shoe]['timestamps'][start_pt+1])/1000
                pt_tod = run_tod + timedelta(seconds=time_sec)
                pt_time = datetime.min + timedelta(seconds=time_sec)
                # print summary of steps?
                log_file.write(foot + ', ' + str(i) + ', '  \
                               + showHMS(run_tod + timedelta(seconds=time_sec)) + ', '   \
                               + locale.format_string('%.1f', time_sec) + ', ' \
                               + showHMSd(datetime.min + timedelta(seconds=time_sec)) + ', '   \
                               + showHMSd(datetime.min + timedelta(seconds=iactive_time[shoe][i]/1000)) + ', '  \
                               + locale.format_string('%.2f',(iactive_dist[shoe][i])) + ', '  \
                               + showMSd(datetime.min + timedelta(seconds=iactive_pace[shoe][i]*60)) + ', '  \
                               + showHMSd(datetime.min + timedelta(seconds=ipause_time[shoe][i]/1000)) + ', '  \
                               + locale.format_string('%.1f', iactive_step_rate[shoe][i]) + ', ' \
                               + locale.format_string('%.2f', iactive_stride_length[shoe][i]) + ', ' \
                               + locale.format_string('%.0f', iactive_contact[shoe][i]) + ', ' \
                               + locale.format_string('%.2f', iactive_braking_gs[shoe][i]) + ', ' \
                               + locale.format_string('%.2f', iactive_impact_gs[shoe][i]) + ', ' \
                               + locale.format_string('%.1f', iactive_footstrike[shoe][i]) + ', ' \
                               + locale.format_string('%.0f', iactive_max_pronation_vel[shoe][i]) + ', ' \
                               + locale.format_string('%.1f', iactive_pro_fs_mp[shoe][i]) + ', ' \
                               + locale.format_string('%.1f', iactive_pro_mp_to[shoe][i]) + ', ' \
                               + locale.format_string('%.1f', iactive_stance_fs_mp[shoe][i]) + ', ' \
                               + locale.format_string('%.1f', iactive_stance_mp_to[shoe][i]) + ', ' \
                               + str(iactive_index[shoe][i]) + ', '  + str(ipause_index[shoe][i]) + ', ' \
                               + locale.format_string('%.2f',(ipause_dist[shoe][i]))  + ', ' \
                               + locale.format_string('%.0f',(iactive_step[shoe][i])) + '\n') 
            log_file.write('\n')              
        log_file.close()

except: # called on all errors - needs better trapping!
    print("\nThere was an error:")
    exc_type, exc_value, exc_traceback = sys.exc_info()
    traceback.print_exception(exc_type, exc_value, exc_traceback, \
                              limit=2, file=sys.stdout)
    
    input("\nPress <Enter> to Exit")

  
