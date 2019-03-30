import visa
import numpy as np
import matplotlib.pyplot as plt
from tkinter import Button, Tk, Frame, Entry, Label, StringVar #, Checkbutton, BooleanVar
import time

def connection_choice(connection):
    """enables the user to choose the connection"""
    global keithley
    try:
        rm = visa.ResourceManager() #import visa
        rm.list_resources() #import visa    
        keithley = rm.open_resource(connection) #creat device connection
        print("connection succeed")
    except:
        raise StopIteration ("Error. Verify the connection (GPIB,RS232,USB,Ethernet) and its identifier")
#--------------------------------------------------------------------------
def close_all():
    """Close the connection"""
    reset() #reset smu
    try:        
        keithley.write("beeper.enable=0") #deactivate beep
        keithley.close() #close the connection
        print("connection closed")        
    except:
        raise StopIteration ("Closing error, connection still open")
#--------------------------------------------------------------------------        
def reset():
    """reset smu"""
    try:
        keithley.write("smua.reset()")
        keithley.write("smub.reset()")
        print("instrument reset")        
    except:
        raise StopIteration ("Reset error")
#--------------------------------------------------------------------------    
def switchON(smux, onoff=False):
    """Turn on/off the smu"""
    try:
        keithley.write(("smu%s.source.output = smu%s.OUTPUT_ON" if onoff else "smu%s.source.output = smu%s.OUTPUT_OFF") % (smux, smux))
        print("Source on" if onoff else "Source off")
    except:
        raise StopIteration ("Source can't be turn on/off")
#--------------------------------------------------------------------------        
def measurement(smux,volts_min,volts_max,nb,delay=0,compliance=0.1,R=0):
    """Send voltage and measure current"""
    global tension_input, tension_diode, measure #allow to save data even when error detected

    measure=np.array([]) #creat array for futur measures
    tension_diode=np.array([]) # array for the real voltage across the diode
    tension_input=np.linspace(volts_min,volts_max,nb) #creat an array with all tensions needed for measurement

    print('U(V)\tUd(V)\tI(A)\t\tpoints') #display titles

    i=0    
    for x in tension_input: #loop over voltage values 
        i+=1 #used to display measure number (could use enumerate instead)
        
        try:    #SOURCE
            keithley.write("smu%s.source.levelv = %f" % (smux,x))  #send voltage values to the smux
        except:
            print("error from applied source")
            break

        time.sleep(delay) #delay not needed
        
        try:    #MEASURE
            y=float(keithley.query("print(smu%s.measure.i())" % smux)) #ask the current value from smux
        except:
            print("error from reading measurement")
            break    
        
        tension_diode=np.append(tension_diode, x - (R*y))  #tension correction due to safety resistance    
        measure=np.append(measure, y) #add the current value to a array regrouping all measurements

        print ("%3.3f\t%3.3f\t%s\t%s/%s" % (x,tension_diode[-1],y,i,nb)) #display voltage and current

        if y>=compliance:
            print("current too high")            
            break

    try:
        keithley.write("smu%s.source.levelv = 0" % smux) #send 0 volt after measurements complete           
    except:
        print("error : can't apply 0 volt")
        reset()
        
    return (tension_diode,measure) #return the voltage and current diode
#--------------------------------------------------------------------------     
def complete_measure(smux,volts_min,volts_max,nb,delay=0,compliance=0.1,R=0):
    """Main fonction taking tkinter value as input. Plot measures and save them."""       
    global tension_input, tension_diode, measure
    
    switchON(smux, True) #active smua

    try:
        keithley.write("smu%s.source.func = smu%s.OUTPUT_DCVOLTS" % (smux,smux)) #select smuX as voltage source   
    except:
        raise StopIteration ("error from choosing the source type")
        
    (tension_diode,measure)=measurement(smux,volts_min,volts_max,nb,R=R,compliance=compliance) #send chosen voltage and measures the current associated

    switchON(smux, False) #deactivate smu

    np.savetxt('Diode %s R=%s.csv' % (smux,str(R)),np.transpose((tension_diode,measure)),delimiter="\t")
    print("data saved")
    
    try:
        plt.figure(num='Diode '+smux+" R="+str(R)) #plot differents figure according to a specific name
        plt.clf() #clear the graph to avoir superposing data from the same set (can be deactivated if need to superpose)
        plt.title('Diode '+str(smux)+' R='+str(R))
        plt.ylabel('I(A)')
        plt.xlabel('U(V)')
        plt.plot(tension_diode,measure, '+', label='Diode '+smux) #display current in fct of input_tension
        plt.legend() #add legend to the graph (take label from plot)
        plt.savefig('Diode %s R=%s.pdf' % (smux,str(R)), format='pdf', dpi=1000, bbox_inches='tight') #save the graph in a vector file
        plt.show() #plot data
        print("plot save and display")
    except:
        print ("error from plotting data")
