import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import base64
from sklearn.decomposition import PCA

def create_cluster_visualization(data, labels, model_name):
    plt.close('all')
    plt.figure(figsize=(10, 6))
    
    try:
        # Validate inputs
        if data is None or labels is None:
            raise ValueError("Data and labels cannot be None")
            
        # Convert data and labels to numpy arrays if they aren't already
        data = np.asarray(data)
        labels = np.asarray(labels)
        
        # Ensure data is 2D
        if len(data.shape) == 1:
            data = data.reshape(-1, 1)
        elif len(data.shape) > 2:
            raise ValueError("Data must be 1D or 2D")
            
        # If data has more than 2 dimensions, use PCA to reduce to 2D
        if data.shape[1] > 2:
            pca = PCA(n_components=2)
            data_2d = pca.fit_transform(data)
        else:
            data_2d = data

        # Create scatter plot
        unique_labels = np.unique(labels)
        colors = plt.cm.rainbow(np.linspace(0, 1, len(unique_labels)))

        for label, color in zip(unique_labels, colors):
            mask = (labels == label)
            if np.any(mask):  # Only plot if there are points with this label
                plt.scatter(data_2d[mask, 0], data_2d[mask, 1], 
                           c=[color], label=f'Cluster {label}',
                           alpha=0.6)

        plt.title(f'Cluster Visualization using {model_name}')
        plt.xlabel('Feature 1' if data.shape[1] <= 2 else 'First Principal Component')
        plt.ylabel('Feature 2' if data.shape[1] <= 2 else 'Second Principal Component')
        plt.legend()
        plt.grid(True, alpha=0.3)

        # Save plot to BytesIO object
        img = BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight', dpi=300)
        img.seek(0)
        
        # Convert to base64 string
        plot_url = base64.b64encode(img.getvalue()).decode()
        plt.close()
        
        return plot_url

    except Exception as e:
        plt.close()
        print(f"Error in cluster visualization: {str(e)}")
        return f"Error creating cluster visualization: {str(e)}"