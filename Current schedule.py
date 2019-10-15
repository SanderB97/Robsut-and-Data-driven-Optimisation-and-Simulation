
import pandas as pd
import numpy as np
import random

def transformToInterarrivalTimeWholeDay(fractionOfDay):
    hours = fractionOfDay*9                 #divided by 9: normally open only 9 hours (8 + lunch break) during a whole day (8-12, 13-17)
    seconds = hours*3600
    return int(seconds);                    #always uses floor

def transformToInterarrivalTimeHalfDay(fractionOfDay):
    hours = fractionOfDay*4                 #divided by 4: normally open only 8 hours during a whole day (8-12, 13-17)
    seconds = hours*3600
    return int(seconds);    

"""Functions that can be used to calculate waiting times"""
def calcDifferenceInSeconds(earliestTimestamp, latestTimestamp):  #Input parameters should be 'pd.Timestamp' objects like above
    delta = latestTimestamp - earliestTimestamp
    return delta.seconds;
def calcDifferenceInMinutes(earliestTimestamp, latestTimestamp):
    delta = latestTimestamp - earliestTimestamp
    return delta.seconds//60;
def calcDifferenceInHours(earliestTimestamp, latestTimestamp):
    delta = latestTimestamp - earliestTimestamp
    return delta.seconds//3600;
def calcDifferenceInDays(earliestTimestamp, latestTimestamp):
    delta = latestTimestamp - earliestTimestamp
    return delta.days;

"""This function creates 1 day based on its shape (number of time slots) and immediately fills in:
    whether it are slots for urgent or elective patients
    begin and end times of each slot
    """
    
def Createday(shape):
    day = pd.DataFrame(np.zeros(shape))
    day.index +=1                               #Set start index to 1 instead of 0 --> indicated number of timeslot
    day.columns = ["Begin", 
                   "End",  
                   "Type of patient",           #0 = Elective, 1 = Urgent
                   "Taken",                     #0 = Not taken, 1 = Taken = a patient is scheduled in this timeslot
                   "Show up",                   #0 = Patient did not show up, 1 = Show up
                   "Phone call time",           
                   "Appointment waiting time", 
                   "Arrival time", 
                   "Scan waiting time", 
                   "Scan start time", 
                   "Service time", 
                   "Departure time",
                   "Type of scan"]
    if(shape[0]==lengthFullday):                
        for i in range(len(rAM)):               #Fill in begin and end times of each timeslot for full days
            day.iloc[i,0] = startHourAM + pd.to_timedelta(rAM[i], unit='m')
            day.iloc[i,1] = startHourAM + pd.to_timedelta(rAM[i]+15, unit='m') 
        for i in range(len(rPM)):
            day.iloc[i+len(rAM),0] = startHourPM + pd.to_timedelta(rPM[i], unit='m')
            day.iloc[i+len(rAM),1] = startHourPM + pd.to_timedelta(rPM[i]+15, unit='m')
        
        for i in (14, 15):                      #Fill in urgent timeslots in morning
            day.iloc[i,2] = 1
        for i in range(31, 40):                      #Fill in urgent timeslots in afternoon
            day.iloc[i,2] = 1
        
    if(shape[0]==lengthHalfday):                
        for i in range(len(rHalfDay)):          #Fill in begin and end times of each timeslot for half days
            day.iloc[i,0] = startHourAM + pd.to_timedelta(rHalfDay[i], unit='m')
            day.iloc[i,1] = startHourAM + pd.to_timedelta(rHalfDay[i]+15, unit='m')
        
        for i in range(15, 24):                      #Fill in urgent timeslots
            day.iloc[i,2] = 1
    return day;

def checkDay(day):
    for rij in range(0, len(day)):
            if(rij!=0):
                if(day.iloc[rij, 3] == 1 and day.iloc[rij, 4] == 1 and day.iloc[rij-1, 11]!=0 and day.iloc[rij, 9] < day.iloc[rij-1, 11]):
                    day.iloc[rij, 9] = day.iloc[rij-1, 11]
                    day.iloc[rij, 11] = day.iloc[rij, 9] + day.iloc[rij, 10]
                    day.iloc[rij, 8] = day.iloc[rij, 9] - day.iloc[rij, 7];

