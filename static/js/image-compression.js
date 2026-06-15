document.addEventListener("DOMContentLoaded", () => {
  
  // Initialize avatar compression
  initializeAvatarCompression();

  // Initialize compression for listing images
  initializeListingImageCompression();
});

/**
 * Compress and resize the profile avatar
 */
function initializeAvatarCompression() {
  const avatarInput = document.getElementById('id_avatar');
  if (!avatarInput) return;
  
  avatarInput.addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (!file || !file.type.match('image.*')) return;
    
    // Preview and compression for the avatar
    compressImage(file, {
      maxWidth: 300,
      maxHeight: 300,
      quality: 0.8,
      outputFormat: 'webp'
    }).then(compressedFile => {
      // Replace the original file with the compressed one
      const dt = new DataTransfer();
      dt.items.add(compressedFile);
      avatarInput.files = dt.files;

      // Show preview
      showImagePreview(compressedFile, 'avatar-preview');
    });
  });
}

/**
 * Compress images for listings
 */
function initializeListingImageCompression() {
  const imageInputs = document.querySelectorAll('input[type="file"][accept*="image"]');
  
  imageInputs.forEach(input => {
    if (input.id === 'id_avatar') return; // Skip avatar, it's handled separately
    
    input.addEventListener('change', function(e) {
      const files = Array.from(e.target.files);
      if (!files.length) return;
      
      Promise.all(files.map(file => {
        if (!file.type.match('image.*')) return file;
        
        return compressImage(file, {
          maxWidth: 1200,
          maxHeight: 800,
          quality: 0.85,
          outputFormat: 'webp'
        });
      })).then(compressedFiles => {
        // Replace the original files with the compressed ones
        const dt = new DataTransfer();
        compressedFiles.forEach(file => dt.items.add(file));
        input.files = dt.files;

        // Show preview for all images
        showMultipleImagePreview(compressedFiles, input.id + '-preview');
      });
    });
  });
}

/**
 * Main function for compressing images
 */
function compressImage(file, options = {}) {
  return new Promise((resolve) => {
    const {
      maxWidth = 1200,
      maxHeight = 800,
      quality = 0.8,
      outputFormat = 'webp'
    } = options;
    
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();
    
    img.onload = function() {
      // Compute the new dimensions while keeping the aspect ratio
      let { width, height } = calculateDimensions(img.width, img.height, maxWidth, maxHeight);
      
      canvas.width = width;
      canvas.height = height;
      
      // Draw the resized image
      ctx.drawImage(img, 0, 0, width, height);

      // Convert to a blob in the desired format
      canvas.toBlob((blob) => {
        // Create a new file with the original name but the new extension
        const newFileName = file.name.replace(/\.[^/.]+$/, `.${outputFormat}`);
        const compressedFile = new File([blob], newFileName, {
          type: `image/${outputFormat}`,
          lastModified: Date.now()
        });
        
        console.log(`Image ${file.name} compressed: ${(file.size / 1024).toFixed(1)}KB → ${(compressedFile.size / 1024).toFixed(1)}KB`);
        resolve(compressedFile);
      }, `image/${outputFormat}`, quality);
    };
    
    img.src = URL.createObjectURL(file);
  });
}

/**
 * Compute the new dimensions while keeping the aspect ratio
 */
function calculateDimensions(originalWidth, originalHeight, maxWidth, maxHeight) {
  let width = originalWidth;
  let height = originalHeight;
  
  // Resize only if necessary
  if (width > maxWidth) {
    height = (height * maxWidth) / width;
    width = maxWidth;
  }
  
  if (height > maxHeight) {
    width = (width * maxHeight) / height;
    height = maxHeight;
  }
  
  return { width: Math.round(width), height: Math.round(height) };
}

/**
 * Show preview for a single image
 */
function showImagePreview(file, containerId) {
  const container = document.getElementById(containerId) || createPreviewContainer(containerId);
  
  const img = document.createElement('img');
  img.src = URL.createObjectURL(file);
  img.style.cssText = `
    max-width: 150px;
    max-height: 150px;
    object-fit: cover;
    border-radius: 8px;
    border: 2px solid #ddd;
    margin: 10px;
  `;
  
  container.innerHTML = '';
  container.appendChild(img);
}

/**
 * Show preview for multiple images
 */
function showMultipleImagePreview(files, containerId) {
  const container = document.getElementById(containerId) || createPreviewContainer(containerId);
  container.innerHTML = '';
  
  files.forEach(file => {
    if (!file.type.match('image.*')) return;
    
    const img = document.createElement('img');
    img.src = URL.createObjectURL(file);
    img.style.cssText = `
      width: 100px;
      height: 100px;
      object-fit: cover;
      border-radius: 6px;
      border: 1px solid #ddd;
      margin: 5px;
      display: inline-block;
    `;
    
    container.appendChild(img);
  });
}

/**
 * Create a preview container if it does not exist
 */
function createPreviewContainer(containerId) {
  const container = document.createElement('div');
  container.id = containerId;
  container.style.cssText = `
    margin-top: 10px;
    padding: 10px;
    border: 1px dashed #ccc;
    border-radius: 6px;
    text-align: center;
    background-color: #f9f9f9;
  `;
  
  // Try to find a suitable place to insert the container
  const fileInput = document.querySelector(`input[type="file"]`);
  if (fileInput && fileInput.parentNode) {
    fileInput.parentNode.appendChild(container);
  }
  
  return container;
}

/**
 * Utility for formatting file sizes
 */
function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}
