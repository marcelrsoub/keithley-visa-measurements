import visa
import numpy as np
import matplotlib.pyplot as plt
from tkinter import Button, Tk, Frame, Entry, Label, StringVar #, Checkbutton, BooleanVar
import time

def connexion_choice(connexion):
    """Permet de choisir la connexion
    \nAllow to choose the connexion"""
    global keithley
    try:
        rm = visa.ResourceManager() #import visa
        rm.list_resources() #import visa    
        keithley = rm.open_resource(connexion) #creat device connexion
    except:
        print("Connexion error, check the connexion (GPIB,RS232,USB,Ethernet) and it's number")
        raise StopIteration ("Erreur de connexion. Verifier la connexion (GPIB,RS232,USB,Ethernet) et son numeros \
                             \nConnexion error, check the connexion (GPIB,RS232,USB,Ethernet) and it's number")
#--------------------------------------------------------------------------
def close_all():
    """Coupe la connexion
    \nClose the connexion"""
    try:
        reset() #reset smu
        keithley.write(":SYSTem:BEEPer:STATe 0") #desactive le beep/deactivate sound
        keithley.close() #ferme la connexion/close the connexion
        print("Connexion closed")
    except:
        print("Closing error")
        raise StopIteration ("Erreur de fermeture \
                             \nClosing error")
#--------------------------------------------------------------------------        
def reset():
    """reset smu"""
    try:
        keithley.write(":system:preset")
    except:
        print("Reset error")
        raise StopIteration ("Erreur de reset \
                             \nReset error")
#--------------------------------------------------------------------------    
def switchON(onoff=False):
    """Active/desactive le smu
    \nTurn on/off the smu"""
    try:
        keithley.write((":output1:state 1" if onoff else ":output1:state 0"))
        print("Source on" if onoff else "Source off")
    except:
        print("Source can't be turn on/off")
        raise StopIteration ("Erreur de changement d'etats \
                             \nSource can't be turn on/off")
#--------------------------------------------------------------------------        
def measurement(volts_min,volts_max,nb,delay=0):
    """Envoi des tensions et mesure des courants. Enregistre les mesures dans la variable measure
    \nSend tensions and measure currents. Save measures in measure variable"""
    measure=[] #creat array for futur measures
    tension_input=np.linspace(volts_min,volts_max,nb) #creat an array with all tensions needed for measurement
    print('U(V)\t I(A)\t\t points\ttemps(s)') #display tension,current,points,time
    time_begin=time.time()
    i=0
    for x in tension_input: #loop on tensions values  
        i+=1
        keithley.write(":SOURce:VOLTage %f" % x) #send the voltage x to the smu
        time.sleep(delay) #delay not needed
                
        y=float(keithley.query(":MEASure?")) #read current value I(A)
        time_end=time.time()
        print ("%3.3f\t%s\t%s/%s\t%3.3f" % (x,y,i,nb,time_end-time_begin)) #display tension,current,points,time
        if y>=0.01: #use to stop if current too high
            close_all()
            print("current too high")
            raise ValueError ("current too high") #used as safety if the protection fail (Redundancy)
        measure.append(y) #add the current value to a array regrouping all measures
        
    return tension_input,measure #return the voltage and current array 
#--------------------------------------------------------------------------     
def complete_measure(volts_min,volts_max,nb,smux="temp",delay=0):
    """Fonction principale prennant les valeurs de tkinter en entrer. Trace les mesures et les sauvegardes.
    Principal fonction taking tkinter value as input. Plot measures and save them."""
    switchON(True) #activate smu
    
    keithley.write(":curr:protection 0.01") #used to prevent too high currents running into the circuit
    keithley.write(":source:function:mode VOLT") #smua devient source de tension (et donc ne peut être que mesure de courant)
    keithley.write(":format:elements curr") #tell the smu to read only currents values
    
    tension_input,measure=measurement(volts_min,volts_max,nb) #envoi les tensions choisis et mesure les courants associées
    keithley.write(":SOURce:VOLTage 0") #Go back to 0 volt after measures dones

    plt.figure(num='Diode '+smux+' Characteristic') #plot differents figure according to a specific name
    plt.clf() #clear the graph to avoir superposing data from the same set (can be deactivated if need to superpose)
    plt.title("Diode "+smux+" Characteristic")
    plt.ylabel('I(A)')
    plt.xlabel('U(V)')
    plt.plot(tension_input,measure, '+', label='Diode '+smux) #display current(input_tension) with dots
    plt.legend() #add legend to the graph (take label from plot)
    plt.savefig('Diode %s Characteristic I(U).svg' %smux, format='svg', dpi=1000, bbox_inches='tight') #save the graph in a vector file
    plt.show() #plot data

    np.savetxt('Diode %s Characteristic I(U).csv' % smux,np.transpose((tension_input,measure)),delimiter="\t") #save data on a binary file
    switchON(False) #deactivate smu
