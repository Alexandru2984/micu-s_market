document.addEventListener("DOMContentLoaded", () => {
  console.log("Micu's Market ready ✅");
  
  // Inițializează compresia pentru avatar
  initializeAvatarCompression();
  
  // Inițializează compresia pentru imagini listing
  initializeListingImageCompression();
});

/**
 * Comprimă și redimensionează avatarul de profil
 */
function initializeAvatarCompression() {
  const avatarInput = document.getElementById('id_avatar');
  if (!avatarInput) return;
  
  avatarInput.addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (!file || !file.type.match('image.*')) return;
    
    // Preview și compresie pentru avatar
    compressImage(file, {
      maxWidth: 300,
      maxHeight: 300,
      quality: 0.8,
      outputFormat: 'webp'
    }).then(compressedFile => {
      // Înlocuiește fișierul original cu cel comprimat
      const dt = new DataTransfer();
      dt.items.add(compressedFile);
      avatarInput.files = dt.files;
      
      // Afișează preview
      showImagePreview(compressedFile, 'avatar-preview');
    });
  });
}

/**
 * Comprimă imaginile pentru listing-uri
 */
function initializeListingImageCompression() {
  const imageInputs = document.querySelectorAll('input[type="file"][accept*="image"]');
  
  imageInputs.forEach(input => {
    if (input.id === 'id_avatar') return; // Skip avatar, e tratat separat
    
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
        // Înlocuiește fișierele originale cu cele comprimate
        const dt = new DataTransfer();
        compressedFiles.forEach(file => dt.items.add(file));
        input.files = dt.files;
        
        // Afișează preview pentru toate imaginile
        showMultipleImagePreview(compressedFiles, input.id + '-preview');
      });
    });
  });
}

/**
 * Funcție principală pentru comprimarea imaginilor
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
      // Calculează dimensiunile noi păstrând aspect ratio
      let { width, height } = calculateDimensions(img.width, img.height, maxWidth, maxHeight);
      
      canvas.width = width;
      canvas.height = height;
      
      // Desenează imaginea redimensionată
      ctx.drawImage(img, 0, 0, width, height);
      
      // Convertește la blob în formatul dorit
      canvas.toBlob((blob) => {
        // Creează un nou fișier cu numele original dar extensia nouă
        const newFileName = file.name.replace(/\.[^/.]+$/, `.${outputFormat}`);
        const compressedFile = new File([blob], newFileName, {
          type: `image/${outputFormat}`,
          lastModified: Date.now()
        });
        
        console.log(`Imaginea ${file.name} comprimată: ${(file.size / 1024).toFixed(1)}KB → ${(compressedFile.size / 1024).toFixed(1)}KB`);
        resolve(compressedFile);
      }, `image/${outputFormat}`, quality);
    };
    
    img.src = URL.createObjectURL(file);
  });
}

/**
 * Calculează dimensiunile noi păstrând aspect ratio
 */
function calculateDimensions(originalWidth, originalHeight, maxWidth, maxHeight) {
  let width = originalWidth;
  let height = originalHeight;
  
  // Redimensionează doar dacă e necesar
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
 * Afișează preview pentru o singură imagine
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
 * Afișează preview pentru multiple imagini
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
 * Creează container pentru preview dacă nu există
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
  
  // Încearcă să găsească un loc potrivit să insereze container-ul
  const fileInput = document.querySelector(`input[type="file"]`);
  if (fileInput && fileInput.parentNode) {
    fileInput.parentNode.appendChild(container);
  }
  
  return container;
}

/**
 * Utility pentru formatarea dimensiunii fișierelor
 */
function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}