#################################################################
###################Initialization################################
#################################################################
def init():
    """make sure all variables in initialization are available globally, not locally"""
    global maxWeeks, maxDays, startDate, infinity,endDate, t, tp, tae, tau, td, number_of_phone_calls, number_of_urgent_arrivals
    global lengthFullday, lengthHalfday, shapeMonday, shapeTuesday, shapeWednesday, shapeThursday, shapeFriday, shapeSaturday, shapeSunday
    global startHourAM, startHourPM, rAM, rPM, rHalfDay
    global weekNames, scheduleNames, schedule, rangeMondays, rangeTuesdays, rangeWednesdays, rangeThursdays, rangeFridays, rangeSaturdays, rangeSundays
    global scanMeans, scanStd, scanNames
    global doctorFree, queue, waitingRoom, taeAssigned 
    global endFullday, endHalfday
    global endTimesPerDay, lengthPerDay , endTimesPerDayForOvertime
    global tdAssigned
    global max_queue, max_waitingRoom
    """set arbitrary limit of simulation"""
    maxWeeks = 400                                   
    maxDays = maxWeeks*7
    
    """Declare system time, first phone call, first urgent arrival
     set first elective arrival and first departure to infinity"""
    startDate = pd.Timestamp(year=2019, month=1, day=1, hour=8, minute = 00, second = 00)     #Start hour of system initialized as opening hour of first day 
    infinity = pd.Timestamp(year=2100, month=1, day=1, hour=8, minute = 00, second = 00)        #Set
    endDate = startDate + pd.to_timedelta(maxDays-7, unit = "D")

    t = startDate
    tp =  startDate + pd.to_timedelta(transformToInterarrivalTimeWholeDay(np.random.exponential(scale = 1/28.345)), unit = 's')       #generate first phone call time
    tae = infinity                                #arrival time elective patient
    tau =  startDate + pd.to_timedelta(transformToInterarrivalTimeWholeDay(np.random.exponential(scale = 1/2.5)), unit = 's')     #generate first urgent arrival
                                                            #scale = Beta = 1/lambda
                                                            #lambda = 2.5 if whole day open
                                                            #lambda = 1.25 is half a day open
    td =  infinity                                  #departure time
    
    number_of_phone_calls = 0
    number_of_urgent_arrivals = 0
    doctorFree = 1
    queue = 0
    waitingRoom = 0
    taeAssigned=0
    tdAssigned=0
    max_queue = 0
    max_waitingRoom = 0
    ###############################################################
    ###Create schedule according to current appointment schedule###
    ###############################################################
    
    """Initialize shapes of each day a.k.a. how many time slots each day has"""
    lengthFullday = 40                              #32 regular slots + 8 urgent slots
    lengthHalfday = 24                              #16 regular slots + 8 urgent slots
    shapeMonday = (lengthFullday, 13)                          
    shapeTuesday = (lengthFullday, 13) 
    shapeWednesday = (lengthFullday, 13) 
    shapeThursday = (lengthHalfday, 13)                        
    shapeFriday = (lengthFullday, 13) 
    shapeSaturday = (lengthHalfday, 13)   
    shapeSunday = (1, 13)                           #all day closed --> shall be skipped in all occasions
    
    """Initialize start hour in morning and afternoon"""
    startHourAM = pd.Timestamp(year=2019, month=1, day=1, hour=8, minute = 00, second = 00)  #Start hour in morning
    startHourPM = pd.Timestamp(year=2019, month=1, day=1, hour=13, minute = 00, second = 00) #Start hour in afternoon
    endFullday = pd.Timestamp(year=2019, month=1, day=1, hour=17, minute = 00, second = 00)
    endHalfday =  pd.Timestamp(year=2019, month=1, day=1, hour=13, minute = 00, second = 00)
    """Used in Createday function"""
    rAM = range(0, 16*15, 15)
    rPM = range(0, 24*15, 15)
    rHalfDay = range(0, lengthHalfday*15, 15)
    
    "Create whole schedule, based on maximum number of weeks arbitrarily set in beginning"""            
    weekNames = list(("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"))
    scheduleNames = maxWeeks * weekNames.copy()       #contains the names of the day, use this to check whether a day in the Schedule is a Monday, Tuesday, ...
    
    
    schedule = [None]*maxDays                         #create empty schedule with number of days = maxDays
    
    rangeMondays = range(0, maxDays, 7)               #define ranges with which index is which day
    rangeTuesdays = range(1, maxDays, 7)
    rangeWednesdays = range(2, maxDays, 7)
    rangeThursdays = range(3, maxDays, 7)
    rangeFridays = range(4, maxDays, 7)
    rangeSaturdays = range(5, maxDays, 7)
    rangeSundays = range(6, maxDays, 7)
    
    for i in range(0, maxDays):                     #fill whole schedule with days
        if i in rangeMondays:
            schedule[i] = Createday(shapeMonday)
        if i in rangeTuesdays:
            schedule[i] = Createday(shapeTuesday)
        if i in rangeWednesdays:
            schedule[i] = Createday(shapeWednesday)
        if i in rangeThursdays:
            schedule[i] = Createday(shapeThursday)
        if i in rangeFridays:
            schedule[i] = Createday(shapeFriday)
        if i in rangeSaturdays:
            schedule[i] = Createday(shapeSaturday)
        if i in rangeSundays:
            schedule[i] = Createday(shapeSunday)
    
    for j in range(len(schedule)):                  #adjust dates
        if j not in range(6, maxDays, 7):
            day = schedule[j]
            for i in range(0, day.shape[0]):
                day.iloc[i, 0] = day.iloc[i, 0] +  pd.to_timedelta(j, unit='D')
                day.iloc[i, 1] = day.iloc[i, 1] +  pd.to_timedelta(j, unit='D')
    
    scanMeans = {
            1: 15,
            2 : 17.5,
            3 : 22.5,
            4 : 30,
            5 : 30
            }      
    scanNames = {
                1: "Brain",
                2 : "Lumbar vertebrae",
                3 : "Cervical vertebrae",
                4 : "Abdomen Ml",
                5 : "Other"
                }                                                               #1 = Brain
                                                                                #2 = Lumbar vert
                                                                                #3 = Cervical vert
                                                                                #4 = Abdomen Ml  
                                                                                #5 = Other
    scanStd = {
            1: 2.5,
            2 : 1,
            3 : 2.5,
            4 : 1,
            5 : 4.5
            }
    
    

    endTimesPerDay = {}
    lengthPerDay = {}
    endTimesPerDayForOvertime  = {}
    for i in range(0, maxDays):                                                  #save the endTimePerday (set to an extreme 21h for a full day or 17h for a half day) and the specific length (number of timeslots) per day
        if i in rangeMondays or i in rangeTuesdays or i in rangeWednesdays or i in rangeFridays:
            endTimesPerDay[i] = pd.Timestamp(year = 2019, month = 1, day = 1, hour = 21, minute = 00, second = 00) + pd.to_timedelta(i, unit = "D")
            endTimesPerDayForOvertime[i] = pd.Timestamp(year = 2019, month = 1, day = 1, hour = 17, minute = 00, second = 00) + pd.to_timedelta(i, unit = "D")
            lengthPerDay[i] = lengthFullday
        elif i in rangeThursdays or i in rangeSaturdays:
            endTimesPerDay[i] = pd.Timestamp(year = 2019, month = 1, day = 1, hour = 17, minute = 00, second = 00) + pd.to_timedelta(i, unit = "D")
            endTimesPerDayForOvertime[i] = pd.Timestamp(year = 2019, month = 1, day = 1, hour = 12, minute = 00, second = 00) + pd.to_timedelta(i, unit = "D")
            lengthPerDay[i] = lengthHalfday;

