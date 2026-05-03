import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import base64
from io import BytesIO
import json
import numpy as np

def create_custom_visualization(df, plot_type, x_column, y_column=None, color_column=None, 
                              size_column=None, title=None, plot_style='default'):
    plt.close('all')
    
    if plot_style != 'default':
        plt.style.use(plot_style)
    
    plt.figure(figsize=(12, 8))
    
    try:
        if plot_type == 'scatter':
            if y_column:
                if color_column and size_column:
                    plt.scatter(df[x_column], df[y_column], 
                              c=df[color_column], s=df[size_column],
                              alpha=0.6)
                elif color_column:
                    plt.scatter(df[x_column], df[y_column], 
                              c=df[color_column], alpha=0.6)
                else:
                    plt.scatter(df[x_column], df[y_column], alpha=0.6)
                
                plt.xlabel(x_column)
                plt.ylabel(y_column)
                
                if color_column:
                    plt.colorbar(label=color_column)
            else:
                return "Error: Scatter plot requires both X and Y columns"
                
        elif plot_type == 'line':
            if y_column:
                if color_column:
                    for category in df[color_column].unique():
                        mask = df[color_column] == category
                        plt.plot(df[mask][x_column], df[mask][y_column], 
                               label=category)
                    plt.legend()
                else:
                    plt.plot(df[x_column], df[y_column])
                    
                plt.xlabel(x_column)
                plt.ylabel(y_column)
            else:
                return "Error: Line plot requires both X and Y columns"
                
        elif plot_type == 'bar':
            if y_column:
                if color_column:
                    df_grouped = df.groupby([x_column, color_column])[y_column].mean().unstack()
                    df_grouped.plot(kind='bar', ax=plt.gca())
                else:
                    df_grouped = df.groupby(x_column)[y_column].mean()
                    df_grouped.plot(kind='bar', ax=plt.gca())
                    
                plt.xlabel(x_column)
                plt.ylabel(f'Mean {y_column}')
                if color_column:
                    plt.legend(title=color_column)
            else:
                counts = df[x_column].value_counts()
                counts.plot(kind='bar')
                plt.xlabel(x_column)
                plt.ylabel('Count')
                
        elif plot_type == 'heatmap':
            if y_column:
                pivot_table = df.pivot_table(index=y_column, columns=x_column, 
                                          values=color_column if color_column else 'count',
                                          aggfunc='mean')
                sns.heatmap(pivot_table, cmap='YlOrRd', annot=True)
            else:
                return "Error: Heatmap requires both X and Y columns"
                
        if title:
            plt.title(title)
            
        plt.tight_layout()
        
        # Save plot to BytesIO object
        img = BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        
        # Convert to base64 string
        plot_url = base64.b64encode(img.getvalue()).decode()
        
        return plot_url
        
    except Exception as e:
        return f"Error creating visualization: {str(e)}"
