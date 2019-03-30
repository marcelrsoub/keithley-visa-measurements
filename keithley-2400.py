import visa
import numpy as np
import matplotlib.pyplot as plt
from tkinter import Button, Tk, Frame, Entry, Label, StringVar #, Checkbutton, BooleanVar
import time
#--------------------------------------------------------------------------
def connection_choice(connection):
    """enables the user to choose the connection"""
    global keithley
    try:
        rm = visa.ResourceManager() #import visa
        rm.list_resources() #import visa    
        keithley = rm.open_resource(connection, send_end=True, read_termination='\r') #creat device connection
        print("connection succeed")
    except:
        raise StopIteration ("Error. Verify the connection (GPIB,RS232,USB,Ethernet) and its identifier")
#--------------------------------------------------------------------------
def close_all():
    """Close the connection"""
    reset() #reset smu
    try:
        keithley.write(":SYSTem:BEEPer:STATe 0") #deactivate beep
        keithley.close() #close the connection
        print("connection closed")
    except:
        raise StopIteration ("Closing error, connection still open")
#--------------------------------------------------------------------------        
def reset():
    """reset smu"""
    try:
        keithley.write("*RST\r")
        print("instrument reset")           
    except:
        raise StopIteration ("Reset error")
#--------------------------------------------------------------------------    
def switchON(onoff=False):
    """Turn on/off the smu"""
    try:
        keithley.write((":outp:state 1" if onoff else ":outp:state 0"))
        print("Source on" if onoff else "Source off")
    except:
        raise StopIteration ("Source can't be turn on/off")
#--------------------------------------------------------------------------        
def measurement(volts_min,volts_max,nb,delay=0, compliance=0.1, R=0):
    """Send voltage and measure current"""
    global voltage_input, voltage_diode, measure #allow to save data even when error detected

    measure=np.array([]) #creat array for futur measures
    voltage_diode=np.array([]) # array for the real voltage across the diode
    voltage_input=np.linspace(volts_min,volts_max,nb) #creat an array with all voltages needed for measurement
 
    print('U(V)\tUd(V)\tI(A)\t\tpoints') #display titles

    i=0
    for x in voltage_input: #loop over voltage values
        i+=1 #used to display measure number (could use enumerate instead)

        try:    #SOURCE 
            keithley.write(":SOUR:VOLT %f\r" % x) #send the voltage x to the smu
        except:
            print("error from applied source")
            break
        
        time.sleep(delay) #delay not needed   
        
        try:    #MEASURE        
            y=float(keithley.query(":MEAS:CURR?\r")) #read current value
        except:
            print("error from reading measurement")
            break            

        voltage_diode=np.append(voltage_diode, x - (R*y)) #voltage correction due to safety resistance    
        measure=np.append(measure, y) #add the current value to a array regrouping all measures
 
        print ("%3.3f\t%3.3f\t%s\t%s/%s" % (x,voltage_diode[-1],y,i,nb)) #display voltage,current,points,time

        if y>=compliance:
            print("current too high")            
            break
        
    try:
        keithley.write(":SOUR:VOLT 0") #Go back to 0 volt after measures dones
    except:
        print("error : can't apply 0 volt")
        reset()
        
    return (voltage_diode,measure) #return the voltage and current array 
#--------------------------------------------------------------------------     
def complete_measure(volts_min,volts_max,nb,smux="temp",delay=0, compliance=0.1, R=0):
    """Main fonction taking tkinter value as input. Plot measures and save them."""       
    global voltage_input, voltage_diode, measure

    switchON(True) #activate smu
    
    try:
        keithley.write(":sour:volt:rang 10\r")
        keithley.write(":sour:volt:mode fix\r")
        keithley.write(":sour:func VOLT\r") #smua devient source de voltage (et donc ne peut être que mesure de courant)
        keithley.write(":curr:prot %f\r" % compliance) #used to prevent too high currents running into the circuit
        keithley.write(":form:elem curr\r") #tell the smu to read only currents values
    except:
        raise StopIteration ("error from parametring instrument")    
        
    (voltage_diode,measure)=measurement(volts_min,volts_max,nb,delay,compliance=compliance,R=R) #envoi les voltages choisis et mesure les courants associées

    switchON(False) #deactivate smu
    
    np.savetxt('Diode %s R=%s.csv' % (smux,str(R)),np.transpose((voltage_diode,measure)),delimiter="\t")
    print("data saved")    

    try:
        plt.figure(num='Diode '+smux+' Characteristic') #plot differents figure according to a specific name
        plt.clf() #clear the graph to avoir superposing data from the same set (can be deactivated if need to superpose)
        plt.title("Diode "+smux+" Characteristic")
        plt.ylabel('I(A)')
        plt.xlabel('U(V)')
        plt.semilogy(voltage_diode,measure, '+', label='Diode '+smux) #display current(input_voltage) with dots
        plt.legend() #add legend to the graph (take label from plot)
        plt.savefig('Diode %s Characteristic I(U).pdf' %smux, format='pdf', dpi=1000, bbox_inches='tight') #save the graph in a vector file
        plt.show() #plot data
        print("plot save and display")
    except:
        print ("error from plotting data")