##################################################################
###################Event Phone call################################
##################################################################
def findFreeTimeslotElectivePatient(day, tp):
    for i in range(0, len(day)):
        if(day.iloc[i,0]> tp and day.iloc[i,2]==0 and day.iloc[i,3]==0):
            return i
            break;   

def handle_phone_event():
    global number_of_phone_calls
    number_of_phone_calls += 1
    global tp
    global t
    global tae, queue, doctorFree, taeAssigned
    t = tp
    verschil = calcDifferenceInDays(startDate, tp)
    slot_found = False

    #search free slot after tp       
    while slot_found == False:
        for i in range(verschil, len(schedule)):   #moet toch gewoon len(schedule) zijn ipv len(schedule)-verschil?
            day = i
            if i not in rangeSundays:                                       #zondagen niet checken op beschikbaar slot
                slot = findFreeTimeslotElectivePatient(schedule[i], tp)    #hier stond schedule[i+verschil] ipv schedule[i] --> als je op dag 8 wou beginnen zoeken, zocht ie naar een tijdslot op dag 8+8 (aangezien in eerste loop i gelijk is aan verschil)
                if slot is not None:
                    slot_found = True
                    break;
    
    #Calculate appointment waiting time and arrival time of elective patient
    #Put it in the slot 
    schedule[day].iloc[slot,3] = 1                                              #set slot to taken                                            
    schedule[day].iloc[slot,5] = tp                                             #set phone call time
    delay = pd.to_timedelta(np.random.normal(0,2.5), unit = "m")
    if(schedule[day].iloc[slot,0] + delay < tp):                                                           #set arrival time using a certain delay (<0, 0 or >0).  If patient too early, it could happen that begin slot - too early < tp -->  Assumption:  if this happens, we transform the time the patient is too early (e.g. 3 mins) into 3 mins. late 
        schedule[day].iloc[slot, 7] = schedule[day].iloc[slot,0] - delay
    elif(delay.days==-1 and slot==0):
        schedule[day].iloc[slot, 7] = schedule[day].iloc[slot,0] - delay
    else:
        schedule[day].iloc[slot, 7] = schedule[day].iloc[slot,0] + delay
        
    schedule[day].iloc[slot,6] =  schedule[day].iloc[slot,7] - schedule[day].iloc[slot,5]                   #set appointment waiting time = arrival time - tp
    
    print("DAGGGGGGG", day)
    print("SLOTTTTTT", slot)
    if(taeAssigned==0):                                                           #if doctor is free, then tae was set to infinity, so we have to overwrite this
        tae = schedule[day].iloc[slot, 7]
        taeAssigned=1
        
    #Calculate a new phone call 
    tp = t + pd.to_timedelta(transformToInterarrivalTimeWholeDay(np.random.exponential(scale = 1/28.345)), unit = 's')

    closingHour = pd.Timestamp(year = tp.year, month = tp.month, day = tp.day, hour = 17, minute = 00, second = 00)                 #calculate Timestamp with closing hour of the specific day we're on
    if(tp>=closingHour):                                                                                                            #if tp>17h, then adjust it to the opening hours of the next day
        friday = False
        if(scheduleNames[calcDifferenceInDays(pd.Timestamp(year=2019, month=1, day=1, hour=17, minute = 00, second = 00), tp)]=="Friday"):  #check whether today is a Friday or not
            friday = True
        tp = tp - pd.to_timedelta(9, unit = 'h')                                                                                    #substract 9 hours (17h-8h = 9h difference)
        if(friday):                                                                                                                 #if it's a Friday, go to Monday (+3:   Fri to Sa = +1, Fri to Su = +2, Fri to Mo = +3) 
            tp = tp + pd.to_timedelta(3, unit = 'D')
        else:                                                                                                                       #else, simply go to the next day (+1)
            tp = tp + pd.to_timedelta(1, unit = 'D');

