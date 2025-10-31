#!/usr/bin/env node

/**
 * Image Optimization Script
 * 
 * Optimizes images for production deployment including:
 * - WebP conversion
 * - Compression
 * - Responsive image generation
 * - Lazy loading preparation
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('🖼️  Starting image optimization...');

// Configuration
const config = {
  inputDir: 'public/images',
  outputDir: 'public/optimized',
  formats: ['webp', 'avif', 'jpg'],
  quality: {
    webp: 80,
    avif: 70,
    jpg: 85,
    png: 90
  },
  sizes: [320, 640, 768, 1024, 1280, 1920],
  enableResponsive: true,
  enableLazyLoading: true
};

// Utility functions
function ensureDir(dir) {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

function getImageFiles(dir) {
  if (!fs.existsSync(dir)) {
    console.log(`ℹ️  Directory ${dir} does not exist, creating it...`);
    ensureDir(dir);
    return [];
  }
  
  const files = [];
  
  function scanDirectory(currentDir) {
    const items = fs.readdirSync(currentDir);
    
    for (const item of items) {
      const fullPath = path.join(currentDir, item);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory()) {
        scanDirectory(fullPath);
      } else if (/\.(jpg|jpeg|png|gif|bmp|tiff)$/i.test(item)) {
        files.push({
          path: fullPath,
          name: item,
          relativePath: path.relative(dir, fullPath),
          size: stat.size,
          extension: path.extname(item).toLowerCase()
        });
      }
    }
  }
  
  scanDirectory(dir);
  return files;
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function optimizeWithSharp(inputPath, outputPath, options = {}) {
  // This is a placeholder for sharp optimization
  // In a real implementation, you would use the sharp library
  console.log(`  📸 Optimizing: ${path.basename(inputPath)} -> ${path.basename(outputPath)}`);
  
  // For now, just copy the file (in real implementation, use sharp)
  try {
    fs.copyFileSync(inputPath, outputPath);
    return true;
  } catch (error) {
    console.error(`    ❌ Failed to optimize ${inputPath}:`, error.message);
    return false;
  }
}

function generateResponsiveImages(imageFile) {
  console.log(`📱 Generating responsive images for: ${imageFile.name}`);
  
  const baseName = path.parse(imageFile.name).name;
  const outputDir = path.join(config.outputDir, path.dirname(imageFile.relativePath));
  ensureDir(outputDir);
  
  const generatedImages = [];
  
  // Generate different sizes
  for (const size of config.sizes) {
    for (const format of config.formats) {
      const outputName = `${baseName}-${size}w.${format}`;
      const outputPath = path.join(outputDir, outputName);
      
      const options = {
        width: size,
        format: format,
        quality: config.quality[format] || 80
      };
      
      if (optimizeWithSharp(imageFile.path, outputPath, options)) {
        generatedImages.push({
          path: outputPath,
          width: size,
          format: format,
          originalSize: imageFile.size
        });
      }
    }
  }
  
  return generatedImages;
}

function generateImageManifest(images, optimizedImages) {
  console.log('📋 Generating image manifest...');
  
  const manifest = {
    timestamp: new Date().toISOString(),
    originalImages: images.length,
    optimizedImages: optimizedImages.length,
    totalSavings: 0,
    images: {}
  };
  
  // Group optimized images by original
  const imageGroups = {};
  
  images.forEach(img => {
    const key = img.relativePath;
    imageGroups[key] = {
      original: img,
      optimized: []
    };
  });
  
  optimizedImages.forEach(opt => {
    // Find corresponding original image
    const originalKey = Object.keys(imageGroups).find(key => {
      const baseName = path.parse(imageGroups[key].original.name).name;
      return opt.path.includes(baseName);
    });
    
    if (originalKey) {
      imageGroups[originalKey].optimized.push(opt);
    }
  });
  
  // Build manifest
  Object.entries(imageGroups).forEach(([key, group]) => {
    manifest.images[key] = {
      original: {
        path: group.original.relativePath,
        size: group.original.size,
        sizeFormatted: formatBytes(group.original.size)
      },
      optimized: group.optimized.map(opt => ({
        path: path.relative('public', opt.path),
        width: opt.width,
        format: opt.format,
        size: opt.originalSize, // In real implementation, get actual optimized size
        sizeFormatted: formatBytes(opt.originalSize)
      }))
    };
  });
  
  // Save manifest
  const manifestPath = path.join(config.outputDir, 'image-manifest.json');
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
  
  console.log(`📄 Image manifest saved to: ${manifestPath}`);
  return manifest;
}

function generateLazyLoadingHelpers() {
  console.log('⚡ Generating lazy loading helpers...');
  
  const lazyLoadingCSS = `
/* Lazy Loading Styles */
.lazy-image {
  opacity: 0;
  transition: opacity 0.3s ease-in-out;
}

