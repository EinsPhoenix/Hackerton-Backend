import json

def load_usage_data(file_path):
    """Load JSON data from the given file path."""
    with open(file_path) as json_file:
        return json.load(json_file)

color_palette = [
    '#FF5733', '#33FF57', '#3357FF', '#FF33A8', '#A833FF', 
    '#33FFF5', '#FFC300', '#DAF7A6', '#581845', '#900C3F'
]

def process_usage_data(data):
    datasets = []
    usage_api = data.get("usage_API", {})
    
    color_index = 0  

    for api_key, info in usage_api.items():
        total_requests = []
        error_count = info.get("errors", 0)

        
        if len(api_key) < 6:
            print(f"Warning: API key '{api_key}' is too short. Skipping...")
            continue

     
        for request in info.get("anfragen", []):
            total_requests.append(request.get("total_token_count", 0))
       
     
        color = color_palette[color_index % len(color_palette)]
        color_index += 1  
        
     
        dataset_requests = {
            'label': f'Anfragen: {api_key}',
            'data': total_requests,
            'borderColor': color,
            'backgroundColor': f'{color}1A',
        }
        datasets.append(dataset_requests)
        
       
        dataset_errors = {
            'label': f'Fehler: {api_key}',
            'data': [error_count] * len(total_requests),  
            'borderColor': '#FF0000',  
            'backgroundColor': '#FF00001A',
            'type': 'line',  
        }
        datasets.append(dataset_errors)

    return datasets