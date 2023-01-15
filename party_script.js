/////////////////////////////////elements for party mode//////////////////////////////////////////////////////////////
var p_button = document.getElementById("party-button");
var n_button = document.getElementById("normal-button");
const p_container = document.getElementById("party-container");
const n_container = document.getElementById("normal-container");

//make the button return back to dark green after it has been clicked and is hovered on
p_button.addEventListener("mouseover", function() {
  p_button.style.backgroundColor = "#263317";
});

//make the button return back to white when it is not hovered on
p_button.addEventListener("mouseout", function() {
  p_button.style.backgroundColor = "white";
});

p_button.addEventListener("click", function() {
  p_button.style.backgroundColor = "white";
  p_container.style.display = "block";
  n_container.style.display = "none";
  p_button.style.display = "none";
  n_button.style.display = "block";
}); 

//make the button return back to dark green after it has been clicked and is hovered on
n_button.addEventListener("mouseover", function() {
  n_button.style.backgroundColor = "transparent";
});

//make the button return back to white when it is not hovered on
n_button.addEventListener("mouseout", function() {
  n_button.style.backgroundColor = "white";
});

n_button.addEventListener("click", function() {
  n_button.style.backgroundColor = "white";
  n_container.style.display = "block";
  p_container.style.display = "none";
  n_button.style.display = "none";
  p_button.style.display = "block";
}); 