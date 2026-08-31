import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score
import torch
import torch.nn as nn
import torch.optim as optim

# 1. Load Dataset
df = pd.read_csv('/home/ananthakrishnan/GAA_PROJECT/gaafet_dataset_sample.csv')

# Feature columns (Inputs to TCAD / Model)
feature_cols = ['Lg_nm', 'Wns_nm', 'Tns_nm', 'Tox_nm', 'WorkFunction_eV', 'Nsd_cm3', 'Nch_cm3']

# Target columns (Outputs from TCAD / Figures of Merit)
target_cols = ['VTH_sat_V', 'SS_mVdec', 'DIBL_mV_V', 'ION_A_um', 'IOFF_A_um']

X = df[feature_cols].values
Y = df[target_cols].values

# Log-transform Nsd and Nch for standard scaling
X[:, 5] = np.log10(X[:, 5]) # log10(Nsd)
X[:, 6] = np.log10(X[:, 6]) # log10(Nch)

# Log-transform IOFF target for stability
Y[:, 4] = np.log10(Y[:, 4]) # log10(IOFF)

# 2. Train / Test Split
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42)

# 3. Standardization
scaler_X = StandardScaler()
scaler_Y = StandardScaler()

X_train_scaled = scaler_X.fit_transform(X_train)
X_test_scaled = scaler_X.transform(X_test)

Y_train_scaled = scaler_Y.fit_transform(Y_train)
Y_test_scaled = scaler_Y.transform(Y_test)

# Convert to PyTorch Tensors
X_train_t = torch.tensor(X_train_scaled, dtype=torch.float32)
Y_train_t = torch.tensor(Y_train_scaled, dtype=torch.float32)
X_test_t = torch.tensor(X_test_scaled, dtype=torch.float32)
Y_test_t = torch.tensor(Y_test_scaled, dtype=torch.float32)

# 4. Define GAAFET Neural Network Surrogate Model
class GAAFETSurrogateNN(nn.Module):
    def __init__(self, in_features=7, out_features=5):
        super(GAAFETSurrogateNN, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(in_features, 64),
            nn.SiLU(), # Swish activation
            nn.Linear(64, 64),
            nn.SiLU(),
            nn.Linear(64, 32),
            nn.SiLU(),
            nn.Linear(32, out_features)
        )
    def forward(self, x):
        return self.net(x)

model = GAAFETSurrogateNN()
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=0.005)

# 5. Model Training Loop
epochs = 200
for epoch in range(epochs):
    model.train()
    optimizer.zero_grad()
    preds = model(X_train_t)
    loss = criterion(preds, Y_train_t)
    loss.backward()
    optimizer.step()

    if (epoch + 1) % 50 == 0:
        model.eval()
        with torch.no_grad():
            val_preds = model(X_test_t)
            val_loss = criterion(val_preds, Y_test_t)
        print(f"Epoch [{epoch+1}/{epochs}] | Train Loss: {loss.item():.4f} | Val Loss: {val_loss.item():.4f}")

# 6. Evaluate Model Performance
model.eval()
with torch.no_grad():
    Y_pred_scaled = model(X_test_t).numpy()
    Y_pred = scaler_Y.inverse_transform(Y_pred_scaled)

print("\n--- Model Evaluation Metrics (R^2 Scores on Test Set) ---")
for i, target in enumerate(target_cols):
    r2 = r2_score(Y_test[:, i], Y_pred[:, i])
    print(f"Target [{target:<12}]: R² Score = {r2:.4f}")

print("\nSample Surrogate Model Training Complete!")
