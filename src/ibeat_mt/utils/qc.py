import os

import matplotlib.pyplot as plt
import seaborn as sns

import numpy as np

import ants
from PIL import Image

from utils import dicom, data


def convert_to_ants(array, fit, coreg):
    
    moving = ants.from_numpy(array.astype(float)) # original 'moving' images
    fixed = ants.from_numpy(np.array(fit)) # registered to image fit
    coreg_ants = ants.from_numpy(coreg.astype(float)) # resulting registrered images

    # reverse image directions right/left
    fi = ants.reflect_image(image=fixed, axis=0)
    mi = ants.reflect_image(image=moving, axis=0)
    ci = ants.reflect_image(image=coreg_ants, axis=0)

    return fi, mi, ci
        

def plot_alignment(fi, mi, ci, series, sitepath):
    
    # fi = fixed = 'fixed' image fit
    # mi = moving = original 'moving' images
    # ci = coreg = resulting registrered images

    filename = f"{series[1]}_{series[2][0]}_{series[-1][0]}"
    filepath = os.path.join(sitepath, filename)
    fileBefore = f'{filepath}_BeforeRegistration.png'
    fileAfter = f'{filepath}_AfterRegistration.png'

    total_slices = mi.shape[2]

    # overlay original moving images on top of fixed fitted images (before reg)
    mi[:,:,:,0].plot(overlay=mi[:,:,:,1], title='Before Registration',
                    cmap='grey', overlay_cmap='hot', overlay_alpha=0.5, nslices = total_slices,
                    axis = 2, filename = fileBefore, dpi = 200)
    ci[:,:,:,0].plot(overlay=ci[:,:,:,1], title='After Registration (MT OFF over MT ON)',
                    cmap='grey', overlay_cmap='hot', overlay_alpha=0.5, nslices = total_slices,
                    axis = 2, filename = fileAfter, dpi = 200)
    
    # Use Pillow to stitch them horizontally 
    imgBefore = Image.open(fileBefore)
    imgAfter = Image.open(fileAfter)

    # Create a blank white canvas matching both widths side-by-side
    combined = Image.new('RGB', (imgBefore.width + imgAfter.width, imgBefore.height), color='white')
    combined.paste(imgBefore, (0, 0))
    combined.paste(imgAfter, (imgBefore.width, 0))

    # Save the final Before vs After comparison
    combined.save(f'{filepath}_RegCompare.png')
    
    # delete the single images
    os.remove(fileBefore)
    os.remove(fileAfter)


def calculate_ier(fi, transfo, patient):

    # Compute the jacobian determinant of the forward deformation field from transformation file
    jacobian = ants.create_jacobian_determinant_image(fi, transfo[0], do_log=False)
    jac_array = jacobian.numpy()

    # Calculate the Inverted Element Ratio (IER)
    # an inverted element occurs where the Jacobian determinant is < 0 (inidcated folding/implausible tissue loss)
    # Identify inverted voxels (Jacobian < 0)
    inverted_voxels = np.sum(jac_array < 0)

    # Total number of voxels in the 3D array
    total_voxels = jac_array.size

    # Calculate the ratio
    ier = inverted_voxels / total_voxels

    print(f"Inverted Element Ratio: {ier:.6f}")

    new_row = {"Patient": patient, "IER [%]": ier}
    

    return new_row


