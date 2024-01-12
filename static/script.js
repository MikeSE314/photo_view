import PhotoSwipeLightbox from '/static/photoswipe-lightbox.esm.js';
import PhotoSwipe from '/static/photoswipe.esm.js';

const lightbox = new PhotoSwipeLightbox({
  gallery: '#my-gallery',
  children: 'a',
  pswpModule: PhotoSwipe,
  loop: false,
});

lightbox.init();


