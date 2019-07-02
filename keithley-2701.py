#import visa
import numpy as np
import matplotlib.pyplot as plt
from tkinter import Button, Tk, Frame, Entry, Label, StringVar, Checkbutton, BooleanVar
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
def measurement(volts_min,volts_max,nb,caract,delay=0):
    """Envoi des tensions et mesure des courants. Enregistre les mesures dans la variable measure
    \nSend tensions and measure currents. Save measures in measure variable"""
    global tension_input,measure
    measure=[] #creat array for futur measures
    tension_input=[]
    tension_input_temp=np.linspace(volts_min,volts_max,nb) #creat an array with all tensions needed for measurement
    i=0
    print('\nWrite the real voltage or nothing to keep theorical or write any string to stop prematuraly ')
    for x in tension_input_temp: #loop on tensions values  
        i+=1
        print("\nSet voltage to %s(V)" % x)
        real_value=input('True volt: ')
        if real_value == "":
            real_value=x
        try:
            real_value=float(real_value)
        except:
            print("Measure stoped")
            break
        if real_value != x:
            tension_input.append(real_value)
        else:
            tension_input.append(x)
            real_value=x
       
        time.sleep(delay) #delay not needed
        y=x #to debug only
        if caract=='Um(V)':
            ""
#            y=float(keithley.query(":MEASure?")) #read current value I(A)
        elif caract=='I(V)':
            ""
        elif caract=='ohm(Ω)':
            ""
#        
        print('Us(V)\t%s\tpoints' % caract) #display tension,current,points,time
        print ("%s\t%s\t%s/%s" % (real_value,y,i,nb)) #display tension,current,points,time

        measure.append(y) #add the current value to a array regrouping all measures
    return tension_input,measure #return the voltage and current array 
#--------------------------------------------------------------------------     
def complete_measure(volts_min,volts_max,nb,caract,smux="temp",delay=0):
    """Fonction principale prennant les valeurs de tkinter en entrer. Trace les mesures et les sauvegardes.
    Principal fonction taking tkinter value as input. Plot measures and save them."""
    global tension_input,measure
#    switchON(True) #activate smu
#    
#    keithley.write(":format:elements curr") #tell the smu to read only currents values
    tension_input,measure=measurement(volts_min,volts_max,nb,caract) #envoi les tensions choisis et mesure les courants associées

#obsolete ?
    if len(tension_input) != len(measure):
        tension_input=tension_input[0:-(len(tension_input)-len(measure))] #reduce input to measure size

    plt.figure(num='Measure '+smux) #plot differents figure according to a specific name
    plt.clf() #clear the graph to avoir superposing data from the same set (can be deactivated if need to superpose)
    plt.title("Measure "+smux)
    plt.ylabel(caract)        
    plt.xlabel('Us(V)')
    plt.plot(tension_input,measure, '+', label='Measure '+smux) #display current(input_tension) with dots
    plt.legend() #add legend to the graph (take label from plot)
    plt.savefig('Measure %s %s.svg' % (smux,caract), format='svg', dpi=1000, bbox_inches='tight') #save the graph in a vector file
    plt.show() #plot data

    np.savetxt('Measure %s %s.csv' % (smux,caract),np.transpose((tension_input,measure)),delimiter="\t") #save data on a binary file
#    switchON(False) #deactivate smu
# =============================================================================
connexion='GPIB0::24::INSTR'
#connexion='COM1'
volts_min=0  #min voltage
nb=101       #nb de mesures
volts_max=1   # max voltage
delay=0  #time between applying voltage and measuring current (not needed)
smux='temp'
caract='Um(V)'

#connexion_choice(connexion) #try to connect the devide using GPIB or RS232
#reset() #reset smu
#keithley.write(":SYSTem:BEEPer:STATe 0") #deactivate beep

