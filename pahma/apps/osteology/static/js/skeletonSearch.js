
var submitForm = function() {
  var formData = $('.csc-osteology-form').serializeArray().filter(function(item) {
    return item['value'] !== "";
  });
    
  $('#waitingImage').css({
      display: "block"
  });

  $.post("../results/", formData).done(function (data) {
      $('#resultsPanel').html(data);
      $('#waitingImage').css({
          display: "none"
      });
  });
}

$(document).ready(function () {
  $('#search').click(function () {
    submitForm();
  });
});