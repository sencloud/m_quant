import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import StandardScaler
import logging
import os
import joblib

logger = logging.getLogger(__name__)

class TimeSeriesDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y)
        
    def __len__(self):
        return len(self.X)
        
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

class LSTMModel(nn.Module):
    def __init__(self, input_size, hidden_size=64):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.dropout = nn.Dropout(0.2)
        self.fc = nn.Linear(hidden_size, 1)
        
    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        out = self.dropout(lstm_out[:, -1, :])
        return self.fc(out)

class GRUModel(nn.Module):
    def __init__(self, input_size, hidden_size=64):
        super().__init__()
        self.gru = nn.GRU(input_size, hidden_size, batch_first=True)
        self.dropout = nn.Dropout(0.2)
        self.fc = nn.Linear(hidden_size, 1)
        
    def forward(self, x):
        gru_out, _ = self.gru(x)
        out = self.dropout(gru_out[:, -1, :])
        return self.fc(out)

class RNNModel(nn.Module):
    def __init__(self, input_size, hidden_size=64):
        super().__init__()
        self.rnn = nn.RNN(input_size, hidden_size, batch_first=True)
        self.dropout = nn.Dropout(0.2)
        self.fc = nn.Linear(hidden_size, 1)
        
    def forward(self, x):
        rnn_out, _ = self.rnn(x)
        out = self.dropout(rnn_out[:, -1, :])
        return self.fc(out)

