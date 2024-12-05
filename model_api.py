import torch
import torchvision.transforms as transforms
from PIL import Image
from pathlib import Path
import torch.nn as nn
import torchvision.models as models
import pickle
import warnings

# Define the ResNet model class
class ResNet(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        self.network = models.resnet50(pretrained=True)
        num_ftrs = self.network.fc.in_features
        self.network.fc = nn.Linear(num_ftrs, num_classes)

    def forward(self, xb):
        return torch.sigmoid(self.network(xb))

# Global variables to hold the model, device, classes, and transformations
_model = None
_device = None
_classes = None
_transformations = None

def load_model(filepath="garbage_classification_model.pt", classes_file="classes.pkl", show_warnings=False):
    """
    Load the model and classes if not already loaded.

    Parameters:
    - filepath: Path to the model file.
    - classes_file: Path to the pickle file containing class labels.

    Returns:
    - The loaded model.
    """
    global _model, _device, _classes, _transformations
    
    # Configure warnings (off by default as they can be distracting)
    if show_warnings:
        warnings.filterwarnings("default", category=UserWarning, module="torch")
    else:
        warnings.filterwarnings("ignore", category=UserWarning, module="torch")
        warnings.filterwarnings("ignore", category=FutureWarning)
            
    if _model is None:
        print("Loading model and resources...")
        
        # Set the device (GPU if available, else CPU)
        _device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load class labels
        with open(classes_file, 'rb') as f:
            _classes = pickle.load(f)
        
        # Initialize the model
        _model = ResNet(num_classes=len(_classes))
        _model.load_state_dict(torch.load(filepath, map_location=_device))
        _model.eval()  # Set the model to evaluation mode

        # Define transformations (same as during training)
        _transformations = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.ToTensor()
        ])

        print("Model and resources loaded successfully.")
    else:
        print("Model is already loaded.")

    return _model

def predict_image(image_path):
    """
    Predict the class of an image.

    Parameters:
    - image_path: Path to the input image.

    Returns:
    - Predicted class name.
    - Probabilities for each class.
    """
    global _model, _device, _classes, _transformations

    if _model is None:
        raise RuntimeError("Model not loaded. Call load_model() first.")

    # Load and preprocess the image
    image = Image.open(image_path)
    input_tensor = _transformations(image)
    input_batch = input_tensor.unsqueeze(0)  # Create a mini-batch

    # Move the input batch to the same device as the model
    input_batch = input_batch.to(_device)

    # Perform prediction
    with torch.no_grad():
        output = _model(input_batch)
        probabilities = torch.nn.functional.softmax(output[0], dim=0)

    # Retrieve the predicted class name and probabilities
    predicted_class_index = torch.argmax(probabilities).item()
    predicted_class_name = _classes[predicted_class_index]
    
    probability_details = [
        {"label": _classes[i], "probability": prob.item()}
        for i, prob in enumerate(probabilities)
    ]

    return predicted_class_name, probability_details

# Optional helper to get the class list
def get_classes():
    """
    Get the list of class names.
    """
    global _classes
    if _classes is None:
        raise RuntimeError("Classes not loaded. Call load_model() first.")
    return _classes
