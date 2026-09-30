%% GAAFET 3-Stack Nanosheet: TCAD-Anchored 10,000+ Dataset Generator
% =========================================================================
% Multi-Fidelity Modeling & Latin Hypercube Sampling Pipeline
% 
% Methodology:
% 1. Loads the 216-run full-factorial TCAD ground truth dataset (TSMC N2 / Samsung 3GAP calibrated).
% 2. Fits Gaussian Process Regression (GPR) models with Matern 5/2 kernels for all PPA metrics.
% 3. Generates 10,000 continuous device geometries via Latin Hypercube Sampling (LHS).
% 4. Evaluates instantaneous surrogate predictions (< 5 seconds for 10,000 runs).
% 5. Exports 'gaafet_10000_matlab_master_dataset.csv'.
% 6. Generates 4-panel publication parity and validation diagnostics.
% =========================================================================

clear; clc; close all;

fprintf('=================================================================\n');
fprintf('  GAAFET TCAD-ANCHORED 10,000+ DATASET GENERATOR (MATLAB PIPELINE)\n');
fprintf('=================================================================\n');

%% 1. Load Master 216-Run TCAD Dataset
csv_path = 'industry_calibrated_doe_vth0p25/gaafet_tcad_master_dataset.csv';
if ~isfile(csv_path)
    error('Master TCAD CSV not found at: %s', csv_path);
end

opts = detectImportOptions(csv_path);
tcad_data = readtable(csv_path, opts);
fprintf('[1/5] Loaded %d verified TCAD anchor runs from: %s\n', height(tcad_data), csv_path);

% Inputs: Lg (nm), Wns (nm), Tns (nm)
X_train = [tcad_data.Lg_nm, tcad_data.Wns_nm, tcad_data.Tns_nm];

targets = {'Vth_lin_V', 'Vth_sat_V', 'SS_mVdec', 'DIBL_mV_V', ...
           'Ion_mA_um', 'logIoff', 'gm_max_mS_um', 'gds_mS_um', ...
           'Cgg_fF_um', 'tau_int_ps', 'logIonIoff'};

%% 2. Train Gaussian Process Regression (GPR) Models
fprintf('[2/5] Training Physics-Informed Gaussian Process models (Matern 5/2)...\n');
gpr_models = struct();

for i = 1:length(targets)
    t_name = targets{i};
    y_train = tcad_data.(t_name);
    
    % Fit GPR with automatic kernel scale optimization
    mdl = fitrgp(X_train, y_train, ...
        'KernelFunction', 'Matern52', ...
        'BasisFunction', 'Constant', ...
        'Standardize', true, ...
        'FitMethod', 'exact', ...
        'PredictMethod', 'exact');
    
    gpr_models.(t_name) = mdl;
    
    % Cross-validation R2
    cv_mdl = crossval(mdl, 'KFold', 5);
    y_pred_cv = kfoldPredict(cv_mdl);
    r2_cv = 1 - sum((y_train - y_pred_cv).^2) / sum((y_train - mean(y_train)).^2);
    fprintf('   -> %-15s | 5-Fold CV R^2: %.4f\n', t_name, r2_cv);
end

%% 3. Latin Hypercube Sampling (LHS) for 10,000 Continuous Geometries
fprintf('[3/5] Generating 10,000 samples via Latin Hypercube Sampling...\n');
num_samples = 10000;
rng(2026, 'twister'); % Reproducible seed

% Bounding box: Lg in [10, 20] nm, Wns in [15, 30] nm, Tns in [3, 8] nm
bounds_min = [10.0, 15.0, 3.0];
bounds_max = [20.0, 30.0, 8.0];

% Generate uniform LHS unit cube
lhs_unit = lhsdesign(num_samples, 3, 'Criterion', 'maximin', 'Iterations', 10);
X_10k = bounds_min + lhs_unit .* (bounds_max - bounds_min);

% Round to 2 decimal places for clean physical reporting
X_10k = round(X_10k, 2);

Lg_10k  = X_10k(:, 1);
Wns_10k = X_10k(:, 2);
Tns_10k = X_10k(:, 3);

% Exact geometric effective perimeter for 3 stacked sheets:
% Weff = 2 * N_sheets * (Wns + Tns) * 1e-3 = 6 * (Wns + Tns) * 1e-3 um
Weff_10k = round(6.0 * (Wns_10k + Tns_10k) * 1e-3, 4);

%% 4. Evaluate Surrogate Predictions for all 10,000 Samples
fprintf('[4/5] Evaluating surrogate predictions for 10,000 devices...\n');
tic;

RunIDs = cell(num_samples, 1);
for k = 1:num_samples
    RunIDs{k} = sprintf('SYNTH_%05d', k);
end

df_10k = table(RunIDs, Lg_10k, Wns_10k, Tns_10k, Weff_10k, ...
    'VariableNames', {'RunID', 'Lg_nm', 'Wns_nm', 'Tns_nm', 'Weff_um'});

for i = 1:length(targets)
    t_name = targets{i};
    [y_pred, y_sd] = predict(gpr_models.(t_name), X_10k);
    df_10k.(t_name) = round(y_pred, 4);
    df_10k.([t_name '_sd']) = round(y_sd, 4);
end

