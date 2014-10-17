$(function() {
    if (typeof django_select2 === 'undefined') {
        return;
    }

    // Override this small function to include the object ID if we have it.
    var orig_get_url_params = django_select2.get_url_params;
    django_select2.get_url_params = function (term, page, context) {
        var res = orig_get_url_params.call(this, term, page, context);

        if (matches = window.location.pathname.match(/\/([0-9]+)\/delete$/)) {
            res['object_id'] = matches[1];
        }
        return res;
    };
});