# =============================================================================
def compute():
    """Fonction utilisée par tkinter pour commander l'instrument
    \nFonction use by tkinter to pilote the instrument"""
    msg_floats["text"] = ""
    msg_nb["text"] = ""
    msg_high_volt["text"] = ""         
    msg_measure["text"] = ""  
        
    smux=str(smux_entry.get()) #return the smux value in the tkinter entry  
    count=0
    if measure_volt.get()==True: #see if can measure resistance and volt or resistance and current
        count+=1                    #if so, change into "if volt and current true" then change loop measure and caract
        caract='Um(V)'
    if measure_current.get()==True:
        count+=1
        caract='I(V)'
    if measure_resistance.get()==True:
        count+=1 
        caract='ohm(Ω)'    
    if count != 1:
        txt_measure="only one choice"
        msg_measure["text"] = txt_measure    
        print(txt_measure)  
    else:
        try:
            volts_min=float(volt_min_entry.get())   # min voltage 
            volts_max=float(volt_max_entry.get())   # max voltage       
            if abs(volts_max)>10 or abs(volts_min)>10:
                txt_high_volt="abs(volt) <=10"
                msg_high_volt["text"] = txt_high_volt      
                print(txt_high_volt)   
            else:                      
                nb=int(point_number_entry.get()) #measures nb
                if nb<1:
                    txt_nb="nb>0"
                    msg_nb["text"] = txt_nb         
                    print(txt_nb)              
                else:
    #                delay=float(delay_entry.get()) #not needed
    #                print(smux,volts_min,volts_max,nb,delay) #used to debug
                    try:  #issues with try: hide internals errors
                        complete_measure(volts_min,volts_max,nb,caract,smux=smux)
                        txt_measure="Measures done"
                        msg_measure["text"] = txt_measure         
                        print(txt_measure)                                 
                    except:
                        txt_measure="Error from measurement detected"
                        msg_measure["text"] = txt_measure          
                        print(txt_measure)   
                        reset() #cause False positive floats error if using without instrument and previous commands disable                      
        except:
            txt_floats="floats"
            msg_floats["text"] = txt_floats  
            print(txt_floats)
    
root = Tk() #used to creat user interface
frame = Frame(root)
root.title("KMT - Keithley Measurement Tool")  #[Marcel]: I changed the labels just a bit
frame.pack()

L0 = Label(frame, text="Measure's name:") #fixed text
L0.grid(row=0, column=0)
smux_entry = Entry(frame, textvariable=StringVar(frame, value=smux), bd =2, width=7) #stringvar is used to have default values
smux_entry.grid(row=0, column=1) #grid is used to position items on the interface

L1 = Label(frame, text="Initial Voltage(V)")
L1.grid(row=1, column=0)
volt_min_entry = Entry(frame, textvariable=StringVar(frame, value=volts_min), bd =2, width=7)
volt_min_entry.grid(row=1, column=1)

msg_high_volt = Label(frame, text="")
msg_high_volt.grid(row=1, column=2) 

L2 = Label(frame, text="Final Voltage(V)")
L2.grid(row=2, column=0)
volt_max_entry = Entry(frame, textvariable=StringVar(frame, value=volts_max), bd =2, width=7)
volt_max_entry.grid(row=2, column=1)

msg_floats = Label(frame, text="")
msg_floats.grid(row=2, column=2)

L3 = Label(frame, text="Number of points")
L3.grid(row=3, column=0)
point_number_entry = Entry(frame, textvariable=StringVar(frame, value=nb), bd =2, width=7)
point_number_entry.grid(row=3, column=1)

msg_nb = Label(frame, text="")
msg_nb.grid(row=3, column=2) 

measure_volt = BooleanVar()
C1 = Checkbutton(frame, text = "Voltage(V)", variable = measure_volt, onvalue = True, offvalue = False)
C1.grid(row=4, column=0) 

measure_current = BooleanVar()
C2 = Checkbutton(frame, text = "Current(A)", variable = measure_current, onvalue = True, offvalue = False)
C2.grid(row=4, column=1) 

measure_resistance = BooleanVar()
C3 = Checkbutton(frame, text = "Resistance(Ω)", variable = measure_resistance, onvalue = True, offvalue = False)
C3.grid(row=4, column=2) 

msg_count = Label(frame, text="")
msg_count.grid(row=4, column=3)

compute_button = Button(frame, text="Measure", width=14, command=compute) #button used to get all values and start measures
compute_button.grid(row=5, column=1)

msg_measure = Label(frame, text="")
msg_measure.grid(row=5, column=2)

root.iconbitmap(default='crystal_oscillator1600.ico') 

root.mainloop() #instance looping until closed
close_all() #reset and close connexion with the instrument