#######################################################################
###################Event Urgent Arrival################################
#######################################################################
def findFreeTimeslotUrgentPatient(day, tau):
    for i in range(0,len(day)):
        if(day.iloc[i,0]>tau and day.iloc[i,3]==0):         #begintime larger than tau , slot not taken yet
            return i
            break;
        
def generateServiceTimeUrgent():
    scantype = [1, 2, 3, 4, 5]                                                  #1 = Brain
                                                                                #2 = Lumbar vert
                                                                                #3 = Cervical vert
                                                                                #4 = Abdomen Ml                                                                            
                                                                                #5 = Other
    weights = [0.7, 0.1, 0.1, 0.05, 0.05]
    scan = random.choices(scantype, weights)
    scanName = scanNames[scan[0]]
    serviceTime= np.random.normal(scanMeans[scan[0]], scanStd[scan[0]])
    serviceTime = pd.to_timedelta(serviceTime, unit='m')
    return scanName, serviceTime;

def time_in_range(start, end, x):
    """Return true if x is in the range [start, end]"""
    if start < end:
        return start <= x < end
    else:
        return start <= x or x < end;
    
def UrgentArrival():
    global tau, t, number_of_urgent_arrivals, queue, doctorFree, td, tdAssigned, waitingRoom, max_queue, max_waitingRoom
    number_of_urgent_arrivals+=1
    queue+=1
    waitingRoom = queue-1
    if queue>max_queue:
        max_queue = queue
    if waitingRoom>max_waitingRoom:
        max_waitingRoom = waitingRoom
    t = tau
    numberOfDayInSimulation = calcDifferenceInDays(startDate, t)
    day = schedule[numberOfDayInSimulation]
    indexOfTimeslot = findFreeTimeslotUrgentPatient(day, tau)
    day.iloc[indexOfTimeslot, 3] = 1              #set slot to Taken
    day.iloc[indexOfTimeslot, 2] = 1              #urgent patient --> if slot already for urgent, this doesn't change anything, if it originally was for elective patients, this changes
    day.iloc[indexOfTimeslot, 4] = 1              #Patient showed up (cause urgent), all urgents show up
    day.iloc[indexOfTimeslot, 7] = t              #set arrival time
    day.iloc[indexOfTimeslot, 12], day.iloc[indexOfTimeslot, 10] = generateServiceTimeUrgent()   #generate service time
    if(doctorFree == 1 or doctorFree==0):                                                        #if doctor is free, immediately treat patients, else, add to queue
        doctorFree = 0
        day.iloc[indexOfTimeslot,9] = day.iloc[indexOfTimeslot,0]                             #if doctor is free, scan start time = begin slot
        day.iloc[indexOfTimeslot,11] = day.iloc[indexOfTimeslot,9] + day.iloc[indexOfTimeslot,10]             #if doctor free, departure time can immediately be calculated:  departure time = scan start time + service time
        if(tdAssigned==0 and day.iloc[indexOfTimeslot,11]<td):
            td = day.iloc[indexOfTimeslot,11]
            tdAssigned=1
        if(tae<=day.iloc[indexOfTimeslot,0]):
            doctorFree=1

    """generate next urgent arrival time tau"""         #scale = Beta = 1/lambda
                                                        #lambda = 2.5 if whole day open
                                                        #lambda = 1.25 is half a day open                                                                          
    
    timeOK=False                                                  
    firstCheck=True                                                    
    while(timeOK==False):
        d = scheduleNames[calcDifferenceInDays(pd.Timestamp(year=2019, month=1, day=1, hour=8, minute = 00, second = 00), tau)]
        if (d in ("Monday", "Tuesday", "Wednesday", "Friday")):
            if(firstCheck):
                tau =  t + pd.to_timedelta(transformToInterarrivalTimeWholeDay(np.random.exponential(scale = 1/2.5)), unit = 's')     #generate first urgent arrival                        
                year=t.year
                month= t.month
                day= t.day
                begin=pd.Timestamp(year=year, month=month, day=day, hour=8, minute = 00, second = 00)
                end= pd.Timestamp(year=year, month=month, day=day, hour=17, minute = 00, second = 00)
                firstCheck=False
            #check if the time is in the opening houres of the hospital
            else:
                year=tau.year
                month= tau.month
                day= tau.day
                begin=pd.Timestamp(year=year, month=month, day=day, hour=8, minute = 00, second = 00)
                end= pd.Timestamp(year=year, month=month, day=day, hour=17, minute = 00, second = 00)
            if(begin<=tau<end):
                timeOK=True
            elif(begin>tau):
                tau =  tau + pd.to_timedelta(transformToInterarrivalTimeWholeDay(np.random.exponential(scale = 1/2.5)), unit = 's')
            else:
                tau = tau - pd.to_timedelta(9, unit = 'h') + pd.to_timedelta(1, unit = 'D')
        if (d == "Thursday"):
            if(firstCheck):
                tau =  t + pd.to_timedelta(transformToInterarrivalTimeHalfDay(np.random.exponential(scale = 1/1.25)), unit = 's')     #generate first urgent arrival                        
                year=t.year
                month= t.month
                day= t.day
                begin=pd.Timestamp(year=year, month=month, day=day, hour=8, minute = 00, second = 00)
                end= pd.Timestamp(year=year, month=month, day=day, hour=12, minute = 00, second = 00)
                firstCheck=False
            #check if the time is in the opening houres of the hospital
            else:
                year=tau.year
                month= tau.month
                day= tau.day
                begin=pd.Timestamp(year=year, month=month, day=day, hour=8, minute = 00, second = 00)
                end= pd.Timestamp(year=year, month=month, day=day, hour=12, minute = 00, second = 00)
            if(begin<=tau<end):
                timeOK=True
            elif(begin>tau):
                tau =  tau + pd.to_timedelta(transformToInterarrivalTimeHalfDay(np.random.exponential(scale = 1/1.25)), unit = 's')
            else:
                tau = tau - pd.to_timedelta(4, unit = 'h') + pd.to_timedelta(1, unit = 'D')
        if (d == "Saturday"):
            if(firstCheck):
                tau =  t + pd.to_timedelta(transformToInterarrivalTimeHalfDay(np.random.exponential(scale = 1/1.25)), unit = 's')     #generate first urgent arrival                        
                year=t.year
                month= t.month
                day= t.day
                begin=pd.Timestamp(year=year, month=month, day=day, hour=8, minute = 00, second = 00)
                end= pd.Timestamp(year=year, month=month, day=day, hour=12, minute = 00, second = 00)
                firstCheck=False
            #check if the time is in the opening houres of the hospital
            else:
                year=tau.year
                month= tau.month
                day= tau.day
                begin=pd.Timestamp(year=year, month=month, day=day, hour=8, minute = 00, second = 00)
                end= pd.Timestamp(year=year, month=month, day=day, hour=12, minute = 00, second = 00)
            if(begin<=tau<end):
                timeOK=True
            elif(begin>tau):
                tau =  tau + pd.to_timedelta(transformToInterarrivalTimeHalfDay(np.random.exponential(scale = 1/1.25)), unit = 's')
            else:
                tau = tau - pd.to_timedelta(4, unit = 'h') + pd.to_timedelta(2, unit = 'D');
        if (d == "Sunday"):
            tau = tau + pd.to_timedelta(1, unit = 'D')
    
