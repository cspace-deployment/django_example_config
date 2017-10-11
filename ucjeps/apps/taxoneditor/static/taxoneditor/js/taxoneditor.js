$(document).on('click', '#taxon-item', function () {
    var tds = $( this ).parent().parent().children().get();
    console.log(tds);
    for (td in tds) {
            var fieldname = tds[td].className;
            console.log(fieldname);
            field_to_set = document.getElementById(fieldname + this.dataset.item);
            if (field_to_set) {
                document.getElementById(fieldname + this.dataset.item).value = tds[td].innerText;
            }
    }
});


$(document).on('click', '#create-taxon', function () {
        event.preventDefault();

        var resultDiv = '#create-result' + this.parentElement.dataset.item ;
        var serviceresultsDiv = '#service-results' + this.parentElement.dataset.item ;

        $('#waitingImage').css({
            display: "inline"
        });

        $.ajax({
            type: 'POST',
            url: 'create',
            data: $(this.parentElement).serialize()
        }).done(function (data) {
            $(resultDiv).html(data);
            $(serviceresultsDiv).css({ display: "none"});
        });

        xga('send', 'pageview', undefined, trackingid);

        $('#waitingImage').css({
            display: "none"
        });
    });


$(document).on('click', '#search-xxx', function () {
        event.preventDefault();

        $('#waitingImage').css({
            display: "inline"
        });

        $.ajax({
            type: 'POST',
            url: '',
            data: $(this.parentElement).serialize()
        }).done(function (data) {
            $('content-main').html(data);
        });

        xga('send', 'pageview', undefined, trackingid);

        $('#waitingImage').css({
            display: "none"
        });
    });

$(document).on('click', '.toggle-serviceresult', function () {
    var serviceresultsDiv = '#service-results' + this.parentElement.dataset.item ;
    $(serviceresultsDiv).toggle();
});