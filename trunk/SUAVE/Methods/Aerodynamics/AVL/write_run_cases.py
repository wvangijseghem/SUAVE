## @ingroup Methods-Aerodynamics-AVL
# write_runcases.py
# 
# Created:  Dec 2014, T. Momose
# Modified: Jan 2016, E. Botero
#           Apr 2017, M. Clarke
#           Aug 2019, M. Clarke
#           Apr 2020, M. Clarke

# ----------------------------------------------------------------------
#  Imports
# ----------------------------------------------------------------------
from SUAVE.Methods.Aerodynamics.AVL.purge_files       import purge_files

## @ingroup Analyses-AVL
def write_run_cases(avl_object,trim_aircraft):
    """ This function writes the run cases used in the AVL batch analysis

    Assumptions:
        None
        
    Source:
        Drela, M. and Youngren, H., AVL, http://web.mit.edu/drela/Public/web/avl
   
    Inputs:
        avl_object.current_status.batch_file                    [-]
        avl_object.geometry.mass_properties.center_of_gravity   [meters]
   
    Outputs:
        None
   
    Properties Used:
        N/A
    """       
    

    # unpack avl_inputs
    aircraft       = avl_object.geometry
    batch_filename = avl_object.current_status.batch_file

    base_case_text = \
'''

 ---------------------------------------------
 Run case  {0}:   {1}

 alpha        ->  {2}       =   {3}        
 beta         ->  beta        =   {4}
 pb/2V        ->  pb/2V       =   0.00000
 qc/2V        ->  qc/2V       =   0.00000
 rb/2V        ->  rb/2V       =   0.00000
{5}
 alpha     =   {6}
 beta      =   0.00000     deg
 pb/2V     =   0.00000
 qc/2V     =   0.00000
 rb/2V     =   0.00000
 CL        =   {7}                        
 CDo       =   {8}
 bank      =   0.00000     deg
 elevation =   0.00000     deg
 heading   =   0.00000     deg
 Mach      =   {9}
 velocity  =   {10}     m/s               
 density   =   {11}     kg/m^3
 grav.acc. =   {12}     m/s^2
 turn_rad. =   0.00000     m
 load_fac. =   0.00000
 X_cg      =   {13}     m
 Y_cg      =   {14}     m
 Z_cg      =   {15}     m
 mass      =   {16}     kg
 Ixx       =   {17}     kg-m^2
 Iyy       =   {18}     kg-m^2
 Izz       =   {19}     kg-m^2
 Ixy       =   {20}     kg-m^2
 Iyz       =   {21}     kg-m^2
 Izx       =   {22}     kg-m^2
 visc CL_a =   0.00000
 visc CL_u =   0.00000
 visc CM_a =   0.00000
 visc CM_u =   0.00000

'''#{4} is a set of control surface inputs that will vary depending on the control surface configuration

    # Open the geometry file after purging if it already exists
    purge_files([batch_filename]) 
    with open(batch_filename,'w') as runcases:
        # extract C.G. coordinates and moment of intertia tensor

        x_cg = aircraft.mass_properties.center_of_gravity[0][0]
        y_cg = aircraft.mass_properties.center_of_gravity[0][1]
        z_cg = aircraft.mass_properties.center_of_gravity[0][2]
        mass = aircraft.mass_properties.mass
        moments_of_inertia = aircraft.mass_properties.moments_of_inertia.tensor
        Ixx  = moments_of_inertia[0][0]
        Iyy  = moments_of_inertia[1][1]
        Izz  = moments_of_inertia[2][2]
        Ixy  = moments_of_inertia[0][1]
        Iyz  = moments_of_inertia[1][2]
        Izx  = moments_of_inertia[2][0]

        for case_name in avl_object.current_status.cases:
            # extract flight conditions 
            case  = avl_object.current_status.cases[case_name]
            index = case.index
            name  = case.tag
            CL    = case.conditions.aerodynamics.flight_CL
            AoA   = round(case.conditions.aerodynamics.angle_of_attack,4)
            CDp   = 0.
            beta  = round(case.conditions.aerodynamics.side_slip_angle,4)
            mach  = round(case.conditions.freestream.mach,4)
            vel   = round(case.conditions.freestream.velocity,4)
            rho   = round(case.conditions.freestream.density,4)
            g     = case.conditions.freestream.gravitational_acceleration
            
            if trim_aircraft == False: # this flag sets up a trim analysis if one is declared by the boolean "trim_aircraft"
                controls_text = '' 
                if CL is None: # if angle of attack is specified without trim, the appropriate fields are filled 
                    toggle_idx = 'alpha'
                    toggle_val = AoA
                    alpha_val  = '0.00000     deg'
                    CL_val     = '0.00000'
                    
                elif AoA is None: # if flight lift coefficient is specified without trim, the appropriate fields are filled 
                    toggle_idx = 'CL   '
                    toggle_val = CL
                    alpha_val  = '0.00000     deg'
                    CL_val     = '0.00000'
 
            elif trim_aircraft: # trim is specified 
                if CL is None: # if angle of attack is specified with trim, the appropriate fields are filled with the trim AoA
                    toggle_idx = 'alpha'
                    toggle_val = AoA
                    alpha_val  = AoA 
                    CL_val     = '0.00000'
                    
                elif AoA is None:  # if flight lift coefficient is specified with trim, the appropriate fields are filled with the trim CL
                    toggle_idx = 'CL'
                    toggle_val = CL
                    alpha_val  = '0.00000     deg'
                    CL_val     = CL
                
                controls = []
                if case.stability_and_control.number_control_surfaces != 0 :
                    # write control surface text in .run file if there is any
                    controls = make_controls_case_text(case.stability_and_control.control_surface_names,case.stability_and_control.control_surface_functions)
                controls_text = ''.join(controls)
                
            # write the .run file using template and the extracted vehicle properties and flight condition
            case_text = base_case_text.format(index,name,toggle_idx,toggle_val,beta,controls_text,alpha_val, CL_val,CDp,
                                              mach,vel,rho,g,x_cg,y_cg,z_cg,mass,Ixx,Iyy,Izz,Ixy,Iyz,Izx,) 
            runcases.write(case_text)

    return