############################
###Elective Arrival Event###
############################  

def arrivalElectiveEvent():
    global t, tae, doctorFree, queue, td, taeAssigned, tdAssigned, waitingRoom, max_queue, max_waitingRoom
    "Increment simulation time"
    t = tae
    "Bepaal dag"
    zoveelsteDag = calcDifferenceInDays(startDate, tae);                            #check which day it is in schedule
    day = schedule[zoveelsteDag]                                                    #extract this day (dataframe) from schedule
    queue+=1
    waitingRoom = queue-1
    "Bepaal bij welke patient (time slot) de arrival hoort en kijk of patient een elective is"
    nextElectiveFound = 0
    rand = 0
    for i in range(0, day.shape[0]):                                                #loop through timeslots on this day
        if(day.iloc[i,7] == t):                                                     #find timeslots with this arrival time
            if(day.iloc[i,2] == 0 and day.iloc[i,3]==1 and nextElectiveFound == 0): #Kijk of het elective is en taken
                nextElectiveFound = 1
                rand = random.uniform(0, 1)                                         #generate a random number between 0 and 1
                if(rand < 0.98):                                                    #98% chance that elective patient shows up
                    day.iloc[i,4] = 1                                               #set patient showed up
                    day.iloc[i,10] = pd.to_timedelta(np.random.normal(loc=15.0, scale=3.0), unit = 'm')      #generate service time = Normal distribution with mean 15 and standard deviation 3           
                    if(doctorFree == 1 or doctorFree==0):                                            #if doctor is free, immediately treat patients, else, add to queue
                        doctorFree = 0
                        if(day.iloc[i,0]<=t):                                        #if begin slot < arrival --> patient too late --> treat immediately --> scan start time = arrival time
                            day.iloc[i,9] = t                                           
                        else:                                                       #else, set scan start time = begin slot
                            day.iloc[i,9] = day.iloc[i,0] 
                        if(day.iloc[i,9]>day.iloc[i,7]):          #Voor de scan waiting times: checken of start scan time groter is dan arrival time
                            day.iloc[i,8] = day.iloc[i,9] - day.iloc[i,7] 
                        else:                                                             #als scanner heeft moeten wachten op patient --> wait voor patient = 0
                            day.iloc[i,8] = 0   
                        day.iloc[i,11] = day.iloc[i,9] + day.iloc[i,10]             #if doctor free, departure time can immediately be calculated:  departure time = scan start time + service time
                        if(day.iloc[i,11]<=td or tdAssigned==0):
                            td = day.iloc[i,11]
                            tdAssigned=1
                else:
                    queue-=1
                    if(queue==0):
                        waitingRoom = 0
                    else:
                        waitingRoom = queue-1
                    day.iloc[i,4] = 0                                              #if no show (2% probability aka rand>0.98)
            break
    
    if queue>max_queue:
        max_queue = queue
    if waitingRoom>max_waitingRoom:
        max_waitingRoom = waitingRoom
    
    "Genereer next arrival time elective"
    nextScheduledPatientFound = 0
    if(i<day.shape[0]-1):                                                           #only do this for loop which searches for the next scheduled patient this day if we're not yet in the last timeslot
        for j in range(i + 1, day.shape[0]):
            if(day.iloc[j,3] == 1 and day.iloc[j,2] == 0 and nextScheduledPatientFound == 0):  #We mogen enkel de eerstvolgende patient beschouwen: if taken and elective patient
                nextScheduledPatientFound = 1
                tae = day.iloc[j,7]

    if(nextScheduledPatientFound==0):                                               #if no other elective patient found in this day, the next elective arrival time = infinity
        tae = infinity
        taeAssigned=0;
     
