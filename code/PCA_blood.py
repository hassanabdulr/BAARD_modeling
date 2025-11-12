import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler 

df = pd.read_csv('blood_data.csv')

## we need to make the SASP index, which is a PCA of all the blood markers we have. this is what was said in the paper: 

# We calculated a SASP index for each participant based on the regression analysis of individual weights of biomarkers included in the SASP panel. 
# For this, we initially carried out a principal component analysis (PCA) with all proteins included in the model. We extracted the individual weight 
# of each biomarker based on its eigenvector value. Finally, we calculated the SASP index for each participant using a multiple linear regression model, 
# in which SASP index was the dependent variable, the individual SASP biomarkers were the predictor variables, and the biomarker’s weight was the regression coefficient for each SASP biomarker:


# select the blood markers
blood_markers = df[['IL-6','gp130','IL-8/CXCL8','uPAR','MIF','CCL2/JE/MCP-1',
                           'Osteoprotegerin/TNFRSF11B','IL-1 beta/IL-1F2','CCL20/MIP-3 alpha',
                           'CCL3/MIP-1 alpha','CCL4/MIP-1 beta','CCL13/MCP-4','GM-CSF',
                           'ICAM-1/CD54','TNF RII/TNFRSF1B','TNF RI/TNFRSF1A','PIGF',
                           'CXCL1/GRO alpha/KC/CINC-1','IGFBP-2','TIMP-1','IGFBP-6','Angiogenin']]

# list of biomarker columns
biomarker_columns = blood_markers.columns.tolist()

# 1) ORIGINAL (no log transform)

# Standardize
scaler_raw = StandardScaler()
blood_scaled_raw = scaler_raw.fit_transform(blood_markers)

# PCA
pca_raw = PCA(n_components=1)
pca_raw.fit(blood_scaled_raw)

# Extract eigenvector loadings (weights)
weights_raw = pca_raw.components_[0]

# Compute SASP index
sasp_index_raw = np.dot(blood_scaled_raw, weights_raw)

# save in dataframe
df['SASP_index_raw'] = sasp_index_raw

# 2) LOG2-TRANSFORMED VERSION (paper method)

# Handle zeros: replace zeros with half the smallest non-zero value
blood_nonzero = blood_markers.replace(0, np.nan)
smallest = blood_nonzero.min().min()
blood_filled = blood_nonzero.fillna(smallest / 2)

# log2 transform
blood_log2 = np.log2(blood_filled)

# standardize
scaler_log = StandardScaler()
blood_scaled_log = scaler_log.fit_transform(blood_log2)

# PCA
pca_log = PCA(n_components=1)
pca_log.fit(blood_scaled_log)

# Extract weights
weights_log = pca_log.components_[0]

# Compute SASP index
sasp_index_log = np.dot(blood_scaled_log, weights_log)

# add to dataframe
df['SASP_index_log2'] = sasp_index_log

# save wights
weights_df = pd.DataFrame({
    'Biomarker': biomarker_columns,
    'Weight_Raw': weights_raw,
    'Weight_Log2': weights_log
})


# save to excel the the sasp indices and weights
with pd.ExcelWriter('blood_SASP_results.xlsx') as writer:
    df.to_excel(writer, sheet_name='PACT_MD_with_SASP', index=False)
    weights_df.to_excel(writer, sheet_name='SASP_Weights', index=False)