def make_controls_case_text(cs_names, cs_functions):
    """ This function writes the text of the control surfaces in the AVL batch analysis.
    This tells AVL what control surface you want use to control a particular response.
    """ 
    control_surface_text = []
    for idx in range(len(cs_names)):
        # template for control surface 
        base_control_cond_text = ' {0}->  {1}=   0.00000\n'
        
        # Get name of control surface 
        cs_function  = cs_functions[idx]
        ctrl_tag     = cs_names[idx]
        # This condition block assigns the control surface to a particular stabiltiy response 
        if cs_function == 'flap':         # if control surface function is 'flap', specify to AVL that it is a flap
            ctrl_name = "{:<13}".format(ctrl_tag)
            variable  = 'flap        '
        elif cs_function == 'aileron':    # if control surface funcion is 'aileron', specify to AVL that this is used to produce no roll moment
            ctrl_name = "{:<13}".format(ctrl_tag)
            variable  = 'Cl roll mom '
        elif cs_function == 'elevator':   # if control surface function is 'elevator', specify to AVL that this is used to produce no pitch moment
            ctrl_name = "{:<13}".format(ctrl_tag)
            variable  = 'Cm pitchmom '
        elif cs_function == 'rudder':     # if control surface function is 'rudder', specify to AVL that this is used to produce no yaw moment
            ctrl_name = "{:<13}".format(ctrl_tag)
            variable  = 'Cn yaw  mom '
            
        # write the control surface functionality into template 
        text = base_control_cond_text.format(ctrl_name,variable)
        
        # append text 
        control_surface_text.append(text)
    return control_surface_text
