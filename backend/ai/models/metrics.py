class ModelMetrics:
    @staticmethod
    def calculate_metrics(actual, predicted):
        if len(actual) != len(predicted):
            return None
            
        # Calculate Mean Absolute Error
        mae = sum(abs(a - p) for a, p in zip(actual, predicted)) / len(actual)
        
        # Calculate Mean Squared Error
        mse = sum((a - p) ** 2 for a, p in zip(actual, predicted)) / len(actual)
        
        # Calculate R-squared
        mean_actual = sum(actual) / len(actual)
        ss_tot = sum((a - mean_actual) ** 2 for a in actual)
        ss_res = sum((a - p) ** 2 for a, p in zip(actual, predicted))
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        return {
            'mae': mae,
            'mse': mse,
            'rmse': mse ** 0.5,
            'r2': r2
        }