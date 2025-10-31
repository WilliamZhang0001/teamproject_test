"""
改进的稳定性预测模型
包含: 特征工程、不平衡处理、RandomForest/XGBoost支持
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Literal
import warnings

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score

# 可选依赖
try:
    from imblearn.over_sampling import SMOTE
    HAS_IMBLEARN = True
except ImportError:
    HAS_IMBLEARN = False
    SMOTE = None
    warnings.warn("imblearn not installed. SMOTE will not be available.")

try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    warnings.warn("xgboost not installed. XGBoost model will not be available.")


@dataclass
class ImprovedStabilityClassifier:
    """
    改进的稳定性分类器
    
    特点:
    1. 支持RandomForest和XGBoost
    2. 自动处理类别不平衡 (SMOTE或class_weight)
    3. 更多特征: 蛋白质类型、polarity、confidence
    4. 交叉验证评估
    """
    
    model_type: Literal["rf", "xgb", "lr"] = "rf"
    use_smote: bool = False
    random_state: int = 42
    model: Optional[Pipeline] = None
    feature_names_: Optional[list] = None
    protein_columns_: Optional[list] = None  # 保存训练时的蛋白质列表
    _imputer: Optional[SimpleImputer] = None  # XGBoost专用
    _scaler: Optional[StandardScaler] = None  # XGBoost专用
    
    def _create_features(self, df: pd.DataFrame, is_training: bool = False) -> pd.DataFrame:
        """
        特征工程 - Phase 1增强版
        
        包含:
        - 基础数值特征: pH, temperature_c, concentration_mg_ml
        - 交互项: pH*temp, pH*conc, temp*conc
        - 区间编码: pH区间, 温度区间, 浓度区间
        - 类别特征: protein_name (one-hot), polarity
        - 质量特征: confidence, 参数缺失指示器
        
        Args:
            df: 输入DataFrame
            is_training: 是否在训练阶段（训练时检测蛋白质列表，预测时使用保存的列表）
        """
        features = pd.DataFrame(index=df.index)
        
        # ===== 基础数值特征 =====
        features['pH'] = df.get('pH') if 'pH' in df.columns else None
        features['temperature_c'] = df.get('temperature_c') if 'temperature_c' in df.columns else None
        features['concentration_mg_ml'] = df.get('concentration_mg_ml') if 'concentration_mg_ml' in df.columns else None
        
        # ===== 交互项特征 =====
        if 'pH' in df.columns and 'temperature_c' in df.columns:
            features['pH_temp_interaction'] = df['pH'] * df['temperature_c']
        
        if 'pH' in df.columns and 'concentration_mg_ml' in df.columns:
            features['pH_conc_interaction'] = df['pH'] * df['concentration_mg_ml'].fillna(0)
        
        if 'temperature_c' in df.columns and 'concentration_mg_ml' in df.columns:
            features['temp_conc_interaction'] = df['temperature_c'] * df['concentration_mg_ml'].fillna(0)
        
        # ===== pH区间编码 =====
        if 'pH' in df.columns:
            ph = df['pH']
            features['pH_acidic'] = ((ph >= 0) & (ph < 6)).astype(int)  # 酸性: 0-6
            features['pH_neutral'] = ((ph >= 6) & (ph <= 8)).astype(int)  # 中性: 6-8
            features['pH_basic'] = ((ph > 8) & (ph <= 14)).astype(int)  # 碱性: 8-14
            features['pH_extreme'] = ((ph < 3) | (ph > 11)).astype(int)  # 极端值
        
        # ===== 温度区间编码 =====
        if 'temperature_c' in df.columns:
            temp = df['temperature_c']
            features['temp_cold'] = (temp < 10).astype(int)  # 低温: <10°C
            features['temp_room'] = ((temp >= 10) & (temp < 30)).astype(int)  # 常温: 10-30°C
            features['temp_moderate'] = ((temp >= 30) & (temp < 60)).astype(int)  # 中温: 30-60°C
            features['temp_hot'] = (temp >= 60).astype(int)  # 高温: ≥60°C
        
        # ===== 浓度区间编码 =====
        if 'concentration_mg_ml' in df.columns:
            conc = df['concentration_mg_ml']
            features['conc_low'] = (conc < 1.0).astype(int)  # 低浓度: <1 mg/mL
            features['conc_medium'] = ((conc >= 1.0) & (conc < 10.0)).astype(int)  # 中浓度: 1-10 mg/mL
            features['conc_high'] = (conc >= 10.0).astype(int)  # 高浓度: ≥10 mg/mL
        
        # ===== 参数缺失指示器 =====
        features['has_ph'] = df['pH'].notna().astype(int) if 'pH' in df.columns else 0
        features['has_temp'] = df['temperature_c'].notna().astype(int) if 'temperature_c' in df.columns else 0
        features['has_conc'] = df['concentration_mg_ml'].notna().astype(int) if 'concentration_mg_ml' in df.columns else 0
        features['param_count'] = features[['has_ph', 'has_temp', 'has_conc']].sum(axis=1)  # 参数数量
        
        # ===== 质量特征 =====
        if 'confidence' in df.columns:
            features['confidence'] = df['confidence']
            # 高置信度指示器
            features['high_confidence'] = (df['confidence'] >= 0.7).astype(int)
        
        # ===== Polarity编码 =====
        if 'polarity' in df.columns:
            polarity_map = {'positive': 1, 'neutral': 0, 'negative': -1, 'mixed': 0.5}
            features['polarity_encoded'] = df['polarity'].map(polarity_map).fillna(0)
            # Polarity one-hot编码
            polarity_dummies = pd.get_dummies(df['polarity'], prefix='polarity', dummy_na=False)
            features = pd.concat([features, polarity_dummies], axis=1)
        
        # ===== 蛋白质编码 =====
        if 'protein_name' in df.columns:
            if is_training:
                # 训练时：检测频繁蛋白质并保存
                protein_counts = df['protein_name'].value_counts()
                frequent_proteins = protein_counts[protein_counts >= 3].index.tolist()  # 降低阈值到3
                self.protein_columns_ = frequent_proteins[:15]  # 增加到15种蛋白质
            
            # 使用保存的蛋白质列表创建特征
            if self.protein_columns_:
                for protein in self.protein_columns_:
                    features[f'is_{protein}'] = (df['protein_name'] == protein).astype(int)
        
        self.feature_names_ = features.columns.tolist()
        return features
    
    def fit(self, df: pd.DataFrame) -> "ImprovedStabilityClassifier":
        """
        训练模型
        
        Args:
            df: DataFrame with columns: pH, temperature_c, concentration_mg_ml,
                label, and optionally: protein_name, polarity, confidence
        """
        # 特征工程（训练模式）
        X = self._create_features(df, is_training=True)
        y = df["label"].astype(int)
        
        # 选择基础模型
        if self.model_type == "rf":
            base_clf = RandomForestClassifier(
                n_estimators=200,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                class_weight='balanced',
                random_state=self.random_state,
                n_jobs=-1
            )
        elif self.model_type == "xgb":
            if not HAS_XGBOOST:
                raise ImportError("XGBoost not installed. Install with: pip install xgboost")
            
            # 计算scale_pos_weight
            n_negative = sum(y == 0)
            n_positive = sum(y == 1)
            scale_pos_weight = n_negative / n_positive if n_positive > 0 else 1
            
            base_clf = XGBClassifier(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.1,
                scale_pos_weight=scale_pos_weight,
                random_state=self.random_state,
                n_jobs=-1,
                eval_metric='logloss',
                enable_categorical=False,  # 禁用分类特征处理
                tree_method='hist'  # 使用直方图方法，更快且稳定
            )
        else:  # lr
            from sklearn.linear_model import LogisticRegression
            base_clf = LogisticRegression(
                C=1.0,
                class_weight='balanced',
                random_state=self.random_state,
                max_iter=1000
            )
        
        # 先填充缺失值和标准化（必须在SMOTE之前）
        imputer = SimpleImputer(strategy="median")
        scaler = StandardScaler()
        
        X_imputed = imputer.fit_transform(X)
        X_scaled = scaler.fit_transform(X_imputed)
        
        # 如果使用SMOTE，对预处理后的数据进行重采样
        if self.use_smote:
            if not HAS_IMBLEARN:
                raise ImportError("imbalanced-learn not installed. Install with: pip install imbalanced-learn")
            
            # 确保少数类样本足够多
            min_class_count = min(sum(y == 0), sum(y == 1))
            k_neighbors = min(5, min_class_count - 1) if min_class_count > 1 else 1
            
            # 应用SMOTE
            smote = SMOTE(random_state=self.random_state, k_neighbors=k_neighbors)
            X_resampled, y_resampled = smote.fit_resample(X_scaled, y)
            print(f"  SMOTE重采样: {len(y)} -> {len(y_resampled)} 条记录")
        else:
            X_resampled, y_resampled = X_scaled, y
        
        # XGBoost与sklearn Pipeline不兼容，需要特殊处理
        if self.model_type == "xgb":
            # 直接训练XGBoost（不用Pipeline）
            base_clf.fit(X_resampled, y_resampled)
            # 保存预处理器和分类器（自定义结构）
            self.model = base_clf
            self._imputer = imputer
            self._scaler = scaler
        else:
            # 对于RF和LR，使用标准Pipeline
            base_clf.fit(X_resampled, y_resampled)
            self.model = Pipeline([
                ("impute", imputer),
                ("scale", scaler),
                ("clf", base_clf)
            ])
        
        return self
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """预测概率"""
        if not self.model:
            raise RuntimeError("Model not fitted")
        
        X_features = self._create_features(X)
        
        # XGBoost特殊处理
        if self.model_type == "xgb":
            X_imputed = self._imputer.transform(X_features)
            X_scaled = self._scaler.transform(X_imputed)
            return self.model.predict_proba(X_scaled)[:, 1]
        else:
            return self.model.predict_proba(X_features)[:, 1]
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """预测类别"""
        if not self.model:
            raise RuntimeError("Model not fitted")
        
        X_features = self._create_features(X)
        
        # XGBoost特殊处理
        if self.model_type == "xgb":
            X_imputed = self._imputer.transform(X_features)
            X_scaled = self._scaler.transform(X_imputed)
            return self.model.predict(X_scaled)
        else:
            return self.model.predict(X_features)
    
    def cross_validate(self, df: pd.DataFrame, cv: int = 5, verbose: bool = True) -> dict:
        """
        交叉验证评估 - Phase 1增强版
        
        包括:
        - 整体指标: Accuracy, Precision, Recall, F1, ROC-AUC
        - 按类别评估: 稳定类别(1)和不稳定类别(0)的Recall
        - 混淆矩阵统计
        """
        X = self._create_features(df, is_training=False)
        y = df["label"].astype(int)
        
        from sklearn.metrics import (
            make_scorer, f1_score, precision_score, recall_score, 
            roc_auc_score, accuracy_score, confusion_matrix,
            classification_report
        )
        from sklearn.model_selection import cross_val_predict
        
        # 基础评估指标
        scorers = {
            'accuracy': make_scorer(accuracy_score),
            'f1': make_scorer(f1_score),
            'precision': make_scorer(precision_score, zero_division=0),
            'recall': make_scorer(recall_score, zero_division=0),
            'roc_auc': 'roc_auc',  # 使用字符串形式，sklearn会自动处理
        }
        
        results = {}
        
        # XGBoost需要特殊处理（手动交叉验证，避免sklearn兼容性问题）
        if self.model_type == "xgb":
            from sklearn.model_selection import KFold
            
            # 手动预处理数据
            X_imputed = self._imputer.transform(X)
            X_scaled = self._scaler.transform(X_imputed)
            
            # 手动实现交叉验证
            kf = KFold(n_splits=cv, shuffle=True, random_state=self.random_state)
            
            accuracy_scores, f1_scores, precision_scores, recall_scores, roc_auc_scores = [], [], [], [], []
            all_y_true, all_y_pred = [], []
            
            for train_idx, test_idx in kf.split(X_scaled):
                X_train, X_test = X_scaled[train_idx], X_scaled[test_idx]
                y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
                
                # 克隆并训练模型
                from copy import deepcopy
                clf = deepcopy(self.model)
                clf.fit(X_train, y_train)
                
                # 预测
                y_pred = clf.predict(X_test)
                y_pred_proba = clf.predict_proba(X_test)[:, 1]
                
                # 计算各项指标
                accuracy_scores.append(accuracy_score(y_test, y_pred))
                f1_scores.append(f1_score(y_test, y_pred))
                precision_scores.append(precision_score(y_test, y_pred, zero_division=0))
                recall_scores.append(recall_score(y_test, y_pred, zero_division=0))
                roc_auc_scores.append(roc_auc_score(y_test, y_pred_proba))
                
                all_y_true.extend(y_test.tolist())
                all_y_pred.extend(y_pred.tolist())
            
            # 聚合结果
            results['accuracy'] = {
                'mean': float(np.mean(accuracy_scores)),
                'std': float(np.std(accuracy_scores)),
                'scores': accuracy_scores
            }
            results['f1'] = {
                'mean': float(np.mean(f1_scores)),
                'std': float(np.std(f1_scores)),
                'scores': f1_scores
            }
            results['precision'] = {
                'mean': float(np.mean(precision_scores)),
                'std': float(np.std(precision_scores)),
                'scores': precision_scores
            }
            results['recall'] = {
                'mean': float(np.mean(recall_scores)),
                'std': float(np.std(recall_scores)),
                'scores': recall_scores
            }
            results['roc_auc'] = {
                'mean': float(np.mean(roc_auc_scores)),
                'std': float(np.std(roc_auc_scores)),
                'scores': roc_auc_scores
            }
            
            # 计算混淆矩阵（用所有fold的预测）
            y_pred = np.array(all_y_pred)
            y_true = np.array(all_y_true)
            cm = confusion_matrix(y_true, y_pred)
        else:
            # RandomForest 和 LR 使用标准交叉验证
            estimator = self.model
            
            for name, scorer in scorers.items():
                try:
                    scores = cross_val_score(estimator, X, y, cv=cv, scoring=scorer, error_score='raise')
                    results[name] = {
                        'mean': float(scores.mean()),
                        'std': float(scores.std()),
                        'scores': scores.tolist()
                    }
                except Exception as e:
                    if verbose:
                        print(f"Warning: Could not compute {name}: {e}")
                    results[name] = {
                        'mean': float('nan'),
                        'std': float('nan'),
                        'scores': []
                    }
            
            # 按类别评估Recall
            y_pred = cross_val_predict(estimator, X, y, cv=cv)
            cm = confusion_matrix(y, y_pred)
        
        # 计算各类别的Recall（对所有模型类型）
        try:
            # 计算各类别的Recall
            if cm.shape == (2, 2):
                tn, fp, fn, tp = cm.ravel()
                results['class_recall'] = {
                    'unstable_class_0': float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0,  # 实际上这是specificity
                    'stable_class_1': float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0,   # Sensitivity/Recall
                    'confusion_matrix': cm.tolist()
                }
                # 添加不平衡度信息
                if self.model_type == "xgb":
                    results['class_distribution'] = {
                        'unstable_count': int(sum(y_true == 0)),
                        'stable_count': int(sum(y_true == 1)),
                        'imbalance_ratio': float(sum(y_true == 1) / sum(y_true == 0)) if sum(y_true == 0) > 0 else float('inf')
                    }
                else:
                    results['class_distribution'] = {
                        'unstable_count': int(sum(y == 0)),
                        'stable_count': int(sum(y == 1)),
                        'imbalance_ratio': float(sum(y == 1) / sum(y == 0)) if sum(y == 0) > 0 else float('inf')
                    }
        except Exception as e:
            if verbose:
                print(f"Warning: Could not compute per-class metrics: {e}")
        
        if verbose:
            print("\n" + "="*60)
            print("交叉验证结果 (Phase 1)")
            print("="*60)
            print(f"准确率 (Accuracy): {results.get('accuracy', {}).get('mean', 0):.3f} ± {results.get('accuracy', {}).get('std', 0):.3f}")
            print(f"精确率 (Precision): {results.get('precision', {}).get('mean', 0):.3f} ± {results.get('precision', {}).get('std', 0):.3f}")
            print(f"召回率 (Recall): {results.get('recall', {}).get('mean', 0):.3f} ± {results.get('recall', {}).get('std', 0):.3f}")
            print(f"F1-score: {results.get('f1', {}).get('mean', 0):.3f} ± {results.get('f1', {}).get('std', 0):.3f}")
            print(f"ROC-AUC: {results.get('roc_auc', {}).get('mean', 0):.3f} ± {results.get('roc_auc', {}).get('std', 0):.3f}")
            
            if 'class_recall' in results:
                print(f"\n按类别召回率:")
                print(f"  稳定类别(1) Recall: {results['class_recall']['stable_class_1']:.3f}")
                print(f"  不稳定类别(0) 识别率: {results['class_recall']['unstable_class_0']:.3f}")
            
            if 'class_distribution' in results:
                dist = results['class_distribution']
                print(f"\n类别分布:")
                print(f"  稳定(1): {dist['stable_count']} 条")
                print(f"  不稳定(0): {dist['unstable_count']} 条")
                print(f"  不平衡比: {dist['imbalance_ratio']:.2f}:1")
            
            print("="*60 + "\n")
        
        return results
    
    def feature_importance(self) -> pd.DataFrame:
        """获取特征重要性 (仅适用于tree-based模型)"""
        if not self.model or self.model_type == "lr":
            raise ValueError("Feature importance only available for tree-based models")
        
        # XGBoost特殊处理
        if self.model_type == "xgb":
            importances = self.model.feature_importances_
        else:
            clf = self.model.named_steps['clf']
            importances = clf.feature_importances_
        
        return pd.DataFrame({
            'feature': self.feature_names_,
            'importance': importances
        }).sort_values('importance', ascending=False)