# =============================================================================
def compute():
    """Fonction utiliser par tkinter pour commander l'instrument
    \nFonction use by tkinter to pilote the instrument"""
    message1["text"] = "" #reset messages
    message2["text"] = ""
    message4["text"] = ""
    message5["text"] = ""     
    message6["text"] = ""      
    message7["text"] = ""  
      
    smux=str(smux_entry.get()) #return the smux value in the tkinter entry     
    try:
        volts_min=float(volt_min_entry.get())   # min voltage 
        volts_max=float(volt_max_entry.get())   # max voltage      
        R=float(resistance_entry.get())   # protection resistance           
        if abs(volts_max)>20 or abs(volts_min)>20:
            texte5="abs(volt) <=10"
            message5["text"] = texte5      
            print(texte5)   
        else:                      
            nb=int(point_number_entry.get()) #measures nb
            if nb<1:
                texte4="nb>0"
                message4["text"] = texte4         
                print(texte4)              
            else:
    #                delay=float(delay_entry.get()) #not needed
    #                print(smux,volts_min,volts_max,nb,delay) #used to debug
                try:
                    complete_measure(volts_min,volts_max,nb,smux=smux,R=R,compliance=compliance)
                    texte7="Measures done"
                    message7["text"] = texte7         
                    print(texte7)                                 
                except Exception as ex:
                    texte6="Error from measurement detected: %s" % str(ex)  #display the error name
                    message6["text"] = texte6          
                    print(texte6)   
                    reset() 
    except:
        texte2="floats"
        message2["text"] = texte2  
        print(texte2)
# =============================================================================
"""Program begin"""
volts_min=0  #min voltage
nb=101       #how many measures
volts_max=1   # max voltage
delay=0  #time between applying voltage and measuring current (not needed)
smux='temp' #part of the measure name
R=0# safe resistance value
compliance=0.2 # max current value

#connection='GPIB0::24::INSTR'
connection='COM1'
connection_choice(connection) #try to connect the devide using GPIB or RS232
reset() #reset smu
keithley.write(":SYSTem:BEEPer:STATe 0") #deactivate beep
# =============================================================================
"""Tkinter menu used to facilitate measurement from an user"""
root = Tk() #used to creat user interface
frame = Frame(root)
root.title("Keithley options")
frame.pack()

L0 = Label(frame, text="diode's name:") #fixed text
L0.grid(row=0, column=0)
smux_entry = Entry(frame, textvariable=StringVar(frame, value=smux), bd =2, width=7) #stringvar is used to have default values
smux_entry.grid(row=0, column=1) #grid is used to position items on the interface

message1 = Label(frame, text="")   #allow to display messages when activate
message1.grid(row=0, column=2) 

L1 = Label(frame, text="start volt(V)")
L1.grid(row=1, column=0)
volt_min_entry = Entry(frame, textvariable=StringVar(frame, value=volts_min), bd =2, width=7)
volt_min_entry.grid(row=1, column=1)

L2 = Label(frame, text="end volt(V)")
L2.grid(row=2, column=0)
volt_max_entry = Entry(frame, textvariable=StringVar(frame, value=volts_max), bd =2, width=7)
volt_max_entry.grid(row=2, column=1)

message5 = Label(frame, text="")
message5.grid(row=2, column=2) 

L3 = Label(frame, text="nbr pts")
L3.grid(row=3, column=0)
point_number_entry = Entry(frame, textvariable=StringVar(frame, value=nb), bd =2, width=7)
point_number_entry.grid(row=3, column=1)

message4 = Label(frame, text="")
message4.grid(row=3, column=2) 

L4 = Label(frame, text="resistance(ohm)")
L4.grid(row=4, column=0)
resistance_entry = Entry(frame, textvariable=StringVar(frame, value=R), bd =2, width=7)
resistance_entry.grid(row=4, column=1)

#L4 = Label(frame, text="delay(s)")
#L4.grid(row=4, column=0)
#delay_entry = Entry(frame, textvariable=StringVar(frame, value=delay), bd =2, width=7)
#delay_entry.grid(row=4, column=1)

message2 = Label(frame, text="")
message2.grid(row=5, column=2)

message6 = Label(frame, text="")
message6.grid(row=6, column=2)

compute_button = Button(frame, text="Measure", width=14, command=compute) #button used to get all values and start measures
compute_button.grid(row=6, column=1)

message7 = Label(frame, text="")
message7.grid(row=6, column=2)

root.mainloop() #instance looping until closed
close_all() #reset and close connection with the instrument