#####################
###Departure Event###
#####################
def departureEvent():
    global t, queue, td,  doctorFree, tdAssigned, waitingRoom
    """nextDayDeparture,"""
    "Increment simulation time"
    t = td
    queue -=1                                                                   #departure --> delete 1 from queue
    if(queue==0):
        doctorFree=1
        waitingRoom=0
    else:
        waitingRoom = queue-1
    
    
    "Bepaal dag"
    zoveelsteDag = calcDifferenceInDays(startDate, td)                          #Kijken hoeveel dagen we verder zijn
                                                                                #Vb: 5 jan - 1 jan = 4 dagen -> zoeken in schedule[4] 
    day = schedule[zoveelsteDag]
    
    "Bepaal bij welke patient (time slot) de departure hoort"
    for i in range(0, day.shape[0]):
        if(day.iloc[i,11] == td):
            row = i
            break
    
    "Scan start times invullen"
    nextScheduledPatientFound = 0
    if(row<day.shape[0]-1):                                                         #only do this for loop which searches for the next scheduled patient this day if we're not yet in the last timeslot
        for j in range(row+1, day.shape[0]):                                            #Is nodig want het kan zijn dat het volgende slot niet taken is           
            if((day.iloc[j,3] == 1 and day.iloc[j,4] == 1 and nextScheduledPatientFound == 0)):                  #We mogen enkel de eerstvolgende patient beschouwen waarvan slot Taken EN Show up
                nextScheduledPatientFound = 1
                print(nextScheduledPatientFound)
                if(td>day.iloc[j,0]):                   #if departure time(i)>begin slot(i+1)          day.iloc[i+1][0] genereert het begin van het volgende ingenomen tijdsslot, difference zal negatief zijn als departure time > next scheduled 
                    if(t > day.iloc[j,7]):                  #if departure time(i) > arrival time(i+1)     departure time is later dan de arrival time (ie, ook de patient was te laat, maar de departure was later)
                        day.iloc[j,9] = td                                                   #scan start time(i+1) = departure time(i)   
                    else:
                        day.iloc[j,9] = day.iloc[j, 7]                                 #else: scan start time(i+1) = arrival time(i+1)   De volgende patient start op de departure van de vorige
                else:                                                               #else if departure time<=begin slot(i+1)
                    if(day.iloc[j,7]>day.iloc[j,0]):      #if arrival time (i+1) > begin slot(i+1)     In deze case is er geen vertraging, maar de patient komt te laat
                        day.iloc[j,9] = day.iloc[j,7]                                     #scan start time = arrival time
                    else:                                                               #else if arrival time(i+1) <= begin slot(i+1)
                        day.iloc[j,9] = day.iloc[j,0]                                     #scan start time(i+1) = begin slot(i+1)      in deze case was de departure voor het volgende tijdsslot en kwam de patient op tijd
                if(day.iloc[j,9]>day.iloc[j,7]):          #Voor de scan waiting times: checken of start scan time groter is dan arrival time
                    day.iloc[j,8] = day.iloc[j,9] - day.iloc[j,7] 
                else:                                                             #als scanner heeft moeten wachten op patient --> wait voor patient = 0
                    day.iloc[j,8] = 0   
                day.iloc[j,11] = day.iloc[j,9] + day.iloc[j,10]                                   #bepaalt de volgende departure time afh van de zonet bepaalde scan start time + service time
                td = day.iloc[j,11] = day.iloc[j,9] + day.iloc[j,10]                #overwrite next departure time
                tdAssigned=1
                break   
                  
            
    "Einde van de dag bepalen"
    if(nextScheduledPatientFound==0):                                           #Wanneer er geen volgende patienten meer gepland zijn/, dan zetten we td op infinity               
        td = infinity
        tdAssigned=0;
    
######
#Main#
######
        
