from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from PIL import Image
import io

def process_image_to_pdf(uploaded_files, quality_val):
    """
    Optimized processor: Resizes images to save RAM and reduce file size.
    """
    if not uploaded_files:
        return None

    image_list = []
    first_image = None
    
    # 1. Determine Max Size based on quality slider
    # If user wants low quality (slider < 50), we shrink images more aggressively.
    if quality_val < 50:
        max_dimension = (800, 800) # Very small file size
    else:
        max_dimension = (1200, 1200) # Decent quality, safe for RAM

    try:
        for file in uploaded_files:
            # Open image
            img = Image.open(file)
            
            # 🌟 VITAL FIX: Resize image BEFORE adding to list
            # This prevents Server RAM from exploding with 50+ images
            img.thumbnail(max_dimension) 
            
            # Convert to RGB (Required for PDF)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            if first_image is None:
                first_image = img
            else:
                image_list.append(img)

        if first_image is None:
            return None

        # Create memory buffer
        buffer = io.BytesIO()
        
        # Save images to buffer
        first_image.save(
            buffer, 
            "PDF", 
            resolution=72.0, # Web resolution (standard is 72, print is 300)
            save_all=True, 
            append_images=image_list,
            quality=quality_val,
            optimize=True
        )
        
        buffer.seek(0)
        return buffer

    except Exception as e:
        print(f"Error processing image: {e}")
        return None

def home(request):
    if request.method == "POST":
        uploaded_files = request.FILES.getlist('images')
        quality_val = int(request.POST.get('quality', 60))
        
        buffer = process_image_to_pdf(uploaded_files, quality_val)

        if buffer:
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="converted_images.pdf"'
            return response
        else:
            return render(request, 'converter/index.html', {'error': "Error converting images."})

    return render(request, 'converter/index.html')

def estimate_size(request):
    if request.method == "POST":
        uploaded_files = request.FILES.getlist('images')
        quality_val = int(request.POST.get('quality', 60))
        
        # We only process a sample to save calculation time if there are too many files
        # (Processing 50 files just for a preview might be slow)
        if len(uploaded_files) > 5:
             # Logic: Process first 3, calculate average, multiply by total count
             sample_files = uploaded_files[:3]
             buffer = process_image_to_pdf(sample_files, quality_val)
             if buffer:
                 sample_size = buffer.getbuffer().nbytes
                 # Estimate total based on average
                 total_estimate = (sample_size / 3) * len(uploaded_files)
                 
                 # Format
                 if total_estimate < 1024 * 1024:
                     readable = f"{total_estimate / 1024:.0f} KB"
                 else:
                     readable = f"{total_estimate / (1024 * 1024):.1f} MB"
                 return JsonResponse({'success': True, 'size': readable})
        
        # Normal processing for small batches
        buffer = process_image_to_pdf(uploaded_files, quality_val)
        
        if buffer:
            size_bytes = buffer.getbuffer().nbytes
            if size_bytes < 1024 * 1024:
                readable_size = f"{size_bytes / 1024:.2f} KB"
            else:
                readable_size = f"{size_bytes / (1024 * 1024):.2f} MB"
            return JsonResponse({'success': True, 'size': readable_size})
            
    return JsonResponse({'success': False})