# =============================================================================
def compute():
    """Fonction use by tkinter to pilote the instrument"""    
    message1["text"] = ""
    message2["text"] = ""
    message3["text"] = ""
    message4["text"] = ""
    message5["text"] = ""     
    message6["text"] = ""      
    message7["text"] = ""        
    try:  
        smux=str(smux_entry.get()) 
        if smux != 'a' and smux != 'b':
            raise ValueError
        try:
            volts_min=float(volt_min_entry.get())   # min voltage 
            volts_max=float(volt_max_entry.get())   # max voltage
            R=float(resistance_entry.get())   # pretection resistance        
            if abs(volts_max)>20 or abs(volts_min)>20:
                texte5="abs(volt) <=20"
                message5["text"] = texte5      
                print(texte5)   
            else:                      
                nb=int(point_number_entry.get()) #measures nb
                if nb<1:
                    texte4="nb>0"
                    message4["text"] = texte4         
                    print(texte4)              
                else:
    #                delay=float(delay_entry.get())  #temps entre mesures en secondes 
#                    print(smux,volts_min,volts_max,nb,delay)   #used to debug
                    try:                            
                        complete_measure(smux,volts_min,volts_max,nb,R=R,compliance=compliance) #start measurements
                        texte7="Measures done"
                        message7["text"] = texte7         
                        print(texte7)                                 
                    except Exception as ex:
                        print(ex)
                        texte6="Error from measurement detected"
                        message6["text"] = texte6          
                        print(texte6)                                       
                        reset()                    
        except:
            texte2="floats" 
            message2["text"] = texte2  
            print(texte2)
    except:
        texte="a or b"
        message1["text"] = texte
        print(texte)
# =============================================================================          
"""Programme begin"""
volts_min=0  #min voltage
nb=101       #nb de mesures
volts_max=1   # max voltage
delay=0  #temps entre mesures en secondes
smux='a'
R=100 # safe resistance value
compliance=0.2

#connection='GPIB0::26::INSTR'
connection='COM1'
connection_choice(connection) #permet de choisir le type de connection
reset() #reset completement les smu
keithley.write("beeper.enable=0") #desactive le beep
# =============================================================================   
"""Tkinter menu used to facilitate measurement from an user"""
root = Tk()
frame = Frame(root)
root.title("Keithley options")
frame.pack()

L0 = Label(frame, text="a or b")
L0.grid(row=0, column=0)
smux_entry = Entry(frame, textvariable=StringVar(frame, value=smux), bd =2, width=7)
smux_entry.grid(row=0, column=1)

message1 = Label(frame, text="")   #allow to display message when activate [text]
message1.grid(row=0, column=3) 

L1 = Label(frame, text="Initial Voltage(V)")
L1.grid(row=1, column=0)
volt_min_entry = Entry(frame, textvariable=StringVar(frame, value=volts_min), bd =2, width=7)
volt_min_entry.grid(row=1, column=1)

message3 = Label(frame, text="")
message3.grid(row=1, column=3) 

L2 = Label(frame, text="Final Voltage(V)")
L2.grid(row=2, column=0)
volt_max_entry = Entry(frame, textvariable=StringVar(frame, value=volts_max), bd =2, width=7)
volt_max_entry.grid(row=2, column=1)

message5 = Label(frame, text="")
message5.grid(row=2, column=3) 

L3 = Label(frame, text="Number of measurements")
L3.grid(row=3, column=0)
point_number_entry = Entry(frame, textvariable=StringVar(frame, value=nb), bd =2, width=7)
point_number_entry.grid(row=3, column=1)

message4 = Label(frame, text="")
message4.grid(row=3, column=3) 

L4 = Label(frame, text="Resistance(ohm)")
L4.grid(row=4, column=0)
resistance_entry = Entry(frame, textvariable=StringVar(frame, value=R), bd =2, width=7)
resistance_entry.grid(row=4, column=1)

#L4 = Label(frame, text="delay(s)")
#L4.grid(row=4, column=0)
#delay_entry = Entry(frame, textvariable=StringVar(frame, value=delay), bd =2, width=7)
#delay_entry.grid(row=4, column=1)

message2 = Label(frame, text="")
message2.grid(row=5, column=3)

message6 = Label(frame, text="")
message6.grid(row=6, column=3)

compute_button = Button(frame, text="Measure", width=14, command=compute) #button used to get all values and start measures
compute_button.grid(row=6, column=1)

message7 = Label(frame, text="")
message7.grid(row=6, column=3)

root.mainloop() #instance looping until closed
close_all() #reset and close connection with the instrument