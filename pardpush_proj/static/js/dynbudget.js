function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

$('.form-check-input').click(function () {
    var tagnames;
    tagnames = $("input:checked").next('label').map(function () {
        return $(this).text().trim();
    }).get();
    $.ajax(
        {
            type: "post",
            url: "/ajax/get_cost/",
            data: {
                tags: tagnames,
                csrfmiddlewaretoken: getCookie('csrftoken')
            },
            success: function (data) {
                $(".puthere").text("$" + parseFloat(data.cost).toFixed(2))
            }
        })

});