def initializeStatistics():
    global statistics 
    statistics = pd.DataFrame(np.zeros((maxDays, 22))) 
                                 
    statistics.columns = ["#urgents", 
                   "#electives",  
                   "#phone calls",         
                   "#noshows",                     
                   "max queue",                 
                   "min service time elective",           
                   "max service time elective", 
                   "mean service time elective", 
                   "min service time urgent",
                   "max service time urgent", 
                   "mean service time urgent", 
                   "min appointment waiting time elective",           
                   "max appointment waiting time elective", 
                   "mean appointment waiting time elective",
                   "overtime", # to do
                   "max waiting room",
                   "min scan waiting time elective",           
                   "max scan waiting time elective", 
                   "mean scan waiting time elective",
                   "min scan waiting time urgent",           
                   "max scan waiting time urgent", 
                   "mean scan waiting time urgent"
                   ]
    
def calculateStatistics(day) :
    urgents=0
    electives=0
    minServicetimeElective =10000000000000000
    maxServicetimeElective=0
    sumServicetimeElective=0
    minServicetimeUrgent =10000000000000000
    maxServicetimeUrgent=0
    sumServicetimeUrgent=0
    minAppointmWaitingtimeElective =10000000000000000
    maxAppointmWaitingtimeElective=0
    sumAppointmWaitingtimeElective=0
    minScanWaitingtimeElective =10000000000000000
    maxScanWaitingtimeElective=0
    sumScanWaitingtimeElective=0
    minScanWaitingtimeUrgent =10000000000000000
    maxScanWaitingtimeUrgent=0
    sumScanWaitingtimeUrgent=0
    noshows=0
    
    for i in range(0, len(schedule[day])):
         if schedule[day].iloc[i,2]==0 and schedule[day].iloc[i,3]==1 and schedule[day].iloc[i,6] !=0 and schedule[day].iloc[i,10] !=0 :  # aantal electives
             electives+=1
             if minServicetimeElective > schedule[day].iloc[i,10].total_seconds():
                 minServicetimeElective= schedule[day].iloc[i,10].total_seconds()
             if maxServicetimeElective < schedule[day].iloc[i,10].total_seconds():
                 maxServicetimeElective  = schedule[day].iloc[i,10].total_seconds()
             sumServicetimeElective+= schedule[day].iloc[i,10].total_seconds()
             if minAppointmWaitingtimeElective > schedule[day].iloc[i,6].total_seconds():
                 minAppointmWaitingtimeElective= schedule[day].iloc[i,6].total_seconds()
             if maxAppointmWaitingtimeElective < schedule[day].iloc[i,6].total_seconds():
                 maxAppointmWaitingtimeElective = schedule[day].iloc[i,6].total_seconds()
             sumAppointmWaitingtimeElective += schedule[day].iloc[i,6].total_seconds()
             if schedule[day].iloc[i,8]==0:
                 minScanWaitingtimeElective = 0
             elif minScanWaitingtimeElective > schedule[day].iloc[i,8].total_seconds():
                 minScanWaitingtimeElective = schedule[day].iloc[i,8].total_seconds()
             if schedule[day].iloc[i,8]!=0:
                 if maxScanWaitingtimeElective < schedule[day].iloc[i,8].total_seconds():
                     maxScanWaitingtimeElective = schedule[day].iloc[i,8].total_seconds()
             if schedule[day].iloc[i,8]==0:
                 sumScanWaitingtimeElective += 0
             else:
                 sumScanWaitingtimeElective += schedule[day].iloc[i,8].total_seconds()

         elif schedule[day].iloc[i,2]==1 and schedule[day].iloc[i,3]==1:
            urgents+=1
            if minServicetimeUrgent > schedule[day].iloc[i,10].total_seconds():
                 minServicetimeUrgent= schedule[day].iloc[i,10].total_seconds()
            if maxServicetimeUrgent < schedule[day].iloc[i,10].total_seconds():
                 maxServicetimeUrgent = schedule[day].iloc[i,10].total_seconds()
            sumServicetimeUrgent+= schedule[day].iloc[i,10].total_seconds()
            if schedule[day].iloc[i,8]==0:
                 minScanWaitingtimeUrgent = 0
            elif minScanWaitingtimeUrgent > schedule[day].iloc[i,8].total_seconds():
                 minScanWaitingtimeUrgent = schedule[day].iloc[i,8].total_seconds()
            if schedule[day].iloc[i,8]!=0:
                if maxScanWaitingtimeUrgent < schedule[day].iloc[i,8].total_seconds():
                    maxScanWaitingtimeUrgent = schedule[day].iloc[i,8].total_seconds()
            if schedule[day].iloc[i,8]==0:
                 sumScanWaitingtimeUrgent += 0
            else:
                 sumScanWaitingtimeUrgent += schedule[day].iloc[i,8].total_seconds()
         if schedule[day].iloc[i,4]==0 and schedule[day].iloc[i,3]==1:
             noshows+=1
         if (schedule[day].iloc[i,11]!=0):
            lastDeparture = schedule[day].iloc[i,11]
            OT = lastDeparture - endTimesPerDayForOvertime[day]
            statistics.iloc[day,14] = OT.total_seconds()
    
    statistics.iloc[day,0] = urgents
    statistics.iloc[day,1] = electives
    statistics.iloc[day,2] = number_of_phone_calls
    statistics.iloc[day,3] = noshows
    statistics.iloc[day,4] = max_queue
    statistics.iloc[day,5] = minServicetimeElective
    statistics.iloc[day,6] = maxServicetimeElective
    statistics.iloc[day,15] = max_waitingRoom
    statistics.iloc[day,16] = minScanWaitingtimeElective
    statistics.iloc[day,17] = maxScanWaitingtimeElective
    
    if electives==0:
        statistics.iloc[day,7]="NA"
    else:
        statistics.iloc[day,7]= sumServicetimeElective / electives
        statistics.iloc[day,18]= sumScanWaitingtimeElective / electives
        
    statistics.iloc[day,8]= minServicetimeUrgent
    statistics.iloc[day,9]= maxServicetimeUrgent
    
    statistics.iloc[day,19]= minScanWaitingtimeUrgent
    statistics.iloc[day,20]= maxScanWaitingtimeUrgent
    
    if urgents==0:
        statistics.iloc[day,10]="NA"
        statistics.iloc[day,8]="NA"
        statistics.iloc[day,9]= "NA"
        statistics.iloc[day,19]="NA"
        statistics.iloc[day,20]= "NA"
        statistics.iloc[day,21]= "NA"
    else:
        statistics.iloc[day,10]= sumServicetimeUrgent / urgents
        statistics.iloc[day,21]= sumScanWaitingtimeUrgent / urgents
    statistics.iloc[day,11]= minAppointmWaitingtimeElective
    statistics.iloc[day,12]= maxAppointmWaitingtimeElective
    
    if electives==0:
        statistics.iloc[day,11]= "NA"
        statistics.iloc[day,12]= "NA"
        statistics.iloc[day,13]= "NA"
        statistics.iloc[day,5]= "NA"
        statistics.iloc[day,6]= "NA"
        statistics.iloc[day,7]= "NA"
        statistics.iloc[day,16]= "NA"
        statistics.iloc[day,17]= "NA"
        statistics.iloc[day,18]= "NA"
    else:
        statistics.iloc[day,13]= sumAppointmWaitingtimeElective / electives
        
        
