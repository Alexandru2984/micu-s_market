// Image compression functionality for listings forms

// Function for automatic image compression
function compressImage(file, maxWidth = 800, maxHeight = 800, quality = 0.8) {
    return new Promise((resolve) => {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const img = new Image();
        
        img.onload = function() {
            // Calculate new dimensions while maintaining aspect ratio
            let { width, height } = img;
            
            if (width > height) {
                if (width > maxWidth) {
                    height = (height * maxWidth) / width;
                    width = maxWidth;
                }
            } else {
                if (height > maxHeight) {
                    width = (width * maxHeight) / height;
                    height = maxHeight;
                }
            }
            
            canvas.width = width;
            canvas.height = height;
            
            // Draw compressed image
            ctx.drawImage(img, 0, 0, width, height);
            
            // Convert back to Blob
            canvas.toBlob(resolve, 'image/jpeg', quality);
        };
        
        img.src = URL.createObjectURL(file);
    });
}

// Add compression functionality to image input
document.addEventListener('DOMContentLoaded', function() {
    const imageInput = document.getElementById('image-input');
    const previewContainer = document.getElementById('image-preview');
    
    if (imageInput) {
        imageInput.addEventListener('change', async function(e) {
            const files = Array.from(e.target.files);
            previewContainer.innerHTML = '';
            
            for (let file of files) {
                if (!file.type.startsWith('image/')) continue;
                
                const originalSize = file.size;
                const maxSize = 2 * 1024 * 1024; // 2MB
                
                // Compress if too large
                if (originalSize > maxSize) {
                    try {
                        const compressedFile = await compressImage(file);
                        // Replace file in list
                        const index = files.indexOf(file);
                        const newFile = new File([compressedFile], file.name, {
                            type: 'image/jpeg',
                            lastModified: Date.now()
                        });
                        files[index] = newFile;
                        
                        // Show preview with compression info
                        showImagePreview(newFile, compressedFile.size, originalSize);
                    } catch (error) {
                        console.error('Compression error:', error);
                        showImagePreview(file);
                    }
                } else {
                    showImagePreview(file);
                }
            }
            
            // Update input with compressed files
            const dataTransfer = new DataTransfer();
            files.forEach(file => dataTransfer.items.add(file));
            e.target.files = dataTransfer.files;
        });
    }
});

function showImagePreview(file, compressedSize = null, originalSize = null) {
    const previewContainer = document.getElementById('image-preview');
    const previewDiv = document.createElement('div');
    previewDiv.className = 'relative';
    
    const reader = new FileReader();
    reader.onload = function(e) {
        previewDiv.innerHTML = `
            <img src="${e.target.result}" alt="Preview" class="image-preview w-full h-32 object-cover rounded-lg border">
            <p class="text-xs text-gray-500 mt-1 text-center">${file.name}</p>
            ${compressedSize ? `
                <div class="compression-info text-center">
                    <i class="fas fa-check-circle"></i>
                    Compresată: ${(originalSize / (1024 * 1024)).toFixed(2)}MB → ${(compressedSize / (1024 * 1024)).toFixed(2)}MB
                </div>
            ` : ''}
        `;
    };
    reader.readAsDataURL(file);
    
    previewContainer.appendChild(previewDiv);
}