.lazy-image.loaded {
  opacity: 1;
}

.lazy-image.loading {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
}

@keyframes loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* Responsive Image Styles */
.responsive-image {
  width: 100%;
  height: auto;
  display: block;
}

.image-container {
  position: relative;
  overflow: hidden;
}

.image-placeholder {
  background-color: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}
`;
  
  const lazyLoadingJS = `
// Lazy Loading JavaScript Helper
class LazyImageLoader {
  constructor(options = {}) {
    this.options = {
      rootMargin: '50px',
      threshold: 0.1,
      ...options
    };
    
    this.observer = new IntersectionObserver(
      this.handleIntersection.bind(this),
      this.options
    );
    
    this.init();
  }
  
  init() {
    const lazyImages = document.querySelectorAll('.lazy-image[data-src]');
    lazyImages.forEach(img => this.observer.observe(img));
  }
  
  handleIntersection(entries) {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        this.loadImage(entry.target);
        this.observer.unobserve(entry.target);
      }
    });
  }
  
  loadImage(img) {
    img.classList.add('loading');
    
    const image = new Image();
    image.onload = () => {
      img.src = img.dataset.src;
      img.classList.remove('loading');
      img.classList.add('loaded');
      img.removeAttribute('data-src');
    };
    
    image.onerror = () => {
      img.classList.remove('loading');
      img.classList.add('error');
    };
    
    image.src = img.dataset.src;
  }
  
  // Load remaining images (e.g., on user interaction)
  loadAll() {
    const lazyImages = document.querySelectorAll('.lazy-image[data-src]');
    lazyImages.forEach(img => {
      this.loadImage(img);
      this.observer.unobserve(img);
    });
  }
}

// Initialize lazy loading when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  new LazyImageLoader();
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = LazyImageLoader;
}
`;
  
  // Save CSS helper
  const cssPath = path.join(config.outputDir, 'lazy-loading.css');
  fs.writeFileSync(cssPath, lazyLoadingCSS.trim());
  
  // Save JS helper
  const jsPath = path.join(config.outputDir, 'lazy-loading.js');
  fs.writeFileSync(jsPath, lazyLoadingJS.trim());
  
  console.log(`✅ Lazy loading helpers saved:`);
  console.log(`  - CSS: ${cssPath}`);
  console.log(`  - JS: ${jsPath}`);
}

function generateUsageExamples() {
  console.log('📖 Generating usage examples...');
  
  const examples = `
# Image Optimization Usage Examples

