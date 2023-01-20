
/////////////////////////////////scroll to top button action//////////////////////////////////////////////////////////////
$(document).ready(function(){
  $("#btnScrollToTop").click(function(){
    $("html,body").animate({scrollTop:0},1000);
  });
});

/////////////////////////////////elements for password//////////////////////////////////////////////////////////////
const password = 'reveil456';
const passwordButton = document.getElementById('password-button');
const passwordInput = document.getElementById('password-input');
const embedContainer = document.getElementById('embed-container');

//have "enter password" dissapear when user starts to type
passwordInput.addEventListener('focus', function() {
  passwordInput.placeholder = "";
});

//if the user is not typing in box, place "enter password" in it
passwordInput.addEventListener('blur', function() {
  if (!passwordInput.value) {
      passwordInput.placeholder = "Enter password";
  }
});

//check if the passcode entered is correct and display element, otherwise, display an error
passwordButton.addEventListener('click', function() {
  if (passwordInput.value === password) {
    embedContainer.style.display = 'block';
    passwordButton.style.display = 'none';
    passwordInput.style.display = 'none';
  } else {
    alert('Incorrect password, please try again.');
  }
});