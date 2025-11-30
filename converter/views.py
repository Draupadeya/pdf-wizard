from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from PIL import Image
import io

def process_image_to_pdf(uploaded_files, quality_val):
    """
    Helper function to process images and return a BytesIO buffer.
    Returns None if processing fails.
    """
    if not uploaded_files:
        return None

    image_list = []
    
    try:
        # Open first image and convert to RGB
        first_image = Image.open(uploaded_files[0])
        first_image = first_image.convert('RGB')

        # Process remaining images
        for file in uploaded_files[1:]:
            img = Image.open(file)
            img = img.convert('RGB')
            image_list.append(img)

        # Create memory buffer
        buffer = io.BytesIO()
        
        # Save images to buffer
        first_image.save(
            buffer, 
            "PDF", 
            resolution=100.0, 
            save_all=True, 
            append_images=image_list,
            quality=quality_val,
            optimize=True
        )
        
        # Reset buffer pointer to the beginning so it can be read
        buffer.seek(0)
        return buffer

    except Exception as e:
        print(f"Error processing image: {e}")
        return None

def home(request):
    """
    View for the main page and handling the actual PDF download.
    """
    if request.method == "POST":
        uploaded_files = request.FILES.getlist('images')
        # Get quality from range slider (default to 60)
        quality_val = int(request.POST.get('quality', 60))
        
        # Use our helper function
        buffer = process_image_to_pdf(uploaded_files, quality_val)

        if buffer:
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="converted_images.pdf"'
            return response
        else:
            return render(request, 'converter/index.html', {'error': "Error converting images. Please ensure files are valid images."})

    return render(request, 'converter/index.html')

def estimate_size(request):
    """
    API View to calculate size without downloading.
    Called via AJAX/JavaScript when slider moves.
    """
    if request.method == "POST":
        uploaded_files = request.FILES.getlist('images')
        quality_val = int(request.POST.get('quality', 60))
        
        # Use the SAME helper function to ensure accuracy
        buffer = process_image_to_pdf(uploaded_files, quality_val)
        
        if buffer:
            # Get size in bytes
            size_bytes = buffer.getbuffer().nbytes
            
            # Format size to KB or MB
            if size_bytes < 1024 * 1024:
                readable_size = f"{size_bytes / 1024:.2f} KB"
            else:
                readable_size = f"{size_bytes / (1024 * 1024):.2f} MB"
                
            return JsonResponse({'success': True, 'size': readable_size})
            
    return JsonResponse({'success': False})