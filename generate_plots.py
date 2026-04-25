# Script para gerar os gráficos do projeto
# Execute este script para gerar as imagens na pasta assets/

import pandas as pd
import numpy as np 
import matplotlib
matplotlib.use('Agg')  # Para salvar em arquivo sem interface gráfica
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
import os

# Criar diretório assets se não existir
os.makedirs('assets', exist_ok=True)

# Carregamento dos dados
geo_0 = pd.read_csv('data/geo_data_0.csv')
geo_1 = pd.read_csv('data/geo_data_1.csv')
geo_2 = pd.read_csv('data/geo_data_2.csv')

# Separação de features e target
X_0 = geo_0.drop(columns=['product']).select_dtypes(include=['number'])
y_0 = geo_0['product']
X_1 = geo_1.drop(columns=['product']).select_dtypes(include=['number'])
y_1 = geo_1['product']
X_2 = geo_2.drop(columns=['product']).select_dtypes(include=['number'])
y_2 = geo_2['product']

# Funções do modelo
def split_data(X, y, test_size=0.25, random_state=12):
    return train_test_split(X, y, test_size=test_size, random_state=random_state)

def train_predict(X_train, X_valid, y_train):
    model = LinearRegression()
    model.fit(X_train, y_train)
    predictions = model.predict(X_valid)
    return model, predictions

def evaluate_model(y_valid, predictions):
    rmse = np.sqrt(mean_squared_error(y_valid, predictions))
    avg_predicted = predictions.mean()
    return rmse, avg_predicted

def run_model(X, y, region_name):
    X_train, X_valid, y_train, y_valid = split_data(X, y)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_valid_scaled = scaler.transform(X_valid)
    model, predictions = train_predict(X_train_scaled, X_valid_scaled, y_train)
    rmse, avg_predicted = evaluate_model(y_valid, predictions)
    return {'model': model, 'predictions': predictions, 'y_valid': y_valid, 'rmse': rmse, 'avg_predicted': avg_predicted}

# Executar modelos
results_0 = run_model(X_0, y_0, 'Região 0')
results_1 = run_model(X_1, y_1, 'Região 1')
results_2 = run_model(X_2, y_2, 'Região 2')

# Variáveis de negócio
budget = 100_000_000
n_wells = 200
revenue_per_unit = 4500
cost_per_well = budget / n_wells
break_even_volume = cost_per_well / revenue_per_unit

# Gráfico 1: Volume Médio vs REQM
def plot_model_results(results_0, results_1, results_2):
    regions = ['Região 0', 'Região 1', 'Região 2']
    avg_predictions = [results_0['avg_predicted'], results_1['avg_predicted'], results_2['avg_predicted']]
    rmse = [results_0['rmse'], results_1['rmse'], results_2['rmse']]
    x = np.arange(len(regions))
    width = 0.35
    plt.figure(figsize=(10, 6))
    plt.bar(x - width/2, avg_predictions, width, label='Volume médio previsto', color='steelblue')
    plt.bar(x + width/2, rmse, width, label='REQM', color='coral')
    plt.xticks(x, regions)
    plt.ylabel('Valores')
    plt.title('Comparação entre volume Previsto e REQM por região')
    plt.legend()
    plt.tight_layout()
    plt.savefig('assets/volume_rmse_comparison.png', dpi=150)
    plt.close()

# Gráfico 2: Break-even
def plot_break_even_comparison(results_0, results_1, results_2, break_even):
    regions = ['Região 0', 'Região 1', 'Região 2']
    avg_volumes = [results_0['avg_predicted'], results_1['avg_predicted'], results_2['avg_predicted']]
    plt.figure(figsize=(10, 6))
    plt.bar(regions, avg_volumes, color='steelblue')
    plt.axhline(y=break_even, linestyle='--', color='red', label=f'Break-even ({break_even:.2f})')
    plt.title('Comparação: Volume Médio vs Break-even')
    plt.ylabel('Volume de Reservas (milhares de barris)')
    plt.legend()
    plt.tight_layout()
    plt.savefig('assets/break_even_comparison.png', dpi=150)
    plt.close()