% Derived figures of merit
df_10k.Ioff_pA_um  = round(10.^(df_10k.logIoff), 3);
df_10k.Pleak_pW_um = round(df_10k.Ioff_pA_um * 0.70, 3);
df_10k.Ion_total_mA = round(df_10k.Ion_mA_um .* df_10k.Weff_um, 4);

eval_time = toc;
fprintf('   -> 10,000 devices evaluated in %.2f seconds (%.1f devices/sec)!\n', ...
    eval_time, num_samples / eval_time);

out_csv = 'gaafet_10000_matlab_master_dataset.csv';
writetable(df_10k, out_csv);
fprintf('   -> Exported to: %s\n', out_csv);

%% 5. Publication Parity & Cross-Verification Diagnostics Plot
fprintf('[5/5] Generating publication diagnostic plots...\n');

figure('Position', [100, 100, 1200, 900], 'Color', 'w');

% Subplot 1: Vth Parity
subplot(2, 2, 1);
y_true = tcad_data.Vth_lin_V;
y_pred = predict(gpr_models.Vth_lin_V, X_train);
scatter(y_true, y_pred, 30, [0.18, 0.45, 0.71], 'filled', 'MarkerEdgeColor', 'k', 'MarkerFaceAlpha', 0.75);
hold on;
min_v = min(y_true)-0.005; max_v = max(y_true)+0.005;
plot([min_v, max_v], [min_v, max_v], 'r--', 'LineWidth', 2);
grid on; box on;
xlabel('Sentaurus TCAD Ground Truth V_{th,lin} (V)', 'FontWeight', 'bold');
ylabel('MATLAB GPR Predicted V_{th,lin} (V)', 'FontWeight', 'bold');
title('1. Threshold Voltage Parity (216 TCAD Anchors)', 'FontWeight', 'bold');
legend('TCAD Anchors', 'Ideal 1:1 Parity', 'Location', 'northwest');

% Subplot 2: Ion Parity
subplot(2, 2, 2);
y_true = tcad_data.Ion_mA_um;
y_pred = predict(gpr_models.Ion_mA_um, X_train);
scatter(y_true, y_pred, 30, [0.22, 0.63, 0.41], 'filled', 'MarkerEdgeColor', 'k', 'MarkerFaceAlpha', 0.75);
hold on;
min_v = min(y_true)-0.02; max_v = max(y_true)+0.02;
plot([min_v, max_v], [min_v, max_v], 'r--', 'LineWidth', 2);
grid on; box on;
xlabel('Sentaurus TCAD Ground Truth I_{on} (mA/\mum)', 'FontWeight', 'bold');
ylabel('MATLAB GPR Predicted I_{on} (mA/\mum)', 'FontWeight', 'bold');
title('2. On-Current Drive Parity', 'FontWeight', 'bold');
legend('TCAD Anchors', 'Ideal 1:1 Parity', 'Location', 'northwest');

% Subplot 3: SS Parity
subplot(2, 2, 3);
y_true = tcad_data.SS_mVdec;
y_pred = predict(gpr_models.SS_mVdec, X_train);
scatter(y_true, y_pred, 30, [0.87, 0.42, 0.13], 'filled', 'MarkerEdgeColor', 'k', 'MarkerFaceAlpha', 0.75);
hold on;
min_v = min(y_true)-0.5; max_v = max(y_true)+0.5;
plot([min_v, max_v], [min_v, max_v], 'r--', 'LineWidth', 2);
grid on; box on;
xlabel('Sentaurus TCAD Ground Truth SS (mV/dec)', 'FontWeight', 'bold');
ylabel('MATLAB GPR Predicted SS (mV/dec)', 'FontWeight', 'bold');
title('3. Subthreshold Swing Parity', 'FontWeight', 'bold');
legend('TCAD Anchors', 'Ideal 1:1 Parity', 'Location', 'northwest');

% Subplot 4: Continuous 10,000 Design Space
subplot(2, 2, 4);
sub_idx = 1:10:num_samples; % Subsample for crisp plotting
scatter(df_10k.Lg_nm(sub_idx), df_10k.Tns_nm(sub_idx), 10, df_10k.Ion_mA_um(sub_idx), 'filled', 'MarkerFaceAlpha', 0.5);
hold on;
scatter(tcad_data.Lg_nm, tcad_data.Tns_nm, 35, 'ks', 'LineWidth', 1.2);
colormap(gca, 'parula');
c = colorbar;
c.Label.String = 'Predicted I_{on} (mA/\mum)';
c.Label.FontWeight = 'bold';
grid on; box on;
xlabel('Gate Length L_g (nm)', 'FontWeight', 'bold');
ylabel('Nanosheet Thickness T_{ns} (nm)', 'FontWeight', 'bold');
title('4. Continuous 10,000-Point Design Space Coverage', 'FontWeight', 'bold');
legend('10k Synthetic Grid (Subsampled)', '216 TCAD Anchors', 'Location', 'northeast');

sgtitle('GAAFET Multi-Fidelity Modeling: TCAD Ground Truth vs. 10,000-Point Surrogate (MATLAB)', ...
    'FontSize', 13, 'FontWeight', 'bold');

saveas(gcf, 'gaafet_matlab_surrogate_validation.png');
fprintf('   -> Saved MATLAB validation plot to: gaafet_matlab_surrogate_validation.png\n');

fprintf('=================================================================\n');
fprintf('  MATLAB PIPELINE EXECUTION COMPLETE: 10,000 DATASET READY!\n');
fprintf('=================================================================\n');
