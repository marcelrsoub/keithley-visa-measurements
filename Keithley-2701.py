import visa
import numpy as np
import matplotlib.pyplot as plt
from tkinter import Button, Tk, Frame, Entry, Label, StringVar,  IntVar, Radiobutton# Checkbutton, BooleanVar,
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
def measurement(volts_min,volts_max,nb,caract,delay=0,R=0):
    """wait for voltage to be set externaly and measure resulting current"""
    global voltage_input, voltage_diode, measure

    measure=np.array([]) #creat array for futur measures
    voltage_input=np.array([]) #voltage
    voltage_diode=np.array([]) # array for the real voltage across the diode
    voltage_input_temp=np.linspace(volts_min,volts_max,nb) #creat an array with all voltages needed for measurement
     
    print('\nWrite the real voltage or write any string to stop the measurement.\nWrite nothing in order to keep the theoretical value')
    i=0
    for x in voltage_input_temp: #loop on voltages values  
        i+=1
        
        print("\nSet voltage to %s(V)" % x) #directive send to user
        
        try:    #"SOURCE"
            real_value=float(input('Input voltage: ') or x) #might need change it into raw_input for different spyder version
#            real_value=float(raw_input('Input voltage: ') or x) #might need change it into input for different spyder version
        except:
            print("Measure stopped")
            break
        
        time.sleep(delay) #delay not needed

        try:    #MEASURE   
            y=float(keithley.query("READ?")) #read current value
        except:
            print("error from reading measurement")
            break              

        voltage_input=np.append(voltage_input,real_value) # real voltage input 
        voltage_diode=np.append(voltage_diode, real_value - (R*y)) #voltage correction due to safety resistance    
        measure=np.append(measure, y) #add the current value to a array regrouping all measures
             
        print('Us(V)\tUd(V)\t%s\tpoints' % caract) #display titles
        print ("%3.3f\t%3.3f\t%s\t%s/%s" % (real_value,voltage_diode[-1],y,i,nb)) #display voltage,current,points,time

    return (voltage_diode,measure) #return the voltage and current array 
#--------------------------------------------------------------------------     
def complete_measure(volts_min,volts_max,nb,caract,smux="temp",delay=0,R=0):
    """Main fonction taking tkinter value as input. Plot measures and save them."""
    global voltage_input, voltage_diode, measure

    try:
        keithley.write(":format:elements READ") #give only value
        if caract=='Um(V)':
            keithley.write(":FUNCtion 'VOLTage'") #change to volt measurement
            
        elif caract=='I(V)':
            keithley.write(":FUNCtion 'CURRent'")
            
        elif caract=='Resistance(Ohm)':
            keithley.write(":FUNCtion 'RESistance'")
    except:
        raise StopIteration ("error from parametring instrument")          
        
    (voltage_diode,measure)=measurement(volts_min,volts_max,nb,caract, R=R) #envoi les voltages choisis et mesure les courants associées

    np.savetxt('Measure %s %s R=%s.csv' % (smux,caract,str(R)),np.transpose((voltage_diode,measure)),delimiter="\t") #save data on a binary file
    print("data saved")   
    
    if measure.any():
        try:
            plt.figure(num='Measure '+smux) #plot differents figure according to a specific name
        #    plt.clf() #clear the graph to avoir superposing data from the same set (can be deactivated if need to superpose)
            plt.title("Measure "+smux)    
        
            if caract=='Resistance(Ohm)':       
                plt.ylabel(r'Resistance$(\Omega)$')   
            elif caract=='Um(V)':       
                plt.ylabel(r'$U_m(V)$')             
            else:
                plt.ylabel(caract) 
            plt.xlabel(r'$U_s$(V)')
            plt.plot(voltage_diode,measure, '+', label='Measure '+smux) #display current(input_voltage) with dots
            plt.legend() #add legend to the graph (take label from plot)
            plt.savefig('Measure %s %s.pdf' % (smux,caract), format='pdf', dpi=1000, bbox_inches='tight') #save the graph in a vector file
            plt.show() #plot data
            print("plot save and display")
        except:
            print ("error from plotting data")    
# =============================================================================
def compute():
    """Fonction use by tkinter to pilote the instrument"""
    msg_floats["text"] = ""
    msg_nb["text"] = ""
    msg_high_volt["text"] = ""         
    msg_measure["text"] = ""  
    msg_nb["text"] = ""  
        
    smux=str(smux_entry.get()) #return the smux value in the tkinter entry  
    if measure_choice.get()==0: #see if can measure resistance and volt or resistance and current                   #if so, change into "if volt and current true" then change loop measure and caract
        caract='Um(V)'
    elif measure_choice.get()==1:
        caract='I(V)'
    elif measure_choice.get()==2:
        caract='Resistance(Ohm)'    
    try:
        volts_min=float(volt_min_entry.get())   # min voltage 
        volts_max=float(volt_max_entry.get())   # max voltage   
        R=float(resistance_entry.get())   # protection resistance   
        if abs(volts_max)>20 or abs(volts_min)>20:
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
                try:
                    complete_measure(volts_min,volts_max,nb,caract,smux=smux, R=R)
                    txt_measure="Measures done"
                    msg_measure["text"] = txt_measure         
                    print(txt_measure)                                 
                except Exception as ex:
                    print(ex) #display the error name
                    txt_measure="Error from measurement detected"
                    msg_measure["text"] = txt_measure          
                    print(txt_measure)   
                    reset()                 
    except:
        txt_floats="floats"
        msg_floats["text"] = txt_floats  
        print(txt_floats)
# =============================================================================
"""Program begin"""
volts_min=0  #min voltage
nb=11       #nb de mesures
volts_max=1   # max voltage
delay=0  #time between applying voltage and measuring current (not needed)
smux='temp'
caract='Um(V)'
R=0

#connection='GPIB0::24::INSTR'
connection='COM1'
connection_choice(connection) #try to connect the devide using GPIB or RS232
reset() #reset smu
keithley.write(":SYSTem:BEEPer:STATe 0") #deactivate beep
# =============================================================================  
"""Tkinter menu used to facilitate measurement from an user"""
root = Tk() #used to creat user interface
frame = Frame(root)
root.title("KMT - Keithley Measurement Tool")
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

L4 = Label(frame, text="resistance(ohm)")
L4.grid(row=4, column=0)
resistance_entry = Entry(frame, textvariable=StringVar(frame, value=R), bd =2, width=7)
resistance_entry.grid(row=4, column=1)

measure_choice= IntVar()
measure_choice.set(1)
options = [
    ("Voltage(V)"),
    ("Current(A)"),
    ("Resistance(Ohm)")
]
Check_button=Label(frame, text="""Choose measurement:""")
Check_button.grid(row=5, column=0)

for val, language in enumerate(options):
    option_button=Radiobutton(frame, 
                  text=language,
                  variable=measure_choice,
                  value=val)
    option_button.grid(row=val+5, column=1)

compute_button = Button(frame, text="Measure", width=14, command=compute) #button used to get all values and start measures
compute_button.grid(row=9, column=1)

msg_measure = Label(frame, text="")
msg_measure.grid(row=9, column=2)

#root.iconbitmap(default='crystal_oscillator1600.ico') 

root.mainloop() #instance looping until closed
close_all() #reset and close connection with the instrument