#!/usr/bin/env python
import sys
import threading
import numpy as np
from collections import deque
import hcipy
from configobj import ConfigObj
import time
import matplotlib.pyplot as plt
import dm
import ipdb

sys.path.insert(0, '../')
from common import plotting_funcs as pf
from common import classes as ff_c
from common import fake_hardware as fhw
from common import support_functions as sf

from sn_classes import SpeckleAreaNulling

def run(camera=None, aosystem=None, config=None, configspec=None,
        my_deque=None, my_event=None, plotter=None):
    if my_deque is None:
        my_deque = deque()

    if my_event is None:
        my_event = threading.Event()
    
    #XYZ this doesn't raise an error, fix it. 
    settings = sf.validate_config(config, configspec)
    
    #----------------------------------------------------------------------
    # Simulation parameters
    #----------------------------------------------------------------------
    flux                = settings['SIMULATION']['flux']
    exptime             = settings['SIMULATION']['exptime']
    rms_wfe             = settings['SIMULATION']['rms_wfe']
    seed                = settings['SIMULATION']['seed']
    print(settings)
    
    aperturename            = settings['SIMULATION']['aperture']
    rotation_angle_aperture = settings['SIMULATION']['rotation angle aperture (deg)']
    Npix_pup                = settings['SIMULATION']['N pix pupil']
    Npix_foc                = settings['SIMULATION']['N pix focal']

    pixscale            = settings['SIMULATION']['pixel scale (mas/pix)']
    coronagraph_IWA_mas = settings['SIMULATION']['coronagraph IWA (mas)']
    lyotstopmask        = settings['SIMULATION']['lyot stop']
    
    wavelength          = settings['SIMULATION']['wavelength (m)']

    #SN Settings
    xcen                = settings['SN_SETTINGS']['xcen']
    ycen                = settings['SN_SETTINGS']['ycen']
    flip_x              = settings['SIMULATION']['flip_x']
    flip_y              = settings['SIMULATION']['flip_y']
    rotation_angle_deg  = settings['SIMULATION']['rotation angle im (deg)']
    #----------------------------------------------------------------------
    # Load instruments
    #----------------------------------------------------------------------
    if camera == 'Sim' and aosystem == 'Sim':
        TelescopeAperture = ff_c.Aperture(Npix_pup=Npix_pup,
                                 aperturename=aperturename,
                                 rotation_angle_aperture=rotation_angle_aperture)
        Lyotcoronagraph   = ff_c.LyotCoronagraph(Npix_foc=Npix_foc, IWA_mas=150, mas_pix=10, pupil_grid=TelescopeAperture.pupil_grid)
        LyotStop          = ff_c.Aperture(Npix_pup=Npix_pup,
                                          rotation_angle_aperture=0,
                                          aperturename=lyotstopmask)
    CSM = ff_c.CoronagraphSystemModel(telescopeaperture=TelescopeAperture,
                       coronagraph=Lyotcoronagraph,
                       lyotaperture=LyotStop,
                       Npix_foc=Npix_foc,
                       mas_pix=pixscale,
                       wavelength=wavelength)
    
    AOSystem = fhw.FakeAODMSystem(OpticalModel=CSM,
                       modebasis=None,
                       initial_rms_wfe=0,
                       rotation_angle_dm = 0,
                       num_actuators_across=22,
                       actuator_spacing=None,
                       seed=seed)
    
    Camera = fhw.FakeDetector(opticalsystem=CSM,
                                  flux = flux,
                                  exptime=exptime,
                                  dark_current_rate=0,
                                  read_noise=10,
                                  flat_field=0,
                                  include_photon_noise=True,
                                  xsize=1024,
                                  ysize=1024,
                                  field_center_x=333,
                                  field_center_y=433)
    
    SAN = SpeckleAreaNulling(Camera, AOSystem, 
                               initial_probe_amplitude=1,
                               initial_regularization=1,
                               controlregion_iwa = 3,
                               controlregion_owa = 8,
                               xcenter=xcen,
                               ycenter=ycen,
                               Npix_foc=Npix_foc,
                               lambdaoverD=4,
                               flipx=False,
                               flipy=False,
                               rotation_angle_deg=0)

    #data_raw = Camera.take_image()
    #data_proc = sf.reduce_images(data_raw, xcen=xcen, ycen=ycen,
    #                                      npix=Npix_foc,
    #                                      flipx = flip_x, flipy=flip_y,
    #                                      rotation_angle_deg=rotation_angle_deg)
    #plt.imshow(data_proc, origin='lower')
    #plt.show() 
    imax=[] 
    ks = []
    for k in np.arange(3,11, 0.25):
        speck = dm.make_speckle_kxy(k, 0, 50e-9, 0, N=22, flipy = False, flipx = False)
        AOSystem.set_dm_data(speck)
        data_speck = Camera.take_image()
        data_proc = sf.reduce_images(data_speck, xcen=xcen, ycen=ycen,
                                              npix=Npix_foc,
                                              flipx = flip_x, flipy=flip_y,
                                              rotation_angle_deg=rotation_angle_deg)
        #plt.imshow(data_proc, origin='lower')
        #plt.show()
        #plt.clf()
        #plt.close()
        ks.append(k)
        imax.append(np.max(data_proc[130,:]))
        #plt.plot(data_proc[130, :], label = str(k))
        #plt.clf()
        #plt.close()
    plt.plot(ks, imax)
    plt.show()
    #plt.imshow(data_proc, origin='lower')
    #plt.show() 
    ipdb.set_trace()
if __name__ == "__main__":
    #plotter = pf.LivePlotter()
    
    camera = "Sim"
    aosystem = "Sim"
    run(camera, aosystem, config='sn_config.ini', configspec='sn_config.spec')#, plotter=plotter)