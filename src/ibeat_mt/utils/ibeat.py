from pathlib import Path
import logging

import dbdicom as db

#ibeat metadata
LEEDS = { # siemens, but no series_description
    "parameters/sequence": ["*fl3d1"]
} 
SIEMENS = { # leeds_setup, bordeaux, exeter
"series_description": [
        "MT_OFF_kidneys_cor-oblique_bh", 
        "MT_ON_kidneys_cor-oblique_bh"
    ]
}
PHILIPS = { # bari, sheffield set-up
    "series_description": [
        "MT_OFF_kidneys_cor-oblique_bh", 
        "MT_ON_kidneys_cor-oblique_bh off resonance"
    ]
}
GE = { # sheffield, turku_ge
    "series_description": [
        "MT_OFF_kidneys_cor-oblique_mbh", 
        "MT_ON_kidneys_cor-oblique_mbh"
    ]
}
TURKU_PHILIPS = {
    "series_description": [
        'mt-off-kidney-coronal-oblique-bh', 
        'mt-on-kidney-coronal-oblique-bh'
    ]
}

DOWNLOAD = {
    'leeds_patients':{
        'project_id': "BEAt-DKD-WP4-Leeds",
        'subject_label':"Leeds_Patients",
        'attr': LEEDS,
    },
    'leeds_volunteers':{
        'project_id': "BEAt-DKD-WP4-Leeds",
        'subject_label':"Leeds_volunteer_repeatability_study",
        'attr': LEEDS,
    },
    'leeds_setup':{
        'project_id': "BEAt-DKD-WP4-Leeds",
        'subject_label':"Leeds_setup_scans",
        'attr': SIEMENS     
    },
    'bari_patients':{
        'project_id': "BEAt-DKD-WP4-Bari",
        'subject_label':"Bari_Patients",
        'attr': PHILIPS,
    },
    'bari_volunteers':{
        'project_id': "BEAt-DKD-WP4-Bari",
        'subject_label':"Bari_Volunteers_Repeatability",
        'attr': PHILIPS,
    },
    'sheffield_patients':{ # rewrite 02_clean_database with experiment path?
        'project_id': "BEAt-DKD-WP4-Sheffield",
        'attr': GE
    },
  #  'sheffield_setup':{ # need to figure out folder placement
  #      'project_id': "ibeat_setup",
  #      'attr': PHILIPS
  #  },
    'turku_ge_patients':{ # rewrite 02_clean_database with experiment path?
        'project_id': "BEAt-DKD-WP4-Turku",
        'subject_label': "Turku_Patients_GE",
        'attr': GE   
    },
    'turku_ge_repeatability':{ # rewrite 02_clean_database with experiment path?
        'project_id': "BEAt-DKD-WP4-Turku",
        'subject_label': "Turku_Volunteers_GE_Repeatability",
        'attr': GE     
    },
  #    'turku_ge_setup':{ # don't think any MT series in here
  #      'project_id': "BEAt-DKD-WP4-Turku",
  #      'subject_label': "Turku_GE_Setup_Tests",
  #      'attr': TURKU_GE_SETUP     
  #  },
    'turku_philips_patients':{
        'project_id': "BEAt-DKD-WP4-Turku",
        'subject_label': "Turku_Patients_Philips",
        'attr': TURKU_PHILIPS      
    },
    'turku_philips_repeatability':{
        'project_id': "BEAt-DKD-WP4-Turku",
        'subject_label': "Turku_volunteer_repeatability_study",
        'attr': TURKU_PHILIPS    
    },
    'bordeaux_patients_baseline':{
        'project_id': "BEAt-DKD-WP4-Bordeaux",
        'subject_label': "Bordeaux_Patients_Baseline",
        'attr': SIEMENS      
    },
    'bordeaux_volunteers':{
        'project_id': "BEAt-DKD-WP4-Bordeaux",
        'subject_label': "Bordeaux_Volunteers_Repeatability_Baseline",
        'attr': SIEMENS      
    },
    'bordeaux_patients_followup':{
        'project_id': "BEAt-DKD-WP4-Bordeaux",
        'subject_label': "Bordeaux_Patients_Followup",
        'attr': SIEMENS     
    },
    'exeter_patients_baseline':{ # check if needs affine in 02_clean_database
        'project_id': "BEAt-DKD-WP4-Exeter",
        'subject_label': "Exeter_Patients_Baseline",
        'attr': SIEMENS      
    },
    'exeter_patients_followup':{ # check if needs affine in 02_clean_database
        'project_id': "BEAt-DKD-WP4-Exeter",
        'subject_label': "Exeter_Patients_Followup",
        'attr': SIEMENS      
    },
    'exeter_volunteers':{
        'project_id': "BEAt-DKD-WP4-Exeter",
        'subject_label': "Exeter_Volunteer",
        'attr': SIEMENS     
    },
      'exeter_setup':{
        'project_id': "BEAt-DKD-WP4-Exeter",
        'subject_label': "Exeter_setup_scans",
        'attr': SIEMENS       
    },
}


