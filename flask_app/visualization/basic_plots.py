import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import base64
import io
from io import BytesIO
import json
import numpy as np

def create_visualization(df, plot_type, columns, title=None, dimension='2d', for_modal=False):
    # Set modern style
    plt.style.use('bmh')
    
    # Vibrant color palette
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD', '#D4A5A5']
    
    # Custom styling
    plt.rcParams.update({
        'figure.facecolor': 'white',
        'axes.facecolor': 'white',
        'axes.grid': True,
        'grid.alpha': 0.2,
        'axes.labelsize': 11,
        'axes.titlesize': 13,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'axes.prop_cycle': plt.cycler('color', colors)
    })
    
    plt.close('all')
    plt.figure(figsize=(12, 7))
    
    if title:
        plt.title(title, pad=20, fontweight='bold')
    
    try:
        if plot_type == 'histogram':
            if dimension == '2d' and len(columns) == 2:
                # Create grouped histogram
                groups = df[columns[1]].unique()
                for i, group in enumerate(groups):
                    group_data = df[df[columns[1]] == group][columns[0]]
                    plt.hist(group_data, bins=30, alpha=0.5, label=f'{columns[1]}={group}', color=colors[i % len(colors)])
                plt.legend()
            else:
                plt.hist(df[columns[0]].dropna(), bins=30, color=colors[0], alpha=0.7)
            plt.xlabel(columns[0])
            plt.ylabel('Count')
                
        elif plot_type == 'scatter':
            if len(columns) == 2:
                plt.scatter(df[columns[0]], df[columns[1]], alpha=0.6, color=colors[1])
                plt.xlabel(columns[0])
                plt.ylabel(columns[1])
                
        elif plot_type == 'line':
            if len(columns) == 2:
                if dimension == '2d':
                    # Group by the second column and plot multiple lines
                    for name, group in df.groupby(columns[1]):
                        group_sorted = group.sort_values(columns[0])
                        plt.plot(group_sorted[columns[0]], group_sorted.index, 
                               label=f'{columns[1]}={name}')
                    plt.legend()
                else:
                    plt.plot(df[columns[0]], df[columns[1]], linewidth=2, color=colors[2])
                plt.xlabel(columns[0])
                plt.ylabel(columns[1])
                
        elif plot_type == 'box':
            if len(columns) == 2:
                plt.figure(figsize=(12, 6))
                bp = df.boxplot(column=columns[0], by=columns[1], 
                              patch_artist=True,
                              medianprops=dict(color="black"),
                              flierprops=dict(marker='o', markerfacecolor=colors[0]),
                              boxprops=dict(facecolor=colors[3], alpha=0.7))
                
                plt.xticks(rotation=45, ha='right')
                plt.xlabel(columns[1], fontsize=11)
                plt.ylabel(columns[0], fontsize=11)
                plt.suptitle('')
                
        elif plot_type == 'bar':
            if dimension == '2d' and len(columns) == 2:
                # Create grouped bar plot
                grouped_data = df.groupby(columns[1])[columns[0]].mean().sort_values(ascending=False)
                bars = plt.bar(range(len(grouped_data)), grouped_data.values, 
                             color=colors[4], alpha=0.8)
                plt.xticks(range(len(grouped_data)), grouped_data.index, 
                          rotation=45, ha='right')
                plt.xlabel(columns[1])
                plt.ylabel(f'Average {columns[0]}')
                
                # Add value labels
                for bar in bars:
                    height = bar.get_height()
                    plt.text(bar.get_x() + bar.get_width()/2., height,
                            f'{height:.2f}',
                            ha='center', va='bottom')
            else:
                value_counts = df[columns[0]].value_counts()
                bars = plt.bar(range(len(value_counts)), value_counts.values, 
                             color=colors[4], alpha=0.8)
                plt.xticks(range(len(value_counts)), value_counts.index, 
                          rotation=45, ha='right')
                plt.xlabel(columns[0])
                plt.ylabel('Count')
                
                # Add value labels
                for bar in bars:
                    height = bar.get_height()
                    plt.text(bar.get_x() + bar.get_width()/2., height,
                            f'{int(height):,}',
                            ha='center', va='bottom')
                
        elif plot_type == 'violin':
            if len(columns) == 2:
                sns.violinplot(data=df, x=columns[1], y=columns[0], 
                             palette=colors[:len(df[columns[1]].unique())],
                             inner='box')
                plt.xticks(rotation=45, ha='right')
                plt.xlabel(columns[1])
                plt.ylabel(columns[0])
                
        elif plot_type == 'heatmap':
            if len(columns) > 1:
                correlation_matrix = df[columns].corr()
                mask = np.triu(np.ones_like(correlation_matrix, dtype=bool))
                cmap = sns.diverging_palette(220, 20, as_cmap=True)
                
                sns.heatmap(correlation_matrix, 
                          mask=mask,
                          cmap=cmap,
                          annot=True,
                          fmt='.2f',
                          center=0,
                          square=True,
                          cbar_kws={'shrink': .8, 'label': 'Correlation'})
                          
                plt.xticks(rotation=45, ha='right')
                plt.yticks(rotation=0)
        
        # Remove top and right spines
        plt.gca().spines['top'].set_visible(False)
        plt.gca().spines['right'].set_visible(False)
        
        # Adjust layout
        plt.tight_layout()
        
        # Save with high DPI
        img = BytesIO()
        plt.savefig(img, format='png', dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        img.seek(0)
        
        # Convert to base64 string
        plot_data = base64.b64encode(img.getvalue()).decode()
        
        return {
            'plot_data': plot_data,
            'plot_type': plot_type
        }

    except Exception as e:
        print(f"Error in create_visualization: {str(e)}")
        return None

def generate_histogram(column_name, df):
    plt.close('all')
    plt.figure(figsize=(10, 6))
    
    try:
        # Create histogram
        plt.hist(df[column_name].dropna(), bins=30, edgecolor='black')
        plt.title(f'Histogram of {column_name}')
        plt.xlabel(column_name)
        plt.ylabel('Frequency')
        
        # Save plot to BytesIO object
        img = BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        
        # Convert to base64 string
        plot_url = base64.b64encode(img.getvalue()).decode()
        
        # Get basic statistics
        stats = {
            'mean': float(df[column_name].mean()),
            'median': float(df[column_name].median()),
            'std': float(df[column_name].std()),
            'min': float(df[column_name].min()),
            'max': float(df[column_name].max())
        }
        
        return plot_url, stats
        
    except Exception as e:
        return None, {'error': str(e)}
