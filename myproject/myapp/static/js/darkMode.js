// /myproject/myapp/static/js/darkMode.js

// ฟังก์ชันสำหรับสลับระหว่างโหมดมืดและโหมดสว่าง
function setupDarkMode() {
  // ตรวจสอบค่าที่บันทึกไว้ใน localStorage หรือการตั้งค่าระบบ
  if (localStorage.getItem('theme') === 'dark' || 
     (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
  
  // รับปุ่มสลับโหมด
  const themeToggle = document.getElementById('theme-toggle');
  
  if (themeToggle) {
    themeToggle.addEventListener('click', function() {
      // สลับคลาส dark ใน document.documentElement (HTML tag)
      document.documentElement.classList.toggle('dark');
      
      // บันทึกค่าลงใน localStorage
      if (document.documentElement.classList.contains('dark')) {
        localStorage.setItem('theme', 'dark');
      } else {
        localStorage.setItem('theme', 'light');
      }

      // อัพเดทสี CSS variables สำหรับส่วนที่ใช้ตัวแปร CSS
      updateThemeColors();
    });
  }

  // อัพเดทสี CSS variables เมื่อโหลดหน้าเว็บ
  updateThemeColors();
}

// ฟังก์ชันอัพเดทสี CSS variables ตาม theme ปัจจุบัน
function updateThemeColors() {
  const isDarkMode = document.documentElement.classList.contains('dark');
  const root = document.documentElement;
  
  // อัพเดท CSS variables ตาม theme
  if (isDarkMode) {
    root.style.setProperty('--navbar-bg', '#1a1a1a');
    root.style.setProperty('--hero-bg', '#1a1a1a');
  } else {
    root.style.setProperty('--navbar-bg', '#0A0D14');
    root.style.setProperty('--hero-bg', '#0A0D14');
  }
}

// รันฟังก์ชันเมื่อเว็บโหลดเสร็จ
document.addEventListener('DOMContentLoaded', setupDarkMode);