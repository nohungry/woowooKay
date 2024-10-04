import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# 讀取CSV資料
df = pd.read_csv(r"D:\temp\MCD64A1_burned_area_full_dataset_2002-2023.csv")

# 聚合資料
df_aggregated = df.groupby(['year', 'country', "month"]).agg({
    'forest': 'sum',
    'savannas': 'sum',
    'shrublands_grasslands': 'sum',
    'croplands': 'sum',
    'other': 'sum'
}).reset_index()

# 計算總燒毀面積
df_aggregated['total_burned_area'] = df_aggregated[['forest', 'savannas', 'shrublands_grasslands', 'croplands', 'other']].sum(axis=1)

# 建立Dash應用程式
app = dash.Dash(__name__)

# 設定應用程式的佈局
app.layout = html.Div(children=[
    html.H1(children='測試report'),

    html.Div([
        dcc.Dropdown(
            id='country-dropdown',
            options=[{'label': country, 'value': country} for country in df['country'].unique()],
            value=df['country'].unique()[0],
            style={'width': '200px'}
        ),
        html.Button('Update', id='update-button', n_clicks=0)
    ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between', 'margin-bottom': '20px'}),

    html.Div([
        dcc.Graph(id='multi-axis-graph', style={'width': '50%', 'display': 'inline-block'}),
        dcc.Graph(id='heatmap-graph', style={'width': '50%', 'display': 'inline-block'}),
    ]),

    dcc.RangeSlider(
        id='year-range-slider',
        min=df_aggregated['year'].min(),
        max=df_aggregated['year'].max(),
        value=[df_aggregated['year'].min(), df_aggregated['year'].max()],
        marks={str(year): str(year) for year in df_aggregated['year'].unique()},
        step=None
    ),
    html.Div(id='output-container-range-slider')
])

# 回調函數更新圖表
@app.callback(
    [Output('multi-axis-graph', 'figure'),
     Output('heatmap-graph', 'figure')],
    [Input('update-button', 'n_clicks'),
     Input('year-range-slider', 'value'),
     Input('country-dropdown', 'value')]
)
def update_graph(n_clicks, selected_years, selected_country):
    df_filtered = df_aggregated[(df_aggregated['year'] >= selected_years[0]) &
                                (df_aggregated['year'] <= selected_years[1]) &
                                (df_aggregated['country'] == selected_country)]

    df_yearly = df_filtered.groupby('year')['total_burned_area'].sum().reset_index()

    short_year = [str(year)[-2:] for year in df_yearly['year']]

    # 柱狀圖
    bar_fig = go.Figure()

    bar_fig.add_trace(go.Bar(
        x=df_yearly['year'],
        y=df_yearly['total_burned_area'],
        name='Yearly Burned Area',
        yaxis='y1',
        marker=dict(color='#1f77b4'),
        hovertemplate='%{y:.0f} ha<extra></extra>'
    ))

    bar_fig.update_layout(
        title=f'Yearly Burned Area - {selected_country} [{selected_years[0]}-{selected_years[1]}]',
        xaxis=dict(
            # title='Year',
            titlefont=dict(color='#1f77b4', size=10),
            tickfont=dict(color='#1f77b4', size=10),
            tickmode='linear',
            dtick=1,
        ),
        yaxis=dict(
            title='Yearly Burned Area [ha]',
            titlefont=dict(color='#1f77b4', size=10),
            tickfont=dict(color='#1f77b4', size=10),
            tickformat=',.0f',
        ),
        bargap=0
    )

    # 熱圖
    # z_values = [[1 if month in [6, 7, 8, 9] else 0 for month in range(1, 13)] for _ in range(selected_years[0], selected_years[1] + 1)]
    z_values = []
    for year in range(selected_years[0], selected_years[1] + 1):
        year_data = []
        for month in range(1, 13):
            fire_data = 1 if df_filtered[(df_filtered['year'] == year) & (df_filtered['month'] == month)]['total_burned_area'].sum() > 0 else 0
            year_data.append(fire_data)
        z_values.append(year_data)

    # 轉置z_values
    z_values_transposed = np.array(z_values).T.tolist()

    heatmap_fig = go.Figure(data=go.Heatmap(
        z=z_values_transposed,
        x=[str(year) for year in range(selected_years[0], selected_years[1] + 1)],
        y=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        colorscale=[[0, '#1f77b4'], [1, '#ff9999']],
        showscale=False,
        xgap=1,
        ygap=1,
        hoverinfo="none"
    ))

    heatmap_fig.update_layout(
        title='Yearly Burned Area Seasonality',
        xaxis=dict(tickfont=dict(color='#1f77b4', size=10)),
        yaxis=dict(tickfont=dict(color='#1f77b4', size=10)),
    )
    
    return bar_fig, heatmap_fig

# 執行應用程式
if __name__ == '__main__':
    app.run_server(debug=True)