class MLModels:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.scaler = StandardScaler()
        self.target_scaler = StandardScaler()
        self.models = {}
        self.model_classes = {
            'lstm': LSTMModel,
            'gru': GRUModel,
            'rnn': RNNModel
        }
        self.sequence_length = 10
        
    def prepare_data(self, df, target_column, feature_columns, test_size=0.2):
        """准备训练数据"""
        try:
            X = df[feature_columns].values
            y = df[target_column].values.reshape(-1, 1)
            
            # 使用简单的时间序列分割而不是随机分割
            train_size = int(len(X) * (1 - test_size))
            X_train, X_test = X[:train_size], X[train_size:]
            y_train, y_test = y[:train_size], y[train_size:]
            
            # 标准化特征和目标值
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            y_train_scaled = self.target_scaler.fit_transform(y_train)
            y_test_scaled = self.target_scaler.transform(y_test)
            
            # 重塑数据为3D格式
            X_train_reshaped = X_train_scaled.reshape(X_train_scaled.shape[0], 1, -1)
            X_test_reshaped = X_test_scaled.reshape(X_test_scaled.shape[0], 1, -1)
            
            # 创建数据加载器（使用标准化后的目标值）
            train_dataset = TimeSeriesDataset(X_train_reshaped, y_train_scaled.squeeze())
            test_dataset = TimeSeriesDataset(X_test_reshaped, y_test_scaled.squeeze())
            
            train_loader = DataLoader(train_dataset, batch_size=32, shuffle=False)  # 时间序列不打乱
            test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)
            
            return train_loader, test_loader, X_test_reshaped, y_test
            
        except Exception as e:
            logger.error(f"Error preparing data: {str(e)}")
            raise
        
    def calculate_metrics(self, y_true, y_pred):
        """计算评估指标"""
        mse = torch.mean((y_true - y_pred) ** 2).item()
        rmse = np.sqrt(mse)
        mae = torch.mean(torch.abs(y_true - y_pred)).item()
        
        # R2 score
        ss_tot = torch.sum((y_true - torch.mean(y_true)) ** 2)
        ss_res = torch.sum((y_true - y_pred) ** 2)
        r2 = (1 - ss_res / ss_tot).item()
        
        return {
            'mse': float(mse),
            'rmse': float(rmse),
            'mae': float(mae),
            'r2': float(r2)
        }
        
    def train_model(self, model_type, train_loader, test_loader, X_test, y_test):
        """训练模型并返回指标"""
        try:
            logger.info(f"Training {model_type} model...")
            
            if model_type not in self.model_classes:
                raise ValueError(f"Unknown model type: {model_type}")
            
            # 获取输入特征的维度
            X_sample, _ = next(iter(train_loader))
            input_size = X_sample.shape[2]
            
            # 创建模型
            model = self.model_classes[model_type](input_size=input_size)
            model = model.to(self.device)
            
            # 保存模型实例到字典中
            self.models[model_type] = model
            
            # 定义损失函数和优化器
            criterion = nn.MSELoss()
            optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
            scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
                optimizer, mode='min', factor=0.5, patience=5, verbose=True
            )
            
            # 训练模型
            best_loss = float('inf')
            patience_counter = 0
            max_patience = 10
            
            model.train()
            for epoch in range(50):
                total_loss = 0
                batch_count = 0
                
                for batch_X, batch_y in train_loader:
                    batch_X = batch_X.to(self.device)
                    batch_y = batch_y.to(self.device)
                    
                    optimizer.zero_grad()
                    outputs = model(batch_X)
                    loss = criterion(outputs.squeeze(), batch_y)
                    loss.backward()
                    optimizer.step()
                    
                    total_loss += loss.item()
                    batch_count += 1
                
                avg_loss = total_loss / batch_count
                scheduler.step(avg_loss)
                
                # 早停
                if avg_loss < best_loss:
                    best_loss = avg_loss
                    patience_counter = 0
                else:
                    patience_counter += 1
                
                if patience_counter >= max_patience:
                    logger.info(f"Early stopping at epoch {epoch+1}")
                    break
                
                if (epoch + 1) % 10 == 0:
                    logger.info(f'Epoch [{epoch+1}/50], Loss: {avg_loss:.4f}')
            
            # 评估模型
            model.eval()
            all_preds = []
            all_targets = []
            
            with torch.no_grad():
                for batch_X, batch_y in test_loader:
                    batch_X = batch_X.to(self.device)
                    batch_y = batch_y.to(self.device)
                    
                    outputs = model(batch_X)
                    all_preds.extend(outputs.squeeze().cpu().numpy())
                    all_targets.extend(batch_y.cpu().numpy())
            
            # 转换为numpy数组计算指标
            y_pred = np.array(all_preds)
            y_true = np.array(all_targets)
            
            metrics = {
                'mse': float(np.mean((y_true - y_pred) ** 2)),
                'rmse': float(np.sqrt(np.mean((y_true - y_pred) ** 2))),
                'mae': float(np.mean(np.abs(y_true - y_pred))),
                'r2': float(1 - np.sum((y_true - y_pred) ** 2) / np.sum((y_true - np.mean(y_true)) ** 2))
            }
            
            logger.info(f"Model {model_type} training completed. Metrics: {metrics}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error training {model_type} model: {str(e)}")
            raise
        
    def predict(self, model_type, X):
        """使用指定模型进行预测"""
        try:
            if model_type not in self.models:
                raise ValueError(f"Model {model_type} has not been loaded yet")
            
            model = self.models[model_type]
            model.eval()
            
            with torch.no_grad():
                # 标准化输入数据
                original_shape = X.shape
                if len(original_shape) == 3:
                    X_2d = X.reshape(-1, original_shape[2])
                    X_scaled_2d = self.scaler.transform(X_2d)
                    X_scaled = X_scaled_2d.reshape(original_shape)
                else:
                    X_scaled = self.scaler.transform(X)
                    X_scaled = X_scaled.reshape(X_scaled.shape[0], 1, -1)
                
                # 预测
                X_tensor = torch.FloatTensor(X_scaled).to(self.device)
                predictions = model(X_tensor).cpu().numpy()
                
                # 反向转换标准化的预测结果
                predictions_reshaped = predictions.reshape(-1, 1)
                predictions_original = self.target_scaler.inverse_transform(predictions_reshaped)
                
                return predictions_original.squeeze()
                
        except Exception as e:
            logger.error(f"Error in prediction: {str(e)}")
            raise
        
    def calculate_prediction_accuracy(self, actual_prices, predicted_prices):
        """计算预测准确度"""
        try:
            actual = np.array(actual_prices)
            predicted = np.array(predicted_prices)
            
            # 计算方向准确度（涨跌预测正确的比例）
            actual_direction = np.diff(actual) > 0
            predicted_direction = np.diff(predicted) > 0
            direction_accuracy = np.mean(actual_direction == predicted_direction)
            
            # 计算预测误差
            mape = np.mean(np.abs((actual - predicted) / actual)) * 100
            
            return {
                'direction_accuracy': float(direction_accuracy),
                'mape': float(mape)
            }
            
        except Exception as e:
            logger.error(f"Error calculating prediction accuracy: {str(e)}")
            return None

    def save_model(self, model_type, path):
        """保存模型和scaler到指定路径"""
        try:
            model = self.models.get(model_type)
            if model:
                # 保存模型
                model_path = path
                scaler_path = path.replace('.pth', '_scaler.pkl')
                target_scaler_path = path.replace('.pth', '_target_scaler.pkl')
                
                os.makedirs(os.path.dirname(path), exist_ok=True)
                torch.save(model.state_dict(), model_path)
                joblib.dump(self.scaler, scaler_path)
                joblib.dump(self.target_scaler, target_scaler_path)
                
                logger.info(f"Successfully saved model and scalers to {path}")
                return True
            logger.error(f"Model {model_type} not found in self.models")
            return False
        except Exception as e:
            logger.error(f"Error saving model {model_type}: {str(e)}")
            return False

    def load_model(self, model_type, path):
        """从指定路径加载模型和scaler"""
        try:
            # 检查模型类型是否有效
            if model_type not in self.model_classes:
                logger.error(f"Invalid model type: {model_type}")
                return False

            # 构造scaler路径
            model_path = path
            scaler_path = path.replace('.pth', '_scaler.pkl')
            target_scaler_path = path.replace('.pth', '_target_scaler.pkl')

            # 检查所有必需的文件是否存在
            if not all(os.path.exists(p) for p in [model_path, scaler_path, target_scaler_path]):
                logger.error(f"One or more model files not found at {path}")
                return False

            # 如果模型还没有实例化，先创建模型实例
            if model_type not in self.models:
                input_size = 9  # 根据你的特征数量设置
                model_class = self.model_classes[model_type]
                self.models[model_type] = model_class(input_size=input_size).to(self.device)

            # 加载模型和scalers
            model = self.models[model_type]
            model.load_state_dict(torch.load(model_path, map_location=self.device))
            model.eval()
            
            self.scaler = joblib.load(scaler_path)
            self.target_scaler = joblib.load(target_scaler_path)
            
            logger.info(f"Successfully loaded model and scalers from {path}")
            return True
        except Exception as e:
            logger.error(f"Error loading model {model_type}: {str(e)}")
            return False

    def calculate_prediction_confidence(self, features, model_type):
        """计算预测置信度"""
        try:
            # 这里实现你的置信度计算逻辑
            # 可以基于模型的不确定性或其他统计指标
            return 0.8  # 示例返回值
        except Exception as e:
            logger.error(f"Error calculating confidence: {str(e)}")
            return 0.0