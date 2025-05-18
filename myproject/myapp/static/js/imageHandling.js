// /myproject/myapp/static/js/imageHandling.js

/**
 * ฟังก์ชันสำหรับ Lazy Load รูปภาพเพื่อช่วยเพิ่มประสิทธิภาพการโหลดเว็บไซต์
 */
function setupLazyLoading() {
  // ตรวจสอบว่าเบราว์เซอร์รองรับ Intersection Observer API หรือไม่
  if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          const src = img.getAttribute('data-src');
          
          if (src) {
            img.src = src;
            img.removeAttribute('data-src');
          }
          
          // Srcset สำหรับรูปภาพแบบ responsive
          const srcset = img.getAttribute('data-srcset');
          if (srcset) {
            img.srcset = srcset;
            img.removeAttribute('data-srcset');
          }
          
          imageObserver.unobserve(img);
        }
      });
    }, {
      rootMargin: '200px 0px', // โหลดรูปภาพล่วงหน้า 200px ก่อนที่จะเลื่อนมาถึง
      threshold: 0.01 // เริ่มโหลดเมื่อรูปภาพปรากฏอย่างน้อย 1%
    });
    
    // เลือกรูปภาพทั้งหมดที่มี data-src
    const lazyImages = document.querySelectorAll('img[data-src]');
    lazyImages.forEach(img => {
      imageObserver.observe(img);
    });
  } else {
    // Fallback สำหรับเบราว์เซอร์ที่ไม่รองรับ Intersection Observer
    const lazyImages = document.querySelectorAll('img[data-src]');
    lazyImages.forEach(img => {
      img.src = img.getAttribute('data-src');
      img.removeAttribute('data-src');
      
      const srcset = img.getAttribute('data-srcset');
      if (srcset) {
        img.srcset = srcset;
        img.removeAttribute('data-srcset');
      }
    });
  }
}

/**
 * ฟังก์ชันสำหรับแสดงรูปภาพแบบ Progressive (เบลอก่อน แล้วค่อยๆ ชัดขึ้น)
 */
function setupProgressiveImages() {
  const progressiveImages = document.querySelectorAll('.progressive-img');
  
  progressiveImages.forEach(container => {
    const thumb = container.querySelector('.thumb');
    const fullImg = container.querySelector('.full-img');
    
    if (thumb && fullImg) {
      // โหลดรูปภาพขนาดเต็ม
      const img = new Image();
      img.src = fullImg.getAttribute('data-src');
      img.onload = function() {
        // เมื่อโหลดเสร็จแล้ว ค่อยๆ แสดง
        fullImg.src = img.src;
        fullImg.classList.add('loaded');
        thumb.classList.add('faded');
      };
    }
  });
}

/**
 * ฟังก์ชันสำหรับ Gallery รูปภาพในหน้ารายละเอียดสินค้า
 */
function setupProductGallery() {
  const mainImage = document.getElementById('mainImage');
  const thumbnails = document.querySelectorAll('.product-thumbnail');
  
  if (thumbnails.length > 0 && mainImage) {
    thumbnails.forEach(thumbnail => {
      thumbnail.addEventListener('click', function() {
        // ลบ border จากทุกรูปภาพ
        thumbnails.forEach(thumb => {
          thumb.classList.remove('border-2', 'border-mint');
        });
        
        // เพิ่ม border ให้รูปภาพที่เลือก
        this.classList.add('border-2', 'border-mint');
        
        // อัพเดทรูปภาพหลัก
        const imgSrc = this.querySelector('img').getAttribute('src');
        
        // Effect fade transition
        mainImage.style.opacity = '0';
        setTimeout(() => {
          mainImage.setAttribute('src', imgSrc);
          mainImage.style.opacity = '1';
        }, 300);
      });
    });
  }
}

/**
 * ฟังก์ชันสำหรับการ Zoom รูปภาพสินค้า
 */
function setupImageZoom() {
  const zoomableImages = document.querySelectorAll('.zoomable-img');
  
  zoomableImages.forEach(img => {
    img.addEventListener('mousemove', function(e) {
      const zoomer = this.querySelector('.zoomer');
      if (zoomer) {
        const x = e.clientX - this.getBoundingClientRect().left;
        const y = e.clientY - this.getBoundingClientRect().top;
        const width = this.offsetWidth;
        const height = this.offsetHeight;
        
        const xPercent = x / width * 100;
        const yPercent = y / height * 100;
        
        zoomer.style.backgroundPosition = `${xPercent}% ${yPercent}%`;
      }
    });
    
    img.addEventListener('mouseenter', function() {
      const zoomer = this.querySelector('.zoomer');
      if (zoomer) {
        zoomer.style.opacity = '1';
      }
    });
    
    img.addEventListener('mouseleave', function() {
      const zoomer = this.querySelector('.zoomer');
      if (zoomer) {
        zoomer.style.opacity = '0';
      }
    });
  });
}

/**
 * เริ่มการทำงานของ Script ทั้งหมดเมื่อหน้าเว็บโหลดเสร็จ
 */
document.addEventListener('DOMContentLoaded', function() {
  setupLazyLoading();
  setupProgressiveImages();
  setupProductGallery();
  setupImageZoom();
});