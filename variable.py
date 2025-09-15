
# loaad data
master_df = pd.read_csv('C:\\Users\\Hassan\\Documents\\Projects\\baard\\baard_master_sheet.csv')


# make variable had_fall if total_number_falls > 0
master_df['had_fall'] = (master_df['total_number_falls'] > 0).astype(int)

# add new varaible BMI_extremer, where 1 = bmi > 40 or < 20, binary variables
master_df['BMI_extreme'] = ((master_df['bmi'] > 40) | (master_df['bmi'] < 20)).astype(int)

# turns gender into a binary variable (sex)
master_df['sex'] = (master_df['gender'] == 'Male').astype(int)

### bup model

bup_basic_variable_list = [['age', 'sex', 'edu_lvl', 'baseline_madrs', 'remission_status',  'mini_addtl_q1','athf_f1_total_trials_v2','years_with_depression','BMI_extreme']]

bup_additional_variable_list =  [[
    # blood
    'IL-6_sqrt', 'gp130_sqrt', 'IL-8/CXCL8_sqrt', 'uPAR_sqrt', 'MIF_sqrt',
    'CCL2/JE/MCP-1_sqrt', 'Osteoprotegerin/TNFRSF11B_sqrt', 'IL-1 beta/IL-1F2_sqrt',
    'CCL20/MIP-3 alpha_sqrt', 'CCL3/MIP-1 alpha_sqrt', 'CCL4/MIP-1 beta_sqrt',
    'CCL13/MCP-4_sqrt', 'GM-CSF_sqrt', 'ICAM-1/CD54_sqrt', 'TNF RII/TNFRSF1B_sqrt',
    'TNF RI/TNFRSF1A_sqrt', 'PIGF_sqrt', 'CXCL1/GRO alpha/KC/CINC-1_sqrt',
    'IGFBP-2_sqrt', 'TIMP-1_sqrt', 'IGFBP-6_sqrt', 'Angiogenin_sqrt',

    # nih
    'fcc_baseline', 'dccs_baseline', 'flanker_baseline', 'listSort_baseline',
    'pattComp_baseline', 'psm_baseline',

    # cog
    'AIS_01', 'MDMIS_01', 'LIS_01', 'MVCIS_01', 'IMIS_01', 'MTOTALIS_01',
    'CWI3CSSFinal_01', 'DERRSS4_01', 'CWI4CSSFinal_01', 'DTMT4ER_01',
    'DTMT4CO_01', 'DTMT4_01', 'DTMTS4_01', 'RCS_Z_01', 'RDS_Z_01',
    'RFC_Z_01', 'RFR_Z_01', 'RLO_Z_01', 'RLL_Z_01', 'RREC_Z_01',
    'PICTURE_Z_01', 'RSR_Z_01', 'RSF_Z_01', 'RSM_Z_01',

    # smri 
    'WM.hypointensities_log',
    # lh
    'lh_bankssts_thickness', 'lh_caudalanteriorcingulate_thickness',
    'lh_caudalmiddlefrontal_thickness', 'lh_cuneus_thickness',
    'lh_entorhinal_thickness', 'lh_fusiform_thickness', 'lh_inferiorparietal_thickness',
    'lh_inferiortemporal_thickness', 'lh_isthmuscingulate_thickness',
    'lh_lateraloccipital_thickness', 'lh_lateralorbitofrontal_thickness',
    'lh_lingual_thickness', 'lh_medialorbitofrontal_thickness',
    'lh_middletemporal_thickness', 'lh_parahippocampal_thickness',
    'lh_paracentral_thickness', 'lh_parsopercularis_thickness',
    'lh_parsorbitalis_thickness', 'lh_parstriangularis_thickness',
    'lh_pericalcarine_thickness', 'lh_postcentral_thickness',
    'lh_posteriorcingulate_thickness', 'lh_precentral_thickness',
    'lh_precuneus_thickness', 'lh_rostralanteriorcingulate_thickness',
    'lh_rostralmiddlefrontal_thickness', 'lh_superiorfrontal_thickness',
    'lh_superiorparietal_thickness', 'lh_superiortemporal_thickness',
    'lh_supramarginal_thickness', 'lh_frontalpole_thickness',
    'lh_temporalpole_thickness', 'lh_transversetemporal_thickness', 'lh_insula_thickness',
    # rh
    'rh_bankssts_thickness', 'rh_caudalanteriorcingulate_thickness',
    'rh_caudalmiddlefrontal_thickness', 'rh_cuneus_thickness',
    'rh_entorhinal_thickness', 'rh_fusiform_thickness', 'rh_inferiorparietal_thickness',
    'rh_inferiortemporal_thickness', 'rh_isthmuscingulate_thickness',
    'rh_lateraloccipital_thickness', 'rh_lateralorbitofrontal_thickness',
    'rh_lingual_thickness', 'rh_medialorbitofrontal_thickness',
    'rh_middletemporal_thickness', 'rh_parahippocampal_thickness',
    'rh_paracentral_thickness', 'rh_parsopercularis_thickness',
    'rh_parsorbitalis_thickness', 'rh_parstriangularis_thickness',
    'rh_pericalcarine_thickness', 'rh_postcentral_thickness',
    'rh_posteriorcingulate_thickness', 'rh_precentral_thickness',
    'rh_precuneus_thickness', 'rh_rostralanteriorcingulate_thickness',
    'rh_rostralmiddlefrontal_thickness', 'rh_superiorfrontal_thickness',
    'rh_superiorparietal_thickness', 'rh_superiortemporal_thickness',
    'rh_supramarginal_thickness', 'rh_frontalpole_thickness',
    'rh_temporalpole_thickness', 'rh_transversetemporal_thickness', 'rh_insula_thickness',

    # subcortex vol
    'Left.Lateral.Ventricle_etiv', 'Left.Inf.Lat.Vent_etiv', 'Left.Thalamus.Proper_etiv',
    'Left.Caudate_etiv', 'Left.Putamen_etiv', 'X3rd.Ventricle_etiv', 'X4th.Ventricle_etiv',
    'Left.Hippocampus_etiv', 'Left.Amygdala_etiv', 'Right.Lateral.Ventricle_etiv',
    'Right.Inf.Lat.Vent_etiv', 'Right.Thalamus.Proper_etiv', 'Right.Caudate_etiv',
    'Right.Putamen_etiv', 'Right.Hippocampus_etiv', 'Right.Amygdala_etiv',

    # fc within network
    'Vis', 'Limbic', 'Cont', 'SomMot', 'SalVentAttn', 'Default', 'DorsAttn',

    # fc between network
    'Limbic_to_Vis', 'Cont_to_Vis', 'SomMot_to_Vis', 'SalVentAttn_to_Vis',
    'Default_to_Vis', 'DorsAttn_to_Vis', 'Cont_to_Limbic', 'Limbic_to_SomMot',
    'Limbic_to_SalVentAttn', 'Default_to_Limbic', 'DorsAttn_to_Limbic',
    'Cont_to_SomMot', 'Cont_to_SalVentAttn', 'Cont_to_Default', 'Cont_to_DorsAttn',
    'SalVentAttn_to_SomMot', 'Default_to_SomMot', 'DorsAttn_to_SomMot',
    'Default_to_SalVentAttn', 'DorsAttn_to_SalVentAttn', 'Default_to_DorsAttn'
]]