# Project structure on XNAT

IBEAT_XNAT = {
    "BEAt-DKD-WP4-Leeds": [
        "Leeds_Patients",
        "Leeds_volunteer_repeatability_study",
        "Leeds_setup_scans",
    ],
    "BEAt-DKD-WP4-Bari": [
        "Bari_Patients",
        "Bari_Volunteers_Repeatability",
    ],
    "BEAt-DKD-WP4-Bordeaux": [
        "Bordeaux_Patients_Baseline",
        "Bordeaux_Patients_Followup",
        "Bordeaux_Volunteers_Repeatability_Baseline",
    ],
    "BEAt-DKD-WP4-Exeter": [
        "Exeter_Patients_Baseline",
        "Exeter_Patients_Followup",
        "Exeter_Volunteers_Repeatability",
        "Exeter_setup_scans",
    ],
    "BEAt-DKD-WP4-Turku": [
        "Turku_GE_Setup_Tests",
        "Turku_Patients_GE",
        "Turku_Patients_Philips",
        "Turku_Volunteers_GE_Repeatability",
        "Turku_volunteer_repeatability_study",
    ],
    "BEAt-DKD-WP4-Sheffield": [
        None,
        # one subject per participant - find all
    ],
    "ibeat_setup": [
        None,
        # Setup scans in Sheffield
    ],
}



# Patient IDS used in the sites

SITE_IDS = {
    'Bari': ['1128'],
    'Leeds': ['4128'],
    'Bordeaux': ['2128', '6128'],
    'Exeter': ['3128'],
    'Leeds': ['4128'],
    'Sheffield': ['7128'],
    'Turku': ['5128', '6128'],
}

# Clean patient IDs and Study Descriptions for known controls

