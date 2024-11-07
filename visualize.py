import pandas as pd
import matplotlib.pyplot as plt 
import seaborn as sns 
import plotly
import plotly.express as px
import plotly.graph_objects as go
import json


# def plot1_barchart(df):
#     innovation_counts = df['dc'].value_counts().sort_index()

#     # Set the style and color palette
#     sns.set_style("whitegrid")
#     sns.set_palette("deep")

#     # Create a figure with a specific size and DPI
#     plt.figure(figsize=(12, 6), dpi=100)

#     # Create a Seaborn bar chart
#     ax = sns.barplot(x=innovation_counts.index, y=innovation_counts.values)

#     # Customize the plot
#     plt.title('Số lượng công việc cải tiến theo từng DC', fontsize=20, fontweight='bold', pad=20)
#     plt.xlabel('DC', fontsize=14, labelpad=10)
#     plt.ylabel('Số lượng công việc cải tiến', fontsize=14, labelpad=10)

#     # Rotate x-axis labels for better readability
#     plt.xticks(rotation=0, fontsize=12)
#     plt.yticks(fontsize=12)

#     # Add value labels on top of each bar
#     for i, v in enumerate(innovation_counts.values):
#         ax.text(i, v, str(v), ha='center', va='bottom', fontsize=12, fontweight='bold')

#     # Customize the spines
#     sns.despine(left=True, bottom=True)

#     # Add a subtle background color
#     ax.set_facecolor('#f0f0f0')

#     # Adjust layout to prevent cutting off labels
#     plt.tight_layout()
def bar_chart(df):
    # Bar chart: Number of innovations by DC
    innovation_counts = df['dc'].value_counts().sort_index()
    bar_chart = px.bar(x=innovation_counts.index, y=innovation_counts.values,
                       labels={'x': 'Design Center', 'y': 'Số lượng công việc cải tiến'},
                       title='Số lượng Công việc cải tiến theo từng DC')
    bar_chart.update_layout(xaxis_tickangle=-45)
    return bar_chart

def line_chart(df):
    # Line chart: Cumulative saved hours over time
    df['created_at'] = pd.to_datetime(df['created_at'])
    df = df.sort_values('created_at')
    df['cumulative_saved_hours'] = df['saved_hours'].cumsum()
    line_chart = px.line(df, x='created_at', y='cumulative_saved_hours',
                         labels={'created_at': 'TimeLine', 'cumulative_saved_hours': 'Tổng số giờ tiết kiệm'},
                         title='Tổng số giờ tiết kiệm theo thời gian')
    return line_chart

def pie_chart(df):
    # Pie chart: Distribution of task types
    task_type_counts = df['task_type'].value_counts()
    pie_chart = px.pie(values=task_type_counts.values, names=task_type_counts.index,
                       title='Phân bố các loại công việc')

    return pie_chart