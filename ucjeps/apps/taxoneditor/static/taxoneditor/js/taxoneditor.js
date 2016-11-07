$(document).on('click', '#taxon-item', function () {
    console.log("we got here");
    var tds = $( this ).parent().parent().children().get();
    console.log(tds);
    for (td in tds) {
            var fieldname = tds[td].className;
            console.log(fieldname);
            field_to_set = document.getElementById(fieldname);
            if (field_to_set) {
                document.getElementById(fieldname).value = tds[td].innerText;
            }
    }
});