CLEAN_CTRL_IDS = {

    # Leeds setup
    ('Leeds_MR_VOL_006', 'BEAt-DKD-WP4-Leeds'): ('4128_C06', 'Visit1'),
    ('Leeds_MR_VOL_007', 'BEAt-DKD-WP4-Leeds'): ('4128_C07', 'Visit1'),
    ('Leeds_MR_VOL_008', 'BEAt-DKD-WP4-Leeds'): ('4128_C08', 'Visit1'),
    ('Leeds_MR_VOL_009', 'BEAt-DKD-WP4-Leeds'): ('4128_C09', 'Visit1'),
    ('Leeds_MR_VOL_012', 'BEAt-DKD-WP4-Leeds'): ('4128_C12', 'Visit1'),
    ('Leeds_MR_VOL_013', 'BEAt-DKD-WP4-Leeds'): ('4128_C13', 'Visit1'),
    ('Leeds_MR_VOL_014', 'BEAt-DKD-WP4-Leeds'): ('4128_C14', 'Visit1'),
    ('Leeds_MR_VOL_016', 'BEAt-DKD-WP4-Leeds'): ('4128_C16', 'Visit1'),
    ('Leeds_MR_VOL_019', 'BEAt-DKD-WP4-Leeds'): ('4128_C19', 'Visit1'),
    ('Leeds_MR_VOL_020', 'BEAt-DKD-WP4-Leeds'): ('4128_C20', 'Visit1'),

    # Leeds repeatability
    ('Leeds_REP_VOL_001_01', 'BEAt-DKD-WP4-Leeds'): ('4128_C21', 'Visit1'),
    ('Leeds_REP_VOL_001_02', 'BEAt-DKD-WP4-Leeds'): ('4128_C21', 'Visit2'),
    ('Leeds_REP_VOL_001_03', 'BEAt-DKD-WP4-Leeds'): ('4128_C21', 'Visit3'),
    ('Leeds_REP_VOL_001_04', 'BEAt-DKD-WP4-Leeds'): ('4128_C21', 'Visit4'),
    ('Leeds_REP_VOL_002_01', 'BEAt-DKD-WP4-Leeds'): ('4128_C22', 'Visit1'),
    ('Leeds_REP_VOL_002_02', 'BEAt-DKD-WP4-Leeds'): ('4128_C22', 'Visit2'),
    ('Leeds_REP_VOL_002_03', 'BEAt-DKD-WP4-Leeds'): ('4128_C22', 'Visit3'),
    ('Leeds_REP_VOL_002_04', 'BEAt-DKD-WP4-Leeds'): ('4128_C22', 'Visit4'),
    ('Leeds_REP_VOL_003_01', 'BEAt-DKD-WP4-Leeds'): ('4128_C23', 'Visit1'),
    ('Leeds_REP_VOL_003_02', 'BEAt-DKD-WP4-Leeds'): ('4128_C23', 'Visit2'),
    ('Leeds_REP_VOL_003_03', 'BEAt-DKD-WP4-Leeds'): ('4128_C23', 'Visit3'),
    ('Leeds_REP_VOL_003_04', 'BEAt-DKD-WP4-Leeds'): ('4128_C23', 'Visit4'),
    ('Leeds_REP_VOL_004_01', 'BEAt-DKD-WP4-Leeds'): ('4128_C24', 'Visit1'),
    ('Leeds_REP_VOL_004_02', 'BEAt-DKD-WP4-Leeds'): ('4128_C24', 'Visit2'),
    ('Leeds_REP_VOL_004_03', 'BEAt-DKD-WP4-Leeds'): ('4128_C24', 'Visit3'),
    ('Leeds_REP_VOL_004_04', 'BEAt-DKD-WP4-Leeds'): ('4128_C24', 'Visit4'),
    ('REP_VOL_004_01', 'BEAt-DKD-WP4-Leeds'): ('4128_C24', 'Visit1'),
    ('REP_VOL_004_02', 'BEAt-DKD-WP4-Leeds'): ('4128_C24', 'Visit2'),
    ('REP_VOL_004_03', 'BEAt-DKD-WP4-Leeds'): ('4128_C24', 'Visit3'),
    ('REP_VOL_004_04', 'BEAt-DKD-WP4-Leeds'): ('4128_C24', 'Visit4'),
    ('Leeds_REP_VOL_005_01', 'BEAt-DKD-WP4-Leeds'): ('4128_C25', 'Visit1'), 
    ('Leeds_Rep_Vol_005_02', 'BEAt-DKD-WP4-Leeds'): ('4128_C25', 'Visit2'),
    ('Leeds_REP_VOL_005_03', 'BEAt-DKD-WP4-Leeds'): ('4128_C25', 'Visit3'), 
    ('Leeds_REP_VOL_005_03', 'BEAt-DKD-WP4-Leeds'): ('4128_C25', 'Visit4'), 

    # Turku volunteers
    ('iBE-5128-251_V1', 'BEAt-DKD-WP4-Turku'): ('5128_C05', 'Visit1'),
    ('iBE-5128-252_V1', 'BEAt-DKD-WP4-Turku'): ('5128_C05', 'Visit2'),
    ('iBE-5128-253_V1', 'BEAt-DKD-WP4-Turku'): ('5128_C05', 'Visit3'),
    ('iBE-5128-251_V2', 'BEAt-DKD-WP4-Turku'): ('5128_C05', 'Visit4'),
    ('iBE-5128-261_V1', 'BEAt-DKD-WP4-Turku'): ('5128_C06', 'Visit1'),
    ('iBE-5128-262_V1', 'BEAt-DKD-WP4-Turku'): ('5128_C06', 'Visit2'),
    ('iBE-5128-263_V1', 'BEAt-DKD-WP4-Turku'): ('5128_C06', 'Visit3'),
    ('iBE-5128-264_V1', 'BEAt-DKD-WP4-Turku'): ('5128_C06', 'Visit4'),
    ('iBE-5128-271_V1', 'BEAt-DKD-WP4-Turku'): ('5128_C07', 'Visit1'),
    ('iBE-5128-281_V1', 'BEAt-DKD-WP4-Turku'): ('5128_C08', 'Visit1'),
    ('iBE-5128-282_V1', 'BEAt-DKD-WP4-Turku'): ('5128_C08', 'Visit2'),
    ('iBE-5128-283_V1', 'BEAt-DKD-WP4-Turku'): ('5128_C08', 'Visit3'),
    ('iBE-5128-281_V2', 'BEAt-DKD-WP4-Turku'): ('5128_C08', 'Visit4'),
    ('iBE-5128-291_V1', 'BEAt-DKD-WP4-Turku'): ('5128_C09', 'Visit1'),
    ('iBE-5128-292_V1', 'BEAt-DKD-WP4-Turku'): ('5128_C09', 'Visit2'),
    ('iBE-5128-293_V1', 'BEAt-DKD-WP4-Turku'): ('5128_C09', 'Visit3'),
    ('iBE-5128-294_V1', 'BEAt-DKD-WP4-Turku'): ('5128_C09', 'Visit4'),
    ('iBE-5128-301_V1', 'BEAt-DKD-WP4-Turku'): ('5128_C10', 'Visit1'),
    ('iBE-5128-301_V2', 'BEAt-DKD-WP4-Turku'): ('5128_C10', 'Visit2'),
    ('iBE-5128-301_V3', 'BEAt-DKD-WP4-Turku'): ('5128_C10', 'Visit3'),
    ('iBE-5128-301_V4', 'BEAt-DKD-WP4-Turku'): ('5128_C10', 'Visit4'),

    # Turku GE setup
    ('subject_1', 'BEAt-DKD-WP4-Turku'): ('5128_C11', 'Visit1'),

    # Turku Philips volunteers
    ('5128-211', 'BEAt-DKD-WP4-Turku'): ('5128_C01', 'Visit1'),
    ('5128-212', 'BEAt-DKD-WP4-Turku'): ('5128_C01', 'Visit2'),
    ('5128-213', 'BEAt-DKD-WP4-Turku'): ('5128_C01', 'Visit3'),
    ('5128-214', 'BEAt-DKD-WP4-Turku'): ('5128_C01', 'Visit4'),
    ('5128-221', 'BEAt-DKD-WP4-Turku'): ('5128_C02', 'Visit1'),
    ('5128-222', 'BEAt-DKD-WP4-Turku'): ('5128_C02', 'Visit2'),
    ('5128-223', 'BEAt-DKD-WP4-Turku'): ('5128_C02', 'Visit3'),
    ('5128-224', 'BEAt-DKD-WP4-Turku'): ('5128_C02', 'Visit4'),
    ('5128-231', 'BEAt-DKD-WP4-Turku'): ('5128_C03', 'Visit1'),
    ('5128-232', 'BEAt-DKD-WP4-Turku'): ('5128_C03', 'Visit2'),
    ('5128-233', 'BEAt-DKD-WP4-Turku'): ('5128_C03', 'Visit3'),
    ('5128-234', 'BEAt-DKD-WP4-Turku'): ('5128_C03', 'Visit4'),
    ('5128-241', 'BEAt-DKD-WP4-Turku'): ('5128_C04', 'Visit1'),
    ('5128-242', 'BEAt-DKD-WP4-Turku'): ('5128_C04', 'Visit2'),
    ('5128-243', 'BEAt-DKD-WP4-Turku'): ('5128_C04', 'Visit3'),
    ('5128-244', 'BEAt-DKD-WP4-Turku'): ('5128_C04', 'Visit4'),

    # Bordeaux volunteers
    ('TEST_RETEST_001', 'BEAt-DKD-WP4-Bordeaux'): ('2128_C01', 'Visit1'),
    ('TEST_RETEST_002', 'BEAt-DKD-WP4-Bordeaux'): ('2128_C01', 'Visit2'),
    ('Bordeaux_Volunteers_Repeatability_Baseline', 'BEAt-DKD-WP4-Bordeaux'): ('2128_C01', 'Visit3'),
    ('TEST_RETEST_004_1', 'BEAt-DKD-WP4-Bordeaux'): ('2128_C01', 'Visit4'),

    # Exeter setup
    ('TestPatient1', 'BEAt-DKD-WP4-Exeter'): ('3128_C01', 'Visit1'),
    ('TestPatient2', 'BEAt-DKD-WP4-Exeter'): ('3128_C02', 'Visit1'),
    ('TestPatient5', 'BEAt-DKD-WP4-Exeter'): ('3128_C01', 'Visit2'),

    # Exeter repeatability
    ('TE37-001', 'BEAt-DKD-WP4-Exeter'): ('3128_C01', None), # StudyDescription not in DICOM header - must be determined from folder_name

    # Bari volunteers
    ('bari_volunteer1_20201222', 'BEAt-DKD-WP4-Bari'): ('1128_C01', 'Visit1'),
    ('bari_volunteer1_20210109', 'BEAt-DKD-WP4-Bari'): ('1128_C01', 'Visit2'),
    ('Bari_Volunteers_Repeatability', 'BEAt-DKD-WP4-Bari'): ('1128_C01', 'Visit3'), # This is 'bari_volunteer1_20210123' with wrong ID entered
    ('bari_volunteer1_20210130', 'BEAt-DKD-WP4-Bari'): ('1128_C01', 'Visit4'),

    # Sheffield setup 
    ('030529-01', 'ibeat_setup'): ('7128_C01', 'Visit1'), #./1.84/75
    ('153741_20210810', 'ibeat_setup'): ('7128_C02', 'Visit1'), #F/./85
    ('153765_20210817', 'ibeat_setup'): ('7128_C03', 'Visit1'), #F/./63
    ('153801_20210823', 'ibeat_setup'): ('7128_C04', 'Visit1'), #M/./85
    ('153999_20211006', 'ibeat_setup'): ('7128_C05', 'Visit1'), #F/1.6/65
    ('154029_20211011', 'ibeat_setup'): ('7128_C06', 'Visit1'), #F/1.75/60
    ('153652_20210712', 'ibeat_setup'): ('7128_C07', 'Visit1'), #'/1.63/63
    ('154288_iBEAT_TOF_TEST', 'ibeat_setup'): ('7128_C08', 'Visit1'), # F/1.6/59
    ('20210809', 'ibeat_setup'): ('Exclude', 'Exclude'), # phantom
    
    ('20211103_1307', 'ibeat_setup'): ('Exclude', 'Exclude'), # phantom
    ('ibeat_test', 'ibeat_setup'): ('Exclude', 'Exclude'), # phantom
}



