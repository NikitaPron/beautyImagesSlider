
let images = [
  'https://klike.net/uploads/posts/2019-09/1568528430_2.jpg',
  'https://klike.net/uploads/posts/2019-09/1568528452_22.jpg',
  'https://klike.net/uploads/posts/2019-09/1568528374_4.jpg',
  'https://klike.net/uploads/posts/2019-09/1568528460_12.jpg',
  'https://klike.net/uploads/posts/2019-09/1568528389_20.jpg',
];

let divSlides = document.querySelector('#slides');

images.forEach((item) => {
  let elem = document.createElement('div');
  elem.style.backgroundImage = `url("${item}")`;
  elem.classList.add('slide');
  divSlides.append(elem);
  elem.addEventListener('click', clickHandler);
});

function clickHandler() {
  document.querySelectorAll('.active').forEach((item) => {
    item.classList.remove('active');
  });
  this.classList.add('active');
}

fetch('http://f0655559.xsph.ru/')
  .then((response) => {
    return response.json();
  })
  .then((data) => {
    console.log(data);
  });