### arp model

arp_basic_variable_list = [['age', 'sex', 'edu_lvl', 'baseline_madrs', 'remission_status',  'mini_addtl_q1','athf_f1_total_trials_v2','years_with_depression','BMI_extreme']]

arp_additional_variable_list = [[
    # blood
    'IL-6_sqrt', 'gp130_sqrt', 'IL-8/CXCL8_sqrt', 'uPAR_sqrt', 'MIF_sqrt',
    'CCL2/JE/MCP-1_sqrt', 'Osteoprotegerin/TNFRSF11B_sqrt', 'IL-1 beta/IL-1F2_sqrt',
    'CCL20/MIP-3 alpha_sqrt', 'CCL3/MIP-1 alpha_sqrt', 'CCL4/MIP-1 beta_sqrt',
    'CCL13/MCP-4_sqrt', 'GM-CSF_sqrt', 'ICAM-1/CD54_sqrt', 'TNF RII/TNFRSF1B_sqrt',
    'TNF RI/TNFRSF1A_sqrt', 'PIGF_sqrt', 'CXCL1/GRO alpha/KC/CINC-1_sqrt',
    'IGFBP-2_sqrt', 'TIMP-1_sqrt', 'IGFBP-6_sqrt', 'Angiogenin_sqrt',

    # nih
    'fcc_baseline', 'dccs_baseline', 'flanker_baseline', 'listSort_baseline',
    'pattComp_baseline', 'psm_baseline',

    # cog
    'AIS_01', 'MDMIS_01', 'LIS_01', 'MVCIS_01', 'IMIS_01', 'MTOTALIS_01',
    'CWI3CSSFinal_01', 'DERRSS4_01', 'CWI4CSSFinal_01', 'DTMT4ER_01',
    'DTMT4CO_01', 'DTMT4_01', 'DTMTS4_01', 'RCS_Z_01', 'RDS_Z_01',
    'RFC_Z_01', 'RFR_Z_01', 'RLO_Z_01', 'RLL_Z_01', 'RREC_Z_01',
    'PICTURE_Z_01', 'RSR_Z_01', 'RSF_Z_01', 'RSM_Z_01',

    # smri 
    'WM.hypointensities_log',
    # lh
    'lh_bankssts_thickness', 'lh_caudalanteriorcingulate_thickness',
    'lh_caudalmiddlefrontal_thickness', 'lh_cuneus_thickness',
    'lh_entorhinal_thickness', 'lh_fusiform_thickness', 'lh_inferiorparietal_thickness',
    'lh_inferiortemporal_thickness', 'lh_isthmuscingulate_thickness',
    'lh_lateraloccipital_thickness', 'lh_lateralorbitofrontal_thickness',
    'lh_lingual_thickness', 'lh_medialorbitofrontal_thickness',
    'lh_middletemporal_thickness', 'lh_parahippocampal_thickness',
    'lh_paracentral_thickness', 'lh_parsopercularis_thickness',
    'lh_parsorbitalis_thickness', 'lh_parstriangularis_thickness',
    'lh_pericalcarine_thickness', 'lh_postcentral_thickness',
    'lh_posteriorcingulate_thickness', 'lh_precentral_thickness',
    'lh_precuneus_thickness', 'lh_rostralanteriorcingulate_thickness',
    'lh_rostralmiddlefrontal_thickness', 'lh_superiorfrontal_thickness',
    'lh_superiorparietal_thickness', 'lh_superiortemporal_thickness',
    'lh_supramarginal_thickness', 'lh_frontalpole_thickness',
    'lh_temporalpole_thickness', 'lh_transversetemporal_thickness', 'lh_insula_thickness',
    # rh
    'rh_bankssts_thickness', 'rh_caudalanteriorcingulate_thickness',
    'rh_caudalmiddlefrontal_thickness', 'rh_cuneus_thickness',
    'rh_entorhinal_thickness', 'rh_fusiform_thickness', 'rh_inferiorparietal_thickness',
    'rh_inferiortemporal_thickness', 'rh_isthmuscingulate_thickness',
    'rh_lateraloccipital_thickness', 'rh_lateralorbitofrontal_thickness',
    'rh_lingual_thickness', 'rh_medialorbitofrontal_thickness',
    'rh_middletemporal_thickness', 'rh_parahippocampal_thickness',
    'rh_paracentral_thickness', 'rh_parsopercularis_thickness',
    'rh_parsorbitalis_thickness', 'rh_parstriangularis_thickness',
    'rh_pericalcarine_thickness', 'rh_postcentral_thickness',
    'rh_posteriorcingulate_thickness', 'rh_precentral_thickness',
    'rh_precuneus_thickness', 'rh_rostralanteriorcingulate_thickness',
    'rh_rostralmiddlefrontal_thickness', 'rh_superiorfrontal_thickness',
    'rh_superiorparietal_thickness', 'rh_superiortemporal_thickness',
    'rh_supramarginal_thickness', 'rh_frontalpole_thickness',
    'rh_temporalpole_thickness', 'rh_transversetemporal_thickness', 'rh_insula_thickness',

    # subcortex vol
    'Left.Lateral.Ventricle_etiv', 'Left.Inf.Lat.Vent_etiv', 'Left.Thalamus.Proper_etiv',
    'Left.Caudate_etiv', 'Left.Putamen_etiv', 'X3rd.Ventricle_etiv', 'X4th.Ventricle_etiv',
    'Left.Hippocampus_etiv', 'Left.Amygdala_etiv', 'Right.Lateral.Ventricle_etiv',
    'Right.Inf.Lat.Vent_etiv', 'Right.Thalamus.Proper_etiv', 'Right.Caudate_etiv',
    'Right.Putamen_etiv', 'Right.Hippocampus_etiv', 'Right.Amygdala_etiv',

    # fc within network
    'Vis', 'Limbic', 'Cont', 'SomMot', 'SalVentAttn', 'Default', 'DorsAttn',

    # fc between network
    'Limbic_to_Vis', 'Cont_to_Vis', 'SomMot_to_Vis', 'SalVentAttn_to_Vis',
    'Default_to_Vis', 'DorsAttn_to_Vis', 'Cont_to_Limbic', 'Limbic_to_SomMot',
    'Limbic_to_SalVentAttn', 'Default_to_Limbic', 'DorsAttn_to_Limbic',
    'Cont_to_SomMot', 'Cont_to_SalVentAttn', 'Cont_to_Default', 'Cont_to_DorsAttn',
    'SalVentAttn_to_SomMot', 'Default_to_SomMot', 'DorsAttn_to_SomMot',
    'Default_to_SalVentAttn', 'DorsAttn_to_SalVentAttn', 'Default_to_DorsAttn'
]]




# make the variable list neater for each model
bup_basic_variable_list = bup_basic_variable_list[0]
bup_additional_variable_list = bup_additional_variable_list[0]