def clean_patient_id(series_xnat, group, site):

    if 'atient' in group: # patients
        if site == 'Bari':
            id = series_xnat[1]
            if id[:3]=='iBE':
                return id[4:].replace('-', '_')
            else:
                return id[:4] + '_' + id[4:]
            
        if site == 'Bordeaux':
            id = series_xnat[1]
            # 2128_001
            if len(id) == 8:
                return id
            # iBE-2128-001_baseline
            id = id[4:12].replace('-', '_')
            return id
        
        if site == 'Exeter':
            id = series_xnat[1]
            if id=='3128-542':
                return '3128_542'
            # iBE-2128-001_baseline
            return id[4:12].replace('-', '_')
        
        if site == 'Leeds':
            id = series_xnat[1]
            if id[:3]=='iBE':
                return id[4:].replace('-', '_')
            else:
                return id[-7:-3] + '_' + id[-3:]

        if site=='Sheffield':
            pn = db.unique('PatientName', series_xnat)[0]
            id = pn[3:7] + '_' + pn[7:10]
            # Fixes a data entry error
            if id == '2178_157': 
                id = '7128_157'
            return id
        
        if site=='Turku':
            id = series_xnat[1]
            # Exception
            if id =='5128-001-28092018':
                return '5128_001'
            # 5128-003
            if len(id) == 8:
                return id.replace('-', '_')
            # iBE-5128-025
            id = id[4:].replace('-', '_')
            id = id[:8]
            return id
    
    # Check if it is one of the known controls
    else: # volunteers
        try:
            id, _ = CLEAN_CTRL_IDS[(series_xnat[1], series_xnat[2][0])]
            if id =='Exclude':
                return
            return id
        except KeyError:
            logging.error(f'Unknown volunteer {(series_xnat[1], series_xnat[2][0])}')
            return
    
    logging.error(f'Unknown PatientID for {series_xnat[1:]}')