def calculate_ice(MTtype, series, path, dir_transforms, transfo, fixed, moving):

    if MTtype == 'ON':
        index = 0
    else:
        index = 1

    patient, study, descr = dicom.get_attributes(series)
    site = series[0].split(os.sep)[-1]
    group = series[0].split(os.sep)[-2]

    patient_folder = os.path.join(dir_transforms, patient)
    os.makedirs(patient_folder, exist_ok=True)

    filename_prefix = f"{patient}_{study}_{descr}"
    folder_and_filename = f"{os.path.join(patient_folder, filename_prefix)}{MTtype}_ice_field_"

    # transfo[0] & transfo[1] order should be [forward_warp, forward_affine, inverse_affine, inverse_warp]
    # Note: forward_affine and inverse_affine are often the same .mat file, just inverted at runtime.
    combined_transfo_list = transfo[0][0] + transfo[0][1]

    # CRITICAL. ANTs does not save a separate inverse affine file; it saves the forward affine .mat file
    # in both the fwdtransforms and invtransforms lists. To get the actual inverse, you must set this flag
    # to True so ANTs performs a matrix inversion at runtime.
    invert_flags = [False, False, True, False] # Invert the affine component
    
    # Calculate inverse consistency error (ICE)
    # Apply forward then inverse transformation to check consistency
    # calculate ICE by composing forward and inverse transforms into a single displacement field.
    # In a perfect registration, composite field would be all zeros (the identity transform)
    #fwd_warp = ants.apply_transforms(fixed=fi, moving=mi, transformlist=transfo[0][0][0])
    #inv_warp = ants.apply_transforms(fixed=fi, moving=mi, transformlist=transfo[0][1][1])
    
    ice_field_path = ants.apply_transforms(
                    fixed=fixed[:,:,:,index], 
                    moving=moving[:,:,:,index],
                    transformlist=combined_transfo_list,
                    whichtoinvert=invert_flags,
                    compose=folder_and_filename # This returns a path to the composed warp
                    )

    return ice_field_path


def plot_ice(series, path, MTtype, ice_warp_path):

    patient, study, descr = dicom.get_attributes(series)

    transform_folder = os.path.join(path, 'transforms')
    os.makedirs(transform_folder, exist_ok=True)

    filename_prefix = f"{patient}_{study}_{descr}"
    
    folder_and_filename = f"{os.path.join(transform_folder, filename_prefix)}{MTtype}_ice.png"
    
    # Load the composed warp field as an ANTs image
    ice_warp = ants.image_read(ice_warp_path)

    # Convert to NumPy array
    # For a 3D image, the array shape is typically (Z, Y, X, 1, 3)
    warp_array = ice_warp.numpy()

    # Calculate the magnitude (Euclidean norm) across the last axis
    # Use axis=-1 to target the (dx, dy, dz) vector components
    ice_mag_array = np.linalg.norm(warp_array, axis=-1)

    # Convert to mm if spacing is not 1x1x1
    dx = warp_array[..., 0] * ice_warp.spacing[0]
    dy = warp_array[..., 1] * ice_warp.spacing[1]
    dz = warp_array[..., 2] * ice_warp.spacing[2]
    ice_mag_mm = np.sqrt(dx**2 + dy**2 + dz**2)

    # flatten the 3D array to a 1D list of all voxel error values
    errors = ice_mag_mm.flatten()

    # Calculate stats
    median_ice = np.median(errors)
    mean_ice = np.mean(errors)

    # Calculate ratio
    print(f"Inverse Consistency Error (median): {median_ice:.6f}")
    print(f"Inverse Consistency Error (mean): {mean_ice:.6f}")

    new_row = {"Patient": f"{patient}_{MTtype}", "ICE median [%]": median_ice, "ICE mean [%]": mean_ice}

    # Set up figure
    fig, ax = plt.subplots(
            figsize=(5, 5),
            dpi=300
        )

    # Plot Probability Density (KDE)
    # hist=True adds the underlying histogram bars for context
    sns.histplot(errors, kde=True, stat="density", color="skyblue", element="step", alpha=0.4)

    # Add vertical line for median
    plt.axvline(median_ice, color='red', linestyle='--', linewidth=2, 
                label=f'Median ICE: {median_ice:.4f} [mm]')

    # Add vertical line for mean
    plt.axvline(mean_ice, color='green', linestyle=':', linewidth=2, 
                label=f'Mean ICE: {mean_ice:.4f} [mm]')

    # Formatting
    plt.title(f'Probability Density of Inverse Consistency Error (ICE) for MT {MTtype}', fontsize=14)
    plt.xlabel('Inconsistency Error [mm]', fontsize=12)
    plt.ylabel('Density', fontsize=12)
    plt.legend()
    plt.grid(axis='y', alpha=0.3)

    #plt.show()
    
    # Save each image to a png file
    fig.savefig(folder_and_filename, bbox_inches='tight')
    plt.close(fig)

    return new_row