# Gráfico 3: Lucro
def select_top_wells(predictions, y_valid, n_wells=200):
    data = pd.DataFrame({'predictions': predictions, 'target': y_valid})
    top_wells = data.sort_values(by='predictions', ascending=False).head(n_wells)
    return top_wells

def calculate_profit(top_wells, revenue_per_unit, budget):
    total_volume = top_wells['target'].sum()
    total_revenue = total_volume * revenue_per_unit
    profit = total_revenue - budget
    return profit, total_volume

def analyze_region(results, region_name, revenue_per_unit, budget):
    top_wells = select_top_wells(results['predictions'], results['y_valid'])
    profit, total_volume = calculate_profit(top_wells, revenue_per_unit, budget)
    return {'profit': profit, 'total_volume': total_volume, 'top_wells': top_wells}

profit_0 = analyze_region(results_0, 'Região 0', revenue_per_unit, budget)
profit_1 = analyze_region(results_1, 'Região 1', revenue_per_unit, budget)
profit_2 = analyze_region(results_2, 'Região 2', revenue_per_unit, budget)

def plot_profit_comparison(profit_0, profit_1, profit_2):
    regions = ['Região 0', 'Região 1', 'Região 2']
    profits = [profit_0['profit'], profit_1['profit'], profit_2['profit']]
    plt.figure(figsize=(10, 6))
    bars = plt.bar(regions, profits, color='steelblue')
    plt.axhline(y=0, linestyle='--', label='Break-even (Lucro = 0)')
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, height, f'{height:,.0f}', ha='center', va='bottom')
    plt.title('Lucro Estimado por Região (Top 200 Poços)')
    plt.ylabel('Lucro ($)')
    plt.legend()
    plt.tight_layout()
    plt.savefig('assets/profit_comparison.png', dpi=150)
    plt.close()

# Gráfico 4: Bootstrapping + Boxplot
def bootstrap_profit(predictions, y_valid, revenue_per_unit, budget, n_samples=1000, n_wells=200):
    profits = []
    for i in range(n_samples):
        indices = np.random.choice(len(predictions), size=500, replace=True)
        sampled_preds = predictions[indices]
        sampled_target = y_valid.iloc[indices]
        data = np.array(list(zip(sampled_preds, sampled_target)))
        data = data[data[:, 0].argsort()[::-1]]
        top_wells = data[:n_wells]
        total_volume = top_wells[:, 1].sum()
        revenue = total_volume * revenue_per_unit
        profit = revenue - budget
        profits.append(profit)
    return profits

profits_0 = bootstrap_profit(results_0['predictions'], results_0['y_valid'], revenue_per_unit, budget)
profits_1 = bootstrap_profit(results_1['predictions'], results_1['y_valid'], revenue_per_unit, budget)
profits_2 = bootstrap_profit(results_2['predictions'], results_2['y_valid'], revenue_per_unit, budget)

def plot_boxplot(profits_0, profits_1, profits_2):
    plt.figure(figsize=(10, 6))
    plt.boxplot([profits_0, profits_1, profits_2], tick_labels=['Região 0', 'Região 1', 'Região 2'])
    plt.axhline(0, linestyle='--', label='Prejuízo')
    plt.title('Distribuição de Lucro por Região (Boxplot)')
    plt.ylabel('Lucro ($)')
    plt.legend()
    plt.tight_layout()
    plt.savefig('assets/boxplot_profit.png', dpi=150)
    plt.close()

# Gerar todos os gráficos
plot_model_results(results_0, results_1, results_2)
plot_break_even_comparison(results_0, results_1, results_2, break_even_volume)
plot_profit_comparison(profit_0, profit_1, profit_2)
plot_boxplot(profits_0, profits_1, profits_2)

print("Gráficos gerados com sucesso na pasta 'assets/'!")