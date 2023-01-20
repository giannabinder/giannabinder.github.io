/////////////////////////////////elements for download button//////////////////////////////////////////////////////////////
var button = document.getElementById("click-button");

//make the button return back to dark green after it has been clicked and is hovered on
button.addEventListener("mouseover", function() {
  button.style.backgroundColor = "#263317";
});

//make the button return back to white when it is not hovered on
button.addEventListener("mouseout", function() {
  button.style.backgroundColor = "white";
});

//download file
button.addEventListener("click", function() {
  button.style.backgroundColor = "white";
  var link = document.createElement("a");
  link.href = "path/to/your/file";
  link.download = "file.extension";
  link.click();
});