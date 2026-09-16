import logging

import dbdicom as db
import vreg


def get_attributes(series):
  
    patient, study, descr = series[1], series[2][0], series[3][0]
    
    return patient, study, descr


def get_vol_arrays(series, dims = None):
  
    try:
      # Read the volume
      if dims is None:
          vol = db.volume(series)
      else:
          vol = db.volume(series, dims = dims)
      array = vol.values # Read the array
    except Exception as e:
      logging.error(f"Patient {series[1]} - error reading I-O {series}: {e}")

    return vol, array


def save(dir_output, series, new_descr, new_array, original_vol):
  
    participant, study, _ = get_attributes(series)
  
    # Save results as DICOM
    new_dicom = [dir_output, participant, study, new_descr]

    if original_vol is None:
      db.write_volume(new_array, new_dicom, ref = series)
    else:
      new_vol = vreg.volume(new_array, original_vol.affine, coords=(original_vol.coords), dims=original_vol.dims)
      db.write_volume(new_vol, new_dicom, ref = series)