def main(end):
    global tp, tau, tae, td, queue, numberOfDay, numberOfPhoneCalls, number_of_phone_calls, numberOfUrgents, numberOfElectives, numberOfDepartures
    global waitingRoom, max_queue, max_waitingRoom, taeAssigned
    numberOfDay = 0
    numberOfPhoneCalls = 0
    numberOfUrgents = 0
    numberOfElectives = 0
    numberOfDepartures = 0
            
    while(tp < end and tau<end):    
        if(tae>endTimesPerDay[numberOfDay] and tp>endTimesPerDay[numberOfDay] and td>endTimesPerDay[numberOfDay] and tau>endTimesPerDay[numberOfDay]):
            queue=0
            waitingRoom=0
            checkDay(schedule[numberOfDay])    
            calculateStatistics(numberOfDay)
            number_of_phone_calls = 0
            max_queue = 0
            max_waitingRoom = 0
            if numberOfDay in rangeMondays or numberOfDay in rangeTuesdays or numberOfDay in rangeWednesdays or numberOfDay in rangeThursdays or numberOfDay in rangeFridays:
                numberOfDay=numberOfDay+1
            elif numberOfDay in rangeSaturdays:                                               #check for next tae on Monday --> numberOfDay+2
                numberOfDay=numberOfDay+2
            day = schedule[numberOfDay]
            for i in range(0, lengthPerDay[numberOfDay]):
                if(day.iloc[i, 2]==0 and day.iloc[i, 3]==1):
                    tae = day.iloc[i, 7]
                    taeAssigned=1
                    break
            
        if(queue==0):
            waitingRoom = 0
        else:
            waitingRoom = queue-1
            
        if(tp<=tau and tp<=tae and tp<=td):
            handle_phone_event()
            numberOfPhoneCalls+=1
            print("phone")
        elif(tau<=tae and tau<=td):
            UrgentArrival()
            numberOfUrgents+=1
            print("urgent")
        elif(tae<=td):
            arrivalElectiveEvent()
            numberOfElectives+=1
            print("elective")
        else:
            departureEvent()
            numberOfDepartures+=1
            print("departure")
            print("queue", queue)
            print("waitingRoom", waitingRoom)
            print("doctorFree", doctorFree)
            print("taeAssigned", taeAssigned)
            print("tp", tp)
            print("tau", tau)
            print("tae", tae)
            print("td", td);

#end = pd.Timestamp(year=2019, month=5, day=10, hour=8, minute = 00, second = 00)
         
#######################
#Perform multiple runs#
#######################

numberOfRuns = 20
path = r"E:\Allerlei\Sander\Andere\School\Universiteit\Master\Datagestuurde & Robuuste besliskunde\Project_assignment\statistics_Current_System_Multiple_Runs.xlsx"
writer = pd.ExcelWriter(path, engine='xlsxwriter')
for i in range(1,numberOfRuns+1):
    print(i)
    init()
    initializeStatistics()
    main(endDate)  
    statistics.to_excel(writer, sheet_name = "Run" + str(i))
writer.save()