# =============================================================================
connexion='GPIB0::24::INSTR'
#connexion='COM1'
volts_min=0  #min voltage
nb=101       #nb de mesures
volts_max=1   # max voltage
delay=0  #time between applying voltage and measuring current (not needed)
smux='temp'

# connexion_choice(connexion) #try to connect the devide using GPIB or RS232
# reset() #reset smu
# keithley.write(":SYSTem:BEEPer:STATe 0") #deactivate beep

# =============================================================================
def compute():
    """Fonction utiliser par tkinter pour commander l'instrument
    \nFonction use by tkinter to pilote the instrument"""
    message1["text"] = "" #reset messages
    message2["text"] = ""
    message3["text"] = ""
    message4["text"] = ""
    message5["text"] = ""     
    message6["text"] = ""      
    message7["text"] = ""        
    smux=str(smux_entry.get()) #return the smux value in the tkinter entry
     
    try:
        volts_min=float(volt_min_entry.get())   # min voltage 
        volts_max=float(volt_max_entry.get())   # max voltage       
        if abs(volts_max)>10 or abs(volts_min)>10:
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
                try:  #issues with try: hide internals errors
                    complete_measure(volts_min,volts_max,nb,smux=smux)
                    texte7="Measures done"
                    message7["text"] = texte7         
                    print(texte7)                                 
                except:
                    texte6="Error from measurement detected"
                    message6["text"] = texte6          
                    print(texte6)   
                    reset() #cause False positive floats error if using without instrument and previous commands disable                      
    except:
        texte2="floats"
        message2["text"] = texte2  
        print(texte2)
    
root = Tk() #used to creat user interface
frame = Frame(root)
root.title("Keithley options")
frame.pack()

L0 = Label(frame, text="diode's name:") #fixed text
L0.grid(row=0, column=0)
smux_entry = Entry(frame, textvariable=StringVar(frame, value=smux), bd =2, width=7) #stringvar is used to have default values
smux_entry.grid(row=0, column=1) #grid is used to position items on the interface

message1 = Label(frame, text="")   #allow to display messages when activate
message1.grid(row=0, column=3) 

L1 = Label(frame, text="start volt(V)")
L1.grid(row=1, column=0)
volt_min_entry = Entry(frame, textvariable=StringVar(frame, value=volts_min), bd =2, width=7)
volt_min_entry.grid(row=1, column=1)

message3 = Label(frame, text="")
message3.grid(row=1, column=3) 

L2 = Label(frame, text="end volt(V)")
L2.grid(row=2, column=0)
volt_max_entry = Entry(frame, textvariable=StringVar(frame, value=volts_max), bd =2, width=7)
volt_max_entry.grid(row=2, column=1)

message5 = Label(frame, text="")
message5.grid(row=2, column=3) 

L3 = Label(frame, text="nbr pts")
L3.grid(row=3, column=0)
point_number_entry = Entry(frame, textvariable=StringVar(frame, value=nb), bd =2, width=7)
point_number_entry.grid(row=3, column=1)

message4 = Label(frame, text="")
message4.grid(row=3, column=3) 

#L4 = Label(frame, text="delay(s)")
#L4.grid(row=4, column=0)
#delay_entry = Entry(frame, textvariable=StringVar(frame, value=delay), bd =2, width=7)
#delay_entry.grid(row=4, column=1)

message2 = Label(frame, text="")
message2.grid(row=4, column=3)

message6 = Label(frame, text="")
message6.grid(row=5, column=3)

compute_button = Button(frame, text="Measure", width=14, command=compute) #button used to get all values and start measures
compute_button.grid(row=5, column=1)

message7 = Label(frame, text="")
message7.grid(row=5, column=3)

root.mainloop() #instance looping until closed
close_all() #reset and close connexion with the instrument