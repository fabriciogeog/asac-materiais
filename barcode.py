from pyzbar.pyzbar import decode
from PIL import Image

# Load your image
img = Image.open('codigos/barcode.png')

# Decode the image
results = decode(img)

for barcode in results:
    # Get the raw bytes data
    raw_data = barcode.data 
    
    # Convert bytes to string to remove the 'b'
    string_data = raw_data.decode('utf-8')
    
    print(string_data)