def clean_study_desc(zip_file, series_xnat, group, site):
    
    if 'atient' in group: # patients
        if site in ['Leeds', 'Sheffield', 'Bari']:
            return 'Baseline'
        
        if site in ['Bordeaux', 'Exeter']: 
            folder_name = Path(zip_file).parent.parent.name
            if 'Baseline' in folder_name:
                return 'Baseline'
            if 'Followup' in folder_name:
                return 'Followup'
            
        if site in ['Turku']: 
            if 'followup' in zip_file:
                return 'Followup'
            else:
                return 'Baseline'
    
    # Check if it is one of the known controls
    else: # volunteers
        try:
            # This needs a cleaner approach
            _, desc = CLEAN_CTRL_IDS[(series_xnat[1], series_xnat[2][0])]
            if desc =='Exclude':
                return
            if desc is None:
                folder_name = Path(zip_file).parent.name
                desc = f'Visit{folder_name[-1]}'
            return desc
        
        except KeyError:
            logging.error(f'Unknown volunteer {(series_xnat[1], series_xnat[2][0])}')
            return
    
    logging.error(f'Unknown StudyDescription for {series_xnat[1:]}')


def clean_series_desc_t2star(series_xnat, image_type):

    # xnat_series_desc = series_xnat[3][0]

    # t2star_desc = {
    #     'None': 'T2star',
    #     "T2star_map_kidneys_cor-oblique_mbh": 'T2star',
    #     "T2star_map_kidney_cor_mph": 'T2star', 
    #     "T2-star-map-kidneys-coronal-oblique-BH": 'T2star', 
    #     "T2*map_kidneys_cor-oblique_mbh": 'T2star',
    #     "T2Star_Images": 'T2star_map_vendor',
    # }

    # try:
    #     series_desc = t2star_desc[series_xnat[3][0]]
    # except KeyError:
    #     logging.error(f'Unknown SeriesDescription for {series_xnat[1:]}')

    magn = [
        ['ORIGINAL', 'PRIMARY', 'M_FFE', 'M', 'FFE'],
        ['ORIGINAL', 'PRIMARY', 'M', 'DIS2D'], 
        ['ORIGINAL', 'PRIMARY', 'M', 'ND'], 
        ['ORIGINAL', 'PRIMARY', 'M_FFE', 'M', 'FFE'],
        ['ORIGINAL', 'PRIMARY', 'OTHER'], 
    ]
    phase = [
        ['ORIGINAL', 'PRIMARY', 'PHASE MAP', 'P', 'FFE'],
        ['ORIGINAL', 'PRIMARY', 'P', 'DIS2D'],
        ['ORIGINAL', 'PRIMARY', 'P', 'ND'], 
        
    ]
    maps = [
        ['DERIVED', 'PRIMARY', 'T2_STAR MAP', 'DIS2D'],
        ['DERIVED', 'PRIMARY', 'T2_STAR MAP', 'ND'],
        ['ORIGINAL', 'PRIMARY', 'T2_STAR_UNSPECIF', 'T2_STAR', 'UNSPECIFIED'], 
    ]

    if image_type in magn:
        return 'T2star_magn'
    if image_type in phase:
        return 'T2star_phase'
    if image_type in maps:
        return 'T2star_map_vendor'
    
    logging.error(f'Unknown ImageType: {image_type}')