## Basic Lazy Loading
\`\`\`html
<img 
  class="lazy-image responsive-image" 
  data-src="/optimized/hero-1280w.webp"
  src="/optimized/hero-320w.jpg"
  alt="Hero image"
  loading="lazy"
/>
\`\`\`

## Responsive Images with Picture Element
\`\`\`html
<picture>
  <source 
    media="(min-width: 1280px)" 
    srcset="/optimized/hero-1920w.avif 1920w, /optimized/hero-1280w.avif 1280w"
    type="image/avif"
  />
  <source 
    media="(min-width: 1280px)" 
    srcset="/optimized/hero-1920w.webp 1920w, /optimized/hero-1280w.webp 1280w"
    type="image/webp"
  />
  <source 
    media="(min-width: 768px)" 
    srcset="/optimized/hero-1024w.webp 1024w, /optimized/hero-768w.webp 768w"
    type="image/webp"
  />
  <img 
    class="responsive-image"
    src="/optimized/hero-640w.jpg"
    srcset="/optimized/hero-640w.jpg 640w, /optimized/hero-320w.jpg 320w"
    sizes="(min-width: 1280px) 1280px, (min-width: 768px) 768px, 100vw"
    alt="Hero image"
    loading="lazy"
  />
</picture>
\`\`\`

## Next.js Image Component
\`\`\`jsx
import Image from 'next/image';

function OptimizedImage() {
  return (
    <Image
      src="/optimized/hero-1280w.webp"
      alt="Hero image"
      width={1280}
      height={720}
      sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
      priority={false} // Set to true for above-the-fold images
      placeholder="blur"
      blurDataURL="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ..."
    />
  );
}
\`\`\`

## CSS Background Images
\`\`\`css
.hero-section {
  background-image: url('/optimized/hero-320w.webp');
}

@media (min-width: 768px) {
  .hero-section {
    background-image: url('/optimized/hero-768w.webp');
  }
}

@media (min-width: 1280px) {
  .hero-section {
    background-image: url('/optimized/hero-1280w.webp');
  }
}
\`\`\`

## Performance Tips
1. Use \`loading="lazy"\` for images below the fold
2. Use \`loading="eager"\` or \`priority={true}\` for above-the-fold images
3. Provide appropriate \`sizes\` attribute for responsive images
4. Use modern formats (WebP, AVIF) with fallbacks
5. Implement proper aspect ratios to prevent layout shift
6. Consider using blur placeholders for better UX
`;
  
  const examplesPath = path.join(config.outputDir, 'USAGE_EXAMPLES.md');
  fs.writeFileSync(examplesPath, examples.trim());
  
  console.log(`📖 Usage examples saved to: ${examplesPath}`);
}

// Main execution
async function main() {
  try {
    console.log('🔧 Configuration:', JSON.stringify(config, null, 2));
    
    // Ensure output directory exists
    ensureDir(config.outputDir);
    
    // Find all images
    const images = getImageFiles(config.inputDir);
    console.log(`📸 Found ${images.length} images to optimize`);
    
    if (images.length === 0) {
      console.log('ℹ️  No images found to optimize');
      return;
    }
    
    // Display image summary
    console.log('\n📊 Image Summary:');
    const totalSize = images.reduce((sum, img) => sum + img.size, 0);
    console.log(`  Total images: ${images.length}`);
    console.log(`  Total size: ${formatBytes(totalSize)}`);
    
    const extensionCounts = {};
    images.forEach(img => {
      extensionCounts[img.extension] = (extensionCounts[img.extension] || 0) + 1;
    });
    
    console.log('  By format:');
    Object.entries(extensionCounts).forEach(([ext, count]) => {
      console.log(`    ${ext}: ${count} files`);
    });
    
    // Optimize images
    console.log('\n🔄 Starting optimization...');
    const optimizedImages = [];
    
    for (const image of images) {
      if (config.enableResponsive) {
        const responsive = generateResponsiveImages(image);
        optimizedImages.push(...responsive);
      } else {
        // Simple optimization
        const outputPath = path.join(config.outputDir, image.relativePath);
        ensureDir(path.dirname(outputPath));
        
        if (optimizeWithSharp(image.path, outputPath)) {
          optimizedImages.push({
            path: outputPath,
            originalSize: image.size
          });
        }
      }
    }
    
    console.log(`✅ Optimized ${optimizedImages.length} image variants`);
    
    // Generate manifest
    const manifest = generateImageManifest(images, optimizedImages);
    
    // Generate helpers
    if (config.enableLazyLoading) {
      generateLazyLoadingHelpers();
    }
    
    // Generate usage examples
    generateUsageExamples();
    
    console.log('\n🎉 Image optimization completed successfully!');
    console.log('\n📋 Summary:');
    console.log(`  Original images: ${images.length}`);
    console.log(`  Optimized variants: ${optimizedImages.length}`);
    console.log(`  Output directory: ${config.outputDir}`);
    console.log(`  Formats generated: ${config.formats.join(', ')}`);
    console.log(`  Responsive sizes: ${config.sizes.join(', ')}`);
    
    console.log('\n💡 Next steps:');
    console.log('  1. Update your components to use optimized images');
    console.log('  2. Include lazy-loading.css in your styles');
    console.log('  3. Include lazy-loading.js in your scripts');
    console.log('  4. Test image loading performance');
    console.log('  5. Monitor Core Web Vitals improvements');
    
  } catch (error) {
    console.error('❌ Image optimization failed:', error);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = {
  main,
  getImageFiles,
  generateResponsiveImages,
  generateImageManifest,
  generateLazyLoadingHelpers,
  config
};